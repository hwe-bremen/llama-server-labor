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
            "def test_t1_x(): assert 1\ndef test_t2_x(): assert 2\ndef test_t3(): assert 3\n", encoding="utf-8")
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


DS = chr(34) * 3

class MethodenTests(unittest.TestCase):
    def test_leere_und_doppelte_methoden(self):
        code = (
            "import unittest\n"
            "class A(unittest.TestCase):\n"
            "    def test_t1_ok(self):\n        self.assertEqual(1, 1)\n"
            "    def test_t2_leer(self):\n        x = 1\n"
            "    def test_t3_kopie(self):\n        " + DS + "anderer Docstring" + DS + "\n        self.assertEqual(1, 1)\n"
            "    def test_t4_raises(self):\n        with self.assertRaises(ValueError):\n            int('x')\n")
        h = kette.methoden_pruefen(code)
        self.assertTrue(any("OHNE PRUEF test_t2_leer" in x for x in h), h)
        self.assertTrue(any("DOPPELT   test_t3_kopie" in x for x in h), h)
        self.assertFalse(any("test_t4_raises" in x for x in h), h)


class GegenprobeTests(unittest.TestCase):
    def test_rot_und_gruen(self):
        import subprocess
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        root = Path(d.name)
        def git(*a):
            subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                           check=True, capture_output=True)
        git("init", "-q")
        (root / "mod.py").write_text("def f():\n    return 1\n")
        git("add", "."); git("commit", "-qm", "alt")
        alt = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        (root / "mod.py").write_text("def f():\n    return 2\n")
        (root / "neu.py").write_text("X = 1\n")
        (root / "tests").mkdir()
        (root / "tests" / "test_g.py").write_text(
            "import sys, unittest\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent))\n"
            "class T(unittest.TestCase):\n"
            "    def test_t1_neu(self):\n        import mod\n        self.assertEqual(mod.f(), 2)\n"
            "    def test_t2_bestand(self):\n        self.assertEqual(1, 1)\n")
        alt_root = kette.ROOT; kette.ROOT = root
        self.addCleanup(lambda: setattr(kette, "ROOT", alt_root))
        code, out = lauf(kette.gegenprobe, "g", alt, 60)
        self.assertEqual(code, 1, out)
        self.assertIn("rot   test_t1_neu  <- mod.py", out)
        self.assertIn("GRUEN test_t2_bestand", out)
        self.assertEqual((root / "mod.py").read_text(), "def f():\n    return 2\n")
        self.assertTrue((root / "neu.py").exists())


class PromptTests(unittest.TestCase):
    def test_alle_vorlagen_fuellbar(self):
        for s in kette.SCHRITTE:
            code, out = lauf(kette.prompt, s, "mein_thema", "20261018", "abc1234")
            self.assertEqual(code, 0, s)
            self.assertNotIn("{", out, s)
            self.assertIn("mein_thema", out, s)



class AnforderungTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        root = Path(self.d.name); (root / "docs/projekt_management").mkdir(parents=True)
        self.alt = (kette.ROOT, kette.PM)
        kette.ROOT, kette.PM = root, root / "docs/projekt_management"
        self.addCleanup(lambda: setattr(kette, "ROOT", self.alt[0]) or setattr(kette, "PM", self.alt[1]))

    def test_anlegen_antwort_und_kein_ueberschreiben(self):
        code, _ = lauf(kette.anforderung, "t", "Zweitlauf darf nichts verlieren.\nZweite Zeile.", None, None, "20261018")
        self.assertEqual(code, 0)
        p = kette.PM / "anforderung_20261018_t.md"
        self.assertEqual(kette.aufgabe_lesen(p), "Zweitlauf darf nichts verlieren.\nZweite Zeile.")
        code, _ = lauf(kette.anforderung, "t", None, "Jeder Eintrag genau einmal per Mail.", "Mail nach Zweitlauf?", None)
        self.assertEqual(code, 0)
        text = p.read_text(encoding="utf-8")
        self.assertIn("> Jeder Eintrag genau einmal per Mail.", text)
        self.assertIn("Frage: Mail nach Zweitlauf?", text)
        code, _ = lauf(kette.anforderung, "t", "anders", None, None, None)
        self.assertEqual(code, 2, "vorhandene Anforderung darf nicht ueberschrieben werden")
        self.assertIn("Zweitlauf darf nichts verlieren.", p.read_text(encoding="utf-8"))

    def test_spec_prompt_fuellt_aufgabe(self):
        lauf(kette.anforderung, "t", "Zweitlauf darf nichts verlieren.", None, None, "20261018")
        code, out = lauf(kette.prompt, "spec", "t", None, "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("Zweitlauf darf nichts verlieren.", out)
        self.assertNotIn("<AUFGABE", out)
        self.assertIn("docs/projekt_management/anforderung_20261018_t.md", out)
        self.assertIn("spec_20261018_t.md", out)

    def test_review_nimmt_datum_der_spec(self):
        lauf(kette.anforderung, "t", "Aufgabe.", None, None, "20261018")
        (kette.PM / "spec_20261018_t.md").write_text("# Spec\n", encoding="utf-8")
        code, out = lauf(kette.prompt, "review", "t", None, "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("spec_20261018_t.md", out)
        self.assertIn("handover_20261018_t.md", out)
        self.assertIn("anforderung_20261018_t.md", out)
        self.assertNotIn("{", out)

    def test_ohne_anforderung_platzhalterpfad(self):
        code, out = lauf(kette.prompt, "review", "x", "20261020", "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("anforderung_20261020_x.md", out)



class QuellenTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        root = Path(self.d.name); (root / "docs/projekt_management").mkdir(parents=True); (root / "src").mkdir()
        self.alt = (kette.ROOT, kette.PM)
        kette.ROOT, kette.PM = root, root / "docs/projekt_management"
        self.addCleanup(lambda: setattr(kette, "ROOT", self.alt[0]) or setattr(kette, "PM", self.alt[1]))
        (root / "src/mod.py").write_text(
            "MAGIC = 0x46554747\n\n\n@dekor\ndef lesen(f):\n    kopf = f.read(4)\n\n    return kopf\n\n\n"
            "class Feld:\n    TYPEN = {0: 'u8'}\n\n    def wert(self):\n        return 1\n\n\ndef danach():\n    pass\n",
            encoding="utf-8")
        (root / "src/kurz.txt").write_text("a\nb\n", encoding="utf-8")

    def spec(self, quellen: str):
        (kette.PM / "spec_20261021_t.md").write_text(f"# Spec\n\n## Quellen\n\n{quellen}\n## Anforderungen\n", encoding="utf-8")

    def ergebnis(self):
        return (kette.PM / "quellen_20261021_t.md").read_text(encoding="utf-8")

    def test_zeilen_def_class_ganz(self):
        self.spec("- `src/mod.py` Zeilen 1–1 – Magic\n- `src/mod.py` def lesen – Kopf\n"
                  "- `src/mod.py` class Feld – Typen\n- `src/kurz.txt` – ganz\n")
        code, out = lauf(kette.quellen, "t", None)
        self.assertEqual(code, 0, out)
        t = self.ergebnis()
        self.assertIn("1| MAGIC = 0x46554747", t)
        self.assertIn("@dekor", t, "Dekorator gehoert zur def")
        self.assertIn("return kopf", t)
        self.assertIn("return 1", t, "Methode gehoert zur class")
        self.assertNotIn("def danach", t, "naechste Funktion gehoert nicht dazu")
        self.assertIn("1| a", t); self.assertIn("2| b", t)
        self.assertIn("– Kopf", t)

    def test_fehlt_und_verweigert(self):
        self.spec("- `src/gibtsnicht.py` – x\n- `../../etc/passwd` – x\n- `src/mod.py` def fehlt – x\n")
        code, out = lauf(kette.quellen, "t", None)
        self.assertEqual(code, 1)
        t = self.ergebnis()
        self.assertEqual(t.count("**FEHLT:**"), 2)
        self.assertIn("**VERWEIGERT:**", t)

    def test_ohne_abschnitt(self):
        (kette.PM / "spec_20261021_t.md").write_text("# Spec\n\n## Anforderungen\n", encoding="utf-8")
        code, _ = lauf(kette.quellen, "t", None)
        self.assertEqual(code, 2)

    def test_umsetzung_prompt_nennt_quellen(self):
        self.spec("- `src/kurz.txt` – ganz\n")
        code, out = lauf(kette.prompt, "umsetzung", "t", None, "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("docs/projekt_management/quellen_20261021_t.md", out)
        self.assertNotIn("{", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
