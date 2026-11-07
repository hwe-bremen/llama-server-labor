# Quellen: mail_zeitfenster

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen mail_zeitfenster` (2026-11-07 10:40, Stand `248942c`), nach dem Abschnitt „Quellen“ in `spec_20261106_mail_zeitfenster.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `agents/mail_planung/mail_planung.py` (Zeilen 20–75) – Importe und Konstanten (Einfügestelle für `date`, `timedelta`)

```python
20| 
21| import argparse
22| import hashlib
23| import imaplib
24| import json
25| import os
26| import sqlite3
27| import sys
28| import tempfile
29| from datetime import datetime
30| from html.parser import HTMLParser
31| from pathlib import Path
32| from typing import Any, Dict, List, Optional
33| 
34| import requests
35| 
36| # ---------------------------------------------------------------------------
37| # sys.path-Anpassung: Beim Start als Skript (__main__) sind relative Imports
38| # nicht m�glich. Dasselbe Muster wie llm_scout.py Zeilen 24-28.
39| # ---------------------------------------------------------------------------
40| _script_dir = str(Path(__file__).resolve().parent)
41| if _script_dir not in sys.path:
42|     sys.path.insert(0, _script_dir)
43| 
44| 
45| # ---------------------------------------------------------------------------
46| # KONFIGURATION (aus Quellen)
47| # ---------------------------------------------------------------------------
48| 
49| # Pfade (Muster: llm_scout.py Zeile 33)
50| MAIL_PLAN_DIR = Path(os.getenv("MAIL_PLAN_DIR", str(Path.home() / "lab")))
51| DB_PATH = MAIL_PLAN_DIR / "mail_planung.db"
52| PLAN_FILE = MAIL_PLAN_DIR / "planung.md"
53| 
54| # IMAP (Muster: send_scout_email.py Zeilen 51-56)
55| IMAP_HOST = os.getenv("IMAP_HOST", "localhost")
56| IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
57| IMAP_USER = os.getenv("IMAP_USER", "")
58| KEYCHAIN_SERVICE = os.getenv("MAIL_IMAP_KEYCHAIN_SERVICE", "lab-mail-imap")
59| MAIL_IMAP_UNENCRYPTED = os.getenv("MAIL_IMAP_UNENCRYPTED")
60| 
61| # LLM (eigene Variablen, gleiche Standardwerte wie Scout)
62| # Muster: llm_scout.py Zeilen 39, 49
63| MAIL_LLM_URL = os.getenv("MAIL_LLM_URL", "http://localhost:8080")
64| MAIL_LLM_MODEL = os.getenv("MAIL_LLM_MODEL", "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL")
65| LLM_TIMEOUT = int(os.getenv("MAIL_LLM_TIMEOUT", "120"))
66| MAIL_MAX_CHARS = int(os.getenv("MAIL_MAX_CHARS", "20000"))
67| 
68| # Projekt-Konfiguration
69| PROJECT_CONFIG_FILE = MAIL_PLAN_DIR / "mail_projects.json"
70| 
71| 
72| # ---------------------------------------------------------------------------
73| # SCHL�SSELBUND (A8) — Muster: send_scout_email.py def get_password
74| # ---------------------------------------------------------------------------
75| 
```

### `agents/mail_planung/mail_planung.py` def init_db (Zeilen 102–113) – Tabelle `processed_mails` (Spalte `message_id`)

```python
102| def init_db(conn: sqlite3.Connection) -> None:
103|     """Erstellt die Tabelle processed_mails, falls nicht vorhanden."""
104|     conn.execute("""
105|         CREATE TABLE IF NOT EXISTS processed_mails
106|         (
107|             id            INTEGER PRIMARY KEY AUTOINCREMENT,
108|             message_id    TEXT UNIQUE NOT NULL,
109|             body_hash     TEXT,
110|             processed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
111|         )
112|     """)
113|     conn.commit()
```

### `agents/mail_planung/mail_planung.py` def mark_as_processed (Zeilen 124–133) – wie Message-IDs gespeichert werden

