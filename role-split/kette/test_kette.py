#!/usr/bin/env python3
"""Selbsttest fuer kette.py (stdlib, ohne Modell):  python3 role-split/kette/test_kette.py"""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kette  # noqa: E402

KOPF = "# Verdikt: x\n\n## Ergebnis\n\n**{u}** – Text.\n\n## Anforderungen einzeln\n\n" \
       "| Nr. | Anforderung | Befund | Fundstelle |\n|---|---|---|---|\n{anf}\n\n## Befunde\n\n" \
       "| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg |\n" \
       "|---|---|---|---|---|---|---|---|\n{bef}\n"


def lauf(fn, *a):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = fn(*a)
    return code, buf.getvalue()


class UrteilTests(unittest.TestCase):
    def verdikt(self, u, anf, bef):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        p = Path(d.name) / "verdict_x.md"
        p.write_text(KOPF.format(u=u, anf=anf, bef=bef), encoding="utf-8")
        return p

    def test_haenger_als_niedrig_wird_hoch(self):
        # Tiefenpruefung 17.10. im neuen Format: Timeout fehlt, 'niedrig', aber Fehler bleibt unbemerkt
        p = self.verdikt("PASS", "| A1 | Fehler-Mail | erfüllt | x.py:1 |",
                         "| 3 | nein | ja | nein | niedrig | x.py:192 | kein SMTP-Timeout | timeout= setzen |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 1)
        self.assertIn("Es gilt:             NACHBESSERN", out)
        self.assertIn("WIDERSPRUCH", out)
        self.assertIn("Befund 3", out)

    def test_harte_vorgabe_echter_versand(self):
        p = self.verdikt("NACHBESSERN", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | nein | ja | niedrig | handover | echter Versand im Test | Sperre |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 1)
        self.assertIn("Harte Vorgabe -> hoch", out)

    def test_teilweise_erfuellt_verhindert_pass(self):
        p = self.verdikt("PASS", "| A2 | x | teilweise erfüllt | x |",
                         "| 1 | nein | nein | nein | niedrig | x | Kosmetik | - |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 1)
        self.assertIn("Anforderungen offen", out)

    def test_sauberes_pass_bleibt(self):
        p = self.verdikt("PASS", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | nein | nein | niedrig | x | Kosmetik | - |")
        code, out = lauf(kette.urteil, p)
        self.assertEqual(code, 0)
        self.assertNotIn("WIDERSPRUCH", out)

    def test_regel_schwaecht_nie_ab(self):
        p = self.verdikt("FAIL", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | nein | nein | niedrig | x | x | - |")
        code, out = lauf(kette.urteil, p)
        self.assertIn("Es gilt:             FAIL", out)

    def test_anhaengen_nur_einmal(self):
        p = self.verdikt("PASS", "| A1 | x | erfüllt | x |",
                         "| 1 | nein | ja | nein | mittel | x | x | - |")
        lauf(kette.urteil, p, True); lauf(kette.urteil, p, True)
        self.assertEqual(p.read_text(encoding="utf-8").count("## Mechanisches Urteil"), 1)


class AbgleichTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        root = Path(self.d.name); (root / "docs/projekt_management").mkdir(parents=True)
        self.alt = (kette.ROOT, kette.PM)
        kette.ROOT, kette.PM = root, root / "docs/projekt_management"
        self.addCleanup(lambda: setattr(kette, "ROOT", self.alt[0]) or setattr(kette, "PM", self.alt[1]))
        (kette.PM / "spec_20261018_t.md").write_text(
            "# Spec\n\n## Testplan\n\n### T1: Timeout bei schweigendem Server (A1)\n\n"
            "### T2: Fehler-Mail ohne markdown-Paket (A6)\n\n### T3: Zaehler im Dateinamen (A4)\n",
            encoding="utf-8")

    def handover(self, getestet, nicht=""):
        (kette.PM / "handover_20261018_t.md").write_text(
            f"# Handover\n\n## Getestet (mit echter Ausgabe)\n\n{getestet}\n\n## Nicht getestet\n\n{nicht}\n",
            encoding="utf-8")

    def test_ausgetauschter_test_wird_erkannt(self):
        self.handover("**T1: Timeout bei schweigendem Server**\n**T2: Pipeline ohne --dry-run**\n"
                      "**T3: Zaehler im Dateinamen**")
        code, out = lauf(kette.abgleich, "t")
        self.assertEqual(code, 1)
        self.assertIn("ANDERS    T2", out)

    def test_fehlender_und_nicht_getesteter(self):
        self.handover("**T1: Timeout bei schweigendem Server**", "- T3: kein Mock moeglich")
        code, out = lauf(kette.abgleich, "t")
        self.assertIn("FEHLT     T2", out)
        self.assertIn("NICHT GET T3", out)

    def test_alles_passend_mit_testskript(self):
        self.handover("**T1: Timeout bei schweigendem Server (A1)**\n**T2: Fehler-Mail ohne markdown-Paket**\n"
                      "**T3: Zaehler im Dateinamen**")
        (kette.ROOT / "tests").mkdir()
        (kette.ROOT / "tests/test_t.py").write_text(
            "def test_t1_x(): assert 1\ndef test_t2_x(): assert 2\ndef test_t3(): assert 3\n", encoding="utf-8")
        code, out = lauf(kette.abgleich, "t")
        self.assertEqual(code, 0, out)
        self.assertIn("alle 3 Tests als Methode", out)

    def test_testskript_ohne_methode(self):
        self.handover("**T1: Timeout bei schweigendem Server**\n**T2: Fehler-Mail ohne markdown-Paket**\n"
                      "**T3: Zaehler im Dateinamen**")
        (kette.ROOT / "tests").mkdir()
        (kette.ROOT / "tests/test_t.py").write_text("def test_t1_x(): pass\n", encoding="utf-8")
        code, out = lauf(kette.abgleich, "t")
        self.assertEqual(code, 1)
        self.assertIn("T2, T3", out)


DS = chr(34) * 3

class MethodenTests(unittest.TestCase):
    def test_leere_und_doppelte_methoden(self):
        code = (
            "import unittest\n"
            "class A(unittest.TestCase):\n"
            "    def test_t1_ok(self):\n        self.assertEqual(1, 1)\n"
            "    def test_t2_leer(self):\n        x = 1\n"
            "    def test_t3_kopie(self):\n        " + DS + "anderer Docstring" + DS + "\n        self.assertEqual(1, 1)\n"
            "    def test_t4_raises(self):\n        with self.assertRaises(ValueError):\n            int('x')\n")
        h = kette.methoden_pruefen(code)
        self.assertTrue(any("OHNE PRUEF test_t2_leer" in x for x in h), h)
        self.assertTrue(any("DOPPELT   test_t3_kopie" in x for x in h), h)
        self.assertFalse(any("test_t4_raises" in x for x in h), h)


class GegenprobeTests(unittest.TestCase):
    def test_rot_und_gruen(self):
        import subprocess
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        root = Path(d.name)
        def git(*a):
            subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                           check=True, capture_output=True)
        git("init", "-q")
        (root / "mod.py").write_text("def f():\n    return 1\n")
        git("add", "."); git("commit", "-qm", "alt")
        alt = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        (root / "mod.py").write_text("def f():\n    return 2\n")
        (root / "neu.py").write_text("X = 1\n")
        (root / "tests").mkdir()
        (root / "tests" / "test_g.py").write_text(
            "import sys, unittest\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent))\n"
            "class T(unittest.TestCase):\n"
            "    def test_t1_neu(self):\n        import mod\n        self.assertEqual(mod.f(), 2)\n"
            "    def test_t2_bestand(self):\n        self.assertEqual(1, 1)\n")
        alt_root = kette.ROOT; kette.ROOT = root
        self.addCleanup(lambda: setattr(kette, "ROOT", alt_root))
        code, out = lauf(kette.gegenprobe, "g", alt, 60)
        self.assertEqual(code, 1, out)
        self.assertIn("rot   test_t1_neu  <- mod.py", out)
        self.assertIn("GRUEN test_t2_bestand", out)
        self.assertEqual((root / "mod.py").read_text(), "def f():\n    return 2\n")
        self.assertTrue((root / "neu.py").exists())


class PruefenTests(unittest.TestCase):
    def setUp(self):
        import subprocess
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        self.root = root = Path(d.name)
        def git(*a):
            subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                           check=True, capture_output=True)
        self.git = git
        git("init", "-q")
        (root / "docs/projekt_management").mkdir(parents=True)
        (root / "mod.py").write_text("def f():\n    return 1\n")
        git("add", "."); git("commit", "-qm", "Spec g")
        self.erster = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                                     capture_output=True, text=True).stdout.strip()
        (root / "mod.py").write_text("def f():\n    return 2\n")
        git("add", "."); git("commit", "-qm", "Spec g")          # spaeterer gleichnamiger Commit
        (root / "tests").mkdir()
        (root / "tests" / "test_g.py").write_text(
            "import sys, unittest\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent))\n"
            "class T(unittest.TestCase):\n"
            "    def test_t1_neu(self):\n        import mod\n        self.assertEqual(mod.f(), 2)\n")
        for name, wert in (("ROOT", root), ("PM", root / "docs/projekt_management")):
            alt = getattr(kette, name); setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)

    def test_aeltester_spec_commit_und_datei(self):
        self.assertEqual(kette.spec_commit("g"), self.erster)
        code, out = lauf(kette.pruefen, "g")
        dateien = list((self.root / "docs/projekt_management").glob("pruefung_*_g.md"))
        self.assertEqual(len(dateien), 1, out)
        text = dateien[0].read_text(encoding="utf-8")
        for teil in ("## abgleich", "## unittest", f"## gegenprobe gegen {self.erster}", "Ran 1 test", "rot   test_t1_neu"):
            self.assertIn(teil, text)
        self.assertEqual(code, 2)                                  # abgleich: keine Spec -> 2, sichtbar
        self.assertIn("abgleich: FEHLER", out)

    def test_ohne_spec_commit_abbruch(self):
        self.assertIsNone(kette.spec_commit("anders"))
        code, out = lauf(kette.pruefen, "anders")
        self.assertEqual(code, 2); self.assertIn("Kein Commit 'Spec anders'", out)
        self.assertEqual(list((self.root / "docs/projekt_management").glob("pruefung_*")), [])

    def test_prompt_review_nimmt_spec_commit_statt_head(self):
        (kette.PM / "spec_20261022_g.md").write_text("# Spec\n", encoding="utf-8")
        code, out = lauf(kette.prompt, "review", "g", None, None)
        self.assertEqual(code, 0)
        self.assertIn(self.erster, out)

    def _paket_vorbereiten(self):
        pm = kette.PM
        (pm / "spec_20261022_g.md").write_text(
            "# Spec\n\n## Ziel\nZIELTEXT\n\n## Nicht-Ziele\nNZTEXT\n\n## Quellen\nQUELLTEXT\n\n## Anforderungen\n### A1: Eins\nANFTEXT\n\n"
            "## Fehlerpfade\nFEHLERTABELLE\n\n## Testplan\n### T1: Erster\n- **Prüft:** A1\n- **Aufbau:** AUFBAUTEXT\n"
            "- **Erwartung:** ERWARTET1\n\n## Offene Fragen\nOQTEXT\n", encoding="utf-8")
        (pm / "anforderung_20261022_g.md").write_text("HAWE WILL X\n", encoding="utf-8")
        (pm / "handover_20261022_g.md").write_text(
            "# HO\n## Umgesetzt\nUMGESETZT\n## Getestet (mit echter Ausgabe)\nLANGE AUSGABE\n"
            "## Abweichungen von der Spec\nABWEICHUNG1\n### Detail\nDETAIL1\n## Nachbesserung 2\nNB2\n"
            "### Abweichungen bei Nachbesserung 2\nABWEICHUNG2\n", encoding="utf-8")
        (pm / "pruefung_20261022_g.md").write_text(
            "# Pruefung g\n\n- Kurz: abgleich: ok | unittest: ok\n\n## abgleich  (Exit 0)\nABGL\n"
            "## unittest  (Exit 0)\ntest_x ... ok\nRan 1 test in 0.1s\nOK\n## gegenprobe gegen x  (Exit 1)\nGEGEN\n  GRUEN test_t1_neu  (wird mit keiner alten Datei rot)\n",
            encoding="utf-8")
        (self.root / "neu_modul.py").write_text("Y = 1\n")

    def test_paket_inhalt(self):
        self._paket_vorbereiten()
        code, out = lauf(kette.paket, "g")
        self.assertEqual(code, 0, out)
        text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
        for soll in ("HAWE WILL X", "ZIELTEXT", "ANFTEXT", "### T1: Erster", "ERWARTET1", "OQTEXT",
                     "### mod.py (stark umgebaut", "   2      return 2", "### neu_modul.py (neue Datei", "   1  Y = 1",
                     "`test_t1_neu` (Zeile", "ABWEICHUNG1", "DETAIL1", "ABWEICHUNG2",
                     "- Kurz: abgleich: ok", "ABGL", "GEGEN", "Ran 1 test", self.erster,
                     "NZTEXT", "#### test_t1_neu", "self.assertEqual(mod.f(), 2)"):
            self.assertIn(soll, text, soll)
        for nicht in ("QUELLTEXT", "FEHLERTABELLE", "AUFBAUTEXT", "LANGE AUSGABE", "UMGESETZT", "test_x ... ok"):
            self.assertNotIn(nicht, text, nicht)
        self.assertIn("Zeichen, ca.", out)

    def test_paket_nur_dateien_aus_handover_und_nie_werkzeug(self):
        self._paket_vorbereiten()
        (self.root / "role-split").mkdir()
        (self.root / "role-split" / "werkzeug.py").write_text("W = 1\n")
        ho = kette.PM / "handover_20261022_g.md"
        ho.write_text(ho.read_text(encoding="utf-8") + "\n## Geänderte und neue Dateien\n- `neu_modul.py` – neu\n",
                      encoding="utf-8")
        lauf(kette.paket, "g")
        text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
        self.assertIn("### neu_modul.py", text)
        self.assertNotIn("### mod.py", text)
        self.assertNotIn("werkzeug.py", text.split("## 3.")[1].split("## 4.")[0])

    def test_paket_kleine_aenderung_als_diff(self):
        self._paket_vorbereiten()
        groß = "".join(f"def f{i}():\n    return {i}\n" for i in range(40))
        (self.root / "gross.py").write_text(groß)
        self.git("add", "gross.py"); self.git("commit", "-qm", "gross")
        import subprocess
        alt_commit = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True).stdout.strip()
        (self.root / "gross.py").write_text(groß.replace("return 7\n", "return 70\n"))
        lauf(kette.paket, "g", alt_commit)
        text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
        self.assertIn("### gross.py (Diff", text)
        self.assertIn("+    return 70", text)

    def test_paket_kappt_lange_dateien(self):
        self._paket_vorbereiten()
        (self.root / "neu_modul.py").write_text("".join(f"Z{i} = {i}\n" for i in range(50)))
        alt = kette.PAKET_DATEI_ZEILEN; kette.PAKET_DATEI_ZEILEN = 10
        self.addCleanup(setattr, kette, "PAKET_DATEI_ZEILEN", alt)
        lauf(kette.paket, "g")
        text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
        self.assertIn("40 weitere Zeilen gekuerzt", text)
        self.assertNotIn("Z45 = 45", text)

    def test_paket_ohne_spec_schreibt_nichts(self):
        code, out = lauf(kette.paket, "g")
        self.assertEqual(code, 2); self.assertIn("Keine Spec", out)
        self.assertEqual(list(kette.PM.glob("review_paket_*")), [])

    def test_prompt_review_baut_paket_und_nennt_es(self):
        self._paket_vorbereiten()
        code, out = lauf(kette.prompt, "review", "g", None, None)
        self.assertEqual(code, 0)
        self.assertTrue((kette.PM / "review_paket_20261022_g.md").exists())
        self.assertIn("review_paket_20261022_g.md", out)

    def test_kurztitel_mit_pfad_abgelehnt(self):
        code, out = lauf(kette.pruefen, "../x")
        self.assertEqual(code, 2); self.assertIn("ungueltig", out)


