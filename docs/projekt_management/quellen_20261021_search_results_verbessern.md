# Quellen: search_results_verbessern

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen search_results_verbessern` (2026-10-21 12:45, Stand `4522651`), nach dem Abschnitt „Quellen“ in `spec_20261021_search_results_verbessern.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `agents/llm_scout/llm_scout.py` (Zeilen 33–46) – `LLAMA_SERVER_URL`, `HF_API_URL`, `GITHUB_RELEASES_RSS`, `MODEL_NAME`, `LOOKBACK_DAYS`: Bestehende Konstanten, die die neue `sources.json`-Logik ergänzen, nicht ersetzen.

```python
33| 
34| # API Endpunkte
35| LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://localhost:8080")
36| HF_API_URL = "https://huggingface.co/api/models"
37| GITHUB_RELEASES_RSS = [
38|     "https://github.com/ggml-org/llama.cpp/releases.atom",
39|     "https://github.com/ollama/ollama/releases.atom",
40|     "https://github.com/huggingface/transformers/releases.atom"
41| ]
42| 
43| # Modell Konfiguration
44| # Wir nutzen das von dir genannte Modell. Falls es nicht läuft, fallback auf Qwen2.5-14B
45| MODEL_NAME = os.getenv("SCOUT_MODEL", "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL")
46| 
```

### `agents/llm_scout/llm_scout.py` def fetch_hf_trending (Zeilen 103–150) – HF-API-Aufruf und Filterlogik. Unverändert. Die Funktion liefert eine Liste von `Dict` mit Keys `source`, `title`, `url`, `summary`, `likes`.

```python
103| def fetch_hf_trending() -> List[Dict[str, Any]]:
104|     """
105|     Holt trending Modelle von Hugging Face.
106|     Filtert nach GGUF, sortiert nach Likes. Nimmt Modelle die
107|     neu sind (<30 Tage) ODER viele Downloads haben (>1000).
108|     """
109|     items = []
110|     try:
111|         params = {
112|             "sort": "likes",
113|             "direction": "-1",
114|             "limit": 50,
115|             "filter": "gguf"
116|         }
117|         response = requests.get(HF_API_URL, params=params, timeout=10)
118|         response.raise_for_status()
119|         models = response.json()
120| 
121|         now = datetime.now(tz=__import__('datetime').timezone.utc)
122|         cutoff = now - timedelta(days=30)
123| 
124|         for model in models:
125|             created = model.get("createdAt", "")
126|             likes = model.get("likes", 0)
127|             downloads = model.get("downloads", 0)
128| 
129|             # Kriterium: neu ODER populär genug
130|             is_new = False
131|             if created:
132|                 try:
133|                     created_dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
134|                     is_new = created_dt > cutoff
135|                 except Exception:
136|                     pass
137| 
138|             if is_new or downloads > 1000:
139|                 items.append({
140|                     "source": "huggingface",
141|                     "title": model["id"],
142|                     "url": f"https://huggingface.co/{model['id']}",
143|                     "summary": f"Likes: {likes}, Downloads: {downloads}, Tags: {', '.join(model['tags'][:5])}",
144|                     "likes": likes
145|                 })
146|     except Exception as e:
147|         print(f"Fehler beim Abrufen von Hugging Face: {e}", file=sys.stderr)
148| 
149|     items.sort(key=lambda x: x.get("likes", 0), reverse=True)
150|     return items
```

### `agents/llm_scout/llm_scout.py` def fetch_github_releases (Zeilen 153–187) – RSS-Abruf und Filterlogik. Unverändert in der Kernlogik, aber wird um die pro-Repo-Differenzierung erweitert (jedes Repo wird separat geloggt).

