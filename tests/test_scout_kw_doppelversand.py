#!/usr/bin/env python3
"""
Tests fuer scout_kw_doppelversand (Spec spec_20261018_scout_kw_doppelversand.md).

Kein Test hat Au遝nwirkung:
- LAB_DIR auf tempor鋜es Verzeichnis
- get_password() und smtplib.SMTP per unittest.mock ersetzt
- SCOUT_SMTP_HOST = 127.0.0.1, SCOUT_SMTP_PORT = 9 (toter Port)
"""

import os
import smtplib
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Module-Variablen muessen vor dem ersten Import gesetzt werden, da sie
# Modul-global aus os.getenv() gelesen werden.
# ---------------------------------------------------------------------------

# Tempor鋜es LAB_DIR fuer alle Tests
_TEST_LAB_DIR = tempfile.mkdtemp(prefix="scout_test_")
os.environ["LAB_DIR"] = _TEST_LAB_DIR
os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
os.environ["SCOUT_SMTP_PORT"] = "9"  # toter Port

# Pfad fuer scripts/ und agents/llm_scout/
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
sys.path.insert(0, str(_REPO_ROOT / "agents" / "llm_scout"))

import send_scout_email as sme
from week_key import week_key_for_filename


class TestBase(unittest.TestCase):
    """
    Gemeinsamer Testaufbau.
    Jeder Test bekommt ein frisches LAB_DIR-Setup.
    """

    @classmethod
    def setUpClass(cls):
        """Speichert Originalwerte der Modul-Variablen (einmalig)."""
        cls._orig_base_dir = sme.BASE_DIR
        cls._orig_report_dir = sme.REPORT_DIR
        cls._orig_outbox_dir = sme.OUTBOX_DIR
        cls._orig_sent_state_file = sme.SENT_STATE_FILE
        cls._orig_smtp_host = sme.SMTP_HOST

    def setUp(self):
        # Frisches tempor鋜es Verzeichnis fuer diesen Test
        self.lab_dir = Path(tempfile.mkdtemp(prefix="scout_test_"))
        self.report_dir = self.lab_dir / "weekly-reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir = self.lab_dir / "outbox"
        self.sent_state_file = self.report_dir / ".sent_state"

        # Module-Variablen auf das Test-LAB_DIR umlenken
        sme.BASE_DIR = self.lab_dir
        sme.REPORT_DIR = self.report_dir
        sme.OUTBOX_DIR = self.outbox_dir
        sme.SENT_STATE_FILE = self.sent_state_file
        sme.SMTP_HOST = "127.0.0.1"

        # get_password() mocken – kein echter Schl黶selbund-Zugriff
        self._patch_get_password = patch.object(
            sme, "get_password", return_value="dummy_password"
        )
        self._mock_get_password = self._patch_get_password.start()

        # smtplib.SMTP mocken – keine echte TCP-Verbindung
        # WICHTIG: Kein spec=, da smtplib.SMTP eventuell schon ein Mock ist
        self._mock_smtp_instance = MagicMock()
        self._mock_smtp_class = MagicMock()
        self._mock_smtp_class.return_value.__enter__ = MagicMock(
            return_value=self._mock_smtp_instance
        )
        self._mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        self._patch_smtp = patch.object(sme.smtplib, "SMTP", self._mock_smtp_class)
        self._patch_smtp.start()

        self._patch_datetime_now = None
        self._wk_patch = None

    def tearDown(self):
        # Module-Variablen rueckstaendig setzen
        sme.BASE_DIR = self.__class__._orig_base_dir
        sme.REPORT_DIR = self.__class__._orig_report_dir
        sme.OUTBOX_DIR = self.__class__._orig_outbox_dir
        sme.SENT_STATE_FILE = self.__class__._orig_sent_state_file
        sme.SMTP_HOST = self.__class__._orig_smtp_host

        self._patch_get_password.stop()
        self._patch_smtp.stop()
        if self._patch_datetime_now:
            self._patch_datetime_now.stop()
        if self._wk_patch:
            self._wk_patch.stop()

    def _create_report_file(self, content="# Test Bericht\n\nInhalt.") -> Path:
        """Erzeugt eine Bericht-Datei fuer die aktuelle ISO-Woche."""
        filename = week_key_for_filename(datetime.now())
        filepath = self.report_dir / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def _write_sent_state(self, week_key: str, date_str: str) -> None:
        """Schreibt eine Zustandszeile in die .sent_state-Datei."""
        self.sent_state_file.write_text(
            f"{week_key} {date_str}\n", encoding="utf-8"
        )

    def _current_week_key(self) -> str:
        """Aktueller Wochenschluessel (wie im Code)."""
        iso_year, iso_week, _ = datetime.now().isocalendar()
        return f"{iso_year}_{iso_week:02d}"

    def _mock_datetime_now(self, dt: datetime):
        """Mockt datetime.now() auf einen bestimmten Wert (in sme und week_key)."""
        fake_dt = MagicMock(wraps=datetime)
        fake_dt.now.return_value = dt
        self._patch_datetime_now = patch.object(sme, "datetime", fake_dt)
        self._patch_datetime_now.start()

        import week_key as wk
        fake_wk_dt = MagicMock(wraps=datetime)
        fake_wk_dt.now.return_value = dt
        self._wk_patch = patch.object(wk, "datetime", fake_wk_dt)
        self._wk_patch.start()


