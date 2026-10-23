#!/usr/bin/env python3
"""
Tests fuer mail_planung (Spec spec_20261022_mail_planung.md).

Kein Test hat Aussenwirkung:
- MAIL_PLAN_DIR auf temporares Verzeichnis
- IMAP_HOST = 127.0.0.1 (lokaler Testserver / Mock)
- get_imap_password() per unittest.mock ersetzt
- LLM-Call per unittest.mock ersetzt
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Module-Variablen mussen vor dem ersten Import gesetzt werden, da sie
# Modul-global aus os.getenv() gelesen werden.
# ---------------------------------------------------------------------------

_TEST_MAIL_PLAN_DIR = tempfile.mkdtemp(prefix="mail_plan_test_")
os.environ["MAIL_PLAN_DIR"] = _TEST_MAIL_PLAN_DIR
os.environ["IMAP_HOST"] = "127.0.0.1"
os.environ["IMAP_PORT"] = "993"
os.environ["IMAP_USER"] = "test@example.com"

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "agents" / "mail_planung"))


class TestMailPlanungBase(unittest.TestCase):
    """Gemeinsamer Testaufbau fuer mail_planung-Tests."""

    def setUp(self):
        # Frisches temporares Verzeichnis fuer jeden Test
        self.plan_dir = Path(tempfile.mkdtemp(prefix="mail_plan_test_"))
        os.environ["MAIL_PLAN_DIR"] = str(self.plan_dir)

        # Modul neu importieren, damit die Umgebungsvariablen greifen
        if "agents.mail_planung.mail_planung" in sys.modules:
            del sys.modules["agents.mail_planung.mail_planung"]
        if "mail_planung" in sys.modules:
            del sys.modules["mail_planung"]

        from agents.mail_planung import mail_planung as mp
        self.mp = mp

        # Module-Variablen auf Test-DIR umlenken
        self.mp.MAIL_PLAN_DIR = self.plan_dir
        self.mp.DB_PATH = self.plan_dir / "mail_planung.db"
        self.mp.PLAN_FILE = self.plan_dir / "planung.md"
        self.mp.PROJECT_CONFIG_FILE = self.plan_dir / "mail_projects.json"

        # get_imap_password mocken - kein echter Schlusselbund-Zugriff
        self._patch_get_password = patch.object(
            self.mp, "get_imap_password", return_value="dummy_password"
        )
        self._mock_get_password = self._patch_get_password.start()

        # LLM-Call mocken
        self._default_llm_result = {
            "projekt": "TestProjekt",
            "aufgaben": ["Testaufgabe"],
            "termine": ["2026-10-25: Teammeeting"],
            "entscheidungen": ["Testentscheidung"],
            "offene_fragen": ["Testfrage"],
        }
        self._mock_response = MagicMock()
        self._mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(self._default_llm_result)}}]
        }
        self._mock_response.raise_for_status = MagicMock()

        self._patch_requests = patch.object(
            self.mp.requests, "post", return_value=self._mock_response
        )
        self._mock_requests_post = self._patch_requests.start()

        # DB initialisieren
        self.conn = sqlite3.connect(self.mp.DB_PATH)
        self.mp.init_db(self.conn)

    def tearDown(self):
        self.conn.close()
        self._patch_get_password.stop()
        self._patch_requests.stop()

    def _create_mail(self, message_id="<test@test>", subject="Test", body="Testbody",
                     from_addr="test@example.com", date="2026-10-22"):
        """Hilfsfunktion zum Erzeugen eines Mail-Dictionaries."""
        return {
            "message_id": message_id,
            "subject": subject,
            "body": body,
            "from": from_addr,
            "date": date,
        }

    def _write_project_config(self, config):
        """Schreibt eine Projekt-Konfigurationsdatei."""
        self.mp.PROJECT_CONFIG_FILE.write_text(
            json.dumps(config), encoding="utf-8"
        )


# =========================================================================
# T2: Nur-HTML-Mail
# =========================================================================
class T2_HTMLMail(TestMailPlanungBase):
    """T2: Nur-HTML-Mail"""

    def test_t2_html_mail(self):
        """Prueft: A9 (HTML), A1 (Block-Format), A2 (read-only)"""
        mp = self.mp

        # HTML-Mail
        html_body = "<p>Aufgabe: Termin vereinbaren</p>"
        mail = self._create_mail(
            message_id="<html-test@test>",
            subject="HTML Test",
            body=html_body,
        )

        # LLM-Mock fuer HTML-Inhalt
        llm_result = {
            "projekt": "Test",
            "aufgaben": ["Termin vereinbaren"],
            "termine": [],
            "entscheidungen": [],
            "offene_fragen": [],
        }
        self._mock_response.json.return_value = {
            "choices": [{"message": {"content": json.dumps(llm_result)}}]
        }

        # extract_text auf HTML anwenden
        from email.mime.text import MIMEText
        msg = MIMEText(html_body, "html", "utf-8")

        extracted = mp.extract_text(msg)
        self.assertIn("Termin vereinbaren", extracted)

        # Block bauen
        block = mp.build_block(mail, llm_result, "Test")
        self.assertIn("### Aufgaben", block)
        self.assertIn("- [ ] Termin vereinbaren", block)

        # Prozessieren
        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0)

        # Planungsdatei pruefen
        self.assertTrue(mp.PLAN_FILE.exists())
        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("Termin vereinbaren", content)

        # DB pruefen
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1)


# =========================================================================
# T3: Umlaute + doppelte Zustellung (gleiche Message-ID)
# =========================================================================
class T3_UmlauteDedup(TestMailPlanungBase):
    """T3: Umlaute + doppelte Zustellung (gleiche Message-ID)"""

    def test_t3_umlaut_dedup(self):
        """Prueft: A9 (Umlaute), A3 (Dedup), A1"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<test-umlaut@test>",
            subject="Aenderung: Ueberfuehrung des Bueros",
            body="Bitte fuehren Sie die Aenderung durch.",
            date="2026-10-22",
        )

        # Erstlauf
        result1 = mp.process_mail(self.conn, mail)
        self.assertEqual(result1, 0)

        plan_content_after_first = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("Aenderung: Ueberfuehrung des Bueros", plan_content_after_first)

        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1)

        # Zweitlauf mit identischer Mail (gleiche ID)
        result2 = mp.process_mail(self.conn, mail)
        self.assertEqual(result2, 0)

        plan_content_after_second = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertEqual(plan_content_after_first, plan_content_after_second,
                         "Planungsdatei muss nach Zweitlauf byte-identisch sein")

        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1,
                         "DB muss weiterhin genau eine Zeile enthalten")


