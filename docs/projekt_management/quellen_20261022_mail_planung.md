# Quellen: mail_planung

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen mail_planung` (2026-10-22 20:17, Stand `83a424d`), nach dem Abschnitt „Quellen“ in `spec_20261022_mail_planung.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `agents/llm_scout/llm_scout.py` (Zeilen 30–33) – `BASE_DIR = Path(os.getenv("LAB_DIR", Path.home() / "lab"))`; `DB_PATH = BASE_DIR / "llm_scout.db"` — Muster für `MAIL_PLAN_DIR` und `DB_PATH`

```python
30| # --- KONFIGURATION ---
31| 
32| # Pfade
33| BASE_DIR = Path(os.getenv("LAB_DIR", Path.home() / "lab"))
```

### `agents/llm_scout/llm_scout.py` def init_db (Zeilen 110–139) – SQLite-Schema `processed_items` (UNIQUE-Index auf `url`); Muster für `processed_mails` (UNIQUE auf `message_id`)

```python
110| def init_db(conn: sqlite3.Connection) -> None:
111|     """Erstellt die Tabelle, falls nicht vorhanden."""
112|     conn.execute("""
113|                   CREATE TABLE IF NOT EXISTS processed_items
114|                   (
115|                       id
116|                       INTEGER
117|                       PRIMARY
118|                       KEY
119|                       AUTOINCREMENT,
120|                       source
121|                       TEXT
122|                       NOT
123|                       NULL,
124|                       title
125|                       TEXT
126|                       NOT
127|                       NULL,
128|                       url
129|                       TEXT
130|                       UNIQUE
131|                       NOT
132|                       NULL,
133|                       processed_at
134|                       TIMESTAMP
135|                       DEFAULT
136|                       CURRENT_TIMESTAMP
137|                   )
138|                   """)
139|     conn.commit()
```

### `agents/llm_scout/llm_scout.py` def is_new_item (Zeilen 142–145) – Abfrage „schon verarbeitet?"; Muster für `is_new_mail`

```python
142| def is_new_item(conn: sqlite3.Connection, url: str) -> bool:
143|     """Prüft, ob die URL bereits verarbeitet wurde."""
144|     cursor = conn.execute("SELECT 1 FROM processed_items WHERE url=?", (url,))
145|     return cursor.fetchone() is None
```

### `agents/llm_scout/llm_scout.py` def mark_as_processed (Zeilen 148–160) – `INSERT … ON CONFLICT DO NOTHING`; Muster für `mark_as_processed`

```python
148| def mark_as_processed(conn: sqlite3.Connection, source: str, title: str, url: str) -> None:
149|     """Markiert ein Item als verarbeitet."""
150|     try:
151|         conn.execute(
152|             "INSERT INTO processed_items (source, title, url) VALUES (?, ?, ?)",
153|             (source, title, url)
154|         )
155|         conn.commit()
156|     except sqlite3.IntegrityError:
157|         pass  # Bereits vorhanden, ignorieren
158| 
159| 
160| # --- SOURCE-TAG-ZUORDNUNG (A5) ---
```

### `agents/llm_scout/llm_scout.py` def main (Zeilen 674–821) – Reihenfolge: `save_report` → `mark_as_processed`; Muster für „Eintrag steht → erst dann Marker"

