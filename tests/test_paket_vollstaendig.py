#!/usr/bin/env python3
"""Tests fuer Spec paket_vollstaendig (K9), Testplan T1–T9 plus Zusatztests K1–K2.

Jeder Test baut ein Wegwerf-Git-Repo und prueft Verhalten (Paketinhalt, Exit-Code, Gegenprobe),
nicht den Quelltext. Laeuft ab Python 3.10. Geschrieben von Claude (Uebernahme NB2, 26.10.).
"""
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJ / "role-split" / "kette"))
import kette  # noqa: E402


def lauf(fn, *a, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = fn(*a, **kw)
    return code, buf.getvalue()


class Basis(unittest.TestCase):
    """Repo mit Spec-Datei und Commit 'Spec g' als Ruecksetzpunkt."""

    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name)
        self.git("init", "-q")
        self.pm = self.root / "docs" / "projekt_management"
        self.pm.mkdir(parents=True)
        (self.pm / "spec_20261026_g.md").write_text(
            "# Spec\n\n## Ziel\nZ\n\n## Nicht-Ziele\nN\n\n## Anforderungen\n### A1: Eins\nX\n\n"
            "## Testplan\n### T1: Erster\n- **Erwartung:** E\n\n## Offene Fragen\nO\n", encoding="utf-8")
        self.schreibe("mod.py", "def f():\n    return 1\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "Spec g")
        self.spec_commit = self.git("rev-parse", "--short", "HEAD").strip()
        for name, wert in (("ROOT", self.root), ("PM", self.pm)):
            alt = getattr(kette, name)
            setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, text=True).stdout

    def schreibe(self, rel, inhalt):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(inhalt, encoding="utf-8")

    def commit(self, nachricht, **dateien):
        for rel, inhalt in dateien.items():
            self.schreibe(rel.replace("__", "/"), inhalt)
        self.git("add", "-A")
        self.git("commit", "-qm", nachricht)

    def handover(self, *dateien):
        zeilen = "".join(f"- `{d}` – x\n" for d in dateien)
        (self.pm / "handover_20261026_g.md").write_text(
            f"# HO\n## Geänderte und neue Dateien\n{zeilen}\n## Abweichungen\nkeine\n", encoding="utf-8")

    def paket(self, **kw):
        code, out = lauf(kette.paket, "g", **kw)
        ziel = self.pm / "review_paket_20261026_g.md"
        text = ziel.read_text(encoding="utf-8") if ziel.exists() else None
        return code, out, text

    @staticmethod
    def code_teil(text):
        rest = text.split("## 3. Code-Aenderungen")[1]
        for ende in ("## 3a.", "## 3b.", "## 4."):
            if ende in rest:
                rest = rest.split(ende)[0]
        return rest

    @staticmethod
    def markiert(code_teil):
        return {b.split(" ")[0] for b in code_teil.split("### ")[1:] if "nicht in der Uebergabe genannt" in b}


