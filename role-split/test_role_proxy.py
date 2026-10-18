#!/usr/bin/env python3
"""Tests für role_proxy.py: Trigger-Logik plus echter Durchlauf mit Fake-Upstream."""
import datetime as dt
import gzip
import http.client
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import role_proxy as rp

ROLES = {"review": "REVIEW-PROMPT", "research": "RESEARCH-PROMPT"}
TODAY = dt.date(2026, 10, 14)


def u(text):
    return {"role": "user", "content": text}


def a(text):
    return {"role": "assistant", "content": text}


class TriggerTests(unittest.TestCase):
    def test_ohne_trigger_unveraendert(self):
        body = {"messages": [u("Hallo")]}
        out, role = rp.apply_roles(body, ROLES, TODAY)
        self.assertIsNone(role)
        self.assertEqual(out["messages"], body["messages"])

    def test_trigger_setzt_system_und_entfernt_trigger(self):
        out, role = rp.apply_roles({"messages": [u("@review Prüf das")]}, ROLES, TODAY)
        self.assertEqual(role, "review")
        self.assertEqual(out["messages"][0]["role"], "system")
        self.assertIn("REVIEW-PROMPT", out["messages"][0]["content"])
        self.assertIn("2026-10-14 (Mittwoch)", out["messages"][0]["content"])
        self.assertEqual(out["messages"][1]["content"], "Prüf das")

    def test_rolle_bleibt_ueber_folgerunden(self):
        msgs = [u("@review A"), a("x"), u("B ohne Trigger")]
        out, role = rp.apply_roles({"messages": msgs}, ROLES, TODAY)
        self.assertEqual(role, "review")
        self.assertEqual([m["content"] for m in out["messages"] if m["role"] == "user"], ["A", "B ohne Trigger"])

    def test_letzter_trigger_gewinnt(self):
        msgs = [u("@review A"), a("x"), u("@research B")]
        _, role = rp.apply_roles({"messages": msgs}, ROLES, TODAY)
        self.assertEqual(role, "research")

    def test_aus_schaltet_ab(self):
        msgs = [u("@review A"), a("Ich bin die Review-Instanz."), u("@aus weiter normal")]
        out, role = rp.apply_roles({"messages": msgs}, ROLES, TODAY)
        self.assertIsNone(role)
        self.assertEqual(out["messages"][0], {"role": "system", "content": rp.RESET_NOTE})
        self.assertNotIn("REVIEW-PROMPT", json.dumps(out, ensure_ascii=False))
        self.assertEqual(out["messages"][-1]["content"], "weiter normal")

    def test_aus_mit_client_system(self):
        msgs = [{"role": "system", "content": "CLIENT"}, u("@review A"), a("x"), u("@aus B")]
        out, _ = rp.apply_roles({"messages": msgs}, ROLES, TODAY)
        sys_text = out["messages"][0]["content"]
        self.assertTrue(sys_text.startswith(rp.RESET_NOTE))
        self.assertIn("CLIENT", sys_text)

    def test_rolle_nach_aus_wieder_an(self):
        msgs = [u("@review A"), a("x"), u("@aus B"), a("y"), u("@research C")]
        out, role = rp.apply_roles({"messages": msgs}, ROLES, TODAY)
        self.assertEqual(role, "research")
        self.assertNotIn(rp.RESET_NOTE, out["messages"][0]["content"])

    def test_client_system_bleibt_erhalten(self):
        msgs = [{"role": "system", "content": "CLIENT"}, u("@review A")]
        out, _ = rp.apply_roles({"messages": msgs}, ROLES, TODAY)
        self.assertEqual(sum(m["role"] == "system" for m in out["messages"]), 1)
        sys_text = out["messages"][0]["content"]
        self.assertLess(sys_text.index("REVIEW-PROMPT"), sys_text.index("CLIENT"))

    def test_unbekannter_trigger_bleibt_stehen(self):
        out, role = rp.apply_roles({"messages": [u("@niemand hallo")]}, ROLES, TODAY)
        self.assertIsNone(role)
        self.assertEqual(out["messages"][0]["content"], "@niemand hallo")

    def test_trigger_mitten_im_text_zaehlt_nicht(self):
        _, role = rp.apply_roles({"messages": [u("bitte @review machen")]}, ROLES, TODAY)
        self.assertIsNone(role)

    def test_trigger_als_wortanfang_nicht_als_praefix(self):
        _, role = rp.apply_roles({"messages": [u("@reviewer hallo")]}, ROLES, TODAY)
        self.assertIsNone(role)

    def test_nur_trigger_ergibt_hinweistext(self):
        out, role = rp.apply_roles({"messages": [u("@review")]}, ROLES, TODAY)
        self.assertEqual(role, "review")
        self.assertTrue(out["messages"][1]["content"])

    def test_listen_content(self):
        msg = {"role": "user", "content": [{"type": "text", "text": "@review Bild prüfen"},
                                           {"type": "image_url", "image_url": {"url": "x"}}]}
        out, role = rp.apply_roles({"messages": [msg]}, ROLES, TODAY)
        self.assertEqual(role, "review")
        self.assertEqual(out["messages"][1]["content"][0]["text"], "Bild prüfen")
        self.assertEqual(out["messages"][1]["content"][1]["type"], "image_url")

    def test_eingabe_wird_nicht_veraendert(self):
        msgs = [u("@review A")]
        rp.apply_roles({"messages": msgs}, ROLES, TODAY)
        self.assertEqual(msgs[0]["content"], "@review A")

    def test_tool_nachrichten_bleiben(self):
        msgs = [u("@review lies"), {"role": "assistant", "content": None, "tool_calls": [{"id": "1"}]},
                {"role": "tool", "tool_call_id": "1", "content": "inhalt"}]
        out, _ = rp.apply_roles({"messages": msgs, "tools": [{"type": "function"}]}, ROLES, TODAY)
        self.assertEqual(out["messages"][2]["tool_calls"], [{"id": "1"}])
        self.assertEqual(out["tools"], [{"type": "function"}])


