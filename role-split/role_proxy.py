#!/usr/bin/env python3
"""role-split: Rollen-Proxy vor dem Router (nur Standardbibliothek).

Der Proxy reicht alle Anfragen unverändert an den Upstream weiter (Router :8080
oder Gedächtnis-Proxy :8091). Nur bei POST auf .../chat/completions schaut er
in die Nachrichten:

* Beginnt eine Nutzernachricht mit @<rolle> (Dateiname in roles/, ohne .md),
  wird der Trigger entfernt und ab dort ist diese Rolle aktiv.
* Weil die UI bei jeder Anfrage den ganzen Verlauf schickt, gilt die zuletzt
  gesetzte Rolle weiter, ohne dass der Proxy Zustand halten muss.
* @aus (oder @off) schaltet die Rolle wieder ab.
* Der Rollen-Prompt plus heutiges Datum wird als erste System-Nachricht
  gesetzt; ein vorhandener System-Prompt des Clients bleibt darunter erhalten.

Rollen-Dateien werden bei jeder Anfrage neu gelesen: Prompt ändern, nächste
Nachricht schicken, fertig.

Aufruf:
  python3 role_proxy.py            # Server starten
  python3 role_proxy.py --check    # Rollen anzeigen und Beispiel trocken durchspielen
"""
from __future__ import annotations

import datetime as _dt
import http.client
import json
import os
import re
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROLES_DIR = Path(os.environ.get("ROLE_DIR", str(HERE / "roles")))
UPSTREAM = os.environ.get("ROLE_UPSTREAM", "http://127.0.0.1:8091")
HOST = os.environ.get("ROLE_HOST", "127.0.0.1")
PORT = int(os.environ.get("ROLE_PORT", "8092"))
LOG_FILE = Path(os.environ.get("ROLE_LOG", str(HERE / "results" / "role_log.jsonl")))

RESET_WORDS = {"aus", "off"}
TRIGGER_RE = re.compile(r"^\s*@([A-Za-z0-9_-]+)(?=\s|$)")
WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

# Header, die beim Weiterreichen nicht kopiert werden. Accept-Encoding bleibt erhalten:
# llama-server liefert die Web-UI nur gzip-komprimiert aus; die Antwort wird
# unverändert (samt Content-Encoding) durchgereicht.
REQ_SKIP = {"host", "content-length", "connection", "keep-alive", "proxy-connection",
            "transfer-encoding", "te", "trailer", "upgrade"}
RESP_SKIP = {"connection", "keep-alive", "proxy-connection", "transfer-encoding",
             "te", "trailer", "upgrade"}


# --------------------------------------------------------------------------- Rollen

