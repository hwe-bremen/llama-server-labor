#!/usr/bin/env python3
"""Vorgabe-Tests fuer pruefen_venv (spec_20261107_pruefen_venv.md, T1–T6).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: Jeder Test (ausser dem Standardwert-Teil von T1) arbeitet in tempfile.TemporaryDirectory()
mit eigenem Git-Repo und umgebogenem kette.ROOT/kette.PM. Das „venv“ im Temp-Repo ist ein Shell-Skript, das seine
Aufrufe in eine Datei ausserhalb des Repos schreibt und das laufende Python mit zusaetzlichem PYTHONPATH startet –
so gibt es ein Modul (nur_im_venv), das nur mit dem venv-Python importierbar ist (wie requests im Pilot).
Kein Netz, kein Modell, kein opencode.
"""
import io
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402

SPEC_K = "# Spec: k\n\n## Testplan\n\n### T1: t\n- **Prüft:** A1\n"
TEST_K = """import unittest
import nur_im_venv
import code_k


class T(unittest.TestCase):
    def test_t1_wert(self):
        self.assertEqual(code_k.f(), nur_im_venv.WERT)
"""


class Temp(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        aussen = tempfile.TemporaryDirectory()
        self.addCleanup(aussen.cleanup)
        self.aussen = Path(aussen.name).resolve()
        self.root = Path(d.name).resolve() / "repo"
        self.pm = self.root / "docs" / "projekt_management"
        self.pm.mkdir(parents=True)
        (self.root / "tests").mkdir()
        for name, wert in (("ROOT", self.root), ("PM", self.pm)):
            alt = getattr(kette, name)
            setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)
        self.aufrufe = self.aussen / "venv_aufrufe.txt"
        (self.root / "nur_venv").mkdir()
        (self.root / "nur_venv" / "nur_im_venv.py").write_text("WERT = 1\n", encoding="utf-8")
        self.venv = self.venv_anlegen(self.root)
        (self.root / ".gitignore").write_text(".venv/\nnur_venv/\n__pycache__/\n", encoding="utf-8")
        (self.root / "code_k.py").write_text("def f():\n    return 0\n", encoding="utf-8")
        (self.root / "tests" / "test_k.py").write_text(TEST_K, encoding="utf-8")
        (self.pm / "spec_20261107_k.md").write_text(SPEC_K, encoding="utf-8")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "Spec k")
        (self.root / "code_k.py").write_text("def f():\n    return 1\n", encoding="utf-8")

    def venv_anlegen(self, ordner: Path) -> Path:
        py = ordner / ".venv" / "bin" / "python"
        py.parent.mkdir(parents=True, exist_ok=True)
        py.write_text("#!/bin/sh\n"
                      f'echo "$@" >> "{self.aufrufe}"\n'
                      f'PYTHONPATH="{self.root / "nur_venv"}${{PYTHONPATH:+:$PYTHONPATH}}" exec "{sys.executable}" "$@"\n',
                      encoding="utf-8")
        py.chmod(py.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return py

    def venv_weg(self):
        shutil.move(str(self.root / ".venv"), str(self.aussen / "venv_weg"))

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, text=True).stdout

    def gelesen(self) -> str:
        return self.aufrufe.read_text(encoding="utf-8") if self.aufrufe.exists() else ""

    def rufen(self, fn, *a):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = fn(*a)
        return code, aus.getvalue()