# =========================================================================
# T4: Mail ohne Message-ID-Header
# =========================================================================
class T4_KeinMessageID(TestMailPlanungBase):
    """T4: Mail ohne Message-ID-Header"""

    def test_t4_synthetic_message_id(self):
        """Prueft: A3 (synthetische ID), A6"""
        mp = self.mp

        mail = self._create_mail(
            message_id="",  # kein Message-ID
            subject="Keine ID",
            body="Body ohne Message-ID",
            from_addr="no-id@test.com",
            date="2026-10-22",
        )

        message_id = mp.get_message_id(mail)
        self.assertTrue(message_id.startswith("<synthetic-"),
                        "Synthetische ID muss mit '<synthetic-' beginnen")

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0)

        cursor = self.conn.execute(
            "SELECT message_id FROM processed_mails WHERE message_id=?",
            (message_id,)
        )
        self.assertIsNotNone(cursor.fetchone(),
                             "Synthetische ID muss in DB stehen")


# =========================================================================
# T5: Leerer Text / nur Anhang
# =========================================================================
class T5_LeeererText(TestMailPlanungBase):
    """T5: Leerer Text / nur Anhang"""

    def test_t5_leerer_body_kein_llm_call(self):
        """Prueft: A9 (leerer Text, Anhang), A1, A5 (LLM-Call wird uebersprungen)"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<empty@test>",
            subject="Leere Mail",
            body="",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0)

        # LLM-Mock wurde nicht aufgerufen
        self.assertEqual(self._mock_requests_post.call_count, 0,
                         "LLM-Call darf bei leerem Body nicht erfolgen")

        # Block mit 'Kein verwertbarer Inhalt'
        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("> Kein verwertbarer Inhalt", content)

        # Marker gesetzt
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1)

    def test_t5_nur_anhang(self):
        """Mail mit nur Anhang (kein Textbody)"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<attachment-only@test>",
            subject="Nur Anhang",
            body="",  # Anhang wird ignoriert, Body bleibt leer
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0)
        self.assertEqual(self._mock_requests_post.call_count, 0)

        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("> Kein verwertbarer Inhalt", content)


