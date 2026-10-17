#!/usr/bin/env python3
"""Selbsttest fuer kette.py (stdlib, ohne Modell):  python3 role-split/kette/test_kette.py"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kette  # noqa: E402

KOPF = "# Verdikt: x\n\n## Ergebnis\n\n**{u}** – Text.\n\n## Anforderungen einzeln\n\n" \
       "| Nr. | Anforderung | Befund | Fundstelle |\n|---|---|---|---|\n{anf}\n\n## Befunde\n\n" \
       "| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg |\n" \
       "|---|---|---|---|---|---|---|---|\n{bef}\n"


def lauf(fn, *a):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = fn(*a)
    return code, buf.getvalue()


class UrteilTests(unittest.TestCase):
    def verdikt(self, u, anf, bef):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        p = Path(d.name) / "verdict_x.md"
        p.write_text(KOPF.format(u=u, anf=anf, bef=bef), encoding="utf-8")
        return p

    def test_haenger_als_niedrig_wird_hoch(self):
        # Tiefenpruefung 17.10. im neuen Format: Timeout fehlt, 'niedrig', aber Fehler bleibt unbemerkt
        p = self.verdikt("PASS", "| A1 | Fehler-Mail | erfüllt | x.py:1 |",
                         "| 3 | nein | ja | nein | niedrig | x.py:192 | kein SMTP-Timeout | timeout= setzen |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 1)
        self.assertIn("Es gilt:             NACHBESSERN", out)
        self.assertIn("WIDERSPRUCH", out)
        self.assertIn("Befund 3", out)

    def test_harte_vorgabe_echter_versand(self):
        p = self.verdikt("NACHBESSERN", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | nein | ja | niedrig | handover | echter Versand im Test | Sperre |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 1)
        self.assertIn("Harte Vorgabe -> hoch", out)

    def test_teilweise_erfuellt_verhindert_pass(self):
        p = self.verdikt("PASS", "| A2 | x | teilweise erfüllt | x |",
                         "| 1 | nein | nein | nein | niedrig | x | Kosmetik | - |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 1)
        self.assertIn("Anforderungen offen", out)

    def test_sauberes_pass_bleibt(self):
        p = self.verdikt("PASS", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | nein | nein | niedrig | x | Kosmetik | - |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 0)
        self.assertNotIn("WIDERSPRUCH", out)

    def test_regel_schwaecht_nie_ab(self):
        p = self.verdikt("FAIL", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | nein | nein | niedrig | x | x | - |")
        code, out = lauf(kette.urteil, p)
        self.assertIn("Es gilt:             FAIL", out)

    def test_anhaengen_nur_einmal(self):
        p = self.verdikt("PASS", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | ja | nein | mittel | x | x | - |")
        lauf(kette.urteil, p, True); lauf(kette.urteil, p, True)
        self.assertEqual(p.read_text(encoding="utf-8").count("## Mechanisches Urteil"), 1)


class AbgleichTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        root = Path(self.d.name); (root / "docs/projekt_management").mkdir(parents=True)
        self.alt = (kette.ROOT, kette.PM)
        kette.ROOT, kette.PM = root, root / "docs/projekt_management"
        self.addCleanup(lambda: setattr(kette, "ROOT", self.alt[0]) or setattr(kette, "PM", self.alt[1]))
        (kette.PM / "spec_20261018_t.md").write_text(
            "# Spec\n\n## Testplan\n\n### T1: Timeout bei schweigendem Server (A1)\n\n"
            "### T2: Fehler-Mail ohne markdown-Paket (A6)\n\n### T3: Zaehler im Dateinamen (A4)\n",
            encoding="utf-8")

    def handover(self, getestet, nicht=""):
        (kette.PM / "handover_20261018_t.md").write_text(
            f"# Handover\n\n## Getestet (mit echter Ausgabe)\n\n{getestet}\n\n## Nicht getestet\n\n{nicht}\n",
            encoding="utf-8")

    def test_ausgetauschter_test_wird_erkannt(self):
        self.handover("**T1: Timeout bei schweigendem Server**\n**T2: Pipeline ohne --dry-run**\n"
                      "**T3: Zaehler im Dateinamen**")
        code, out = lauf(kette.abgleich, "t")
        self.assertEqual(code, 1)
        self.assertIn("ANDERS    T2", out)

    def test_fehlender_und_nicht_getesteter(self):
        self.handover("**T1: Timeout bei schweigendem Server**", "- T3: kein Mock moeglich")
        code, out = lauf(kette.abgleich, "t")
        self.assertIn("FEHLT     T2", out)
        self.assertIn("NICHT GET T3", out)

    def test_alles_passend_mit_testskript(self):
        self.handover("**T1: Timeout bei schweigendem Server (A1)**\n**T2: Fehler-Mail ohne markdown-Paket**\n"
                      "**T3: Zaehler im Dateinamen**")
        (kette.ROOT / "tests").mkdir()
        (kette.ROOT / "tests/test_t.py").write_text(
            "def test_t1_x(): pass\ndef test_t2_x(): pass\ndef test_t3(): pass\n", encoding="utf-8")
        code, out = lauf(kette.abgleich, "t")
        self.assertEqual(code, 0, out)
        self.assertIn("alle 3 Tests als Methode", out)

    def test_testskript_ohne_methode(self):
        self.handover("**T1: Timeout bei schweigendem Server**\n**T2: Fehler-Mail ohne markdown-Paket**\n"
                      "**T3: Zaehler im Dateinamen**")
        (kette.ROOT / "tests").mkdir()
        (kette.ROOT / "tests/test_t.py").write_text("def test_t1_x(): pass\n", encoding="utf-8")
        code, out = lauf(kette.abgleich, "t")
        self.assertEqual(code, 1)
        self.assertIn("T2, T3", out)


class PromptTests(unittest.TestCase):
    def test_alle_vorlagen_fuellbar(self):
        for s in kette.SCHRITTE:
            code, out = lauf(kette.prompt, s, "mein_thema", "20261018", "abc1234")
            self.assertEqual(code, 0, s)
            self.assertNotIn("{", out, s)
            self.assertIn("mein_thema", out, s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