class Auswahl(Temp):

    def test_t1_test_python_auswahl(self):
        """T1: test_python – nächstes .venv bis ROOT, Pfad nicht aufgelöst, sonst sys.executable; Standardwert echtes Repo"""
        tp = kette.test_python
        self.assertEqual(tp(self.root / "tests" / "test_k.py"), str(self.venv))
        self.assertEqual(tp("tests/test_k.py"), str(self.venv))
        unter = self.root / "tests" / "sub"
        unter.mkdir()
        eigen = self.venv_anlegen(unter)
        self.assertEqual(tp(unter / "test_x.py"), str(eigen))
        self.assertEqual(tp("tests/test_k.py"), str(self.venv))
        self.assertEqual(tp(self.aussen / "test_fremd.py"), sys.executable)
        self.venv_anlegen(self.root.parent)
        self.venv_weg()
        self.assertEqual(tp("tests/test_k.py"), sys.executable, "venv oberhalb von ROOT darf nicht zählen")
        link = self.root / ".venv" / "bin" / "python"
        link.parent.mkdir(parents=True)
        link.symlink_to(sys.executable)
        self.assertEqual(tp("tests/test_k.py"), str(link), "venv-Python nicht auflösen")
        link.unlink()
        link.symlink_to(self.aussen / "gibt_es_nicht")
        self.assertEqual(tp("tests/test_k.py"), sys.executable, "kaputter Link zählt nicht")
        # Nachgeschärft 07.11. (Claude): ROOT hinter einem Link (macOS: /var -> /private/var) – kein Hänger
        import threading
        echt_ordner = self.aussen / "echt"
        (echt_ordner / "tests").mkdir(parents=True)
        verweis = self.aussen / "verweis"
        verweis.symlink_to(echt_ordner)
        setattr(kette, "ROOT", verweis)
        erg = []
        for arg in ("tests/test_k.py", verweis / "tests" / "test_k.py"):
            th = threading.Thread(target=lambda a=arg: erg.append(tp(a)), daemon=True)
            th.start()
            th.join(5)
            self.assertFalse(th.is_alive(), f"test_python hängt bei ROOT hinter einem Link ({arg})")
        self.assertEqual(erg, [sys.executable, sys.executable])
        self.venv_anlegen(echt_ordner)
        self.assertEqual(tp("tests/test_k.py"), str(echt_ordner / ".venv" / "bin" / "python"))
        setattr(kette, "ROOT", ECHT)
        echt = ECHT / ".venv" / "bin" / "python"
        erwartet = str(echt) if echt.exists() else sys.executable
        self.assertEqual(tp("tests/test_pruefen_venv.py"), erwartet)
        self.assertEqual(tp(ECHT / "tests" / "test_pruefen_venv.py"), erwartet)


class Laeufe(Temp):

    def test_t2_tests_laufen_mit_venv(self):
        """T2: tests_laufen startet die Tests mit dem venv-Python; ohne venv wie bisher sys.executable"""
        erg = kette.tests_laufen(self.root / "tests" / "test_k.py", 60)
        self.assertEqual(erg, {"test_t1_wert": "ok"})
        self.assertIn("-X pycache_prefix=", self.gelesen())
        self.venv_weg()
        erg = kette.tests_laufen(self.root / "tests" / "test_k.py", 60)
        self.assertNotIn("ok", erg.values(), erg)
        self.assertIn("ERROR", erg.values(), erg)
        self.assertEqual(self.gelesen().count("pycache_prefix="), 1)

    def test_t3_unittest_mit_venv(self):
        """T3: pruefen/unittest mit dem venv-Python, erste Ausgabezeile nennt es"""
        teile = kette._pruefen_teile("k")
        code, out = teile["unittest"]
        self.assertEqual(code, 0, out)
        self.assertTrue(out.startswith(f"Python: {self.venv}\n"), out[:200])
        self.assertIn("OK", out)
        self.assertIn("-m unittest -v tests/test_k.py", self.gelesen())

    def test_t4_unittest_ohne_venv(self):
        """T4: ohne venv – unittest mit sys.executable, Zeile nennt es, fehlendes Modul ergibt Abweichung"""
        self.venv_weg()
        code, out = kette._pruefen_teile("k")["unittest"]
        self.assertEqual(code, 1, out)
        self.assertTrue(out.startswith(f"Python: {sys.executable}\n"), out[:200])
        self.assertIn("nur_im_venv", out)
        self.assertEqual(self.gelesen(), "")

    def test_t5_gegenprobe_mit_venv(self):
        """T5: gegenprobe läuft mit dem venv-Python und erkennt die zurückgesetzte Datei"""
        code, out = kette._pruefen_teile("k")["gegenprobe"]
        self.assertEqual(code, 0, out)
        self.assertIn("1 von 1 Tests werden durch eine einzelne alte Datei rot.", out)
        self.assertIn("code_k.py", out)
        self.assertGreaterEqual(self.gelesen().count("pycache_prefix="), 2)


class Einstieg(Temp):

    def test_t6_pruefen_ueber_main(self):
        """T6: kette.main(['pruefen', 'k']) – Prüfdatei nennt das venv-Python, unittest ok"""
        code, out = self.rufen(kette.main, ["pruefen", "k"])
        datei = self.pm / "pruefung_20261107_k.md"
        if not datei.exists():
            datei = next(self.root.glob("docs/projekt_management/**/pruefung_*_k.md"))
        text = datei.read_text(encoding="utf-8")
        self.assertIn(f"## unittest  (Exit 0)\n\n```\nPython: {self.venv}\n", text)
        self.assertIn("unittest: ok", out)
        self.assertIn("gegenprobe: ok", out)


if __name__ == "__main__":
    unittest.main()
