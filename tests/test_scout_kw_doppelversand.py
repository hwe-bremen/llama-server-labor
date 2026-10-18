#!/usr/bin/env python3
"""
Tests fuer scout_kw_doppelversand (Spec spec_20261018_scout_kw_doppelversand.md).

Kein Test hat Außenwirkung:
- LAB_DIR auf temporäres Verzeichnis
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
# Module-Variablen müssen vor dem ersten Import gesetzt werden, da sie
# Modul-global aus os.getenv() gelesen werden.
# ---------------------------------------------------------------------------

# Temporäres LAB_DIR fuer alle Tests
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
        # Frisches temporäres Verzeichnis fuer diesen Test
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

        # get_password() mocken – kein echter Schlüsselbund-Zugriff
        self._patch_get_password = patch.object(
            sme, "get_password", return_value="dummy_password"
        )
        self._mock_get_password = self._patch_get_password.start()

        # smtplib.SMTP mocken – keine echte TCP-Verbindung
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
        """Mockt datetime.now() auf einen bestimmten Wert."""
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
        self._create_report_file()
        self._mock_smtp_instance.sendmail.side_effect = smtplib.SMTPException(
            "Connection refused"
        )
        result = sme.mode_normal()
        self.assertEqual(result, 1)
        self.assertFalse(
            self.sent_state_file.exists(),
            "Zustandsdatei darf nach SMTP-Fehler nicht existieren",
        )
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            1,
            "sendmail() muss genau einmal aufgerufen worden sein",
        )


# =========================================================================
# T2: Fehlendes REPORT_DIR / leerer LAB_DIR -> Exit 3
# =========================================================================
class T2_Fehlendes_REPORT_DIR(TestBase):
    """T2: Fehlendes REPORT_DIR / leerer LAB_DIR -> Exit 3"""

    def test_t2_kein_report_dir_exit_3(self):
        self.assertFalse(self.sent_state_file.exists())
        result = sme.mode_normal()
        self.assertEqual(result, 3, "Muss Exit-Code 3 bei fehlendem Bericht")
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
        wk = self._current_week_key()
        today = datetime.now().strftime("%Y-%m-%d")
        self._write_sent_state(wk, today)
        self._create_report_file()
        result = sme.mode_normal()
        self.assertEqual(result, 0)
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            0,
            "SMTP darf bei bereits gesendeter KW nicht aufgerufen werden",
        )
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
        self._create_report_file()
        result1 = sme.mode_normal()
        self.assertEqual(result1, 0)
        result2 = sme.mode_normal()
        self.assertEqual(result2, 0)
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            1,
            "sendmail() darf insgesamt genau einmal aufgerufen werden",
        )
        content = self.sent_state_file.read_text(encoding="utf-8").strip()
        lines = [l for l in content.splitlines() if l.strip()]
        self.assertEqual(len(lines), 1, "Es muss genau eine Zustandszeile geben")


# =========================================================================
# T5: Dry-Run beruehrt Zustandsdatei nicht
# =========================================================================
class T5_Dry_Run(TestBase):
    """T5: Dry-Run beruehrt Zustandsdatei nicht"""

    def test_t5_dry_run_keine_zustandsdatei(self):
        self._create_report_file()
        self.assertFalse(self.sent_state_file.exists())
        result = sme.mode_dry_run()
        self.assertEqual(result, 0)
        self.assertFalse(
            self.sent_state_file.exists(),
            "Dry-Run darf Zustandsdatei nicht anlegen",
        )
        eml_files = list(self.outbox_dir.glob("*.eml"))
        self.assertGreaterEqual(len(eml_files), 1, "Dry-Run legt .eml in outbox ab")

    def test_t5_dry_run_zustandsdatei_unveraendert(self):
        wk = self._current_week_key()
        today = datetime.now().strftime("%Y-%m-%d")
        self._write_sent_state(wk, today)
        self._create_report_file()
        result = sme.mode_dry_run()
        self.assertEqual(result, 0)
        content = self.sent_state_file.read_text(encoding="utf-8").strip()
        lines = [l for l in content.splitlines() if l.strip()]
        self.assertEqual(len(lines), 1, "Dry-Run darf Zustandsdatei nicht aendern")
        self.assertEqual(
            self._mock_smtp_instance.sendmail.call_count,
            0,
            "SMTP darf bei bereits gesendeter KW nicht aufgerufen werden",
        )


# =========================================================================
# Wiederhergestellt von Claude 18.10.: T6, T7, T8 und der Grenztage-Teil von T10
# gingen beim Neuschreiben der Nachbesserung verloren (kette.py abgleich hat es gemeldet).
# =========================================================================
class T6_Atomarer_Zustand(TestBase):
    """T6: Atomarer Zustand – Zustandsdatei bleibt unveraendert bei simuliertem Fehler"""

    def test_t6_atomares_schreiben_fehler(self):
        self._create_report_file()
        with patch.object(os, "replace", side_effect=OSError("No space left on device")):
            with self.assertRaises(OSError):
                sme.record_sent_week()
        if self.sent_state_file.exists():
            self.assertEqual(self.sent_state_file.read_text(encoding="utf-8").strip(), "")
        self.assertEqual(list(self.report_dir.glob(".sent_state_*.tmp")), [],
                         "Temp-Datei muss nach Fehler aufgeraeumt sein")


class T7_Fehlender_Bericht(TestBase):
    """T7: Fehlender Bericht, ungesendete Woche -> Exit 3"""

    def test_t7_bericht_fehlt_woche_nicht_gesendet(self):
        self.assertFalse(self.sent_state_file.exists())
        self.assertEqual(sme.mode_normal(), 3)
        self.assertEqual(self._mock_smtp_instance.sendmail.call_count, 0)


class T8_Fehlender_Bericht_bereits_gesendet(TestBase):
    """T8: Fehlender Bericht, aber Woche bereits gesendet -> Exit 0"""

    def test_t8_bericht_fehlt_woche_bereits_gesendet(self):
        self._write_sent_state(self._current_week_key(), datetime.now().strftime("%Y-%m-%d"))
        self.assertEqual(sme.mode_normal(), 0)
        self.assertEqual(self._mock_smtp_instance.sendmail.call_count, 0)


class T10_Grenztage(TestBase):
    """T10 (Teil 2): Grenztage selbst suchen; Name des Erzeugers == Name, den der Sucher findet."""

    def test_t10_grenztage_erzeuger_und_sucher(self):
        import datetime as dt_mod
        kandidaten = []
        for year in range(2024, 2033):
            for offset in range(-10, 11):
                d = datetime(year, 1, 1) + dt_mod.timedelta(days=offset)
                if d.isocalendar()[0] != d.year:
                    kandidaten.append(d)
        dez = [d for d in kandidaten if d.month == 12]
        jan = [d for d in kandidaten if d.month == 1]
        self.assertTrue(dez and jan, "Es muss Dezember- und Januar-Grenztage geben")
        for d in (dez[0], jan[0]):
            with self.subTest(datum=d.date()):
                name = week_key_for_filename(d)          # so schreibt llm_scout.py (T10 Teil 1 prueft das)
                self.assertNotIn(f"_{d.year}.md", name, "Grenztag darf nicht das Kalenderjahr tragen")
                (self.report_dir / name).write_text("# x", encoding="utf-8")
                self._mock_datetime_now(d)
                self.assertIsNotNone(sme.find_current_report(), f"Sucher findet {name} nicht")
                self._patch_datetime_now.stop(); self._patch_datetime_now = None
                self._wk_patch.stop(); self._wk_patch = None


# =========================================================================
# T9: Pipeline-E2E mit Ersatzskripten
# =========================================================================
class T9_Pipeline(unittest.TestCase):
    """
    T9: Pipeline-E2E-Test mit temporarem Verzeichnis und Ersatzskripten.
    Scout exit 3 -> Pipeline-Log zeigt EMAIL_EXIT=3.
    Scout exit 2 -> Pipeline-Log zeigt SCOUT_EXIT=2.
    """

    def _make_fake_scout(self, path, exit_code):
        path.write_text(
            f'#!/usr/bin/env python3\nimport sys\nsys.exit({exit_code})\n',
            encoding="utf-8"
        )
        os.chmod(str(path), 0o755)

    def _make_fake_email(self, path, exit_code):
        path.write_text(
            f'#!/usr/bin/env python3\nimport sys\nsys.exit({exit_code})\n',
            encoding="utf-8"
        )
        os.chmod(str(path), 0o755)

    def test_t9_pipeline_scout_exit_3(self):
        """Scout liefert exit 3 -> Pipeline-Log zeigt EMAIL_EXIT=3."""
        tmp_root = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
        (tmp_root / "scripts").mkdir(parents=True)
        (tmp_root / "weekly-reports").mkdir(parents=True)

        # Pipeline in scripts/ – REPO_ROOT wird aus parent von scripts/ abgeleitet
        pipeline_src = _REPO_ROOT / "scripts" / "run_scout_pipeline.sh"
        pipeline_dst = tmp_root / "scripts" / "run_scout_pipeline.sh"
        pipeline_dst.write_text(pipeline_src.read_text(encoding="utf-8"), encoding="utf-8")
        os.chmod(str(pipeline_dst), 0o755)

        # Ersatzskripte
        scout = tmp_root / "agents" / "llm_scout" / "llm_scout.py"
        scout.parent.mkdir(parents=True, exist_ok=True)
        self._make_fake_scout(scout, 3)

        email = tmp_root / "scripts" / "send_scout_email.py"
        self._make_fake_email(email, 0)

        # Venv-Stub
        venv_bin = tmp_root / ".venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        python_stub = venv_bin / "python3"
        python_stub.write_text(
            "#!/bin/bash\nexec python3 \"$@\"\n", encoding="utf-8"
        )
        os.chmod(str(python_stub), 0o755)

        env = os.environ.copy()
        env["LAB_DIR"] = str(tmp_root)
        result = subprocess.run(
            ["bash", str(pipeline_dst)],
            capture_output=True, text=True, env=env
        )
        # Log steht in pipeline_runs.log, nicht auf stderr
        pipeline_log = tmp_root / "pipeline_runs.log"
        self.assertTrue(
            pipeline_log.exists(),
            "pipeline_runs.log muss existieren"
        )
        log_content = pipeline_log.read_text(encoding="utf-8")
        self.assertIn("SCOUT_EXIT=3", log_content,
                       "Log muss SCOUT_EXIT=3 enthalten")
        self.assertIn("EMAIL_EXIT=skipped", log_content,
                       "Log muss EMAIL_EXIT=skipped enthalten bei Scout-Fehler")

    def test_t9_pipeline_email_exit_3(self):
        """Scout ok, send_scout_email.py liefert 3 -> Pipeline exit 3, Log EMAIL_EXIT=3.
        (Nachgetragen von Claude 18.10.: der Fall aus A4 war bisher ungetestet.)"""
        tmp_root = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
        (tmp_root / "scripts").mkdir(parents=True)
        pipeline_dst = tmp_root / "scripts" / "run_scout_pipeline.sh"
        pipeline_dst.write_text((_REPO_ROOT / "scripts" / "run_scout_pipeline.sh").read_text(encoding="utf-8"),
                                encoding="utf-8")
        scout = tmp_root / "agents" / "llm_scout" / "llm_scout.py"
        scout.parent.mkdir(parents=True, exist_ok=True)
        self._make_fake_scout(scout, 0)
        self._make_fake_email(tmp_root / "scripts" / "send_scout_email.py", 3)
        venv_bin = tmp_root / ".venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        (venv_bin / "python3").write_text(f'#!/bin/bash\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
        os.chmod(str(venv_bin / "python3"), 0o755)
        env = os.environ.copy()
        env["LAB_DIR"] = str(tmp_root)
        result = subprocess.run(["bash", str(pipeline_dst)], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 3, result.stderr)
        log_content = (tmp_root / "pipeline_runs.log").read_text(encoding="utf-8")
        self.assertIn("SCOUT_EXIT=0 EMAIL_EXIT=3", log_content)

    def test_t9_pipeline_scout_exit_2(self):
        """Scout liefert exit 2 -> Pipeline-Log zeigt SCOUT_EXIT=2."""
        tmp_root = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
        (tmp_root / "scripts").mkdir(parents=True)
        (tmp_root / "weekly-reports").mkdir(parents=True)

        pipeline_src = _REPO_ROOT / "scripts" / "run_scout_pipeline.sh"
        pipeline_dst = tmp_root / "scripts" / "run_scout_pipeline.sh"
        pipeline_dst.write_text(pipeline_src.read_text(encoding="utf-8"), encoding="utf-8")
        os.chmod(str(pipeline_dst), 0o755)

        scout = tmp_root / "agents" / "llm_scout" / "llm_scout.py"
        scout.parent.mkdir(parents=True, exist_ok=True)
        self._make_fake_scout(scout, 2)

        email = tmp_root / "scripts" / "send_scout_email.py"
        self._make_fake_email(email, 0)

        venv_bin = tmp_root / ".venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        python_stub = venv_bin / "python3"
        python_stub.write_text(
            "#!/bin/bash\nexec python3 \"$@\"\n", encoding="utf-8"
        )
        os.chmod(str(python_stub), 0o755)

        env = os.environ.copy()
        env["LAB_DIR"] = str(tmp_root)
        result = subprocess.run(
            ["bash", str(pipeline_dst)],
            capture_output=True, text=True, env=env
        )
        pipeline_log = tmp_root / "pipeline_runs.log"
        self.assertTrue(
            pipeline_log.exists(),
            "pipeline_runs.log muss existieren"
        )
        log_content = pipeline_log.read_text(encoding="utf-8")
        self.assertIn("SCOUT_EXIT=2", log_content,
                       "Log muss SCOUT_EXIT=2 enthalten")


# =========================================================================
# T10: Quelltext-Pruefung llm_scout.py
# =========================================================================
class T10_Quelltext(unittest.TestCase):
    """T10: llm_scout.py verwendet week_key_for_filename, nicht strftime('%Y')."""

    def test_t10_kein_strftime_year(self):
        src = (_REPO_ROOT / "agents" / "llm_scout" / "llm_scout.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn(
            "strftime('%Y')", src,
            "llm_scout.py darf strftime('%Y') nicht verwenden"
        )
        self.assertIn(
            "week_key_for_filename(", src,
            "llm_scout.py muss week_key_for_filename() verwenden"
        )


# =========================================================================
# T11: llm_scout.py laedt als Skript ohne ImportError
# =========================================================================
class T11_SkriptLoad(unittest.TestCase):
    """T11: llm_scout.py laedt als Skript (keine Import-Fehler)."""

    def test_t11_scout_laedt_als_skript(self):
        scout_path = str(_REPO_ROOT / "agents" / "llm_scout" / "llm_scout.py")
        result = subprocess.run(
            [sys.executable, "-c",
             f"import runpy; runpy.run_path('{scout_path}', run_name='kein_main')"],
            capture_output=True, text=True
        )
        self.assertEqual(
            result.returncode, 0,
            f"llm_scout.py muss als Skript laeden koennen. stderr: {result.stderr}"
        )

if __name__ == "__main__":
    unittest.main()