# =========================================================================
# T6: Weiterleitungskette + moegliche Duplikate
# =========================================================================
class T6_WeiterleitungDuplikat(TestMailPlanungBase):
    """T6: Weiterleitungskette + moegliche Duplikate"""

    def test_t6_duplikat_kennzeichnung(self):
        """Prueft: A9 (Weiterleitung), A4 (Duplikat-Kennzeichnung)"""
        mp = self.mp

        # Erste Mail
        mail1 = self._create_mail(
            message_id="<first@test>",
            subject="Original",
            body="Dies ist der Originaltext der Mail.",
        )
        result1 = mp.process_mail(self.conn, mail1)
        self.assertEqual(result1, 0)

        # Zweite Mail: gleicher Inhalt, andere Message-ID
        mail2 = self._create_mail(
            message_id="<second@test>",
            subject="Original (Weiterleitung)",
            body="Dies ist der Originaltext der Mail.",
        )
        result2 = mp.process_mail(self.conn, mail2)
        self.assertEqual(result2, 0)

        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("m\u00f6gliches Duplikat von <first@test>", content)

        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 2)


# =========================================================================
# T7: Fehlerpfad — LLM liefert ungueltiges JSON (Validierungsfehler)
# =========================================================================
class T7_UngueltigesJSON(TestMailPlanungBase):
    """T7: Fehlerpfad — LLM liefert ungueltiges JSON (Validierungsfehler)"""

    def test_t7_ungueltiges_json_validierungsfehler(self):
        """Prueft: Nachbesserung 1 — ungueltiges JSON ist Validierungsfehler:
        Block mit Warnung, Marker gesetzt, Exit 0."""
        mp = self.mp

        # LLM-Mock liefert ungueltiges JSON
        self._mock_response.json.return_value = {
            "choices": [{"message": {"content": "dies ist kein JSON"}}]
        }

        mail = self._create_mail(
            message_id="<bad-json@test>",
            subject="Bad JSON",
            body="Body fuer schlechtes JSON",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0,
                          "Validierungsfehler darf Exit 0 liefern (Block wird geschrieben)")

        # Marker in DB gesetzt
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1,
                          "Marker muss gesetzt werden")

        # Planungsdatei entholt Block mit Warnung
        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("<!-- mail-id: <bad-json@test> -->", content)
        self.assertIn("Auswertung fehlgeschlagen", content)