class ModelTests(unittest.TestCase):
    QWEN = "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL"
    GEMMA = "unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_XL"

    def test_kuerzel(self):
        self.assertEqual(rp.model_tag(self.QWEN), "qwen36-27b")
        self.assertEqual(rp.model_tag("unsloth/Qwen3.8-27B-GGUF:Q4_K_XL"), "qwen38-27b")
        self.assertEqual(rp.model_tag(self.GEMMA), "gemma4-26b")
        self.assertEqual(rp.model_tag("unsloth/gemma-4-31B-it-GGUF:Q4_K_XL"), "gemma4-31b")
        self.assertEqual(rp.model_tag("JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q6_K:Q6_K"), "mellum2-12b")
        self.assertEqual(rp.model_tag("jondale/Apertus-8B-Instruct-2509-GGUF:Q4_K_M"), "apertus-8b")
        self.assertEqual(rp.model_tag("foo/Neues-Modell_7B:Q4"), "neuesmodell7b")
        self.assertEqual(rp.model_tag(""), "modell")

    def test_kuerzel_unterscheidet_familienmitglieder(self):
        tags = {rp.model_tag(m) for m in (
            self.QWEN, "unsloth/Qwen3.8-27B-GGUF:Q4_K_XL",
            self.GEMMA, "unsloth/gemma-4-31B-it-GGUF:Q4_K_XL")}
        self.assertEqual(len(tags), 4)

    def test_modell_im_system_prompt(self):
        out, _ = rp.apply_roles({"model": self.GEMMA, "messages": [u("@review A")]}, ROLES, TODAY)
        sys_text = out["messages"][0]["content"]
        self.assertIn(f"Du läufst als Modell: {self.GEMMA}", sys_text)
        self.assertIn("Kürzel für Dateinamen: gemma4-26b", sys_text)

    def test_ohne_modell_keine_zeile(self):
        for body in ({"messages": [u("@review A")]}, {"model": "default", "messages": [u("@review A")]}):
            out, _ = rp.apply_roles(body, ROLES, TODAY)
            self.assertNotIn("Du läufst als Modell", out["messages"][0]["content"])

    def test_modell_nur_bei_aktiver_rolle(self):
        out, _ = rp.apply_roles({"model": self.QWEN, "messages": [u("hallo")]}, ROLES, TODAY)
        self.assertEqual(out["messages"], [u("hallo")])

    def test_trigger_mit_doppelpunkt(self):
        out, role = rp.apply_roles({"messages": [u("@review: Prüf das")]}, ROLES, TODAY)
        self.assertEqual(role, "review")
        self.assertEqual(out["messages"][1]["content"], "Prüf das")
        # Befund 14.10. 22:18: "@review: @review Prüf …" lief ohne Rolle
        out, role = rp.apply_roles({"messages": [u("@review: @review Prüf")]}, ROLES, TODAY)
        self.assertEqual(role, "review")

    def test_doppelpunkt_ohne_leerzeichen_kein_trigger(self):
        _, role = rp.apply_roles({"messages": [u("@review:x")]}, ROLES, TODAY)
        self.assertIsNone(role)


