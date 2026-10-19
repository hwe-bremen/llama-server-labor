#!/usr/bin/env python3
"""Isolated Slipstream preparation; stdlib only; never downloads or converts.

smoke / serve-empty start a model-less router with an EMPTY private model dir.
Only owned Popen handles are terminated. Stop foreground serving with Ctrl+C.
glm-plan prints future commands, it NEVER executes them.
"""
from __future__ import annotations

import argparse
import errno
import gzip
import json
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from urllib.error import HTTPError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CFG = json.loads((HERE / "config.json").read_text())
LAB_PORTS = (8080, 8091, 8092, 8787)


def local_path(value):
    p = Path(value).expanduser()
    return p if p.is_absolute() else HERE / p


def listeners(port):
    r = subprocess.run(["/usr/sbin/lsof", "-nP", f"-iTCP:{port}",
                        "-sTCP:LISTEN", "-Fpcn"], capture_output=True, text=True)
    if r.returncode not in (0, 1) or r.stderr.strip():
        raise RuntimeError(f"Listener-Prüfung nicht verlässlich: {r.stderr.strip()}")
    return r.stdout.strip()


def http_get(port, path):
    # Explicitly bypass inherited HTTP proxies for local checks.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    # Bundled llama-server UI is gzip-only and returns 415 without this header.
    headers = {"Accept-Encoding": "gzip", "Accept": "text/html"} if path == "/" else {}
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}", headers=headers)
    try:
        with opener.open(request, timeout=3) as r:
            body = r.read(8 * 1024 * 1024 + 1)
            if len(body) > 8 * 1024 * 1024:
                raise RuntimeError("HTTP-Prüfantwort größer als 8 MiB; nicht still abschneiden.")
            if r.headers.get("Content-Encoding", "").lower() == "gzip":
                body = gzip.decompress(body)
            return r.status, body
    except HTTPError as e:
        return e.code, e.read(4096)
    except OSError as exc:
        reason = getattr(exc, "reason", exc)
        if getattr(reason, "errno", None) in (errno.EPERM, errno.EACCES):
            raise RuntimeError("localhost-Zugriff durch Umgebung blockiert; "
                               "kein Engine-Fehler, kein Wiederholungsversuch.") from exc
        raise


def lab_snapshot():
    result = {}
    for port in LAB_PORTS:
        entry = {"listeners": listeners(port)}
        try:
            path = "/health" if port != 8787 else "/mcp"
            status, _ = http_get(port, path)
            entry["http_status"] = status
        except (OSError, RuntimeError) as exc:
            entry["http_error"] = str(exc)
        result[str(port)] = entry
    return result


def mounted_external():
    mount = Path(CFG["external_mount"])
    if mount.is_symlink() or not mount.is_mount():
        raise RuntimeError(f"Externes Volume nicht als eigener Mount bestätigt: {mount}")
    return mount


def binaries():
    bundle = local_path(os.environ.get("SLIPSTREAM_BUNDLE", CFG["bundle"]))
    info = bundle / "Contents/Info.plist"
    if not info.is_file():
        raise RuntimeError(f"Slipstream-Bundle fehlt: {bundle}; kein Homebrew-Fallback.")
    meta = plistlib.loads(info.read_bytes())
    if meta.get("CFBundleShortVersionString") != "0.3.4":
        raise RuntimeError("Diese Konfiguration ist nur für das geprüfte Bundle 0.3.4 vorbereitet.")
    resources = bundle / "Contents/Resources"
    found = []
    for name in ("llama-server", "pgrn-convert"):
        candidates = [resources / "resources" / name, resources / name]
        matches = [p for p in candidates if p.is_file() and os.access(p, os.X_OK)]
        if not matches:
            raise RuntimeError(f"Gebündelte ausführbare Datei fehlt: {name} unter {resources}")
        found.append(matches[0])
    return found


def capabilities():
    server, converter = binaries()
    logs = HERE / "logs"
    logs.mkdir(exist_ok=True)
    outputs = {}
    for label, argv in (("engine-version", [server, "--version"]),
                        ("engine-help", [server, "--help"]),
                        ("converter-help", [converter, "--help"])):
        r = subprocess.run(list(map(str, argv)), capture_output=True, text=True, timeout=30)
        text = r.stdout + r.stderr
        (logs / f"{label}.txt").write_text(text)
        if r.returncode:
            raise RuntimeError(f"{label} fehlgeschlagen: Exit {r.returncode}; siehe logs/")
        outputs[label] = text
    if "--pgrn" not in outputs["engine-help"]:
        raise RuntimeError("Engine bietet kein --pgrn: kein bestätigter Slipstream-Server.")
    print(outputs["engine-version"].strip())
    print(f"Engine: {server}\nKonverter: {converter}\nHilfe gespeichert in {logs}")
    return server, converter, outputs["engine-help"]


