#!/usr/bin/env python3
"""Vorgabe-Tests fuer K11a vorgabe_tests (spec_20261027_vorgabe_tests.md, T1–T8).

VORGABE: Diese Datei hat Claude vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: T1–T5 arbeiten in tempfile.TemporaryDirectory() mit umgebogenem kette.ROOT/kette.PM;
T6–T8 nutzen die Testklasse Basis aus tests/test_umsetzung_auto.py (eigenes Temp-Git-Repo, Attrappe
opencode_fake.py mit Temp-Sperre, Pruefung am Ende, dass das echte Repo unveraendert ist).
Neue Funktionen werden in den Methoden importiert, damit die Gegenprobe je Test aussagekraeftig ist.
"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT))
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402
from tests.test_umsetzung_auto import Basis, DATUM, HANDOVER  # noqa: E402

SPEC_K = ("# Spec: k\n\n## Ziel\nx\n\n## Vorgabe-Tests\n\n- `tests/test_k.py`\n\n"
          "## Testplan\n\n### T1: Erster\n- **Erwartung:** a\n\n### T2: Zweiter\n- **Erwartung:** b\n")
# Beide Tests rot ohne Umsetzung: neue Funktion wird in der Methode importiert.
ROT = ("import unittest\n\nclass K(unittest.TestCase):\n"
       "    def test_t1_erster(self):\n        from neu import f\n        self.assertEqual(f(), 1)\n\n"
       "    def test_t2_zweiter(self):\n        from neu import g\n        self.assertEqual(g(), 2)\n")


class Temp(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name).resolve()
        self.pm = self.root / "docs" / "projekt_management"
        self.pm.mkdir(parents=True)
        (self.root / "tests").mkdir()
        for name, wert in (("ROOT", self.root), ("PM", self.pm)):
            alt = getattr(kette, name)
            setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)
        (self.pm / "spec_20261028_k.md").write_text(SPEC_K, encoding="utf-8")

    def schreibe_testdatei(self, text: str):
        (self.root / "tests" / "test_k.py").write_text(text, encoding="utf-8")

    def rufen(self, fn, *a):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = fn(*a)
        return code, aus.getvalue()


class TestsPruefen(Temp):

    def test_t1_tests_pruefen_rot_vorab_ok(self):
        """T1: tests-pruefen – alle Vorgabe-Tests vorhanden und rot vorab"""
        from kette import tests_pruefen
        self.schreibe_testdatei(ROT)
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 0, out)
        self.assertIn("rot       T1", out)
        self.assertIn("rot       T2", out)
        self.assertIn("Keine Abweichung.", out)
        code2, out2 = self.rufen(kette.main, ["tests-pruefen", "k"])
        self.assertEqual(code2, 0, out2)

    def test_t2_tests_pruefen_test_fehlt(self):
        """T2: tests-pruefen – Test-ID ohne Methode"""
        from kette import tests_pruefen
        self.schreibe_testdatei(ROT.split("    def test_t2_zweiter")[0])
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 1, out)
        self.assertIn("FEHLT     T2", out)
        self.assertIn("rot       T1", out)

    def test_t3_tests_pruefen_gruen_ohne_umsetzung(self):
        """T3: tests-pruefen – Test ohne Umsetzung schon gruen"""
        from kette import tests_pruefen
        self.schreibe_testdatei(ROT.replace("from neu import f\n        self.assertEqual(f(), 1)",
                                         "self.assertEqual(1, 1)"))
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 1, out)
        self.assertIn("NICHT ROT T1", out)
        self.assertIn("rot       T2", out)

    def test_t4_tests_pruefen_laedt_nicht(self):
        """T4: tests-pruefen – Testskript laedt nicht"""
        from kette import tests_pruefen
        self.schreibe_testdatei("from neu import f\n" + ROT)
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 1, out)
        self.assertIn("LAEDT NICHT", out)
        self.assertNotIn("rot       T1", out)

    def test_t5_tests_pruefen_voraussetzung_fehlt(self):
        """T5: tests-pruefen – Testdatei oder Spec fehlt"""
        from kette import tests_pruefen
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 2, out)
        self.assertIn("tests/test_k.py", out)
        self.schreibe_testdatei(ROT)
        (self.pm / "spec_20261028_k.md").unlink()
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 2, out)


SPEC_VORGABE = (
    "# Spec: g\n\n## Ziel\nTest.\n\n## Schreibbereich\n\n"
    "- `src/`\n- `role-split/kette/`\n- `docs/projekt_management/`\n- `tests/`\n\n"
    "## Vorgabe-Tests\n\n- `tests/test_g.py`\n\n"
    "## Testplan\n\n### T1: Erster\n- **Erwartung:** x\n"
)
ROT_G = ("import unittest\n\nclass G(unittest.TestCase):\n"
         "    def test_t1_erster(self):\n        from src.neu import f\n        self.assertEqual(f(), 1)\n")
GRUEN_G = ROT_G.replace("from src.neu import f\n        self.assertEqual(f(), 1)", "self.assertTrue(True)")


class UmsetzungMitVorgabe(Basis):

    def vorgabe(self, testcode: str, spec: str = SPEC_VORGABE, nachricht: str = "Tests g"):
        (self.pm / f"spec_{DATUM}_g.md").write_text(spec, encoding="utf-8")
        (self.root / "tests").mkdir(exist_ok=True)
        (self.root / "tests" / "test_g.py").write_text(testcode, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", nachricht)

    def prompt_text(self) -> str:
        return json.loads(self.argsdatei.read_text(encoding="utf-8"))[-1]

    def test_t6_erstlauf_nur_mit_rot_vorab(self):
        """T6: umsetzung-auto – Erstlauf startet nur mit bestandener Testpruefung"""
        self.vorgabe(GRUEN_G)
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 2, out)
        self.assertFalse(self.gestartet(), out)
        self.assertIn("NICHT ROT T1", out)
        self.vorgabe(ROT_G)
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 0, out)
        self.assertTrue(self.gestartet(), out)
        self.assertIn("## Vorgabe-Tests", self.prompt_text())
        self.assertIn("Du änderst diese Datei nicht", self.prompt_text())

    def test_t7_vorgabe_tests_geaendert(self):
        """T7: umsetzung-auto – Aenderung an Vorgabe-Tests ist ein Verstoss"""
        # Gegenfall zuerst: ohne Abschnitt Vorgabe-Tests darf der Umsetzer die Testdatei schreiben.
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_EDIT="tests/test_g.py")
        self.assertEqual(code, 0, out)
        self.assertNotIn("Vorgabe-Tests", out)
        self.assertNotIn("## Vorgabe-Tests", self.prompt_text())
        self.argsdatei.unlink()
        self.vorgabe(ROT_G, nachricht="zwischen")
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_EDIT="tests/test_g.py")
        self.assertEqual(code, 1, out)
        self.assertIn("Vorgabe-Tests in diesem Lauf geändert: tests/test_g.py", out)
        self.assertNotIn("Schreibbereich verletzt", out)

    def test_t8_nacharbeit_ohne_rot_vorab(self):
        """T8: umsetzung-auto – Nacharbeit prueft nicht auf rot vorab, Prompt nennt Vorgabe"""
        self.vorgabe(GRUEN_G)
        datei = self.nacharbeit_vorbereiten()
        code, out = self.lauf(nacharbeit=str(datei), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG=1)
        self.assertTrue(self.gestartet(), out)
        self.assertEqual(code, 0, out)
        self.assertNotIn("NICHT ROT", out)
        self.assertIn("## Vorgabe-Tests", self.prompt_text())


if __name__ == "__main__":
    unittest.main()