```python
674| def main():
675|     # Exit-Code-Semantik:
676|     #   0 = Erfolg (inkl. "keine neuen Items")
677|     #   1 = kritischer Fehler (API-Abruf, LLM-Evaluation, DB-Fehler)
678|     #   2 = llama-server nicht erreichbar
679|     print("--- Local LLM Scout gestartet ---")
680| 
681|     # (A2) sources.json laden – vor jeglicher DB-Interaktion
682|     try:
683|         sources_config = load_sources()
684|     except SystemExit:
685|         raise  # Exit 1, keine DB-Änderung
686| 
687|     # Warnung bei 8+ GitHub-Repos (stderr), Lauf wird fortgesetzt
688|     github_repos = sources_config.get("github", [])
689|     if len(github_repos) >= 8:
690|         print(f"[WARN] {len(github_repos)} GitHub-Repos konfiguriert (>= 8). "
691|               "Das kann zu langen Abrufzeiten und großen Prompts führen.", file=sys.stderr)
692| 
693|     if not router_ready():
694|         print(f"llama-server unter {LLAMA_SERVER_URL} nicht erreichbar – nichts geholt, nichts markiert.",
695|               file=sys.stderr)
696|         sys.exit(2)
697| 
698|     try:
699|         # DB Initialisierung
700|         conn = sqlite3.connect(DB_PATH)
701|         init_db(conn)
702| 
703|         # 1. Daten holen
704|         print("Hole Daten von Hugging Face und GitHub...")
705|         hf_fetched, hf_items = fetch_hf_trending()
706| 
707|         # GitHub-Repos pro-Repo holen (aus sources.json) – Slipstream wird hier mitgeholt
708|         gh_items_by_repo: Dict[str, List[Dict[str, Any]]] = {}
709|         gh_fetched_by_repo: Dict[str, int] = {}
710|         for repo_config in github_repos:
711|             repo_name = repo_config["repo"]
712|             rss_url = repo_config["rss"]
713|             source_key = get_source_key_for_repo(repo_name)
714|             fetched_count, repo_items = fetch_github_releases_for_repo(rss_url, repo_name)
715|             gh_items_by_repo[source_key] = repo_items
716|             gh_fetched_by_repo[source_key] = fetched_count
717| 
718|         # Alle Items zusammenfassen (Slipstream ist Teil von gh_items_by_repo)
719|         all_items = list(hf_items)
720|         for source_key, repo_items in gh_items_by_repo.items():
721|             all_items.extend(repo_items)
722| 
723|         total_gh = sum(len(v) for v in gh_items_by_repo.values())
724|         print(f"Gesamt gefunden: {len(hf_items)} HF + {total_gh} GH = {len(all_items)} Items")
725| 
726|         # 2. Filtern (nur neue) – noch NICHT markieren
727|         new_items = []
728|         for item in all_items:
729|             if is_new_item(conn, item['url']):
730|                 new_items.append(item)
731|             else:
732|                 print(f"  (bereits verarbeitet) {item['title']}")
733|         print(f"Neue Items (nach DB-Abgleich): {len(new_items)}")
734| 
735|         # Neue Items pro Quelle gruppieren für das Protokoll
736|         new_by_source: Dict[str, List[Dict[str, Any]]] = {}
737|         for item in new_items:
738|             src = item.get("source", "unknown")
739|             new_by_source.setdefault(src, []).append(item)
740| 
741|         # (A1) Pro-Quellen-Protokoll bauen
742|         # fetched counts: API-Antwort VOR jeglichem Filter
743|         # after_filter counts: nach 7-Tage-Filter
744|         # new counts: nach DB-Abgleich
745|         # sent_to_llm: Items die an das LLM gesendet werden
746| 
747|         # (A4) Pro-Quellen-Selektion
748|         evaluated = select_items(new_items)
749|         evaluated_by_source: Dict[str, List[Dict[str, Any]]] = {}
750|         for item in evaluated:
751|             src = item.get("source", "unknown")
752|             evaluated_by_source.setdefault(src, []).append(item)
753| 
754|         # sent_to_llm: Liste von {url, title} pro Quelle
755|         sent_to_llm: Dict[str, List[Dict[str, Any]]] = {}
756|         for src, src_eval in evaluated_by_source.items():
757|             sent_to_llm[src] = [{"url": it["url"], "title": it["title"]} for it in src_eval]
758| 
759|         # Alle konfigurierten Quellen im Protokoll (auch leere)
760|         source_log_data: Dict[str, Dict[str, Any]] = {}
761|         source_log_data["huggingface"] = {
762|             "fetched": hf_fetched,
763|             "after_filter": len(hf_items),
764|             "new": len(new_by_source.get("huggingface", [])),
765|             "sent_to_llm": sent_to_llm.get("huggingface", [])
766|         }
767|         for repo_config in github_repos:
768|             repo_name = repo_config["repo"]
769|             source_key = get_source_key_for_repo(repo_name)
770|             source_log_data[source_key] = {
771|                 "fetched": gh_fetched_by_repo.get(source_key, 0),
772|                 "after_filter": len(gh_items_by_repo.get(source_key, [])),
773|                 "new": len(new_by_source.get(source_key, [])),
774|                 "sent_to_llm": sent_to_llm.get(source_key, [])
775|             }
776| 
777|         # (A1) Protokoll schreiben – VOR dem LLM-Aufruf
778|         write_source_run_log(BASE_DIR, source_log_data)
779|         print(f"Quellenprotokoll geschrieben: source_run_log_kw*.jsonl")
780| 
781|         # Bericht-Logik:
782|         # - Erster Lauf der Woche (Bericht existiert noch nicht):
783|         #   Immer Bericht mit allen Sektionen schreiben (auch wenn leer)
784|         # - Weiterer Lauf derselben Woche ohne neue Items:
785|         #   Nichts anhaengen, Bericht bleibt unveraendert
786|         # - Weiterer Lauf mit neuen Items:
787|         #   Wie bisher anhaengen
788|         os.makedirs(REPORT_DIR, exist_ok=True)
789|         now = datetime.now()
790|         filename = week_key_for_filename(now)
791|         filepath = REPORT_DIR / filename
792|         report_exists = filepath.exists()
793| 
794|         if not new_items and report_exists:
795|             # Kein neuer Input, Bericht existiert bereits -> nichts tun
796|             conn.close()
797|             print("Keine neuen Items und Bericht existiert bereits. Skript beendet.")
798|             sys.exit(0)
799| 
800|         # LLM aufrufen (mit allen Sektionen, auch wenn leer)
801|         print(f"Bewerte Items ({len(new_items)} neue, {len(evaluated)} fuer LLM)...")
802|         report_content = call_llm_for_evaluation(new_items, sources_config)
803| 
804|         # Bericht absichern: Jede erwartete Sektion muss im Bericht stehen
805|         report_content = secure_report_sections(report_content, evaluated, sources_config)
806| 
807|         # Bericht speichern
808|         save_report(filepath, report_content, now)
809|         print(f"Bericht gespeichert unter: {filepath}")
810| 
811|         # 5. Erst jetzt markieren – und nur, was wirklich bewertet wurde
812|         for item in evaluated:
813|             mark_as_processed(conn, item['source'], item['title'], item['url'])
814|         conn.close()
815|         print(f"Als verarbeitet markiert: {len(evaluated)} (Rest bleibt fuer die naechste Woche offen)")
816|         print("--- Skript beendet ---")
817|         sys.exit(0)
818| 
819|     except Exception as e:
820|         print(f"Kritischer Fehler: {e}", file=sys.stderr)
821|         sys.exit(1)
```