```python
153| def fetch_github_releases() -> List[Dict[str, Any]]:
154|     """
155|     Holt neue Releases von GitHub Repositories via RSS.
156|     """
157|     items = []
158|     cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)
159| 
160|     for rss_url in GITHUB_RELEASES_RSS:
161|         try:
162|             # Abruf ueber requests (nutzt certifi): feedparser/urllib scheitert mit dem
163|             # python.org-Python auf macOS an der Zertifikatspruefung -> still 0 Eintraege.
164|             resp = requests.get(rss_url, timeout=15, headers={"User-Agent": "llm-scout-lab/1.0"})
165|             resp.raise_for_status()
166|             feed = feedparser.parse(resp.content)
167|             if feed.bozo and not feed.entries:
168|                 print(f"  WARNUNG {rss_url}: Feed nicht lesbar ({feed.get('bozo_exception')})", file=sys.stderr)
169|             print(f"  RSS {rss_url}: {len(feed.entries)} Einträge (cutoff: {cutoff_date.strftime('%Y-%m-%d')})")
170|             for entry in feed.entries:
171|                 # Datum prüfen – updated_parsed ist time.struct_time (UTC)
172|                 updated_parsed = getattr(entry, 'updated_parsed', None)
173|                 if updated_parsed:
174|                     updated_dt = datetime(*updated_parsed[:6])
175|                     if updated_dt > cutoff_date:
176|                         items.append({
177|                             "source": "github",
178|                             "title": entry.title,
179|                             "url": entry.link,
180|                             "summary": entry.summary[:200] + "..." if len(entry.summary) > 200 else entry.summary
181|                         })
182|                 else:
183|                     print(f"    (kein Datum) {entry.title}")
184|         except Exception as e:
185|             print(f"Fehler beim Abrufen von {rss_url}: {e}", file=sys.stderr)
186| 
187|     return items
```

### `agents/llm_scout/llm_scout.py` def select_items (Zeilen 190–195) – Auswahl der Top-3 pro Quelle für den LLM-Prompt. Wird geändert: pro-Quellen-Selektion, keine globale Top-3 über alle Quellen.

```python
190| def select_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
191|     """Was tatsaechlich bewertet wird: Top 3 HF + Top 3 GitHub (Kontext sparen).
192|     Nur diese Items werden nach einem gespeicherten Bericht als verarbeitet markiert."""
193|     hf = [i for i in items if i['source'] == 'huggingface'][:3]
194|     gh = [i for i in items if i['source'] == 'github'][:3]
195|     return hf + gh
```

### `agents/llm_scout/llm_scout.py` def call_llm_for_evaluation (Zeilen 206–292) – LLM-Aufruf. System-Prompt und User-Prompt werden geändert (getrennte Sektionen, pro-Quellen-Präsentation, Verworf-Logik sichtbar).

