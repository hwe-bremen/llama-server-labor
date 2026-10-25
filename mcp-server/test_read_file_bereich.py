#!/usr/bin/env python3
"""Tests: read_file mit Zeilenbereich (Kontext schonen, 25.10.).

Aufruf:  cd mcp-server && .venv/bin/python -m unittest test_read_file_bereich -v
Anlass: Spec-Chat K8 lief voll, weil read_file immer die ganze Datei liefert.
"""
import tempfile
import unittest
from pathlib import Path

from test_search_files import load


class ReadFileBereichTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "gross.py").write_text("".join(f"zeile {i}\n" for i in range(1, 401)))
        (self.root / "klein.txt").write_text("a\nb\nc\n")
        (self.root / "geheim").mkdir()
        (self.root / "geheim" / "x.txt").write_text("nein\n")
        self.m = load({"MCP_SCOPE_ROOT": str(self.root), "MCP_READONLY": "1",
                       "MCP_ALLOW_WEB": "0", "MCP_DENY": "geheim"})

    def tearDown(self):
        self.tmp.cleanup()

    def test_ohne_bereich_wie_bisher(self):
        self.assertEqual(self.m.read_file("klein.txt"), "a\nb\nc\n")

    def test_bereich_mit_zeilennummern(self):
        r = self.m.read_file("gross.py", 10, 12)
        self.assertIn("Zeilen 10–12 von 400", r)
        self.assertIn("10| zeile 10", r)
        self.assertIn("12| zeile 12", r)
        self.assertNotIn("zeile 13", r)
        self.assertNotIn("zeile 9\n", r)

    def test_nur_start_bis_ende(self):
        r = self.m.read_file("gross.py", 399)
        self.assertIn("Zeilen 399–400 von 400", r)
        self.assertIn("400| zeile 400", r)

    def test_nur_ende_ab_anfang(self):
        r = self.m.read_file("gross.py", 0, 2)
        self.assertIn("Zeilen 1–2 von 400", r)

    def test_ende_ueber_dateiende_wird_gekappt(self):
        self.assertIn("Zeilen 398–400 von 400", self.m.read_file("gross.py", 398, 9999))

    def test_start_hinter_dateiende(self):
        self.assertIn("nur 400 Zeilen", self.m.read_file("gross.py", 500, 510))

    def test_vertauschter_bereich(self):
        self.assertIn("Leerer Bereich", self.m.read_file("gross.py", 20, 10))

    def test_negativ_verweigert(self):
        self.assertIn("nicht negativ", self.m.read_file("gross.py", -5, 10))

    def test_text_statt_zahl(self):
        self.assertIn("ganze Zahlen", self.m.read_file("gross.py", "abc", 3))

    def test_zahl_als_text_geht(self):
        self.assertIn("Zeilen 5–6 von 400", self.m.read_file("gross.py", "5", "6"))

    def test_hinweis_bei_grosser_datei(self):
        r = self.m.read_file("gross.py")
        self.assertIn("zeile 400", r)
        self.assertIn("start_line/end_line", r)

    def test_kein_hinweis_bei_kleiner_datei(self):
        self.assertNotIn("Hinweis", self.m.read_file("klein.txt"))

    def test_sperre_gilt_auch_mit_bereich(self):
        with self.assertRaises(Exception):
            self.m.read_file("geheim/x.txt", 1, 1)

    def test_traversal_mit_bereich(self):
        with self.assertRaises(Exception):
            self.m.read_file("../../etc/passwd", 1, 3)


if __name__ == "__main__":
    unittest.main()
