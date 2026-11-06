#!/usr/bin/env python3
"""Vorgabe-Tests fuer K12a2 lauf_spec_pruefen (spec_20261106_lauf_spec_pruefen.md, T1–T6).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: T1–T5 arbeiten in tempfile.TemporaryDirectory() mit eigenem Temp-Git-Repo und umgebogenem
kette.ROOT/kette.PM. T6 liest den echten Bestand nur (git status vorher = nachher). umsetzung_auto und review_auto
werden im Modul kette durch Attrappen ersetzt (kein opencode, kein Modell, kein Netz). automatik und spec_pruefen
werden in jeder Methode importiert.
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
KETTE_DIR = ECHT / "role-split" / "kette"
sys.path.insert(0, str(KETTE_DIR))
import kette  # noqa: E402

DATUM = "20261106"


def spec(tests: int = 2, anforderungen: int = 2, bereich: int = 1, vorgabe: bool = True,
         stellen: str | None = "3", offene: str = "- Keine") -> str:
    """Vollstaendige Spec, die spec-pruefen ohne Befund besteht (bei den Standardwerten)."""
    t = "# Spec: k\n\n- **Datum:** 2026-11-06\n- **Modell:** Test\n- **Betroffene Dateien:** `src/d0.py`\n"
    if stellen is not None:
        t += f"- **Änderungsstellen:** {stellen}\n"
    t += "\n## Ziel\n\nx\n\n## Nicht-Ziele\n\n- y\n\n## Schreibbereich\n\n"
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
    t += f"## Offene Fragen\n\n{offene}\n\n## Abweichende Meinung\n\n- Keine\n"
    return t


def attrappen(test: unittest.TestCase) -> list:
    """umsetzung_auto/review_auto in kette ersetzen; Rueckgabe: Liste der Aufrufe."""
    aufrufe: list = []
    test.code_umsetzung = 0
    test.code_review = 0

    def umsetzung(kurztitel, nacharbeit=None):
        aufrufe.append(("umsetzung", kurztitel))
        return test.code_umsetzung

    def review(kurztitel):
        aufrufe.append(("review", kurztitel))
        return test.code_review
    for name, f in (("umsetzung_auto", umsetzung), ("review_auto", review)):
        p = mock.patch.object(kette, name, f)
        p.start()
        test.addCleanup(p.stop)
    return aufrufe


def rufen(fn, *a):
    aus = io.StringIO()
    with redirect_stdout(aus), redirect_stderr(aus):
        code = fn(*a)
    return code, aus.getvalue()


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
        self.aufrufe = attrappen(self)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, text=True).stdout

    def spec_committen(self, text: str, nachricht: str = "Spec k"):
        (self.pm / f"spec_{DATUM}_k.md").write_text(text, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", nachricht)


class Halt(Temp):

    def test_t1_befunde_halten_vor_der_umsetzung(self):
        """T1: lauf – Befunde aus spec-pruefen halten mit Exit 3 vor der Umsetzung"""
        import automatik
        self.spec_committen(spec(offene="- Soll X oder Y?"))
        code, out = rufen(automatik.lauf, "k")
        self.assertEqual(code, 3, out)
        self.assertEqual(self.aufrufe, [])
        self.assertIn(f"Spec-Prüfung k: spec_{DATUM}_k.md", out)
        self.assertIn("  BEFUND   Offene Fragen nicht geklärt", out)
        self.assertIn("HALT – Spec-Prüfung mit Befunden", out)
        self.assertNotIn("Umsetzer:", out)
        self.assertNotIn("HALT – Entscheidung Hawe.", out)
        self.spec_committen(spec(stellen=None), nachricht="alte Spec ohne Zeile")
        code, out = rufen(automatik.lauf, "k")
        self.assertEqual(code, 3, out)
        self.assertIn("  BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt", out)
        self.assertEqual(self.aufrufe, [])

    def test_t2_groesse_nur_hinweis(self):
        """T2: lauf – Größe über den alten Schwellen und über R59 hält nicht mehr an"""
        import automatik
        self.spec_committen(spec(tests=9, anforderungen=7, bereich=3, stellen="12"))
        code, out = rufen(automatik.lauf, "k")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.aufrufe, [("umsetzung", "k"), ("review", "k")])
        for h in ("Dateien 3 > 1", "Anforderungen 7 > 4", "Tests 9 > 8", "Änderungsstellen 12 > 9"):
            self.assertIn(f"  HINWEIS  Größe über R59 (vorläufig): {h}", out)
        self.assertIn("Keine Befunde (4 Hinweis(e)).", out)
        self.assertNotIn("teilen", out)
        self.assertIn("HALT – Entscheidung Hawe.", out)


class Ablauf(Temp):

    def test_t3_ausgabe_wie_einzelbefehl(self):
        """T3: lauf – gültige Spec: Ausgabe wie spec-pruefen, danach Umsetzung und Review"""
        import automatik
        import spec_pruefen
        self.spec_committen(spec())
        _, einzeln = rufen(spec_pruefen.spec_pruefen, "k")
        code, out = rufen(automatik.lauf, "k")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.aufrufe, [("umsetzung", "k"), ("review", "k")])
        self.assertTrue(out.startswith(einzeln), out)
        self.assertIn("  Größe: 1 Datei(en), 2 Anforderungen, 2 Tests, 3 Änderungsstellen (R59 1/4/8/9, vorläufig)\n"
                      "Keine Befunde (0 Hinweis(e)).\nUmsetzer: 35B\n", out)
        self.assertNotIn("Schwellen 2/6/8", out)
        self.code_umsetzung = 1
        code, out = rufen(automatik.lauf, "k")
        self.assertEqual(code, 1, out)
        self.assertEqual(self.aufrufe[-1], ("umsetzung", "k"))

    def test_t4_vorbedingungen_und_exit_2(self):
        """T4: lauf – Vorbedingungen vor der Spec-Prüfung, Exit 2 der Spec-Prüfung durchgereicht"""
        import automatik
        import spec_pruefen
        self.spec_committen(spec(vorgabe=False))
        code, out = rufen(automatik.lauf, "k")
        self.assertEqual(code, 2, out)
        self.assertIn("Vorgabe-Tests", out)
        self.assertNotIn("Spec-Prüfung", out)
        self.spec_committen(spec(), nachricht="mit Vorgabe")
        gesehen = []
        with mock.patch.object(spec_pruefen, "spec_pruefen", lambda kt: gesehen.append(kt) or 2):
            code, out = rufen(automatik.lauf, "k")
        self.assertEqual(gesehen, ["k"])
        self.assertEqual(code, 2, out)
        self.assertEqual(self.aufrufe, [])
        self.assertNotIn("HALT – Entscheidung Hawe.", out)
        with mock.patch.object(spec_pruefen, "spec_pruefen", lambda kt: 1):
            code, out = rufen(automatik.lauf, "k")
        self.assertEqual(code, 3, out)
        self.assertEqual(self.aufrufe, [])


class Einstieg(Temp):

    def test_t5_standardwerte_und_echter_aufruf(self):
        """T5: Standardwerte – alte Schwellen weg, groesse bleibt, lauf und spec-pruefen über kette.main in frischem Prozess"""
        import automatik
        import spec_pruefen
        for name in ("GROESSE_DATEIEN", "GROESSE_ANFORDERUNGEN", "GROESSE_TESTS"):
            self.assertFalse(hasattr(automatik, name), name)
        self.assertEqual(automatik.groesse(spec(tests=3)), {"dateien": 1, "anforderungen": 2, "tests": 3})
        self.assertEqual(automatik.UMSETZER_VORSCHLAG, "35B")
        self.assertEqual(spec_pruefen.R59, {"dateien": 1, "anforderungen": 4, "tests": 8, "stellen": 9})
        self.spec_committen(spec(offene="- Frage offen"))
        skript = (
            "import sys\n"
            f"sys.path.insert(0, {str(KETTE_DIR)!r})\n"
            "from pathlib import Path\n"
            "import kette\n"
            "kette.ROOT = Path(sys.argv[1]); kette.PM = kette.ROOT / 'docs' / 'projekt_management'\n"
            "kette.umsetzung_auto = lambda *a, **k: sys.exit(99)\n"
            "kette.review_auto = lambda *a, **k: sys.exit(98)\n"
            "sys.exit(kette.main(['lauf', 'k']))\n"
        )
        r = subprocess.run([sys.executable, "-c", skript, str(self.root)], capture_output=True, text=True,
                           cwd=str(self.root), timeout=60)
        self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
        self.assertIn("HALT – Spec-Prüfung mit Befunden", r.stdout)
        self.assertNotIn("Traceback", r.stderr)
        r = subprocess.run([sys.executable, "-c", skript.replace("['lauf', 'k']", "['spec-pruefen', 'k']"),
                            str(self.root)], capture_output=True, text=True, cwd=str(self.root), timeout=60)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)


class Bestand(unittest.TestCase):

    def test_t6_trockenlauf_echter_bestand(self):
        """T6: Trockenlauf am echten Bestand – alte Spec hält, saubere Spec läuft, nichts geschrieben"""
        import automatik
        aufrufe = attrappen(self)
        vorher = subprocess.run(["git", "-C", str(kette.ROOT), "status", "--porcelain"],
                                capture_output=True, text=True).stdout
        code, out = rufen(automatik.lauf, "git_schutz")
        self.assertEqual(code, 3, out)
        befunde = [z for z in out.splitlines() if z.startswith("  BEFUND")]
        self.assertEqual(befunde, ["  BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt"], out)
        self.assertEqual(aufrufe, [])
        code, out = rufen(automatik.lauf, "spec_pruefen")
        self.assertEqual(code, 0, out)
        self.assertIn("Keine Befunde", out)
        self.assertEqual(aufrufe, [("umsetzung", "spec_pruefen"), ("review", "spec_pruefen")])
        nachher = subprocess.run(["git", "-C", str(kette.ROOT), "status", "--porcelain"],
                                 capture_output=True, text=True).stdout
        self.assertEqual(vorher, nachher)


if __name__ == "__main__":
    unittest.main()
