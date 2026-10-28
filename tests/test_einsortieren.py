#!/usr/bin/env python3
"""Vorgabe-Tests fuer K13b einsortieren (spec_20261028_einsortieren.md, T1–T7).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: Jeder Test arbeitet in tempfile.TemporaryDirectory() mit umgebogenem kette.ROOT/kette.PM.
einsortieren wird in jeder Methode importiert (rot vorab).
"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402

D = "20261028"


class Temp(unittest.TestCase):
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

    def dateien(self, *namen):
        for n in namen:
            (self.pm / n).write_text(f"# {n}\n", encoding="utf-8")

    def rufen(self, fn, *a):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = fn(*a)
        return code, aus.getvalue()


class Anlegen(Temp):

    def test_t1_neue_kette_bekommt_ordner(self):
        """T1: anforderung – neue Kette bekommt ihren Ordner"""
        code, out = self.rufen(kette.anforderung, "k", "Aufgabe X", None, None, D)
        self.assertEqual(code, 0, out)
        self.assertTrue((self.pm / "k" / f"anforderung_{D}_k.md").is_file(), out)
        self.assertFalse((self.pm / f"anforderung_{D}_k.md").exists())
        code, out = self.rufen(kette.anforderung, "k", None, "Antwort Y", "Frage?", None)
        self.assertEqual(code, 0, out)
        self.assertIn("> Antwort Y", (self.pm / "k" / f"anforderung_{D}_k.md").read_text(encoding="utf-8"))
        self.assertEqual(kette.ablage("k"), self.pm / "k")
        import einsortieren  # noqa: F401  (Modul muss existieren)


class Zuordnen(Temp):

    def test_t2_zuordnen_nach_name(self):
        """T2: zuordnen – Datei zur Kette, längster Kurztitel gewinnt"""
        from einsortieren import zuordnen
        kts = ["scout_mail", "scout_mail_trockenlauf", "k"]
        self.assertEqual(zuordnen(f"verdict_{D}_scout_mail_trockenlauf_qwen38-27b.md", kts), "scout_mail_trockenlauf")
        self.assertEqual(zuordnen(f"spec_{D}_scout_mail.md", kts), "scout_mail")
        self.assertEqual(zuordnen(f"pruefung_{D}_k.md", kts), "k")
        self.assertEqual(zuordnen(f"review_paket_{D}_k.md", kts), "k")
        self.assertEqual(zuordnen(f"spec_paket_{D}_k.md", kts), "k")
        self.assertEqual(zuordnen(f"nacharbeit_{D}_k_1.md", kts), "k")
        self.assertIsNone(zuordnen(f"handover_{D}_kx.md", kts))           # kein Praefix-Treffer
        self.assertIsNone(zuordnen("_vorlage_spec.md", kts))
        self.assertIsNone(zuordnen("verdict_kette4replay_qwen38-27b.md", kts + ["kette4replay"]))   # ohne Datum
        self.assertIsNone(zuordnen(f"review_{D}_k.md", kts))               # kein Kettentyp
        self.assertIsNone(zuordnen(f"verdict_{D}_probe_k5_qwen36-35b.md", kts))


class Einsortieren(Temp):

    def test_t3_einsortieren_einer_kette(self):
        """T3: einsortieren <kt> – nur die Dateien dieser Kette, Vorlagen und fremde bleiben"""
        from einsortieren import einsortieren
        self.dateien(f"spec_{D}_k.md", f"handover_{D}_k.md", f"verdict_{D}_k_qwen36-35b.md",
                     f"spec_{D}_andere.md", "_vorlage_spec.md")
        code, out = self.rufen(einsortieren, "k")
        self.assertEqual(code, 0, out)
        for n in (f"spec_{D}_k.md", f"handover_{D}_k.md", f"verdict_{D}_k_qwen36-35b.md"):
            self.assertTrue((self.pm / "k" / n).is_file(), n)
            self.assertFalse((self.pm / n).exists(), n)
        self.assertTrue((self.pm / f"spec_{D}_andere.md").is_file())
        self.assertTrue((self.pm / "_vorlage_spec.md").is_file())
        self.assertFalse((self.pm / "andere").exists())
        self.assertIn(f"verschoben  spec_{D}_k.md -> k/", out)
        self.assertIn("3 Datei(en) in 1 Ordner verschoben", out)
        code, out = self.rufen(einsortieren, "k")                          # zweiter Lauf: nichts mehr zu tun
        self.assertEqual(code, 0, out)
        self.assertIn("0 Datei(en) in 0 Ordner verschoben", out)

    def test_t4_alle_ueber_main(self):
        """T4: einsortieren --alle über kette.py – alle Ketten mit Spec oder Anforderung"""
        self.dateien(f"spec_{D}_a.md", f"pruefung_{D}_a.md", f"anforderung_{D}_b.md", f"gesamt_{D}_b.md",
                     f"verdict_{D}_probe_x_qwen.md", "_vorlage_spec.md")
        code, out = self.rufen(kette.main, ["einsortieren", "--alle"])
        self.assertEqual(code, 0, out)
        self.assertTrue((self.pm / "a" / f"pruefung_{D}_a.md").is_file(), out)
        self.assertTrue((self.pm / "b" / f"gesamt_{D}_b.md").is_file(), out)
        self.assertTrue((self.pm / f"verdict_{D}_probe_x_qwen.md").is_file())
        self.assertIn("4 Datei(en) in 2 Ordner verschoben, 0 Ziel(e) belegt, 1 Datei(en) bleiben flach.", out)
        self.assertEqual(kette.datei_suchen("spec", "a", None), self.pm / "a" / f"spec_{D}_a.md")

    def test_t5_ziel_belegt(self):
        """T5: einsortieren – vorhandene Datei im Ordner wird nicht überschrieben"""
        from einsortieren import einsortieren
        self.dateien(f"spec_{D}_k.md", f"handover_{D}_k.md")
        (self.pm / "k").mkdir()
        (self.pm / "k" / f"handover_{D}_k.md").write_text("im Ordner\n", encoding="utf-8")
        code, out = self.rufen(einsortieren, "k")
        self.assertEqual(code, 1, out)
        self.assertIn(f"ZIEL BELEGT {f'handover_{D}_k.md'} -> k/", out)
        self.assertEqual((self.pm / "k" / f"handover_{D}_k.md").read_text(encoding="utf-8"), "im Ordner\n")
        self.assertTrue((self.pm / f"handover_{D}_k.md").is_file())
        self.assertTrue((self.pm / "k" / f"spec_{D}_k.md").is_file())

    def test_t6_falsche_aufrufe(self):
        """T6: einsortieren – ungültiger Kurztitel, Aufruf ohne Kurztitel und ohne --alle"""
        from einsortieren import einsortieren
        code, out = self.rufen(einsortieren, "K-x")
        self.assertEqual(code, 2, out)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            kette.main(["einsortieren"])
        self.assertEqual(e.exception.code, 2)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            kette.main(["einsortieren", "k", "--alle"])

    def test_t7_kette_ohne_flache_spec(self):
        """T7: einsortieren <kt> – Kette, deren Spec schon im Ordner liegt"""
        from einsortieren import einsortieren
        (self.pm / "k").mkdir()
        (self.pm / "k" / f"spec_{D}_k.md").write_text("# Spec\n", encoding="utf-8")
        self.dateien(f"pruefung_{D}_k.md")
        code, out = self.rufen(einsortieren, "k")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.pm / "k" / f"pruefung_{D}_k.md").is_file(), out)
        self.assertEqual(kette.datei_suchen("pruefung", "k", None), self.pm / "k" / f"pruefung_{D}_k.md")


if __name__ == "__main__":
    unittest.main()
