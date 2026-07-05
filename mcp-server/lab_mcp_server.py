#!/usr/bin/env python3
"""
lab_mcp_server.py — MCP-Server fürs llama-server-Lab

Gibt einem MCP-Client (z.B. Claude) Datei-, Such-, Git- und optional
Python-Zugriff — aber ausschließlich innerhalb eines fest definierten
Scope-Ordners (Traversal-geschützt). Kein `shell=True`, kein `os.system`.

Konfiguration über Umgebungsvariablen (alle optional):
    MCP_SCOPE_ROOT   Wurzel des erlaubten Bereichs. Default: Ordner dieser Datei.
    MCP_TRANSPORT    "stdio" | "sse" | "streamable-http". Default: streamable-http.
    MCP_HOST         Bind-Adresse. Default: 127.0.0.1 (nur lokal).
    MCP_PORT         Port. Default: 8787.
    MCP_READONLY     "1" = alle schreibenden Tools deaktivieren. Default: 0.
    MCP_ALLOW_DELETE "1" = delete_file aktiv. Default: 1.
    MCP_ALLOW_PYTHON "1" = run_python aktiv (bricht die Sandbox bewusst auf!).
                     Default: 0 (aus).
    MCP_MAX_READ     Max. Lese-Bytes pro Datei. Default: 2_000_000.

Start (lokal, für Claude-Connector über Tailscale):
    MCP_TRANSPORT=streamable-http python lab_mcp_server.py
    -> erreichbar unter http://127.0.0.1:8787/mcp

SICHERHEIT: Bei Netzwerk-Exposition (Tailscale / MCP_HOST != 127.0.0.1) gilt
llama.cpps "untrusted environment"-Warnung sinngemäss auch hier: dieser Server
hat KEINE eigene Authentifizierung. Nur im privaten Tailnet betreiben und die
Tailscale-ACLs auf das eine erlaubte Gerät (iPad) begrenzen.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# --------------------------------------------------------------------------
# Konfiguration
# --------------------------------------------------------------------------
SCOPE_ROOT = Path(
    os.environ.get("MCP_SCOPE_ROOT", str(Path(__file__).resolve().parent))
).resolve()

TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable-http")
HOST = os.environ.get("MCP_HOST", "127.0.0.1")
PORT = int(os.environ.get("MCP_PORT", "8787"))

READONLY = os.environ.get("MCP_READONLY", "0") == "1"
ALLOW_DELETE = os.environ.get("MCP_ALLOW_DELETE", "1") == "1" and not READONLY
ALLOW_PYTHON = os.environ.get("MCP_ALLOW_PYTHON", "0") == "1"
MAX_READ = int(os.environ.get("MCP_MAX_READ", "2000000"))

mcp = FastMCP("llama-server-lab", host=HOST, port=PORT)


# --------------------------------------------------------------------------
# Scope-Guard — die eine Stelle, die Traversal verhindert
# --------------------------------------------------------------------------
class ScopeError(ValueError):
    """Pfad liegt ausserhalb des erlaubten Scope-Ordners."""


def _resolve_in_scope(rel_path: str) -> Path:
    """
    Loest rel_path relativ zu SCOPE_ROOT auf und stellt sicher, dass das
    Ergebnis WIRKLICH innerhalb von SCOPE_ROOT liegt.

    Deckt ab:
      - '..'-Traversal          -> resolve() normalisiert, Containment-Check kippt
      - absolute Pfade          -> pathlib laesst absolute rechts gewinnen,
                                   resolve() zeigt raus -> Check kippt
      - Symlink-Escape          -> resolve() folgt Symlinks -> Check kippt
    Nicht-existente Zielpfade (z.B. beim Schreiben neuer Dateien) sind ok,
    weil resolve(strict=False) die Elternkette dennoch aufloest.
    """
    if rel_path is None:
        rel_path = "."
    candidate = (SCOPE_ROOT / rel_path).resolve()
    if candidate != SCOPE_ROOT and SCOPE_ROOT not in candidate.parents:
        raise ScopeError(
            f"Pfad '{rel_path}' liegt ausserhalb des Scope-Ordners "
            f"({SCOPE_ROOT}). Zugriff verweigert."
        )
    return candidate


def _rel(p: Path) -> str:
    """Fuer nutzerfreundliche Ausgabe: Pfad relativ zum Scope-Root."""
    try:
        return str(p.relative_to(SCOPE_ROOT)) or "."
    except ValueError:
        return str(p)


# --------------------------------------------------------------------------
# Lese-Tools (immer aktiv)
# --------------------------------------------------------------------------
@mcp.tool()
def list_directory(path: str = ".") -> str:
    """Verzeichnisinhalt innerhalb des Scope-Ordners auflisten.

    Args:
        path: Pfad relativ zum Scope-Root (Default: Root selbst).
    """
    target = _resolve_in_scope(path)
    if not target.exists():
        return f"Nicht gefunden: {_rel(target)}"
    if not target.is_dir():
        return f"Kein Verzeichnis: {_rel(target)}"
    lines = []
    for entry in sorted(target.iterdir(), key=lambda e: (not e.is_dir(), e.name)):
        marker = "d" if entry.is_dir() else "-"
        size = "" if entry.is_dir() else f"  {entry.stat().st_size} B"
        lines.append(f"{marker} {_rel(entry)}{size}")
    return "\n".join(lines) if lines else "(leer)"


@mcp.tool()
def read_file(path: str) -> str:
    """Textdatei innerhalb des Scope-Ordners lesen (bis MCP_MAX_READ Bytes).

    Args:
        path: Pfad relativ zum Scope-Root.
    """
    target = _resolve_in_scope(path)
    if not target.is_file():
        return f"Keine Datei: {_rel(target)}"
    data = target.read_bytes()[: MAX_READ + 1]
    truncated = len(data) > MAX_READ
    data = data[:MAX_READ]
    if b"\x00" in data:
        return f"Binaerdatei ({len(data)} B) — nicht als Text lesbar."
    text = data.decode("utf-8", errors="replace")
    if truncated:
        text += f"\n\n[... abgeschnitten bei {MAX_READ} Bytes ...]"
    return text


@mcp.tool()
def search_files(pattern: str, path: str = ".", max_results: int = 100) -> str:
    """Textsuche (Regex, grep-artig) rekursiv innerhalb des Scope-Ordners.

    Args:
        pattern: Regulaerer Ausdruck.
        path: Startordner relativ zum Scope-Root.
        max_results: Obergrenze der Treffer (Default 100).
    """
    root = _resolve_in_scope(path)
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"Ungueltiges Regex: {e}"
    hits: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as fh:
                for lineno, line in enumerate(fh, 1):
                    if rx.search(line):
                        hits.append(f"{_rel(p)}:{lineno}: {line.rstrip()[:200]}")
                        if len(hits) >= max_results:
                            hits.append(f"[... bei {max_results} Treffern gestoppt ...]")
                            return "\n".join(hits)
        except (OSError, UnicodeError):
            continue
    return "\n".join(hits) if hits else "Keine Treffer."


# --------------------------------------------------------------------------
# Git-Tools (subprocess mit argv-Liste, cwd=Scope; kein shell=True)
# --------------------------------------------------------------------------
def _git(*args: str, timeout: int = 30) -> str:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(SCOPE_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return "git ist nicht installiert / nicht im PATH."
    except subprocess.TimeoutExpired:
        return "git-Aufruf hat das Zeitlimit ueberschritten."
    out = (r.stdout or "") + (r.stderr or "")
    return out.strip() or f"(git rc={r.returncode}, keine Ausgabe)"


@mcp.tool()
def git_status() -> str:
    """git status (kurz) im Scope-Ordner."""
    return _git("status", "--short", "--branch")


@mcp.tool()
def git_diff(path: str = "") -> str:
    """git diff im Scope-Ordner. Optional auf einen Pfad eingrenzen.

    Args:
        path: Optionaler Pfad relativ zum Scope-Root.
    """
    if path:
        _resolve_in_scope(path)  # Scope validieren
        return _git("diff", "--", path)
    return _git("diff")


@mcp.tool()
def git_log(count: int = 10) -> str:
    """Die letzten Commits (oneline) im Scope-Ordner.

    Args:
        count: Anzahl Commits (Default 10).
    """
    return _git("log", f"-{max(1, count)}", "--oneline")


if not READONLY:

    @mcp.tool()
    def git_commit(message: str) -> str:
        """Alle Aenderungen stagen und committen (Scope-Ordner).

        Nutzt `git commit -F <tmpfile>`, damit Sonderzeichen wie '!' in der
        Message keine Shell-Fallen ausloesen.

        Args:
            message: Commit-Nachricht.
        """
        _git("add", "-A")
        fd, tmp = tempfile.mkstemp(suffix=".txt", prefix="commit_msg_")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(message)
            return _git("commit", "-F", tmp)
        finally:
            try:
                os.unlink(tmp)
            except OSError:
                pass


# --------------------------------------------------------------------------
# Schreib-/Loesch-Tools (deaktivierbar via MCP_READONLY / MCP_ALLOW_DELETE)
# --------------------------------------------------------------------------
if not READONLY:

    @mcp.tool()
    def write_file(path: str, content: str) -> str:
        """Datei innerhalb des Scope-Ordners erstellen oder ueberschreiben.
        Fehlende Elternordner (im Scope) werden angelegt.

        Args:
            path: Pfad relativ zum Scope-Root.
            content: Vollstaendiger neuer Dateiinhalt.
        """
        target = _resolve_in_scope(path)
        if target.is_dir():
            return f"Ist ein Verzeichnis: {_rel(target)}"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Geschrieben: {_rel(target)} ({len(content)} Zeichen)"


if ALLOW_DELETE:

    @mcp.tool()
    def delete_file(path: str) -> str:
        """Einzelne Datei innerhalb des Scope-Ordners loeschen.
        Verzeichnisse werden bewusst NICHT geloescht.

        Args:
            path: Pfad relativ zum Scope-Root.
        """
        target = _resolve_in_scope(path)
        if not target.exists():
            return f"Nicht gefunden: {_rel(target)}"
        if target.is_dir():
            return f"Verzeichnis — nicht geloescht: {_rel(target)}"
        target.unlink()
        return f"Geloescht: {_rel(target)}"


# --------------------------------------------------------------------------
# Python-Ausfuehrung (STANDARDMAESSIG AUS — bricht die Sandbox auf)
# --------------------------------------------------------------------------
if ALLOW_PYTHON:

    @mcp.tool()
    def run_python(code: str, timeout: int = 60) -> str:
        """Python-Code in einem Subprozess ausfuehren (cwd = Scope-Root).

        WARNUNG: Dieses Tool umgeht den Datei-Scope-Guard konstruktionsbedingt —
        beliebiger Python-Code kann alles tun, was der Startnutzer darf. Nur im
        vertrauenswuerdigen Lab aktivieren (MCP_ALLOW_PYTHON=1).

        Args:
            code: Python-Quelltext.
            timeout: Zeitlimit in Sekunden (Default 60).
        """
        try:
            r = subprocess.run(
                [sys.executable, "-c", code],
                cwd=str(SCOPE_ROOT),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return f"Abgebrochen: Zeitlimit ({timeout}s) ueberschritten."
        out = (r.stdout or "")
        err = (r.stderr or "")
        parts = []
        if out:
            parts.append("STDOUT:\n" + out)
        if err:
            parts.append("STDERR:\n" + err)
        parts.append(f"(rc={r.returncode})")
        return "\n".join(parts)


# --------------------------------------------------------------------------
# Start
# --------------------------------------------------------------------------
def _banner() -> None:
    print("=" * 60, file=sys.stderr)
    print(" llama-server-lab MCP", file=sys.stderr)
    print(f"  Scope-Root : {SCOPE_ROOT}", file=sys.stderr)
    print(f"  Transport  : {TRANSPORT}", file=sys.stderr)
    if TRANSPORT != "stdio":
        print(f"  Bind       : {HOST}:{PORT}", file=sys.stderr)
    print(f"  readonly   : {READONLY}", file=sys.stderr)
    print(f"  delete     : {ALLOW_DELETE}", file=sys.stderr)
    print(f"  run_python : {ALLOW_PYTHON}", file=sys.stderr)
    if TRANSPORT != "stdio" and HOST not in ("127.0.0.1", "localhost"):
        print(
            "  ! WARNUNG: gebunden ausserhalb localhost — kein Auth-Layer!\n"
            "  ! Nur im privaten Tailnet mit Geraete-ACL betreiben.",
            file=sys.stderr,
        )
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    _banner()
    mcp.run(transport=TRANSPORT)
