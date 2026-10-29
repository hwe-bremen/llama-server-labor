#!/usr/bin/env python3
"""Vorgabe-Tests fuer alle_tests (spec_20261029_alle_tests.md, T1–T8).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: T1–T7 arbeiten in tempfile.TemporaryDirectory() mit umgebogenem alle_tests.ROOT
und kleinen Ersatz-Testdateien. T8 ruft das echte Skript nur mit --liste auf (fuehrt nichts aus).
alle_tests wird in jeder Methode importiert (rot vorab).
"""
import io
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "scripts"))

UT_OK = """import unittest
class T(unittest.TestCase):
    def test_a(self):
        self.assertTrue(True)
"""
UT_ROT = """import unittest
class T(unittest.TestCase):
    def test_a(self):
        print("OK")  # irrefuehrende letzte Zeile
        self.fail("absichtlich rot")
"""


def at():
    import alle_tests
    return alle_tests


class Temp(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name).resolve()

    def modul(self):
        m = at()
        alt = m.ROOT
        m.ROOT = self.root
        self.addCleanup(setattr, m, "ROOT", alt)
        return m

    def datei(self, rel, text="pass\n"):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        return p

    def rufen(self, m, *argv):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            try:
                code = m.main(list(argv))
            except SystemExit as e:
                code = e.code
        return code, aus.getvalue()


class Finden(Temp):

    def test_t1_finden_fundorte_und_ausschluesse(self):
        """T1: finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert"""
        m = self.modul()
        for rel in ("tests/test_b.py", "tests/test_a.py", "role-split/test_r.py",
                    "role-split/kette/test_k.py", "mcp-server/test_m.py", "scripts/test_s.py",
                    "tests/hilfe.py", "tests/x_test.py", "tmp/test_tmp.py", "agents/test_ag.py",
                    "mcp-server/.venv/lib/test_venv.py", "role-split/venv/test_v.py",
                    "tests/__pycache__/test_c.py", "role-split/kette/testdata/test_fake.py"):
            self.datei(rel)
        self.assertEqual(m.finden(), ["mcp-server/test_m.py", "role-split/kette/test_k.py",
                                      "role-split/test_r.py", "scripts/test_s.py",
                                      "tests/test_a.py", "tests/test_b.py"])
        self.assertEqual(m.FUNDORTE, ("tests", "role-split", "mcp-server", "scripts"))


class Aufruf(Temp):

    def test_t2_art_aufruf_und_suchpfad(self):
        """T2: art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad"""
        m = self.modul()
        self.datei("tests/test_u.py", UT_OK)
        self.datei("tests/test_u2.py", "from unittest import TestCase\nclass T(TestCase):\n    pass\n")
        self.datei("mcp-server/test_tool_log.py", "import sys\nprint(sys.argv)\n")
        self.datei("scripts/test_s.py", "print('x')\n")
        self.assertEqual(m.art("tests/test_u.py"), "unittest")
        self.assertEqual(m.art("tests/test_u2.py"), "unittest")
        self.assertEqual(m.art("scripts/test_s.py"), "skript")
        argv, env = m.aufruf("tests/test_u.py")
        self.assertEqual(argv[1:], ["-m", "unittest", "tests/test_u.py"])
        argv, env = m.aufruf("mcp-server/test_tool_log.py")
        self.assertEqual(argv[1:], ["mcp-server/test_tool_log.py", "mcp-server/lab_mcp_server.py"])
        self.assertEqual(env["PYTHONPATH"].split(os.pathsep)[0], str(self.root / "mcp-server"))
        argv, _ = m.aufruf("scripts/test_s.py")
        self.assertEqual(argv[1:], ["scripts/test_s.py"])
        alt = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = "/vorher"
        self.addCleanup(lambda: os.environ.__setitem__("PYTHONPATH", alt) if alt is not None
                        else os.environ.pop("PYTHONPATH", None))
        _, env = m.aufruf("tests/test_u.py")
        self.assertEqual(env["PYTHONPATH"], str(self.root / "tests") + os.pathsep + "/vorher")

    def test_t3_interpreter_naechstes_venv(self):
        """T3: interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable"""
        m = self.modul()
        self.datei("tests/test_a.py")
        self.datei("mcp-server/test_m.py")
        self.datei("role-split/kette/test_k.py")
        self.assertEqual(m.interpreter("tests/test_a.py"), sys.executable)
        for ort in ("mcp-server", "."):
            py = self.root / ort / ".venv" / "bin" / "python"
            py.parent.mkdir(parents=True)
            py.symlink_to(sys.executable)
        self.assertEqual(m.interpreter("mcp-server/test_m.py"), str(self.root / "mcp-server/.venv/bin/python"))
        self.assertEqual(m.interpreter("role-split/kette/test_k.py"), str(self.root / ".venv/bin/python"))
        self.assertEqual(m.interpreter("tests/test_a.py"), str(self.root / ".venv/bin/python"))


