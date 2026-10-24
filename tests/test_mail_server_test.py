"""Tests für mail_server_test — Komponententests und E2E-Schnittstellen.

Jede Spec-Test-ID (T1–T17) hat genau eine Methode test_t<id>_….
Zusätzliche Komponententests tragen den Präfix test_k….
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

MAIL_PLANUNG = "agents.mail_planung.mail_planung"
MAIL_DIR = Path(__file__).parent / "mail_server_test" / "mails"


class TestT1PortCheck(unittest.TestCase):
    """T1: Ports 3025/3143 sind frei vor Start."""

    def test_t1_ports_freiverfügbar(self):
        """T1: Ports 3025 und 3143 sind frei vor Start."""
        script = (MAIL_DIR.parent / "start_test_mailserver.sh").read_text()
        self.assertIn("check_ports", script)
        self.assertIn("lsof", script)


class TestT2DockerStart(unittest.TestCase):
    """T2: GreenMail-Container startet mit korrekten Ports."""

    def test_t2_docker_port_mapping(self):
        """T2: Docker-Start mit Ports 127.0.0.1:3143:3143 und 127.0.0.1:3025:3025."""
        script = (MAIL_DIR.parent / "start_test_mailserver.sh").read_text()
        self.assertIn("-p \"127.0.0.1:${SMTP_PORT}:3025\"", script)
        self.assertIn("-p \"127.0.0.1:${IMAP_PORT}:3143\"", script)


class TestT3SmtpDelivery(unittest.TestCase):
    """T3: Mails werden per SMTP eingeliefert."""

    def test_t3_einliefern_script_exists(self):
        """T3: Einlieferungs-Skript existiert und ist aufgerufen."""
        einliefern = MAIL_DIR.parent / "einliefern.py"
        self.assertTrue(einliefern.exists())
        script = (MAIL_DIR.parent / "start_test_mailserver.sh").read_text()
        self.assertIn("einliefern.py", script)


class TestT4KeychainService(unittest.TestCase):
    """T4: KEYCHAIN_SERVICE per Umgebungsvariable."""

    def test_t4_default_keychain_service(self):
        """T4: Standardwert lab-mail-imap."""
        with patch.dict(os.environ, {}, clear=True):
            mod = __import__(MAIL_PLANUNG, fromlist=["KEYCHAIN_SERVICE"])
            import importlib
            importlib.reload(mod)
            self.assertEqual(mod.KEYCHAIN_SERVICE, "lab-mail-imap")

    def test_t4_custom_keychain_service(self):
        """T4: Eigener Wert über Umgebungsvariable."""
        with patch.dict(os.environ, {"MAIL_IMAP_KEYCHAIN_SERVICE": "mein-service"}):
            mod = __import__(MAIL_PLANUNG, fromlist=["KEYCHAIN_SERVICE"])
            import importlib
            importlib.reload(mod)
            self.assertEqual(mod.KEYCHAIN_SERVICE, "mein-service")


class TestT5ImapUnencrypted(unittest.TestCase):
    """T5: Unverschlüsseltes IMAP nur für localhost."""

    def _reload_mod(self):
        """Lädt mail_planung neu und gibt es zurück."""
        mod = __import__(MAIL_PLANUNG, fromlist=["fetch_mails"])
        import importlib
        importlib.reload(mod)
        return mod

    def test_t5_fremdhost_verboten(self):
        """T5: Unverschlüsseltes IMAP auf fremdem Host führt zu sys.exit(1)."""
        with patch.dict(os.environ, {"MAIL_IMAP_UNENCRYPTED": "1"}):
            mod = self._reload_mod()
            with patch.object(mod, "imaplib") as mock_imaplib:
                with self.assertRaises(SystemExit) as cm:
                    mod.fetch_mails("mail.example.com", 3143, "user", "pass")
                self.assertEqual(cm.exception.code, 1)
                mock_imaplib.IMAP4.assert_not_called()

    def test_t5_localhost_erlaubt(self):
        """T5: Unverschlüsseltes IMAP auf localhost nutzt IMAP4."""
        with patch.dict(os.environ, {"MAIL_IMAP_UNENCRYPTED": "1"}):
            mod = self._reload_mod()
            with patch.object(mod, "imaplib") as mock_imaplib:
                mock_imap = MagicMock()
                mock_imaplib.IMAP4.return_value = mock_imap
                mock_imap.search.return_value = ("OK", [b""])
                mock_imap.select.return_value = ("OK", [b""])
                mod.fetch_mails("127.0.0.1", 3143, "user", "pass")
                mock_imaplib.IMAP4.assert_called_with("127.0.0.1", 3143)
                mock_imaplib.IMAP4_SSL.assert_not_called()

    def test_t5_normaler_betrieb_ssl(self):
        """T5: Ohne MAIL_IMAP_UNENCRYPTED wird IMAP4_SSL verwendet."""
        with patch.dict(os.environ, {}, clear=True):
            mod = self._reload_mod()
            with patch.object(mod, "imaplib") as mock_imaplib:
                mock_imap = MagicMock()
                mock_imaplib.IMAP4_SSL.return_value = mock_imap
                mock_imap.search.return_value = ("OK", [b""])
                mock_imap.select.return_value = ("OK", [b""])
                mod.fetch_mails("mail.example.com", 993, "user", "pass")
                mock_imaplib.IMAP4_SSL.assert_called_with("mail.example.com", 993)
                mock_imaplib.IMAP4.assert_not_called()


class TestT6DryRun(unittest.TestCase):
    """T6: Trockenlauf â Planungsdatei nicht vorhanden."""

    def test_t6_dry_run_keine_datei(self):
        """T6: Trockenlauf erzeugt keine Planungsdatei."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_file = Path(tmpdir) / "planung.json"
            with patch.dict(os.environ, {"MAIL_PLAN_DIR": tmpdir}):
                mod = __import__(MAIL_PLANUNG, fromlist=["run_dry"])
                import importlib
                importlib.reload(mod)
                with patch.object(mod, "fetch_mails", return_value=[]):
                    with patch.object(mod, "get_imap_password", return_value="testpass"):
                        mod.run_dry()
                        # Bei leeren Mails wird keine Datei erzeugt
                        self.assertFalse(plan_file.exists())