### `scripts/send_scout_email.py` def get_password (Zeilen 65–79) – `subprocess.check_output(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"])`; Muster für IMAP-Schlüsselbund-Aufruf

```python
65| def get_password() -> str:
66|     """Holt das App-Passwort aus dem macOS-Schlüsselbund."""
67|     try:
68|         password = subprocess.check_output(
69|             ["security", "find-generic-password", "-s", KEYCHAIN_SERVICE, "-w"],
70|             stderr=subprocess.PIPE,
71|         ).decode().strip()
72|         if not password:
73|             raise RuntimeError("Schlüsselbund-Eintrag ist leer")
74|         return password
75|     except subprocess.CalledProcessError as e:
76|         raise RuntimeError(
77|             f"Schlüsselbund-Eintrag '{KEYCHAIN_SERVICE}' nicht gefunden "
78|             f"(security exit code {e.returncode})"
79|         ) from e
```

### `scripts/send_scout_email.py` Textstelle „SCOUT_ALLOW_SEND“ (Zeilen 50–64) – Versand-Sperre: `SCOUT_ALLOW_SEND` als Umgebungsvariable; Muster für `MAIL_ALLOW_IMAP` (optional, falls echtes IMAP-Host ≠ 127.0.0.1 gesperrt werden soll)

```python
50| # SMTP: Default Gmail, kann per Umgebungsvariablen überschrieben werden (Test-Support)
51| SMTP_HOST = os.getenv("SCOUT_SMTP_HOST", "smtp.gmail.com")
52| LOCAL_TEST_HOSTS = {"127.0.0.1", "localhost", "::1"}   # ohne SCOUT_ALLOW_SEND erlaubt
53| # SMTP_PORT wird lazy in send_email_smtp() geparst (N2: kein Crash beim Import)
54| SENDER = "askvalentinai@gmail.com"
55| RECIPIENT = "askvalentinai@gmail.com"
56| KEYCHAIN_SERVICE = "lab-scout-smtp"
57| 
58| # Exit-Code-Semantik des Scouts (für Fehler-Mail-Meldungen)
59| EXIT_CODE_MEANINGS = {
60|     2: "llama-server nicht erreichbar (kein Server unter der konfigurierten URL)",
61|     1: "Kritischer Fehler in der Scout-Pipeline (API-Abruf, LLM-Evaluation oder DB-Fehler) – Details im Log",
62| }
63| 
64| 
```

