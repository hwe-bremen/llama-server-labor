#!/usr/bin/env python3
"""Tests: Verdikte (verdict_*.md) werden vom MCP-Server nie ueberschrieben oder geloescht.

Aufruf:  cd mcp-server && .venv/bin/python -m unittest test_verdict_schutz -v
"""
import tempfile
import unittest
from pathlib import Path

from test_search_files import load


class VerdictSchutzTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "pm").mkdir(parents=True)
        self.m = load({"MCP_SCOPE_ROOT": str(self.root), "MCP_READONLY": "0",
                       "MCP_WRITE_ROOTS": "docs/pm", "MCP_ALLOW_WEB": "0"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_neues_verdikt_darf_geschrieben_werden(self):
        out = self.m.write_file("docs/pm/verdict_20261017_x_qwen.md", "eins")
        self.assertIn("Geschrieben", out)

    def test_bestehendes_verdikt_nicht_ueberschreiben(self):
        self.m.write_file("docs/pm/verdict_20261017_x_qwen.md", "eins")
        out = self.m.write_file("docs/pm/verdict_20261017_x_qwen.md", "zwei")
        self.assertIn("Verweigert", out)
        self.assertEqual((self.root / "docs/pm/verdict_20261017_x_qwen.md").read_text(), "eins")

    def test_verdikt_nicht_loeschen(self):
        self.m.write_file("docs/pm/verdict_20261017_x_qwen.md", "eins")
        out = self.m.delete_file("docs/pm/verdict_20261017_x_qwen.md")
        self.assertIn("Verweigert", out)
        self.assertTrue((self.root / "docs/pm/verdict_20261017_x_qwen.md").exists())

    def test_spec_darf_ueberschrieben_werden(self):
        self.m.write_file("docs/pm/spec_20261017_x.md", "eins")
        out = self.m.write_file("docs/pm/spec_20261017_x.md", "zwei")
        self.assertIn("Geschrieben", out)


if __name__ == "__main__":
    unittest.main()