class RoleFileTests(unittest.TestCase):
    def test_laden_mit_frontmatter_und_unterstrich(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "review.md").write_text("---\nx: 1\n---\nPROMPT", encoding="utf-8")
            (p / "_entwurf.md").write_text("ignorieren", encoding="utf-8")
            (p / "aus.md").write_text("darf kein Rollenname sein", encoding="utf-8")
            roles = rp.load_roles(p)
        self.assertEqual(roles, {"review": "PROMPT"})

    def test_echte_rollen_dateien(self):
        roles = rp.load_roles(Path(__file__).parent / "roles")
        self.assertIn("review", roles)
        self.assertIn("research", roles)


class FakeUpstream(BaseHTTPRequestHandler):
    received = []

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        FakeUpstream.received.append((self.path, json.loads(self.rfile.read(n))))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for i in range(3):
            self.wfile.write(f"data: {{\"n\": {i}}}\n\n".encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")

    def do_GET(self):
        # wie llama-server: Web-UI nur, wenn der Client gzip annimmt
        if "gzip" not in (self.headers.get("Accept-Encoding") or ""):
            body = b"Error: gzip is not supported by this browser"
            self.send_response(406)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = gzip.compress(b"<html>webui</html>")
        self.send_response(200)
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


class ProxyIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        roles = Path(cls.tmp.name) / "roles"
        roles.mkdir()
        (roles / "review.md").write_text("REVIEW-PROMPT", encoding="utf-8")
        cls.up = ThreadingHTTPServer(("127.0.0.1", 0), FakeUpstream)
        threading.Thread(target=cls.up.serve_forever, daemon=True).start()
        rp.UPSTREAM = f"http://127.0.0.1:{cls.up.server_address[1]}"
        rp.ROLES_DIR = roles
        rp.LOG_FILE = Path(cls.tmp.name) / "log.jsonl"
        rp.Handler.log_message = lambda *a: None
        cls.px = ThreadingHTTPServer(("127.0.0.1", 0), rp.Handler)
        threading.Thread(target=cls.px.serve_forever, daemon=True).start()
        cls.port = cls.px.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.px.shutdown()
        cls.up.shutdown()
        cls.tmp.cleanup()

    def _post(self, payload):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        data = json.dumps(payload).encode()
        conn.request("POST", "/v1/chat/completions", body=data, headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        return resp, resp.read().decode()

    def test_chat_mit_rolle_und_stream(self):
        FakeUpstream.received.clear()
        resp, text = self._post({"stream": True, "messages": [u("@review hallo")]})
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader("X-Lab-Role"), "review")
        self.assertIn("[DONE]", text)
        self.assertEqual(text.count("data:"), 4)
        path, body = FakeUpstream.received[-1]
        self.assertEqual(path, "/v1/chat/completions")
        self.assertIn("REVIEW-PROMPT", body["messages"][0]["content"])
        self.assertEqual(body["messages"][1]["content"], "hallo")
        log = rp.LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(json.loads(log[-1])["rolle"], "review")

    def test_log_enthaelt_modell(self):
        self._post({"model": "unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_XL", "messages": [u("@review x")]})
        entry = json.loads(rp.LOG_FILE.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(entry["modell"], "unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_XL")
        self.assertIn("Du läufst als Modell", FakeUpstream.received[-1][1]["messages"][0]["content"])

    def test_chat_ohne_rolle_kein_header(self):
        FakeUpstream.received.clear()
        resp, _ = self._post({"messages": [u("hallo")]})
        self.assertIsNone(resp.getheader("X-Lab-Role"))
        self.assertEqual(FakeUpstream.received[-1][1]["messages"], [u("hallo")])

    def test_get_wird_durchgereicht(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.request("GET", "/", headers={"Accept-Encoding": "gzip, deflate, br"})
        resp = conn.getresponse()
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader("Content-Encoding"), "gzip")
        self.assertEqual(gzip.decompress(resp.read()), b"<html>webui</html>")

    def test_upstream_weg_gibt_502(self):
        old = rp.UPSTREAM
        rp.UPSTREAM = "http://127.0.0.1:9"  # Port 9: dort lauscht nichts
        try:
            resp, _ = self._post({"messages": [u("hallo")]})
            self.assertEqual(resp.status, 502)
        finally:
            rp.UPSTREAM = old


class DefaultModelTest(unittest.TestCase):
    def test_effective_model_prefers_request(self):
        self.assertEqual(rp.effective_model({"model": "x-27B"}, "std"), "x-27B")

    def test_effective_model_falls_back(self):
        self.assertEqual(rp.effective_model({}, "Qwen3-Coder-Next-80B-A3B"), "Qwen3-Coder-Next-80B-A3B")
        self.assertEqual(rp.effective_model({"model": "default"}, "std"), "std")

    def test_tag_for_default(self):
        self.assertEqual(rp.model_tag("Qwen3-Coder-Next-80B-A3B"), "qwen3-80b")


if __name__ == "__main__":
    unittest.main(verbosity=2)
