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
    MCP_ALLOW_WEB    "1" = web_search aktiv. Default: 1.
    MCP_ALLOW_GITLOG "0" = git_log aus (Review-Eval: Fix-Commits verraten sonst
                     die Loesung). Default: 1.
    MCP_NAME         Servername in MCP-Clients. Default: llama-server-lab.
    MCP_DENY         Sperrpfade relativ zum Scope-Root, kommagetrennt. Default: leer.
    MCP_WRITE_ROOTS  Schreibgrenze: Ordner relativ zum Scope-Root, kommagetrennt.
                     Wenn gesetzt, duerfen write_file/delete_file nur darunter
                     schreiben, und git_commit ist abgeschaltet. Lesen bleibt im
                     ganzen Scope erlaubt. Default: leer (ganzer Scope).
                     Default: 0 (aus).
    MCP_MAX_READ     Max. Lese-Bytes pro Datei. Default: 2_000_000.
    MCP_MAX_APPEND   Max. Zeichen je append_file-Aufruf. Default: 20000.

Start (lokal, für Claude-Connector über Tailscale):
    MCP_TRANSPORT=streamable-http python lab_mcp_server.py
    -> erreichbar unter http://127.0.0.1:8787/mcp

SICHERHEIT: Bei Netzwerk-Exposition (Tailscale / MCP_HOST != 127.0.0.1) gilt
llama.cpps "untrusted environment"-Warnung sinngemäss auch hier: dieser Server
hat KEINE eigene Authentifizierung. Nur im privaten Tailnet betreiben und die
Tailscale-ACLs auf das eine erlaubte Gerät (iPad) begrenzen.
"""
from __future__ import annotations

import base64
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
ALLOW_WEB = os.environ.get("MCP_ALLOW_WEB", "1") == "1"
# Eval-Laeufe: git_log aus, damit Fix-Commits die Loesung nicht verraten.
ALLOW_GITLOG = os.environ.get("MCP_ALLOW_GITLOG", "1") == "1"
SERVER_NAME = os.environ.get("MCP_NAME", "llama-server-lab")
# Sperrliste: gesperrte Pfade (und alles darunter), relativ zum Scope-Root.
DENY_PATHS = [
    (SCOPE_ROOT / p.strip()).resolve()
    for p in os.environ.get("MCP_DENY", "").split(",")
    if p.strip()
]
# Schreibgrenze (role-split): Review-Instanz darf nur Uebergabe-Dokumente schreiben.
WRITE_ROOTS = [
    (SCOPE_ROOT / p.strip()).resolve()
    for p in os.environ.get("MCP_WRITE_ROOTS", "").split(",")
    if p.strip()
]

mcp = FastMCP(SERVER_NAME, host=HOST, port=PORT)


def _tool_if(enabled: bool):
    """Wie @mcp.tool(), registriert das Tool aber nur, wenn enabled True ist."""
    if enabled:
        return mcp.tool()
    return lambda fn: fn


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
    if _is_denied(candidate):
        raise ScopeError(
            f"Pfad '{rel_path}' ist gesperrt (MCP_DENY). Zugriff verweigert."
        )
    return candidate


def _in_scope(p: Path) -> bool:
    """True, wenn der (bereits aufgeloeste) Pfad p innerhalb von SCOPE_ROOT liegt."""
    return p == SCOPE_ROOT or SCOPE_ROOT in p.parents


def _is_denied(p: Path) -> bool:
    """True, wenn p ein gesperrter Pfad ist oder darunter liegt."""
    return any(p == d or d in p.parents for d in DENY_PATHS)


def _check_writable(p: Path, rel_path: str) -> None:
    """Wirft ScopeError, wenn MCP_WRITE_ROOTS gesetzt ist und p nicht darunter liegt."""
    if WRITE_ROOTS and not any(p == r or r in p.parents for r in WRITE_ROOTS):
        allowed = ", ".join(_rel(r) for r in WRITE_ROOTS)
        raise ScopeError(
            f"Pfad '{rel_path}' liegt ausserhalb von MCP_WRITE_ROOTS ({allowed}). "
            f"Schreiben verweigert."
        )


# Verdikte sind Messergebnisse: nie ueberschreiben oder loeschen (Befund 17.10.:
# Tiefenpruefung hat das Verdikt aus Lauf 1 unter gleichem Namen ersetzt).
PROTECTED_PATTERNS = ("verdict_*.md",)
# Vorgaben der Kette: Modelle lesen sie, aendern sie aber nie (Befund 18.10.: Qwen3-Next hat die
# Verdikt-Vorlage ueberschrieben). Anforderung (Proxy) und Quellen (kette.py) schreibt die Maschine.
READONLY_PATTERNS = ("_vorlage_*.md", "anforderung_*.md", "quellen_*.md")
# Anhaengen braucht eine Obergrenze je Aufruf, damit ein Modell in einer Schleife die Datei
# nicht unbegrenzt aufblaeht.
MAX_APPEND = int(os.environ.get("MCP_MAX_APPEND", "20000"))


def _protected(p: Path) -> bool:
    return any(p.match(pat) for pat in PROTECTED_PATTERNS)


def _readonly(p: Path) -> bool:
    return any(p.match(pat) for pat in READONLY_PATTERNS)


def _decode(content: str, content_b64: str) -> str:
    """Klartext oder Base64 (Vorrang) -> Text. Wirft ValueError mit lesbarer Meldung."""
    if not content_b64:
        return content
    try:
        raw = base64.b64decode(content_b64, validate=True)
    except Exception as e:
        raise ValueError(f"content_b64 ist kein gueltiges Base64: {e}") from e
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"content_b64 dekodiert nicht als UTF-8: {e}") from e


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


# Ab dieser Laenge haengt read_file ohne Bereich einen Hinweis an (Kontext schonen, 25.10.).
LANG_ZEILEN = 300


@mcp.tool()
def read_file(path: str, start_line: int = 0, end_line: int = 0) -> str:
    """Textdatei innerhalb des Scope-Ordners lesen (bis MCP_MAX_READ Bytes).

    Ohne start_line/end_line: ganze Datei. Mit Bereich: nur diese Zeilen,
    jede mit Zeilennummer ("123| text"). Grosse Dateien gezielt lesen:
    erst search_files (liefert Zeilennummern), dann read_file mit Bereich.

    Args:
        path: Pfad relativ zum Scope-Root.
        start_line: Erste Zeile (ab 1). 0 = ab Anfang.
        end_line: Letzte Zeile (einschliesslich). 0 = bis Ende.
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
    try:
        start_line = int(start_line or 0)
        end_line = int(end_line or 0)
    except (TypeError, ValueError):
        return "start_line und end_line muessen ganze Zahlen sein."
    zeilen = text.splitlines()
    gesamt = len(zeilen)
    if start_line or end_line:
        if start_line < 0 or end_line < 0:
            return "start_line und end_line duerfen nicht negativ sein."
        von = max(start_line, 1)
        bis = end_line if end_line else gesamt
        if bis < von:
            return f"Leerer Bereich: start_line {von} > end_line {bis}."
        if von > gesamt:
            return f"{_rel(target)} hat nur {gesamt} Zeilen (start_line {von})."
        bis = min(bis, gesamt)
        breite = len(str(bis))
        auszug = "\n".join(f"{n:>{breite}}| {zeilen[n - 1]}" for n in range(von, bis + 1))
        kopf = f"[{_rel(target)}: Zeilen {von}–{bis} von {gesamt}]"
        if truncated:
            kopf += f" [Datei bei {MAX_READ} Bytes abgeschnitten]"
        return kopf + "\n" + auszug
    if truncated:
        text += f"\n\n[... abgeschnitten bei {MAX_READ} Bytes ...]"
    if gesamt > LANG_ZEILEN:
        text += (f"\n\n[Hinweis: {gesamt} Zeilen gelesen. Fuer Ausschnitte: search_files fuer die "
                 f"Zeilennummer, dann read_file mit start_line/end_line.]")
    return text