class TestcodeTests(unittest.TestCase):
    def test_auffaellige_ids(self):
        txt = "  GRUEN test_t12_x  (..)\n  LADEN test_t3_y (..)\n  ANDERS    T8    Spec: …\n  rot   test_t1_z <- a.py\n"
        self.assertEqual(kette._auffaellige_tests(txt), {"test_t12_x", "test_t3_y", "t8"})

    def test_code_nach_id_und_name(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        p = Path(d.name) / "t.py"
        p.write_text("class T:\n    def test_t8_leer(self):\n        assert 1\n"
                     "    def test_t16_zweit(self):\n        assert 2\n    def test_t1_ok(self):\n        assert 3\n")
        out = kette._testcode(p, {"t8", "test_t16_zweit"})
        self.assertIn("#### test_t8_leer", out); self.assertIn("#### test_t16_zweit", out)
        self.assertNotIn("test_t1_ok", out)
        self.assertEqual(kette._testcode(p, set()), "")


class QuelleLesenTests(unittest.TestCase):
    """Zeilen aus der K6-Spec (22.10.), die vorher als UNKLAR verworfen wurden."""
    def test_formen(self):
        f = kette.quelle_lesen
        q = f("- `a/b.py` `def init_db` — SQLite-Schema; Muster")
        self.assertEqual((q["art"], q["name"]), ("def", "init_db")); self.assertTrue(q["zweck"].startswith("SQLite"))
        q = f("- `a/b.py` `def record_sent_week` (Zeilen 340–390) — atomares Schreiben")
        self.assertEqual((q["art"], q["name"], q["von"]), ("def", "record_sent_week", None))
        q = f("- `t/x.py` `TestBase.setUp` — Mocking-Muster")
        self.assertEqual((q["art"], q["name"]), (None, "TestBase.setUp"))
        q = f("- `t/x.py` `T9_Pipeline` — E2E")
        self.assertEqual(q["name"], "T9_Pipeline")
        q = f("- `c/l.plist` `EnvironmentVariables` — LAB_DIR")
        self.assertEqual(q["name"], "EnvironmentVariables")
        q = f("- `a/b.py` Zeilen 30–33 — `BASE_DIR = Path(...)`")
        self.assertEqual((q["von"], q["bis"]), (30, 33))
        q = f("- `a/requirements.txt` — vorhandene Abhängigkeiten")
        self.assertEqual((q["von"], q["name"], q["text"]), (None, None, None))
        q = f("- `CLAUDE.md` Abschnitt „Key environment variables\u201c — LAB_BIND")
        self.assertEqual(q["text"], "Key environment variables")
        self.assertIsNone(f("- `nur ein wort` ohne Pfad"))

    def test_quellen_holt_alles_und_meldet_gedaechtniszeilen(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        root = Path(d.name); pm = root / "docs/projekt_management"; pm.mkdir(parents=True)
        (root / "m.py").write_text("X = 1\n\nclass TestBase:\n    def setUp(self):\n        self.a = 1\n\n"
                                   "    def tearDown(self):\n        pass\n\n\ndef init_db():\n    return 2\n")
        (root / "l.plist").write_text("<dict>\n<key>EnvironmentVariables</key>\n<dict/>\n</dict>\n")
        (pm / "spec_20261022_q.md").write_text(
            "# S\n\n## Quellen\n\n- `m.py` `def init_db` — DB\n- `m.py` `TestBase.setUp` — Mock\n"
            "- `l.plist` `EnvironmentVariables` — Env\n- `m.py` Zeilen 1–1 — `BASE_DIR = Path()`\n\n## Anforderungen\n",
            encoding="utf-8")
        for name, wert in (("ROOT", root), ("PM", pm)):
            alt = getattr(kette, name); setattr(kette, name, wert); self.addCleanup(setattr, kette, name, alt)
        code, out = lauf(kette.quellen, "q")
        text = (pm / "quellen_20261022_q.md").read_text(encoding="utf-8")
        self.assertIn("def init_db (Zeilen 11–12)", text)
        self.assertIn("def TestBase.setUp (Zeilen 4–5)", text); self.assertNotIn("tearDown", text)
        self.assertIn("Textstelle „EnvironmentVariables“", text)
        self.assertIn("**PRÜFEN:**", text)                     # Zeilen 1–1 enthalten BASE_DIR nicht
        self.assertNotIn("UNKLAR", text)
        self.assertEqual(code, 1); self.assertIn("PRÜFEN", out)


class LaufTests(unittest.TestCase):
    def test_lauf_nummer_im_verdiktnamen(self):
        code, out = lauf(kette.prompt, "review", "mein_thema", "20261018", "abc1234", 2)
        self.assertEqual(code, 0)
        self.assertIn("_<modellkürzel>_lauf2.md", out)
        self.assertIn("Verdikte anderer Läufe liest du nicht.", out)
        code, out = lauf(kette.prompt, "review", "mein_thema", "20261018", "abc1234")
        self.assertNotIn("_lauf", out)


class PromptTests(unittest.TestCase):
    def test_alle_vorlagen_fuellbar(self):
        for s in kette.SCHRITTE:
            code, out = lauf(kette.prompt, s, "mein_thema", "20261018", "abc1234")
            self.assertEqual(code, 0, s)
            self.assertNotIn("{", out, s)
            self.assertIn("mein_thema", out, s)



class AnforderungTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        root = Path(self.d.name); (root / "docs/projekt_management").mkdir(parents=True)
        self.alt = (kette.ROOT, kette.PM)
        kette.ROOT, kette.PM = root, root / "docs/projekt_management"
        self.addCleanup(lambda: setattr(kette, "ROOT", self.alt[0]) or setattr(kette, "PM", self.alt[1]))

    def test_anlegen_antwort_und_kein_ueberschreiben(self):
        code, _ = lauf(kette.anforderung, "t", "Zweitlauf darf nichts verlieren.\nZweite Zeile.", None, None, "20261018")
        self.assertEqual(code, 0)
        p = kette.PM / "anforderung_20261018_t.md"
        self.assertEqual(kette.aufgabe_lesen(p), "Zweitlauf darf nichts verlieren.\nZweite Zeile.")
        code, _ = lauf(kette.anforderung, "t", None, "Jeder Eintrag genau einmal per Mail.", "Mail nach Zweitlauf?", None)
        self.assertEqual(code, 0)
        text = p.read_text(encoding="utf-8")
        self.assertIn("> Jeder Eintrag genau einmal per Mail.", text)
        self.assertIn("Frage: Mail nach Zweitlauf?", text)
        code, _ = lauf(kette.anforderung, "t", "anders", None, None, None)
        self.assertEqual(code, 2, "vorhandene Anforderung darf nicht ueberschrieben werden")
        self.assertIn("Zweitlauf darf nichts verlieren.", p.read_text(encoding="utf-8"))

    def test_spec_prompt_fuellt_aufgabe(self):
        lauf(kette.anforderung, "t", "Zweitlauf darf nichts verlieren.", None, None, "20261018")
        code, out = lauf(kette.prompt, "spec", "t", None, "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("Zweitlauf darf nichts verlieren.", out)
        self.assertNotIn("<AUFGABE", out)
        self.assertIn("docs/projekt_management/anforderung_20261018_t.md", out)
        self.assertIn("spec_20261018_t.md", out)

    def test_review_nimmt_datum_der_spec(self):
        lauf(kette.anforderung, "t", "Aufgabe.", None, None, "20261018")
        (kette.PM / "spec_20261018_t.md").write_text("# Spec\n", encoding="utf-8")
        code, out = lauf(kette.prompt, "review", "t", None, "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("spec_20261018_t.md", out)
        self.assertIn("handover_20261018_t.md", out)
        self.assertIn("anforderung_20261018_t.md", out)
        self.assertNotIn("{", out)

    def test_ohne_anforderung_platzhalterpfad(self):
        code, out = lauf(kette.prompt, "review", "x", "20261020", "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("anforderung_20261020_x.md", out)



class QuellenTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        root = Path(self.d.name); (root / "docs/projekt_management").mkdir(parents=True); (root / "src").mkdir()
        self.alt = (kette.ROOT, kette.PM)
        kette.ROOT, kette.PM = root, root / "docs/projekt_management"
        self.addCleanup(lambda: setattr(kette, "ROOT", self.alt[0]) or setattr(kette, "PM", self.alt[1]))
        (root / "src/mod.py").write_text(
            "MAGIC = 0x46554747\n\n\n@dekor\ndef lesen(f):\n    kopf = f.read(4)\n\n    return kopf\n\n\n"
            "class Feld:\n    TYPEN = {0: 'u8'}\n\n    def wert(self):\n        return 1\n\n\ndef danach():\n    pass\n",
            encoding="utf-8")
        (root / "src/kurz.txt").write_text("a\nb\n", encoding="utf-8")

    def spec(self, quellen: str):
        (kette.PM / "spec_20261021_t.md").write_text(f"# Spec\n\n## Quellen\n\n{quellen}\n## Anforderungen\n", encoding="utf-8")

    def ergebnis(self):
        return (kette.PM / "quellen_20261021_t.md").read_text(encoding="utf-8")

    def test_zeilen_def_class_ganz(self):
        self.spec("- `src/mod.py` Zeilen 1–1 – Magic\n- `src/mod.py` def lesen – Kopf\n"
                  "- `src/mod.py` class Feld – Typen\n- `src/kurz.txt` – ganz\n")
        code, out = lauf(kette.quellen, "t", None)
        self.assertEqual(code, 0, out)
        t = self.ergebnis()
        self.assertIn("1| MAGIC = 0x46554747", t)
        self.assertIn("@dekor", t, "Dekorator gehoert zur def")
        self.assertIn("return kopf", t)
        self.assertIn("return 1", t, "Methode gehoert zur class")
        self.assertNotIn("def danach", t, "naechste Funktion gehoert nicht dazu")
        self.assertIn("1| a", t); self.assertIn("2| b", t)
        self.assertIn("– Kopf", t)

    def test_def_in_backticks_mit_klammern_und_unklar(self):
        self.spec("- `src/mod.py` `def lesen()` – Kopf\n- `src/mod.py` `class Feld` – Typen\n"
                  "- `src/mod.py` irgendwo unten – unklare Angabe\n")
        code, out = lauf(kette.quellen, "t", None)
        t = self.ergebnis()
        self.assertIn("return kopf", t)
        self.assertIn("return 1", t)
        self.assertIn("**UNKLAR:**", t, "unklare Fundstelle muss gemeldet, nicht verschluckt werden")
        self.assertIn("UNKLAR (nicht geholt)", out)
        self.assertEqual(code, 1)

    def test_fehlt_und_verweigert(self):
        self.spec("- `src/gibtsnicht.py` – x\n- `../../etc/passwd` – x\n- `src/mod.py` def fehlt – x\n")
        code, out = lauf(kette.quellen, "t", None)
        self.assertEqual(code, 1)
        t = self.ergebnis()
        self.assertEqual(t.count("**FEHLT:**"), 2)
        self.assertIn("**VERWEIGERT:**", t)

    def test_ohne_abschnitt(self):
        (kette.PM / "spec_20261021_t.md").write_text("# Spec\n\n## Anforderungen\n", encoding="utf-8")
        code, _ = lauf(kette.quellen, "t", None)
        self.assertEqual(code, 2)

    def test_umsetzung_prompt_nennt_quellen(self):
        self.spec("- `src/kurz.txt` – ganz\n")
        code, out = lauf(kette.prompt, "umsetzung", "t", None, "abc1234")
        self.assertEqual(code, 0)
        self.assertIn("docs/projekt_management/quellen_20261021_t.md", out)
        self.assertNotIn("{", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