# =========================================================================
# T8: Fehlerpfad — os.replace schlaegt fehl
# =========================================================================
class T8_OsReplaceFehler(TestMailPlanungBase):
    """T8: Fehlerpfad — os.replace schlaegt fehl"""

    def test_t8_os_replace_fehler(self):
        """Prueft: A6 (Reihenfolge), A1 (atomares Schreiben)"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<replace-fail@test>",
            subject="Replace Fail",
            body="Body fuer Replace-Fehler",
        )

        with patch.object(os, "replace", side_effect=OSError("No space left on device")):
            result = mp.process_mail(self.conn, mail)
            self.assertNotEqual(result, 0)

        # Planungsdatei unveraendert
        if mp.PLAN_FILE.exists():
            content = mp.PLAN_FILE.read_text(encoding="utf-8")
            self.assertNotIn("Replace Fail", content)

        # Kein Marker in DB
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 0)

        # Temp-Dateien aufgeraeumt
        tmp_files = list(self.plan_dir.glob(".planung_*.tmp"))
        self.assertEqual(len(tmp_files), 0, "Temp-Datei muss aufgeraeumt sein")


# =========================================================================
# T9: Leeres Postfach
# =========================================================================
class T9_LeeeresPostfach(TestMailPlanungBase):
    """T9: Leeres Postfach"""

    def test_t9_leeres_postfach(self):
        """Prueft: A2 (leeres Postfach), A6"""
        mp = self.mp

        # fetch_mails mocken: leere Liste
        with patch.object(mp, "fetch_mails", return_value=[]):
            result = mp.main()
            self.assertEqual(result, 0)

        # Planungsdatei nicht angelegt
        self.assertFalse(mp.PLAN_FILE.exists(),
                         "Planungsdatei darf bei leerem Postfach nicht angelegt werden")


# =========================================================================
# T10: Postfach bleibt unveraendert (read-only)
# =========================================================================
class T10_Readonly(TestMailPlanungBase):
    """T10: Postfach bleibt unveraendert (read-only)"""

    def test_t10_readonly_select(self):
        """Prueft: A2"""
        mp = self.mp

        # imaplib.IMAP4_SSL mocken
        mock_imap = MagicMock()
        mock_imap.search.return_value = ("OK", [b""])
        mock_imap.logout = MagicMock()

        with patch.object(mp.imaplib, "IMAP4_SSL", return_value=mock_imap):
            with patch.object(mp, "get_imap_password", return_value="dummy"):
                mp.fetch_mails("127.0.0.1", 993, "test@test.com", "dummy")

        # select wurde mit readonly=True aufgerufen
        mock_imap.select.assert_called_with("INBOX", readonly=True)


# =========================================================================
# T11: Trockenlauf (run_dry)
# =========================================================================
class T11_Trockenlauf(TestMailPlanungBase):
    """T11: Trockenlauf ueber run_dry()"""

    def test_t11_dry_run(self):
        """Prueft: A7 — Trockenlauf via run_dry(), fetch_mails & get_imap_password gemockt"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<dry-run@test>",
            subject="Dry Run Test",
            body="Body fuer Trockenlauf",
        )

        # Vorheriger Zustand
        plan_existed = mp.PLAN_FILE.exists()
        plan_content_before = mp.PLAN_FILE.read_text(encoding="utf-8") if plan_existed else ""

        # fetch_mails und get_imap_password mocken (run_dry ruft beide auf)
        with patch.object(mp, "fetch_mails", return_value=[mail]):
            with patch.object(mp, "get_imap_password", return_value="dummy_password"):
                result = mp.run_dry()
                self.assertEqual(result, 0)

        # Planungsdatei unveraendert
        if plan_existed:
            self.assertEqual(mp.PLAN_FILE.read_text(encoding="utf-8"), plan_content_before)
        else:
            self.assertFalse(mp.PLAN_FILE.exists())

        # DB unveraendert
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 0,
                          "DB darf im Trockenlauf nicht veraendert werden")

        # Preview existiert
        outbox_dir = self.plan_dir / "outbox"
        preview_files = list(outbox_dir.glob("preview_*.md"))
        self.assertGreaterEqual(len(preview_files), 1,
                                 "Preview-Datei muss existieren")

        preview_content = preview_files[0].read_text(encoding="utf-8")
        self.assertIn("Dry Run Test", preview_content)


# =========================================================================
# T12: Skript laedt als Skript (kein ImportError)
# =========================================================================
class T12_SkriptLoad(unittest.TestCase):
    """T12: Skript laedt als Skript (kein ImportError)"""

    def test_t12_sript_ladet_als_skript(self):
        """Prueft: Einstiegspunkt (Skript-Start)"""
        script_path = str(_REPO_ROOT / "agents" / "mail_planung" / "mail_planung.py")
        result = subprocess.run(
            [sys.executable, "-c",
             f"import runpy; runpy.run_path('{script_path}', run_name='kein_main')"],
            capture_output=True, text=True
        )
        self.assertEqual(
            result.returncode, 0,
            f"mail_planung.py muss als Skript laden koennen. stderr: {result.stderr}"
        )
        self.assertNotIn("ImportError", result.stderr)


