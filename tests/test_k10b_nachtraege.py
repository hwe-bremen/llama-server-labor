#!/usr/bin/env python3
"""Tests fuer K10b (spec_20261027_k10b_nachtraege.md, T1–T4), nach R42 von Claude uebernommen.

Je Test-ID eine Methode; der Gegenfall steht in derselben Methode, damit die Gegenprobe jeden Test
rot macht. T3 nutzt Basis aus tests/test_umsetzung_auto.py (Attrappe mit Temp-Sperre, Pruefung des
echten Repos). Neue Funktionen werden in den Methoden importiert.
"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
sys.path.insert(0, str(ECHT))
import kette  # noqa: E402
from tests.test_umsetzung_auto import Basis, HANDOVER  # noqa: E402

SPEC = "# Spec: k\n\n## Testplan\n\n### T1: Erster\n- x\n\n### T2: Zweiter Fall\n- y\n"
KOPF = ("| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |\n"
        "|---|---|---|---|---|---|---|---|\n")


class TempPM(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name).resolve()
        self.pm = self.root / "docs" / "projekt_management"
        self.pm.mkdir(parents=True)
        for name, wert in (("ROOT", self.root), ("PM", self.pm)):
            alt = getattr(kette, name)
            setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)

    def leise(self, f, *a):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = f(*a)
        return code, aus.getvalue()


class PromptTests(TempPM):
    def test_t1_pflichtzeilen_im_prompt(self):
        """T1: Prompt nennt je Test-ID eine Pflichtzeile"""
        from kette import _umsetzung_prompt
        (self.pm / "spec_20261027_k.md").write_text(SPEC, encoding="utf-8")
        text = _umsetzung_prompt("k", "20261027", "abc1234", None, 1)
        self.assertIn("## Pflichtzeilen im Handover", text)
        self.assertIn("**T1: Erster** – bestanden | fehlgeschlagen", text)
        self.assertIn("**T2: Zweiter Fall** – bestanden | fehlgeschlagen", text)
        # Spec-Reihenfolge, nicht Textsortierung: T2 vor T10
        (self.pm / "spec_20261027_k.md").write_text("# Spec: k\n\n### T2: Zwei\n- x\n\n### T10: Zehn\n- y\n",
                                                   encoding="utf-8")
        text = _umsetzung_prompt("k", "20261027", "abc1234", None, 1)
        self.assertLess(text.index("**T2: Zwei**"), text.index("**T10: Zehn**"))
        # Gegenfall: Spec ohne Test-IDs -> kein Abschnitt
        (self.pm / "spec_20261027_k.md").write_text("# Spec: k\n\n## Ziel\nx\n", encoding="utf-8")
        text = _umsetzung_prompt("k", "20261027", "abc1234", None, 1)
        self.assertNotIn("Pflichtzeilen", text)


class AbgleichTests(TempPM):
    def handover(self, nicht):
        (self.pm / "spec_20261027_k.md").write_text(SPEC, encoding="utf-8")
        (self.pm / "handover_20261027_k.md").write_text(
            "# Handover\n\n## Getestet (mit echter Ausgabe)\n\n**T1: Erster** – bestanden\n\n"
            f"## Nicht getestet\n\n{nicht}\n", encoding="utf-8")

    def test_t2_bereich_zaehlt_nicht(self):
        """T2: abgleich – Bereich „T1–T2“ unter Nicht getestet ist keine Einzelnennung"""
        self.handover("- Nichts, alle Tests (T1–T2) laufen grün.")
        code, out = self.leise(kette.abgleich, "k")
        self.assertIn("FEHLT     T2", out)
        self.assertNotIn("NICHT GET", out)
        self.assertEqual(code, 1)
        # Gegenfall: einzeln genannte Test-ID bleibt "nicht getestet"
        self.handover("- T2: braucht einen echten Server.")
        code, out = self.leise(kette.abgleich, "k")
        self.assertIn("NICHT GET T2", out)


class TokenTests(Basis):
    def test_t3_tokens_spitze(self):
        """T3: Tokens – Spitze je Schritt im Protokoll und auf stdout"""
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 0, out)
        self.assertIn("Tokens 150 (Spitze 100)", out)
        self.assertIn("  - Tokens: input 130, output 18, reasoning 2, spitze 100", self.protokoll())


class ZusammenfuehrenTests(TempPM):
    def verdikte(self, zeilen1, ergebnis1="PASS"):
        p1 = self.pm / "verdict_20261027_k_qwen36-35b.md"
        p2 = self.pm / "verdict_20261027_k_qwen36-35b_betrieb.md"
        p1.write_text(f"# V\n\n## Ergebnis\n\n{ergebnis1}\n\n## Befunde\n\n{KOPF}{zeilen1}", encoding="utf-8")
        p2.write_text(f"# V\n\n## Ergebnis\n\nPASS\n\n## Befunde\n\n{KOPF}"
                      "| – | nein | nein | nein | – | – | keine Befunde | – |\n", encoding="utf-8")
        return [p1, p2]

    def test_t4_zurueckgezogen_nicht_hoch(self):
        """T4: zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht"""
        pfade = self.verdikte("| 1 | nein | nein | nein | hoch | `x.py:1` | Prüfung X ist da. **Befund entfällt.** | – |\n"
                              "| 2 | nein | ja | nein | hoch | `x.py:2` | Fall Y: Exit 2. **Korrekt.** | – |\n")
        code, out = self.leise(kette.zusammenfuehren, pfade)
        self.assertEqual(code, 0, out)
        self.assertIn("davon 0 hoch, 2 zurückgezogen -> PASS", out)
        gesamt = (self.pm / "gesamt_20261027_k.md").read_text(encoding="utf-8")
        self.assertEqual(gesamt.count("| nein (zurückgezogen) |"), 2)
        self.assertIn("Befund entfällt.", gesamt)               # nichts weggelassen
        # Gegenfall: echter hoher Befund bleibt hoch
        pfade = self.verdikte("| 1 | nein | nein | nein | hoch | `x.py:1` | Timeout fehlt, Lauf hängt unbegrenzt. | – |\n")
        code, out = self.leise(kette.zusammenfuehren, pfade)
        self.assertEqual(code, 1, out)
        self.assertIn("davon 1 hoch -> NACHBESSERN", out)


if __name__ == "__main__":
    unittest.main()