```python
206| def call_llm_for_evaluation(items: List[Dict[str, Any]]) -> str:
207|     """
208|     Sendet die Liste der neuen Items an llama-server zur Bewertung.
209|     """
210|     if not items:
211|         return "Keine neuen relevanten Entwicklungen gefunden."
212| 
213|     # Prompt Konstruktion
214|     system_prompt = """
215|     Du bist ein Experte für lokale LLM-Infrastruktur (llama.cpp, Ollama, GGUF).
216|     Deine Aufgabe ist es, eine Liste neuer Modell-Releases und Tool-Updates zu bewerten.
217| 
218|     Kriterien für Relevanz:
219|     1. Modellgröße: Ideal < 15GB in Q4_K_M Quantisierung (passend für M4 Mac mit 48GB RAM).
220|     2. Kompatibilität: Muss GGUF unterstützen oder für llama.cpp/Ollama tauglich sein.
221|     3. Leistung: Zeigt es signifikante Verbesserungen in Benchmarks (MMLU, GPQA, etc.)?
222|     4. Lizenz: Open Source (Apache 2.0, MIT, etc.) bevorzugt.
223|     5. Sprache: Deutsch-Unterstützung ist ein Bonus.
224| 
225|     Gib die Top 3-5 interessantesten Entwicklungen zurück.
226|     Wenn es nur kleine Bugfixes sind, ignoriere sie.
227| 
228|     Ausgabeformat:
229|     # LLM Scout Weekly
230| 
231|     ## Top Modelle
232|     - **[Modellname](Link)**: Kurze Begründung (Größe, Leistung, Sprache).
233| 
234|     ## Tool Updates
235|     - **[Toolname](Link)**: Wichtige neue Features.
236| 
237|     ## Fazit
238|     Ein Satz zusammenfassend, ob sich ein Update lohnt.
239|     """
240| 
241|     # Items für den Prompt vorbereiten (max 10 Items, um Kontext zu sparen)
242|     # Wir nehmen die Top 3 HF und Top 3 GH
243|     relevant_items = select_items(items)
244| 
245|     items_text = "\n".join([
246|         f"- Source: {i['source']}, Title: {i['title']}, URL: {i['url']}, Summary: {i['summary']}"
247|         for i in relevant_items
248|     ])
249| 
250|     user_prompt = f"""
251|     Hier sind die neuen Entwicklungen der letzten Woche:
252| 
253|     {items_text}
254| 
255|     Bitte bewerte diese und erstelle das Infopaper.
256|     """
257| 
258|     # API Call an llama-server
259|     # Wir nutzen das OpenAI-kompatible Format, da es am weitesten verbreitet ist in llama.cpp
260|     payload = {
261|         "model": MODEL_NAME,
262|         "messages": [
263|             {"role": "system", "content": system_prompt},
264|             {"role": "user", "content": user_prompt}
265|         ],
266|         "temperature": 0.2,
267|         "max_tokens": 4096,
268|         "stream": False,
269|         # Qwen3.x denkt sonst ins max_tokens-Budget hinein -> leerer content
270|         "chat_template_kwargs": {"enable_thinking": False}
271|     }
272| 
273|     try:
274|         print(f"Frage wird an LLM ({MODEL_NAME}) gestellt...")
275|         response = requests.post(
276|             f"{LLAMA_SERVER_URL}/v1/chat/completions",
277|             json=payload,
278|             timeout=120
279|         )
280|         print(f"  HTTP-Status: {response.status_code}")
281|         if response.status_code != 200:
282|             print(f"  Antwort: {response.text[:500]}")
283|         response.raise_for_status()
284|         result = response.json()
285|         print(f"  Roh-JSON: {json.dumps(result, indent=2)[:1000]}")
286|         content = (result["choices"][0]["message"].get("content") or "").strip()
287|         print(f"  Antwortlänge: {len(content)} Zeichen")
288|     except requests.exceptions.ConnectionError as e:
289|         raise RuntimeError(f"keine Verbindung zu {LLAMA_SERVER_URL}") from e
290|     if not content:
291|         raise RuntimeError("Modell lieferte leeren Inhalt")
292|     return content
```

### `agents/llm_scout/llm_scout.py` def save_report (Zeilen 295–315) – Bericht-Schreiben. Unverändert (hängt an `week_key_for_filename` und der Zweitlauf-Logik).

```python
295| def save_report(filepath: Path, report_content: str, now: datetime) -> None:
296|     """
297|     Schreibt den LLM-Bericht in die Datei.
298| 
299|     A1: Existiert die Datei bereits (Zweitlauf derselben ISO-KW), wird der
300|     neue Output als klar gekennzeichneter Nachtrag angehängt, statt den
301|     Erstbericht zu überschreiben.
302|     """
303|     iso_year, iso_week, _ = now.isocalendar()
304|     date_str = now.strftime("%Y-%m-%d %H:%M")
305| 
306|     if filepath.exists():
307|         # Zweitlauf: Nachtrag anhängen, Erstbericht bleibt byte-identisch
308|         with open(filepath, 'a', encoding='utf-8') as f:
309|             f.write(f"\n\n---\n\n")
310|             f.write(f"## Nachtrag KW{iso_week}_{iso_year} ({date_str})\n\n")
311|             f.write(report_content)
312|     else:
313|         # Erstlauf: Datei neu anlegen
314|         with open(filepath, 'w', encoding='utf-8') as f:
315|             f.write(report_content)
```

### `agents/llm_scout/llm_scout.py` def main (Zeilen 318–381) – Hauptablauf. Wird geändert: (1) `sources.json` laden, (2) pro-Quellen-Protokoll schreiben (B), (3) pro-Quellen-Items an `call_llm_for_evaluation` übergeben.

