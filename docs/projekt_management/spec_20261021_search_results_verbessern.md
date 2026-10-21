# Spec: search_results_verbessern

- **Datum:** 2026-10-21
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Betroffene Dateien:** `agents/llm_scout/llm_scout.py`, `agents/llm_scout/week_key.py`, `agents/llm_scout/sources.json` (neu), `agents/llm_scout/requirements.txt`, `tests/test_search_results_verbessern.py` (neu), `scripts/send_scout_email.py` (geprüft, keine Änderung geplant), `scripts/run_scout_pipeline.sh` (geprüft, keine Änderung geplant), `config/launchd/llm_scout.plist` (geprüft, keine Änderung geplant)

## Ziel

Der wöchentliche LLM-Scout-Bericht macht für **jede** Quelle – Hugging Face, jedes GitHub-Repo einzeln, Slipstream – sichtbar, was in den letzten 7 Tagen gefunden und an das LLM übergeben wurde, auch wenn die Antwort „nichts Neues" ist. Ein Quellenverteilungsprotokoll (B) wird **vor** der Prompt- und Ausbaumaßnahme (A) eingeführt, damit der erste instrumentierte Lauf die reale Item-Verteilung pro Quelle zeigt.

## Nicht-Ziele

- Keine Änderung der DB-Schema (`processed_items`), der Woche-Dedup-Logik, des Exit-Code-Schemas, der E-Mail-Versand-Logik oder der Pipeline-Wrapper-Logik.
- Keine Änderung von `scripts/send_scout_email.py`, `scripts/run_scout_pipeline.sh`, `config/launchd/llm_scout.plist`.
- Keine Änderung des HF-API-Aufrufs (Endpoints, Parameters, Filterkriterien).
- Kein Hugging Face Blog-Feed (`huggingface.co/blog.xml`) als Quelle. (Entschieden OQ3/OQ4, 2026-10-21.)
- Kein automatischer Download neuer Quellen, kein Crawler, kein Polling im Hintergrund.
- Keine Änderung des Markdown-zu-HTML-Renderings in `send_scout_email.py` (der neue Bericht muss im bestehenden Template lesbar sein).
- Die Slipstream-Quellendatei `sources.json` wird nicht als Ersatz für die bestehende `GITHUB_RELEASES_RSS`-Konstante verwendet; sie ergänzt sie um die Slipstream-spezifischen Einträge.

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?**
  - **Netzwerk:** HTTP-GET zu Hugging Face API (`huggingface.co/api/models`), GitHub Releases-Atom-Feeds (`github.com/*/releases.atom`, u. a. `github.com/Schero94/slipstream/releases.atom`) und GitHub-Repo-API (`api.github.com/repos/*/releases`).
  - **llama-server:** POST an `LLAMA_SERVER_URL/v1/chat/completions` (Default `http://localhost:8080`).
  - **E-Mail:** Indirekt – `send_scout_email.py` liest die neue Bericht-Datei und sendet sie per SMTP an Gmail. Der SMTP-Versand ist durch `SCOUT_ALLOW_SEND` und `LOCAL_TEST_HOSTS` in `send_scout_email.py` bereits gesondert gesichert.
  - **Schlüsselbund:** Indirekt über `get_password()` in `send_scout_email.py` – nur beim echten SMTP-Versand, nicht im Scout selbst.
  - **Echte Daten/DB:** `llm_scout.db` (SQLite) unter `LAB_DIR/` – wird beim produktiven Lauf beschrieben.
  - **launchd:** Die `sources.json` liegt neben dem Script (`agents/llm_scout/sources.json`) und muss vom Laufzeit-Pfad des Scout-Scripts lesbar sein, wenn launchd den Scout startet (`WorkingDirectory` = Repo-Root, `LAB_DIR` = `agents/llm_scout/data`).

- **Technische Sperre für Tests:**
  - **Netzwerk:** Alle HTTP-Aufrufe (`requests.get`, `requests.post`) werden per `unittest.mock.patch` ersetzt. Kein Test stellt eine echte TCP-Verbindung her.
  - **llama-server:** `call_llm_for_evaluation` wird im Test per Mock ersetzt (erzeugt einen vordefinierten String). Kein Test spricht einen echten Server an.
  - **DB:** `LAB_DIR` wird auf ein `tempfile.mkdtemp()`-Verzeichnis gesetzt. `llm_scout.db` wird im temporären Verzeichnis angelegt und nach dem Test gelöscht.
  - **E-Mail/Schlüsselbund:** Kein Test ruft `send_scout_email.py` oder `get_password()` auf. Die E-Mail-Versand-Logik ist nicht Teil dieser Spec.
  - **Quellen-Datei:** `sources.json` wird im Test auf einen Pfad im temporären Verzeichnis umgelenkt (Pfad-Parameter oder Umgebungsvariable), so dass keine echte `agents/llm_scout/sources.json` gelesen oder geschrieben wird.
  - **Protokoll-Datei:** `source_run_log_<KW>.jsonl` wird im Test in das temporäre `LAB_DIR` umgelenkt, so dass keine echte Protokoll-Datei im Repo beschrieben wird.

## Einstiegspunkte

Welche geänderten Dateien werden **wie** gestartet?

| Datei | Wie gestartet | Test |
|---|---|---|
| `agents/llm_scout/llm_scout.py` | Von `scripts/run_scout_pipeline.sh` als `python3 llm_scout.py` (launchd: `de.hawe.lab.llm_scout`, montags 08:00). Von Hand: `python3 agents/llm_scout/llm_scout.py`. Als Modul importiert (Test). | T1, T2, T12 |
| `agents/llm_scout/sources.json` | Wird von `llm_scout.py` zum Start gelesen. Liegt **neben dem Script** (`Path(__file__).parent / "sources.json"`), kein `LAB_DIR`-Fallback. Kein eigener Einstiegspunkt. | T2, T3 |
| `tests/test_search_results_verbessern.py` | `python3 -m pytest tests/test_search_results_verbessern.py` oder `python3 tests/test_search_results_verbessern.py`. | T1–T12 |

