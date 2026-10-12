#!/usr/bin/env python3
"""Mitschnitt-Proxy: prueft, welche Tool-Schemas ein Agent (OpenCode, Cline, ...) an llama-server
schickt und ob darin ein JSON-Schema-`pattern` nicht mit ^ beginnt und mit $ endet.

llama-server (--jinja) baut aus den Tool-Schemas eine Grammatik und lehnt unverankerte Patterns
mit 400 ab: "JSON schema conversion failed: Pattern must start with '^' and end with '$'".
Die Meldung nennt das Tool nicht – dieser Proxy tut es.

  python3 scripts/toolcheck.py            # lauscht auf 127.0.0.1:8089, reicht an 127.0.0.1:8080 weiter
  ROUTER=http://127.0.0.1:8091 python3 scripts/toolcheck.py

Im Client die baseURL voruebergehend auf http://127.0.0.1:8089/v1 setzen, eine Frage stellen,
hier die Zeile "[toolcheck] N Tools; unverankert: [...]" lesen, Tool in der Client-Config
abschalten (OpenCode: "tools": {"<name>": false}), baseURL zuruecksetzen, Ctrl+C.
Nur localhost, nur Durchreichen, es wird nichts gespeichert.
"""
import http.server
import json
import os
import urllib.error
import urllib.request

ROUTER = os.environ.get("ROUTER", "http://127.0.0.1:8080")
PORT = int(os.environ.get("PORT", "8089"))


def scan(o, path, hits):
    if isinstance(o, dict):
        p = o.get("pattern")
        if isinstance(p, str) and not (p.startswith("^") and p.endswith("$")):
            hits.append(f"{path}: pattern={p!r}")
        for k, v in o.items():
            scan(v, f"{path}.{k}", hits)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            scan(v, f"{path}[{i}]", hits)


class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            d = json.loads(body)
            hits = []
            for t in d.get("tools", []):
                fn = t.get("function", {})
                scan(fn.get("parameters", {}), fn.get("name", "?"), hits)
            print(f"[toolcheck] {len(d.get('tools', []))} Tools; unverankert: {hits or 'keine'}", flush=True)
        except Exception as e:  # noqa: BLE001
            print("[toolcheck] kein JSON:", e, flush=True)
        req = urllib.request.Request(ROUTER + self.path, data=body, method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as r:
                self.send_response(r.status)
                self.end_headers()
                self.wfile.write(r.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())

    def do_GET(self):
        try:
            with urllib.request.urlopen(ROUTER + self.path) as r:
                self.send_response(r.status)
                self.end_headers()
                self.wfile.write(r.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(e.read())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"[toolcheck] lauscht auf 127.0.0.1:{PORT} -> {ROUTER}", flush=True)
    http.server.HTTPServer(("127.0.0.1", PORT), H).serve_forever()
