#!/usr/bin/env python3
"""Tests: append_file (abschnittsweises Speichern) und schreibgeschuetzte Vorgaben der Kette.

Aufruf:  cd mcp-server && .venv/bin/python -m unittest test_append_file -v
Anlass 22.10.: Verdikte/Specs gingen beim vollen Kontext komplett verloren, weil nur ganze
Dateien geschrieben werden konnten.
"""
import tempfile
import unittest
from pathlib import Path

from test_search_files import load, tool_names


class AppendFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs" / "pm").mkdir(parents=True)
        (self.root / "code.py").write_text("x = 1\n")
        self.m = load({"MCP_SCOPE_ROOT": str(self.root), "MCP_READONLY": "0",
                       "MCP_WRITE_ROOTS": "docs/pm", "MCP_ALLOW_WEB": "0", "MCP_MAX_APPEND": "100"})

    def tearDown(self):
        self.tmp.cleanup()

    def lies(self, rel):
        return (self.root / rel).read_text(encoding="utf-8")

    def test_tool_registriert(self):
        self.assertIn("append_file", tool_names(self.m))

    def test_abschnitte_an_verdikt_anhaengen(self):
        self.assertIn("Geschrieben", self.m.write_file("docs/pm/verdict_x.md", "# Verdikt\n"))
        self.assertIn("Angehaengt", self.m.append_file("docs/pm/verdict_x.md", "## Ergebnis\nPASS"))
        self.assertIn("Angehaengt", self.m.append_file("docs/pm/verdict_x.md", "## Befunde\n- keiner\n"))
        self.assertEqual(self.lies("docs/pm/verdict_x.md"),
                         "# Verdikt\n## Ergebnis\nPASS\n## Befunde\n- keiner\n")

    def test_verdikt_bleibt_gegen_ueberschreiben_geschuetzt(self):
        self.m.write_file("docs/pm/verdict_x.md", "eins\n")
        self.m.append_file("docs/pm/verdict_x.md", "zwei\n")
        self.assertIn("Verweigert", self.m.write_file("docs/pm/verdict_x.md", "neu"))
        self.assertEqual(self.lies("docs/pm/verdict_x.md"), "eins\nzwei\n")

    def test_legt_fehlende_datei_an(self):
        self.assertIn("Angehaengt", self.m.append_file("docs/pm/neu/spec_y.md", "a"))
        self.assertEqual(self.lies("docs/pm/neu/spec_y.md"), "a")

    def test_base64_hat_vorrang(self):
        import base64
        b = base64.b64encode('zitat "x" \\n'.encode()).decode()
        self.m.append_file("docs/pm/a.md", "ignoriert", b)
        self.assertEqual(self.lies("docs/pm/a.md"), 'zitat "x" \\n')

    def test_ausserhalb_schreibgrenze_verweigert(self):
        with self.assertRaises(Exception):
            self.m.append_file("code.py", "y = 2\n")
        self.assertEqual(self.lies("code.py"), "x = 1\n")

    def test_traversal_verweigert(self):
        with self.assertRaises(Exception):
            self.m.append_file("docs/pm/../../../etc/x.md", "boom")
        with self.assertRaises(Exception):
            self.m.append_file("/tmp/x.md", "boom")

    def test_zu_gross_und_leer(self):
        self.assertIn("Verweigert", self.m.append_file("docs/pm/a.md", "x" * 101))
        self.assertIn("Nichts angehaengt", self.m.append_file("docs/pm/a.md", ""))
        self.assertFalse((self.root / "docs/pm/a.md").exists())

    def test_vorgaben_nie_schreiben_anhaengen_loeschen(self):
        for name in ("_vorlage_verdict.md", "anforderung_20261022_k.md", "quellen_20261022_k.md"):
            (self.root / "docs/pm" / name).write_text("original\n")
            self.assertIn("Verweigert", self.m.write_file(f"docs/pm/{name}", "neu"))
            self.assertIn("Verweigert", self.m.append_file(f"docs/pm/{name}", "mehr"))
            self.assertIn("Verweigert", self.m.delete_file(f"docs/pm/{name}"))
            self.assertEqual(self.lies(f"docs/pm/{name}"), "original\n")

    def test_vorgabe_auch_nicht_neu_anlegen(self):
        self.assertIn("Verweigert", self.m.write_file("docs/pm/anforderung_20261022_neu.md", "x"))
        self.assertFalse((self.root / "docs/pm/anforderung_20261022_neu.md").exists())


class ReadonlyModusTests(unittest.TestCase):
    def test_kein_append_im_readonly(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        m = load({"MCP_SCOPE_ROOT": tmp.name, "MCP_READONLY": "1", "MCP_ALLOW_WEB": "0"})
        self.assertNotIn("append_file", tool_names(m))


if __name__ == "__main__":
    unittest.main()