class Laufen(Temp):

    def test_t4_gruen_mit_nachbarmodul_und_bindestrich(self):
        """T4: Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0"""
        m = self.modul()
        self.datei("role-split/nachbar.py", "WERT = 42\n")
        self.datei("role-split/test_n.py", "import unittest\nimport nachbar\n"
                   "class T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(nachbar.WERT, 42)\n")
        self.datei("mcp-server/lab_mcp_server.py", "")
        self.datei("mcp-server/test_tool_log.py", "import sys, pathlib\n"
                   "assert pathlib.Path(sys.argv[1]).is_file(), sys.argv\nprint('Skript gut')\n")
        self.datei("tests/test_u.py", UT_OK)
        code, out = self.rufen(m)
        self.assertEqual(code, 0, out)
        self.assertIn("Testdateien: 3 (Zeitlimit 300 s je Datei)", out)
        for rel in ("role-split/test_n.py", "mcp-server/test_tool_log.py", "tests/test_u.py"):
            self.assertRegex(out, rf"\n  ok    {rel}  \(\d+\.\d s\)")
        self.assertIn("3 Datei(en): 3 ok, 0 rot, 0 Zeit.", out)
        self.assertNotIn("---", out)

    def test_t5_rot_nach_exit_code_mit_ausgabe(self):
        """T5: Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende"""
        m = self.modul()
        self.datei("tests/test_rot.py", UT_ROT)
        self.datei("scripts/test_s.py", "import sys\nprint('Meldung vom Skript')\nsys.exit(3)\n")
        self.datei("tests/test_u.py", UT_OK)
        code, out = self.rufen(m)
        self.assertEqual(code, 1, out)
        self.assertIn("  ROT   scripts/test_s.py  Exit 3  (", out)
        self.assertIn("  ROT   tests/test_rot.py  Exit 1  (", out)
        self.assertIn("  ok    tests/test_u.py  (", out)
        self.assertIn("--- scripts/test_s.py – letzte 1 Zeilen ---\nMeldung vom Skript", out)
        self.assertIn("--- tests/test_rot.py – letzte", out)
        self.assertIn("absichtlich rot", out)
        self.assertIn("3 Datei(en): 1 ok, 2 rot, 0 Zeit.", out)
        lang = "import sys\n" + "".join(f"print('z{i}')\n" for i in range(50)) + "sys.exit(1)\n"
        self.datei("scripts/test_s.py", lang)
        code, out = self.rufen(m)
        self.assertIn("--- scripts/test_s.py – letzte 20 Zeilen ---\nz30\n", out)
        self.assertIn("z49", out)
        self.assertNotIn("z29\n", out)

    def test_t6_zeitlimit(self):
        """T6: Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter"""
        m = self.modul()
        self.datei("tests/test_haengt.py", "import time\ntime.sleep(30)\n")
        self.datei("tests/test_u.py", UT_OK)
        t0 = time.monotonic()
        code, out = self.rufen(m, "--timeout", "1")
        self.assertLess(time.monotonic() - t0, 15, "Zeitlimit wirkt nicht")
        self.assertEqual(code, 1, out)
        self.assertIn("  ZEIT  tests/test_haengt.py  nach 1 s abgebrochen", out)
        self.assertIn("  ok    tests/test_u.py  (", out)
        self.assertIn("2 Datei(en): 1 ok, 0 rot, 1 Zeit.", out)
        code, out = self.rufen(m, "--timeout", "0")
        self.assertEqual(code, 2, out)

    def test_t7_liste_und_leer(self):
        """T7: --liste führt nichts aus; keine Testdateien → Exit 2"""
        m = self.modul()
        code, out = self.rufen(m)
        self.assertEqual(code, 2, out)
        self.assertIn("Keine Testdateien gefunden.", out)
        self.assertEqual(self.rufen(m, "--liste")[0], 2)
        marke = self.root / "MARKE"
        self.datei("tests/test_marke.py", f"import unittest, pathlib\npathlib.Path({str(marke)!r}).touch()\n")
        self.datei("mcp-server/test_tool_log.py", f"import pathlib\npathlib.Path({str(marke)!r}).touch()\n")
        code, out = self.rufen(m, "--liste")
        self.assertEqual(code, 0, out)
        self.assertFalse(marke.exists(), "--liste hat eine Testdatei ausgeführt")
        self.assertIn("Testdateien: 2", out)
        self.assertIn("  unittest tests/test_marke.py  [python]", out)
        self.assertIn("  skript   mcp-server/test_tool_log.py  [python] mcp-server/lab_mcp_server.py", out)


class Einstieg(unittest.TestCase):

    def test_t8_echtes_repo_standardwerte(self):
        """T8: Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile"""
        m = at()
        self.assertEqual(m.ROOT, ECHT)
        self.assertEqual(m.TIMEOUT, 300)
        r = subprocess.run([sys.executable, str(ECHT / "scripts" / "alle_tests.py"), "--liste"],
                           capture_output=True, text=True, timeout=60, cwd=str(ECHT / "docs"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(" tests/test_alle_tests.py  [", r.stdout)
        self.assertRegex(r.stdout, r"  unittest role-split/test_role_proxy\.py  \[")
        self.assertRegex(r.stdout, r"  skript   mcp-server/test_tool_log\.py  \[[^\]]+\] mcp-server/lab_mcp_server\.py")
        self.assertNotIn(".venv/lib", r.stdout)
        self.assertNotIn("__pycache__", r.stdout)


if __name__ == "__main__":
    unittest.main()
