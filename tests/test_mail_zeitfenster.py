#!/usr/bin/env python3
"""Vorgabe-Tests fuer mail_zeitfenster (spec_20261106_mail_zeitfenster.md, T1–T8).

VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.

Keine Aussenwirkung: MAIL_PLAN_DIR je Test in tempfile.mkdtemp(); imaplib.IMAP4_SSL durch FakeIMAP ersetzt (nur
erfundene Mails, kein Netz); get_imap_password und requests.post durch Attrappen ersetzt (kein Schluesselbund,
kein Modell). T8 startet das Skript in einem Unterprozess mit ungueltiger Einstellung – es endet vor Schluesselbund,
DB und IMAP. Neue Funktionen werden in jeder Methode ueber self.mp angesprochen (rot vorab).
"""
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, timedelta
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "agents" / "mail_planung"))
os.environ.setdefault("MAIL_PLAN_DIR", tempfile.mkdtemp(prefix="mail_zf_"))
os.environ["IMAP_HOST"] = "127.0.0.1"
os.environ["IMAP_PORT"] = "993"
os.environ["IMAP_USER"] = "test@example.com"
SKRIPT = _REPO / "agents" / "mail_planung" / "mail_planung.py"


def roh(nr: int, mit_id: bool = True) -> bytes:
    m = EmailMessage()
    m["From"] = "absender@example.com"
    m["Subject"] = f"Mail {nr}"
    m["Date"] = "Fri, 06 Nov 2026 08:00:00 +0100"
    if mit_id:
        m["Message-ID"] = f"<m{nr}@test>"
    m.set_content(f"Inhalt der Mail {nr}")
    return bytes(m)


class FakeIMAP:
    """Ersatz fuer imaplib.IMAP4_SSL: Postfach aus erfundenen Mails, zeichnet Aufrufe auf."""

    def __init__(self, mails: list[bytes]):
        self.mails = mails
        self.suchen: list[tuple] = []
        self.voll: list[int] = []
        self.kopf: list[int] = []
        self.select_args = None

    def __call__(self, host, port):
        return self

    def login(self, user, pw):
        return "OK", [b""]

    def select(self, box, readonly=False):
        self.select_args = (box, readonly)
        return "OK", [str(len(self.mails)).encode()]

    def search(self, charset, *kriterien):
        self.suchen.append(kriterien)
        return "OK", [" ".join(str(i + 1) for i in range(len(self.mails))).encode()]

    def fetch(self, mid, teile):
        i = int(mid)
        raw = self.mails[i - 1]
        if "HEADER.FIELDS" in teile:
            self.kopf.append(i)
            kopf = b"".join(z + b"\n" for z in raw.split(b"\n") if z.lower().startswith(b"message-id:")) + b"\r\n"
            return "OK", [(f"{i} (BODY[HEADER.FIELDS (MESSAGE-ID)] {{{len(kopf)}}}".encode(), kopf), b")"]
        if "RFC822" in teile or "BODY[]" in teile or "BODY.PEEK[]" in teile:
            self.voll.append(i)
            return "OK", [(f"{i} (RFC822 {{{len(raw)}}}".encode(), raw), b")"]
        return "NO", [b""]

    def logout(self):
        return "BYE", [b""]


