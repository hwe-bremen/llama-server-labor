#!/usr/bin/env python3
"""Tests fuer kette.py umsetzung-auto (K10, spec_20261027_umsetzung_auto.md, T1–T21).

Keine Aussenwirkung: Jeder Test baut ein eigenes temporaeres Git-Repo und biegt kette.ROOT/kette.PM
dorthin um. Statt opencode laeuft die Attrappe role-split/kette/testdata/opencode_fake.py; sie
verweigert jede Aktion ausserhalb des Temp-Ordners (technische Sperre). Zusaetzlich prueft jeder Test,
dass HEAD und Arbeitsstand des echten Repos unveraendert bleiben. Kein echtes Modell, kein Netz.
Neue Funktionen werden in den Methoden importiert (Gegenprobe).
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402

FAKE = ECHT / "role-split" / "kette" / "testdata" / "opencode_fake.py"
DATUM = "20261027"
HANDOVER = f"docs/projekt_management/handover_{DATUM}_g.md"
SPEC = (
    "# Spec: g\n\n## Ziel\nTest.\n\n## Schreibbereich\n\n"
    "- `src/`\n- `role-split/kette/`\n- `docs/projekt_management/`\n\n"
    "## Testplan\n\n### T1: Erster\n- **Erwartung:** x\n"
)


def _echter_stand() -> tuple[str, str, dict]:
    """HEAD, Status und Pruefsummen der offenen Dateien des echten Repos (Schutz gegen Tests, die dort
    etwas tun – auch gegen weitere Aenderungen an Dateien, die schon offen sind)."""
    def g(*a):
        return subprocess.run(["git", "-C", str(ECHT), *a], capture_output=True, text=True).stdout
    summen = {}
    for eintrag in g("status", "--porcelain", "-z", "--untracked-files=all").split("\0"):
        pfad = ECHT / eintrag[3:] if len(eintrag) > 3 else None
        if pfad and pfad.is_file():
            summen[eintrag[3:]] = hashlib.sha256(pfad.read_bytes()).hexdigest()
    return g("rev-parse", "HEAD").strip(), g("status", "--porcelain"), summen


class Basis(unittest.TestCase):
    pruefen_code = 0
    pruefen_ausgabe = "Ran 1 test in 0.001s\n\nOK"

    def setUp(self):
        self.echt_vorher = _echter_stand()
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.root = root = Path(d.name).resolve()
        self.pm = root / "docs" / "projekt_management"
        self.pm.mkdir(parents=True)
        (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC, encoding="utf-8")
        (self.pm / f"anforderung_{DATUM}_g.md").write_text("# Anforderung g\n\n## Aufgabe\n\n> X\n", encoding="utf-8")
        (self.pm / f"quellen_{DATUM}_g.md").write_text("# Quellen g\n", encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "modul.py").write_text("X = 1\n", encoding="utf-8")
        (root / "role-split" / "kette").mkdir(parents=True)
        (root / "role-split" / "kette" / "kette.py").write_text("# Platzhalter\n", encoding="utf-8")
        (root / ".gitignore").write_text("role-split/results/\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "Spec g")
        for name, wert in (("ROOT", root), ("PM", self.pm)):
            alt = getattr(kette, name)
            setattr(kette, name, wert)
            self.addCleanup(setattr, kette, name, alt)
        self.aufrufe_pruefen = 0

        def pruefen_attrappe(kurztitel, commit=None, timeout=300):
            self.aufrufe_pruefen += 1
            (self.pm / f"pruefung_{DATUM}_{kurztitel}.md").write_text(
                f"# Pruefung {kurztitel}\n\n## unittest  (Exit {self.pruefen_code})\n\n```\n"
                f"{self.pruefen_ausgabe}\n```\n", encoding="utf-8")
            return self.pruefen_code
        alt_pruefen = kette.pruefen
        kette.pruefen = pruefen_attrappe
        self.addCleanup(setattr, kette, "pruefen", alt_pruefen)
        self.argsdatei = root.parent / f"{root.name}_args.json"
        self.addCleanup(lambda: self.argsdatei.unlink(missing_ok=True))
        umgebung = {k: v for k, v in os.environ.items() if not k.startswith("FAKE_")}
        umgebung.update({"KETTE_OPENCODE": str(FAKE), "KETTE_UMSETZUNG_TIMEOUT": "60",
                         "FAKE_ARGS": str(self.argsdatei)})
        umgebung.pop("KETTE_UMSETZUNG_MODEL", None)
        p = mock.patch.dict(os.environ, umgebung, clear=True)
        p.start()
        self.addCleanup(p.stop)
        self.addCleanup(self._echt_unveraendert)

    def _echt_unveraendert(self):
        self.assertEqual(_echter_stand(), self.echt_vorher, "Test hat das echte Repo veraendert!")

    def git(self, *a) -> str:
        return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
                              check=True, capture_output=True, text=True).stdout

    def lauf(self, kurztitel="g", nacharbeit=None, **fake):
        from kette import umsetzung_auto
        os.environ.update({k: str(v) for k, v in fake.items()})
        aus, fehler = io.StringIO(), io.StringIO()
        with redirect_stdout(aus), redirect_stderr(fehler):
            code = umsetzung_auto(kurztitel, nacharbeit)
        return code, aus.getvalue() + fehler.getvalue()

    def protokoll(self) -> str:
        p = self.pm / f"umsetzung_{DATUM}_g.md"
        return p.read_text(encoding="utf-8") if p.exists() else ""

    def gestartet(self) -> bool:
        return self.argsdatei.exists()

    def nacharbeit_vorbereiten(self, auftrag="Bitte A3 korrigieren: Feld X fehlt."):
        (self.root / HANDOVER).write_text("# Handover g\n\nErstumsetzung.\n", encoding="utf-8")
        datei = self.pm / f"nacharbeit_{DATUM}_g_1.md"
        datei.write_text(auftrag + "\n", encoding="utf-8")
        return datei


class VorabTests(Basis):

    def test_t1_vorab_pruefung_kurztitel_ungueltig(self):
        """T1: Vorab-Prüfung – Kurztitel ungültig"""
        code, out = self.lauf("Ungültig-Titel")
        self.assertEqual(code, 2, out)
        self.assertIn("ungültig", out)
        self.assertFalse(self.gestartet())

    def test_t2_vorab_pruefung_kein_spec_commit(self):
        """T2: Vorab-Prüfung – kein Spec-Commit"""
        (self.pm / f"spec_{DATUM}_anders.md").write_text(SPEC, encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "foo")
        code, out = self.lauf("anders")
        self.assertEqual(code, 2, out)
        self.assertIn("Spec", out)
        self.assertFalse(self.gestartet())

    def test_t3_vorab_pruefung_spec_ohne_schreibbereich(self):
        """T3: Vorab-Prüfung – Spec ohne ## Schreibbereich"""
        (self.pm / f"spec_{DATUM}_ohne.md").write_text("# Spec: ohne\n\n## Ziel\nX\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Spec ohne")
        code, out = self.lauf("ohne")
        self.assertEqual(code, 2, out)
        self.assertIn("Schreibbereich", out)
        self.assertIn("ergaenzen", out)
        self.assertFalse(self.gestartet())

    def test_t3_vorab_pruefung_leerer_schreibbereich(self):
        """T3: Vorab-Prüfung – Spec ohne ## Schreibbereich (Abweichung 2: leerer Abschnitt gilt wie fehlend)"""
        (self.pm / f"spec_{DATUM}_leer.md").write_text(
            "# Spec: leer\n\n## Schreibbereich\n\n## Testplan\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "Spec leer")
        code, out = self.lauf("leer")
        self.assertEqual(code, 2, out)
        self.assertIn("ist leer", out)
        self.assertFalse(self.gestartet())

    def test_t4_vorab_pruefung_unrunder_arbeitsstand(self):
        """T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)"""
        (self.root / "src" / "modul.py").write_text("X = 2\n", encoding="utf-8")
        code, out = self.lauf()
        self.assertEqual(code, 2, out)
        self.assertIn("Arbeitsstand", out)
        self.assertIn("src/modul.py", out)
        self.assertFalse(self.gestartet())

    def test_t5_vorab_pruefung_opencode_fehlt(self):
        """T5: Vorab-Prüfung – opencode fehlt"""
        os.environ.pop("KETTE_OPENCODE")
        with mock.patch("kette.shutil.which", return_value=None):
            code, out = self.lauf()
        self.assertEqual(code, 2, out)
        self.assertIn("opencode", out)
        os.environ["KETTE_OPENCODE"] = str(self.root / "gibt_es_nicht.py")
        code, out = self.lauf()
        self.assertEqual(code, 2, out)
        self.assertFalse(self.gestartet())

    def test_t6_vorab_pruefung_modell_kein_llamacpp(self):
        """T6: Vorab-Prüfung – Modell kein llamacpp/"""
        code, out = self.lauf(KETTE_UMSETZUNG_MODEL="gedaechtnis/test-model")
        self.assertEqual(code, 2, out)
        self.assertIn("llamacpp", out)
        self.assertFalse(self.gestartet())


class LaufTests(Basis):

    def test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen(self):
        """T7: Erfolgreicher Lauf, reason: stop, alle Prüfungen grün"""
        code, out = self.lauf(FAKE_EDIT="src/modul.py", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.aufrufe_pruefen, 1)
        zeile = self.protokoll()
        self.assertIn("reason: stop, rot: 0, pruefen: 0, art: erst, Exit: 0", zeile)
        roh = list((self.root / "role-split" / "results").glob(f"umsetzung_auto_{DATUM}_g_*.jsonl"))
        self.assertEqual(len(roh), 1)
        ereignisse = [json.loads(z) for z in roh[0].read_text(encoding="utf-8").splitlines() if z.strip()]
        self.assertGreaterEqual(len(ereignisse), 5)            # ganzer Strom, nicht nur die letzte Zeile
        argv = json.loads(self.argsdatei.read_text(encoding="utf-8"))
        self.assertEqual(argv[:7], ["run", "--format", "json", "--agent", "umsetzung_nacht", "--model",
                                    "llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL"])
        self.assertIn("--dir", argv)
        self.assertNotIn("--continue", argv)
        self.assertNotIn("--message", argv)
        self.assertIn(f"spec_{DATUM}_g.md", argv[-1])          # Prompt = letztes Positionsargument
        self.assertIn("LERNREGELN.md", argv[-1])

    def test_t7_exitcode_von_opencode_wird_ignoriert(self):
        """T7: Erfolgreicher Lauf, reason: stop (opencode-Exit ≠ 0 zählt nicht, nur das JSON)"""
        code, out = self.lauf(FAKE_EXIT="1", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 0, out)
        self.assertIn("reason: stop, rot: 0, pruefen: 0, art: erst, Exit: 0", self.protokoll())
        self.assertIn("  - Tokens: input 130, output 18, reasoning 2", self.protokoll())

    def test_t8_kein_gueltiges_json(self):
        """T8: Lauf ohne reason: stop (Strom ohne gültiges JSON)"""
        code, out = self.lauf(FAKE_KAPUTT="1", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("Keine gültigen JSON-Ereignisse", out)
        self.assertEqual(self.aufrufe_pruefen, 0)

    def test_t8_lauf_ohne_reason_stop(self):
        """T8: Lauf ohne reason: stop"""
        code, out = self.lauf(FAKE_REASON="tool-calls", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("nicht abgeschlossen", out)
        self.assertIn("(d) übersprungen", out)
        self.assertEqual(self.aufrufe_pruefen, 0)
        self.assertIn("reason: tool-calls, rot: –, pruefen: –, art: erst, Exit: 1", self.protokoll())

    def test_t9_timeout(self):
        """T9: Timeout"""
        start = time.monotonic()
        code, out = self.lauf(FAKE_SLEEP="5", KETTE_UMSETZUNG_TIMEOUT="1", FAKE_HANDOVER=HANDOVER)
        dauer = time.monotonic() - start
        self.assertEqual(code, 1, out)
        self.assertIn("Timeout", out)
        self.assertLess(dauer, 4.5, "Prozess wurde nicht nach dem Zeitlimit beendet")
        self.assertIn("reason: timeout", self.protokoll())
        self.assertEqual(self.aufrufe_pruefen, 0)

    def test_t9_timeout_beendet_unterprozesse(self):
        """T9: Timeout (auch Kindprozesse von opencode werden beendet)"""
        piddatei = self.root.parent / f"{self.root.name}_kind.pid"
        self.addCleanup(lambda: piddatei.unlink(missing_ok=True))
        code, out = self.lauf(FAKE_SLEEP="5", KETTE_UMSETZUNG_TIMEOUT="1", FAKE_KIND=str(piddatei))
        self.assertEqual(code, 1, out)
        pid = int(piddatei.read_text(encoding="utf-8"))

        def lebt() -> bool:
            st = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
            return bool(st) and not st.startswith("Z")
        frist = time.monotonic() + 3
        while lebt() and time.monotonic() < frist:
            time.sleep(0.1)
        if lebt():
            os.kill(pid, 9)
            self.fail("Kindprozess von opencode lebt nach dem Timeout weiter")

    def test_t10_selbst_commit(self):
        """T10: Selbst-Commit"""
        head = self.git("rev-parse", "HEAD").strip()
        code, out = self.lauf(FAKE_COMMIT="1", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("Selbst-Commit", out)
        self.assertNotEqual(self.git("rev-parse", "HEAD").strip(), head)    # Commit bleibt, nichts zurueckgesetzt

    def test_t11_datei_ausserhalb_schreibbereich(self):
        """T11: Datei außerhalb Schreibbereich"""
        code, out = self.lauf(FAKE_EDIT="anderes/datei.txt", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("anderes/datei.txt", out)
        self.assertIn("Schreibbereich verletzt", out)
        self.assertTrue((self.root / "anderes" / "datei.txt").exists())       # nichts zurueckgesetzt

    def test_t12_handover_fehlt(self):
        """T12: Handover fehlt"""
        code, out = self.lauf(FAKE_EDIT="src/modul.py")
        self.assertEqual(code, 1, out)
        self.assertIn("Handover", out)

    def test_t15_lebendsignal_werkzeugzeile(self):
        """T15: Lebendsignal – Werkzeugzeile"""
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_ABGELEHNT="1")
        self.assertIn("] bash: python3 -m unittest -v tests/test_fake.py", out)
        self.assertIn("abgelehnt: bash: git commit -m checkpoint", out)
        self.assertIn("Abgelehnt: 1", self.protokoll())

    def test_t15_fehlgeschlagener_befehl_mit_wortlaut(self):
        """T15: Lebendsignal – Werkzeugzeile (fehlgeschlagener, nicht abgelehnter Befehl mit Wortlaut)"""
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_FEHLER="1")
        self.assertIn("fehlgeschlagen: bash: python3 kaputt.py --x", out)
        self.assertNotIn("abgelehnt: bash: python3 kaputt.py", out)
        self.assertIn("  - fehlgeschlagen: bash: python3 kaputt.py --x", self.protokoll())
        self.assertIn("Fehler: 1, Abgelehnt: 0", self.protokoll())

    def test_t15_herzschlag(self):
        """T15: Lebendsignal – Werkzeugzeile (Herzschlag während einer langen Pause)"""
        with mock.patch.object(kette, "KETTE_HERZSCHLAG_S", 1):
            code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_SLEEP="2.5")
        self.assertEqual(code, 0, out)
        self.assertIn("Lebenszeichen, Lauf läuft seit", out)

    def test_t16_pruefen_rot(self):
        """T16: pruefen rot"""
        self.pruefen_code = 1
        self.pruefen_ausgabe = "Ran 3 tests in 0.01s\n\nFAILED (failures=1, errors=1)"
        code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("rot: 2, pruefen: 1, art: erst, Exit: 1", self.protokoll())

    def test_t18_schreibbereich_ordner_eintrag(self):
        """T18: Schreibbereich – Ordner-Eintrag"""
        code, out = self.lauf(FAKE_EDIT="role-split/kette/kette.py", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 0, out)

    def test_t19_schreibbereich_verbotene_dateien(self):
        """T19: Schreibbereich – Verbotene Dateien"""
        # docs/projekt_management/ liegt im Schreibbereich – die Spec selbst bleibt trotzdem verboten
        code, out = self.lauf(FAKE_EDIT=f"docs/projekt_management/spec_{DATUM}_g.md", FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn(f"docs/projekt_management/spec_{DATUM}_g.md", out)


class NacharbeitTests(Basis):

    def test_t13_nacharbeit_auftrag_aus_datei(self):
        """T13: Nacharbeit – Auftrag aus Datei"""
        auftrag = self.nacharbeit_vorbereiten()
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG="1")
        self.assertEqual(code, 0, out)
        prompt = json.loads(self.argsdatei.read_text(encoding="utf-8"))[-1]
        self.assertIn("Bitte A3 korrigieren: Feld X fehlt.", prompt)
        self.assertIn("„## Nachbesserung 1\"", prompt)
        self.assertIn("\n## Nachbesserung 1\n", (self.root / HANDOVER).read_text(encoding="utf-8"))
        self.assertIn("art: nb1", self.protokoll())

    def test_t13_ohne_neuen_abschnitt_nicht_in_ordnung(self):
        """T13: Nacharbeit – Auftrag aus Datei (Handover ohne neuen Abschnitt → Exit 1)"""
        auftrag = self.nacharbeit_vorbereiten()
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("keinen Abschnitt '## Nachbesserung 1'", out)

    def test_t13_nummer_aus_handover(self):
        """T13: Nacharbeit – Auftrag aus Datei (Nummer n = bestehende Abschnitte im Handover + 1)"""
        auftrag = self.nacharbeit_vorbereiten()
        (self.root / HANDOVER).write_text("# Handover g\n\n## Nachbesserung 1\n\nvon Hand.\n", encoding="utf-8")
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG="2")
        self.assertEqual(code, 0, out)
        prompt = json.loads(self.argsdatei.read_text(encoding="utf-8"))[-1]
        self.assertIn("Das ist Nachbesserung 2.", prompt)
        self.assertIn("art: nb2", self.protokoll())

    def test_t14_nacharbeit_zwei_ohne_fortschritt(self):
        """T14: Nacharbeit – zwei ohne Fortschritt"""
        auftrag = self.nacharbeit_vorbereiten()
        z = "- **2026-10-27 10:00** – Modell: m, Dauer: 1 s, Tools: 1, Fehler: 0, Abgelehnt: 0, Tokens: 1, reason: stop, "
        (self.pm / f"umsetzung_{DATUM}_g.md").write_text(
            "# Protokoll\n\n" + z + "rot: 2, pruefen: 1, art: erst, Exit: 1\n"
            + z + "rot: 2, pruefen: 1, art: nb1, Exit: 1\n"
            + z + "rot: –, pruefen: –, art: nb2, Exit: 1\n", encoding="utf-8")
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 1, out)
        self.assertIn("Übergabe an Hawe", out)
        self.assertFalse(self.gestartet(), "trotz Halt-Regel gestartet")

    def test_t14_gegenfall_fortschritt_hebt_halt_auf(self):
        """T14: Nacharbeit – zwei ohne Fortschritt (Gegenfall: einer mit Fortschritt)"""
        from kette import _halt_noetig
        def z(rot, pr, art):
            return {"rot": rot, "pruefen": pr, "art": art}
        self.assertTrue(_halt_noetig([z("2", "1", "erst"), z("2", "1", "nb1"), z("3", "1", "nb2")]))
        self.assertFalse(_halt_noetig([z("2", "1", "erst"), z("1", "1", "nb1"), z("1", "1", "nb2")]))
        self.assertFalse(_halt_noetig([z("2", "1", "erst"), z("2", "1", "nb1")]))
        self.assertTrue(_halt_noetig([z("2", "1", "erst"), z("0", "2", "nb1"), z("0", "2", "nb2")]))  # pruefen schlechter
        self.assertTrue(_halt_noetig([z("–", "–", "erst"), z("–", "–", "nb1"), z("–", "–", "nb2")]))

    def test_t14_unterzeilen_zaehlen_nicht(self):
        """T14: Nacharbeit – zwei ohne Fortschritt (Unterzeilen mit fremdem Text zählen nicht als Lauf)"""
        from kette import _protokoll
        p = self.pm / f"umsetzung_{DATUM}_g.md"
        p.write_text("# Protokoll\n\n- **2026-10-27 10:00** – Modell: m, reason: stop, rot: 2, pruefen: 1, art: erst, Exit: 1\n"
                     "  - fehlgeschlagen: bash: python3 x.py – AssertionError: rot: 0, pruefen: 0, art: nb1\n",
                     encoding="utf-8")
        self.assertEqual(_protokoll(p), [{"rot": "2", "pruefen": "1", "art": "erst"}])

    def test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen(self):
        """T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen"""
        auftrag = self.nacharbeit_vorbereiten()
        (self.root / "fremd.txt").write_text("x\n", encoding="utf-8")
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 2, out)
        self.assertIn("fremd.txt", out)
        self.assertFalse(self.gestartet())
        (self.root / "fremd.txt").unlink()
        (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC + "\ngeaendert\n", encoding="utf-8")
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 2, out)                                          # Vorgabe offen -> nie erlaubt
        self.assertIn(f"spec_{DATUM}_g.md", out)

    def test_t17_handover_anderes_datum_ist_fremd(self):
        """T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen (Handover mit anderem Datum)"""
        # Schreibbereich ohne docs/projekt_management/, sonst waere der alte Handover ueber den Ordner erlaubt
        (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC.replace("- `docs/projekt_management/`\n", ""), encoding="utf-8")
        self.git("commit", "-qam", "Spec g")
        auftrag = self.nacharbeit_vorbereiten()
        (self.pm / "handover_20261001_g.md").write_text("# alter Handover\n", encoding="utf-8")
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
        self.assertEqual(code, 2, out)
        self.assertIn("handover_20261001_g.md", out)
        self.assertNotIn(f"spec_{DATUM}_g.md", out.split("Nacharbeit:")[-1])
        self.assertFalse(self.gestartet())

    def test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei(self):
        """T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)"""
        auftrag = self.nacharbeit_vorbereiten()
        (self.pm / f"pruefung_{DATUM}_g.md").write_text("# Pruefung\n", encoding="utf-8")
        (self.pm / f"verdict_{DATUM}_g_qwen36-35b.md").write_text("# Verdikt\n", encoding="utf-8")
        (self.root / "role-split" / "results").mkdir(parents=True)
        (self.root / "role-split" / "results" / "alt.jsonl").write_text("{}\n", encoding="utf-8")
        code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG="1")
        self.assertNotEqual(code, 2, out)
        self.assertTrue(self.gestartet())
        self.assertEqual(code, 0, out)