@mcp.tool()
def search_files(
    pattern: str, path: str = ".", max_results: int = 100, ignore_case: bool = False
) -> str:
    """Textsuche (Regex, grep-artig) innerhalb des Scope-Ordners.

    Args:
        pattern: Regulaerer Ausdruck.
        path: Ordner (rekursiv) ODER einzelne Datei, relativ zum Scope-Root.
        max_results: Obergrenze der Treffer (Default 100).
        ignore_case: Gross-/Kleinschreibung ignorieren (Default False).
    """
    root = _resolve_in_scope(path)
    if not root.exists():
        return f"Nicht gefunden: {_rel(root)}"
    try:
        rx = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
    except re.error as e:
        return f"Ungueltiges Regex: {e}"
    hits: list[str] = []
    searched = 0
    # Befund 16.10.: path=<Datei> lieferte frueher still "Keine Treffer",
    # weil rglob auf einer Datei nichts findet.
    candidates = [root] if root.is_file() else root.rglob("*")
    for p in candidates:
        if not p.is_file():
            continue
        # rglob kennt weder Scope noch Sperrliste: pro Datei pruefen.
        # Faengt Symlinks nach draussen und Suchen ab einem Elternordner.
        rp = p.resolve()
        if not _in_scope(rp) or _is_denied(p) or _is_denied(rp):
            continue
        searched += 1
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
    if hits:
        return "\n".join(hits)
    return f"Keine Treffer ({searched} Datei(en) durchsucht: {_rel(root)})."