# =========================================================================
# T13: Modul-Import ohne Nebenwirkung
# =========================================================================
class T13_ModulImport(unittest.TestCase):
    """T13: Modul-Import ohne Nebenwirkung"""

    def test_t13_import_ohne_nebenwirkung(self):
        """Prueft: Einstiegspunkt (Modul-Import)"""
        test_dir = tempfile.mkdtemp(prefix="mail_plan_import_test_")
        env = os.environ.copy()
        env["MAIL_PLAN_DIR"] = test_dir
        env["IMAP_HOST"] = "127.0.0.1"

        result = subprocess.run(
            [sys.executable, "-c",
             "from agents.mail_planung import mail_planung"],
            capture_output=True, text=True, env=env
        )
        self.assertEqual(result.returncode, 0,
                         f"Import muss gelingen. stderr: {result.stderr}")

        # Keine Dateien im MAIL_PLAN_DIR erstellt
        plan_dir = Path(test_dir)
        files = list(plan_dir.iterdir())
        self.assertEqual(len(files), 0,
                         "Import darf keine Dateien erstellen")


# =========================================================================
# T14: Schlusselbund-Fehler
# =========================================================================
class T14_SchlusselbundFehler(TestMailPlanungBase):
    """T14: Schlusselbund-Fehler"""

    def test_t14_schlusselbund_fehler(self):
        """Prueft: A8"""
        mp = self.mp

        # get_imap_password mocken mit Fehler
        with patch.object(mp, "get_imap_password",
                          side_effect=RuntimeError(
                              "Schluesselbund-Eintrag 'lab-mail-imap' nicht gefunden")):
            result = mp.main()
            self.assertNotEqual(result, 0,
                                "Exit-Code muss ungleich 0 sein bei Schlusselbund-Fehler")

        # Keine IMAP-Verbindung aufgebaut
        # Planungsdatei und DB unveraendert
        self.assertFalse(mp.PLAN_FILE.exists())


# =========================================================================
# T15: Projekt-Zuordnung ueber Konfigurationsdatei
# =========================================================================
class T15_ProjektZuordnung(TestMailPlanungBase):
    """T15: Projekt-Zuordnung ueber Konfigurationsdatei"""

    def test_t15_projekt_treffer(self):
        """Prueft: A10"""
        mp = self.mp

        config = [
            {"sender": "a@firma-x.de", "project": "X"},
            {"keyword": "haushalt", "project": "H"},
        ]
        self._write_project_config(config)

        mail = self._create_mail(
            message_id="<proj-x@test>",
            subject="Projekt X Mail",
            body="Body fuer Projekt X",
            from_addr="a@firma-x.de",
        )

        project = mp.resolve_project(mail)
        self.assertEqual(project, "X")

    def test_t15_projekt_unzugeordnet(self):
        """Prueft: A10 (kein Treffer)"""
        mp = self.mp

        config = [
            {"sender": "a@firma-x.de", "project": "X"},
        ]
        self._write_project_config(config)

        mail = self._create_mail(
            message_id="<proj-none@test>",
            subject="Kein Projekt",
            body="Body ohne Treffer",
            from_addr="unknown@test.com",
        )

        project = mp.resolve_project(mail)
        self.assertEqual(project, "Unzugeordnet")


