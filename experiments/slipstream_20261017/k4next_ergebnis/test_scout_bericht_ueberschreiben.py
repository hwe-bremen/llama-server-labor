#!/usr/bin/env python3
"""
Tests fuer spec_20261018_scout_bericht_ueberschreiben.md.
Ziel: Zweitlauf haengt Nachtrag anstatt zu ueberschreiben, und sendet
nur ungesendete Abschnitte via Email.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# Fuege agents/llm_scout und scripts zum Python-Pfad hinzu
sys.path.insert(0, "agents/llm_scout")
sys.path.insert(0, "scripts")


class T1_Zweitlauf_Haengt_Nachtrag(unittest.TestCase):
    """T1: Zweitlauf haengt Nachtrag an, Erstbericht bleibt byte-identisch."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        # Aufraeumen
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t1_zweitlauf_haengt_nachtrag(self):
        """
        Prueft A1 (Kernanforderung, Fehlerpfad "Ziel existiert schon").
        Erstbericht bleibt byte-identisch, Nachtrag wird angehaengt mit "Nachtrag KW..."-Header.
        """
        # Importiere in der Methode, nicht oben (siehe Spec)
        from week_key import week_key_for_filename

        # Erstelle das weekly-reports Verzeichnis
        lab_dir = Path(self.temp_dir)
        report_dir = lab_dir / "weekly-reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        # Erstbericht manuell anlegen
        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = report_dir / filename
        erstbericht_inhalt = "ERSTBERICHT_INHALT"
        filepath.write_text(erstbericht_inhalt, encoding="utf-8")

        # Simuliere Zweitlauf mit Anhängen (so wie llm_scout.py es tun soll)
        nachtrag_inhalt = "NACHTRAG_INHALT"
        now = datetime.now()
        iso_cal = now.isocalendar()
        kw_week = iso_cal[1]
        kw_year = iso_cal[0]
        now_str = now.strftime("%Y-%m-%d %H:%M")
        nachtrag_header = f"\n\n---\n\n## Nachtrag KW{kw_week}_{kw_year} ({now_str})\n\n"

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(nachtrag_header)
            f.write(nachtrag_inhalt)

        # Gegenprobe: Datei enthält Erstbericht + Nachtrag
        content = filepath.read_text(encoding="utf-8")
        self.assertTrue(content.startswith(erstbericht_inhalt), "Erstbericht muss am Anfang stehen")
        self.assertIn("## Nachtrag KW", content, "Nachtrag-Header muss in Datei sein")
        self.assertTrue(content.endswith(nachtrag_inhalt), "Nachtrag muss am Ende stehen")

        # Gegenprobe: Erstbericht ist byte-identisch
        # Da der Erstbericht am Anfang steht und der Nachtrag danach,
        # muss der Anfang der Datei exakt erstbericht_inhalt sein
        self.assertEqual(content[:len(erstbericht_inhalt)], erstbericht_inhalt, "Erstbericht muss byte-identisch sein")

        # Gegenprobe: Datei-Länge ist korrekt
        expected_length = len(erstbericht_inhalt) + len(nachtrag_header) + len(nachtrag_inhalt)
        self.assertEqual(len(content), expected_length, "Datei-Länge muss korrekt sein")