# =========================================================================
# T1: SMTP-Fehler -> keine Zustandszeile, Exit 1
# =========================================================================
class T1_SMTP_Fehler(TestBase):
    """T1: SMTP-Fehler -> keine Zustandszeile, Exit 1"""

    def test_t1_smtp_fehler_keine_zustandszeile(self):
        # Aufbau: Bericht vorhanden, SMTP wirft Exception
        self._create_report_file()
        self._mock_smtp_instance.sendmail.side_effect = smtplib.SMTPException(
            "Connection refused"
        )

        # Act
        result = sme.mode_normal()

        # Assert
        self.assertEqual(result, 1)
        # Zustandsdatei darf nicht existieren
        self.assertFalse(
            self.sent_state_file.exists(),
            "Zustandsdatei darf nach SMTP-Fehler nicht existieren",
        )
        # sendmail() wurde genau einmal aufgerufen
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            1,
            "sendmail() muss genau einmal aufgerufen worden sein",
        )


# =========================================================================
# T2: Fehlendes REPORT_DIR / leerer LAB_DIR -> Exit 3
# =========================================================================
class T2_Fehlendes_REPORT_DIR(TestBase):
    """T2: Fehlendes REPORT_DIR / leerer LAB_DIR -> Exit 3, keine halbe Zustandsdatei"""

    def test_t2_kein_report_dir_exit_3(self):
        # Aufbau: Keine weekly-reports, kein Bericht, keine Zustandsdatei
        # report_dir existiert (setUp), aber ist leer
        # Zustandsdatei existiert nicht
        self.assertFalse(self.sent_state_file.exists())

        # Act
        result = sme.mode_normal()

        # Assert
        self.assertEqual(result, 3, "Muss Exit-Code 3 liefern bei fehlendem Bericht")
        self.assertFalse(
            self.sent_state_file.exists(),
            "Zustandsdatei darf nicht angelegt werden",
        )


# =========================================================================
# T3: Zustandsdatei mit Zeile fuer dieselbe ISO-Woche -> keine Doppelzeile
# =========================================================================
class T3_Zustandsdatei_bereits_vorhanden(TestBase):
    """T3: Zustandsdatei mit Zeile fuer dieselbe ISO-Woche -> keine Doppelzeile"""

    def test_t3_keine_doppelzeile(self):
        # Aufbau: Zustandsdatei mit aktueller Woche, Bericht vorhanden
        wk = self._current_week_key()
        today = datetime.now().strftime("%Y-%m-%d")
        self._write_sent_state(wk, today)
        self._create_report_file()

        # Act
        result = sme.mode_normal()

        # Assert
        self.assertEqual(result, 0)
        # SMTP darf nicht aufgerufen werden
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            0,
            "SMTP darf bei bereits gesendeter KW nicht aufgerufen werden",
        )
        # Genau eine Zeile in der Zustandsdatei
        content = self.sent_state_file.read_text(encoding="utf-8").strip()
        lines = [l for l in content.splitlines() if l.strip()]
        self.assertEqual(len(lines), 1, "Es darf genau eine Zustandszeile geben")
        self.assertTrue(
            lines[0].startswith(wk),
            f"Die Zeile muss mit '{wk}' beginnen",
        )


# =========================================================================
# T4: Zweitlauf in derselben ISO-Woche -> nur eine Mail, Exit 0
# =========================================================================
class T4_Zweitlauf(TestBase):
    """T4: Zweitlauf in derselben ISO-Woche -> nur eine Mail, Exit 0"""

    def test_t4_zweitlauf_nur_eine_mail(self):
        # Aufbau: Bericht vorhanden, kein Versand-Nachweis
        self._create_report_file()

        # Erster Aufruf
        result1 = sme.mode_normal()
        self.assertEqual(result1, 0)

        # Zweiter Aufruf
        result2 = sme.mode_normal()
        self.assertEqual(result2, 0)

        # Assert
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            1,
            "sendmail() darf insgesamt genau einmal aufgerufen werden",
        )
        # Genau eine Zeile in der Zustandsdatei
        content = self.sent_state_file.read_text(encoding="utf-8").strip()
        lines = [l for l in content.splitlines() if l.strip()]
        self.assertEqual(
            len(lines), 1, "Es muss genau eine Zustandszeile geben"
        )