class Basis(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="mail_zf_"))
        for name in ("agents.mail_planung.mail_planung", "mail_planung"):
            sys.modules.pop(name, None)
        from agents.mail_planung import mail_planung as mp
        self.mp = mp
        mp.MAIL_PLAN_DIR = self.dir
        mp.DB_PATH = self.dir / "mail_planung.db"
        mp.PLAN_FILE = self.dir / "planung.md"
        mp.PROJECT_CONFIG_FILE = self.dir / "mail_projects.json"
        self.pw = patch.object(mp, "get_imap_password", return_value="dummy")
        self.pw_mock = self.pw.start()
        self.addCleanup(self.pw.stop)
        antwort = MagicMock()
        antwort.json.return_value = {"choices": [{"message": {"content": json.dumps(
            {"projekt": "P", "aufgaben": ["a"], "termine": ["2026-11-07: x"], "entscheidungen": [],
             "offene_fragen": []})}}]}
        antwort.raise_for_status = MagicMock()
        self.post = patch.object(mp.requests, "post", return_value=antwort)
        self.post.start()
        self.addCleanup(self.post.stop)
        self.env = patch.dict(os.environ, {}, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)
        os.environ.pop("MAIL_SINCE_DAYS", None)
        os.environ.pop("MAIL_MAX_JE_LAUF", None)

    def rufen(self, fn, *a, **k):
        aus, err = io.StringIO(), io.StringIO()
        with redirect_stdout(aus), redirect_stderr(err):
            code = fn(*a, **k)
        return code, aus.getvalue(), err.getvalue()

    def db_ids(self) -> set:
        if not self.mp.DB_PATH.exists():
            return set()
        with sqlite3.connect(self.mp.DB_PATH) as c:
            try:
                return {r[0] for r in c.execute("SELECT message_id FROM processed_mails")}
            except sqlite3.OperationalError:
                return set()


class Einstellungen(Basis):

    def test_t1_zeitfenster_und_imap_datum(self):
        """T1: Standardwerte 0/20, gültige und ungültige Werte, IMAP-Datum unabhängig von der Locale"""
        mp = self.mp
        self.assertEqual(mp.zeitfenster(), (0, 20))
        os.environ["MAIL_SINCE_DAYS"], os.environ["MAIL_MAX_JE_LAUF"] = " 3 ", "5"
        self.assertEqual(mp.zeitfenster(), (3, 5))
        for name, wert, minimum in (("MAIL_SINCE_DAYS", "-1", 0), ("MAIL_SINCE_DAYS", "heute", 0),
                                    ("MAIL_MAX_JE_LAUF", "0", 1), ("MAIL_MAX_JE_LAUF", "abc", 1),
                                    ("MAIL_MAX_JE_LAUF", "2.5", 1)):
            os.environ["MAIL_SINCE_DAYS"], os.environ["MAIL_MAX_JE_LAUF"] = "0", "20"
            os.environ[name] = wert
            with self.assertRaises(ValueError) as ctx:
                mp.zeitfenster()
            self.assertEqual(str(ctx.exception), f"{name} ungültig: '{wert}' (ganze Zahl ≥ {minimum})")
        class KeinStrftime(date):
            def strftime(self, fmt):
                raise AssertionError("strftime hängt von der Locale ab (Mai/Dez statt May/Dec)")

            def __format__(self, fmt):
                if fmt:
                    raise AssertionError("Datumsformat hängt von der Locale ab")
                return super().__format__(fmt)
        self.assertEqual(mp.imap_datum(KeinStrftime(2026, 5, 1)), "01-May-2026")
        self.assertEqual(mp.imap_datum(KeinStrftime(2026, 12, 9)), "09-Dec-2026")
        import locale
        alt = locale.setlocale(locale.LC_TIME)
        for loc in ("de_DE.UTF-8", "de_DE.utf8", "de_DE"):
            try:
                locale.setlocale(locale.LC_TIME, loc)
                break
            except locale.Error:
                continue
        try:
            self.assertEqual(mp.imap_datum(date(2026, 11, 6)), "06-Nov-2026")
            self.assertEqual(mp.imap_datum(date(2026, 5, 1)), "01-May-2026")
            self.assertEqual(mp.imap_datum(date(2027, 3, 31)), "31-Mar-2027")
            self.assertEqual(mp.imap_datum(date(2026, 12, 9)), "09-Dec-2026")
        finally:
            locale.setlocale(locale.LC_TIME, alt)


