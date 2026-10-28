#!/usr/bin/env python3
"""Vorgabe-Tests fuer mcp_kette (spec_20261028_mcp_kette.md, T1–T8).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: Jeder Test arbeitet in tempfile.TemporaryDirectory() mit umgebogenem
kette_werkzeuge.ROOT / KETTE_PY / LAUF_DIR. Statt kette.py laeuft ein Ersatzskript, das nur
schlaeft und druckt; git nur in einem Wegwerf-Repo im Temp-Verzeichnis.
kette_werkzeuge wird in jeder Methode importiert (rot vorab).
"""
import ast
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "mcp-server"))

ERSATZ = '''import os, sys, time
cmd, kt = sys.argv[1], sys.argv[2]
if cmd == "lauf":
    print(f"Groesse: lauf {kt}")
    time.sleep(float(os.environ.get("ERSATZ_DAUER", "1")))
    print("HALT – Entscheidung Hawe.")
    sys.exit(int(os.environ.get("ERSATZ_EXIT", "3")))
if cmd == "status":
    print(f"Status {kt}")
    print("Naechster Schritt: Ersatz")
    sys.exit(0)
sys.exit(9)
'''

SPEC = """# Spec: k

## Schreibbereich

- `pkg/`
- `einzeln.py`

## Vorgabe-Tests

- `tests/test_k.py`
"""


def kw():
    import kette_werkzeuge
    return kette_werkzeuge