### `scripts/send_scout_email.py` def record_sent_week (Zeilen 294–338) – atomares Schreiben: `tempfile.mkstemp` + `os.replace`; Muster für atomares Schreiben der Markdown-Planungsdatei

```python
294| def record_sent_week(lauf_nr: int) -> None:
295|     """
296|     Speichert eine Zustandszeile fuer die aktuelle ISO-KW und lauf_nr atomar.
297| 
298|     A2: Format: "{iso_year}_{iso_week:02d} {lauf_nr} {datum}"
299|     Wird erst NACH erfolgreichem SMTP-Versand aufgerufen (Nachbesserung 19.10.,
300|     wie in Kette 3): scheitert der Versand, sendet der naechste Lauf nach.
301|     Wenn dieselbe lauf_nr bereits existiert (exakter Vergleich), wird nichts geschrieben.
302| 
303|     Nutzt atomares Schreiben (Temp-Datei + os.replace).
304|     """
305|     current_key = get_current_week_key()
306|     today = datetime.now().strftime("%Y-%m-%d")
307|     new_line = f"{current_key} {lauf_nr} {today}\n"
308| 
309|     # Pruefen, ob dieselbe lauf_nr bereits im Nachweis steht (exakt, kein Praefix)
310|     if SENT_STATE_FILE.exists():
311|         if lauf_nr in _sent_lauf_nrs(SENT_STATE_FILE.read_text(encoding="utf-8"), current_key):
312|             return
313| 
314|     # Atomares Schreiben: zuerst in Temp-Datei, dann os.replace
315|     existing_content = ""
316|     if SENT_STATE_FILE.exists():
317|         existing_content = SENT_STATE_FILE.read_text(encoding="utf-8")
318| 
319|     SENT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
320| 
321|     # Temp-Datei im gleichen Verzeichnis fuer atomares replace
322|     fd, tmp_path = tempfile.mkstemp(
323|         dir=str(SENT_STATE_FILE.parent),
324|         prefix=".sent_state_",
325|         suffix=".tmp",
326|     )
327|     try:
328|         with os.fdopen(fd, "w", encoding="utf-8") as f:
329|             f.write(existing_content)
330|             f.write(new_line)
331|         os.replace(tmp_path, str(SENT_STATE_FILE))
332|     except Exception:
333|         # Bei Fehler: Temp-Datei rueckstaendig loeschen
334|         try:
335|             os.unlink(tmp_path)
336|         except OSError:
337|             pass
338|         raise
```

### `scripts/send_scout_email.py` def mode_dry_run (Zeilen 401–418) – Trockenlauf ohne SMTP, ohne Schlüsselbund, schreibt nur `.eml` nach `outbox/`; Muster für `--dry-run`

```python
401| def mode_dry_run() -> int:
402|     """Trockenlauf: Bericht finden, bauen, als .eml ablegen (kein SMTP, kein Schlüsselbund)."""
403|     report_path = find_current_report()
404|     if report_path is None:
405|         print("Keine Bericht-Datei fuer die aktuelle KW gefunden. Kein Trockenlauf.", file=sys.stderr)
406|         return 0
407| 
408|     print(f"Bericht gefunden: {report_path}")
409| 
410|     try:
411|         msg = build_email_message(report_path)
412|         eml_filename = report_path.name.replace(".md", ".eml")
413|         saved = save_email_to_file(msg, eml_filename)
414|         print(f"Trockenlauf: E-Mail abgelegt unter {saved}")
415|         return 0
416|     except Exception as e:
417|         print(f"Fehler beim Bauen der E-Mail: {e}", file=sys.stderr)
418|         return 1
```

### `config/launchd/llm_scout.plist` Textstelle „EnvironmentVariables“ (Zeilen 15–29) – `LAB_DIR` und `SCOUT_ALLOW_SEND` als launchd-Env-Vars; Muster für `MAIL_PLAN_DIR` und `IMAP_HOST` in einem späteren plist

