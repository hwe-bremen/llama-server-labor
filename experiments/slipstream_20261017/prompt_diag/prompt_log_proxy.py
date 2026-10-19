#!/usr/bin/env python3
"""Protokoll-Proxy: reicht alles unveraendert an UPSTREAM weiter und speichert jeden
/v1/chat/completions-Body als eine Zeile in requests_<zeit>.jsonl. Nur stdlib, nur 127.0.0.1.

  PDIAG_PORT=8085 PDIAG_UPSTREAM=http://127.0.0.1:8080 python3 prompt_log_proxy.py
"""
import datetime, http.client, json, os, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

PORT = int(os.environ.get("PDIAG_PORT", "8085"))
UP = urlsplit(os.environ.get("PDIAG_UPSTREAM", "http://127.0.0.1:8080"))
LOG = Path(__file__).resolve().parent / f"requests_{datetime.datetime.now():%Y%m%dT%H%M%S}.jsonl"
LOCK = threading.Lock()
HOP = {"connection", "keep-alive", "transfer-encoding", "te", "trailer", "upgrade", "proxy-authorization", "proxy-authenticate", "host", "content-length"}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _forward(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n) if n else b""
        if self.command == "POST" and self.path.rstrip("/").endswith("/chat/completions") and body:
            try:
                rec = {"zeit": datetime.datetime.now().isoformat(timespec="seconds"), "body": json.loads(body)}
                with LOCK, LOG.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception as e:  # Protokoll darf den Betrieb nie stoeren
                print("Protokollfehler:", e, file=sys.stderr)
        conn = http.client.HTTPConnection(UP.hostname, UP.port or 80, timeout=3600)
        hdrs = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
        try:
            conn.request(self.command, self.path, body=body or None, headers=hdrs)
            r = conn.getresponse()
        except OSError as e:
            msg = f"Upstream {UP.geturl()} nicht erreichbar: {e}".encode()
            print(msg.decode(), file=sys.stderr, flush=True)
            self.send_response(502)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(msg)
            self.close_connection = True
            return
        self.send_response(r.status, r.reason)
        for k, v in r.getheaders():
            if k.lower() not in HOP:
                self.send_header(k, v)
        self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.end_headers()
        while True:
            chunk = r.read1(65536) if hasattr(r, "read1") else r.read(65536)
            if not chunk:
                break
            self.wfile.write(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
            self.wfile.flush()
        self.wfile.write(b"0\r\n\r\n")
        conn.close()
        self.close_connection = True

    do_GET = do_POST = do_PUT = do_DELETE = do_OPTIONS = _forward

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Protokoll-Proxy 127.0.0.1:{PORT} -> {UP.geturl()}  |  Log: {LOG}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