class Abruf(Basis):

    def test_t2_suche_since_und_bestand(self):
        """T2: fetch_mails sucht mit SINCE; ohne since wie bisher ALL und alles (Bestand-Aufruf)"""
        mp = self.mp
        fake = FakeIMAP([roh(1), roh(2), roh(3)])
        with patch.object(mp.imaplib, "IMAP4_SSL", fake):
            _, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p", since="06-Nov-2026")
        self.assertEqual(fake.suchen, [("SINCE", "06-Nov-2026")])
        self.assertEqual(fake.select_args, ("INBOX", True))
        fake = FakeIMAP([roh(1), roh(2), roh(3)])
        with patch.object(mp.imaplib, "IMAP4_SSL", fake):
            code, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p")
        self.assertEqual(fake.suchen, [("ALL",)])
        self.assertEqual([m["subject"] for m in code], ["Mail 1", "Mail 2", "Mail 3"])
        self.assertEqual(fake.voll, [1, 2, 3])

    def test_t3_hoechstzahl_aelteste_zuerst(self):
        """T3: höchstens max_anzahl neue Mails vollständig, älteste zuerst, Zusammenfassung mit Rest"""
        mp = self.mp
        fake = FakeIMAP([roh(i) for i in range(1, 26)])
        with patch.object(mp.imaplib, "IMAP4_SSL", fake):
            mails, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p", since="06-Nov-2026",
                                       max_anzahl=20, bekannt=set())
        self.assertEqual([m["subject"] for m in mails], [f"Mail {i}" for i in range(1, 21)])
        self.assertEqual(fake.voll, list(range(1, 21)))
        self.assertIn("Postfach: 25 Mails seit 06-Nov-2026, 0 schon verarbeitet, 20 geholt, "
                      "5 beim nächsten Lauf.\n", out)

    def test_t4_bekannte_und_ohne_message_id(self):
        """T4: bekannte Mails nur per Kopfzeile erkannt und übersprungen; ohne Message-ID immer geholt, zählt nicht

        Nachgeschärft 07.11. (Claude): bekannt enthält auch IDs außerhalb des Fensters – gezählt werden nur die im Fenster.
        """
        mp = self.mp
        fake = FakeIMAP([roh(1), roh(2), roh(3), roh(4, mit_id=False), roh(5), roh(6)])
        with patch.object(mp.imaplib, "IMAP4_SSL", fake):
            mails, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p", since="06-Nov-2026",
                                       max_anzahl=2, bekannt={"<m1@test>", "<m2@test>", "<alt-1@test>", "<alt-2@test>"})
        self.assertEqual([m["subject"] for m in mails], ["Mail 3", "Mail 4", "Mail 5"])
        self.assertEqual(fake.voll, [3, 4, 5])
        self.assertEqual(fake.kopf, [1, 2, 3, 4, 5, 6])
        self.assertIn("Postfach: 6 Mails seit 06-Nov-2026, 2 schon verarbeitet, 3 geholt, "
                      "1 beim nächsten Lauf.\n", out)