```xml
15| 
16|     <!-- DB und Berichte im Repo statt ~/lab (Default im Code) -->
17|     <key>EnvironmentVariables</key>
18|     <dict>
19|         <key>LAB_DIR</key>
20|         <string>/Users/hans-wernereberhardt/PycharmProjects/llama-server/agents/llm_scout/data</string>
21|         <!-- Versand-Sperre: nur der launchd-Lauf darf echt senden -->
22|         <key>SCOUT_ALLOW_SEND</key>
23|         <string>1</string>
24|     </dict>
25| 
26|     <key>WorkingDirectory</key>
27|     <string>/Users/hans-wernereberhardt/PycharmProjects/llama-server</string>
28| 
29|     <key>StartCalendarInterval</key>
```

### `tests/test_scout_kw_doppelversand.py` def TestBase.setUp (Zeilen 56–89) – Mocking-Muster: `patch.object(mod, "get_password", return_value="dummy")`, `patch.object(mod.smtplib, "SMTP", …)`, `MAIL_PLAN_DIR`/`LAB_DIR` auf `tempfile.mkdtemp()`

```python
56|     def setUp(self):
57|         # Frisches temporäres Verzeichnis fuer diesen Test
58|         self.lab_dir = Path(tempfile.mkdtemp(prefix="scout_test_"))
59|         self.report_dir = self.lab_dir / "weekly-reports"
60|         self.report_dir.mkdir(parents=True, exist_ok=True)
61|         self.outbox_dir = self.lab_dir / "outbox"
62|         self.sent_state_file = self.report_dir / ".sent_state"
63| 
64|         # Module-Variablen auf das Test-LAB_DIR umlenken
65|         sme.BASE_DIR = self.lab_dir
66|         sme.REPORT_DIR = self.report_dir
67|         sme.OUTBOX_DIR = self.outbox_dir
68|         sme.SENT_STATE_FILE = self.sent_state_file
69|         sme.SMTP_HOST = "127.0.0.1"
70| 
71|         # get_password() mocken – kein echter Schlüsselbund-Zugriff
72|         self._patch_get_password = patch.object(
73|             sme, "get_password", return_value="dummy_password"
74|         )
75|         self._mock_get_password = self._patch_get_password.start()
76| 
77|         # smtplib.SMTP mocken – keine echte TCP-Verbindung
78|         self._mock_smtp_instance = MagicMock()
79|         self._mock_smtp_class = MagicMock()
80|         self._mock_smtp_class.return_value.__enter__ = MagicMock(
81|             return_value=self._mock_smtp_instance
82|         )
83|         self._mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)
84| 
85|         self._patch_smtp = patch.object(sme.smtplib, "SMTP", self._mock_smtp_class)
86|         self._patch_smtp.start()
87| 
88|         self._patch_datetime_now = None
89|         self._wk_patch = None
```

### `tests/test_scout_kw_doppelversand.py` class T9_Pipeline (Zeilen 326–461) – Pipeline-E2E mit Ersatzskripten (temporäres Verzeichnis, `subprocess.run`, `pipeline_runs.log`); Muster für einen späteren Pipeline-Test, wenn ein Shell-Wrapper existiert