class TestPaketVollstaendig(Basis):

    def test_t1_fehlerpfade_von_paket(self):
        """T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)"""
        code, out = lauf(kette.paket, "G-1")
        self.assertEqual(code, 2); self.assertIn("ungueltig", out)
        code, out = lauf(kette.paket, "nichtda")
        self.assertEqual(code, 2); self.assertIn("Keine Spec", out)
        (self.pm / "spec_20261026_ohne.md").write_text("# Spec\n", encoding="utf-8")
        code, out = lauf(kette.paket, "ohne")
        self.assertEqual(code, 2); self.assertIn("Kein Commit 'Spec ohne'", out)
        code, out = lauf(kette.paket, "g", commit="deadbeefdeadbeef")
        self.assertEqual(code, 2); self.assertIn("git-Fehler", out)
        self.assertEqual(list(self.pm.glob("review_paket_*")), [])

    def test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte(self):
        """T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte"""
        self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
        self.schreibe("tests/test_g.py", "import unittest\n")                       # unversioniert
        self.schreibe("tests/daten/x.json", '{"a": 1}\n')                            # unversioniert
        self.schreibe("role-split/kette/hilfs.py", "H = 1\n")
        self.git("add", "role-split/kette/hilfs.py")                                 # nur vorgemerkt
        self.schreibe("role-split/rollen/r.md", "# Rolle R\n")                       # .md unter role-split
        self.handover("mod.py")
        code, out, text = self.paket()
        self.assertEqual(code, 0, out)
        teil = self.code_teil(text)
        for d in ("mod.py", "tests/test_g.py", "tests/daten/x.json", "role-split/kette/hilfs.py",
                  "role-split/rollen/r.md"):
            self.assertIn(f"### {d} ", teil, d)
        self.assertEqual(self.markiert(teil), {"tests/test_g.py", "tests/daten/x.json",
                                               "role-split/kette/hilfs.py", "role-split/rollen/r.md"})

    def test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung(self):
        """T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung"""
        self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
        self.schreibe("tests/test_g.py", "import unittest\n")
        self.schreibe("role-split/kette/hilfs.py", "H = 1\n")
        self.handover("mod.py", "tests/test_g.py")
        code, out, text = self.paket()
        self.assertEqual(code, 0, out)
        self.assertEqual(self.markiert(self.code_teil(text)), {"role-split/kette/hilfs.py"})

    def test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen(self):
        """T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen"""
        self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
        self.schreibe("tests/test_g.py", "import unittest\n")
        zeile = "Testzeile mit Inhalt fuer eine grosse Datei\n"
        self.schreibe("tests/daten/gross.eml", zeile * 2500)          # ~110 000 Zeichen, Vorrang 3
        alt = kette.PAKET_DATEI_ZEILEN
        kette.PAKET_DATEI_ZEILEN = 5000
        self.addCleanup(setattr, kette, "PAKET_DATEI_ZEILEN", alt)
        self.handover("mod.py")
        code, out, text = self.paket()
        self.assertEqual(code, 0, out)
        teil = self.code_teil(text)
        self.assertIn("### mod.py ", teil)
        self.assertIn("### tests/test_g.py ", teil)                    # Vorrang 2 bleibt, reicht schon
        self.assertNotIn("gross.eml", teil)
        weg = text.split("## 3b.")[1].split("## 4.")[0]
        self.assertIn("`tests/daten/gross.eml` – Testdaten", weg)
        self.assertLessEqual(len(text), kette.PAKET_WARNUNG_ZEICHEN)

    def test_t5_kette_paket_max_ueberschritten_exit_1(self):
        """T5: KETTE_PAKET_MAX überschritten → Exit 1"""
        self.commit("g: mod", **{"mod.py": "".join(f"def f{i}():\n    return {i}\n" for i in range(300))})
        self.handover("mod.py")
        alt = kette.KETTE_PAKET_MAX
        kette.KETTE_PAKET_MAX = 3000
        self.addCleanup(setattr, kette, "KETTE_PAKET_MAX", alt)
        code, out, text = self.paket()
        self.assertEqual(code, 1, out)
        self.assertIn("passt nicht in den Kontext", out)
        self.assertIsNone(text)

    def test_t6_gegenprobe_beruecksichtigt_role_split_kette(self):
        """T6: Gegenprobe berücksichtigt role-split/kette/"""
        self.commit("Werkzeug: fremd", **{"fremd.py": "F = 5\n"})
        self.commit("g: hilfs", **{"role-split__kette__hilfs.py": "H = 7\n"})
        self.schreibe("tests/test_g.py",
                      "import sys, unittest\nfrom pathlib import Path\n"
                      "R = Path(__file__).resolve().parent.parent\n"
                      "sys.path.insert(0, str(R / 'role-split' / 'kette')); sys.path.insert(0, str(R))\n"
                      "class T(unittest.TestCase):\n"
                      "    def test_t1_hilfs(self):\n        import hilfs\n        self.assertEqual(hilfs.H, 7)\n"
                      "    def test_t2_fremd(self):\n        import fremd\n        self.assertEqual(fremd.F, 5)\n")
        code, out = lauf(kette.gegenprobe, "g", self.spec_commit)
        self.assertIn("rot   test_t1_hilfs  <- hilfs.py", out)
        self.assertIn("GRUEN test_t2_fremd", out)                     # fremde Datei nicht zurueckgesetzt
        self.assertNotIn("fremd.py:", out)
        self.assertEqual((self.root / "role-split/kette/hilfs.py").read_text(), "H = 7\n")

    def test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen(self):
        """T7: Bestehende Tests in test_kette.py bleiben grün"""
        r = subprocess.run([sys.executable, str(PROJ / "role-split" / "kette" / "test_kette.py")],
                           capture_output=True, text=True, timeout=300)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])

    def test_t8_fremde_commits_nur_als_liste(self):
        """T8: Fremde Commits nur als Liste"""
        self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
        self.commit("Werkzeug: x", **{"werkzeug.py": "GEHEIMER_INHALT = 1\n", "anderes.py": "A = 1\n"})
        self.handover("mod.py", "anderes.py")
        code, out, text = self.paket()
        self.assertEqual(code, 0, out)
        teil = self.code_teil(text)
        self.assertIn("### mod.py ", teil)
        self.assertIn("### anderes.py ", teil)                          # fremd, aber in der Uebergabe
        self.assertNotIn("GEHEIMER_INHALT", text)
        fremd = text.split("## 3a.")[1].split("## 4.")[0]
        self.assertIn("`werkzeug.py`", fremd)
        self.assertIn("Werkzeug: x", fremd)
        self.assertNotIn("anderes.py", fremd)

    def test_t9_paket_ohne_code_trotz_aenderungen_exit_1(self):
        """T9: Paket ohne Code trotz Änderungen → Exit 1"""
        self.commit("Werkzeug: x", **{"mod.py": "def f():\n    return 9\n"})
        code, out, text = self.paket()
        self.assertEqual(code, 1, out)
        self.assertIn("Paket ohne Code trotz Aenderungen", out)
        self.assertIsNone(text)

    def test_k1_nur_docs_geaendert_exit_0(self):
        """K1: Nur docs/ geaendert -> Exit 0, 'keine Code-Dateien'"""
        self.commit("g: doku", **{"docs__notiz.md": "x\n"})
        code, out, text = self.paket()
        self.assertEqual(code, 0, out)
        self.assertIn("Geaenderte Code-Dateien: keine", text)

    def test_k2_kurztitel_als_ganzes_wort(self):
        """K2: Kurztitel 'g' trifft nicht 'gross' -> Datei aus 'gross init' ist fremd"""
        self.commit("gross init", **{"gross.py": "G = 1\n"})
        self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
        code, out, text = self.paket()
        self.assertEqual(code, 0, out)
        self.assertIn("`gross.py`", text.split("## 3a.")[1].split("## 4.")[0])
        self.assertNotIn("### gross.py", self.code_teil(text))


if __name__ == "__main__":
    unittest.main()