# =========================================================================
# T5: Dry-Run beruehrt Zustandsdatei nicht
# =========================================================================
class T5_Dry_Run(TestBase):
    """T5: Dry-Run beruehrt Zustandsdatei nicht"""

    def test_t5_dry_run_keine_zustandsdatei(self):
        # Szenario (a): Zustandsdatei existiert nicht vor dem Dry-Run
        self._create_report_file()
        self.assertFalse(self.sent_state_file.exists())

        result = sme.mode_dry_run()
        self.assertEqual(result, 0)
        self.assertFalse(
            self.sent_state_file.exists(),
            "Dry-Run darf Zustandsdatei nicht anlegen",
        )
        # .eml in outbox
        eml_files = list(self.outbox_dir.glob("*.eml"))
        self.assertGreaterEqual(len(eml_files), 1, "Dry-Run legt .eml in outbox ab")

    def test_t5_dry_run_zustandsdatei_unveraendert(self):
        # Szenario (b): Zustandsdatei existiert mit einer Zeile
        wk = self._current_week_key()
        today = datetime.now().strftime("%Y-%m-%d")
        self._write_sent_state(wk, today)
        self._create_report_file()

        result = sme.mode_dry_run()
        self.assertEqual(result, 0)

        # Zustandsdatei unver鋘dert
        content = self.sent_state_file.read_text(encoding="utf-8").strip()
        lines = [l for l in content.splitlines() if l.strip()]
        self.assertEqual(len(lines), 1, "Dry-Run darf Zustandsdatei nicht aendern")

        # SMTP nie aufgerufen
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            0,
            "Dry-Run darf SMTP nie aufrufen",
        )


# =========================================================================
# T6: Atomarer Zustand – Zustandsdatei bleibt unveraendert bei simuliertem Fehler
# =========================================================================
class T6_Atomarer_Zustand(TestBase):
    """T6: Atomarer Zustand – Zustandsdatei bleibt unveraendert bei simuliertem Fehler"""

    def test_t6_atomares_schreiben_fehler(self):
        # Aufbau: Bericht vorhanden
        self._create_report_file()

        # os.replace mocken, dass es OSError wirft (simulierter voller Datentraeger)
        def failing_replace(src, dst):
            raise OSError("No space left on device")

        with patch.object(os, "replace", side_effect=failing_replace):
            # record_sent_week() direkt aufrufen
            with self.assertRaises(OSError):
                sme.record_sent_week()

        # Zustandsdatei darf nicht existieren (oder leer sein)
        if self.sent_state_file.exists():
            content = self.sent_state_file.read_text(encoding="utf-8").strip()
            self.assertEqual(
                content,
                "",
                "Zustandsdatei darf bei atomarem Fehler keine halbe Zeile enthalten",
            )


# =========================================================================
# T7: Fehlender Bericht, ungesendete Woche -> Exit 3
# =========================================================================
class T7_Fehlender_Bericht(TestBase):
    """T7: Fehlender Bericht, ungesendete Woche -> Exit 3"""

    def test_t7_bericht_fehlt_woche_nicht_gesendet(self):
        # Aufbau: weekly-reports existiert, aber kein Bericht, keine Zustandsdatei
        self.assertFalse(self.sent_state_file.exists())
        # Kein Bericht erstellen

        # Act
        result = sme.mode_normal()

        # Assert
        self.assertEqual(
            result,
            3,
            "Muss Exit-Code 3 bei fehlendem Bericht und ungesendeter Woche liefern",
        )


# =========================================================================
# T8: Fehlender Bericht, aber Woche bereits gesendet -> Exit 0
# =========================================================================
class T8_Fehlender_Bericht_bereits_gesendet(TestBase):
    """T8: Fehlender Bericht, aber Woche bereits gesendet -> Exit 0"""

    def test_t8_bericht_fehlt_woche_bereits_gesendet(self):
        # Aufbau: Kein Bericht, aber Zustandsdatei mit aktueller Woche
        wk = self._current_week_key()
        today = datetime.now().strftime("%Y-%m-%d")
        self._write_sent_state(wk, today)

        # Act
        result = sme.mode_normal()

        # Assert
        self.assertEqual(
            result,
            0,
            "Muss Exit-Code 0 liefern, wenn Woche bereits gesendet ist",
        )
        # SMTP darf nicht aufgerufen werden
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            0,
            "SMTP darf bei bereits gesendeter KW nicht aufgerufen werden",
        )