# =========================================================================
# T16: mail-id-Kommentar statt Datum-Betreff-Zeile
# =========================================================================
class T16_MailIdKommentar(TestMailPlanungBase):
    """T16: mail-id-Kommentar in Block und Prüfung"""

    def test_t16_mail_id_comment_in_block(self):
        """Prüft: Nachbesserung 1 — Block enthält <!-- mail-id: ... -->"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<t16@test>",
            subject="Mail-ID Test",
            body="Body für T16",
        )

        block = mp.build_block(mail, self._default_llm_result, "Test", message_id="<t16@test>")
        self.assertIn("<!-- mail-id: <t16@test> -->", block)
        self.assertNotIn("<!-- mail-id: ", block.split("<!-- mail-id: <t16@test> -->")[0],
                         "mail-id-Kommentar muss am Block-Anfang stehen")

    def test_t16_mail_id_check_in_process_mail(self):
        """Prüft: Nachbesserung 1 — process_mail sucht mail-id-Kommentar, nicht ##-Zeile"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<t16-check@test>",
            subject="Mail-ID Check",
            body="Body für T16b",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0)

        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("<!-- mail-id: <t16-check@test> -->", content)


# =========================================================================
# T17: Datum-Validierung mit strptime (Monat 13 / Tag 32 ungültig)
# =========================================================================
class T17_DatumValidierung(TestMailPlanungBase):
    """T17: Datum-Validierung mit strptime"""

    def test_t17_strptime_gueltiges_datum(self):
        """Prüft: Nachbesserung 1 — gültiges Datum akzeptiert"""
        mp = self.mp

        error = mp.validate_evaluation({
            "projekt": "Test",
            "aufgaben": [],
            "termine": ["2026-10-25: Meeting"],
            "entscheidungen": [],
            "offene_fragen": [],
        })
        self.assertEqual(error, "", "Gültiges Datum darf keinen Fehler liefern")

    def test_t17_strptime_monat_13(self):
        """Prüft: Nachbesserung 1 — Monat 13 ist ungültig"""
        mp = self.mp

        error = mp.validate_evaluation({
            "projekt": "Test",
            "aufgaben": [],
            "termine": ["2026-13-01: Meeting"],
            "entscheidungen": [],
            "offene_fragen": [],
        })
        self.assertNotEqual(error, "", "Monat 13 muss fehlschlagen")
        self.assertIn("Ungültiges Datum", error)

    def test_t17_strptime_tag_32(self):
        """Prüft: Nachbesserung 1 — Tag 32 ist ungültig"""
        mp = self.mp

        error = mp.validate_evaluation({
            "projekt": "Test",
            "aufgaben": [],
            "termine": ["2026-02-32: Meeting"],
            "entscheidungen": [],
            "offene_fragen": [],
        })
        self.assertNotEqual(error, "", "Tag 32 muss fehlschlagen")
        self.assertIn("Ungültiges Datum", error)


# =========================================================================
# T18: JSON-Cleaning (Code-Zäune + Text vor/nach JSON)
# =========================================================================
class T18_JsonCleaning(TestMailPlanungBase):
    """T18: Code-Zäune und umgebenden Text entfernen"""

    def test_t18_code_fence_json(self):
        """Prüft: Nachbesserung 1 — ```json ... ``` entfernen"""
        mp = self.mp

        content = "```json\n{\"projekt\": \"Test\", \"aufgaben\": [], \"termine\": [], \"entscheidungen\": [], \"offene_fragen\": []}\n```"
        cleaned = mp._extract_json_from_content(content)
        self.assertIn('"projekt"', cleaned)
        self.assertNotIn("```", cleaned)

    def test_t18_code_fence_plain(self):
        """Prüft: Nachbesserung 1 — ``` ... ``` entfernen"""
        mp = self.mp

        content = "```\n{\"aufgaben\": []}\n```"
        cleaned = mp._extract_json_from_content(content)
        self.assertIn('"aufgaben"', cleaned)
        self.assertNotIn("```", cleaned)

    def test_t18_text_around_json(self):
        """Prüft: Nachbesserung 1 — Text vor/nach JSON entfernen"""
        mp = self.mp

        content = "Hier ist die Antwort:\n{\"projekt\": \"X\"}\nVielen Dank!"
        cleaned = mp._extract_json_from_content(content)
        self.assertEqual(cleaned, '{"projekt": "X"}')