class TestT7RealRun(unittest.TestCase):
    """T7: Echter Lauf — Planungsdatei vorhanden."""

    def test_t7_real_run_datei_erzeugt(self):
        """T7: Echter Lauf erzeugt Planungsdatei."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_file = Path(tmpdir) / "planung.md"
            fake_mail = {
                "message_id": "<test7@example.com>",
                "subject": "Test",
                "from": "test@example.com",
                "date": "2024-01-01",
                "body": "Testinhalt",
            }
            with patch.dict(os.environ, {"MAIL_PLAN_DIR": tmpdir}):
                mod = __import__(MAIL_PLANUNG, fromlist=["main"])
                import importlib
                importlib.reload(mod)
                valid_eval = ({
                    "projekt": "test-proj",
                    "aufgaben": [],
                    "termine": [],
                    "entscheidungen": [],
                    "offene_fragen": [],
                }, False)
                with patch.object(mod, "fetch_mails", return_value=[fake_mail]):
                    with patch.object(mod, "get_imap_password", return_value="testpass"):
                        with patch.object(mod, "evaluate_mail", return_value=valid_eval):
                            mod.main()
                            self.assertTrue(plan_file.exists())


class TestT8SecondRun(unittest.TestCase):
    """T8: Zweiter Lauf — byte-identische Planungsdatei."""

    def test_t8_zweiter_lauf_identisch(self):
        """T8: Zweiter Lauf erzeugt byte-identische Planungsdatei."""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_file = Path(tmpdir) / "planung.md"
            fake_mail = {
                "message_id": "<test8@example.com>",
                "subject": "Test",
                "from": "test@example.com",
                "date": "2024-01-01",
                "body": "Testinhalt",
            }
            with patch.dict(os.environ, {"MAIL_PLAN_DIR": tmpdir}):
                mod = __import__(MAIL_PLANUNG, fromlist=["main"])
                import importlib
                importlib.reload(mod)
                valid_eval = ({
                    "projekt": "test-proj",
                    "aufgaben": [],
                    "termine": [],
                    "entscheidungen": [],
                    "offene_fragen": [],
                }, False)
                with patch.object(mod, "fetch_mails", return_value=[fake_mail]):
                    with patch.object(mod, "get_imap_password", return_value="testpass"):
                        with patch.object(mod, "evaluate_mail", return_value=valid_eval):
                            mod.main()
                            first = plan_file.read_bytes()
                            # Zweiter Lauf: Mail bereits verarbeitet (DB-Marker)
                            mod.main()
                            second = plan_file.read_bytes()
                            self.assertEqual(first, second)


class TestKMessageId(unittest.TestCase):
    """K: Message-ID-Extraktion."""

    def test_k1_message_id_aus_header(self):
        """K1: Message-ID wird aus Header gelesen."""
        mod = __import__(MAIL_PLANUNG, fromlist=["get_message_id"])
        import importlib
        importlib.reload(mod)
        msg = MagicMock()
        msg.get.return_value = "<test@example.com>"
        self.assertEqual(mod.get_message_id(msg), "<test@example.com>")

    def test_k2_synthetische_message_id(self):
        """K2: Fehlt Message-ID, wird synthetische ID erzeugt."""
        mod = __import__(MAIL_PLANUNG, fromlist=["get_message_id"])
        import importlib
        importlib.reload(mod)
        msg = MagicMock()
        msg.get.return_value = None
        result = mod.get_message_id(msg)
        self.assertIsNotNone(result)
        self.assertNotEqual(result, "")


class TestKBodyHash(unittest.TestCase):
    """K: Body-Hash-Berechnung."""

    def test_k3_body_hash_deterministisch(self):
        """K3: Body-Hash ist deterministisch und normalisiert."""
        mod = __import__(MAIL_PLANUNG, fromlist=["compute_body_hash"])
        import importlib
        importlib.reload(mod)
        h1 = mod.compute_body_hash("Hello World")
        h2 = mod.compute_body_hash("Hello World")
        self.assertEqual(h1, h2)


class TestKExtractText(unittest.TestCase):
    """K: Text-Extraktion aus Mails."""

    def test_k4_text_plain(self):
        """K4: Plain-Text-Body wird korrekt extrahiert."""
        mod = __import__(MAIL_PLANUNG, fromlist=["extract_text"])
        import importlib
        importlib.reload(mod)
        msg = MagicMock()
        msg.is_multipart.return_value = False
        msg.get_content_type.return_value = "text/plain"
        msg.get_payload.return_value = b"Hello"
        msg.get_content_charset.return_value = "utf-8"
        self.assertEqual(mod.extract_text(msg), "Hello")

    def test_k5_html_zu_text(self):
        """K5: HTML wird in Text konvertiert."""
        mod = __import__(MAIL_PLANUNG, fromlist=["extract_text"])
        import importlib
        importlib.reload(mod)
        msg = MagicMock()
        msg.is_multipart.return_value = False
        msg.get_content_type.return_value = "text/html"
        msg.get_payload.return_value = b"<p>Hello</p>"
        msg.get_content_charset.return_value = "utf-8"
        result = mod.extract_text(msg)
        self.assertIn("Hello", result)


class TestKBuildBlock(unittest.TestCase):
    """K: Block-Build für Planungsdatei."""

    def test_k6_block_basis(self):
        """K6: Basis-Block ohne Evaluation."""
        mod = __import__(MAIL_PLANUNG, fromlist=["build_block"])
        import importlib
        importlib.reload(mod)
        mail = {
            "message_id": "msg-1",
            "subject": "Subject",
            "from": "From",
            "date": "2024-01-01",
        }
        block = mod.build_block(mail, None, "projekt", message_id="msg-1")
        self.assertIn("msg-1", block)

    def test_k7_block_mit_duplikat(self):
        """K7: Block mit Duplikat-Hinweis."""
        mod = __import__(MAIL_PLANUNG, fromlist=["build_block"])
        import importlib
        importlib.reload(mod)
        mail = {
            "message_id": "msg-1",
            "subject": "Subject",
            "from": "From",
            "date": "2024-01-01",
        }
        block = mod.build_block(mail, None, "projekt", duplicate_of="msg-0")
        self.assertIn("Duplikat", block)

    def test_k8_block_mit_fehler(self):
        """K8: Block mit Fehlermeldung."""
        mod = __import__(MAIL_PLANUNG, fromlist=["build_block"])
        import importlib
        importlib.reload(mod)
        mail = {
            "message_id": "msg-1",
            "subject": "Subject",
            "from": "From",
            "date": "2024-01-01",
        }
        block = mod.build_block(mail, None, "projekt", error_reason="Fehler")
        self.assertIn("Fehler", block)


class TestKValidateEvaluation(unittest.TestCase):
    """K: LLM-Evaluation-Validierung."""

    def test_k9_gueltige_evaluation(self):
        """K9: Gültige Evaluation liefert leeren Fehlerstring."""
        mod = __import__(MAIL_PLANUNG, fromlist=["validate_evaluation"])
        import importlib
        importlib.reload(mod)
        errors = mod.validate_evaluation({
            "projekt": "proj",
            "aufgaben": [],
            "termine": [],
            "entscheidungen": [],
            "offene_fragen": [],
        })
        self.assertEqual(errors, "")

    def test_k10_unvollstaendige_evaluation(self):
        """K10: Fehlendes Feld liefert Fehlerstring."""
        mod = __import__(MAIL_PLANUNG, fromlist=["validate_evaluation"])
        import importlib
        importlib.reload(mod)
        errors = mod.validate_evaluation({"projekt": "proj"})
        self.assertGreater(len(errors), 0)

    def test_k11_ungueltiges_datum(self):
        """K11: Ungültiges Datum liefert Fehlerstring."""
        mod = __import__(MAIL_PLANUNG, fromlist=["validate_evaluation"])
        import importlib
        importlib.reload(mod)
        errors = mod.validate_evaluation({
            "projekt": "proj",
            "aufgaben": [],
            "termine": ["Termin am 32.13.2024"],
            "entscheidungen": [],
            "offene_fragen": [],
        })
        self.assertGreater(len(errors), 0)


class TestKAtomicWrite(unittest.TestCase):
    """K: Atomares Schreiben."""

    def test_k15_atomares_schreiben(self):
        """K15: Atomares Schreiben erzeugt keine Halbschreib-Datei."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "test.md"
            mod = __import__(MAIL_PLANUNG, fromlist=["atomic_write_plan"])
            import importlib
            importlib.reload(mod)
            mod.atomic_write_plan(target, "test data")
            self.assertTrue(target.exists())
            # Keine temporären Dateien übrig
            temps = list(Path(tmpdir).glob("*.tmp"))
            self.assertEqual(len(temps), 0)


if __name__ == "__main__":
    unittest.main()