**Wichtig:** Die `sources.json`-Datei liegt **im Repo neben dem Script** (`agents/llm_scout/sources.json`) und wird per `Path(__file__).parent / "sources.json"` gelesen. Es gibt **keinen** Fallback auf `LAB_DIR` oder `Path.home() / "lab"` (Entschieden OQ1, 2026-10-21). Fehlt die Datei, bricht der Scout mit Exit 1 ab.

## Quellen

Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo:

- `agents/llm_scout/llm_scout.py` Zeilen 33–46 – `LLAMA_SERVER_URL`, `HF_API_URL`, `GITHUB_RELEASES_RSS`, `MODEL_NAME`, `LOOKBACK_DAYS`: Bestehende Konstanten, die die neue `sources.json`-Logik ergänzen, nicht ersetzen.
- `agents/llm_scout/llm_scout.py` `def fetch_hf_trending()` – HF-API-Aufruf und Filterlogik. Unverändert. Die Funktion liefert eine Liste von `Dict` mit Keys `source`, `title`, `url`, `summary`, `likes`.
- `agents/llm_scout/llm_scout.py` `def fetch_github_releases()` – RSS-Abruf und Filterlogik. Unverändert in der Kernlogik, aber wird um die pro-Repo-Differenzierung erweitert (jedes Repo wird separat geloggt).
- `agents/llm_scout/llm_scout.py` `def select_items()` – Auswahl der Top-3 pro Quelle für den LLM-Prompt. Wird geändert: pro-Quellen-Selektion, keine globale Top-3 über alle Quellen.
- `agents/llm_scout/llm_scout.py` `def call_llm_for_evaluation()` – LLM-Aufruf. System-Prompt und User-Prompt werden geändert (getrennte Sektionen, pro-Quellen-Präsentation, Verworf-Logik sichtbar).
- `agents/llm_scout/llm_scout.py` `def save_report()` – Bericht-Schreiben. Unverändert (hängt an `week_key_for_filename` und der Zweitlauf-Logik).
- `agents/llm_scout/llm_scout.py` `def main()` – Hauptablauf. Wird geändert: (1) `sources.json` laden, (2) pro-Quellen-Protokoll schreiben (B), (3) pro-Quellen-Items an `call_llm_for_evaluation` übergeben.
- `agents/llm_scout/week_key.py` `def week_key_for_filename()` – Wochen-Datumsname. Unverändert.
- `agents/llm_scout/requirements.txt` – Abhängigkeiten `feedparser`, `requests`. Unverändert (keine neuen Pakete nötig).
- `agents/llm_scout/sources.json` – **Neu.** Quellenkonfiguration, liegt im Repo neben dem Script. Format: siehe A2.
- `scripts/send_scout_email.py` `def build_email_message()` – Markdown-zu-HTML-Konvertierung mit `markdown`-Lib. Unverändert. Der neue Bericht muss in diesem Template lesbar sein.
- `scripts/run_scout_pipeline.sh` – Pipeline-Wrapper. Unverändert.
- `config/launchd/llm_scout.plist` – launchd-Konfiguration. Unverändert. `LAB_DIR` und `SCOUT_ALLOW_SEND` sind gesetzt.

**Nicht im Repo (externe Formate):**
- GitHub Releases-Atom-Feed-Format (`releases.atom`): Nicht im Repo dokumentiert. Das Format ist durch `feedparser` abstrahiert. `fetch_github_releases()` nutzt `entry.title`, `entry.link`, `entry.summary`, `entry.updated_parsed`.
- GitHub REST-API-Format für Releases: Nicht im Repo dokumentiert. Nicht verwendet – die Slipstream-Quelle ist per `sources.json` als Atom-Feed (`https://github.com/Schero94/slipstream/releases.atom`) angebunden (entschieden OQ2, 2026-10-21).

## Anforderungen

### A1: Quellenverteilungsprotokoll (B) – pro Quelle sichtbar, was abgerufen, gefiltert und an das Modell übergeben wurde