def strip_frontmatter(text: str) -> str:
    """Entfernt optionalen YAML-Kopf (--- ... ---) am Dateianfang."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def load_roles(roles_dir: Path = None) -> dict[str, str]:
    """Liest roles/*.md -> {name: prompt}. Dateien mit _ am Anfang werden übersprungen."""
    roles_dir = Path(roles_dir or ROLES_DIR)
    roles: dict[str, str] = {}
    if not roles_dir.is_dir():
        return roles
    for path in sorted(roles_dir.glob("*.md")):
        name = path.stem.lower()
        if name.startswith("_") or name in RESET_WORDS:
            continue
        roles[name] = strip_frontmatter(path.read_text(encoding="utf-8")).strip()
    return roles


def date_line(today: _dt.date | None = None) -> str:
    today = today or _dt.date.today()
    return f"Heutiges Datum: {today.isoformat()} ({WOCHENTAGE[today.weekday()]})."


# ------------------------------------------------------------------ Nachrichten

def _strip_trigger_text(text: str, roles: dict[str, str]) -> tuple[str | None, str]:
    m = TRIGGER_RE.match(text)
    if not m:
        return None, text
    name = m.group(1).lower()
    if name not in roles and name not in RESET_WORDS:
        return None, text  # z. B. "@jemand" in normalem Text bleibt stehen
    rest = text[m.end():].lstrip()
    if not rest:
        rest = "(Rolle abgeschaltet.)" if name in RESET_WORDS else f"(Rolle gewechselt: {name}.)"
    return name, rest


def _strip_trigger(msg: dict, roles: dict[str, str]) -> tuple[str | None, dict]:
    """Prüft eine Nutzernachricht auf Trigger. Gibt (rolle|None, ggf. neue Nachricht)."""
    content = msg.get("content")
    if isinstance(content, str):
        name, rest = _strip_trigger_text(content, roles)
        if name:
            new = dict(msg)
            new["content"] = rest
            return name, new
        return None, msg
    if isinstance(content, list):
        for i, part in enumerate(content):
            if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str):
                name, rest = _strip_trigger_text(part["text"], roles)
                if name:
                    new_parts = list(content)
                    new_parts[i] = dict(part, text=rest)
                    new = dict(msg)
                    new["content"] = new_parts
                    return name, new
                break  # nur der erste Textteil zählt
    return None, msg


def _content_as_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(p.get("text", "") for p in content
                         if isinstance(p, dict) and p.get("type") == "text")
    return ""


def apply_roles(body: dict, roles: dict[str, str],
                today: _dt.date | None = None) -> tuple[dict, str | None]:
    """Setzt den Rollen-Prompt gemäß dem zuletzt gesetzten Trigger.

    Gibt (neuer Body, aktive Rolle oder None) zurück. Ohne aktive Rolle
    werden nur Trigger (@aus) entfernt, der System-Prompt bleibt unverändert.
    """
    msgs = body.get("messages")
    if not isinstance(msgs, list):
        return body, None

    active = None
    new_msgs = []
    for msg in msgs:
        if isinstance(msg, dict) and msg.get("role") == "user":
            name, msg = _strip_trigger(msg, roles)
            if name:
                active = None if name in RESET_WORDS else name
        new_msgs.append(msg)

    if active:
        role_text = roles[active].strip() + "\n\n" + date_line(today)
        if new_msgs and isinstance(new_msgs[0], dict) and new_msgs[0].get("role") == "system":
            existing = _content_as_text(new_msgs[0].get("content")).strip()
            merged = role_text
            if existing:
                merged += "\n\n---\n\n## Weitere Hinweise des Clients\n\n" + existing
            new_msgs[0] = dict(new_msgs[0], content=merged)
        else:
            new_msgs.insert(0, {"role": "system", "content": role_text})

    out = dict(body)
    out["messages"] = new_msgs
    return out, active


def last_user_text(body: dict) -> str:
    for msg in reversed(body.get("messages") or []):
        if isinstance(msg, dict) and msg.get("role") == "user":
            return _content_as_text(msg.get("content"))
    return ""


def log_event(role: str | None, path: str, body: dict) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "zeit": _dt.datetime.now().isoformat(timespec="seconds"),
            "rolle": role,
            "pfad": path,
            "nachrichten": len(body.get("messages") or []),
            "letzte_nutzernachricht": last_user_text(body)[:120],
        }
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:  # Log darf den Proxy nie stoppen
        print(f"[role-split] Log-Fehler: {exc}", file=sys.stderr)


# ------------------------------------------------------------------------ Server

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # Antwortende = Verbindungsende, einfach und streaming-fähig
    server_version = "role-split"

    def do_GET(self):
        self._forward()

    def do_POST(self):
        self._forward()

    def do_PUT(self):
        self._forward()

    def do_DELETE(self):
        self._forward()

    def do_OPTIONS(self):
        self._forward()

    def do_HEAD(self):
        self._forward()

    def log_message(self, fmt, *args):  # knapper als der Standard
        sys.stderr.write("[role-split] " + (fmt % args) + "\n")

    def _forward(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        role = None

        if self.command == "POST" and self.path.split("?", 1)[0].endswith("/chat/completions") and body:
            try:
                data = json.loads(body)
            except ValueError:
                data = None
            if isinstance(data, dict):
                data, role = apply_roles(data, load_roles())
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                log_event(role, self.path, data)

        up = urllib.parse.urlsplit(UPSTREAM)
        conn = http.client.HTTPConnection(up.hostname, up.port or 80, timeout=900)
        headers = {k: v for k, v in self.headers.items() if k.lower() not in REQ_SKIP}
        if body or self.command in ("POST", "PUT"):
            headers["Content-Length"] = str(len(body))
        try:
            conn.request(self.command, self.path, body=body or None, headers=headers)
            resp = conn.getresponse()
        except OSError as exc:
            self.send_error(502, f"Upstream nicht erreichbar: {UPSTREAM} ({exc})")
            return

        self.send_response(resp.status, resp.reason)
        for k, v in resp.getheaders():
            if k.lower() not in RESP_SKIP:
                self.send_header(k, v)
        if role:
            self.send_header("X-Lab-Role", role)
        self.send_header("Connection", "close")
        self.end_headers()

        if self.command != "HEAD":
            try:
                while True:
                    chunk = resp.read1(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
        conn.close()


def banner(roles: dict[str, str]) -> str:
    lines = [
        "=" * 60,
        " role-split · Rollen-Proxy",
        f" lauscht auf : http://{HOST}:{PORT}",
        f" Upstream    : {UPSTREAM}",
        f" Rollen      : {', '.join('@' + r for r in roles) or '(keine gefunden!)'}  · @aus",
        f" Rollen-Dir  : {ROLES_DIR}",
        f" Log         : {LOG_FILE}",
    ]
    if HOST not in ("127.0.0.1", "localhost", "::1"):
        lines.append(" WARNUNG     : nicht nur lokal gebunden – kein Auth-Layer davor!")
    lines.append("=" * 60)
    return "\n".join(lines)


def check() -> int:
    roles = load_roles()
    print(banner(roles))
    if not roles:
        print("Keine Rollen gefunden.", file=sys.stderr)
        return 1
    first = next(iter(roles))
    sample = {"messages": [
        {"role": "system", "content": "Client-Prompt"},
        {"role": "user", "content": f"@{first} Hallo"},
        {"role": "assistant", "content": "…"},
        {"role": "user", "content": "Weiter ohne Trigger"},
    ]}
    out, active = apply_roles(sample, roles)
    print(f"\nTrockenlauf: aktive Rolle = {active}")
    print("System-Prompt (Anfang):")
    print("  " + out["messages"][0]["content"][:200].replace("\n", "\n  ") + " …")
    print("Nutzernachrichten nach Bereinigung:",
          [m["content"] for m in out["messages"] if m["role"] == "user"])
    return 0


def main(argv: list[str]) -> int:
    if "--check" in argv:
        return check()
    print(banner(load_roles()))
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[role-split] beendet.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