```python
318| def main():
319|     # Exit-Code-Semantik:
320|     #   0 = Erfolg (inkl. "keine neuen Items")
321|     #   1 = kritischer Fehler (API-Abruf, LLM-Evaluation, DB-Fehler)
322|     #   2 = llama-server nicht erreichbar
323|     print("--- Local LLM Scout gestartet ---")
324| 
325|     if not router_ready():
326|         print(f"llama-server unter {LLAMA_SERVER_URL} nicht erreichbar – nichts geholt, nichts markiert.",
327|               file=sys.stderr)
328|         sys.exit(2)
329| 
330|     try:
331|         # DB Initialisierung
332|         conn = sqlite3.connect(DB_PATH)
333|         init_db(conn)
334| 
335|         # 1. Daten holen
336|         print("Hole Daten von Hugging Face und GitHub...")
337|         hf_items = fetch_hf_trending()
338|         gh_items = fetch_github_releases()
339|         all_items = hf_items + gh_items
340|         print(f"Gesamt gefunden: {len(hf_items)} HF + {len(gh_items)} GH = {len(all_items)} Items")
341| 
342|         # 2. Filtern (nur neue) – noch NICHT markieren
343|         new_items = []
344|         for item in all_items:
345|             if is_new_item(conn, item['url']):
346|                 new_items.append(item)
347|             else:
348|                 print(f"  (bereits verarbeitet) {item['title']}")
349|         print(f"Neue Items: {len(new_items)}")
350| 
351|         if not new_items:
352|             conn.close()
353|             print("Keine neuen Items gefunden. Skript beendet.")
354|             sys.exit(0)
355| 
356|         print(f"Gefunden {len(new_items)} neue Items. Bewerte sie...")
357| 
358|         # 3. Evaluation durch LLM
359|         report_content = call_llm_for_evaluation(new_items)
360| 
361|         # 4. Bericht speichern (A1: Zweitlauf hängt nach, statt zu überschreiben)
362|         os.makedirs(REPORT_DIR, exist_ok=True)
363|         now = datetime.now()
364|         filename = week_key_for_filename(now)
365|         filepath = REPORT_DIR / filename
366| 
367|         save_report(filepath, report_content, now)
368|         print(f"Bericht gespeichert unter: {filepath}")
369| 
370|         # 5. Erst jetzt markieren – und nur, was wirklich bewertet wurde
371|         evaluated = select_items(new_items)
372|         for item in evaluated:
373|             mark_as_processed(conn, item['source'], item['title'], item['url'])
374|         conn.close()
375|         print(f"Als verarbeitet markiert: {len(evaluated)} (Rest bleibt fuer die naechste Woche offen)")
376|         print("--- Skript beendet ---")
377|         sys.exit(0)
378| 
379|     except Exception as e:
380|         print(f"Kritischer Fehler: {e}", file=sys.stderr)
381|         sys.exit(1)
```

### `agents/llm_scout/week_key.py` def week_key_for_filename (Zeilen 14–29) – Wochen-Datumsname. Unverändert.

```python
14| def week_key_for_filename(dt: datetime) -> str:
15|     """
16|     Bildet den Dateinamen fuer einen Wochenbericht aus einem datetime-Objekt.
17| 
18|     Nutzt isocalendar() fuer ISO-Jahr und ISO-Kalenderwoche.
19|     Beispiel: 29.12.2025 -> "llm_scout_kw1_2026.md"
20|               01.01.2027 -> "llm_scout_kw53_2026.md"
21| 
22|     Args:
23|         dt: Ein datetime-Objekt (naiv oder bewusst, muss ein gueltiges Datum sein).
24| 
25|     Returns:
26|         Der Dateiname als String, z. B. "llm_scout_kw1_2026.md".
27|     """
28|     iso_year, iso_week, _ = dt.isocalendar()
29|     return f"llm_scout_kw{iso_week}_{iso_year}.md"
```

### `agents/llm_scout/requirements.txt` (Zeilen 1–2) – Abhängigkeiten `feedparser`, `requests`. Unverändert (keine neuen Pakete nötig).

```
1| feedparser
2| requests
```

### `agents/llm_scout/sources.json`

**FEHLT:** Datei nicht gefunden.

### `scripts/send_scout_email.py` def build_email_message (Zeilen 95–121) – Markdown-zu-HTML-Konvertierung mit `markdown`-Lib. Unverändert. Der neue Bericht muss in diesem Template lesbar sein.