```python
326| class T9_Pipeline(unittest.TestCase):
327|     """
328|     T9: Pipeline-E2E-Test mit temporarem Verzeichnis und Ersatzskripten.
329|     Scout exit 3 -> Pipeline-Log zeigt EMAIL_EXIT=3.
330|     Scout exit 2 -> Pipeline-Log zeigt SCOUT_EXIT=2.
331|     """
332| 
333|     def _make_fake_scout(self, path, exit_code):
334|         path.write_text(
335|             f'#!/usr/bin/env python3\nimport sys\nsys.exit({exit_code})\n',
336|             encoding="utf-8"
337|         )
338|         os.chmod(str(path), 0o755)
339| 
340|     def _make_fake_email(self, path, exit_code):
341|         path.write_text(
342|             f'#!/usr/bin/env python3\nimport sys\nsys.exit({exit_code})\n',
343|             encoding="utf-8"
344|         )
345|         os.chmod(str(path), 0o755)
346| 
347|     def test_t9_pipeline_scout_exit_3(self):
348|         """Scout liefert exit 3 -> Pipeline-Log zeigt EMAIL_EXIT=3."""
349|         tmp_root = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
350|         (tmp_root / "scripts").mkdir(parents=True)
351|         (tmp_root / "weekly-reports").mkdir(parents=True)
352| 
353|         # Pipeline in scripts/ – REPO_ROOT wird aus parent von scripts/ abgeleitet
354|         pipeline_src = _REPO_ROOT / "scripts" / "run_scout_pipeline.sh"
355|         pipeline_dst = tmp_root / "scripts" / "run_scout_pipeline.sh"
356|         pipeline_dst.write_text(pipeline_src.read_text(encoding="utf-8"), encoding="utf-8")
357|         os.chmod(str(pipeline_dst), 0o755)
358| 
359|         # Ersatzskripte
360|         scout = tmp_root / "agents" / "llm_scout" / "llm_scout.py"
361|         scout.parent.mkdir(parents=True, exist_ok=True)
362|         self._make_fake_scout(scout, 3)
363| 
364|         email = tmp_root / "scripts" / "send_scout_email.py"
365|         self._make_fake_email(email, 0)
366| 
367|         # Venv-Stub
368|         venv_bin = tmp_root / ".venv" / "bin"
369|         venv_bin.mkdir(parents=True, exist_ok=True)
370|         python_stub = venv_bin / "python3"
371|         python_stub.write_text(
372|             "#!/bin/bash\nexec python3 \"$@\"\n", encoding="utf-8"
373|         )
374|         os.chmod(str(python_stub), 0o755)
375| 
376|         env = os.environ.copy()
377|         env["LAB_DIR"] = str(tmp_root)
378|         result = subprocess.run(
379|             ["bash", str(pipeline_dst)],
380|             capture_output=True, text=True, env=env
381|         )
382|         # Log steht in pipeline_runs.log, nicht auf stderr
383|         pipeline_log = tmp_root / "pipeline_runs.log"
384|         self.assertTrue(
385|             pipeline_log.exists(),
386|             "pipeline_runs.log muss existieren"
387|         )
388|         log_content = pipeline_log.read_text(encoding="utf-8")
389|         self.assertIn("SCOUT_EXIT=3", log_content,
390|                        "Log muss SCOUT_EXIT=3 enthalten")
391|         self.assertIn("EMAIL_EXIT=skipped", log_content,
392|                        "Log muss EMAIL_EXIT=skipped enthalten bei Scout-Fehler")
393| 
394|     def test_t9_pipeline_email_exit_3(self):
395|         """Scout ok, send_scout_email.py liefert 3 -> Pipeline exit 3, Log EMAIL_EXIT=3.
396|         (Nachgetragen von Claude 18.10.: der Fall aus A4 war bisher ungetestet.)"""
397|         tmp_root = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
398|         (tmp_root / "scripts").mkdir(parents=True)
399|         pipeline_dst = tmp_root / "scripts" / "run_scout_pipeline.sh"
400|         pipeline_dst.write_text((_REPO_ROOT / "scripts" / "run_scout_pipeline.sh").read_text(encoding="utf-8"),
401|                                 encoding="utf-8")
402|         scout = tmp_root / "agents" / "llm_scout" / "llm_scout.py"
403|         scout.parent.mkdir(parents=True, exist_ok=True)
404|         self._make_fake_scout(scout, 0)
405|         self._make_fake_email(tmp_root / "scripts" / "send_scout_email.py", 3)
406|         venv_bin = tmp_root / ".venv" / "bin"
407|         venv_bin.mkdir(parents=True, exist_ok=True)
408|         (venv_bin / "python3").write_text(f'#!/bin/bash\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
409|         os.chmod(str(venv_bin / "python3"), 0o755)
410|         env = os.environ.copy()
411|         env["LAB_DIR"] = str(tmp_root)
412|         result = subprocess.run(["bash", str(pipeline_dst)], capture_output=True, text=True, env=env)
413|         self.assertEqual(result.returncode, 3, result.stderr)
414|         log_content = (tmp_root / "pipeline_runs.log").read_text(encoding="utf-8")
415|         self.assertIn("SCOUT_EXIT=0 EMAIL_EXIT=3", log_content)
416| 
417|     def test_t9_pipeline_scout_exit_2(self):
418|         """Scout liefert exit 2 -> Pipeline-Log zeigt SCOUT_EXIT=2."""
419|         tmp_root = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
420|         (tmp_root / "scripts").mkdir(parents=True)
421|         (tmp_root / "weekly-reports").mkdir(parents=True)
422| 
423|         pipeline_src = _REPO_ROOT / "scripts" / "run_scout_pipeline.sh"
424|         pipeline_dst = tmp_root / "scripts" / "run_scout_pipeline.sh"
425|         pipeline_dst.write_text(pipeline_src.read_text(encoding="utf-8"), encoding="utf-8")
426|         os.chmod(str(pipeline_dst), 0o755)
427| 
428|         scout = tmp_root / "agents" / "llm_scout" / "llm_scout.py"
429|         scout.parent.mkdir(parents=True, exist_ok=True)
430|         self._make_fake_scout(scout, 2)
431| 
432|         email = tmp_root / "scripts" / "send_scout_email.py"
433|         self._make_fake_email(email, 0)
434| 
435|         venv_bin = tmp_root / ".venv" / "bin"
436|         venv_bin.mkdir(parents=True, exist_ok=True)
437|         python_stub = venv_bin / "python3"
438|         python_stub.write_text(
439|             "#!/bin/bash\nexec python3 \"$@\"\n", encoding="utf-8"
440|         )
441|         os.chmod(str(python_stub), 0o755)
442| 
443|         env = os.environ.copy()
444|         env["LAB_DIR"] = str(tmp_root)
445|         result = subprocess.run(
446|             ["bash", str(pipeline_dst)],
447|             capture_output=True, text=True, env=env
448|         )
449|         pipeline_log = tmp_root / "pipeline_runs.log"
450|         self.assertTrue(
451|             pipeline_log.exists(),
452|             "pipeline_runs.log muss existieren"
453|         )
454|         log_content = pipeline_log.read_text(encoding="utf-8")
455|         self.assertIn("SCOUT_EXIT=2", log_content,
456|                        "Log muss SCOUT_EXIT=2 enthalten")
457| 
458| 
459| # =========================================================================
460| # T10: Quelltext-Pruefung llm_scout.py
461| # =========================================================================
```

