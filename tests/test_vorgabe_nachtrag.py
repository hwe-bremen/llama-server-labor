#!/usr/bin/env python3
"""Vorgabe-Tests fuer K11a2 vorgabe_nachtrag (spec_20261028_vorgabe_nachtrag.md, T1–T4).

VORGABE: Diese Datei hat Claude vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: T1–T3 arbeiten in tempfile.TemporaryDirectory() mit umgebogenem kette.ROOT/kette.PM
(T3 mit eigenem Temp-Git-Repo); T4 nutzt Basis aus tests/test_umsetzung_auto.py (Temp-Git-Repo, Attrappe
opencode_fake.py mit Temp-Sperre, Pruefung am Ende, dass das echte Repo unveraendert ist).
Jede Methode enthaelt einen Teil, der mit dem alten kette.py rot wird (rot vorab).
"""
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT))
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402
from tests.test_umsetzung_auto import Basis, DATUM, HANDOVER  # noqa: E402

SPEC_K = ("# Spec: k\n\n## Ziel\nx\n\n## Vorgabe-Tests\n\n- `tests/test_k.py`\n\n"
          "## Testplan\n\n### T1: Neu\n- **Erwartung:** a\n\n### T2: Altes Verhalten bleibt (Bestand)\n- **Erwartung:** b\n")
# T1 rot ohne Umsetzung, T2 prueft Bestehendes und ist gruen.
TESTS_K = ("import unittest\n\nclass K(unittest.TestCase):\n"
           "    def test_t1_neu(self):\n        from neu import f\n        self.assertEqual(f(), 1)\n\n"
           "    def test_t2_bestand(self):\n        self.assertEqual(1 + 1, 2)\n")


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

    def datei(self, rel: str, text: str):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    def rufen(self, fn, *a):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = fn(*a)
        return code, aus.getvalue()


class TestsPruefenBestand(Temp):

    def test_t1_bestand_gruen_ok_und_spec_ohne_ids(self):
        """T1: tests-pruefen – Bestand-Test gruen ist in Ordnung; Spec ohne Test-ID ist Exit 2"""
        from kette import tests_pruefen
        self.datei("docs/projekt_management/spec_20261028_k.md", SPEC_K)
        self.datei("tests/test_k.py", TESTS_K)
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 0, out)
        self.assertIn("rot       T1", out)
        self.assertIn("gruen     T2", out)
        self.assertIn("Keine Abweichung.", out)
        # Befund 1 (K11a-Gegenpruefung): Spec ohne Test-ID -> Exit 2, nicht "Keine Abweichung."
        self.datei("docs/projekt_management/spec_20261028_k.md", "# Spec: k\n\n## Ziel\nx\n\n## Vorgabe-Tests\n")
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 2, out)
        self.assertNotIn("Keine Abweichung.", out)

    def test_t2_bestand_rot_und_timeout_weitergereicht(self):
        """T2: tests-pruefen – Bestand-Test rot ist eine Abweichung; --timeout wird weitergereicht"""
        from kette import tests_pruefen
        self.datei("docs/projekt_management/spec_20261028_k.md", SPEC_K)
        self.datei("tests/test_k.py", TESTS_K.replace("self.assertEqual(1 + 1, 2)", "self.assertEqual(1 + 1, 3)"))
        code, out = self.rufen(tests_pruefen, "k")
        self.assertEqual(code, 1, out)
        self.assertIn("NICHT GRUEN T2", out)
        self.assertIn("rot       T1", out)
        # Befund 5: main reicht --timeout an tests_laufen weiter
        gesehen = []

        def attrappe(skript, timeout):
            gesehen.append(timeout)
            return {"test_t1_neu": "FAIL", "test_t2_bestand": "ok"}
        with mock.patch.object(kette, "tests_laufen", attrappe):
            code, out = self.rufen(kette.main, ["tests-pruefen", "k", "--timeout", "7"])
        self.assertEqual(gesehen, [7], out)
        self.assertEqual(code, 0, out)


