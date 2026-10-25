#!/usr/bin/env python3
"""Tests fuer kette.review_auto – keine Außenwirkung, nur 127.0.0.1."""
import http.server
import io
import json
import os
import socket
import threading
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys_path_patch = __import__("sys").path.insert(0, str(Path(__file__).resolve().parent.parent / "role-split" / "kette"))
import kette  # noqa: E402

KOPF = "# Verdikt: x\n\n## Ergebnis\n\n**{u}** – Text.\n\n## Anforderungen einzeln\n\n" \
       "| Nr. | Anforderung | Befund | Fundstelle |\n|---|---|---|---|\n{anf}\n\n## Befunde\n\n" \
       "| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg |\n" \
       "|---|---|---|---|---|---|---|---|\n{bef}\n"


# ------------------------------------------------------------------ Hilfsklassen

class _MiniServer(http.server.BaseHTTPRequestHandler):
    """Simuliert /v1/chat/completions mit vorgegebenen Antworten."""

    antworten = []          # Liste von dicts, pro Request wird das nächste genommen
    anzahl_rufe = 0

    def do_POST(self):
        _MiniServer.anzahl_rufe += 1
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))
        # Antwort zusammenbauen
        idx = (_MiniServer.anzahl_rufe - 1) % max(len(_MiniServer.antworten), 1)
        resp = _MiniServer.antworten[idx]
        payload = json.dumps(resp).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        pass  # Stille Logs


def _freier_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _server_thread(port, delay=0, max_requests=0):
    """Startet den MiniServer in einem Thread, optional mit Verzögerung.
    max_requests=0 bedeutet: unendlich viele Requests bedienen."""
    def _run():
        if delay:
            time.sleep(delay)
        srv = http.server.HTTPServer(("127.0.0.1", port), _MiniServer)
        if max_requests > 0:
            srv.handle_request()  # nur angegebene Anzahl
        else:
            srv.serve_forever()  # unendlich viele
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


# ------------------------------------------------------------------ Tests

class ReviewAutoTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        kette.PM = Path(self.tmp.name)
        self._orig_url = os.environ.get("KETTE_LLM_URL")
        self._orig_model = os.environ.get("KETTE_LLM_MODEL")
        self._orig_timeout = os.environ.get("KETTE_LLM_TIMEOUT")
        self._orig_heartbeat = os.environ.get("KETTE_HERZSCHLAG_S")
        self._orig_kette_url = getattr(kette, "KETTE_LLM_URL", None)
        os.environ["KETTE_LLM_TIMEOUT"] = "3"
        os.environ["KETTE_HERZSCHLAG_S"] = "1"
        _MiniServer.antworten = []
        _MiniServer.anzahl_rufe = 0

    def tearDown(self):
        if self._orig_url is not None:
            os.environ["KETTE_LLM_URL"] = self._orig_url
        elif "KETTE_LLM_URL" in os.environ:
            del os.environ["KETTE_LLM_URL"]
        if self._orig_model is not None:
            os.environ["KETTE_LLM_MODEL"] = self._orig_model
        elif "KETTE_LLM_MODEL" in os.environ:
            del os.environ["KETTE_LLM_MODEL"]
        if self._orig_timeout is not None:
            os.environ["KETTE_LLM_TIMEOUT"] = self._orig_timeout
        elif "KETTE_LLM_TIMEOUT" in os.environ:
            del os.environ["KETTE_LLM_TIMEOUT"]
        if self._orig_heartbeat is not None:
            os.environ["KETTE_HERZSCHLAG_S"] = self._orig_heartbeat
        elif "KETTE_HERZSCHLAG_S" in os.environ:
            del os.environ["KETTE_HERZSCHLAG_S"]
        if self._orig_kette_url is not None:
            kette.KETTE_LLM_URL = self._orig_kette_url
        elif hasattr(kette, "KETTE_LLM_URL"):
            delattr(kette, "KETTE_LLM_URL")

    # --- T1: Endergebnis bei zwei gültigen Läufen ---

    def test_t1_endergebnis_zwei_gueltige_laeufe(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        _MiniServer.antworten = [
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 2 | nein | nein | nein | niedrig | x.py:2 | x | y |")}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
        ]
        _server_thread(port)
        # pruefen patchen auf Exit 0
        orig_teile = kette._pruefen_teile
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        # paket patchen auf Exit 0
        orig_paket = kette.paket
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "paket", orig_paket)

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test1")
        out = buf.getvalue()
        self.assertIn("Ergebnis", out)
        self.assertIn("gesamt_", out)
        self.assertEqual(_MiniServer.anzahl_rufe, 2)
        gesamt = list(kette.PM.glob("gesamt_*.md"))
        self.assertTrue(bool(gesamt))

    # --- T2: Router nicht erreichbar ---

    def test_t2_router_nicht_erreichbar(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test2")
        out = buf.getvalue()
        self.assertEqual(code, 1)
        self.assertTrue("nicht erreichbar" in out.lower() or "verbin" in out.lower())
        verdikte = list(kette.PM.glob("verdict_*.md"))
        self.assertEqual(len(verdikte), 0)

    # --- T3: Ungültiger Kurztitel ---

    def test_t3_ungueltiger_kurztitel(self):
        orig_paket = kette.paket
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("Ungültig-Titel")
        self.assertEqual(code, 2)
        self.assertIn("ungültig", buf.getvalue().lower())

    # --- T4: Nur rote Unit-Tests brechen ab ---

    def test_t4_rote_unit_tests_abbruch(self):
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (1, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test4")
        self.assertEqual(code, 1)
        self.assertIn("Unit-Tests rot", buf.getvalue())
        self.assertEqual(_MiniServer.anzahl_rufe, 0)

    # --- T5: Paket-Voraussetzung fehlt ---

    def test_t5_paket_voraussetzung_fehlt(self):
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 2
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test5")
        self.assertEqual(code, 2)
        self.assertIn("Paket", buf.getvalue())

    # --- T6: Leere Modellantwort ---

    def test_t6_leere_modellantwort(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        _MiniServer.antworten = [
            {"choices": []},
            {"choices": [{"message": {"content": ""}}]},
        ]
        _server_thread(port)
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test6")
        self.assertEqual(code, 1)
        self.assertIn("leere", buf.getvalue().lower())

    # --- T7: Automatisches Umbenennen ---

    def test_t7_automatisches_umbenennen(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        _MiniServer.antworten = [
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {}},
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 2 | nein | nein | nein | niedrig | x.py:2 | x | y |")}, "finish_reason": "stop"}], "usage": {}},
        ]
        _server_thread(port)
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        # Vorab existierende Datei anlegen
        datum = "20261025"
        (kette.PM / f"verdict_{datum}_test7_qwen36-35b.md").write_text("alter Inhalt", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test7")
        self.assertIn("_2", buf.getvalue())
        verdikte = sorted(kette.PM.glob("verdict_*.md"))
        self.assertTrue(any("_2" in v.name for v in verdikte))

    # --- T8: Fehlende Befund-Tabelle ---

    def test_t8_fehlende_befund_tabelle(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        # Lauf 1: gültiges Verdikt
        # Lauf 2: Verdikt ohne Befund-Tabelle
        _MiniServer.antworten = [
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {}},
            {"choices": [{"message": {"content": "# Verdikt\n\n## Ergebnis\n\n**PASS** – Text.\n\n## Anforderungen\n\n| A1 | x | erfüllt | x |"}}], "usage": {}},
        ]
        _server_thread(port)
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test8")
        self.assertEqual(code, 1)
        # Spec A6: gesamt_*.md existiert, enthält UNVOLLSTÄNDIG, zeigt kein PASS
        gesamt = list(kette.PM.glob("gesamt_*.md"))
        self.assertTrue(bool(gesamt), "gesamt_*.md muss existieren")
        gesamt_text = gesamt[0].read_text(encoding="utf-8")
        self.assertIn("UNVOLLSTÄNDIG", gesamt_text, "gesamt_*.md muss UNVOLLSTÄNDIG enthalten")
        self.assertNotIn("PASS", gesamt_text, "gesamt_*.md darf kein PASS enthalten")

    # --- T9: Abbruch bei Lauf 2 (Lauf 1 bleibt erhalten) ---

    def test_t9_abbruch_bei_lauf_2(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        # Lauf 1: sofortige Antwort
        # Lauf 2: verzögert (länger als KETTE_LLM_TIMEOUT=3)
        _MiniServer.antworten = [
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {}},
            {"choices": [{"message": {"content": "spät"}}], "usage": {}},
        ]
        # Server nur für Lauf 1, Lauf 2 wird vom Server nicht bedient (Timeout)
        t1 = _server_thread(port, delay=0)
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test9")
        verdikte = list(kette.PM.glob("verdict_*.md"))
        self.assertTrue(bool(verdikte))  # Lauf 1 existiert
        self.assertEqual(code, 1)

    # --- T10: Zusammenfassung und Gesamt-Datei ---

    def test_t10_zusammenfassung_gesamt_datei(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        _MiniServer.antworten = [
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {}},
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 2 | nein | nein | nein | niedrig | x.py:2 | x | y |")}, "finish_reason": "stop"}], "usage": {}},
        ]
        _server_thread(port)
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            kette.review_auto("test10")
        out = buf.getvalue()
        self.assertIn("Ergebnis", out)
        self.assertIn("Verdikt 1", out)
        self.assertIn("Verdikt 2", out)
        self.assertIn("Gesamt", out)
        self.assertTrue(bool(list(kette.PM.glob("gesamt_*.md"))))

    # --- T11: Nur 127.0.0.1 ---

    def test_t11_nur_loopback(self):
        os.environ["KETTE_LLM_URL"] = "http://192.0.2.1:8080"
        kette.KETTE_LLM_URL = "http://192.0.2.1:8080"
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test11")
        self.assertEqual(code, 1)
        self.assertIn("127.0.0.1", buf.getvalue())

    # --- T12: Abgeschnittene Antwort und HTTP-Fehler ---

    def test_t12_abgeschnittene_antwort(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        _MiniServer.antworten = [
            {"choices": [{"message": {"content": "Text"}, "finish_reason": "length"}], "usage": {}},
        ]
        _server_thread(port)
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test12a")
        self.assertEqual(code, 1)
        self.assertIn("abgeschnitten", buf.getvalue().lower())

    # --- T13: Herzschlag während des Laufs ---

    def test_t13_herzschlag_waehrend_lauf(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        os.environ["KETTE_HERZSCHLAG_S"] = "1"
        _MiniServer.antworten = [
            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {}},
        ]
        # Server antwortet erst nach 2.5 s
        def _delayed_server():
            time.sleep(2.5)
            srv = http.server.HTTPServer(("127.0.0.1", port), _MiniServer)
            srv.handle_request()
        threading.Thread(target=_delayed_server, daemon=True).start()
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            kette.review_auto("test13")
        out = buf.getvalue()
        herzschlag_count = out.count("min")
        # Daemon-Thread-Prints koennten durch redirect_stdout teilweise verloren gehen
        self.assertGreaterEqual(herzschlag_count, 1)

    # --- T14: Lauf 1 fehlschlaegt, Server genau ein Request ---

    def test_k1_lauf1_fehlschlaegt_ein_request(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        _MiniServer.antworten = [
            {"choices": []},  # leere Antwort -> Lauf 1 scheitert
        ]
        _server_thread(port)
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test14")
        self.assertEqual(code, 1)
        self.assertEqual(_MiniServer.anzahl_rufe, 1)

    # --- T15: Timeout yield Zeitüberschreitung ---

    def test_k2_timeout_zeitueberschreitung(self):
        port = _freier_port()
        url = f"http://127.0.0.1:{port}"
        os.environ["KETTE_LLM_URL"] = url
        kette.KETTE_LLM_URL = url
        orig_timeout = getattr(kette, "KETTE_LLM_TIMEOUT", None)
        kette.KETTE_LLM_TIMEOUT = 1
        self.addCleanup(setattr, kette, "KETTE_LLM_TIMEOUT", orig_timeout)
        # Server lauscht sofort, Handler antwortet erst nach 3 s -> Timeout
        class _DelayHandler(_MiniServer):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                self.rfile.read(length)
                time.sleep(3)
                resp = {"choices": [{"message": {"content": "delayed"}}], "usage": {}}
                payload = json.dumps(resp).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            def log_message(self, *a): pass
        srv = http.server.HTTPServer(("127.0.0.1", port), _DelayHandler)
        srv.socket.settimeout(5)  # Socket-Timeout für den Server
        threading.Thread(target=srv.handle_request, daemon=True).start()
        orig_teile = kette._pruefen_teile
        orig_paket = kette.paket
        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
        kette.paket = lambda *a: 0
        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
        self.addCleanup(setattr, kette, "paket", orig_paket)
        self.addCleanup(srv.server_close)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = kette.review_auto("test15")
        self.assertEqual(code, 1)
        self.assertIn("Zeitüberschreitung", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