# =========================================================================
# T19: enable_thinking: False im Request
# =========================================================================
class T19_EnableThinking(TestMailPlanungBase):
    """T19: enable_thinking: False im LLM-Request"""

    def test_t19_chat_template_kwargs(self):
        """Prüft: Nachbesserung 1 — chat_template_kwargs im Request"""
        mp = self.mp

        mail = self._create_mail(
            message_id="<t19@test>",
            subject="Enable Thinking Test",
            body="Body für T19",
        )

        # evaluate_mail aufrufen
        try:
            mp.evaluate_mail(mail["body"])
        except Exception:
            pass  # Mock liefert evtl. falsches Format, wir prüfen nur den Call

        # Request-JSON prüfen
        self.assertEqual(self._mock_requests_post.call_count, 1)
        call_args = self._mock_requests_post.call_args
        request_json = call_args[1]["json"]
        self.assertIn("chat_template_kwargs", request_json)
        self.assertEqual(request_json["chat_template_kwargs"]["enable_thinking"], False)


# =========================================================================
# T20: Fehlerarten trennen (Netzwerk vs Validierung)
# =========================================================================
class T20_FehlerartenTrennen(TestMailPlanungBase):
    """T20: Fehlerarten trennen (Netzwerk vs Validierung)"""

    def test_t20_network_error_no_entry(self):
        """Prüft: Nachbesserung 1 — Netzwerkfehler → Exit 1, kein Eintrag, kein Marker"""
        mp = self.mp

        # Netzwerkfehler simulieren
        self._mock_requests_post.side_effect = mp.requests.exceptions.ConnectionError("Connection refused")

        mail = self._create_mail(
            message_id="<t20-net@test>",
            subject="Network Error",
            body="Body für T20a",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertNotEqual(result, 0, "Netzwerkfehler muss Exit ≠ 0 liefern")

        # Kein Eintrag in Planungsdatei
        if mp.PLAN_FILE.exists():
            content = mp.PLAN_FILE.read_text(encoding="utf-8")
            self.assertNotIn("<t20-net@test>", content)

        # Kein Marker in DB
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 0)

    def test_t20_validation_error_with_entry(self):
        """Prüft: Nachbesserung 1 — Validierungsfehler → Block mit Warnung, Marker gesetzt"""
        mp = self.mp

        # Validierungsfehler simulieren (fehlendes Feld)
        self._mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"aufgaben": []}'}}]
        }

        mail = self._create_mail(
            message_id="<t20-val@test>",
            subject="Validation Error",
            body="Body für T20b",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0, "Validierungsfehler darf Exit 0 liefern (Block wird geschrieben)")

        # Eintrag in Planungsdatei mit Warnung
        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("<!-- mail-id: <t20-val@test> -->", content)
        self.assertIn("Auswertung fehlgeschlagen", content)

        # Marker gesetzt
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1)


# =========================================================================
# T21: Sehr langer Mailtext -> Kuerzung
# =========================================================================
class T21_LangerMailtext(TestMailPlanungBase):
    """T21: Sehr langer Mailtext -> Kuerzung auf MAIL_MAX_CHARS"""

    def test_t21_langer_mailtext_kuerzung(self):
        """Prueft: Nachbesserung 2 — LLM bekommt hochstens MAIL_MAX_CHARS,
        Block mit Kuerzungshinweis."""
        mp = self.mp

        # Sehr langer Body (25000 Zeichen)
        long_body = "X" * 25000
        mail = self._create_mail(
            message_id="<t21-long@test>",
            subject="Langer Text",
            body=long_body,
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0)

        # LLM-Call wurde aufgerufen
        self.assertEqual(self._mock_requests_post.call_count, 1)

        # LLM bekam hochstens MAIL_MAX_CHARS
        call_args = self._mock_requests_post.call_args
        request_json = call_args[1]["json"]
        user_content = request_json["messages"][1]["content"]
        # "Analysiere folgende E-Mail:\n\n" = 29 Zeichen Prefix
        body_in_prompt = user_content[len("Analysiere folgende E-Mail:\n\n"):]
        self.assertLessEqual(len(body_in_prompt), mp.MAIL_MAX_CHARS,
                             "LLM darf nicht mehr als MAIL_MAX_CHARS bekommen")

        # Block mit Kuerzungshinweis
        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("(Mailtext f\u00fcr die Auswertung gek\u00fcrzt)", content)