class GegenprobeBestand(Temp):

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, text=True).stdout

    def test_t3_gegenprobe_bestand_gruen_zaehlt_nicht(self):
        """T3: gegenprobe – gruener Bestand-Test laut Spec ist keine Abweichung"""
        spec_ohne = SPEC_K.replace(" (Bestand)", "")
        self.datei("docs/projekt_management/spec_20261028_k.md", spec_ohne)
        self.datei("src/m.py", "X = 1\n")
        self.datei("tests/test_k.py",
                   "import unittest\n\nclass K(unittest.TestCase):\n"
                   "    def test_t1_neu(self):\n        from src.m import f\n        self.assertEqual(f(), 1)\n\n"
                   "    def test_t2_bestand(self):\n        from src.m import X\n        self.assertEqual(X, 1)\n")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "Spec k")
        commit = self.git("rev-parse", "--short", "HEAD").strip()
        self.datei("src/m.py", "X = 1\n\ndef f():\n    return 1\n")
        # Gegenfall: ohne Kennzeichnung bleibt ein gruener Test eine Abweichung
        code, out = self.rufen(kette.gegenprobe, "k", commit)
        self.assertEqual(code, 1, out)
        self.assertIn("GRUEN test_t2_bestand", out)
        # mit "(Bestand)" im Titel: kein Befund, eigene Zeile
        self.datei("docs/projekt_management/spec_20261028_k.md", SPEC_K)
        code, out = self.rufen(kette.gegenprobe, "k", commit)
        self.assertEqual(code, 0, out)
        self.assertIn("BESTAND test_t2_bestand", out)
        self.assertNotIn("GRUEN test_t2_bestand", out)
        self.assertIn("rot   test_t1_neu", out)


SPEC_VORGABE = (
    "# Spec: g\n\n## Ziel\nTest.\n\n## Schreibbereich\n\n"
    "- `src/`\n- `role-split/kette/`\n- `docs/projekt_management/`\n\n"
    "## Vorgabe-Tests\n\n- `tests/test_g.py`\n\n"
    "## Testplan\n\n### T1: Erster\n- **Erwartung:** x\n"
)
ROT_G = ("import unittest\n\nclass G(unittest.TestCase):\n"
         "    def test_t1_erster(self):\n        from src.neu import f\n        self.assertEqual(f(), 1)\n")
VORGABE_TEXT = ("Abweichend von den Testregeln oben: Die Tests stehen schon in tests/test_g.py. Du änderst diese "
                "Datei nicht – keine Zeile. Schreib nur den Code, bis python3 -m unittest -v tests/test_g.py grün ist. "
                "Passt ein Test nicht zur Spec, nenne ihn im Handover unter „Abweichungen“.")


class NacharbeitVorgabe(Basis):

    def test_t4_nacharbeit_mit_offener_testdatei(self):
        """T4: umsetzung-auto – Nacharbeit startet nicht, solange die Vorgabe-Tests offene Aenderungen haben"""
        (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC_VORGABE, encoding="utf-8")
        (self.root / "tests").mkdir(exist_ok=True)
        (self.root / "tests" / "test_g.py").write_text(ROT_G, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Tests g")
        datei = self.nacharbeit_vorbereiten()
        (self.root / "tests" / "test_g.py").write_text(ROT_G + "# vom Erstlauf geschwaecht\n", encoding="utf-8")
        code, out = self.lauf(nacharbeit=str(datei), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG=1)
        self.assertEqual(code, 2, out)
        self.assertFalse(self.gestartet(), out)
        self.assertIn("tests/test_g.py", out)
        self.assertIn("git restore", out)
        # bewusste Korrektur committet -> Nacharbeit startet; Prompt-Abschnitt vollstaendig und an der richtigen Stelle
        self.git("add", "tests/test_g.py")
        self.git("commit", "-qm", "Korrektur Vorgabe-Test")
        code, out = self.lauf(nacharbeit=str(datei), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG=1)
        self.assertTrue(self.gestartet(), out)
        self.assertEqual(code, 0, out)
        prompt = json.loads(self.argsdatei.read_text(encoding="utf-8"))[-1]
        self.assertIn("## Vorgabe-Tests\n\n" + VORGABE_TEXT, prompt)
        self.assertLess(prompt.index("## Pflichtzeilen im Handover"), prompt.index("## Vorgabe-Tests"))
        self.assertLess(prompt.index("## Vorgabe-Tests"), prompt.index("## Nachbesserung 1"))


if __name__ == "__main__":
    unittest.main()
