#!/usr/bin/env python3
"""Vorgabe-Tests fuer K11b lauf_status (spec_20261028_lauf_status.md, T1–T8).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: Jeder Test arbeitet in tempfile.TemporaryDirectory() mit eigenem Temp-Git-Repo und
umgebogenem kette.ROOT/kette.PM. umsetzung_auto und review_auto werden im Modul kette durch Attrappen
ersetzt (kein opencode, kein Modell, kein Netz). automatik wird in jeder Methode importiert (rot vorab).

Angepasst mit K12a2 (spec_20261106_lauf_spec_pruefen.md, von Claude vor dem Lauf): spec() liefert eine Spec ohne
Befund aus spec-pruefen; T3 prüft nur noch die Schwelle, das Verhalten bei Überschreitung prüft test_lauf_spec_pruefen.py.
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
    """Vollstaendige Spec ohne Befund aus spec-pruefen (K12a2: lauf prueft die Spec vor der Umsetzung)."""
    t = ("# Spec: k\n\n- **Datum:** 2026-10-28\n- **Modell:** Test\n- **Betroffene Dateien:** `src/d0.py`\n"
         "- **Änderungsstellen:** 3\n\n## Ziel\n\nx\n\n## Nicht-Ziele\n\n- y\n\n## Schreibbereich\n\n")
    t += "".join(f"- `src/d{i}.py`\n" for i in range(bereich))
    if vorgabe:
        t += "\n## Vorgabe-Tests\n\n- `tests/test_k.py`\n"
    t += ("\n## Außenwirkung und Sperre\n\n- nichts\n\n## Einstiegspunkte\n\n| Datei | Wie | Test |\n|---|---|---|\n"
          "| `src/d0.py` | Modul | T1 |\n\n## Quellen\n\n- `src/d0.py` def f – Muster\n\n## Anforderungen\n\n")
    t += "".join(f"### A{i + 1}: a\n- **Anforderung:** x\n- **Stelle:** `src/d0.py`, f\n- **Akzeptanz:** T1\n\n"
                 for i in range(anforderungen))
    t += "## Fehlerpfade\n\n| Anforderung | Fall |\n|---|---|\n| A1 | n. a. |\n\n## Testplan\n\n"
    t += "".join(f"### T{i + 1}: t\n- **Prüft:** A{i % anforderungen + 1}\n- **Erwartung:** y\n\n"
                 for i in range(tests))
    t += "## Offene Fragen\n\n- Keine\n\n## Abweichende Meinung\n\n- Keine\n"
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
        """T3: lauf – an der alten Schwelle 2/6/8 läuft es (Halt bei Überschreitung entfällt mit K12a2)"""
        import automatik
        self.spec_committen(spec(tests=8, anforderungen=6, bereich=2), nachricht="Spec k")
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
        self.assertIn(f"Spec:          spec_{DATUM}_k.md\n", out)      # Dateiname, kein Pfad (C4; Nacharbeit 1)
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
        (self.pm / f"gesamt_{DATUM}_k.md").write_text("# Gesamtbefund: k\n\n> Hinweis\n\n**UNVOLLSTÄNDIG** – Regel\n",
                                                encoding="utf-8")
        code, out = self.rufen(automatik.status, "k")
        self.assertIn("Review:        UNVOLLSTÄNDIG", out)          # Wert wie in gesamt_* (C3; Nacharbeit 1)
        self.assertIn("gegenprüfen", out.split("Nächster Schritt:")[1])
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