class EinstiegTests(Basis):

    def test_t20_main_gleicher_exit_wie_funktionsaufruf(self):
        """T20: main() – gleicher Exit wie Funktionsaufruf"""
        os.environ.update({"FAKE_HANDOVER": HANDOVER})
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(aus):
            code = kette.main(["umsetzung-auto", "g"])
        self.assertEqual(code, 0, aus.getvalue())
        self.assertIn("art: erst, Exit: 0", self.protokoll())
        # Fehlerfall ueber denselben Weg: ungueltiger Kurztitel -> 2 wie T1
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(kette.main(["umsetzung-auto", "Ungültig-Titel"]), 2)

    def test_t20_attrappe_sperrt_echtes_repo(self):
        """T20 Absicherung (kein main()-Aufruf): Attrappe sperrt das echte Repo und Ziele außerhalb von Temp"""
        r = subprocess.run([sys.executable, str(FAKE), "run", "--dir", str(ECHT), "x"],
                           capture_output=True, text=True, timeout=30,
                           env=dict(os.environ, FAKE_COMMIT="1", FAKE_EDIT="sperrtest.txt"))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("Sperre", r.stderr)
        self.assertFalse((ECHT / "sperrtest.txt").exists())
        # Ausbruch per ../ – der "Temp-Ordner" der Attrappe ist hier ein Unterordner (TMPDIR), damit selbst eine
        # Attrappe ohne Sperre (Gegenprobe mit altem Stand) nur in unserem eigenen Temp-Verzeichnis landet.
        aussen = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, aussen, True)
        arbeit = aussen / "sandkasten" / "arbeit"
        arbeit.mkdir(parents=True)
        r = subprocess.run([sys.executable, str(FAKE), "run", "--dir", str(arbeit), "x"],
                           capture_output=True, text=True, timeout=30,
                           env=dict(os.environ, TMPDIR=str(aussen / "sandkasten"), FAKE_EDIT="../../ausbruch.txt"))
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertFalse((aussen / "ausbruch.txt").exists())


if __name__ == "__main__":
    unittest.main()
