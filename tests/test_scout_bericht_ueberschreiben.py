#!/usr/bin/env python3
"""
Tests fuer scout_bericht_ueberschreiben.

Kein Test hat Außenwirkung:
- LAB_DIR immer temporär
- get_password() und smtplib.SMTP per Mock ersetzt
- SMTP auf 127.0.0.1 / toter Port
- llm_scout.py nie als __main__ ausgeführt
"""

import os
import smtplib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime
from pathlib import Path


class TestA1Zweitlauf(unittest.TestCase):
    """T1, T9: Anhäng-Logik statt Überschreiben."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.report_dir = Path(self.tmpdir) / "weekly-reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self._orig_lab_dir = os.environ.get("LAB_DIR")
        os.environ["LAB_DIR"] = self.tmpdir

    def tearDown(self):
        if self._orig_lab_dir is not None:
            os.environ["LAB_DIR"] = self._orig_lab_dir
        else:
            os.environ.pop("LAB_DIR", None)

    def test_t1_zweitlauf_haengt_nachtrag_an_erstbericht_bleibt_byte_identisch(self):
        """T1: Zweitlauf hängt Nachtrag an, Erstbericht bleibt byte-identisch."""
        # Import in der Methode (Spec: "in der Methode importiert")
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents" / "llm_scout"))
        from llm_scout import save_report, week_key_for_filename

        now = datetime.now()
        filename = week_key_for_filename(now)
        filepath = self.report_dir / filename

        # Erstlauf simulieren: Datei mit festem Inhalt
        erstbericht = "ERSTBERICHT_INHALT"
        filepath.write_text(erstbericht, encoding="utf-8")

        # Zweitlauf: save_report soll anhängen
        nachtrag = "NACHTRAG_INHALT"
        save_report(filepath, nachtrag, now)

        content = filepath.read_text(encoding="utf-8")

        # Erstbericht byte-identisch am Anfang
        self.assertTrue(content.startswith(erstbericht),
                        f"Erstbericht nicht am Anfang: {content!r}")

        # Nachtrag-Header vorhanden
        self.assertIn("## Nachtrag KW", content,
                      f"Nachtrag-Header fehlt: {content!r}")

        # Nachtrag-Inhalt am Ende
        self.assertTrue(content.endswith(nachtrag),
                        f"Nachtrag nicht am Ende: {content!r}")

    def test_t9_dritter_lauf_haengt_zweiten_nachtrag_an(self):
        """T9: Dritter Lauf hängt zweiten Nachtrag an."""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents" / "llm_scout"))
        from llm_scout import save_report, week_key_for_filename

        now = datetime.now()
        iso_year, iso_week, _ = now.isocalendar()
        date_str = now.strftime("%Y-%m-%d %H:%M")
        filename = week_key_for_filename(now)
        filepath = self.report_dir / filename

        # Vorheriger Zustand: Erstbericht + Nachtrag 1
        erstbericht = "ERSTBERICHT_INHALT"
        nachtrag1 = "NACHTRAG1_INHALT"
        existing = (
            erstbericht
            + f"\n\n---\n\n"
            + f"## Nachtrag KW{iso_week}_{iso_year} ({date_str})\n\n"
            + nachtrag1
        )
        filepath.write_text(existing, encoding="utf-8")

        # Dritter Lauf
        nachtrag2 = "NACHTRAG2_INHALT"
        save_report(filepath, nachtrag2, now)

        content = filepath.read_text(encoding="utf-8")

        # Erstbericht byte-identisch
        self.assertTrue(content.startswith(erstbericht))
        # Nachtrag 1 byte-identisch
        self.assertIn(nachtrag1, content)
        # Zweiter Nachtrag-Header
        self.assertEqual(content.count("## Nachtrag KW"), 2,
                         "Es muss genau zwei Nachtrag-Header geben")
        # Nachtrag 2 am Ende
        self.assertTrue(content.endswith(nachtrag2))


class TestA2VersandNachweis(unittest.TestCase):
    """T2, T4: Versand-Nachweis pro Lauf."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.report_dir = Path(self.tmpdir) / "weekly-reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir = Path(self.tmpdir) / "outbox"
        self._orig_lab_dir = os.environ.get("LAB_DIR")
        os.environ["LAB_DIR"] = self.tmpdir
        self._orig_smtp_host = os.environ.get("SCOUT_SMTP_HOST")
        self._orig_smtp_port = os.environ.get("SCOUT_SMTP_PORT")
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        if self._orig_lab_dir is not None:
            os.environ["LAB_DIR"] = self._orig_lab_dir
        else:
            os.environ.pop("LAB_DIR", None)
        if self._orig_smtp_host is not None:
            os.environ["SCOUT_SMTP_HOST"] = self._orig_smtp_host
        else:
            os.environ.pop("SCOUT_SMTP_HOST", None)
        if self._orig_smtp_port is not None:
            os.environ["SCOUT_SMTP_PORT"] = self._orig_smtp_port
        else:
            os.environ.pop("SCOUT_SMTP_PORT", None)

    def test_t2_fehlender_bericht_ungesendete_woche_exit_3(self):
        """T2: Fehlender Bericht, ungesendete Woche → Exit 3."""
        # Kein Bericht, keine Zustandsdatei
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "send_scout_email.py")],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 3,
                         f"Erwartet Exit 3, bekam {result.returncode}\nstderr: {result.stderr}")

        # Zustandsdatei existiert nicht
        sent_state = self.report_dir / ".sent_state"
        self.assertFalse(sent_state.exists(),
                         "Zustandsdatei darf nicht angelegt werden")

    def test_t4_alles_gesendet_exit_0_keine_mail(self):
        """T4: Alles gesendet → Exit 0, keine Mail."""
        now = datetime.now()
        iso_year, iso_week, _ = now.isocalendar()
        date_str = now.strftime("%Y-%m-%d %H:%M")

        # Bericht mit zwei Läufen (Erstbericht + ein Nachtrag)
        filename = f"llm_scout_kw{iso_week}_{iso_year}.md"
        report_path = self.report_dir / filename
        report_path.write_text(
            "ERSTBERICHT"
            + f"\n\n---\n\n"
            + f"## Nachtrag KW{iso_week}_{iso_year} ({date_str})\n\n"
            + "NACHTRAG1",
            encoding="utf-8",
        )

        # Zustandsdatei: lauf_nr 1 und 2 schon gesendet
        sent_state = self.report_dir / ".sent_state"
        sent_state.write_text(
            f"{iso_year}_{iso_week:02d} 1 2026-10-10\n"
            f"{iso_year}_{iso_week:02d} 2 2026-10-11\n",
            encoding="utf-8",
        )

        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "send_scout_email.py")],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 0,
                         f"Erwartet Exit 0, bekam {result.returncode}\nstderr: {result.stderr}")

        # Zustandsdatei hat genau zwei Zeilen
        lines = [l for l in sent_state.read_text(encoding="utf-8").strip().splitlines() if l.strip()]
        self.assertEqual(len(lines), 2,
                         f"Zustandsdatei soll 2 Zeilen haben, hat {len(lines)}")