```python
 95| def build_email_message(report_path: Path, md_content: str | None = None,
 96|                         subject_suffix: str = "") -> MIMEText:
 97|     """
 98|     Liest den Markdown-Bericht, konvertiert zu HTML und baut eine MIME-Message.
 99|     Gibt die fertige MIMEText-Instanz zurück (ohne Versand).
100| 
101|     md_content: nur diesen Markdown-Text senden (z. B. nur die ungesendeten
102|     Nachträge, Nachbesserung 19.10.); Default: die ganze Datei.
103|     subject_suffix: Zusatz zum Betreff, z. B. " – Nachtrag".
104|     """
105|     iso_cal = datetime.now().isocalendar()
106|     kw_year = iso_cal[0]
107|     week = iso_cal[1]
108|     subject = f"LLM Scout KW{week} {kw_year}{subject_suffix}"
109| 
110|     # Markdown lesen und zu HTML konvertieren
111|     if md_content is None:
112|         md_content = report_path.read_text(encoding="utf-8")
113|     # N6: lazy import – nur hier nötig, nicht in build_fail_email()
114|     import markdown as md_lib
115|     html_body = md_lib.markdown(
116|         md_content,
117|         extensions=["extra", "tables", "fenced_code"],
118|     )
119| 
120|     # HTML-E-Mail zusammenbauen (mit minimalem CSS fuer bessere Lesbarkeit)
121|     html_template = f"""<!DOCTYPE html>
```

### `scripts/run_scout_pipeline.sh` (Zeilen 1–93) – Pipeline-Wrapper. Unverändert.