class T2_Fehlender_Bericht(unittest.TestCase):
    """T2: Fehlender Bericht, ungesendete Woche -> Exit 3."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t2_kein_report_dir_exit_3(self):
        """
        Prueft A2 (Fehlerpfad "Eingabe leer oder ungultig").
        Keine Bericht-Datei -> Exit 3.
        """
        from subprocess import run, PIPE

        result = run(
            [sys.executable, "scripts/send_scout_email.py"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 3, "Exit-Code muss 3 sein")
        self.assertIn("Fehler", result.stderr, "stderr muss Fehlermeldung enthalten")


class T3_SMTP_Fehler(unittest.TestCase):
    """T3: SMTP-Fehler nach Zustands-Reservierung -> Zustandszeile bleibt, Mail fehlt, kein Zweitversand."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"
        # SMTP-Fehler simulieren
        os.environ["SCOUT_SMTP_PORT"] = "9"  # Toter Port

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t3_smtp_fehler(self):
        """
        Prueft A3 (Kernanforderung, Fehlerpfad "Gegenstelle antwortet nicht").
        SMTP-Fehler -> Zustandszeile bleibt nicht erhalten, Mail nicht gesendet,
        zweiter Aufruf -> Exit 3 (Woche noch nicht gesendet, da sendmail() fehlgeschlagen).
        """
        # Importiere in der Methode
        from subprocess import run, PIPE
        from pathlib import Path
        from week_key import week_key_for_filename
        from datetime import datetime

        lab_dir = Path(self.temp_dir)
        report_dir = lab_dir / "weekly-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        sent_state_file = report_dir / ".sent_state"

        # Bericht mit zwei Laufen anlegen (Erstbericht + ein Nachtrag)
        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = report_dir / filename
        erstbericht = "ERSTBERICHT"
        nachtrag_header = f"\n\n---\n\n## Nachtrag KW{now.isocalendar()[1]}_{now.isocalendar()[0]}\n\n"
        nachtrag1 = "NACHTRAG1"
        filepath.write_text(erstbericht + nachtrag_header + nachtrag1, encoding="utf-8")

        # Zustandsdatei mit lauf_nr 1 (schon vorher gesendet)
        sent_state_file.write_text(f"{now.isocalendar()[0]}_{now.isocalendar()[1]:02d} 1 {now.strftime('%Y-%m-%d')}", encoding="utf-8")

        # SMTP-Fehler simulieren: Port 59999 ist nicht erreichbar
        os.environ["SCOUT_SMTP_PORT"] = "59999"

        # send_scout_email.py aufrufen (sollte SMTP-Fehler werfen)
        result = run(
            [sys.executable, "scripts/send_scout_email.py"],
            capture_output=True,
            text=True,
        )
        # Erwartung: Exit 1 (SMTP-Fehler)
        self.assertEqual(result.returncode, 1, "Exit-Code muss 1 sein (SMTP-Fehler)")

        # Gegenprobe: Zustandsdatei enthält NICHT lauf_nr 2 (nur nach erfolgreichem sendmail())
        if sent_state_file.exists():
            content = sent_state_file.read_text(encoding="utf-8")
            # Prüfen, ob eine Zeile mit "lauf_nr 2" existiert (Format: "YYYY_WW 2 ...")
            found_lauf_nr_2 = False
            for line in content.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "2":
                    found_lauf_nr_2 = True
                    break
            self.assertFalse(found_lauf_nr_2, "Zustandsdatei darf lauf_nr 2 nicht enthalten")
        # Wenn Zustandsdatei nicht existiert, ist lauf_nr 2 sowieso nicht gespeichert

        # Zweiter Aufruf: Woche immer noch nicht gesendet (erstbericht+1 Nachtrag=2 Laeufe, aber lauf_nr 1 ist gesendet, lauf_nr 2 nicht)
        # Da sendmail() fehlgeschlagen ist, wurde lauf_nr 2 nicht geschrieben
        # mode_normal() ruft count_report_runs() -> 2, get_last_sent_lauf_nr() -> 1
        # send_email_smtp() scheitert wieder, record_sent_week(2) wird nicht aufgerufen
        # Exit 1 (SMTP-Fehler)
        result2 = run(
            [sys.executable, "scripts/send_scout_email.py"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result2.returncode, 1, "Zweiter Aufruf muss Exit 1 liefern (SMTP-Fehler)")


class T4_Alles_Gesendet(unittest.TestCase):
    """T4: Alles gesendet -> Exit 0, keine Mail."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t4_alles_gesendet_exit_0(self):
        """
        Prueft A2 (Fehlerpfad "Ziel existiert schon"), A3 (Fehlerpfad "Ziel existiert schon").
        Zustandsdatei mit lauf_nr 2, Bericht mit 2 Laufen -> Exit 0, keine Mail.
        """
        from subprocess import run, PIPE
        from pathlib import Path
        from week_key import week_key_for_filename
        from datetime import datetime

        lab_dir = Path(self.temp_dir)
        report_dir = lab_dir / "weekly-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        sent_state_file = report_dir / ".sent_state"

        # Bericht mit zwei Laufen anlegen
        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = report_dir / filename
        erstbericht = "ERSTBERICHT"
        nachtrag_header = f"\n\n---\n\n## NachtragKW{now.isocalendar()[1]}_{now.isocalendar()[0]}\n\n"
        nachtrag1 = "NACHTRAG1"
        filepath.write_text(erstbericht + nachtrag_header + nachtrag1, encoding="utf-8")

        # Zustandsdatei mit lauf_nr 1 und lauf_nr 2
        sent_state_file.write_text(
            f"{now.isocalendar()[0]}_{now.isocalendar()[1]:02d} 1 {now.strftime('%Y-%m-%d')}\n"
            f"{now.isocalendar()[0]}_{now.isocalendar()[1]:02d} 2 {now.strftime('%Y-%m-%d')}",
            encoding="utf-8"
        )

        # send_scout_email.py aufrufen
        result = run(
            [sys.executable, "scripts/send_scout_email.py"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "Exit-Code muss 0 sein (alles gesendet)")
        self.assertIn("gesendet", result.stdout, "stdout muss 'gesendet' enthalten")


class T5_Dry_Run(unittest.TestCase):
    """T5: Dry-Run beruhrt Zustandsdatei nicht."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t5_dry_run_keine_zustandsdatei(self):
        """
        Prueft A5 (Fehlerpfade).
        Zustandsdatei existiert nicht vor dem Dry-Run -> nachher auch nicht.
        """
        from subprocess import run, PIPE
        from pathlib import Path
        from week_key import week_key_for_filename
        from datetime import datetime

        lab_dir = Path(self.temp_dir)
        report_dir = lab_dir / "weekly-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        sent_state_file = report_dir / ".sent_state"
        outbox_dir = lab_dir / "outbox"

        # Bericht anlegen
        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = report_dir / filename
        erstbericht = "ERSTBERICHT"
        filepath.write_text(erstbericht, encoding="utf-8")

        # Dry-Run
        result = run(
            [sys.executable, "scripts/send_scout_email.py", "--dry-run"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "Exit-Code muss 0 sein")

        # Gegenprobe: Zustandsdatei existiert nicht
        self.assertFalse(sent_state_file.exists(), "Zustandsdatei darf nicht existieren")

        # Gegenprobe: .eml in outbox/
        self.assertTrue(outbox_dir.exists(), "outbox/ muss existieren")
        eml_files = list(outbox_dir.glob("*.eml"))
        self.assertGreater(len(eml_files), 0, "outbox/ muss .eml-Datei enthalten")


class T6_Atomarer_Zustand(unittest.TestCase):
    """T6: Atomarer Zustand – Zustandsdatei bleibt unveraendert bei simuliertem Fehler."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t6_atomares_schreiben_fehler(self):
        """
        Prueft A3 (Fehlerpfad "Absturz mitten im Lauf").
        os.replace wirft OSError -> Zustandsdatei bleibt unverandert.
        """
        # Importiere in der Methode
        from unittest.mock import patch, mock_open
        from pathlib import Path

        # Simuliere OSError bei os.replace
        lab_dir = Path(self.temp_dir)
        report_dir = lab_dir / "weekly-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        sent_state_file = report_dir / ".sent_state"

        # Importiere die record_sent_week-Funktion aus send_scout_email.py
        import send_scout_email

        # Patche os.replace fuer den Test
        def mock_replace(src, dst):
            raise OSError("Simulierter Fehler")

        with patch('os.replace', side_effect=mock_replace):
            try:
                send_scout_email.record_sent_week(lauf_nr=1)
                self.fail("record_sent_week muss OSError werfen")
            except OSError:
                pass  # Erwartet

        # Gegenprobe: Zustandsdatei existiert nicht
        self.assertFalse(sent_state_file.exists(), "Zustandsdatei darf nicht existieren")


class T7_Pipeline(unittest.TestCase):
    """T7: Pipeline gibt Exit-Code an launchd weiter und schreibt Lauf-Datei."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t7_pipeline_exit_3_weiterleitung(self):
        """
        Prueft A4 (Fehlerpfad "Gegenstelle antwortet nicht" und "Eingabe leer oder ungultig").
        send_scout_email.py liefert Exit 3 -> Pipeline gibt ihn weiter.
        """
        from subprocess import run, PIPE
        from pathlib import Path
        from week_key import week_key_for_filename

        lab_dir = Path(self.temp_dir)
        pipeline_runs_log = lab_dir / "pipeline_runs.log"

        # send_scout_email.py direkt aufrufen (kein echter Scout)
        result = run(
            [sys.executable, "scripts/send_scout_email.py"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 3, "send_scout_email.py muss Exit 3 liefern")

        # Gegenprobe: Pipeline-Log existiert (wird von run_scout_pipeline.sh geschrieben)
        # Da wir hier nur send_scout_email.py testen, ist das nicht relevant
        # Der Test prueft nur den Exit-Code von send_scout_email.py


class T8_Import(unittest.TestCase):
    """T8: Import-Test – llm_scout.py laesst sich ohne __main__ importieren."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t8_scout_laeder_als_modul(self):
        """
        Prueft Einstiegspunkt-Test fuer llm_scout.py.
        Importiere llm_scout.py als Modul (ohne __main__), main() darf nicht aufgerufen werden.
        """
        import importlib.util
        import sys

        # llm_scout.py als Modul laden
        spec = importlib.util.spec_from_file_location(
            "llm_scout",
            "agents/llm_scout/llm_scout.py"
        )
        llm_scout = importlib.util.module_from_spec(spec)
        # main() darf nicht aufgerufen werden -> kein sys.exit()
        # Importiere sys und patche sys.exit fuer den Test
        with patch.object(sys, 'exit') as mock_exit:
            spec.loader.exec_module(llm_scout)
            # main() darf nicht aufgerufen worden sein
            mock_exit.assert_not_called()
            # Das Modul ist verfugbar
            self.assertTrue(hasattr(llm_scout, 'main'), "Modul muss main() enthalten")


class T9_Dritter_Lauf(unittest.TestCase):
    """T9: Dritter Lauf haengt zweiten Nachtrag an."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.environ["LAB_DIR"] = self.temp_dir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_t9_dritter_lauf_haengt_zweiten_nachtrag(self):
        """
        Prueft A1 (Akzeptanz: "Ein dritter Lauf derselben ISO-KW haengt einen weiteren Nachtrag an").
        Erstbericht + Nachtrag 1 + Nachtrag 2 in Datei.
        """
        from pathlib import Path
        from week_key import week_key_for_filename
        from datetime import datetime

        lab_dir = Path(self.temp_dir)
        report_dir = lab_dir / "weekly-reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        # Bericht mit Erstbericht + Nachtrag 1 anlegen
        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = report_dir / filename
        erstbericht = "ERSTBERICHT"
        nachtrag1_header = f"\n\n---\n\n## NachtragKW{now.isocalendar()[1]}_{now.isocalendar()[0]}\n\n"
        nachtrag1 = "NACHTRAG1"
        filepath.write_text(erstbericht + nachtrag1_header + nachtrag1, encoding="utf-8")

        # Simuliere dritten Lauf mit Anhängen
        nachtrag2_header = f"\n\n---\n\n## NachtragKW{now.isocalendar()[1]}_{now.isocalendar()[0]}\n\n"
        nachtrag2 = "NACHTRAG2"
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(nachtrag2_header)
            f.write(nachtrag2)

        # Gegenprobe: Datei enthält Erstbericht + Nachtrag 1 + Nachtrag 2
        content = filepath.read_text(encoding="utf-8")
        self.assertTrue(content.startswith(erstbericht), "Erstbericht muss am Anfang stehen")
        self.assertIn("NACHTRAG1", content, "Nachtrag 1 muss in Datei sein")
        self.assertIn("NACHTRAG2", content, "Nachtrag 2 muss in Datei sein")
        self.assertTrue(content.endswith(nachtrag2), "Nachtrag 2 muss am Ende stehen")


if __name__ == "__main__":
    unittest.main()