class TestA3CrashSafety(unittest.TestCase):
    """T3, T6: Merker erst nach Versand (Nachbesserung 19.10.), atomares Schreiben."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.report_dir = Path(self.tmpdir) / "weekly-reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir = Path(self.tmpdir) / "outbox"
        self._orig_lab_dir = os.environ.get("LAB_DIR")
        os.environ["LAB_DIR"] = self.tmpdir
        self._orig_smtp_host = os.environ.get("SCOUT_SMTP_HOST")
        self._orig_smtp_port = os.environ.get("SCOUT_SMTP_PORT")
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        if self._orig_lab_dir is not None:
            os.environ["LAB_DIR"] = self._orig_lab_dir
        else:
            os.environ.pop("LAB_DIR", None)
        if self._orig_smtp_host is not None:
            os.environ["SCOUT_SMTP_HOST"] = self._orig_smtp_host
        else:
            os.environ.pop("SCOUT_SMTP_HOST", None)
        if self._orig_smtp_port is not None:
            os.environ["SCOUT_SMTP_PORT"] = self._orig_smtp_port
        else:
            os.environ.pop("SCOUT_SMTP_PORT", None)

    def test_t3_smtp_fehler_kein_merker_naechster_lauf_sendet_nach(self):
        """T3: SMTP-Fehler → kein Merker, Exit 1; der nächste Lauf sendet nach (Nachbesserung 19.10., D1)."""
        import unittest.mock as mock
        _bericht(self.report_dir, "ERSTBERICHT", "NACHTRAG1")
        sent_state = self.report_dir / ".sent_state"
        sent_state.write_text(f"{_key()} 1 2026-10-10\n", encoding="utf-8")
        mod = _lade_send_modul()

        smtp, gesendet = _smtp_mock(fehler_beim_ersten=True)
        with mock.patch('smtplib.SMTP', return_value=smtp), \
                mock.patch.object(mod, 'get_password', return_value='testpass'):
            exit1 = mod.mode_normal()
            zeilen_nach_fehler = _zeilen(sent_state)
            exit2 = mod.mode_normal()

        self.assertEqual(exit1, 1, "Erster Lauf (SMTP-Fehler) muss Exit 1 liefern")
        self.assertEqual(zeilen_nach_fehler, [f"{_key()} 1 2026-10-10"],
                         "Nach SMTP-Fehler darf kein neuer Merker stehen")
        self.assertEqual(exit2, 0, "Zweiter Lauf muss nachsenden und Exit 0 liefern")
        self.assertEqual(len(gesendet), 2, "sendmail: 1 Fehlversuch + 1 Nachsendung")
        self.assertEqual(sorted(mod._sent_lauf_nrs(sent_state.read_text(encoding="utf-8"), _key())), [1, 2])

    def test_t6_atomarer_zustand_os_replace_fehler(self):
        """T6: Atomarer Zustand – Zustandsdatei bleibt unverändert bei simuliertem os.replace-Fehler."""
        import unittest.mock as mock

        # Zustandsdatei anlegen mit bestehendem Inhalt
        now = datetime.now()
        iso_year, iso_week, _ = now.isocalendar()
        sent_state = self.report_dir / ".sent_state"
        original_content = f"{iso_year}_{iso_week:02d} 1 2026-10-10\n"
        sent_state.write_text(original_content, encoding="utf-8")

        # Module importieren
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        if "send_scout_email" in sys.modules:
            del sys.modules["send_scout_email"]
        import send_scout_email

        # os.replace wirft OSError (voller Datenträger)
        with mock.patch("os.replace", side_effect=OSError("No space left on device")):
            with self.assertRaises(OSError):
                send_scout_email.record_sent_week(lauf_nr=2)

        # Zustandsdatei bleibt unverändert
        self.assertEqual(sent_state.read_text(encoding="utf-8"), original_content,
                         "Zustandsdatei muss unverändert bleiben bei os.replace-Fehler")


class TestA5DryRun(unittest.TestCase):
    """T5: Dry-Run berührt Zustandsdatei nicht."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.report_dir = Path(self.tmpdir) / "weekly-reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.outbox_dir = Path(self.tmpdir) / "outbox"
        self._orig_lab_dir = os.environ.get("LAB_DIR")
        os.environ["LAB_DIR"] = self.tmpdir
        self._orig_smtp_host = os.environ.get("SCOUT_SMTP_HOST")
        self._orig_smtp_port = os.environ.get("SCOUT_SMTP_PORT")
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        if self._orig_lab_dir is not None:
            os.environ["LAB_DIR"] = self._orig_lab_dir
        else:
            os.environ.pop("LAB_DIR", None)
        if self._orig_smtp_host is not None:
            os.environ["SCOUT_SMTP_HOST"] = self._orig_smtp_host
        else:
            os.environ.pop("SCOUT_SMTP_HOST", None)
        if self._orig_smtp_port is not None:
            os.environ["SCOUT_SMTP_PORT"] = self._orig_smtp_port
        else:
            os.environ.pop("SCOUT_SMTP_PORT", None)

    def test_t5_dry_run_beruehrt_zustandsdatei_nicht(self):
        """T5: Dry-Run berührt Zustandsdatei nicht."""
        now = datetime.now()
        iso_year, iso_week, _ = now.isocalendar()
        date_str = now.strftime("%Y-%m-%d %H:%M")

        # Bericht mit Nachtrag
        filename = f"llm_scout_kw{iso_week}_{iso_year}.md"
        report_path = self.report_dir / filename
        report_path.write_text(
            "ERSTBERICHT"
            + f"\n\n---\n\n"
            + f"## Nachtrag KW{iso_week}_{iso_year} ({date_str})\n\n"
            + "NACHTRAG1",
            encoding="utf-8",
        )

        # Szenario (a): Zustandsdatei existiert nicht
        sent_state = self.report_dir / ".sent_state"
        self.assertFalse(sent_state.exists())

        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "send_scout_email.py"), "--dry-run"],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        self.assertEqual(result.returncode, 0,
                         f"Erwartet Exit 0, bekam {result.returncode}\nstderr: {result.stderr}")

        # Zustandsdatei existiert nach wie vor nicht
        self.assertFalse(sent_state.exists(),
                         "Dry-Run darf keine Zustandsdatei anlegen")

        # .eml in Outbox
        eml_files = list(self.outbox_dir.glob("*.eml"))
        self.assertTrue(len(eml_files) > 0,
                        "Dry-Run soll .eml in outbox/ ablegen")

        # Szenario (b): Zustandsdatei existiert mit zwei Zeilen
        sent_state.write_text(
            f"{iso_year}_{iso_week:02d} 1 2026-10-10\n"
            f"{iso_year}_{iso_week:02d} 2 2026-10-11\n",
            encoding="utf-8",
        )

        result2 = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "send_scout_email.py"), "--dry-run"],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
        )
        self.assertEqual(result2.returncode, 0,
                         f"Erwartet Exit 0, bekam {result2.returncode}\nstderr: {result2.stderr}")

        # Zustandsdatei unverändert
        lines = [l for l in sent_state.read_text(encoding="utf-8").strip().splitlines() if l.strip()]
        self.assertEqual(len(lines), 2,
                         "Dry-Run darf Zustandsdatei nicht verändern")