```python
124| def mark_as_processed(conn: sqlite3.Connection, message_id: str, body_hash: str) -> None:
125|     """Markiert eine Mail als verarbeitet. INSERT ... ON CONFLICT DO NOTHING."""
126|     try:
127|         conn.execute(
128|             "INSERT INTO processed_mails (message_id, body_hash) VALUES (?, ?)",
129|             (message_id, body_hash),
130|         )
131|         conn.commit()
132|     except sqlite3.IntegrityError:
133|         pass  # Bereits vorhanden, ignorieren
```

### `agents/mail_planung/mail_planung.py` def get_message_id (Zeilen 155–167) – Message-ID wird mit `.strip()` gespeichert; ohne Header synthetisch (braucht den ganzen Text)

```python
155| def get_message_id(mail: Dict[str, Any]) -> str:
156|     """Ermittelt die Message-ID einer Mail.
157| 
158|     Bei fehlendem Header wird eine synthetische ID erzeugt
159|     (SHA-256 von Absender|Betreff|Datum|Body).
160|     """
161|     mid = mail.get("message_id", "")
162|     if mid:
163|         return mid.strip()
164|     # Synthetische ID
165|     raw = f"{mail.get('from', '')}|{mail.get('subject', '')}|{mail.get('date', '')}|{mail.get('body', '')}"
166|     synthetic = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
167|     return f"<synthetic-{synthetic}@mail-planung>"
```

### `agents/mail_planung/mail_planung.py` def fetch_mails (Zeilen 180–241) – Einbaustelle Suche, Schleife, Zusammenfassung

```python
180| def fetch_mails(host: str, port: int, user: str, password: str) -> List[Dict[str, Any]]:
181|     """Liest Mails aus dem Postfach (read-only).
182| 
183|     Verbindet sich per IMAP, �ffnet INBOX read-only, listet alle Mails
184|     und schlie�t die Verbindung. Ver�ndert das Postfach nicht.
185|     """
186|     # A5: Unverschlüsseltes IMAP nur auf ausdrücklichen Wunsch und nur für localhost
187|     if MAIL_IMAP_UNENCRYPTED == "1":
188|         if host not in ("127.0.0.1", "localhost"):
189|             print("Unverschlüsseltes IMAP wird nur für localhost unterstützt", file=sys.stderr)
190|             sys.exit(1)
191|         imap = imaplib.IMAP4(host, port)
192|     else:
193|         # Normaler Betrieb: IMAP4_SSL mit Zertifikatsprüfung
194|         imap = imaplib.IMAP4_SSL(host, port)
195|     imap.login(user, password)
196|     imap.select("INBOX", readonly=True)  # A2: read-only
197|     status, data = imap.search(None, "ALL")
198|     if status != "OK":
199|         imap.logout()
200|         return []
201| 
202|     mail_ids = data[0].split()
203|     mails: List[Dict[str, Any]] = []
204|     for mid in mail_ids:
205|         status, msg_data = imap.fetch(mid, "(RFC822)")
206|         if status != "OK":
207|             continue
208|         raw = msg_data[0][1]
209|         import email
210|         msg = email.message_from_bytes(raw)
211| 
212|         # Message-ID
213|         message_id = msg.get("Message-ID", "")
214| 
215|         # Absender
216|         from_addr = msg.get("From", "")
217| 
218|         # Betreff
219|         subject = decode_subject(msg.get("Subject", ""))
220| 
221|         # Datum
222|         date_str = msg.get("Date", "")
223| 
224|         # Textk�rper extrahieren
225|         body = extract_text(msg)
226| 
227|         mails.append({
228|             "message_id": message_id,
229|             "from": from_addr,
230|             "subject": subject,
231|             "date": date_str,
232|             "body": body,
233|         })
234| 
235|     imap.logout()
236|     return mails
237| 
238| 
239| # ---------------------------------------------------------------------------
240| # TEXT-EXTRAKTION (A9) — HTML per html.parser, Umlaute, Anhang ignorieren
241| # ---------------------------------------------------------------------------
```

### `agents/mail_planung/mail_planung.py` def run_dry (Zeilen 748–782) – Einbaustelle Trockenlauf

