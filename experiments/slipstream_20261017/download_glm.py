#!/usr/bin/env python3
"""Download only the two pinned GLM GGUF shards directly onto the external SSD.

No model loading, no PGRN conversion, no huggingface/Xet internal weight cache.
Run in normal macOS Terminal. Re-running resumes .download files.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
REVISION = "b0f8153e9e7cf57cd3b0aad146667abf9de56f0e"
REPOSITORY = "unsloth/GLM-4.5-Air-GGUF"
RESERVE = 10 * 2**30


def message(text):
    print(text, flush=True)
    with (HERE / "logs/glm-download.log").open("a") as stream:
        stream.write(datetime.now(timezone.utc).isoformat() + " " + text + "\n")


def check_mount(mount, directory=None):
    if mount.is_symlink() or not mount.is_mount():
        raise RuntimeError(f"SSD nicht eingehängt: {mount}. Kein Ersatzordner wird erzeugt.")
    if directory is not None:
        if not directory.resolve().is_relative_to(mount.resolve()):
            raise RuntimeError("Ziel verlässt den externen Mountpoint.")
        if directory.exists() and directory.stat().st_dev != mount.stat().st_dev:
            raise RuntimeError("Ziel liegt nicht auf dem eingehängten externen Dateisystem.")


def external_directory(mount, destination):
    """Use open directory FDs: missing mounts cannot redirect mkdir to local storage."""
    check_mount(mount)
    relative = destination.relative_to(mount)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(mount, flags)
    device = os.fstat(fd).st_dev
    try:
        for component in relative.parts:
            if component in (".", ".."):
                raise RuntimeError("Unzulässiger Zielpfad.")
            check_mount(mount)
            try:
                os.mkdir(component, dir_fd=fd)
            except FileExistsError:
                pass
            next_fd = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
            if os.fstat(fd).st_dev != device:
                raise RuntimeError("Zieldateisystem hat gewechselt.")
        check_mount(mount, destination)
        # Relative curl output stays on this filesystem even if the mount disappears.
        os.fchdir(fd)
    finally:
        os.close(fd)


def validate_file(path, item):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"Kein regulärer Modelldateipfad: {path}")
    if path.stat().st_size != item["size_bytes"]:
        raise RuntimeError(f"Falsche Dateigröße: {path}")
    message(f"Prüfe SHA-256: {path.name} (kann einige Minuten dauern)")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        if stream.read(4) != b"GGUF":
            raise RuntimeError(f"Keine GGUF-Datei: {path}")
        stream.seek(0)
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    actual = digest.hexdigest()
    if actual != item["sha256"]:
        raise RuntimeError(f"SHA-256 stimmt nicht: {path}. Datei bleibt zur Prüfung erhalten.")
    message(f"VERIFIZIERT: {path.name}, {item['size_bytes']} Bytes, SHA-256 {actual}")


def verify_published_pointer(item):
    url = f"https://huggingface.co/{REPOSITORY}/raw/{REVISION}/{item['path']}"
    response = subprocess.run([
        "/usr/bin/curl", "--fail", "--silent", "--show-error", "--location",
        "--proto", "=https", "--proto-redir", "=https", "--connect-timeout", "20",
        "--max-time", "45", url,
    ], check=True, text=True, capture_output=True)
    pointer = response.stdout
    if not re.search(r"^oid sha256:" + re.escape(item["sha256"]) + r"$", pointer, re.M):
        raise RuntimeError("Veröffentlichter LFS-Zeiger passt nicht zur erwarteten SHA-256.")
    if not re.search(r"^size " + str(item["size_bytes"]) + r"$", pointer, re.M):
        raise RuntimeError("Veröffentlichter LFS-Zeiger passt nicht zur erwarteten Größe.")
    return f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{item['path']}?download=true"


def main():
    config = json.loads((HERE / "config.json").read_text())
    source = json.loads((HERE / "sources.json").read_text())
    items = source["gguf_files"]
    if source["gguf_repository"] != REPOSITORY or len(items) != 2:
        raise RuntimeError("Unerwartetes Downloadmanifest.")
    expected_names = {
        "Q4_K_M/GLM-4.5-Air-Q4_K_M-00001-of-00002.gguf",
        "Q4_K_M/GLM-4.5-Air-Q4_K_M-00002-of-00002.gguf",
    }
    if {item["path"] for item in items} != expected_names:
        raise RuntimeError("Unerwartete Modelldateien im Manifest.")
    mount = Path(config["external_mount"])
    destination = Path(config["gguf_directory"])
    check_mount(mount, destination)
    (HERE / "logs").mkdir(exist_ok=True)
    with (HERE / "logs/glm-download.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Ein weiterer GLM-Downloader läuft bereits.")
        message(f"Download freigegeben: 72,98 GB; Ziel {destination}; Revision {REVISION}")
        # Resolve/check both tiny published pointers before any large transfer.
        urls = [verify_published_pointer(item) for item in items]
        remaining = 0
        for item in items:
            final = destination / Path(item["path"]).name
            partial = final.with_name(final.name + ".download")
            for path in (final, partial):
                if path.is_symlink():
                    raise RuntimeError(f"Symlink als Modelldatei abgewiesen: {path}")
            have = final.stat().st_size if final.exists() else partial.stat().st_size if partial.exists() else 0
            if have > item["size_bytes"]:
                raise RuntimeError(f"Vorhandene Datei ist zu groß: {final.name}")
            remaining += item["size_bytes"] - have
        if shutil.disk_usage(mount).free < remaining + RESERVE:
            raise RuntimeError("SSD-Platz reicht nicht für restlichen Download plus 10 GiB Reserve.")
        external_directory(mount, destination)
        for item, url in zip(items, urls):
            check_mount(mount, destination)
            name = Path(item["path"]).name
            final = Path(name)
            partial = Path(name + ".download")
            if final.exists():
                validate_file(final, item)
                continue
            if not partial.exists() or partial.stat().st_size < item["size_bytes"]:
                message(f"Lade {name}; Teil-Datei bleibt extern und ist fortsetzbar.")
                subprocess.run([
                    "/usr/bin/curl", "--fail", "--location", "--progress-bar",
                    "--proto", "=https", "--proto-redir", "=https",
                    "--connect-timeout", "20", "--continue-at", "-",
                    "--header", "Accept-Encoding: identity",
                    "--max-filesize", str(item["size_bytes"]),
                    "--output", str(partial), url,
                ], check=True)
            check_mount(mount, destination)
            validate_file(partial, item)
            if final.exists():
                raise RuntimeError(f"Zieldatei inzwischen vorhanden: {final}")
            partial.rename(final)
        manifest = {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "repository": REPOSITORY, "revision": REVISION,
            "directory": str(destination), "files": items,
            "total_bytes": sum(item["size_bytes"] for item in items),
            "sha256_verified": True, "converted": False, "model_started": False,
        }
        (HERE / "logs/glm-download-complete.json").write_text(json.dumps(manifest, indent=2) + "\n")
        message("FERTIG: Beide GGUF-Teile extern vollständig und SHA-256-verifiziert. Keine Konvertierung, kein Modellstart.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nUnterbrochen. Mit demselben Befehl fortsetzen; .download-Dateien bleiben extern.", file=sys.stderr)
        raise SystemExit(130)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ABBRUCH: {exc}", file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise SystemExit(1)