### `agents/llm_scout/requirements.txt` (Zeilen 1–2) – vorhandene Abhängigkeiten: `feedparser`, `requests`. Für das Mail-Werkzeug kommt `imaplib` (Standardbibliothek) hinzu; **keine neue externe Abhängigkeit** ist geplant.

```
1| feedparser
2| requests
```

### `CLAUDE.md` Textstelle „Key environment variables“ (Zeilen 51–78) – `LAB_BIND`, `MCP_READONLY` usw.; zeigt, dass Umgebungsvariablen als Steuerungsmechanismus im Repo-Standard etabliert sind

```markdown
51| ```
52| 
53| ## Key environment variables
54| 
55| | Variable | Effect |
56| |---|---|
57| | `MCP_READONLY=0/1` | Enables/disables write+delete tools on the MCP server |
58| | `MCP_ALLOW_PYTHON=1` | Enables `run_python` tool (breaks the file sandbox — off by default) |
59| | `MCP_SCOPE_ROOT` | Root path the MCP server's scope guard enforces |
60| | `LAB_BIND=serve/tailscale/all` | Network exposure mode for the router |
61| | `HARNESS_MODEL` | Exact model ID for the harness (empty = auto-discovery, prefers Mellum) |
62| | `HARNESS_READONLY=1` | Starts the harness in read-only mode |
63| | `HARNESS_MAX_STEPS` | Tool-call loop limit (default 8) |
64| 
65| ## Health checks
66| 
67| ```bash
68| curl http://127.0.0.1:8787/mcp          # MCP-Server: 406 = running
69| curl -sI http://127.0.0.1:8080/health   # Router: 200 = running
70| ```
71| 
72| ## Architecture
73| 
74| ```
75|   Claude Desktop ──stdio──┐
76|   llama-Harness  ──stdio──┤
77|                           ├──> mcp-server/lab_mcp_server.py ──> Files + Git (scope-guarded)
78|   Web-UI (Browser) ───────┘        (port 8787, streamable-http / stdio)
```