```python
748| def run_dry() -> int:
749|     """Trockenlauf: Mails holen, auswerten, Preview schreiben.
750| 
751|     Keine �nderung der Planungsdatei, keine DB-�nderung,
752|     keine IMAP-Write-Befehle.
753|     """
754|     password = get_imap_password()
755| 
756|     try:
757|         mails = fetch_mails(IMAP_HOST, IMAP_PORT, IMAP_USER, password)
758|     except Exception as e:
759|         print(f"IMAP-Verbindung fehlgeschlagen: {e}", file=sys.stderr)
760|         return 1
761| 
762|     if not mails:
763|         print("Keine neuen Mails")
764|         return 0
765| 
766|     # DB nur lesen (f�r Dedup-Pr�fung)
767|     conn = sqlite3.connect(DB_PATH)
768|     try:
769|         init_db(conn)
770|         exit_code = 0
771|         for mail in mails:
772|             result = process_mail(conn, mail, dry_run=True)
773|             if result != 0:
774|                 exit_code = result
775|         return exit_code
776|     finally:
777|         conn.close()
778| 
779| 
780| # ---------------------------------------------------------------------------
781| # MAIN (A6) — Reihenfolge analog llm_scout.py main
782| # ---------------------------------------------------------------------------
```

### `agents/mail_planung/mail_planung.py` def main (Zeilen 784–831) – Einbaustelle Normallauf

```python
784| def main() -> int:
785|     """Hauptfunktion: Mails holen, auswerten, Planungsdatei aktualisieren.
786| 
787|     Reihenfolge:
788|     1. Passwort holen
789|     2. Mails f�r IMAP
790|     3. DB initialisieren
791|     4. Pro Mail: LLM -> Block -> atomar schreiben -> pr�fen -> markieren
792| 
793|     Gibt Exit-Code zur�ck (0 = Erfolg, 1 = Fehler).
794|     """
795|     # 1. Passwort aus Schl�sselbund (A8)
796|     try:
797|         password = get_imap_password()
798|     except RuntimeError as e:
799|         print(f"{e}", file=sys.stderr)
800|         return 1
801| 
802|     # 2. Mails holen (A2)
803|     try:
804|         mails = fetch_mails(IMAP_HOST, IMAP_PORT, IMAP_USER, password)
805|     except Exception as e:
806|         print(f"IMAP-Verbindung fehlgeschlagen: {e}", file=sys.stderr)
807|         return 1
808| 
809|     if not mails:
810|         print("Keine neuen Mails")
811|         return 0
812| 
813|     # 3. DB initialisieren
814|     conn = sqlite3.connect(DB_PATH)
815|     try:
816|         init_db(conn)
817| 
818|         exit_code = 0
819|         for mail in mails:
820|             result = process_mail(conn, mail)
821|             if result != 0:
822|                 exit_code = result
823| 
824|         return exit_code
825|     finally:
826|         conn.close()
827| 
828| 
829| # ---------------------------------------------------------------------------
830| # EINSTIEGSPUNKT
831| # ---------------------------------------------------------------------------
```

### `tests/test_mail_planung.py` (Zeilen 37–90) – Bestand-Testaufbau (Modul neu laden, Pfade umbiegen, Attrappen)