```bash
 1| #!/usr/bin/env bash
 2| #
 3| # run_scout_pipeline.sh
 4| # Fuehrt den LLM Scout aus und versendet den Bericht per E-Mail.
 5| #
 6| # Wird von launchd (de.hawe.lab.llm_scout) aufgerufen.
 7| # Exit-Code 0 bei Erfolg, != 0 bei Fehlern.
 8| #
 9| set -euo pipefail
10| 
11| # Repo-Root (elternverzeichnis dieses Skripts)
12| SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
13| REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
14| 
15| # LAB_DIR: übernehmen aus der Umgebung oder Default auf Repo-Pfad
16| DEFAULT_LAB_DIR="${REPO_ROOT}/agents/llm_scout/data"
17| DRY_RUN=0
18| if [ "${1:-}" = "--dry-run" ]; then
19|     DRY_RUN=1
20| fi
21| 
22| if [ "$DRY_RUN" -eq 1 ]; then
23|     if [ -z "${LAB_DIR:-}" ]; then
24|         # Trockenlauf ohne explizites LAB_DIR: temporäres Verzeichnis
25|         LAB_DIR="$(mktemp -d)"
26|         echo "Trockenlauf: temporäres LAB_DIR=${LAB_DIR}" >&2
27|         # DB reinkopieren, falls vorhanden
28|         if [ -f "${DEFAULT_LAB_DIR}/llm_scout.db" ]; then
29|             cp "${DEFAULT_LAB_DIR}/llm_scout.db" "${LAB_DIR}/"
30|         fi
31|     fi
32| else
33|     LAB_DIR="${LAB_DIR:-${DEFAULT_LAB_DIR}}"
34| fi
35| export LAB_DIR
36| 
37| # Python-Interpreter aus dem Projekt-venv
38| PYTHON="${REPO_ROOT}/.venv/bin/python3"
39| 
40| echo "=== LLM Scout Pipeline gestartet ==="
41| if [ "$DRY_RUN" -eq 1 ]; then
42|     echo "(Trockenlauf-Modus)"
43| fi
44| echo "Repo-Root: ${REPO_ROOT}"
45| echo "LAB_DIR:   ${LAB_DIR}"
46| echo ""
47| 
48| # Schritt 1: Scout-Bericht generieren
49| echo "--- Schritt 1: LLM Scout ---"
50| # (set -e wuerde sonst sofort abbrechen, bevor eine Meldung kommt)
51| SCOUT_EXIT=0
52| "${PYTHON}" "${REPO_ROOT}/agents/llm_scout/llm_scout.py" || SCOUT_EXIT=$?
53| if [ ${SCOUT_EXIT} -ne 0 ]; then
54|     echo "Fehler: llm_scout.py beendet mit Exit-Code ${SCOUT_EXIT}." >&2
55|     if [ "$DRY_RUN" -eq 1 ]; then
56|         echo "Trockenlauf: Fehler-Mail uebersprungen (Scout Exit-Code ${SCOUT_EXIT})" >&2
57|     else
58|         # Fehler-Mail versuchen (set -e gefangen, damit der Wrapper den originalen Exit-Code gibt)
59|         "${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" --fail-mail --exit-code ${SCOUT_EXIT} || :
60|         # Pipeline-Lauf-Datei schreiben (auch bei Scout-Fehler, damit der Exit-Code sichtbar ist)
61|         PIPELINE_LOG="${LAB_DIR}/pipeline_runs.log"
62|         TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
63|         echo "${TIMESTAMP} SCOUT_EXIT=${SCOUT_EXIT} EMAIL_EXIT=skipped" >> "${PIPELINE_LOG}"
64|     fi
65|     exit ${SCOUT_EXIT}
66| fi
67| 
68| echo ""
69| 
70| # Schritt 2: Bericht per E-Mail versenden
71| echo "--- Schritt 2: E-Mail-Versand ---"
72| EMAIL_EXIT=0
73| if [ "$DRY_RUN" -eq 1 ]; then
74|     "${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" --dry-run || EMAIL_EXIT=$?
75| else
76|     "${PYTHON}" "${REPO_ROOT}/scripts/send_scout_email.py" || EMAIL_EXIT=$?
77| fi
78| 
79| # A4: Pipeline-Lauf-Datei schreiben (nur bei echtem Lauf, nicht im Dry-Run)
80| if [ "$DRY_RUN" -eq 0 ]; then
81|     PIPELINE_LOG="${LAB_DIR}/pipeline_runs.log"
82|     TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"
83|     echo "${TIMESTAMP} SCOUT_EXIT=${SCOUT_EXIT} EMAIL_EXIT=${EMAIL_EXIT}" >> "${PIPELINE_LOG}"
84| fi
85| 
86| if [ ${EMAIL_EXIT} -ne 0 ]; then
87|     echo "Fehler: send_scout_email.py beendet mit Exit-Code ${EMAIL_EXIT}." >&2
88|     exit ${EMAIL_EXIT}
89| fi
90| 
91| echo ""
92| echo "=== Pipeline erfolgreich abgeschlossen ==="
93| exit 0
```

### `config/launchd/llm_scout.plist` (Zeilen 1–47) – launchd-Konfiguration. Unverändert. `LAB_DIR` und `SCOUT_ALLOW_SEND` sind gesetzt.

```xml
 1| <?xml version="1.0" encoding="UTF-8"?>
 2| <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 3|   "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
 4| <plist version="1.0">
 5| <dict>
 6|     <!-- Local LLM Scout: wöchentliches Infopaper neuer lokaler LLM-Entwicklungen -->
 7|     <key>Label</key>
 8|     <string>de.hawe.lab.llm_scout</string>
 9| 
10|     <key>ProgramArguments</key>
11|     <array>
12|         <string>/bin/bash</string>
13|         <string>/Users/hans-wernereberhardt/PycharmProjects/llama-server/scripts/run_scout_pipeline.sh</string>
14|     </array>
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
30|     <array>
31|         <dict>
32|             <key>Weekday</key>
33|             <integer>1</integer>
34|             <key>Hour</key>
35|             <integer>8</integer>
36|             <key>Minute</key>
37|             <integer>0</integer>
38|         </dict>
39|     </array>
40| 
41|     <key>StandardOutPath</key>
42|     <string>/Users/hans-wernereberhardt/PycharmProjects/llama-server/logs/llm_scout_out.log</string>
43| 
44|     <key>StandardErrorPath</key>
45|     <string>/Users/hans-wernereberhardt/PycharmProjects/llama-server/logs/llm_scout_err.log</string>
46| </dict>
47| </plist>
```