@_tool_if(ALLOW_WEB)
def web_search(query: str, max_results: int = 10) -> str:
    """Web-Suche mit DuckDuckGo.

    Fuehrt eine Websuche durch und gibt die Top-Ergebnisse zurueck,
    inkl. Titel, URL und kurzer Beschreibung.

    Args:
        query: Suchbegriff oder Suchfrage.
        max_results: Anzahl der zurueckgegebenen Ergebnisse (Default: 10, Max: 20).
    """
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return "Fehler: duckduckgo-search ist nicht installiert. Fuehre 'pip install duckduckgo-search' aus."

    try:
        max_results = min(max(max_results, 1), 20)  # Begrenzung auf 1-20 Ergebnisse
        with DDGS() as ddgs:
            results = list(ddgs.text(keywords=query, max_results=max_results))

        if not results:
            return f"Keine Ergebnisse fuer '{query}' gefunden."

        lines = []
        lines.append(f"Suchergebnisse fuer '{query}':\n")
        for i, r in enumerate(results, 1):
            title = r.get("title", "Kein Titel")
            url = r.get("href", "Keine URL")
            body = r.get("body", "Keine Beschreibung")
            lines.append(f"{i}. {title}")
            lines.append(f"   URL: {url}")
            if body:
                lines.append(f"   {body[:200]}")
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        return f"Fehler bei der Websuche: {e}"


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


@_tool_if(ALLOW_GITLOG)
def git_log(count: int = 10) -> str:
    """Die letzten Commits (oneline) im Scope-Ordner.

    Args:
        count: Anzahl Commits (Default 10).
    """
    return _git("log", f"-{max(1, count)}", "--oneline")