```python
37| class TestMailPlanungBase(unittest.TestCase):
38|     """Gemeinsamer Testaufbau fuer mail_planung-Tests."""
39| 
40|     def setUp(self):
41|         # Frisches temporares Verzeichnis fuer jeden Test
42|         self.plan_dir = Path(tempfile.mkdtemp(prefix="mail_plan_test_"))
43|         os.environ["MAIL_PLAN_DIR"] = str(self.plan_dir)
44| 
45|         # Modul neu importieren, damit die Umgebungsvariablen greifen
46|         if "agents.mail_planung.mail_planung" in sys.modules:
47|             del sys.modules["agents.mail_planung.mail_planung"]
48|         if "mail_planung" in sys.modules:
49|             del sys.modules["mail_planung"]
50| 
51|         from agents.mail_planung import mail_planung as mp
52|         self.mp = mp
53| 
54|         # Module-Variablen auf Test-DIR umlenken
55|         self.mp.MAIL_PLAN_DIR = self.plan_dir
56|         self.mp.DB_PATH = self.plan_dir / "mail_planung.db"
57|         self.mp.PLAN_FILE = self.plan_dir / "planung.md"
58|         self.mp.PROJECT_CONFIG_FILE = self.plan_dir / "mail_projects.json"
59| 
60|         # get_imap_password mocken - kein echter Schlusselbund-Zugriff
61|         self._patch_get_password = patch.object(
62|             self.mp, "get_imap_password", return_value="dummy_password"
63|         )
64|         self._mock_get_password = self._patch_get_password.start()
65| 
66|         # LLM-Call mocken
67|         self._default_llm_result = {
68|             "projekt": "TestProjekt",
69|             "aufgaben": ["Testaufgabe"],
70|             "termine": ["2026-10-25: Teammeeting"],
71|             "entscheidungen": ["Testentscheidung"],
72|             "offene_fragen": ["Testfrage"],
73|         }
74|         self._mock_response = MagicMock()
75|         self._mock_response.json.return_value = {
76|             "choices": [{"message": {"content": json.dumps(self._default_llm_result)}}]
77|         }
78|         self._mock_response.raise_for_status = MagicMock()
79| 
80|         self._patch_requests = patch.object(
81|             self.mp.requests, "post", return_value=self._mock_response
82|         )
83|         self._mock_requests_post = self._patch_requests.start()
84| 
85|         # DB initialisieren
86|         self.conn = sqlite3.connect(self.mp.DB_PATH)
87|         self.mp.init_db(self.conn)
88| 
89|     def tearDown(self):
90|         self.conn.close()
```

### `tests/test_mail_zeitfenster.py` (Zeilen 1–313) – Vorgabe-Tests (`FakeIMAP`, Meldetexte wörtlich übernehmen)