def check():
    print(json.dumps({"lab": lab_snapshot(), "experiment_ports": {
        str(p): listeners(p) or "frei" for p in (CFG["engine_port"], CFG["role_port"])
    }}, ensure_ascii=False, indent=2))
    for path in (HERE, mounted_external()):
        print(f"Frei: {path}: {shutil.disk_usage(path).free / 2**30:.2f} GiB")
    server, converter = binaries()
    print(f"Bundle gefunden: {server}, {converter}; noch nicht gestartet")


def wait_listener(process, port, label):
    print(f"{label}: Prozess erzeugt, eigene PID {process.pid}", flush=True)
    deadline = time.monotonic() + 10
    while True:
        if process.poll() is not None:
            raise RuntimeError(f"{label}: Prozess beendet (Exit {process.returncode}); Log prüfen.")
        data = listeners(port)
        if data:
            lines = data.splitlines()
            pids = {int(line[1:]) for line in lines if line.startswith("p")}
            addresses = {line[1:] for line in lines if line.startswith("n")}
            if pids != {process.pid} or addresses != {f"127.0.0.1:{port}"}:
                raise RuntimeError(f"{label}: Listener gehört nicht ausschließlich zum "
                                   f"eigenen Prozess auf 127.0.0.1:{port}: {data}")
            print(f"{label}: eigener Listener 127.0.0.1:{port} bestätigt", flush=True)
            return
        if time.monotonic() >= deadline:
            raise RuntimeError(f"{label}: kein Listener nach 10 s; Log prüfen.")
        time.sleep(0.2)


def expected_no_model(status, body):
    # Loading/initializing messages are not treated as proof of a ready empty router.
    text = body.decode("utf-8", "replace").lower()
    return status == 503 and any(s in text for s in
                                ("no model loaded", "no models loaded", "no models available"))


def supervise(smoke):
    engine_port, role_port = CFG["engine_port"], CFG["role_port"]
    if engine_port == role_port or any(p in LAB_PORTS or not 1024 <= p <= 65535
                                      for p in (engine_port, role_port)):
        raise RuntimeError("Experimentports müssen verschieden und außerhalb der Laborports liegen.")
    for port in (engine_port, role_port):
        if listeners(port):
            raise RuntimeError(f"Port {port} belegt; kein Prozess wird gestoppt. config.json anpassen.")
    server, _, help_text = capabilities()
    flags = ("--host", "--port", "--models-dir", "--models-max",
             "--no-models-autoload", "--ui-mcp-proxy")
    missing = [flag for flag in flags if flag not in help_text]
    if missing:
        raise RuntimeError(f"Modellloser Start nicht qualifiziert; fehlende Optionen: {missing}")
    empty = HERE / "empty-models"
    empty.mkdir(exist_ok=True)
    if any(empty.iterdir()):
        raise RuntimeError("empty-models ist nicht leer; Start abgebrochen.")
    # --models-dir is additive: llama-server also discovers shared cache presets.
    # Isolate that second source without altering the existing Lab's environment.
    cache = HERE / "empty-cache"
    cache.mkdir(exist_ok=True)
    if cache.is_symlink() or any(cache.iterdir()):
        raise RuntimeError("empty-cache muss ein eigenes leeres Verzeichnis sein.")
    before = lab_snapshot()
    owned = []
    log_handles = []
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("LLAMA_ARG_", "PGRN_", "ROLE_"))}
    env["LLAMA_CACHE"] = str(cache) + os.sep
    try:
        engine_log = (HERE / "logs/engine.log").open("w")
        log_handles.append(engine_log)
        cmd = [str(server), "--host", "127.0.0.1", "--port", str(engine_port),
               "--models-dir", str(empty), "--models-max", "1", "--no-models-autoload",
               "--ui-mcp-proxy"]
        print("Start ohne Modell:", shlex.join(cmd), flush=True)
        print(f"Isolierter Cache: LLAMA_CACHE={env['LLAMA_CACHE']}", flush=True)
        owned.append(subprocess.Popen(cmd, env=env, stdout=engine_log,
                                      stderr=subprocess.STDOUT, start_new_session=True))
        wait_listener(owned[0], engine_port, "Engine")
        deadline = time.monotonic() + 30
        while True:
            if owned[0].poll() is not None:
                raise RuntimeError("Engine beendet; siehe logs/engine.log")
            try:
                status, body = http_get(engine_port, "/health")
                if status == 200 or expected_no_model(status, body):
                    print(f"Engine: HTTP /health {status}: "
                          f"{body[:200].decode('utf-8', 'replace')}", flush=True)
                    break
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("Engine nach 30 s nicht bereit.")
            time.sleep(0.2)
        role_env = dict(env, ROLE_HOST="127.0.0.1", ROLE_PORT=str(role_port),
                        ROLE_UPSTREAM=f"http://127.0.0.1:{engine_port}",
                        ROLE_LOG=str(HERE / "logs/roles.jsonl"),
                        ROLE_DIR=str(ROOT / "role-split/roles"))
        role_log = (HERE / "logs/role-proxy.log").open("w")
        log_handles.append(role_log)
        owned.append(subprocess.Popen([sys.executable, str(ROOT / "role-split/role_proxy.py")],
                                      env=role_env, stdout=role_log, stderr=subprocess.STDOUT,
                                      start_new_session=True))
        wait_listener(owned[-1], role_port, "Rollen-Proxy")
        deadline = time.monotonic() + 10
        while True:
            if owned[-1].poll() is not None:
                raise RuntimeError("Rollen-Proxy beendet; siehe logs/role-proxy.log")
            try:
                status, body = http_get(role_port, "/health")
                if status == 200 or expected_no_model(status, body):
                    print(f"Rollen-Proxy: HTTP /health {status}", flush=True)
                    break
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise RuntimeError("Rollen-Proxy nach 10 s nicht bereit.")
            time.sleep(0.2)
        for port in (engine_port, role_port):
            for path in ("/health", "/v1/models", "/props", "/"):
                status, body = http_get(port, path)
                print(f"GET :{port}{path}: HTTP {status}, {len(body)} Bytes", flush=True)
                label = path.strip('/').replace('/', '-') or 'index'
                (HERE / "logs" / f"http-{port}-{label}.txt").write_bytes(body)
                if status != 200:
                    if expected_no_model(status, body):
                        print("Erwarteter Hinweis: kein Modell geladen (kein Prozess-Startfehler).",
                              flush=True)
                        if path != "/v1/models":
                            continue
                    raise RuntimeError(f"HTTP/UI-Endpunkt :{port}{path} nicht qualifiziert; "
                                       "dies allein belegt keinen Prozess-Startfehler.")
                if path == "/v1/models" and json.loads(body).get("data") != []:
                    raise RuntimeError("Modellloser Test meldet unerwartete Modelle.")
                if path == "/" and b"<html" not in body.lower():
                    raise RuntimeError(f"Web-UI :{port} liefert kein erkennbares HTML-Dokument.")
        print("Modellloser HTTP/UI-Test bestanden. Keine Inferenz/PGRN/GLM-Bestätigung.", flush=True)
        if not smoke:
            print(f"Web-UI: http://127.0.0.1:{role_port}; Stop: Ctrl+C hier.", flush=True)
            while all(p.poll() is None for p in owned):
                time.sleep(0.5)
            raise RuntimeError("Ein Experimentprozess wurde unerwartet beendet.")
    finally:
        for p in reversed(owned):
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
        for handle in log_handles:
            handle.close()
        after = lab_snapshot()
        (HERE / "logs/lab-before-after.json").write_text(json.dumps(
            {"before": before, "after": after}, ensure_ascii=False, indent=2))
        print("Laborprüfung vorher/nachher:", "identisch" if before == after else
              "abweichend — logs/lab-before-after.json prüfen", flush=True)
        for port in (engine_port, role_port):
            print(f"Port {port} nach Stop: {listeners(port) or 'frei'}")