class Temp(unittest.TestCase):
    def setUp(self):
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = Path(d.name).resolve()
        self.laeufe = self.root / "laeufe"
        self.ersatz = self.root / "ersatz_kette.py"
        self.ersatz.write_text(ERSATZ, encoding="utf-8")
        self.env = mock.patch.dict(os.environ, {"ERSATZ_DAUER": "1", "ERSATZ_EXIT": "3"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def modul(self):
        m = kw()
        for name, wert in (("ROOT", self.root), ("KETTE_PY", self.ersatz), ("LAUF_DIR", self.laeufe)):
            alt = getattr(m, name)
            setattr(m, name, wert)
            self.addCleanup(setattr, m, name, alt)
        self.addCleanup(self.aufraeumen, m)
        return m

    def aufraeumen(self, m):
        for p in list(getattr(m, "_PROZESSE", [])):
            try:
                p.wait(timeout=30)
            except Exception:
                p.kill()
        m._PROZESSE.clear()

    def warten_fertig(self, kt, sek=30):
        ende = time.time() + sek
        while time.time() < ende:
            if (self.laeufe / f"{kt}.json").is_file() and not (self.laeufe / "lauf.lock").exists():
                return json.loads((self.laeufe / f"{kt}.json").read_text(encoding="utf-8"))
            time.sleep(0.1)
        self.fail(f"Lauf {kt} nach {sek} s nicht fertig")

    def git(self, *a):
        return subprocess.run(["git", "-C", str(self.root), *a], capture_output=True, text=True, check=True).stdout


class Gemeinsam(Temp):

    def test_t1_ungueltiger_kurztitel(self):
        """T1: Ungültiger Kurztitel – jedes Werkzeug meldet FEHLER und tut nichts"""
        m = self.modul()
        for kt in ("../x", "K", "", "a b", "k;rm"):
            for fn in (m.kette_status, m.kette_lauf, m.kette_ergebnis, m.kette_commit):
                out = fn(kt)
                self.assertIsInstance(out, str)
                self.assertTrue(out.startswith("FEHLER"), f"{fn.__name__}({kt!r}): {out}")
                self.assertIn("ungültig", out, f"{fn.__name__}({kt!r}): Kurztitel nicht geprüft")
        self.assertFalse(self.laeufe.exists(), "Lauf-Ordner darf nicht angelegt werden")
        self.assertEqual(m._PROZESSE, [])


class Lauf(Temp):

    def test_t2_lauf_kehrt_sofort_zurueck_und_laeuft_durch(self):
        """T2: kette_lauf kehrt sofort zurück; Läufer schreibt Protokoll und Ergebnis und gibt die Sperre frei"""
        m = self.modul()
        os.environ["ERSATZ_DAUER"] = "2"
        t0 = time.monotonic()
        out = m.kette_lauf("k")
        dauer = time.monotonic() - t0
        self.assertLess(dauer, 1.5, f"blockiert {dauer:.1f} s")
        self.assertTrue(out.startswith("Lauf gestartet: k"), out)
        self.assertIn('kette_status(kurztitel="k")', out)
        self.assertTrue((self.laeufe / "lauf.lock").is_file(), "Sperre fehlt während des Laufs")
        sperre = json.loads((self.laeufe / "lauf.lock").read_text(encoding="utf-8"))
        self.assertEqual(sperre["kurztitel"], "k")
        e = self.warten_fertig("k")
        self.assertEqual(e["exit"], 3)
        self.assertEqual(e["kurztitel"], "k")
        self.assertGreaterEqual(e["ende"] - e["start"], 1.5)
        log = (self.laeufe / "k.log").read_text(encoding="utf-8")
        self.assertIn("Groesse: lauf k", log)
        self.assertIn("HALT", log)
        self.assertIsNone(m.laufender())

    def test_t3_nur_ein_lauf_und_schreibsperre(self):
        """T3: Während eines Laufs: zweiter Start und Commit abgelehnt; danach wieder frei"""
        m = self.modul()
        os.environ["ERSATZ_DAUER"] = "3"
        self.assertTrue(m.kette_lauf("k").startswith("Lauf gestartet"))
        out = m.kette_lauf("k2")
        self.assertTrue(out.startswith("ABGELEHNT"), out)
        self.assertIn("k", out)
        self.assertTrue(m.kette_lauf("k").startswith("ABGELEHNT"))
        self.assertTrue(m.kette_commit("k").startswith("ABGELEHNT"))
        self.assertEqual(len(m._PROZESSE), 1, "es darf nur ein Läufer gestartet sein")
        self.assertFalse((self.laeufe / "k2.log").exists())
        self.warten_fertig("k")
        os.environ["ERSATZ_DAUER"] = "0"
        self.assertTrue(m.kette_lauf("k2").startswith("Lauf gestartet: k2"))
        self.assertEqual(self.warten_fertig("k2")["exit"], 3)

    def test_t4_verwaiste_sperre(self):
        """T4: Verwaiste Sperre (toter Prozess, alte Sperre ohne pid) wird entfernt; frische ohne pid gilt als belegt"""
        m = self.modul()
        self.laeufe.mkdir()
        tot = subprocess.Popen([sys.executable, "-c", "pass"])
        tot.wait()
        sperre = self.laeufe / "lauf.lock"
        sperre.write_text(json.dumps({"kurztitel": "alt", "start": time.time(), "pid": tot.pid}), encoding="utf-8")
        self.assertIsNone(m.laufender())
        self.assertFalse(sperre.exists(), "verwaiste Sperre (toter Prozess) nicht entfernt")
        sperre.write_text(json.dumps({"kurztitel": "alt", "start": time.time() - 3600, "pid": None}),
                          encoding="utf-8")
        self.assertIsNone(m.laufender())
        self.assertFalse(sperre.exists(), "alte Sperre ohne pid nicht entfernt")
        sperre.write_text(json.dumps({"kurztitel": "alt", "start": time.time(), "pid": None}), encoding="utf-8")
        self.assertTrue(m.kette_lauf("k").startswith("ABGELEHNT"))
        sperre.write_text("kaputt", encoding="utf-8")
        os.environ["ERSATZ_DAUER"] = "0"
        self.assertTrue(m.kette_lauf("k").startswith("Lauf gestartet"), "kaputte Sperre muss als verwaist gelten")
        self.warten_fertig("k")
        os.environ["ERSATZ_DAUER"] = "30"
        self.assertTrue(m.kette_lauf("k").startswith("Lauf gestartet"))
        laeufer = m._PROZESSE[-1]
        os.killpg(laeufer.pid, signal.SIGKILL)
        time.sleep(0.5)
        self.assertTrue(sperre.exists(), "Sperre bleibt nach hartem Abbruch liegen")
        self.assertIsNone(m.laufender(), "abgeschossener Läufer (Zombie) gilt noch als lebend")
        self.assertFalse(sperre.exists())


class Anzeige(Temp):

    def test_t5_status(self):
        """T5: kette_status – keiner / läuft / letzter Exit, jeweils mit der Ausgabe von kette.py status"""
        m = self.modul()
        out = m.kette_status("k")
        self.assertTrue(out.startswith("Lauf: keiner"), out)
        self.assertIn("Status k", out)
        self.assertIn("Exit 0", out)
        os.environ["ERSATZ_DAUER"] = "2"
        m.kette_lauf("k")
        out = m.kette_status("k")
        self.assertTrue(out.startswith("Lauf: läuft (k"), out)
        self.assertIn("Status k", out)
        self.warten_fertig("k")
        out = m.kette_status("k")
        self.assertTrue(out.startswith("Lauf: letzter Lauf Exit 3"), out)

    def test_t6_ergebnis(self):
        """T6: kette_ergebnis – ohne Protokoll, nach dem Lauf, nur das Ende langer Protokolle"""
        m = self.modul()
        self.assertTrue(m.kette_ergebnis("k").startswith("Kein Protokoll für k"))
        os.environ["ERSATZ_DAUER"] = "0"
        m.kette_lauf("k")
        self.warten_fertig("k")
        out = m.kette_ergebnis("k")
        self.assertTrue(out.startswith("Lauf k: Exit 3"), out)
        self.assertIn("HALT", out)
        (self.laeufe / "lang.log").write_text("\n".join(f"zeile {i}" for i in range(200)) + "\n",
                                              encoding="utf-8")
        (self.laeufe / "lang.json").write_text(json.dumps({"kurztitel": "lang", "exit": 0, "start": 1, "ende": 2}),
                                               encoding="utf-8")
        out = m.kette_ergebnis("lang")
        self.assertIn("zeile 199", out)
        self.assertIn("zeile 120", out)
        self.assertNotIn("zeile 119\n", out)
        self.assertIn("Letzte 80 von 200 Zeilen", out)


class Commit(Temp):

    def repo(self):
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        pm = self.root / "docs" / "projekt_management" / "k"
        pm.mkdir(parents=True)
        (pm / "spec_20261028_k.md").write_text(SPEC, encoding="utf-8")
        (self.root / "pkg").mkdir()
        (self.root / "pkg" / "a.py").write_text("A = 1\n", encoding="utf-8")
        (self.root / "alt.py").write_text("x\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "Start")
        return self.git("rev-parse", "HEAD").strip()

    def test_t7_commit_zwei_schritte_nur_erlaubte_dateien(self):
        """T7: kette_commit – Vorschau ohne Commit, falscher Code abgelehnt, richtiger Code committet nur Erlaubtes"""
        m = self.modul()
        self.laeufe.mkdir()
        start = self.repo()
        (self.root / "pkg" / "a.py").write_text("A = 2\n", encoding="utf-8")
        (self.root / "pkg" / "neu.py").write_text("B = 1\n", encoding="utf-8")
        (self.root / "tests").mkdir()
        (self.root / "tests" / "test_k.py").write_text("# t\n", encoding="utf-8")
        (self.root / "docs" / "projekt_management" / "k" / "handover_20261028_k.md").write_text("h\n", encoding="utf-8")
        (self.root / "fremd.txt").write_text("f\n", encoding="utf-8")
        (self.root / "alt.py").unlink()
        (self.root / "vorgemerkt.txt").write_text("v\n", encoding="utf-8")
        self.git("add", "vorgemerkt.txt")

        out = m.kette_commit("k")
        self.assertTrue(out.startswith("Vorschau Commit k"), out)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), start, "Vorschau darf nicht committen")
        self.assertIn("Im Commit (4)", out)
        for p in ("pkg/a.py", "pkg/neu.py", "tests/test_k.py", "docs/projekt_management/k/handover_20261028_k.md"):
            self.assertIn(p, out)
        self.assertIn("Nicht im Commit (3)", out)
        code = out.split("Bestätigungscode: ")[1].split()[0]
        self.assertRegex(code, r"^[0-9a-f]{6}$")

        out = m.kette_commit("k", "000000" if code != "000000" else "111111")
        self.assertTrue(out.startswith("ABGELEHNT"), out)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), start)

        out = m.kette_commit("k", code)
        self.assertTrue(out.startswith("Committet:"), out)
        self.assertNotEqual(self.git("rev-parse", "HEAD").strip(), start)
        namen = set(self.git("show", "--name-only", "--format=", "HEAD").split())
        self.assertEqual(namen, {"pkg/a.py", "pkg/neu.py", "tests/test_k.py",
                                 "docs/projekt_management/k/handover_20261028_k.md"})
        self.assertTrue(self.git("log", "-1", "--format=%s").startswith("Kette k:"))
        rest = self.git("status", "--porcelain")
        self.assertIn("fremd.txt", rest)
        self.assertIn("alt.py", rest)
        self.assertIn("vorgemerkt.txt", rest, "vorher Vorgemerktes darf nicht mitgenommen werden")
        self.assertEqual(self.git("diff", "--cached", "--name-only").split(), ["vorgemerkt.txt"],
                         "fremde Dateien dürfen nicht vorgemerkt werden")

        self.assertTrue(m.kette_commit("k").startswith("Nichts zu committen für k"))
        self.assertTrue(m.kette_commit("ohne_spec").startswith("FEHLER"))