```python
  1| #!/usr/bin/env python3
  2| """Vorgabe-Tests fuer mail_zeitfenster (spec_20261106_mail_zeitfenster.md, T1–T8).
  3| 
  4| VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.
  5| 
  6| Keine Aussenwirkung: MAIL_PLAN_DIR je Test in tempfile.mkdtemp(); imaplib.IMAP4_SSL durch FakeIMAP ersetzt (nur
  7| erfundene Mails, kein Netz); get_imap_password und requests.post durch Attrappen ersetzt (kein Schluesselbund,
  8| kein Modell). T8 startet das Skript in einem Unterprozess mit ungueltiger Einstellung – es endet vor Schluesselbund,
  9| DB und IMAP. Neue Funktionen werden in jeder Methode ueber self.mp angesprochen (rot vorab).
 10| """
 11| import io
 12| import json
 13| import os
 14| import sqlite3
 15| import subprocess
 16| import sys
 17| import tempfile
 18| import unittest
 19| from contextlib import redirect_stderr, redirect_stdout
 20| from datetime import date, timedelta
 21| from email.message import EmailMessage
 22| from pathlib import Path
 23| from unittest.mock import MagicMock, patch
 24| 
 25| _REPO = Path(__file__).resolve().parent.parent
 26| sys.path.insert(0, str(_REPO))
 27| sys.path.insert(0, str(_REPO / "agents" / "mail_planung"))
 28| os.environ.setdefault("MAIL_PLAN_DIR", tempfile.mkdtemp(prefix="mail_zf_"))
 29| os.environ["IMAP_HOST"] = "127.0.0.1"
 30| os.environ["IMAP_PORT"] = "993"
 31| os.environ["IMAP_USER"] = "test@example.com"
 32| SKRIPT = _REPO / "agents" / "mail_planung" / "mail_planung.py"
 33| 
 34| 
 35| def roh(nr: int, mit_id: bool = True) -> bytes:
 36|     m = EmailMessage()
 37|     m["From"] = "absender@example.com"
 38|     m["Subject"] = f"Mail {nr}"
 39|     m["Date"] = "Fri, 06 Nov 2026 08:00:00 +0100"
 40|     if mit_id:
 41|         m["Message-ID"] = f"<m{nr}@test>"
 42|     m.set_content(f"Inhalt der Mail {nr}")
 43|     return bytes(m)
 44| 
 45| 
 46| class FakeIMAP:
 47|     """Ersatz fuer imaplib.IMAP4_SSL: Postfach aus erfundenen Mails, zeichnet Aufrufe auf."""
 48| 
 49|     def __init__(self, mails: list[bytes]):
 50|         self.mails = mails
 51|         self.suchen: list[tuple] = []
 52|         self.voll: list[int] = []
 53|         self.kopf: list[int] = []
 54|         self.select_args = None
 55| 
 56|     def __call__(self, host, port):
 57|         return self
 58| 
 59|     def login(self, user, pw):
 60|         return "OK", [b""]
 61| 
 62|     def select(self, box, readonly=False):
 63|         self.select_args = (box, readonly)
 64|         return "OK", [str(len(self.mails)).encode()]
 65| 
 66|     def search(self, charset, *kriterien):
 67|         self.suchen.append(kriterien)
 68|         return "OK", [" ".join(str(i + 1) for i in range(len(self.mails))).encode()]
 69| 
 70|     def fetch(self, mid, teile):
 71|         i = int(mid)
 72|         raw = self.mails[i - 1]
 73|         if "HEADER.FIELDS" in teile:
 74|             self.kopf.append(i)
 75|             kopf = b"".join(z + b"\n" for z in raw.split(b"\n") if z.lower().startswith(b"message-id:")) + b"\r\n"
 76|             return "OK", [(f"{i} (BODY[HEADER.FIELDS (MESSAGE-ID)] {{{len(kopf)}}}".encode(), kopf), b")"]
 77|         if "RFC822" in teile or "BODY[]" in teile or "BODY.PEEK[]" in teile:
 78|             self.voll.append(i)
 79|             return "OK", [(f"{i} (RFC822 {{{len(raw)}}}".encode(), raw), b")"]
 80|         return "NO", [b""]
 81| 
 82|     def logout(self):
 83|         return "BYE", [b""]
 84| 
 85| 
 86| class Basis(unittest.TestCase):
 87|     def setUp(self):
 88|         self.dir = Path(tempfile.mkdtemp(prefix="mail_zf_"))
 89|         for name in ("agents.mail_planung.mail_planung", "mail_planung"):
 90|             sys.modules.pop(name, None)
 91|         from agents.mail_planung import mail_planung as mp
 92|         self.mp = mp
 93|         mp.MAIL_PLAN_DIR = self.dir
 94|         mp.DB_PATH = self.dir / "mail_planung.db"
 95|         mp.PLAN_FILE = self.dir / "planung.md"
 96|         mp.PROJECT_CONFIG_FILE = self.dir / "mail_projects.json"
 97|         self.pw = patch.object(mp, "get_imap_password", return_value="dummy")
 98|         self.pw_mock = self.pw.start()
 99|         self.addCleanup(self.pw.stop)
100|         antwort = MagicMock()
101|         antwort.json.return_value = {"choices": [{"message": {"content": json.dumps(
102|             {"projekt": "P", "aufgaben": ["a"], "termine": ["2026-11-07: x"], "entscheidungen": [],
103|              "offene_fragen": []})}}]}
104|         antwort.raise_for_status = MagicMock()
105|         self.post = patch.object(mp.requests, "post", return_value=antwort)
106|         self.post.start()
107|         self.addCleanup(self.post.stop)
108|         self.env = patch.dict(os.environ, {}, clear=False)
109|         self.env.start()
110|         self.addCleanup(self.env.stop)
111|         os.environ.pop("MAIL_SINCE_DAYS", None)
112|         os.environ.pop("MAIL_MAX_JE_LAUF", None)
113| 
114|     def rufen(self, fn, *a, **k):
115|         aus, err = io.StringIO(), io.StringIO()
116|         with redirect_stdout(aus), redirect_stderr(err):
117|             code = fn(*a, **k)
118|         return code, aus.getvalue(), err.getvalue()
119| 
120|     def db_ids(self) -> set:
121|         if not self.mp.DB_PATH.exists():
122|             return set()
123|         with sqlite3.connect(self.mp.DB_PATH) as c:
124|             try:
125|                 return {r[0] for r in c.execute("SELECT message_id FROM processed_mails")}
126|             except sqlite3.OperationalError:
127|                 return set()
128| 
129| 
130| class Einstellungen(Basis):
131| 
132|     def test_t1_zeitfenster_und_imap_datum(self):
133|         """T1: Standardwerte 0/20, gültige und ungültige Werte, IMAP-Datum unabhängig von der Locale"""
134|         mp = self.mp
135|         self.assertEqual(mp.zeitfenster(), (0, 20))
136|         os.environ["MAIL_SINCE_DAYS"], os.environ["MAIL_MAX_JE_LAUF"] = " 3 ", "5"
137|         self.assertEqual(mp.zeitfenster(), (3, 5))
138|         for name, wert, minimum in (("MAIL_SINCE_DAYS", "-1", 0), ("MAIL_SINCE_DAYS", "heute", 0),
139|                                     ("MAIL_MAX_JE_LAUF", "0", 1), ("MAIL_MAX_JE_LAUF", "abc", 1),
140|                                     ("MAIL_MAX_JE_LAUF", "2.5", 1)):
141|             os.environ["MAIL_SINCE_DAYS"], os.environ["MAIL_MAX_JE_LAUF"] = "0", "20"
142|             os.environ[name] = wert
143|             with self.assertRaises(ValueError) as ctx:
144|                 mp.zeitfenster()
145|             self.assertEqual(str(ctx.exception), f"{name} ungültig: '{wert}' (ganze Zahl ≥ {minimum})")
146|         class KeinStrftime(date):
147|             def strftime(self, fmt):
148|                 raise AssertionError("strftime hängt von der Locale ab (Mai/Dez statt May/Dec)")
149| 
150|             def __format__(self, fmt):
151|                 if fmt:
152|                     raise AssertionError("Datumsformat hängt von der Locale ab")
153|                 return super().__format__(fmt)
154|         self.assertEqual(mp.imap_datum(KeinStrftime(2026, 5, 1)), "01-May-2026")
155|         self.assertEqual(mp.imap_datum(KeinStrftime(2026, 12, 9)), "09-Dec-2026")
156|         import locale
157|         alt = locale.setlocale(locale.LC_TIME)
158|         for loc in ("de_DE.UTF-8", "de_DE.utf8", "de_DE"):
159|             try:
160|                 locale.setlocale(locale.LC_TIME, loc)
161|                 break
162|             except locale.Error:
163|                 continue
164|         try:
165|             self.assertEqual(mp.imap_datum(date(2026, 11, 6)), "06-Nov-2026")
166|             self.assertEqual(mp.imap_datum(date(2026, 5, 1)), "01-May-2026")
167|             self.assertEqual(mp.imap_datum(date(2027, 3, 31)), "31-Mar-2027")
168|             self.assertEqual(mp.imap_datum(date(2026, 12, 9)), "09-Dec-2026")
169|         finally:
170|             locale.setlocale(locale.LC_TIME, alt)
171| 
172| 
173| class Abruf(Basis):
174| 
175|     def test_t2_suche_since_und_bestand(self):
176|         """T2: fetch_mails sucht mit SINCE; ohne since wie bisher ALL und alles (Bestand-Aufruf)"""
177|         mp = self.mp
178|         fake = FakeIMAP([roh(1), roh(2), roh(3)])
179|         with patch.object(mp.imaplib, "IMAP4_SSL", fake):
180|             _, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p", since="06-Nov-2026")
181|         self.assertEqual(fake.suchen, [("SINCE", "06-Nov-2026")])
182|         self.assertEqual(fake.select_args, ("INBOX", True))
183|         fake = FakeIMAP([roh(1), roh(2), roh(3)])
184|         with patch.object(mp.imaplib, "IMAP4_SSL", fake):
185|             code, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p")
186|         self.assertEqual(fake.suchen, [("ALL",)])
187|         self.assertEqual([m["subject"] for m in code], ["Mail 1", "Mail 2", "Mail 3"])
188|         self.assertEqual(fake.voll, [1, 2, 3])
189| 
190|     def test_t3_hoechstzahl_aelteste_zuerst(self):
191|         """T3: höchstens max_anzahl neue Mails vollständig, älteste zuerst, Zusammenfassung mit Rest"""
192|         mp = self.mp
193|         fake = FakeIMAP([roh(i) for i in range(1, 26)])
194|         with patch.object(mp.imaplib, "IMAP4_SSL", fake):
195|             mails, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p", since="06-Nov-2026",
196|                                        max_anzahl=20, bekannt=set())
197|         self.assertEqual([m["subject"] for m in mails], [f"Mail {i}" for i in range(1, 21)])
198|         self.assertEqual(fake.voll, list(range(1, 21)))
199|         self.assertIn("Postfach: 25 Mails seit 06-Nov-2026, 0 schon verarbeitet, 20 geholt, "
200|                       "5 beim nächsten Lauf.\n", out)
201| 
202|     def test_t4_bekannte_und_ohne_message_id(self):
203|         """T4: bekannte Mails nur per Kopfzeile erkannt und übersprungen; ohne Message-ID immer geholt, zählt nicht"""
204|         mp = self.mp
205|         fake = FakeIMAP([roh(1), roh(2), roh(3), roh(4, mit_id=False), roh(5), roh(6)])
206|         with patch.object(mp.imaplib, "IMAP4_SSL", fake):
207|             mails, out, _ = self.rufen(mp.fetch_mails, "127.0.0.1", 993, "u", "p", since="06-Nov-2026",
208|                                        max_anzahl=2, bekannt={"<m1@test>", "<m2@test>"})
209|         self.assertEqual([m["subject"] for m in mails], ["Mail 3", "Mail 4", "Mail 5"])
210|         self.assertEqual(fake.voll, [3, 4, 5])
211|         self.assertEqual(fake.kopf, [1, 2, 3, 4, 5, 6])
212|         self.assertIn("Postfach: 6 Mails seit 06-Nov-2026, 2 schon verarbeitet, 3 geholt, "
213|                       "1 beim nächsten Lauf.\n", out)
214| 
215| 
216| class Verdrahtung(Basis):
217| 
218|     def test_t5_main_reihenfolge_und_werte(self):
219|         """T5: main – ungültige Einstellung vor Schlüsselbund/IMAP mit Exit 1; sonst Zeitfenster, Höchstzahl, bekannte IDs"""
220|         mp = self.mp
221|         os.environ["MAIL_MAX_JE_LAUF"] = "abc"
222|         fake = FakeIMAP([roh(1)])
223|         with patch.object(mp.imaplib, "IMAP4_SSL", fake):
224|             code, out, err = self.rufen(mp.main)
225|         self.assertEqual(code, 1)
226|         self.assertIn("MAIL_MAX_JE_LAUF ungültig: 'abc' (ganze Zahl ≥ 1)", err)
227|         self.pw_mock.assert_not_called()
228|         self.assertEqual(fake.suchen, [])
229|         os.environ["MAIL_MAX_JE_LAUF"], os.environ["MAIL_SINCE_DAYS"] = "7", "2"
230|         with sqlite3.connect(mp.DB_PATH) as c:
231|             mp.init_db(c)
232|             mp.mark_as_processed(c, "<alt@test>", "h")
233|         gesehen = {}
234|         with patch.object(mp, "fetch_mails", lambda *a, **k: gesehen.update(k) or []):
235|             code, out, err = self.rufen(mp.main)
236|         self.assertEqual(code, 0, err)
237|         self.assertEqual(gesehen.get("since"), mp.imap_datum(date.today() - timedelta(days=2)))
238|         self.assertEqual(gesehen.get("max_anzahl"), 7)
239|         self.assertEqual(gesehen.get("bekannt"), {"<alt@test>"})
240| 
241|     def test_t6_trockenlauf_verdrahtung(self):
242|         """T6: run_dry – gleiche Werte wie main, DB unverändert, Schlüsselbund-Fehler ohne Traceback mit Exit 1"""
243|         mp = self.mp
244|         with sqlite3.connect(mp.DB_PATH) as c:
245|             mp.init_db(c)
246|             mp.mark_as_processed(c, "<m1@test>", "h")
247|         fake = FakeIMAP([roh(1), roh(2), roh(3)])
248|         os.environ["MAIL_MAX_JE_LAUF"] = "1"
249|         with patch.object(mp.imaplib, "IMAP4_SSL", fake):
250|             code, out, err = self.rufen(mp.run_dry)
251|         self.assertEqual(code, 0, err)
252|         self.assertEqual(fake.suchen, [("SINCE", mp.imap_datum(date.today()))])
253|         self.assertEqual(fake.voll, [2])
254|         self.assertEqual(self.db_ids(), {"<m1@test>"})
255|         self.assertFalse(mp.PLAN_FILE.exists())
256|         self.assertEqual(len(list((self.dir / "outbox").glob("preview_*.md"))), 1)
257|         self.pw.stop()
258|         with patch.object(mp, "get_imap_password", side_effect=RuntimeError("Schlüsselbund-Eintrag 'x' nicht gefunden")):
259|             fake = FakeIMAP([roh(1)])
260|             with patch.object(mp.imaplib, "IMAP4_SSL", fake):
261|                 code, out, err = self.rufen(mp.run_dry)
262|         self.pw.start()
263|         self.assertEqual(code, 1)
264|         self.assertIn("nicht gefunden", err)
265|         self.assertEqual(fake.suchen, [])
266|         os.environ["MAIL_SINCE_DAYS"] = "-2"
267|         code, out, err = self.rufen(mp.run_dry)
268|         self.assertEqual(code, 1)
269|         self.assertIn("MAIL_SINCE_DAYS ungültig: '-2' (ganze Zahl ≥ 0)", err)
270| 
271| 
272| class EndeZuEnde(Basis):
273| 
274|     def test_t7_nichts_geht_verloren(self):
275|         """T7: 5 Mails, Höchstzahl 2 – nach drei Läufen jede genau einmal in der Planung, vierter Lauf holt nichts"""
276|         mp = self.mp
277|         os.environ["MAIL_MAX_JE_LAUF"] = "2"
278|         fake = FakeIMAP([roh(i) for i in range(1, 6)])
279|         laeufe = []
280|         with patch.object(mp.imaplib, "IMAP4_SSL", fake):
281|             for _ in range(4):
282|                 fake.voll = []
283|                 code, out, err = self.rufen(mp.main)
284|                 self.assertEqual(code, 0, err)
285|                 laeufe.append(list(fake.voll))
286|         self.assertEqual(laeufe, [[1, 2], [3, 4], [5], []])
287|         plan = mp.PLAN_FILE.read_text(encoding="utf-8")
288|         for i in range(1, 6):
289|             self.assertEqual(plan.count(f"<!-- mail-id: <m{i}@test> -->"), 1, i)
290|         self.assertEqual(self.db_ids(), {f"<m{i}@test>" for i in range(1, 6)})
291|         self.assertIn("Keine neuen Mails", out)
292| 
293| 
294| class Einstieg(unittest.TestCase):
295| 
296|     def test_t8_als_skript(self):
297|         """T8: als Skript (--dry-run und normal) – ungültige Einstellung: Exit 1, Meldung, kein Traceback, nichts angelegt"""
298|         d = tempfile.mkdtemp(prefix="mail_zf_skript_")
299|         env = {**os.environ, "MAIL_PLAN_DIR": d, "IMAP_HOST": "127.0.0.1", "IMAP_PORT": "1",
300|                "MAIL_MAX_JE_LAUF": "abc", "MAIL_IMAP_KEYCHAIN_SERVICE": "lab-mail-imap-test-gibt-es-nicht"}
301|         env.pop("MAIL_SINCE_DAYS", None)
302|         for args in (["--dry-run"], []):
303|             r = subprocess.run([sys.executable, str(SKRIPT), *args], capture_output=True, text=True, env=env,
304|                                cwd=d, timeout=60)
305|             self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
306|             self.assertIn("MAIL_MAX_JE_LAUF ungültig: 'abc' (ganze Zahl ≥ 1)", r.stderr)
307|             self.assertNotIn("Traceback", r.stderr)
308|             self.assertNotIn("Schl", r.stderr)
309|         self.assertEqual(sorted(os.listdir(d)), [])
310| 
311| 
312| if __name__ == "__main__":
313|     unittest.main()
```