class TestA4Pipeline(unittest.TestCase):
    """T7: Pipeline gibt Exit-Code weiter."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.report_dir = Path(self.tmpdir) / "weekly-reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self._orig_lab_dir = os.environ.get("LAB_DIR")
        os.environ["LAB_DIR"] = self.tmpdir
        self._orig_smtp_host = os.environ.get("SCOUT_SMTP_HOST")
        self._orig_smtp_port = os.environ.get("SCOUT_SMTP_PORT")
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        if self._orig_lab_dir is not None:
            os.environ["LAB_DIR"] = self._orig_lab_dir
        else:
            os.environ.pop("LAB_DIR", None)
        if self._orig_smtp_host is not None:
            os.environ["SCOUT_SMTP_HOST"] = self._orig_smtp_host
        else:
            os.environ.pop("SCOUT_SMTP_HOST", None)
        if self._orig_smtp_port is not None:
            os.environ["SCOUT_SMTP_PORT"] = self._orig_smtp_port
        else:
            os.environ.pop("SCOUT_SMTP_PORT", None)

    def _fake_repo(self, scout_exit: int, mail_exit: int) -> Path:
        """Wegwerf-Repo mit dem ECHTEN Pipeline-Skript und Platzhaltern fuer Scout und Versand."""
        import shutil
        repo_root = Path(__file__).resolve().parent.parent
        fake = Path(tempfile.mkdtemp())
        (fake / "scripts").mkdir()
        (fake / "agents" / "llm_scout").mkdir(parents=True)
        (fake / ".venv" / "bin").mkdir(parents=True)
        shutil.copy(repo_root / "scripts" / "run_scout_pipeline.sh", fake / "scripts")
        py = fake / ".venv" / "bin" / "python3"
        py.write_text(f"#!/bin/sh\nexec {sys.executable} \"$@\"\n")
        py.chmod(0o755)
        calls = fake / "calls.log"
        (fake / "agents" / "llm_scout" / "llm_scout.py").write_text(
            f"import sys\nopen({str(calls)!r}, 'a').write('scout\\n')\nsys.exit({scout_exit})\n")
        (fake / "scripts" / "send_scout_email.py").write_text(
            f"import sys\nopen({str(calls)!r}, 'a').write('mail ' + ' '.join(sys.argv[1:]) + '\\n')\n"
            f"sys.exit(0 if '--fail-mail' in sys.argv else {mail_exit})\n")
        return fake

    def _run(self, fake: Path, *args: str):
        env = os.environ.copy()
        env["LAB_DIR"] = self.tmpdir
        return subprocess.run(["bash", str(fake / "scripts" / "run_scout_pipeline.sh"), *args],
                              capture_output=True, text=True, env=env, timeout=60)

    def test_t7_pipeline_gibt_exit_code_weiter_und_schreibt_lauf_datei(self):
        """T7: Pipeline gibt Exit-Code an launchd weiter und schreibt Lauf-Datei (echter Pipeline-Lauf, Platzhalter)."""
        log = Path(self.tmpdir) / "pipeline_runs.log"

        # (a) Scout ok, Versand Exit 3 -> Pipeline Exit 3, Lauf-Datei EMAIL_EXIT=3
        fake = self._fake_repo(scout_exit=0, mail_exit=3)
        r = self._run(fake)
        self.assertEqual(r.returncode, 3, r.stderr)
        self.assertIn("SCOUT_EXIT=0 EMAIL_EXIT=3", log.read_text())

        # (b) Scout Exit 2 -> Fehler-Mail angestossen, Pipeline Exit 2, Lauf-Datei EMAIL_EXIT=skipped
        fake = self._fake_repo(scout_exit=2, mail_exit=0)
        r = self._run(fake)
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("SCOUT_EXIT=2 EMAIL_EXIT=skipped", log.read_text())
        self.assertIn("mail --fail-mail --exit-code 2", (fake / "calls.log").read_text())

        # (c) Trockenlauf: keine Lauf-Datei-Zeile, Versand nur mit --dry-run
        zeilen_vorher = log.read_text().count("\n")
        fake = self._fake_repo(scout_exit=0, mail_exit=0)
        r = self._run(fake, "--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(log.read_text().count("\n"), zeilen_vorher)
        self.assertIn("mail --dry-run", (fake / "calls.log").read_text())


class TestNachbesserung(unittest.TestCase):
    """T10–T13: Nachbesserung 19.10. (Erfolgsfall, Nachtrag-Mail, Alt-Zeilen, Zaehlung)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.report_dir = Path(self.tmpdir) / "weekly-reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self._env = {k: os.environ.get(k) for k in ("LAB_DIR", "SCOUT_SMTP_HOST", "SCOUT_SMTP_PORT")}
        os.environ["LAB_DIR"] = self.tmpdir
        os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"
        os.environ["SCOUT_SMTP_PORT"] = "9"

    def tearDown(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _lauf(self, mod, smtp):
        import unittest.mock as mock
        with mock.patch('smtplib.SMTP', return_value=smtp), \
                mock.patch.object(mod, 'get_password', return_value='testpass'):
            return mod.mode_normal()

    def test_t10_erfolgreicher_versand_setzt_merker_genau_einmal(self):
        """T10: Erfolgsfall Erstbericht: Mail einmal, Merker lauf_nr 1, zweiter Lauf sendet nicht."""
        _bericht(self.report_dir, "ERSTBERICHT")
        mod = _lade_send_modul()
        smtp, gesendet = _smtp_mock()
        self.assertEqual(self._lauf(mod, smtp), 0)
        self.assertEqual(self._lauf(mod, smtp), 0)
        self.assertEqual(len(gesendet), 1, "genau eine Mail")
        self.assertIn("ERSTBERICHT", _mailtext(gesendet[0]))
        self.assertEqual(_zeilen(self.report_dir / ".sent_state")[0].split()[:2], [_key(), "1"])

    def test_t11_nachtrag_mail_nur_mit_neuem_und_eigenem_betreff(self):
        """T11: Nachtrag-Mail enthaelt nur den Nachtrag, nicht den gesendeten Erstbericht; Betreff „Nachtrag"."""
        _bericht(self.report_dir, "ERSTBERICHT_TEXT", "NACHTRAG1_TEXT")
        (self.report_dir / ".sent_state").write_text(f"{_key()} 1 2026-10-10\n", encoding="utf-8")
        mod = _lade_send_modul()
        smtp, gesendet = _smtp_mock()
        self.assertEqual(self._lauf(mod, smtp), 0)
        self.assertEqual(len(gesendet), 1)
        text = _mailtext(gesendet[0])
        self.assertIn("NACHTRAG1_TEXT", text)
        self.assertNotIn("ERSTBERICHT_TEXT", text)
        self.assertIn("Nachtrag", _betreff(gesendet[0]))

    def test_t12_altzeile_aus_kette3_zaehlt_als_erstbericht_gesendet(self):
        """T12: Merkerzeile im alten Format ("KEY DATUM") = Erstbericht gesendet; Nachtrag einmal, dann Ruhe."""
        _bericht(self.report_dir, "ERSTBERICHT_TEXT", "NACHTRAG1_TEXT")
        sent_state = self.report_dir / ".sent_state"
        sent_state.write_text(f"{_key()} 2026-10-12\n", encoding="utf-8")
        mod = _lade_send_modul()
        smtp, gesendet = _smtp_mock()
        self.assertEqual(self._lauf(mod, smtp), 0)
        self.assertEqual(self._lauf(mod, smtp), 0)
        self.assertEqual(len(gesendet), 1, "nur der Nachtrag, und nur einmal")
        self.assertNotIn("ERSTBERICHT_TEXT", _mailtext(gesendet[0]))
        self.assertIn(2, mod._sent_lauf_nrs(sent_state.read_text(encoding="utf-8"), _key()))

    def test_t13_nachtrag_nur_an_der_trennstelle_gezaehlt(self):
        """T13: „## Nachtrag KW" im Berichtstext zaehlt nicht als eigener Lauf."""
        _bericht(self.report_dir, "Text mit Zitat:\n## Nachtrag KW1_2026 (aus einem Beispiel)\nEnde")
        mod = _lade_send_modul()
        self.assertEqual(mod.count_report_runs(mod.find_current_report()), 1)


# --- Hilfsfunktionen (Nachbesserung 19.10.) ---

def _key() -> str:
    y, w, _ = datetime.now().isocalendar()
    return f"{y}_{w:02d}"


def _bericht(report_dir: Path, erst: str, *nachtraege: str) -> Path:
    """Legt den Bericht so an, wie llm_scout.save_report() ihn schreibt (Dateiname ueber week_key)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents" / "llm_scout"))
    from week_key import week_key_for_filename
    now = datetime.now()
    y, w, _ = now.isocalendar()
    text = erst
    for n in nachtraege:
        text += f"\n\n---\n\n## Nachtrag KW{w}_{y} ({now.strftime('%Y-%m-%d %H:%M')})\n\n{n}"
    path = report_dir / week_key_for_filename(now)
    path.write_text(text, encoding="utf-8")
    return path


def _lade_send_modul():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    sys.modules.pop("send_scout_email", None)
    import send_scout_email
    return send_scout_email


def _smtp_mock(fehler_beim_ersten: bool = False):
    import unittest.mock as mock
    gesendet: list[str] = []
    smtp = mock.MagicMock()
    smtp.__enter__ = mock.MagicMock(return_value=smtp)

    def fake_sendmail(absender, empfaenger, nachricht):
        gesendet.append(nachricht)
        if fehler_beim_ersten and len(gesendet) == 1:
            raise smtplib.SMTPException("Verbindung abgebrochen")

    smtp.sendmail = fake_sendmail
    # Fehlversuch nicht als gesendete Mail zaehlen? -> bewusst mitgezaehlt (Aufrufe von sendmail)
    return smtp, gesendet


def _mailtext(rohmail: str) -> str:
    import email
    msg = email.message_from_string(rohmail)
    return msg.get_payload(decode=True).decode("utf-8")


def _betreff(rohmail: str) -> str:
    import email
    from email.header import decode_header, make_header
    return str(make_header(decode_header(email.message_from_string(rohmail)["Subject"])))


def _zeilen(path: Path) -> list[str]:
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


class TestT8Import(unittest.TestCase):
    """T8: llm_scout.py lässt sich ohne __main__ importieren."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self._orig_lab_dir = os.environ.get("LAB_DIR")
        os.environ["LAB_DIR"] = self.tmpdir

    def tearDown(self):
        if self._orig_lab_dir is not None:
            os.environ["LAB_DIR"] = self._orig_lab_dir
        else:
            os.environ.pop("LAB_DIR", None)

    def test_t8_import_test_llm_scout_ohne_main(self):
        """T8: Import-Test – llm_scout.py lässt sich ohne __main__ importieren."""
        import importlib.util

        repo_root = Path(__file__).resolve().parent.parent
        llm_scout_path = repo_root / "agents" / "llm_scout" / "llm_scout.py"

        spec = importlib.util.spec_from_file_location("llm_scout_test", llm_scout_path)
        module = importlib.util.module_from_spec(spec)

        # main() darf nicht aufgerufen werden (keine HF/GitHub-Requests)
        # Wir setzen sys.exit zu einem Mock, um sicherzustellen, dass er nicht aufgerufen wird
        import unittest.mock as mock
        with mock.patch.object(sys, 'exit', side_effect=AssertionError("sys.exit() wurde aufgerufen – main() lief")):
            spec.loader.exec_module(module)

        # Modul ist verfügbar
        self.assertTrue(hasattr(module, 'main'),
                        "Modul muss main() enthalten")
        self.assertTrue(hasattr(module, 'save_report'),
                        "Modul muss save_report() enthalten (A1)")


if __name__ == "__main__":
    unittest.main()