class Einstieg(unittest.TestCase):

    def test_t8_registrierung_und_server(self):
        """T8: registrieren meldet genau vier Werkzeuge an; lab_mcp_server schaltet sie nur mit MCP_ALLOW_KETTE=1 frei"""
        m = kw()

        class Attrappe:
            def __init__(self):
                self.namen = []

            def tool(self, *a, **k):
                def deco(fn):
                    self.namen.append(fn.__name__)
                    self.assertdoc(fn)
                    return fn
                return deco

            def assertdoc(self, fn):
                if not (fn.__doc__ or "").strip():
                    raise AssertionError(f"{fn.__name__} ohne Beschreibung")

        a = Attrappe()
        namen = m.registrieren(a)
        erwartet = ["kette_status", "kette_lauf", "kette_ergebnis", "kette_commit"]
        self.assertEqual(sorted(a.namen), sorted(erwartet))
        self.assertEqual(sorted(namen), sorted(erwartet))
        self.assertIn("nicht erneut", m.kette_lauf.__doc__.lower())
        self.assertIn("zustimmung", m.kette_commit.__doc__.lower())

        quelle = (ECHT / "mcp-server" / "lab_mcp_server.py").read_text(encoding="utf-8")
        baum = ast.parse(quelle)
        texte = {n.value for n in ast.walk(baum) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        self.assertIn("MCP_ALLOW_KETTE", texte)
        aufrufe = [n for n in ast.walk(baum) if isinstance(n, ast.Call)
                   and isinstance(n.func, ast.Attribute) and n.func.attr == "registrieren"]
        self.assertEqual(len(aufrufe), 1, "registrieren(mcp) genau einmal aufrufen")
        ifs = [n for n in ast.walk(baum) if isinstance(n, ast.If)
               and any(c is aufrufe[0] for c in ast.walk(n))]
        self.assertTrue(ifs, "registrieren muss hinter einer Bedingung stehen")
        self.assertTrue(any("ALLOW_KETTE" in ast.unparse(n.test) for n in ifs),
                        "Bedingung muss ALLOW_KETTE prüfen")
        zuw = [n for n in ast.walk(baum) if isinstance(n, ast.Assign)
               and any(isinstance(z, ast.Name) and z.id == "ALLOW_KETTE" for z in n.targets)]
        self.assertEqual(len(zuw), 1, "ALLOW_KETTE genau einmal zuweisen")
        self.assertIn("MCP_ALLOW_KETTE", ast.unparse(zuw[0].value))
        self.assertIn("READONLY", ast.unparse(zuw[0].value), "mit MCP_READONLY=1 muss es aus sein")

        r = subprocess.run([sys.executable, str(ECHT / "mcp-server" / "kette_werkzeuge.py")],
                           capture_output=True, text=True, timeout=30)
        self.assertEqual(r.returncode, 2, "ohne --laeufer: Exit 2")


if __name__ == "__main__":
    unittest.main()