def glm_plan():
    source = json.loads((HERE / "sources.json").read_text())
    compatibility = source.get("gguf_converter_check", {})
    if compatibility.get("supported") is False:
        raise RuntimeError("Diese konkrete GGUF-Ausgabe ist laut Konverter-Dry-run inkompatibel: "
                           + compatibility.get("error", "nicht unterstützte Expertentypen")
                           + ". Keine Konvertierung oder Modellstart-Empfehlung.")
    mounted_external()
    server, converter = binaries()
    directory = Path(CFG["gguf_directory"])
    first = directory / "GLM-4.5-Air-Q4_K_M-00001-of-00002.gguf"
    pgrn = local_path(CFG["pgrn"])
    s = CFG["provisional_glm_settings"]
    print("NUR PLAN — keine Konvertierung und kein Modellstart:")
    print(shlex.join([str(converter), "--input", str(first), "--dry-run"]))
    print("Erst nach separater Freigabe und verifizierten installierten Optionen:")
    print(shlex.join([str(server), "--model", str(first), "--pgrn", str(pgrn),
          "--host", "127.0.0.1", "--port", str(CFG["engine_port"]),
          "--alias", CFG["model_alias"], "--jinja", "--ui-mcp-proxy",
          "--gpu-layers", "99", "--ctx-size", str(s["context"]),
          "--parallel", "1", "--pgrn-cache-gb", str(s["expert_cache_gib"]),
          "--pgrn-headroom-gb", str(s["headroom_gib"]),
          "--pgrn-io-threads", str(s["io_threads"]), "--cache-ram", "512"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("check", "capabilities", "smoke", "serve-empty", "glm-plan"))
    action = parser.parse_args().action
    def interrupted(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        if action == "check":
            check()
        elif action == "capabilities":
            capabilities()
        elif action == "glm-plan":
            glm_plan()
        else:
            supervise(action == "smoke")
    except KeyboardInterrupt:
        print("Experiment beendet; nur eigene gestartete Prozesse wurden bereinigt.")
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ABBRUCH: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