- **Anforderung:** Bei jedem Scout-Lauf wird ein strukturiertes Protokoll (JSONL, eine Zeile pro Lauf) angehängt, das pro Quelle die drei Stufen zeigt: (1) Anzahl der abgerufenen Items (Feed-Größe), (2) Anzahl der nach dem 7-Tage-Filter verbliebenen Items, (3) die konkrete Liste der Items, die an den LLM-Prompt übergeben werden (URL + Titel). Dieses Protokoll wird in `LAB_DIR/` gespeichert als `source_run_log_<ISO-KW>.jsonl`. Es wird **vor** dem LLM-Aufruf geschrieben, damit es auch bei einem LLM-Fehler vorliegt.
- **Stelle:** `agents/llm_scout/llm_scout.py`, neu: `def write_source_run_log(...)` und Aufruf in `main()` nach dem Datenholen, vor `call_llm_for_evaluation()`.
- **Akzeptanz:** Nach einem Lauf existiert `LAB_DIR/source_run_log_<KW>.jsonl` mit den Keys `huggingface`, `github:ggml-org/llama.cpp`, `github:ollama/ollama`, `github:huggingface/transformers`, `slipstream` (jeder Key ist ein Objekt mit `fetched`, `after_filter`, `sent_to_llm`). Bei einer leeren Quelle: `"fetched": 0, "after_filter": 0, "sent_to_llm": []`. Der Scout schreibt das Protokoll, **auch wenn** keine neuen Items gefunden wurden (Exit 0, „keine neuen Items").

### A2: Erweiterte Quellenkonfiguration in `sources.json` – ohne Codeänderung erweiterbar

- **Anforderung:** Die Datei `agents/llm_scout/sources.json` (im Repo, neben dem Script) definiert alle Quellen in einem einzigen JSON-Dokument. Das Format:
  ```json
  {
    "github": [
      {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
      {"repo": "ollama/ollama", "rss": "https://github.com/ollama/ollama/releases.atom"},
      {"repo": "huggingface/transformers", "rss": "https://github.com/huggingface/transformers/releases.atom"},
      {"repo": "Schero94/slipstream", "rss": "https://github.com/Schero94/slipstream/releases.atom"}
    ]
  }
  ```
  Ein neuer Eintrag wird hinzugefügt, indem das JSON erweitert wird – **ohne Codeänderung**. Der Scout liest `sources.json` zum Start. Fehlt die Datei oder ist sie ungültig, bricht der Scout mit einer klaren Fehlermeldung ab (Exit 1) und schreibt keine DB-Änderungen.
- **Stelle:** `agents/llm_scout/sources.json` (neu), `agents/llm_scout/llm_scout.py` `def load_sources()` (neu) und Aufruf in `main()`.
- **Akzeptanz:** (1) `sources.json` mit den obigen vier GitHub-Repos lädt erfolgreich. (2) Ein hinzugefügtes fünftes GitHub-Repo (`{"repo": "test/repo", "rss": "..."}`) wird ohne Codeänderung vom Scout gelesen und im Protokoll als `github:test/repo` aufgeführt. (3) Fehlt `sources.json`: Scout bricht mit Exit 1 ab, meldet „sources.json nicht gefunden", schreibt kein `llm_scout.db`. (4) Ungültiges JSON: Scout bricht mit Exit 1 ab, meldet den JSON-Fehler.

### A3: Slipstream als eigene, klar abgegrenzte Quelle

- **Anforderung:** Slipstream ist **keine** zusätzliche GitHub-Repo-Quelle im bestehenden `GITHUB_RELEASES_RSS`-Array. Sie wird in `sources.json` unter `github` als `Schero94/slipstream` aufgeführt **und** als eigene logische Sektion im Bericht ausgegeben. Der Bericht enthält eine **eigene Sektion** `## Slipstream neueste Entwicklungen`, die die Releases von `Schero94/slipstream` der letzten 7 Tage auflistet. **Kein** anderes Projekt namens „Slipstream" darf in dieser Sektion erscheinen. Der Filter erfolgt über die exakte Repo-ID `Schero94/slipstream`.
- **Stelle:** `agents/llm_scout/llm_scout.py` `def fetch_slipstream()` (neu) oder Erweiterung von `fetch_github_releases()` um eine separate Slipstream-Filterstufe.
- **Akzeptanz:** (1) Der Bericht enthält den Abschnitt `## Slipstream neueste Entwicklungen`. (2) In dieser Sektion erscheinen **nur** Items aus `Schero94/slipstream`. (3) Ein GitHub-Repo `chenzhuofu/slipstream` (oder jedes andere „slipstream"-Projekt) taucht **nicht** in der Slipstream-Sektion auf. (4) Wenn keine Slipstream-Releases in den letzten 7 Tagen gefunden wurden: Die Sektion existiert und enthält den Satz „Keine neuen Entwicklungen in den letzten 7 Tagen."

### A4: Pro-Quellen-Selektion und getrennte Präsentation im LLM-Prompt

- **Anforderung:** `select_items()` wählt pro Quelle unabhängig die Top-N Items (N = 3, konfigurierbar). Das LLM-Prompt zeigt **jede** Quelle als eigene, klar beschriftete Sektion:
  ```
  ## Hugging Face (neue Modelle)
  - [Modellname](URL): Summary
  (oder: „Keine neuen Modelle in den letzten 7 Tagen.")

  ## GitHub: ggml-org/llama.cpp
  - [Release-Titel](URL): Summary
  (oder: „Keine neuen Releases in den letzten 7 Tagen.")

  ## GitHub: ollama/ollama
  ...

  ## Slipstream neueste Entwicklungen
  - [Release-Titel](URL): Summary
  (oder: „Keine neuen Entwicklungen in den letzten 7 Tagen.")
  ```
  Ein Item aus einer Quelle darf **nicht** ein Item aus einer anderen Quelle verdrängen. Jede Quelle wird unabhängig bewertet. Das System-Prompt des LLMs wird um die Anweisung erweitert: „Bewerte jede Quelle getrennt. Für jede Quelle, die keine neuen Items hat, schreibe explizit ‚Keine neuen Entwicklungen in den letzten 7 Tagen.' Verwerfe kein Item ohne eine einzeilige Begründung."
- **Stelle:** `agents/llm_scout/llm_scout.py` `def select_items()` (geändert), `def call_llm_for_evaluation()` (System-Prompt und User-Prompt geändert).
- **Akzeptanz:** (1) Der LLM-Prompt enthält alle vier Quellen als eigene Sektionen. (2) Wenn `ollama/ollama` 0 neue Items hat und `llama.cpp` 3 neue Items hat: Beide Sektionen erscheinen im Prompt. Die `ollama/ollama`-Sektion enthält „Keine neuen Releases in den letzten 7 Tagen." (3) Das LLM-Output enthält für jede Quelle einen eigenen Abschnitt. (4) Ein verworfenes Item wird im Output mit einer einzeiligen Begründung aufgeführt (nicht stillschweigend weggelassen).

### A5: Pro-Quellen-Dedup in der DB

- **Anforderung:** Die `processed_items`-Tabelle in `llm_scout.db` dedupliziert pro URL (bestehendes Verhalten). Die neue `source`-Spalte wird korrekt befüllt: `huggingface`, `github:ggml-org/llama.cpp`, `github:ollama/ollama`, `github:huggingface/transformers`, `slipstream`. Ein Item wird **nur** als `slipstream` markiert, wenn es aus `Schero94/slipstream` stammt.
- **Stelle:** `agents/llm_scout/llm_scout.py` `def mark_as_processed()` (bestehend, unverändert in der Logik), aber die `source`-Wert-Zuordnung in `main()` wird angepasst.
- **Akzeptanz:** (1) Nach einem Lauf mit einem neuen `Schero94/slipstream`-Release: `SELECT source FROM processed_items WHERE url LIKE '%Schero94%'` liefert `slipstream`. (2) Ein HF-Modell liefert `huggingface`. (3) Ein `llama.cpp`-Release liefert `github:ggml-org/llama.cpp`.

### A6: Bericht zeigt „nichts Neues" pro Quelle

- **Anforderung:** Der Markdown-Bericht enthält für **jede** konfigurierte Quelle eine eigene Sektion. Wenn eine Quelle in den letzten 7 Tagen keine neuen Items geliefert hat, enthält die Sektion den Satz „Keine neuen Entwicklungen in den letzten 7 Tagen." (bzw. die quellenspezifische Variante: „Keine neuen Modelle", „Keine neuen Releases"). Die Sektion wird **nicht** weggelassen. Der Bericht ist so strukturiert, dass eine leere Quelle vom Leser sofort erkennbar ist.
- **Stelle:** `agents/llm_scout/llm_scout.py` `def call_llm_for_evaluation()` (System-Prompt-Anweisung) und/oder `def build_report_sections()` (neu, optional: deterministischer Sektions-Aufbau ohne LLM).
- **Akzeptanz:** (1) Der Bericht enthält die Sektionen: `## Hugging Face (neue Modelle)`, `## GitHub: ggml-org/llama.cpp`, `## GitHub: ollama/ollama`, `## GitHub: huggingface/transformers`, `## Slipstream neueste Entwicklungen`. (2) Wenn `ollama/ollama` 0 neue Items hat: Die Sektion `## GitHub: ollama/ollama` existiert und enthält „Keine neuen Releases in den letzten 7 Tagen." (3) Alle fünf Sektionen sind **immer** vorhanden, unabhängig davon, welche Quelle Items geliefert hat.

## Fehlerpfade

Für **jede** Anforderung jede Frage durchspielen.

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht (HF-API, GitHub-RSS, Slipstream-Feed) | `source_run_log` wird **nach** dem Datenholen geschrieben, **vor** dem LLM-Aufruf. Die fehlende Quelle ist im Protokoll mit `fetched: 0` sichtbar. | Scout bricht **nicht** ab (ein Feed-Fehler ist kein kritischer Fehler, bestehendes Verhalten). Protokoll zeigt die leere Quelle. Exit 0 (falls andere Quellen Items geliefert haben) oder Exit 0 (falls alle Quellen leer). stderr-Meldung für den fehlenden Feed. | T1 |
| A1 | `sources.json` fehlt | `main()` liest `sources.json` **vor** dem Datenholen. Kein Protokoll geschrieben, kein LLM-Aufruf. | Exit 1. stderr: „sources.json nicht gefunden unter <pfad>". Kein `llm_scout.db`-Schriftzugriff. Kein `source_run_log`-File. | T2 |
| A1 | `sources.json` ungültiges JSON | `main()` liest `sources.json`, JSON-Parser wirft `json.JSONDecodeError`. | Exit 1. stderr: „sources.json ist ungültiges JSON: <Fehler>". Kein DB-Schriftzugriff. | T2 |
| A1 | `sources.json` leer (`{}`) | `main()` liert die Datei, findet keine Quellen. | Exit 0. Protokoll mit leeren Listen für alle Quellen. Bericht enthält fünf leere Sektionen. | T3 |
| A1 | Lauf ohne Testschalter / gegen echte Daten | `source_run_log` wird in `LAB_DIR/` geschrieben. Im produktiven Lauf: `LAB_DIR/source_run_log_<KW>.jsonl`. | Datei existiert, jede Zeile ist gültiges JSON. Im Dry-Run (wenn implementiert): temporäres Verzeichnis. | T1, T2 |
| A1 | Absturz mitten im Lauf (nach `write_source_run_log`, vor LLM-Aufruf) | Protokoll ist geschrieben. DB noch nicht markiert. | Protokoll-Datei existiert und ist vollständig. DB ist unverändert. Beim nächsten Lauf: Items werden erneut geholt (nicht als verarbeitet markiert). | T1 |
| A2 | `sources.json` hat ein unbekanntes Key-Format (z. B. `"gitlab": [...]`) | `load_sources()` liest nur `github`. Unbekannte Keys werden ignoriert (mit stderr-Warnung). | Exit 0. Protokoll enthält nur die erkannten Quellen. stderr: „WARNUNG: Unbekannter Quellentyp 'gitlab' in sources.json, wird ignoriert." | T3 |
| A2 | GitHub-RSS-URL ist falsch (404) | `fetch_github_releases()` (bzw. `fetch_slipstream()`) fängt die `requests.HTTPError`. Quelle wird im Protokoll mit `fetched: 0` geloggt. | Exit 0 (andere Quellen liefern Items). stderr: „Fehler beim Abrufen von <url>: 404". Protokoll zeigt die leere Quelle. | T1 |
| A2 | GitHub-RSS-Feed ist leer (0 Einträge) | `feedparser` liefert `feed.entries == []`. | Exit 0. Protokoll: `fetched: 0, after_filter: 0, sent_to_llm: []`. Bericht: „Keine neuen Releases in den letzten 7 Tagen." | T1 |
| A2 | `sources.json` wird während des Laufs geändert | `load_sources()` liest die Datei **einmal** zum Start. Änderungen während des Laufs haben keine Auswirkung. | Lauf läuft mit der zum Start gelesenen Quelle-Konfiguration. | n. a. (kein Test) |
| A3 | `Schero94/slipstream` hat keine Releases in den letzten 7 Tagen | `fetch_slipstream()` liefert `[]`. | Slipstream-Sektion im Bericht: „Keine neuen Entwicklungen in den letzten 7 Tagen." | T4 |
| A3 | Ein GitHub-Repo `chenzhuofu/slipstream` wird in `sources.json` aufgenommen | `fetch_github_releases()` holt das Repo. Das Item wird als `github:chenzhuofu/slipstream` markiert, **nicht** als `slipstream`. | Das Item erscheint in der Sektion `## GitHub: chenzhuofu/slipstream`, **nicht** in `## Slipstream neueste Entwicklungen`. | T4 |
| A3 | `sources.json` enthält `Schero94/slipstream` **und** `chenzhuofu/slipstream` | Beide Repos werden geholt. `Schero94/slipstream` → `slipstream`, `chenzhuofu/slipstream` → `github:chenzhuofu/slipstream`. | Zwei separate Sektionen im Bericht. | T4 |
| A4 | `select_items()` mit einer Quelle, die 10 neue Items hat | Top 3 werden an den LLM-Prompt übergeben. Die restlichen 7 bleiben in der DB unmarkiert. | Protokoll: `sent_to_llm` enthält 3 Items. DB: 3 Items markiert, 7 offen. | T5 |
| A4 | `select_items()` mit einer Quelle, die 0 neue Items hat | Keine Items für diese Quelle im Prompt. | Prompt enthält die Quellen-Sektion mit „Keine neuen Releases in den letzten 7 Tagen." | T5 |
| A4 | LLM-Prompt wird zu lang (viele Quellen, viele Items) | `max_tokens = 4096` ist bereits gesetzt. Der Prompt selbst hat keine explizite Obergrenze. **Akzeptiertes Restrisiko:** Bei sehr vielen Quellen kann der Prompt das Kontextlimit des Modells überschreiten. Das LLM liefert dann einen leeren oder unvollständigen Output. | `call_llm_for_evaluation()` wirft `RuntimeError("Modell lieferte leeren Inhalt")`. Exit 1. stderr-Meldung. | T5 |
| A4 | LLM verwirft alle Items einer Quelle | System-Prompt verlangt eine einzeilige Begründung pro verworfenem Item. | Output enthält die verworfenen Items mit Begründung. | T5 |
| A5 | `mark_as_processed()` mit neuer `source`-Wert (`slipstream`) | DB-Schema hat eine `source TEXT NOT NULL`-Spalte. Neue Werte werden einfach eingefügt. | `INSERT` erfolgreich. `SELECT source FROM processed_items WHERE url = ?` liefert `slipstream`. | T6 |
| A5 | `mark_as_processed()` mit URL, die bereits als `github:ggml-org/llama.cpp` markiert ist, jetzt aber `slipstream` sein soll | `url` hat ein `UNIQUE`-Constraint. `IntegrityError` wird gefangen und ignoriert. | Item wird **nicht** doppelt markiert. Die ursprüngliche `source`-Wert bleibt erhalten. | T6 |
| A5 | DB-Datei ist korrupt | `sqlite3.connect()` oder `init_db()` wirft `sqlite3.DatabaseError`. | Exit 1. stderr: „Kritischer Fehler: <sqlite3-Fehler>". | T6 |
| A6 | Bericht wird geschrieben, LLM liefert leeren Output | `call_llm_for_evaluation()` wirft `RuntimeError`. `save_report()` wird **nicht** aufgerufen. | Exit 1. Keine Bericht-Datei geschrieben. `source_run_log` existiert. | T7 |
| A6 | Bericht-Datei existiert bereits (Zweitlauf) | `save_report()` hängt an (bestehendes Verhalten, A1 aus der Vorlage). | Datei wird **nicht** überschrieben. Nachtrag angehängt. | T7 |
| A6 | `week_key_for_filename()` liefert einen Dateinamen, der bereits gesendet wurde (`.sent_state`) | `send_scout_email.py` prüft die `.sent_state`-Datei. | Versand wird übersprungen, Exit 0. | n. a. (aus `send_scout_email.py`, nicht Teil dieser Spec) |

## Testplan

Alle Tests werden als `tests/test_search_results_verbessern.py` (unittest) umgesetzt. Kein Test hat Außenwirkung.
**Wichtige Test-Regel:** Neue Funktionen (`load_sources`, `write_source_run_log`, `fetch_slipstream`, geänderte `select_items`, geänderte `call_llm_for_evaluation`) werden **in der Testmethode** importiert, nicht am Datei-Anfang. So lädt das Testskript den alten Code und die neue Funktion separat, und die Gegenprobe (`kette.py gegenprobe`) sagt je Test etwas.

### T1: Feed-Fehler (404) → Quelle im Protokoll mit `fetched: 0`, Scout bricht nicht ab

- **Prüft:** A1, A2, Fehlerpfad „Gegenstelle antwortet nicht", „GitHub-RSS-URL ist falsch (404)"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit einem validen `github`-Eintrag und einem ungültigen (404-URL). `requests.get` wird per Mock auf `HTTPError(404)` für die ungültige URL und auf einen gültigen Feed-Inhalt für die gültige URL gesetzt. `call_llm_for_evaluation` wird per Mock ersetzt (liefert einen festen String). DB wird im temporären Verzeichnis angelegt.
- **Erwartung:** (1) Exit-Code 0. (2) `source_run_log_<KW>.jsonl` existiert. (3) Das JSONL-Protokoll enthält `"github:<repo_404>": {"fetched": 0, ...}`. (4) Das JSONL-Protokoll enthält `"github:<repo_ok>": {"fetched": <n> > 0, ...}`. (5) `llm_scout.db` enthält ein `processed_items`-Record für die gültige Quelle.
- **Warum misst der Test das Richtige?** Wenn der Scout bei einem Feed-Fehler abbrechen würde (Exit ≠ 0), scheitert der Test an der Exit-Code-Prüfung. Wenn das Protokoll nicht geschrieben würde, scheitert der Test an der Dateipräsenz-Prüfung. Wenn die 404-Quelle nicht im Protokoll auftaucht, scheitert der Test an der JSONL-Inhaltsprüfung.
- **Gegenprobe:** Im alten Code (ohne `write_source_run_log`) existiert keine `source_run_log`-Datei → Test rot. Im alten Code bricht der Scout bei einem Feed-Fehler nicht ab (bestehendes Verhalten), aber das Protokoll fehlt ebenfalls → Test rot.

### T2: `sources.json` fehlt → Exit 1, keine DB-Änderung

- **Prüft:** A1, A2, Fehlerpfad „`sources.json` fehlt"
- **Aufbau:** Temporäres `LAB_DIR`. **Keine** `sources.json` neben dem Script (Pfad wird im Test umgelenkt). `llm_scout.py` wird per `subprocess` mit `LAB_DIR=<tmp>` aufgerufen.
- **Erwartung:** (1) Exit-Code 1. (2) stderr enthält „sources.json nicht gefunden". (3) Kein `llm_scout.db` im temporären Verzeichnis. (4) Kein `source_run_log`-File.
- **Warum misst der Test das Richtige?** Wenn der Scout ohne `sources.json` weiterlaufen würde (Exit 0), scheitert der Test an der Exit-Code-Prüfung. Wenn die DB trotzdem angelegt wird, scheitert der Test an der DB-Prüfung.
- **Gegenprobe:** Im alten Code existiert `load_sources()` nicht. Der Scout liest die `GITHUB_RELEASES_RSS`-Konstante und läuft weiter → Exit 0 → Test rot.

### T3: `sources.json` mit unbekanntem Key → Warnung, Exit 0, nur erkannte Quellen im Protokoll

- **Prüft:** A2, Fehlerpfad „`sources.json` hat ein unbekanntes Key-Format"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit `github: [...]` (valid) und `gitlab: [...]` (unbekannt). `requests.get` per Mock. `call_llm_for_evaluation` per Mock.
- **Erwartung:** (1) Exit-Code 0. (2) stderr enthält „WARNUNG: Unbekannter Quellentyp 'gitlab'". (3) `source_run_log` enthält **nur** `github:*`-Keys, keinen `gitlab:*`-Key.
- **Warum misst der Test das Richtige?** Wenn der Scout bei einem unbekannten Key abbrechen würde (Exit ≠ 0), scheitert der Test. Wenn der `gitlab`-Key im Protokoll auftaucht, scheitert der Test an der JSONL-Inhaltsprüfung.
- **Gegenprobe:** Im alten Code existiert `load_sources()` nicht → Test rot.

### T4: Slipstream-Filter – nur `Schero94/slipstream`, kein anderes „slipstream"-Projekt

- **Prüft:** A3, Fehlerpfad „`chenzhuofu/slipstream` wird in `sources.json` aufgenommen", „`Schero94/slipstream` hat keine Releases in den letzten 7 Tagen"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit `Schero94/slipstream` und `chenzhuofu/slipstream`. `requests.get` per Mock: (a) `Schero94/slipstream` → ein Release, (b) `chenzhuofu/slipstream` → ein Release. `call_llm_for_evaluation` per Mock.
- **Erwartung:** (1) Exit-Code 0. (2) Protokoll: `slipstream.fetched ≥ 1`, `github:chenzhuofu/slipstream.fetched ≥ 1`. (3) Das `sent_to_llm`-Feld der `slipstream`-Quelle enthält **nur** das `Schero94/slipstream`-Release. (4) Das `sent_to_llm`-Feld von `github:chenzhuofu/slipstream` enthält das `chenzhuofu`-Release. (5) Das `chenzhuofu/slipstream`-Item taucht in **keiner** `slipstream`-`sent_to_llm`-Liste auf.
- **Warum misst der Test das Richtige?** Wenn das `chenzhuofu/slipstream`-Item in der `slipstream`-Sektion landet, scheitert der Test an der JSONL-Inhaltsprüfung.
- **Gegenprobe:** Im alten Code existiert `fetch_slipstream()` nicht, die Slipstream-Filterlogik nicht → Test rot.

### T5: `select_items()` pro Quelle – Top 3, leere Quelle bleibt sichtbar

- **Prüft:** A4, Fehlerpfad „`select_items()` mit einer Quelle, die 10 neue Items hat", „`select_items()` mit einer Quelle, die 0 neue Items hat"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit zwei GitHub-Repos. `requests.get` per Mock: Repo A → 10 neue Items, Repo B → 0 neue Items. `call_llm_for_evaluation` per Mock.
- **Erwartung:** (1) Protokoll: `github:repo_a.sent_to_llm` enthält genau 3 Items. (2) Protokoll: `github:repo_b.sent_to_llm` enthält 0 Items. (3) Der LLM-Prompt (übergeben an den Mock) enthält die Sektion für Repo B mit „Keine neuen Releases in den letzten 7 Tagen." (4) DB: 3 Items für Repo A markiert, 0 für Repo B.
- **Warum misst der Test das Richtige?** Wenn `select_items()` global Top 3 über alle Quellen nehmen würde (bestehendes Verhalten), läge Repo B im Prompt nicht als eigene Sektion vor → Test rot an der Prompt-Prüfung. Wenn Repo B im Protokoll fehlt, rot an der JSONL-Prüfung.
- **Gegenprobe:** Im alten Code ist `select_items()` global (Top 3 HF + Top 3 GH) → Test rot.

### T6: DB-`source`-Wert korrekt befüllt, `UNIQUE`-Constraint respektiert

- **Prüft:** A5, Fehlerpfad „`mark_as_processed()` mit neuer `source`-Wert", „`mark_as_processed()` mit URL, die bereits markiert ist"
- **Aufbau:** Temporäres `LAB_DIR`. `llm_scout.db` wird initialisiert. `mark_as_processed()` wird direkt aufgerufen mit: (a) `source="slipstream"`, (b) `source="github:ggml-org/llama.cpp"`, (c) dieselbe URL wie (b) mit `source="slipstream"`.
- **Erwartung:** (1) Nach (a): `SELECT source FROM processed_items WHERE url = ?` liefert `slipstream`. (2) Nach (b): `SELECT source FROM processed_items WHERE url = ?` liefert `github:ggml-org/llama.cpp`. (3) Nach (c): Kein `IntegrityError`. `SELECT source FROM processed_items WHERE url = ?` liefert weiterhin `github:ggml-org/llama.cpp` (die zweite Markierung wird ignoriert). (4) `SELECT COUNT(*) FROM processed_items WHERE url = ?` liefert 1.
- **Warum misst der Test das Richtige?** Wenn die `source`-Wert-Zuordnung falsch wäre (z. B. `slipstream` für ein `llama.cpp`-Item), scheitert der Test an der SELECT-Prüfung. Wenn der `UNIQUE`-Constraint nicht respektiert wird (doppelte Einträge), scheitert der Test an der COUNT-Prüfung.
- **Gegenprobe:** Im alten Code ist die `source`-Wert-Zuordnung an `mark_as_processed()` gebunden, die `source`-Parameter direkt übergeben. Der Test würde im alten Code **grün** bleiben, weil `mark_as_processed()` unverändert ist. **Gegenprobe-Problem:** Dieser Test prüft das bestehende Verhalten, nicht die neue Logik. Die neue Logik ist die `source`-Wert-Zuordnung **vor** dem Aufruf von `mark_as_processed()` in `main()`. Der Test muss daher `main()` (oder die aufrufende Funktion) mit einer simulierten Item-Liste füttern, die die `source`-Werte korrekt zuweist. **Anpassung:** Der Test ruft eine neue Funktion `def assign_source_tags(items)` auf (neu in `llm_scout.py`), die die `source`-Werte den Items zuweist, und prüft, dass `Schero94/slipstream` → `slipstream`, `ggml-org/llama.cpp` → `github:ggml-org/llama.cpp`.

### T7: LLM-Fehler → kein Bericht, Protokoll existiert, Exit 1

- **Prüft:** A1, A6, Fehlerpfad „Bericht wird geschrieben, LLM liefert leeren Output"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit einem validen GitHub-Repo. `requests.get` per Mock (gültiger Feed). `call_llm_for_evaluation` per Mock, der `RuntimeError("Modell lieferte leeren Inhalt")` wirft.
- **Erwartung:** (1) Exit-Code 1. (2) `source_run_log_<KW>.jsonl` existiert und ist gültiges JSONL. (3) **Keine** Bericht-Datei in `LAB_DIR/weekly-reports/`. (4) DB: Kein `processed_items`-Record (Items nicht markiert).
- **Warum misst der Test das Richtige?** Wenn der Bericht trotzdem geschrieben würde, scheitert der Test an der Dateipräsenz-Prüfung. Wenn das Protokoll bei einem LLM-Fehler nicht geschrieben würde, scheitert der Test an der Protokoll-Prüfung. Wenn die DB markiert würde, scheitert der Test an der DB-Prüfung.
- **Gegenprobe:** Im alten Code wirft `call_llm_for_evaluation()` ebenfalls `RuntimeError` bei leerem Output, und `save_report()` wird nicht aufgerufen → Exit 1. Aber das Protokoll existiert im alten Code nicht → Test rot an der Protokoll-Prüfung.

### T8: `sources.json` leer (`{}`) → Exit 0, fünf leere Sektionen im Bericht

- **Prüft:** A1, A2, A6, Fehlerpfad „`sources.json` leer"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit `{}`. `call_llm_for_evaluation` per Mock (liefert einen Bericht mit fünf leeren Sektionen).
- **Erwartung:** (1) Exit-Code 0. (2) `source_run_log` existiert, alle `fetched: 0`. (3) Die Bericht-Datei enthält fünf Sektionen, jede mit „Keine neuen Entwicklungen in den letzten 7 Tagen."
- **Warum misst der Test das Richtige?** Wenn der Scout bei leerer `sources.json` abbrechen würde (Exit ≠ 0), rot. Wenn der Bericht nicht geschrieben würde, rot. Wenn eine Sektion fehlt, rot.
- **Gegenprobe:** Im alten Code existiert `sources.json` nicht, der Scout liest `GITHUB_RELEASES_RSS` → Exit 0, aber kein Protokoll → Test rot.

### T9: Zweiter Lauf in derselben Woche → Bericht wird angehängt, nicht überschrieben (bestehendes Verhalten)

- **Prüft:** A6, Fehlerpfad „Bericht-Datei existiert bereits (Zweitlauf)"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit einem validen GitHub-Repo. Erster Lauf: `requests.get` per Mock (gültiger Feed), `call_llm_for_evaluation` per Mock (liefert Bericht A). Zweiter Lauf: `requests.get` per Mock (gültiger Feed, andere Items), `call_llm_for_evaluation` per Mock (liefert Bericht B).
- **Erwartung:** (1) Erster Lauf: Exit 0, Bericht-Datei existiert mit Inhalt A. (2) Zweiter Lauf: Exit 0, Bericht-Datei enthält A **und** B (angehängt, nicht überschrieben). (3) DB: Items aus Lauf 1 und Lauf 2 sind beide markiert. (4) `source_run_log_<KW>.jsonl` enthält **zwei** Zeilen (eine pro Lauf), beide gültiges JSON.
- **Warum misst der Test das Richtige?** Wenn der zweite Lauf den Bericht überschreiben würde, scheitert der Test an der Inhaltsprüfung. Wenn das Protokoll den ersten Lauf überschreiben würde, scheitert der Test an der Zeilenanzahl-Prüfung.
- **Gegenprobe:** Im alten Code hängt `save_report()` an → Test grün. Dieser Test prüft das bestehende Verhalten. **Gegenprobe:** „keine" – Test prüft Bestehendes, die Anhäng-Logik ist unverändert.

### T10: Slipstream-Repo-Feed ist leer (0 Einträge) → Slipstream-Sektion mit „Keine neuen Entwicklungen"

- **Prüft:** A3, A6, Fehlerpfad „`Schero94/slipstream` hat keine Releases in den letzten 7 Tagen"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit `Schero94/slipstream`. `requests.get` per Mock: Feed mit 0 Einträgen (oder alle Einträge älter als 7 Tage). `call_llm_for_evaluation` per Mock.
- **Erwartung:** (1) Exit-Code 0. (2) Protokoll: `slipstream.fetched: 0` (oder `fetched: <n>`, `after_filter: 0`). (3) Bericht enthält die Sektion `## Slipstream neueste Entwicklungen` mit „Keine neuen Entwicklungen in den letzten 7 Tagen."
- **Warum misst der Test das Richtige?** Wenn die Slipstream-Sektion bei 0 Items weggelassen würde, scheitert der Test an der Inhaltsprüfung.
- **Gegenprobe:** Im alten Code existiert die Slipstream-Sektion nicht → Test rot.

### T11: `sources.json`-Erweiterung ohne Codeänderung – fünftes Repo wird erkannt

- **Prüft:** A2, Fehlerpfad „GitHub-RSS-Feed ist leer (0 Einträge)"
- **Aufbau:** Temporäres `LAB_DIR`. `sources.json` mit vier GitHub-Repos (wie im Akzeptanz-Beispiel). `requests.get` per Mock für alle vier. Dann: `sources.json` wird um ein fünftes Repo (`test/repo`) erweitert. `requests.get` per Mock für das fünfte Repo (gültiger Feed mit 1 Item). `call_llm_for_evaluation` per Mock.
- **Erwartung:** (1) Exit-Code 0. (2) Protokoll enthält `github:test/repo` mit `fetched ≥ 1`. (3) Keine Codeänderung war nötig – nur die `sources.json` wurde erweitert.
- **Warum misst der Test das Richtige?** Wenn der Scout das fünfte Repo nicht erkennen würde (weil die Quelle-Konfiguration hartkodiert wäre), scheitert der Test an der Protokoll-Prüfung.
- **Gegenprobe:** Im alten Code ist `GITHUB_RELEASES_RSS` eine hartkodierte Liste → das fünfte Repo wird nicht gelesen → Test rot.

### T12: `llm_scout.py` lädt als Skript ohne ImportError (Bestandssicherung)

- **Prüft:** Einstiegspunkt „als Modul importiert"
- **Aufbau:** `runpy.run_path('agents/llm_scout/llm_scout.py', run_name='kein_main')`.
- **Erwartung:** Exit-Code 0, kein `ImportError`, kein `ModuleNotFoundError`.
- **Warum misst der Test das Richtige?** Wenn die neue `sources.json`-Logik einen Import-Fehler verursacht (z. B. fehlendes `json`-Modul, falscher Pfad), scheitert der Test.
- **Gegenprobe:** Im alten Code: `llm_scout.py` lädt erfolgreich → Test grün. Dieser Test ist eine Bestandssicherung. **Gegenprobe:** „keine" – Test prüft Bestehendes.

## Offene Fragen

- **OQ1: Pfad der `sources.json` bei manuellem Lauf ohne `LAB_DIR`.** *(Entschieden 2026-10-21, 11:15.)* Nur `agents/llm_scout/sources.json` im Repo, kein Fallback; fehlt sie, Exit 1.
- **OQ2: Slipstream-Feed-Format – Atom oder REST-API.** *(Entschieden 2026-10-21, 11:15.)* Atom-Feed `https://github.com/Schero94/slipstream/releases.atom`.
- **OQ3: HF-Blog-Feed-Endpunkt und -Format.** *(Entschieden 2026-10-21, 11:15.)* HF-Blog streichen. Slipstream ist ausschließlich das Repo `Schero94/slipstream` (Releases). Weitere Quellen später nur über `sources.json`.
- **OQ4: MoE-Expert-Streaming-Filter – Keyword oder Topic-ID.** *(Entschieden 2026-10-21, 11:15.)* Wie OQ3: HF-Blog streichen. Slipstream ist ausschließlich das Repo `Schero94/slipstream` (Releases).
- **OQ5: Protokoll-Format – JSON oder Markdown.** *(Entschieden 2026-10-21, 11:15.)* JSON (JSONL).
- **OQ6: Protokoll-Datei-Namen – pro Lauf oder pro Woche.** *(Entschieden 2026-10-21, 11:15.)* `source_run_log_<KW>.jsonl`, eine Zeile pro Lauf, anhängen.
- **OQ7: Maximalzahl der GitHub-Repos in `sources.json`.** *(Entschieden 2026-10-21, 11:15.)* Keine Grenze, Warnung ab 8 Repos.

## Abweichende Meinung

- **Hawes Diagnose „GitHub-Abruf funktioniert nicht" ist durch den eigenen KW43-Bericht widerlegt.** Der Bericht enthält drei `llama.cpp`-Items unter „Tool Updates". Der Fetch und das Filtern laufen. Die eigentliche Schwäche ist die **präsentationelle Verdrängung**: HF wird zu einer LLM-Zeile zusammengefasst, GitHub-Items konkurrieren in einem gemeinsamen Textblock, und ein leerer HF-Wochenlauf ist vom Bericht nicht unterscheidbar. Die Spec adressiert das mit A3 (pro-Quellen-Sektionen), A4 (pro-Quellen-Prompt) und A6 (leere Quellen sichtbar). Wenn Hawe der Meinung ist, dass der GitHub-Abruf **tatsächlich** nicht funktioniert (z. B. weil in anderen Wochen keine GitHub-Items im Bericht standen), muss der Testlauf (B) das klären – die Spec kann das nicht vorab entscheiden.
- **Slipstream als eigene Quelle, nicht als zusätzliches GitHub-Repo.** Die Anforderung sagt „Ergänze also im html eine extra Sektion 'Slipstream neueste Entwicklungen'". Die Spec interpretiert das als: Slipstream ist eine **logische Sektion** im Bericht, die aus der GitHub-Quelle `Schero94/slipstream` gespeist wird. Sie ist **nicht** einfach ein weiteres Element im `GITHUB_RELEASES_RSS`-Array.
- **HF-Blog-Kopplung an Slipstream war überflüssig.** Die ursprüngliche Spec-Specifizierte Slipstream-Sektion sollte zusätzlich HF-Blog-Posts zum Thema „MoE-Expert-Streaming" enthalten. Hawe hat OQ3/OQ4 am 2026-10-21 entschieden: HF-Blog streichen, Slipstream ist ausschließlich `Schero94/slipstream` (Releases). Die Kopplung an den HF-Blog war aus meiner Sicht ein konstruierter Zusatz ohne klaren Mehrwert – die Requirement war bereits mit dem Repo-Feed erfüllt. Die Entscheidung Hawes bestätigt das.
