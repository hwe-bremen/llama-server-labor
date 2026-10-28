#!/usr/bin/env python3
"""Vorgabe-Tests fuer K11b lauf_status (spec_20261028_lauf_status.md, T1–T8).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: Jeder Test arbeitet in tempfile.TemporaryDirectory() mit eigenem Temp-Git-Repo und
umgebogenem kette.ROOT/kette.PM. umsetzung_auto und review_auto werden im Modul kette durch Attrappen
ersetzt (kein opencode, kein Modell, kein Netz). automatik wird in jeder Methode importiert (rot vorab).
"""
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402

DATUM = "20261028"


def spec(tests: int = 2, anforderungen: int = 2, bereich: int = 1, vorgabe: bool = True) -> str:
    t = "# Spec: k\n\n## Ziel\nx\n\n## Schreibbereich\n\n" + "".join(f"- `src/d{i}.py`\n" for i in range(bereich))
    if vorgabe:
        t += "\n## Vorgabe-Tests\n\n- `tests/test_k.py`\n"
    t += "\n## Anforderungen\n\n" + "".join(f"### A{i + 1}: a\n- x\n\n" for i in range(anforderungen))
    t += "## Testplan\n\n" + "".join(f"### T{i + 1}: t\n- **Erwartung:** y\n\n" for i in range(tests))
    return t


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
        self.git("init", "-q")
        self.aufrufe = []
        self.code_umsetzung = 0
        self.code_review = 0

        def umsetzung(kurztitel, nacharbeit=None):
            self.aufrufe.append(("umsetzung", kurztitel, nacharbeit))
            return self.code_umsetzung

        def review(kurztitel):
            self.aufrufe.append(("review", kurztitel))
            return self.code_review
        for name, f in (("umsetzung_auto", umsetzung), ("review_auto", review)):
            p = mock.patch.object(kette, name, f)
            p.start()
            self.addCleanup(p.stop)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, text=True).stdout

    def spec_committen(self, text: str, nachricht: str = "Spec k"):
        (self.pm / f"spec_{DATUM}_k.md").write_text(text, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", nachricht)

    def rufen(self, fn, *a):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = fn(*a)
        return code, aus.getvalue()


class LaufVorab(Temp):

    def test_t1_lauf_ohne_spec_commit(self):
        """T1: lauf – ohne Commit „Spec <kt>“ kein Start"""
        import automatik
        self.spec_committen(spec(), nachricht="irgendwas")
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 2, out)
        self.assertIn("Spec k", out)
        self.assertEqual(self.aufrufe, [])
        code, out = self.rufen(automatik.lauf, "K-ungueltig")
        self.assertEqual(code, 2, out)

    def test_t2_lauf_ohne_vorgabe_tests(self):
        """T2: lauf – ohne Abschnitt Vorgabe-Tests kein Start"""
        import automatik
        self.spec_committen(spec(vorgabe=False))
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 2, out)
        self.assertIn("Vorgabe-Tests", out)
        self.assertEqual(self.aufrufe, [])

    def test_t3_lauf_zu_gross(self):
        """T3: lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es"""
        import automatik
        self.spec_committen(spec(tests=9))
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 3, out)
        self.assertIn("9 Tests", out)
        self.assertIn("teilen", out)
        self.assertEqual(self.aufrufe, [])
        for zu_viel in (dict(anforderungen=7), dict(bereich=3)):
            self.spec_committen(spec(**zu_viel), nachricht="Aenderung")
            code, out = self.rufen(automatik.lauf, "k")
            self.assertEqual(code, 3, (zu_viel, out))
        self.spec_committen(spec(tests=8, anforderungen=6, bereich=2), nachricht="Schwelle")
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 0, out)
        self.assertIn("2 Datei(en), 6 Anforderungen, 8 Tests", out)


