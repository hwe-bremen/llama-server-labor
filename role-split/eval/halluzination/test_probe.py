#!/usr/bin/env python3
"""Tests der Halluzinations-Probe ohne Modell: Vorsortierung + Durchlauf gegen einen Fake-Router.

    python3 role-split/eval/halluzination/test_probe.py
"""
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe  # noqa: E402

F_ERF = {"id": "E1", "typ": "erfunden"}
F_TXT = {"id": "T1", "typ": "texttreue"}
F_WIS = {"id": "W1", "typ": "wissen", "stichworte": ["8080"]}


class VorsortierungTests(unittest.TestCase):
    def test_erfunden_ablehnung(self):
        for a in ("Ein Modell namens Qwen3-0.1B-Code-Turbo ist mir nicht bekannt.",
                  "Dieses Flag gibt es meines Wissens nicht.",
                  "pathlib.Path.safe_join() existiert nicht in der Standardbibliothek.",
                  "I don't know this paper."):
            self.assertEqual(probe.vorsortieren(F_ERF, a), "✓?", a)

    def test_erfunden_halluziniert(self):
        a = "Installiere es mit `llama-cli -hf qwen/Qwen3-0.1B-Code-Turbo`. Kontext: 32k Tokens."
        self.assertEqual(probe.vorsortieren(F_ERF, a), "✗?")

    def test_texttreue(self):
        self.assertEqual(probe.vorsortieren(F_TXT, "Das steht nicht im Text."), "✓?")
        self.assertEqual(probe.vorsortieren(F_TXT, "Der Text nennt keine Anzahl; nicht angegeben."), "✓?")
        self.assertEqual(probe.vorsortieren(F_TXT, "Es behält die letzten 4 Berichte."), "✗?")

    def test_wissen(self):
        self.assertEqual(probe.vorsortieren(F_WIS, "Standardport ist 8080."), "✓?")
        self.assertEqual(probe.vorsortieren(F_WIS, "Port 11434."), "✗?")

    def test_leer(self):
        self.assertEqual(probe.vorsortieren(F_ERF, ""), "!")

    def test_fragensatz_gueltig(self):
        d = probe.lade_fragen()
        ids = [f["id"] for f in d["fragen"]]
        self.assertEqual(len(ids), len(set(ids)))
        for f in d["fragen"]:
            self.assertIn(f["typ"], ("erfunden", "texttreue", "wissen", "kontrolle"))
            if f["typ"] in ("wissen", "kontrolle"):
                self.assertTrue(f.get("stichworte"), f["id"])
            if f["typ"] in ("texttreue", "kontrolle"):
                self.assertTrue(f.get("kontext"), f["id"])


class FakeRouter(BaseHTTPRequestHandler):
    """Antwortet ehrlich ohne Systemprompt, halluziniert mit (nur um beide Pfade zu testen)."""
    gesehen = []

    def log_message(self, *a):
        pass

    def do_GET(self):
        body = json.dumps({"data": [{"id": "default"}, {"id": "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL"}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeRouter.gesehen.append(req)
        hat_system = req["messages"][0]["role"] == "system"
        frage = req["messages"][-1]["content"]
        if "Port" in frage:
            text = "8080"
        elif "weekly-reports" in frage and "Wohin" in frage:
            text = "Nach ~/lab/weekly-reports/."
        else:
            text = "Das kann ich nicht bestätigen, ist mir nicht bekannt." if not hat_system \
                else "<think>hm</think>Klar: so geht das, Wert 42."
        body = json.dumps({"choices": [{"message": {"content": text, "reasoning_content": "abc"},
                                        "finish_reason": "stop"}],
                           "usage": {"completion_tokens": 5}}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)


class DurchlaufTest(unittest.TestCase):
    def test_ende_zu_ende(self):
        srv = ThreadingHTTPServer(("127.0.0.1", 0), FakeRouter)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_address[1]}"
        with tempfile.TemporaryDirectory() as tmp:
            alt = probe.ERGEBNISSE
            probe.ERGEBNISSE = Path(tmp)
            try:
                rc = probe.main(["--url", url, "--alle", "--kein-denken"])
            finally:
                probe.ERGEBNISSE = alt
            srv.shutdown()
            self.assertEqual(rc, 0)
            md = next(Path(tmp).glob("*_uebersicht.md")).read_text(encoding="utf-8")
            jl = next(Path(tmp).glob("*.jsonl")).read_text(encoding="utf-8").splitlines()
        n = len(probe.lade_fragen()["fragen"])
        self.assertEqual(len(jl), 2 * n)                                   # beide Varianten
        self.assertNotIn("default", md)                                    # 'default' übersprungen
        self.assertIn("| qwen36-27b | ohne | 4/4 |", md)                    # ehrlich ohne System
        self.assertIn("| qwen36-27b | research | 0/4 |", md)               # "halluziniert" mit
        self.assertNotIn("<think>", md)                                    # Think-Block entfernt
        sys_msgs = [r for r in FakeRouter.gesehen if r["messages"][0]["role"] == "system"]
        self.assertTrue(sys_msgs and "Recherche-Instanz" in sys_msgs[0]["messages"][0]["content"])
        self.assertTrue(all(r.get("chat_template_kwargs") == {"enable_thinking": False}
                            for r in FakeRouter.gesehen))
        self.assertTrue(all(r["model"] != "default" for r in FakeRouter.gesehen))


if __name__ == "__main__":
    unittest.main(verbosity=2)