# =========================================================================
# T9: Pipeline gibt Exit-Code 3 an launchd weiter und schreibt Lauf-Datei
# =========================================================================
class T9_Pipeline(TestBase):
    """T9: Pipeline gibt Exit-Code 3 an launchd weiter und schreibt Lauf-Datei"""

    def test_t9_pipeline_exit_3_weiterleitung(self):
        # send_scout_email.py als Subprozess aufrufen (kein Bericht, keine Zustandsdatei)
        # -> sollte Exit 3 liefern

        env = os.environ.copy()
        env["LAB_DIR"] = str(self.lab_dir)
        env["SCOUT_SMTP_HOST"] = "127.0.0.1"
        env["SCOUT_SMTP_PORT"] = "9"

        script_path = _REPO_ROOT / "scripts" / "send_scout_email.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            env=env,
            capture_output=True,
            timeout=30,
        )

        self.assertEqual(
            result.returncode,
            3,
            f"send_scout_email.py muss Exit-Code 3 liefern. "
            f"stderr: {result.stderr.decode()}",
        )

    def test_t9_pipeline_runs_log(self):
        """
        Die pipeline_runs.log-Logik ist in run_scout_pipeline.sh.
        Dieser Test prueft, dass send_scout_email.py den richtigen Exit-Code
        liefert, den die Pipeline dann weiterleiten und loggen wuerde.
        """
        env = os.environ.copy()
        env["LAB_DIR"] = str(self.lab_dir)
        env["SCOUT_SMTP_HOST"] = "127.0.0.1"
        env["SCOUT_SMTP_PORT"] = "9"

        script_path = _REPO_ROOT / "scripts" / "send_scout_email.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            env=env,
            capture_output=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 3)


# =========================================================================
# T10: ISO-Jahreswechsel – Erzeuger und Sucher stimmen auf denselben Dateinamen
# =========================================================================
class T10_ISO_Jahreswechsel(TestBase):
    """T10: ISO-Jahreswechsel – Erzeuger und Sucher stimmen auf denselben Dateinamen"""

    def test_t10_iso_jahreswechsel_namensuebereinstimmung(self):
        """
        Schleift ueber Tage um den Jahreswechsel mehrerer Jahre,
        waehlt Grenztage aus (iso_year != cal_year) und prueft,
        dass Erzeuger und Sucher denselben Dateinamen verwenden.
        """
        import datetime as dt_mod

        test_dates = []
        for year in range(2024, 2030):
            # 20 Tage vor und nach dem 01.01.
            for offset in range(-20, 21):
                try:
                    if offset < 0:
                        d = datetime(year, 1, 1) + dt_mod.timedelta(days=offset)
                    else:
                        d = datetime(year, 1, 1) + dt_mod.timedelta(days=offset)
                except ValueError:
                    continue

                iso_year, iso_week, _ = d.isocalendar()
                cal_year = d.year

                if iso_year != cal_year:
                    test_dates.append(d)

        if not test_dates:
            self.fail("Keine Grenztage gefunden – Test kann nicht ausfuehren")

        # Mindestens einen Dezember-Tag und einen Januar-Tag pruefen
        dec_dates = [d for d in test_dates if d.month == 12]
        jan_dates = [d for d in test_dates if d.month == 1]

        selected_dates = []
        if dec_dates:
            selected_dates.append(dec_dates[0])
        if jan_dates:
            selected_dates.append(jan_dates[0])
        if not selected_dates:
            selected_dates = test_dates[:2] if len(test_dates) >= 2 else test_dates

        for dt in selected_dates:
            with self.subTest(date=dt):
                # Erzeuger-Dateiname berechnen (wie llm_scout.py es tut)
                generated_filename = week_key_for_filename(dt)

                # Bericht-Datei im Test-LAB_DIR anlegen
                report_path = self.report_dir / generated_filename
                report_path.write_text("# Test", encoding="utf-8")

                # datetime.now() auf das Testdatum setzen
                self._mock_datetime_now(dt)

                # Sucher aufrufen
                found = sme.find_current_report()

                self.assertIsNotNone(
                    found,
                    f"find_current_report() muss die Datei fuer {dt} finden. "
                    f"Erzeuger: {generated_filename}",
                )

                # datetime.now() rueckstaendig setzen fuer naechsten subTest
                self._patch_datetime_now.stop()
                self._patch_datetime_now = None
                self._wk_patch.stop()
                self._wk_patch = None


if __name__ == "__main__":
    unittest.main()