# =========================================================================
# T22: HTTP 400 -> dauerhaft, Block "Auswertung fehlgeschlagen", Marker
# =========================================================================
class T22_HTTP400(TestMailPlanungBase):
    """T22: HTTP 400 -> dauerhaft wie Validierungsfehler"""

    def test_t22_http_400_dauerhaft(self):
        """Prueft: Nachbesserung 2 — HTTP 400 -> Block 'Auswertung fehlgeschlagen',
        Marker gesetzt, Exit 0."""
        mp = self.mp

        # HTTP 400 simulieren
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        http_error = mp.requests.exceptions.HTTPError("400 Client Error")
        http_error.response = mock_resp
        mock_raise = MagicMock(side_effect=http_error)
        self._mock_response.raise_for_status = mock_raise

        mail = self._create_mail(
            message_id="<t22-400@test>",
            subject="HTTP 400",
            body="Body fuer T22",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0,
                         "HTTP 400 muss wie Validierungsfehler behandelt werden (Exit 0)")

        # Block mit "Auswertung fehlgeschlagen"
        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("<!-- mail-id: <t22-400@test> -->", content)
        self.assertIn("Auswertung fehlgeschlagen", content)

        # Marker gesetzt
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1)


# =========================================================================
# T23: HTTP 503 -> voruebergehend, kein Eintrag, kein Marker, Exit 1
# =========================================================================
class T23_HTTP503(TestMailPlanungBase):
    """T23: HTTP 503 -> voruebergehend"""

    def test_t23_http_503_voruebergehend(self):
        """Prueft: Nachbesserung 2 — HTTP 503 -> kein Eintrag, kein Marker, Exit 1."""
        mp = self.mp

        # HTTP 503 simulieren
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        http_error = mp.requests.exceptions.HTTPError("503 Server Error")
        http_error.response = mock_resp
        mock_raise = MagicMock(side_effect=http_error)
        self._mock_response.raise_for_status = mock_raise

        mail = self._create_mail(
            message_id="<t23-503@test>",
            subject="HTTP 503",
            body="Body fuer T23",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertNotEqual(result, 0, "HTTP 503 muss Exit != 0 liefern")

        # Kein Eintrag in Planungsdatei
        if mp.PLAN_FILE.exists():
            content = mp.PLAN_FILE.read_text(encoding="utf-8")
            self.assertNotIn("<t23-503@test>", content)

        # Kein Marker in DB
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 0)


# =========================================================================
# T24: content None -> dauerhaft, Block "Auswertung fehlgeschlagen"
# =========================================================================
class T24_ContentNone(TestMailPlanungBase):
    """T24: content None -> dauerhaft"""

    def test_t24_content_none(self):
        """Prueft: Nachbesserung 2 — content None -> Block 'Auswertung fehlgeschlagen',
        Marker gesetzt."""
        mp = self.mp

        # Antwort mit content=None
        self._mock_response.json.return_value = {
            "choices": [{"message": {"content": None}}]
        }

        mail = self._create_mail(
            message_id="<t24-none@test>",
            subject="Content None",
            body="Body fuer T24",
        )

        result = mp.process_mail(self.conn, mail)
        self.assertEqual(result, 0,
                         "content None muss wie Validierungsfehler behandelt werden (Exit 0)")

        # Block mit "Auswertung fehlgeschlagen"
        content = mp.PLAN_FILE.read_text(encoding="utf-8")
        self.assertIn("<!-- mail-id: <t24-none@test> -->", content)
        self.assertIn("Auswertung fehlgeschlagen", content)

        # Marker gesetzt
        cursor = self.conn.execute("SELECT COUNT(*) FROM processed_mails")
        self.assertEqual(cursor.fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