class LaufAblauf(Temp):

    def test_t4_lauf_ok_bis_halt(self):
        """T4: lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung"""
        import automatik
        self.spec_committen(spec())
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.aufrufe, [("umsetzung", "k", None), ("review", "k")])
        self.assertIn("Umsetzer: 35B", out)
        self.assertIn("HALT – Entscheidung Hawe.", out)
        self.assertIn("Nächster Schritt:", out)

    def test_t5_lauf_umsetzung_rot(self):
        """T5: lauf – Umsetzung nicht in Ordnung, kein Review"""
        import automatik
        self.spec_committen(spec())
        self.code_umsetzung = 1
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.aufrufe, [("umsetzung", "k", None)])
        self.assertIn("HALT – Entscheidung Hawe.", out)
        self.code_umsetzung = 2
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 2, out)

    def test_t6_lauf_review_nicht_pass(self):
        """T6: lauf – Review nicht PASS ergibt Exit 1"""
        import automatik
        self.spec_committen(spec())
        self.code_review = 1
        code, out = self.rufen(automatik.lauf, "k")
        self.assertEqual(code, 1, out)
        self.assertEqual([a[0] for a in self.aufrufe], ["umsetzung", "review"])


class Status(Temp):

    def protokoll(self, *zeilen):
        (self.pm / f"umsetzung_{DATUM}_k.md").write_text(
            "# Protokoll\n\n" + "".join(f"- **2026-10-28 10:00** – Modell: m, reason: stop, rot: 0, pruefen: 0, "
                                        f"art: {a}, Exit: {e}\n  - Tokens: art: nb9, Exit: 0\n" for a, e in zeilen),
            encoding="utf-8")

    def test_t7_status_naechster_schritt(self):
        """T7: status – Stand und nächster Schritt aus den Dateien"""
        import automatik
        code, out = self.rufen(automatik.status, "k")
        self.assertEqual(code, 2, out)
        self.assertIn("Spec:          fehlt", out)
        self.spec_committen(spec())
        code, out = self.rufen(automatik.status, "k")
        self.assertEqual(code, 0, out)
        self.assertIn("Vorgabe-Tests: ja", out)
        self.assertIn("Nächster Schritt: kette.py lauf k", out)
        self.protokoll(("erst", 1))
        code, out = self.rufen(automatik.status, "k")
        self.assertIn("Umsetzung:     erst Exit 1", out)
        self.assertNotIn("nb9", out)
        self.assertIn("Nacharbeit", out.split("Nächster Schritt:")[1])
        self.protokoll(("erst", 1), ("nb1", 0))
        code, out = self.rufen(automatik.status, "k")
        self.assertIn("Nächster Schritt: kette.py review-auto k", out)
        (self.pm / f"gesamt_{DATUM}_k.md").write_text("# Gesamtbefund: k\n\n**NACHBESSERN** – Regel\n", encoding="utf-8")
        code, out = self.rufen(automatik.status, "k")
        self.assertIn("Review:        NACHBESSERN", out)
        self.assertIn("gegenprüfen", out)
        (self.pm / f"gesamt_{DATUM}_k.md").write_text("# Gesamtbefund: k\n\n**PASS** – Regel\n", encoding="utf-8")
        code, out = self.rufen(automatik.status, "k")
        self.assertIn("committen", out.split("Nächster Schritt:")[1])
        self.git("add", ".")
        self.git("commit", "-qm", "fertig")
        code, out = self.rufen(automatik.status, "k")
        self.assertIn("Abgeschlossen", out)
        self.assertEqual(self.aufrufe, [])


class Einstieg(Temp):

    def test_t8_main_lauf_und_status(self):
        """T8: main – lauf und status über kette.py"""
        import automatik
        gesehen = []
        with mock.patch.object(automatik, "lauf", lambda kt: gesehen.append(("lauf", kt)) or 3), \
             mock.patch.object(automatik, "status", lambda kt: gesehen.append(("status", kt)) or 0):
            self.assertEqual(kette.main(["lauf", "k"]), 3)
            self.assertEqual(kette.main(["status", "k"]), 0)
        self.assertEqual(gesehen, [("lauf", "k"), ("status", "k")])


if __name__ == "__main__":
    unittest.main()