# git_commit staged alles (git add -A) und wuerde die Schreibgrenze aushebeln.
if not READONLY and not WRITE_ROOTS:

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
    def write_file(path: str, content: str = "", content_b64: str = "") -> str:
        """Datei innerhalb des Scope-Ordners erstellen oder ueberschreiben.
        Fehlende Elternordner (im Scope) werden angelegt.

        Fuer Inhalte mit vielen Anfuehrungszeichen/Escapes (z.B. Python-Code
        mit Docstrings und f-Strings) `content_b64` verwenden: Base64-
        kodierter UTF-8-Inhalt. Umgeht JSON-Escaping-Fehler kleinerer/
        lokaler Modelle strukturell, da Base64 keine Quotes/Backslashes/
        Newlines enthaelt. Ist `content_b64` gesetzt, hat es Vorrang vor
        `content`.

        Args:
            path: Pfad relativ zum Scope-Root.
            content: Vollstaendiger neuer Dateiinhalt (Klartext).
            content_b64: Vollstaendiger neuer Dateiinhalt, Base64-kodiert.
        """
        target = _resolve_in_scope(path)
        _check_writable(target, path)
        if target.is_dir():
            return f"Ist ein Verzeichnis: {_rel(target)}"
        if _readonly(target):
            return (f"Verweigert: {_rel(target)} ist eine Vorgabe der Kette (Vorlage, Anforderung "
                    f"oder Quellen) und wird von Modellen nie geschrieben.")
        if target.exists() and _protected(target):
            return (f"Verweigert: {_rel(target)} existiert bereits und ist geschuetzt "
                    f"(Verdikte werden nie ueberschrieben). Weitere Abschnitte mit append_file "
                    f"anhaengen; nur fuer ein ganz neues Verdikt einen neuen Namen (_2.md) waehlen.")
        try:
            text = _decode(content, content_b64)
        except ValueError as e:
            return f"Fehler: {e}"

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return f"Geschrieben: {_rel(target)} ({len(text)} Zeichen)"

    @mcp.tool()
    def replace_in_file(path: str, old_text: str, new_text: str = "") -> str:
        """Eine Textstelle in einer Datei ersetzen, ohne die ganze Datei neu zu schreiben.

        Fuer kleine Korrekturen an langen Dokumenten (Spec, Handover): old_text muss GENAU EINMAL
        in der Datei vorkommen (inkl. Leerzeichen/Zeilenumbruechen), sonst wird nichts geaendert.
        new_text leer = Stelle loeschen. Verdikte und Vorgaben der Kette sind ausgenommen.

        Args:
            path: Pfad relativ zum Scope-Root.
            old_text: Exakt zu ersetzender Text (einmalig in der Datei).
            new_text: Ersatztext.
        """
        target = _resolve_in_scope(path)
        _check_writable(target, path)
        if not target.is_file():
            return f"Nicht gefunden: {_rel(target)}"
        if _readonly(target):
            return (f"Verweigert: {_rel(target)} ist eine Vorgabe der Kette (Vorlage, Anforderung "
                    f"oder Quellen) und wird von Modellen nie geschrieben.")
        if _protected(target):
            return f"Verweigert: {_rel(target)} ist ein Verdikt – nur append_file erlaubt."
        if not old_text:
            return "Fehler: old_text ist leer."
        if len(old_text) > MAX_APPEND or len(new_text) > MAX_APPEND:
            return f"Verweigert: old_text/new_text > {MAX_APPEND} Zeichen. Kleinere Stellen ersetzen."
        text = target.read_text(encoding="utf-8")
        anzahl = text.count(old_text)
        if anzahl != 1:
            return (f"Nichts geaendert: old_text kommt {anzahl}-mal vor (muss genau 1-mal). "
                    f"Mehr umgebenden Text mitgeben bzw. exakt aus der Datei kopieren.")
        neu = text.replace(old_text, new_text, 1)
        fd, tmp = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(neu)
            os.replace(tmp, target)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        return f"Ersetzt in {_rel(target)}: {len(old_text)} -> {len(new_text)} Zeichen (jetzt {len(neu)})"

    @mcp.tool()
    def append_file(path: str, content: str = "", content_b64: str = "") -> str:
        """Text an eine Datei ANHAENGEN (legt sie an, falls sie fehlt). Bestehender Inhalt bleibt.

        Zum abschnittsweisen Speichern langer Dokumente (Verdikt, Spec): erst mit write_file
        oder append_file den ersten Abschnitt anlegen, dann jeden weiteren Abschnitt einzeln
        anhaengen. Bricht ein Aufruf ab, sind die frueheren Abschnitte schon gespeichert.
        Auch fuer bestehende Verdikte erlaubt (nur anhaengen, nie ersetzen).
        Zwischen zwei Abschnitten wird ein Zeilenumbruch eingefuegt, falls keiner da ist.

        Args:
            path: Pfad relativ zum Scope-Root.
            content: Anzuhaengender Text (Klartext), hoechstens MCP_MAX_APPEND Zeichen.
            content_b64: Anzuhaengender Text, Base64-kodiert (Vorrang vor content).
        """
        target = _resolve_in_scope(path)
        _check_writable(target, path)
        if target.is_dir():
            return f"Ist ein Verzeichnis: {_rel(target)}"
        if _readonly(target):
            return (f"Verweigert: {_rel(target)} ist eine Vorgabe der Kette (Vorlage, Anforderung "
                    f"oder Quellen) und wird von Modellen nie geschrieben.")
        try:
            text = _decode(content, content_b64)
        except ValueError as e:
            return f"Fehler: {e}"
        if not text:
            return "Nichts angehaengt: Inhalt ist leer."
        if len(text) > MAX_APPEND:
            return (f"Verweigert: {len(text)} Zeichen > {MAX_APPEND} je Aufruf. "
                    f"In kleinere Abschnitte teilen.")
        target.parent.mkdir(parents=True, exist_ok=True)
        vorher = target.read_text(encoding="utf-8") if target.exists() else ""
        trenner = "\n" if vorher and not vorher.endswith("\n") else ""
        with target.open("a", encoding="utf-8") as fh:
            fh.write(trenner + text)
        gesamt = len(vorher) + len(trenner) + len(text)
        return f"Angehaengt: {_rel(target)} (+{len(text)} Zeichen, jetzt {gesamt})"


if ALLOW_DELETE:

    @mcp.tool()
    def delete_file(path: str) -> str:
        """Einzelne Datei innerhalb des Scope-Ordners loeschen.
        Verzeichnisse werden bewusst NICHT geloescht.

        Args:
            path: Pfad relativ zum Scope-Root.
        """
        target = _resolve_in_scope(path)
        _check_writable(target, path)
        if not target.exists():
            return f"Nicht gefunden: {_rel(target)}"
        if target.is_dir():
            return f"Verzeichnis — nicht geloescht: {_rel(target)}"
        if _protected(target) or _readonly(target):
            return f"Verweigert: {_rel(target)} ist geschuetzt (Verdikte und Vorgaben werden nie geloescht)."
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
    print(f"  web_search : {ALLOW_WEB}", file=sys.stderr)
    print(f"  git_log    : {ALLOW_GITLOG}", file=sys.stderr)
    print(f"  name       : {SERVER_NAME}", file=sys.stderr)
    print(f"  deny       : {[_rel(d) for d in DENY_PATHS] or '-'}", file=sys.stderr)
    print(f"  write_roots: {[_rel(r) for r in WRITE_ROOTS] or '- (ganzer Scope)'}", file=sys.stderr)
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