class Verdrahtung(Basis):

    def test_t5_main_reihenfolge_und_werte(self):
        """T5: main – ungültige Einstellung vor Schlüsselbund/IMAP mit Exit 1; sonst Zeitfenster, Höchstzahl, bekannte IDs"""
        mp = self.mp
        os.environ["MAIL_MAX_JE_LAUF"] = "abc"
        fake = FakeIMAP([roh(1)])
        with patch.object(mp.imaplib, "IMAP4_SSL", fake):
            code, out, err = self.rufen(mp.main)
        self.assertEqual(code, 1)
        self.assertIn("MAIL_MAX_JE_LAUF ungültig: 'abc' (ganze Zahl ≥ 1)", err)
        self.pw_mock.assert_not_called()
        self.assertEqual(fake.suchen, [])
        os.environ["MAIL_MAX_JE_LAUF"], os.environ["MAIL_SINCE_DAYS"] = "7", "2"
        with sqlite3.connect(mp.DB_PATH) as c:
            mp.init_db(c)
            mp.mark_as_processed(c, "<alt@test>", "h")
        gesehen = {}
        with patch.object(mp, "fetch_mails", lambda *a, **k: gesehen.update(k) or []):
            code, out, err = self.rufen(mp.main)
        self.assertEqual(code, 0, err)
        self.assertEqual(gesehen.get("since"), mp.imap_datum(date.today() - timedelta(days=2)))
        self.assertEqual(gesehen.get("max_anzahl"), 7)
        self.assertEqual(gesehen.get("bekannt"), {"<alt@test>"})

    def test_t6_trockenlauf_verdrahtung(self):
        """T6: run_dry – gleiche Werte wie main, DB unverändert, Schlüsselbund-Fehler ohne Traceback mit Exit 1"""
        mp = self.mp
        with sqlite3.connect(mp.DB_PATH) as c:
            mp.init_db(c)
            mp.mark_as_processed(c, "<m1@test>", "h")
        fake = FakeIMAP([roh(1), roh(2), roh(3)])
        os.environ["MAIL_MAX_JE_LAUF"] = "1"
        with patch.object(mp.imaplib, "IMAP4_SSL", fake):
            code, out, err = self.rufen(mp.run_dry)
        self.assertEqual(code, 0, err)
        self.assertEqual(fake.suchen, [("SINCE", mp.imap_datum(date.today()))])
        self.assertEqual(fake.voll, [2])
        self.assertEqual(self.db_ids(), {"<m1@test>"})
        self.assertFalse(mp.PLAN_FILE.exists())
        self.assertEqual(len(list((self.dir / "outbox").glob("preview_*.md"))), 1)
        self.pw.stop()
        with patch.object(mp, "get_imap_password", side_effect=RuntimeError("Schlüsselbund-Eintrag 'x' nicht gefunden")):
            fake = FakeIMAP([roh(1)])
            with patch.object(mp.imaplib, "IMAP4_SSL", fake):
                code, out, err = self.rufen(mp.run_dry)
        self.pw.start()
        self.assertEqual(code, 1)
        self.assertIn("nicht gefunden", err)
        self.assertEqual(fake.suchen, [])
        os.environ["MAIL_SINCE_DAYS"] = "-2"
        code, out, err = self.rufen(mp.run_dry)
        self.assertEqual(code, 1)
        self.assertIn("MAIL_SINCE_DAYS ungültig: '-2' (ganze Zahl ≥ 0)", err)


class EndeZuEnde(Basis):

    def test_t7_nichts_geht_verloren(self):
        """T7: 5 Mails, Höchstzahl 2 – nach drei Läufen jede genau einmal in der Planung, vierter Lauf holt nichts"""
        mp = self.mp
        os.environ["MAIL_MAX_JE_LAUF"] = "2"
        fake = FakeIMAP([roh(i) for i in range(1, 6)])
        laeufe = []
        with patch.object(mp.imaplib, "IMAP4_SSL", fake):
            for _ in range(4):
                fake.voll = []
                code, out, err = self.rufen(mp.main)
                self.assertEqual(code, 0, err)
                laeufe.append(list(fake.voll))
        self.assertEqual(laeufe, [[1, 2], [3, 4], [5], []])
        plan = mp.PLAN_FILE.read_text(encoding="utf-8")
        for i in range(1, 6):
            self.assertEqual(plan.count(f"<!-- mail-id: <m{i}@test> -->"), 1, i)
        self.assertEqual(self.db_ids(), {f"<m{i}@test>" for i in range(1, 6)})
        self.assertIn("Keine neuen Mails", out)


class Einstieg(unittest.TestCase):

    def test_t8_als_skript(self):
        """T8: als Skript (--dry-run und normal) – ungültige Einstellung: Exit 1, Meldung, kein Traceback, nichts angelegt"""
        d = tempfile.mkdtemp(prefix="mail_zf_skript_")
        env = {**os.environ, "MAIL_PLAN_DIR": d, "IMAP_HOST": "127.0.0.1", "IMAP_PORT": "1",
               "MAIL_MAX_JE_LAUF": "abc", "MAIL_IMAP_KEYCHAIN_SERVICE": "lab-mail-imap-test-gibt-es-nicht"}
        env.pop("MAIL_SINCE_DAYS", None)
        for args in (["--dry-run"], []):
            r = subprocess.run([sys.executable, str(SKRIPT), *args], capture_output=True, text=True, env=env,
                               cwd=d, timeout=60)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("MAIL_MAX_JE_LAUF ungültig: 'abc' (ganze Zahl ≥ 1)", r.stderr)
            self.assertNotIn("Traceback", r.stderr)
            self.assertNotIn("Schl", r.stderr)
        self.assertEqual(sorted(os.listdir(d)), [])


if __name__ == "__main__":
    unittest.main()
