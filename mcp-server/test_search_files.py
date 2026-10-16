#!/usr/bin/env python3
"""Tests fuer search_files und den git_log-Schalter (stdlib unittest).

Aufruf (im mcp-server-venv, braucht das Paket `mcp`):
    cd mcp-server && .venv/bin/python -m unittest test_search_files -v

Befund 16.10.: search_files mit path=<Datei> lieferte still "Keine Treffer"
(rglob auf einer Datei findet nichts). Qwen3.8 hat deshalb im Review-Eval
Zeilennummern von Hand gezaehlt.
"""
import asyncio
import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def load(env: dict):
    """Server-Modul mit frischer Umgebung laden (Konfig wird beim Import gelesen)."""
    for k in list(os.environ):
        if k.startswith("MCP_"):
            del os.environ[k]
    os.environ.update(env)
    sys.modules.pop("lab_mcp_server", None)
    return importlib.import_module("lab_mcp_server")


def tool_names(m) -> set:
    return {t.name for t in asyncio.run(m.mcp.list_tools())}


class SearchFilesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "pkg").mkdir()
        (root / "pkg" / "scout.py").write_text(
            "import feedparser\nGITHUB_RELEASES_RSS = []\nfeed = feedparser.parse(url)\n",
            encoding="utf-8",
        )
        (root / "pkg" / "other.txt").write_text("nichts hier\n", encoding="utf-8")
        (root / "secret").mkdir()
        (root / "secret" / "x.py").write_text("feedparser\n", encoding="utf-8")
        self.m = load({
            "MCP_SCOPE_ROOT": str(root),
            "MCP_ALLOW_WEB": "0",
            "MCP_DENY": "secret",
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_einzeldatei_findet_treffer(self):
        out = self.m.search_files("parser", path="pkg/scout.py")
        self.assertIn("pkg/scout.py:1:", out)
        self.assertIn("pkg/scout.py:3:", out)

    def test_einzeldatei_teilstring_wie_im_eval(self):
        # genau die Muster, an denen Qwen3.8 gescheitert ist
        for pat in ("gith", "RSS", "parser"):
            out = self.m.search_files(pat, path="pkg/scout.py", ignore_case=True)
            self.assertNotIn("Keine Treffer", out, pat)

    def test_ordner_weiterhin_rekursiv(self):
        out = self.m.search_files("feedparser", path="pkg")
        self.assertIn("pkg/scout.py:1:", out)

    def test_ignore_case(self):
        self.assertIn("Keine Treffer", self.m.search_files("github_releases", path="pkg"))
        self.assertIn("pkg/scout.py:2:",
                      self.m.search_files("github_releases", path="pkg", ignore_case=True))

    def test_keine_treffer_nennt_anzahl(self):
        out = self.m.search_files("gibtsnicht", path="pkg/scout.py")
        self.assertIn("1 Datei(en) durchsucht", out)

    def test_nicht_existierender_pfad(self):
        self.assertIn("Nicht gefunden", self.m.search_files("x", path="pkg/fehlt.py"))

    def test_sperrliste_gilt_auch_fuer_einzeldatei(self):
        with self.assertRaises(self.m.ScopeError):
            self.m.search_files("feedparser", path="secret/x.py")
        # und rekursiv ab Root taucht secret/ nicht auf
        self.assertNotIn("secret/", self.m.search_files("feedparser", path="."))

    def test_traversal_bleibt_blockiert(self):
        with self.assertRaises(self.m.ScopeError):
            self.m.search_files("root", path="../../etc/passwd")


class GitLogSwitchTests(unittest.TestCase):
    def test_default_an(self):
        m = load({"MCP_SCOPE_ROOT": tempfile.gettempdir(), "MCP_ALLOW_WEB": "0"})
        self.assertIn("git_log", tool_names(m))

    def test_eval_aus(self):
        m = load({"MCP_SCOPE_ROOT": tempfile.gettempdir(), "MCP_ALLOW_WEB": "0",
                  "MCP_ALLOW_GITLOG": "0"})
        names = tool_names(m)
        self.assertNotIn("git_log", names)
        self.assertIn("git_status", names)   # Rest unveraendert
        self.assertIn("read_file", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
