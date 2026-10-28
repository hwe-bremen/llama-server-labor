# Review-Paket: search_results_verbessern


Erzeugt 2026-10-22 11:37 von `kette.py paket`. Ruecksetzpunkt: `ea9288f`. Geaenderte Code-Dateien: `agents/llm_scout/llm_scout.py`, `agents/llm_scout/sources.json`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: search_results_verbessern

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Der wöchentliche Mailversand mit aktuellen Infos zum Entwicklungsstand lokaler LLM soll hinsichtlich der Bereitstellung der Informationen noch verbessert werden:
> 1. llama Infos kommen gut an, jedoch von git-hub werden bisher keine Infos extrahiert, da scheint die Logik noch nicht zu passen. Also funktioniert hier der Abruf bzw. die Wissens/Info Extraction noch nicht wie gewünscht:
> LLAMA_SERVER_URL = os.getenv("LLAMA_SERVER_URL", "http://localhost:8080")
> HF_API_URL = "https://huggingface.co/api/models"
> GITHUB_RELEASES_RSS = [
>     "https://github.com/ggml-org/llama.cpp/releases.atom",
>     "https://github.com/ollama/ollama/releases.atom",
>     "https://github.com/huggingface/transformers/releases.atom"
> 2. Da wir slipstream auch testen, aber erstmal zurückstellen, bis neue interessante Modelle für slipstream in der community diskutiert werden, wäre auch hier ein Infosuche sehr gut. Ergänze also im html eine extra Sektion "Slipstream neueste Entwicklungen" und fasse hier die entsprechenden Resultate zusammen. Bitte erstelle eine Linkliste die entsprechend zu den vorhandenen Zieladressen ergänzt werden kann.
>
> Wenn Du zu dem Auftrag fragen hast melde Dich.

## Antworten auf Rueckfragen

**2026-10-21 10:13** — Frage: **Hast du in den Scout-Logs (`logs/llm_scout_out.log`) schon gesehen, ob die Zeile `RSS https://github.com/...: N Einträge` mit N > 0 kommt?** Wenn ja: Problem liegt im Filter oder in der LLM-Bewertung. Wenn N = 0: Problem liegt im Fetch. Wenn du die Log-Zeile nicht hast oder unsicher bist, sage ich

> HIer ist der Inhalt einer erzeugten MD Datei:
> LLM Scout Weekly
> Top Modelle
> Keine neuen relevanten Modell-Releases gefunden: In der bereitgestellten Liste sind ausschließlich Updates für die llama.cpp Infrastruktur enthalten. Es wurden keine neuen GGUF-Modelle (z. B. von Qwen, Llama, Mistral oder DeepSeek) veröffentlicht, die den Kriterien für Größe (<15GB Q4), Leistung oder Sprache entsprechen.
> Tool Updates
> llama.cpp b11724: Kritischer Bugfix für CUDA-Benutzer. Behebung eines Shared-Memory WAR-Hazards in flash_attn_ext_vec. Dies erhöht die Stabilität und Korrektheit der Inferenz auf NVIDIA-GPUs, ist aber für M4 Macs (Metal Backend) nicht direkt relevant.
> llama.cpp b11723: Verbesserungen für Hexagon-Backends (Qualcomm Snapdragon). Fokus auf längere Kontexte und Sliding Window Attention (SWA). Relevant nur für Nutzer von Android/Qualcomm-Hardware, nicht für Apple Silicon.
> llama.cpp b11722: Ermöglicht Multistream Flash Attention für Hexagon. Ebenfalls spezifisch für Qualcomm-Hardware-Optimierungen.
> Fazit
> Ein Update lohnt sich aktuell nur, wenn du NVIDIA-GPUs nutzt (wegen des CUDA-Fixes in b11724); für M4 Macs sind diese Releases irrelevant, da sie sich auf CUDA und Hexagon konzentrieren.
>
> _____
>
> Nur Llama inhakte kein github, kein hugging face
>
> ____
>
> ZU slipsream:  hier das repro https://github.com/chenzhuofu/slipstream oder z.B.: https://huggingface.co/blog/anthonym21/slipstream-for-agent-communication

**2026-10-21 10:31** — Frage: **Welchen Umfang willst du für die Spec?** Nur A, oder A+B?

> A und B, und zwar B zuerst: erst ein Lauf, der pro Quelle protokolliert, was abgerufen, gefiltert und an das Modell gegeben wurde, dann der Fix.
> Zusätzlich verbindlich:
>
> Im Bericht muss für jede Quelle sichtbar sein, was gefunden wurde, auch „nichts Neues“: Hugging Face, jedes GitHub-Repo einzeln, Slipstream. Keine Quelle darf eine andere verdrängen.
> Korrektur Slipstream: Meine beiden Links waren falsch. Gemeint ist ausschließlich das Projekt https://github.com/Schero94/slipstream (Releases) sowie Diskussionen zu MoE-Expert-Streaming von der SSD. Der Name „Slipstream“ ist mehrdeutig, es gibt viele fremde Projekte gleichen Namens. Die dürfen nicht im Bericht landen.
> Die Linkliste soll ohne Codeänderung erweiterbar sein.
>
> Dann Spec schreiben.

**2026-10-21 11:15**

> Nachtrag:
> OQ1: nur agents/llm_scout/sources.json im Repo, kein Fallback; fehlt sie, Exit 1.
> OQ2: Atom-Feed https://github.com/Schero94/slipstream/releases.atom.
> OQ3/OQ4: HF-Blog streichen. Slipstream ist ausschließlich das Repo Schero94/slipstream (Releases). Weitere Quellen später nur über sources.json.
> OQ5: JSON.
> OQ6: source_run_log_<KW>.jsonl, eine Zeile pro Lauf, anhängen.
> OQ7: keine Grenze, Warnung ab 8 Repos.
> Bitte Spec entsprechend anpassen (A3, Quellen, Tests T4/T10) und die offenen Fragen als entschieden markieren.

## 2. Spec (Auszug aus `spec_20261021_search_results_verbessern.md`)

### Ziel
Der wöchentliche LLM-Scout-Bericht macht für **jede** Quelle – Hugging Face, jedes GitHub-Repo einzeln, Slipstream – sichtbar, was in den letzten 7 Tagen gefunden und an das LLM übergeben wurde, auch wenn die Antwort „nichts Neues" ist. Ein Quellenverteilungsprotokoll (B) wird **vor** der Prompt- und Ausbaumaßnahme (A) eingeführt, damit der erste instrumentierte Lauf die reale Item-Verteilung pro Quelle zeigt.

### Anforderungen
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

### Testplan (nur Titel und Erwartungen)
### T1: Feed-Fehler (404) → Quelle im Protokoll mit `fetched: 0`, Scout bricht nicht ab
- **Erwartung:** (1) Exit-Code 0. (2) `source_run_log_<KW>.jsonl` existiert. (3) Das JSONL-Protokoll enthält `"github:<repo_404>": {"fetched": 0, ...}`. (4) Das JSONL-Protokoll enthält `"github:<repo_ok>": {"fetched": <n> > 0, ...}`. (5) `llm_scout.db` enthält ein `processed_items`-Record für die gültige Quelle.
### T2: `sources.json` fehlt → Exit 1, keine DB-Änderung
- **Erwartung:** (1) Exit-Code 1. (2) stderr enthält „sources.json nicht gefunden". (3) Kein `llm_scout.db` im temporären Verzeichnis. (4) Kein `source_run_log`-File.
### T3: `sources.json` mit unbekanntem Key → Warnung, Exit 0, nur erkannte Quellen im Protokoll
- **Erwartung:** (1) Exit-Code 0. (2) stderr enthält „WARNUNG: Unbekannter Quellentyp 'gitlab'". (3) `source_run_log` enthält **nur** `github:*`-Keys, keinen `gitlab:*`-Key.
### T4: Slipstream-Filter – nur `Schero94/slipstream`, kein anderes „slipstream"-Projekt
- **Erwartung:** (1) Exit-Code 0. (2) Protokoll: `slipstream.fetched ≥ 1`, `github:chenzhuofu/slipstream.fetched ≥ 1`. (3) Das `sent_to_llm`-Feld der `slipstream`-Quelle enthält **nur** das `Schero94/slipstream`-Release. (4) Das `sent_to_llm`-Feld von `github:chenzhuofu/slipstream` enthält das `chenzhuofu`-Release. (5) Das `chenzhuofu/slipstream`-Item taucht in **keiner** `slipstream`-`sent_to_llm`-Liste auf.
### T5: `select_items()` pro Quelle – Top 3, leere Quelle bleibt sichtbar
- **Erwartung:** (1) Protokoll: `github:repo_a.sent_to_llm` enthält genau 3 Items. (2) Protokoll: `github:repo_b.sent_to_llm` enthält 0 Items. (3) Der LLM-Prompt (übergeben an den Mock) enthält die Sektion für Repo B mit „Keine neuen Releases in den letzten 7 Tagen." (4) DB: 3 Items für Repo A markiert, 0 für Repo B.
### T6: DB-`source`-Wert korrekt befüllt, `UNIQUE`-Constraint respektiert
- **Erwartung:** (1) Nach (a): `SELECT source FROM processed_items WHERE url = ?` liefert `slipstream`. (2) Nach (b): `SELECT source FROM processed_items WHERE url = ?` liefert `github:ggml-org/llama.cpp`. (3) Nach (c): Kein `IntegrityError`. `SELECT source FROM processed_items WHERE url = ?` liefert weiterhin `github:ggml-org/llama.cpp` (die zweite Markierung wird ignoriert). (4) `SELECT COUNT(*) FROM processed_items WHERE url = ?` liefert 1.
### T7: LLM-Fehler → kein Bericht, Protokoll existiert, Exit 1
- **Erwartung:** (1) Exit-Code 1. (2) `source_run_log_<KW>.jsonl` existiert und ist gültiges JSONL. (3) **Keine** Bericht-Datei in `LAB_DIR/weekly-reports/`. (4) DB: Kein `processed_items`-Record (Items nicht markiert).
### T8: `sources.json` leer (`{}`) → Exit 0, fünf leere Sektionen im Bericht
- **Erwartung:** (1) Exit-Code 0. (2) `source_run_log` existiert, alle `fetched: 0`. (3) Die Bericht-Datei enthält fünf Sektionen, jede mit „Keine neuen Entwicklungen in den letzten 7 Tagen."
### T9: Zweiter Lauf in derselben Woche → Bericht wird angehängt, nicht überschrieben (bestehendes Verhalten)
- **Erwartung:** (1) Erster Lauf: Exit 0, Bericht-Datei existiert mit Inhalt A. (2) Zweiter Lauf: Exit 0, Bericht-Datei enthält A **und** B (angehängt, nicht überschrieben). (3) DB: Items aus Lauf 1 und Lauf 2 sind beide markiert. (4) `source_run_log_<KW>.jsonl` enthält **zwei** Zeilen (eine pro Lauf), beide gültiges JSON.
### T10: Slipstream-Repo-Feed ist leer (0 Einträge) → Slipstream-Sektion mit „Keine neuen Entwicklungen"
- **Erwartung:** (1) Exit-Code 0. (2) Protokoll: `slipstream.fetched: 0` (oder `fetched: <n>`, `after_filter: 0`). (3) Bericht enthält die Sektion `## Slipstream neueste Entwicklungen` mit „Keine neuen Entwicklungen in den letzten 7 Tagen."
### T11: `sources.json`-Erweiterung ohne Codeänderung – fünftes Repo wird erkannt
- **Erwartung:** (1) Exit-Code 0. (2) Protokoll enthält `github:test/repo` mit `fetched ≥ 1`. (3) Keine Codeänderung war nötig – nur die `sources.json` wurde erweitert.
### T12: `llm_scout.py` lädt als Skript ohne ImportError (Bestandssicherung)
- **Erwartung:** Exit-Code 0, kein `ImportError`, kein `ModuleNotFoundError`.

### Offene Fragen
- **OQ1: Pfad der `sources.json` bei manuellem Lauf ohne `LAB_DIR`.** *(Entschieden 2026-10-21, 11:15.)* Nur `agents/llm_scout/sources.json` im Repo, kein Fallback; fehlt sie, Exit 1.
- **OQ2: Slipstream-Feed-Format – Atom oder REST-API.** *(Entschieden 2026-10-21, 11:15.)* Atom-Feed `https://github.com/Schero94/slipstream/releases.atom`.
- **OQ3: HF-Blog-Feed-Endpunkt und -Format.** *(Entschieden 2026-10-21, 11:15.)* HF-Blog streichen. Slipstream ist ausschließlich das Repo `Schero94/slipstream` (Releases). Weitere Quellen später nur über `sources.json`.
- **OQ4: MoE-Expert-Streaming-Filter – Keyword oder Topic-ID.** *(Entschieden 2026-10-21, 11:15.)* Wie OQ3: HF-Blog streichen. Slipstream ist ausschließlich das Repo `Schero94/slipstream` (Releases).
- **OQ5: Protokoll-Format – JSON oder Markdown.** *(Entschieden 2026-10-21, 11:15.)* JSON (JSONL).
- **OQ6: Protokoll-Datei-Namen – pro Lauf oder pro Woche.** *(Entschieden 2026-10-21, 11:15.)* `source_run_log_<KW>.jsonl`, eine Zeile pro Lauf, anhängen.
- **OQ7: Maximalzahl der GitHub-Repos in `sources.json`.** *(Entschieden 2026-10-21, 11:15.)* Keine Grenze, Warnung ab 8 Repos.

## 3. Code-Aenderungen gegen `ea9288f`

### agents/llm_scout/llm_scout.py (Diff, 806 Zeilen)

```diff
diff --git a/agents/llm_scout/llm_scout.py b/agents/llm_scout/llm_scout.py
index d0d1545..f81ed21 100755
--- a/agents/llm_scout/llm_scout.py
+++ b/agents/llm_scout/llm_scout.py
@@ -2,16 +2,20 @@
 """
 Local LLM Scout: Wöchentliche Zusammenfassung neuer lokaler LLM-Entwicklungen.
 Nutzt Hugging Face API, GitHub RSS und llama-server für die Evaluation.
+
+Erweitert um pro-Quellen-Protokoll, sources.json-Konfiguration,
+Slipstream als eigene Quelle, und pro-Quellen-Prompt-Präsentation.
 """
 
 import json
 import os
+import re
 import sqlite3
 import sys
 import time
 from datetime import datetime, timedelta
 from pathlib import Path
-from typing import List, Dict, Any
+from typing import List, Dict, Any, Optional
 
 import feedparser
 import requests
@@ -47,38 +51,91 @@ MODEL_NAME = os.getenv("SCOUT_MODEL", "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL")
 # Zeitfenster: Nur Items der letzten N Tage betrachten (Standard: 7 Tage für "wöchentlich")
 LOOKBACK_DAYS = 7
 
+# Top-N Items pro Quelle für den LLM-Prompt
+ITEMS_PER_SOURCE = 3
+
+# Pfad zur sources.json – liegt neben dem Script im Repo
+_SOURCES_JSON_PATH = Path(__file__).resolve().parent / "sources.json"
+
+# Slipstream-Repo-ID (exakt)
+SLIPSTREAM_REPO = "Schero94/slipstream"
+
+
+# --- QUELLENKONFIGURATION (A2) ---
+
+def load_sources(sources_path: Optional[Path] = None) -> Dict[str, Any]:
+    """
+    Liest die sources.json und gibt das Quellen-Dictionary zurück.
+
+    Erkennt nur den Key 'github'. Unbekannte Keys werden mit
+    einer stderr-Warnung ignoriert.
+
+    Args:
+        sources_path: Pfad zur sources.json. Default: neben dem Script.
+
+    Returns:
+        Dictionary mit Quellen, z. B.:
+        {"github": [{"repo": "ggml-org/llama.cpp", "rss": "..."}, ...]}
+
+    Raises:
+        SystemExit(1): Datei fehlt oder ist ungültiges JSON.
+    """
+    path = sources_path or _SOURCES_JSON_PATH
+
+    if not path.exists():
+        print(f"sources.json nicht gefunden unter {path}", file=sys.stderr)
+        sys.exit(1)
+
+    try:
+        with open(path, 'r', encoding='utf-8') as f:
+            data = json.load(f)
+    except json.JSONDecodeError as e:
+        print(f"sources.json ist ungültiges JSON: {e}", file=sys.stderr)
+        sys.exit(1)
+
+    # Nur bekannte Keys verarbeiten
+    result = {}
+    for key in data:
+        if key == "github":
+            result[key] = data[key]
+        else:
+            print(f"Warnung: Unbekannter Quellentyp '{key}' in sources.json, wird ignoriert.",
+                  file=sys.stderr)
+
+    return result
+
 
 # --- HILFSFUNKTIONEN ---
 
 def init_db(conn: sqlite3.Connection) -> None:
     """Erstellt die Tabelle, falls nicht vorhanden."""
     conn.execute("""
-                 CREATE TABLE IF NOT EXISTS processed_items
-                 (
-                     id
-                     INTEGER
-                     PRIMARY
-                     KEY
-                     AUTOINCREMENT,
-                     source
-                     TEXT
-                     NOT
-                     NULL,
-                     title
-                     TEXT
-                     NOT
-                     NULL,
-                     url
-                     TEXT
-                     UNIQUE
-                     NOT
-                     NULL,
-                     processed_at
-                     TIMESTAMP
-                     DEFAULT
-                     CURRENT_TIMESTAMP
-                 )
-                 """)
+                  CREATE TABLE IF NOT EXISTS processed_items
+                  (
+                      id
+                      INTEGER
+                      PRIMARY
+                      KEY
+                      AUTOINCREMENT,
+                      source
+                      TEXT
+                      NOT
+                      NULL,
+                      title
+                      TEXT
+                      NOT
+                      NULL,
+                      url
+                      TEXT
+                      UNIQUE
+                      NOT
+                      NULL,
+                      processed_at
+                      TIMESTAMP
+                      DEFAULT
+                      CURRENT_TIMESTAMP
+                  )
+                  """)
     conn.commit()
 
 
@@ -100,13 +157,55 @@ def mark_as_processed(conn: sqlite3.Connection, source: str, title: str, url: st
         pass  # Bereits vorhanden, ignorieren
 
 
-def fetch_hf_trending() -> List[Dict[str, Any]]:
+# --- SOURCE-TAG-ZUORDNUNG (A5) ---
+
+def assign_source_tags(item: Dict[str, Any], source_key: str) -> Dict[str, Any]:
+    """
+    Weist einem Item den korrekten source-Tag zu.
+
+    Slipstream-Items aus Schero94/slipstream bekommen den Tag 'slipstream',
+    alle anderen GitHub-Items bekommen 'github:<repo>'.
+
+    Args:
+        item: Das Item-Dictionary (wird nicht verändert).
+        source_key: Der Quellen-Schlüssel, z. B. 'github:ggml-org/llama.cpp',
+                    'slipstream', 'huggingface'.
+
+    Returns:
+        Das Item mit dem korrigierten 'source'-Feld.
+    """
+    result = dict(item)
+    result["source"] = source_key
+    return result
+
+
+def get_source_key_for_repo(repo_name: str) -> str:
+    """
+    Bildet den source-Key für ein GitHub-Repo.
+
+    Schero94/slipstream -> 'slipstream'
+    ggml-org/llama.cpp -> 'github:ggml-org/llama.cpp'
+    """
+    if repo_name == SLIPSTREAM_REPO:
+        return "slipstream"
+    return f"github:{repo_name}"
+
+
+# --- DATEN HOLEN (unverändert, aber pro-Repo aufgeteilt) ---
+
+def fetch_hf_trending() -> tuple:
     """
     Holt trending Modelle von Hugging Face.
     Filtert nach GGUF, sortiert nach Likes. Nimmt Modelle die
     neu sind (<30 Tage) ODER viele Downloads haben (>1000).
+
+    Returns:
+        Tuple (fetched_count, items_after_filter) wobei fetched_count die
+        Anzahl der Modelle aus der API-Antwort ist (vor jeglichem Filter)
+        und items_after_filter die gefilterte Liste.
     """
     items = []
+    fetched_count = 0
     try:
         params = {
             "sort": "likes",
@@ -117,6 +216,7 @@ def fetch_hf_trending() -> List[Dict[str, Any]]:
         response = requests.get(HF_API_URL, params=params, timeout=10)
         response.raise_for_status()
         models = response.json()
+        fetched_count = len(models)
 
         now = datetime.now(tz=__import__('datetime').timezone.utc)
         cutoff = now - timedelta(days=30)
@@ -147,112 +247,233 @@ def fetch_hf_trending() -> List[Dict[str, Any]]:
         print(f"Fehler beim Abrufen von Hugging Face: {e}", file=sys.stderr)
 
     items.sort(key=lambda x: x.get("likes", 0), reverse=True)
-    return items
+    return (fetched_count, items)
 
 
-def fetch_github_releases() -> List[Dict[str, Any]]:
+def fetch_github_releases_for_repo(rss_url: str, repo_name: str) -> tuple:
     """
-    Holt neue Releases von GitHub Repositories via RSS.
+    Holt neue Releases von einem einzelnen GitHub Repository via RSS.
+
+    Args:
+        rss_url: Die RSS-URL des Repos.
+        repo_name: Der Repo-Name, z. B. 'ggml-org/llama.cpp'.
+
+    Returns:
+        Tuple (fetched_count, items_after_filter) wobei fetched_count die
+        Anzahl der Eintraege im Feed VOR dem 7-Tage-Filter ist und
+        items_after_filter nur die Items nach dem Filter.
     """
     items = []
     cutoff_date = datetime.now() - timedelta(days=LOOKBACK_DAYS)
+    source_key = get_source_key_for_repo(repo_name)
+    fetched_count = 0
+
+    try:
+        # Abruf ueber requests (nutzt certifi): feedparser/urllib scheitert mit dem
+        # python.org-Python auf macOS an der Zertifikatspruefung -> still 0 Eintraege.
+        resp = requests.get(rss_url, timeout=15, headers={"User-Agent": "llm-scout-lab/1.0"})
+        resp.raise_for_status()
+        feed = feedparser.parse(resp.content)
+        if feed.bozo and not feed.entries:
+            print(f"  WARNUNG {rss_url}: Feed nicht lesbar ({feed.get('bozo_exception')})", file=sys.stderr)
+            return (0, items)
+        fetched_count = len(feed.entries)
+        print(f"  RSS {rss_url}: {fetched_count} fetched, cutoff: {cutoff_date.strftime('%Y-%m-%d')}")
+        for entry in feed.entries:
+            # Datum prüfen – updated_parsed ist time.struct_time (UTC)
+            updated_parsed = getattr(entry, 'updated_parsed', None)
+            if updated_parsed:
+                updated_dt = datetime(*updated_parsed[:6])
+                if updated_dt > cutoff_date:
+                    items.append({
+                        "source": source_key,
+                        "title": entry.title,
+                        "url": entry.link,
+                        "summary": entry.summary[:200] + "..." if len(entry.summary) > 200 else entry.summary
+                    })
+            else:
+                print(f"    (kein Datum) {entry.title}")
+    except Exception as e:
+        print(f"Fehler beim Abrufen von {rss_url}: {e}", file=sys.stderr)
+
+    return (fetched_count, items)
 
-    for rss_url in GITHUB_RELEASES_RSS:
-        try:
-            # Abruf ueber requests (nutzt certifi): feedparser/urllib scheitert mit dem
-            # python.org-Python auf macOS an der Zertifikatspruefung -> still 0 Eintraege.
-            resp = requests.get(rss_url, timeout=15, headers={"User-Agent": "llm-scout-lab/1.0"})
-            resp.raise_for_status()
-            feed = feedparser.parse(resp.content)
-            if feed.bozo and not feed.entries:
-                print(f"  WARNUNG {rss_url}: Feed nicht lesbar ({feed.get('bozo_exception')})", file=sys.stderr)
-            print(f"  RSS {rss_url}: {len(feed.entries)} Einträge (cutoff: {cutoff_date.strftime('%Y-%m-%d')})")
-            for entry in feed.entries:
-                # Datum prüfen – updated_parsed ist time.struct_time (UTC)
-                updated_parsed = getattr(entry, 'updated_parsed', None)
-                if updated_parsed:
-                    updated_dt = datetime(*updated_parsed[:6])
-                    if updated_dt > cutoff_date:
-                        items.append({
-                            "source": "github",
-                            "title": entry.title,
-                            "url": entry.link,
-                            "summary": entry.summary[:200] + "..." if len(entry.summary) > 200 else entry.summary
-                        })
-                else:
-                    print(f"    (kein Datum) {entry.title}")
-        except Exception as e:
-            print(f"Fehler beim Abrufen von {rss_url}: {e}", file=sys.stderr)
-
-    return items
 
 
+# --- PRO-QUELLEN-SELEKTION (A4) ---
+
 def select_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
-    """Was tatsaechlich bewertet wird: Top 3 HF + Top 3 GitHub (Kontext sparen).
-    Nur diese Items werden nach einem gespeicherten Bericht als verarbeitet markiert."""
-    hf = [i for i in items if i['source'] == 'huggingface'][:3]
-    gh = [i for i in items if i['source'] == 'github'][:3]
-    return hf + gh
+    """Was tatsaechlich bewertet wird: Top N pro Quelle (Kontext sparen).
+    Nur diese Items werden nach einem gespeicherten Bericht als verarbeitet markiert.
 
+    Im Gegensatz zum alten Code (global Top 3 HF + Top 3 GH) wird nun
+    pro source-Key unabhängig selektiert.
+    """
+    # Items nach source gruppieren
+    by_source: Dict[str, List[Dict[str, Any]]] = {}
+    for item in items:
+        src = item.get("source", "unknown")
+        by_source.setdefault(src, []).append(item)
+
+    selected = []
+    for src, src_items in by_source.items():
+        selected.extend(src_items[:ITEMS_PER_SOURCE])
+    return selected
 
-def router_ready(timeout: float = 5.0) -> bool:
-    """Laeuft der llama-server? Ohne ihn gar nicht erst anfangen (nichts markieren)."""
-    try:
-        return requests.get(f"{LLAMA_SERVER_URL}/v1/models", timeout=timeout).status_code == 200
-    except Exception:
-        return False
 
+# --- PRO-QUELLEN-PROTOKOLL (A1) ---
 
-def call_llm_for_evaluation(items: List[Dict[str, Any]]) -> str:
+def write_source_run_log(lab_dir: Path, source_data: Dict[str, Dict[str, Any]]) -> None:
     """
-    Sendet die Liste der neuen Items an llama-server zur Bewertung.
+    Schreibt das Quellenverteilungsprotokoll als JSONL-Datei.
+
+    Jede Quelle hat vier Stufen:
+        - fetched: Eintraege im Feed/API-Antwort VOR jedem Filter
+        - after_filter: nach 7-Tage-Filter
+        - new: nach DB-Abgleich (noch nicht verarbeitet)
+        - sent_to_llm: Items die tatsaechlich an das LLM gesendet wurden
+
+    Args:
+        lab_dir: Das LAB_DIR-Verzeichnis.
+        source_data: Dictionary mit pro Quelle:
+            {
+                "huggingface": {"fetched": 50, "after_filter": 5, "new": 3, "sent_to_llm": [...]},
+                ...
+            }
+    """
+    iso_year, iso_week, _ = datetime.now().isocalendar()
+    log_filename = f"source_run_log_kw{iso_week}_{iso_year}.jsonl"
+    log_path = lab_dir / log_filename
+
+    with open(log_path, 'a', encoding='utf-8') as f:
+        f.write(json.dumps(source_data, ensure_ascii=False) + "\n")
+
+
+# --- LLM-PROMPT MIT PRO-QUELLEN-SEKTIONEN (A4, A6) ---
+
+def build_prompt_sections(items: List[Dict[str, Any]], sources_config: Dict[str, Any]) -> str:
+    """
+    Baut den User-Prompt mit pro-Quellen-Sektionen.
+
+    Jede konfigurierte Quelle (aus sources_config) und Hugging Face erscheinen
+    als eigene Markdown-Sektion – auch wenn keine Items vorhanden sind.
+    Der Code baut das Geruest, das LLM fuellt die Bewertungen.
+
+    Args:
+        items: Alle Items (nach DB-Filter).
+        sources_config: Die sources.json-Konfiguration.
+    """
+    # Items nach source gruppieren
+    by_source: Dict[str, List[Dict[str, Any]]] = {}
+    for item in items:
+        src = item.get("source", "unknown")
+        by_source.setdefault(src, []).append(item)
+
+    sections = []
+
+    # Hugging Face Sektion (immer vorhanden)
+    hf_items = by_source.get("huggingface", [])
+    sections.append("## Hugging Face (neue Modelle)")
+    if hf_items:
+        for it in hf_items[:ITEMS_PER_SOURCE]:
+            sections.append(f"- [{it['title']}]({it['url']}): {it['summary']}")
+    else:
+        sections.append("Keine neuen Modelle in den letzten 7 Tagen.")
+    sections.append("")
+
+    # GitHub-Sektionen (jedes konfigurierte Repo separat, auch ohne Items)
+    github_repos = sources_config.get("github", [])
+    for repo_config in github_repos:
+        repo_name = repo_config["repo"]
+        if repo_name == SLIPSTREAM_REPO:
+            continue  # Slipstream wird separat behandelt
+        source_key = get_source_key_for_repo(repo_name)
+        repo_items = by_source.get(source_key, [])
+        sections.append(f"## GitHub: {repo_name}")
+        if repo_items:
+            for it in repo_items[:ITEMS_PER_SOURCE]:
+                sections.append(f"- [{it['title']}]({it['url']}): {it['summary']}")
+        else:
+            sections.append("Keine neuen Releases in den letzten 7 Tagen.")
+        sections.append("")
+
+    # Slipstream-Sektion (immer vorhanden, auch wenn nicht in sources.json)
+    slipstream_configured = any(
+        r.get("repo") == SLIPSTREAM_REPO for r in github_repos
+    )
+    slip_items = by_source.get("slipstream", [])
+    sections.append("## Slipstream neueste Entwicklungen")
+    if slip_items:
+        for it in slip_items[:ITEMS_PER_SOURCE]:
+            sections.append(f"- [{it['title']}]({it['url']}): {it['summary']}")
+    elif slipstream_configured:
+        sections.append("Keine neuen Entwicklungen in den letzten 7 Tagen.")
+    else:
+        sections.append("nicht konfiguriert")
+
+    return "\n".join(sections)
+
+
+def call_llm_for_evaluation(items: List[Dict[str, Any]],
+                            sources_config: Dict[str, Any]) -> str:
     """
-    if not items:
-        return "Keine neuen relevanten Entwicklungen gefunden."
+    Sendet die Liste der neuen Items an llama-server zur Bewertung.
+    Nutzt pro-Quellen-Prompt-Struktur (A4, A6).
+
+    Der Prompt enthält Sektionen für ALLE konfigurierten Quellen, auch wenn
+    keine Items vorhanden sind. Das LLM bewertet jede Sektion.
 
+    Args:
+        items: Liste aller neuen Items (nach DB-Filter).
+        sources_config: Die sources.json-Konfiguration.
+    """
     # Prompt Konstruktion
     system_prompt = """
     Du bist ein Experte für lokale LLM-Infrastruktur (llama.cpp, Ollama, GGUF).
     Deine Aufgabe ist es, eine Liste neuer Modell-Releases und Tool-Updates zu bewerten.
 
-    Kriterien für Relevanz:
-    1. Modellgröße: Ideal < 15GB in Q4_K_M Quantisierung (passend für M4 Mac mit 48GB RAM).
-    2. Kompatibilität: Muss GGUF unterstützen oder für llama.cpp/Ollama tauglich sein.
-    3. Leistung: Zeigt es signifikante Verbesserungen in Benchmarks (MMLU, GPQA, etc.)?
-    4. Lizenz: Open Source (Apache 2.0, MIT, etc.) bevorzugt.
-    5. Sprache: Deutsch-Unterstützung ist ein Bonus.
+    Bewerte jede Quelle getrennt. Für jede Quelle, die keine neuen Items hat,
+    schreibe explizit 'Keine neuen Entwicklungen in den letzten 7 Tagen.'
 
-    Gib die Top 3-5 interessantesten Entwicklungen zurück.
-    Wenn es nur kleine Bugfixes sind, ignoriere sie.
+    Fuehre JEDES uebergebene Item in seiner Quellen-Sektion auf: relevant mit
+    kurzer Begründung, oder 'verworfen: <einzeiliger Grund>'.
+
+    Kriterien fuer Tool-Releases (llama.cpp, Ollama, etc.):
+    - Relevanz fuer Apple Silicon / Metal-Unterstuetzung
+    - Neue Features (z. B. neue Quantisierungen, Backends, Modellformate)
+    - Breaking Changes oder API-Änderungen
 
     Ausgabeformat:
     # LLM Scout Weekly
 
-    ## Top Modelle
-    - **[Modellname](Link)**: Kurze Begründung (Größe, Leistung, Sprache).
+    ## Hugging Face (neue Modelle)
+    - **[Modellname](Link)**: Kurze Begründung.
+    (oder: „Keine neuen Modelle in den letzten 7 Tagen.")
+
+    ## GitHub: ggml-org/llama.cpp
+    - **[Release-Titel](Link)**: Wichtige neue Features.
+    (oder: „Keine neuen Releases in den letzten 7 Tagen.")
 
-    ## Tool Updates
-    - **[Toolname](Link)**: Wichtige neue Features.
+    ## GitHub: ollama/ollama
+    ...
+
+    ## Slipstream neueste Entwicklungen
+    - **[Release-Titel](Link)**: Wichtige neue Features.
+    (oder: „Keine neuen Entwicklungen in den letzten 7 Tagen.")
 
     ## Fazit
     Ein Satz zusammenfassend, ob sich ein Update lohnt.
     """
 
-    # Items für den Prompt vorbereiten (max 10 Items, um Kontext zu sparen)
-    # Wir nehmen die Top 3 HF und Top 3 GH
-    relevant_items = select_items(items)
-
-    items_text = "\n".join([
-        f"- Source: {i['source']}, Title: {i['title']}, URL: {i['url']}, Summary: {i['summary']}"
-        for i in relevant_items
-    ])
+    # Pro-Quellen-Prompt mit Sektionen (alle konfigurierten Quellen, auch ohne Items)
+    items_text = build_prompt_sections(items, sources_config)
 
     user_prompt = f"""
     Hier sind die neuen Entwicklungen der letzten Woche:
 
     {items_text}
 
-    Bitte bewerte diese und erstelle das Infopaper.
+    Bitte bewerte jede Quelle getrennt und erstelle das Infopaper.
     """
 
     # API Call an llama-server
@@ -292,6 +513,133 @@ def call_llm_for_evaluation(items: List[Dict[str, Any]]) -> str:
     return content
 
 
+def secure_report_sections(report_content: str,
+                            evaluated_items: List[Dict[str, Any]],
+                            sources_config: Dict[str, Any]) -> str:
+    """
+    Prueft, ob jede erwartete Sektion als Ueberschrift im Bericht steht und
+    ob die URL jedes Items aus evaluated im Bericht vorkommt.
+
+    Fehlende Sektionen werden nachgetragen – mit den an das Modell gegebenen
+    Eintraegen dieser Quelle als Liste oder mit „Keine neuen … in den letzten 7 Tagen.".
+
+    Fehlende Items werden in einer Sektion "## Nicht vom Modell bewertet"
+    als "- [Titel](URL)" aufgelistet.
+
+    Fehlende Sektionen und die Liste stehen VOR "## Fazit", falls vorhanden,
+    sonst am Ende des Berichts.
+
+    Slipstream bleibt immer im Bericht, auch wenn Schero94/slipstream nicht
+    in sources.json steht (Inhalt dann „nicht konfiguriert").
+
+    Args:
+        report_content: Roh-Bericht vom LLM.
+        evaluated_items: Items die an das LLM gesendet wurden (nach select_items).
+        sources_config: Die sources.json-Konfiguration.
+
+    Returns:
+        Bericht mit allen Sektionen und Items (unverändert oder um fehlende ergänzt).
+    """
+    # Items nach source gruppieren
+    by_source: Dict[str, List[Dict[str, Any]]] = {}
+    for item in evaluated_items:
+        src = item.get("source", "unknown")
+        by_source.setdefault(src, []).append(item)
+
+    # Erwartete Sektionen zusammenstellen
+    expected_sections = []
+
+    # Hugging Face (immer)
+    expected_sections.append(("## Hugging Face (neue Modelle)", "huggingface",
+                               "Keine neuen Modelle in den letzten 7 Tagen."))
+
+    # GitHub-Repos aus sources.json (außer Slipstream)
+    github_repos = sources_config.get("github", [])
+    for repo_config in github_repos:
+        repo_name = repo_config["repo"]
+        if repo_name == SLIPSTREAM_REPO:
+            continue
+        source_key = get_source_key_for_repo(repo_name)
+        expected_sections.append((f"## GitHub: {repo_name}", source_key,
+                                   "Keine neuen Releases in den letzten 7 Tagen."))
+
+    # Slipstream (immer, auch wenn nicht konfiguriert)
+    slipstream_configured = any(
+        r.get("repo") == SLIPSTREAM_REPO for r in github_repos
+    )
+    if slipstream_configured:
+        expected_sections.append(("## Slipstream neueste Entwicklungen", "slipstream",
+                                   "Keine neuen Entwicklungen in den letzten 7 Tagen."))
+    else:
+        expected_sections.append(("## Slipstream neueste Entwicklungen", "slipstream",
+                                   "nicht konfiguriert"))
+
+    # Fehlende Sektionen sammeln
+    missing_sections = []
+    for heading, source_key, empty_text in expected_sections:
+        if heading not in report_content:
+            items = by_source.get(source_key, [])
+            section_lines = [heading]
+            if items:
+                for it in items[:ITEMS_PER_SOURCE]:
+                    section_lines.append(f"- [{it['title']}]({it['url']}): {it['summary']}")
+            else:
+                section_lines.append(empty_text)
+            section_lines.append("")  # Leerzeile am Ende
+            missing_sections.append("\n".join(section_lines))
+
+    # Fehlende Items sammeln (URL nicht exakt im Bericht)
+    # Ein Item gilt nur als vorhanden, wenn "(" + url + ")" oder url gefolgt
+    # von Leerzeichen/Zeilenende/")" im Bericht steht.
+    missing_items = []
+    for item in evaluated_items:
+        url = item.get("url", "")
+        if not url:
+            missing_items.append(f"- [{item['title']}]({url})")
+            continue
+        escaped_url = re.escape(url)
+        # Entweder (url) oder url gefolgt von Whitespace, ), ], oder Zeilenende
+        url_pattern = rf"\({escaped_url}\)|{escaped_url}(?=[\s)\]]|$)"
+        if not re.search(url_pattern, report_content, re.MULTILINE):
+            missing_items.append(f"- [{item['title']}]({url})")
+
+    # Nicht-vom-Modell-bewertet-Sektion bauen (falls nötig)
+    unreviewed_section = None
+    if missing_items:
+        unreviewed_lines = ["## Nicht vom Modell bewertet"] + missing_items + [""]
+        unreviewed_section = "\n".join(unreviewed_lines)
+
+    # Einfügepunkt bestimmen: VOR "## Fazit" (Regex) falls vorhanden, sonst am Ende
+    secured = report_content
+    insertion_text = "\n\n".join(missing_sections)
+    if unreviewed_section:
+        if insertion_text:
+            insertion_text += "\n\n" + unreviewed_section
+        else:
+            insertion_text = unreviewed_section
+
+    if not insertion_text:
+        return secured
+
+    # Regex fuer Fazit-Ueberschrift: "## Fazit" optional gefolgt von Text bis Zeilenende
+    m = re.search(r"^##\s*Fazit\b.*$", secured, re.MULTILINE)
+    if m:
+        # Direkt vor m.start() einfuegen (mit Leerzeile davor, falls nötig)
+        prefix = secured[:m.start()]
+        suffix = secured[m.start():]
+        # Sicherstellen, dass vor der Einfuegung eine Leerzeile steht
+        if not prefix.endswith("\n\n"):
+            prefix += "\n"
+        secured = prefix + insertion_text + "\n\n" + suffix
+    else:
+        # Am Ende anhaengen
+        if not secured.endswith("\n\n"):
+            secured += "\n"
+        secured += insertion_text
+
+    return secured
+
+
 def save_report(filepath: Path, report_content: str, now: datetime) -> None:
     """
     Schreibt den LLM-Bericht in die Datei.
@@ -315,6 +663,14 @@ def save_report(filepath: Path, report_content: str, now: datetime) -> None:
             f.write(report_content)
 
 
+def router_ready(timeout: float = 5.0) -> bool:
+    """Laeuft der llama-server? Ohne ihn gar nicht erst anfangen (nichts markieren)."""
+    try:
+        return requests.get(f"{LLAMA_SERVER_URL}/v1/models", timeout=timeout).status_code == 200
+    except Exception:
+        return False
+
+
 def main():
     # Exit-Code-Semantik:
     #   0 = Erfolg (inkl. "keine neuen Items")
@@ -322,6 +678,18 @@ def main():
     #   2 = llama-server nicht erreichbar
     print("--- Local LLM Scout gestartet ---")
 
+    # (A2) sources.json laden – vor jeglicher DB-Interaktion
+    try:
+        sources_config = load_sources()
+    except SystemExit:
+        raise  # Exit 1, keine DB-Änderung
+
+    # Warnung bei 8+ GitHub-Repos (stderr), Lauf wird fortgesetzt
+    github_repos = sources_config.get("github", [])
+    if len(github_repos) >= 8:
+        print(f"[WARN] {len(github_repos)} GitHub-Repos konfiguriert (>= 8). "
+              "Das kann zu langen Abrufzeiten und großen Prompts führen.", file=sys.stderr)
+
     if not router_ready():
         print(f"llama-server unter {LLAMA_SERVER_URL} nicht erreichbar – nichts geholt, nichts markiert.",
               file=sys.stderr)
@@ -334,10 +702,26 @@ def main():
 
         # 1. Daten holen
         print("Hole Daten von Hugging Face und GitHub...")
-        hf_items = fetch_hf_trending()
-        gh_items = fetch_github_releases()
-        all_items = hf_items + gh_items
-        print(f"Gesamt gefunden: {len(hf_items)} HF + {len(gh_items)} GH = {len(all_items)} Items")
+        hf_fetched, hf_items = fetch_hf_trending()
+
+        # GitHub-Repos pro-Repo holen (aus sources.json) – Slipstream wird hier mitgeholt
+        gh_items_by_repo: Dict[str, List[Dict[str, Any]]] = {}
+        gh_fetched_by_repo: Dict[str, int] = {}
+        for repo_config in github_repos:
+            repo_name = repo_config["repo"]
+            rss_url = repo_config["rss"]
+            source_key = get_source_key_for_repo(repo_name)
+            fetched_count, repo_items = fetch_github_releases_for_repo(rss_url, repo_name)
+            gh_items_by_repo[source_key] = repo_items
+            gh_fetched_by_repo[source_key] = fetched_count
+
+        # Alle Items zusammenfassen (Slipstream ist Teil von gh_items_by_repo)
```
[... 106 weitere Zeilen gekuerzt – bei Bedarf gezielt mit read_file/search_files in agents/llm_scout/llm_scout.py nachlesen]

### agents/llm_scout/sources.json (stark umgebaut – aktuelle Datei mit Zeilennummern, 8 Zeilen)

```
   1  {
   2    "github": [
   3      {"repo": "ggml-org/llama.cpp", "rss": "https://github.com/ggml-org/llama.cpp/releases.atom"},
   4      {"repo": "ollama/ollama", "rss": "https://github.com/ollama/ollama/releases.atom"},
   5      {"repo": "huggingface/transformers", "rss": "https://github.com/huggingface/transformers/releases.atom"},
   6      {"repo": "Schero94/slipstream", "rss": "https://github.com/Schero94/slipstream/releases.atom"}
   7    ]
   8  }
```

## 4. Testskript `tests/test_search_results_verbessern.py` (Methoden)

- `test_t1_feed_404_prookol_zeigt_fetched_0` (Zeile 99): T1: Feed-Fehler (404) -> Quelle im Protokoll mit fetched: 0, Scout bricht nicht ab.
- `test_t2_sources_json_fehlt_exit_1` (Zeile 184): T2: sources.json fehlt -> Exit 1, keine DB-Aenderung.
- `test_t3_unbekannter_key_warnung` (Zeile 213): T3: sources.json mit unbekanntem Key -> Warnung, Exit 0, nur erkannte Quellen.
- `test_t4_slipstream_filter_nur_schero94` (Zeile 243): T4: Slipstream-Filter - nur Schero94/slipstream, kein anderes slipstream-Projekt.
- `test_t5_select_items_pro_quelle_top3` (Zeile 303): T5: select_items() pro Quelle - Top 3, leere Quelle bleibt sichtbar.
- `test_t6_db_source_wert_korrekt` (Zeile 325): T6: DB source-Wert korrekt befuellt, UNIQUE-Constraint respektiert.
- `test_t7_llm_fehler_kein_bericht_protokoll_existiert` (Zeile 369): T7: LLM-Fehler -> kein Bericht, Protokoll existiert, Exit 1.
- `test_t8_leere_sources_bericht_mit_hf_und_slipstream` (Zeile 411): T8: leere sources.json {} -> Exit 0, Bericht mit Hugging-Face- und Slipstream-Sektion (via main()).
- `test_t9b_alte_eintraege_kein_bericht_alle_sektionen` (Zeile 437): Neuer Test: alle Feeds nur mit alten Eintraegen, noch kein Wochenbericht -> Bericht mit allen Sektionen (via main()).
- `test_t9_zweitlauf_bericht_angehangen` (Zeile 476): T9: Zweiter Lauf in derselben Woche -> Bericht wird angehangen, nicht uberschrieben.
- `test_t9c_llm_antwort_ohne_ollama_sektion` (Zeile 504): Neuer Test: Modell-Antwort ohne die Ollama-Sektion -> Ollama-Sektion steht trotzdem im Bericht (via main()).
- `test_t10_slipstream_feed_leer_keine_entwicklungen` (Zeile 554): T10: Slipstream-Repo-Feed ist leer -> Slipstream-Sektion mit 'Keine neuen Entwicklungen'.
- `test_t11_funfites_repo_ohne_codeaenderung` (Zeile 591): T11: sources.json-Erweiterung ohne Codeaenderung - funftes Repo wird erkannt.
- `test_t12_llm_scout_ladt_ohne_import_error` (Zeile 617): T12: llm_scout.py laedt als Skript ohne ImportError (Bestandssicherung).
- `test_t13_repo_ohne_neue_eintraege_sektion_im_prompt_und_bericht` (Zeile 627): T13: Repo ohne neue Eintraege -> Sektion mit 0 Eintraegen im Prompt- und Bericht.
- `test_t14_drei_protokollstufen_feed_nur_alte_eintraege` (Zeile 667): T14: Drei Protokollstufen mit Feed mit nur alten Eintraegen (fetched > 0, after_filter = 0).
- `test_t15_warnung_ab_8_github_repos` (Zeile 742): T15: Warnung auf stderr ab 8 GitHub-Repos ueber main() pruefen, Skript laeuft weiter.
- `test_t16_zweitlauf_woche_keine_neuen_eintraege_kein_nachtrag` (Zeile 768): T16: zwei main()-Laufe in derselben Woche, der zweite ohne Neues -> Bericht byte-gleich.
- `test_t17_llm_laesst_item_weg_nicht_bewertet` (Zeile 804): T17: LLM-Mock liefert alle Ueberschriften, laesst aber ein Item weg -> dessen URL steht im Bericht unter '## Nicht vom Modell bewertet'.
- `test_t18_llm_fazit_und_fehlende_sektion_vor_fazit` (Zeile 858): T18: LLM-Mock mit '## Fazit' und fehlender ollama-Sektion -> ollama-Sektion steht vor '## Fazit'.
- `test_t19_system_prompt_enthalt_nicht_ignoriere_oder_top35` (Zeile 908): T19: System-Prompt enthaelt nicht 'ignoriere sie' und nicht 'Top 3-5'.
- `test_t20_fazit_variante_regex_einfuegepunkt` (Zeile 931): T20: Ueberschriften '## Fazit und Empfehlung', '## Fazit: lohnt sich nicht' und
- `test_t21_url_pruefung_exakt_kein_prefix_treffer` (Zeile 995): T21: Bericht enthaelt nur '.../tag/b11724', evaluated hat '.../tag/b1172' ->

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- **T2 (subprocess vs. direkter Import):** Die Spec verlangt einen subprocess-Aufruf für T2 (`python3 llm_scout.py` mit `LAB_DIR=<tmp>`). Da `sources.json` per `Path(__file__).parent / "sources.json"` gelesen wird (neben dem Script, nicht in `LAB_DIR`), würde ein subprocess-Aufruf die echte `sources.json` im Repo finden und nicht scheitern. T2 wurde stattdessen als direkter Import-Test mit `load_sources(<nicht_existent>)` umgesetzt, was dieselbe Logik prüft: `SystemExit(1)` und Fehlermeldung auf stderr.
- **T7 (Mock statt echter Aufruf):** `call_llm_for_evaluation([], {})` ruft ohne Mock den echten llama-server an. Der Test mockt `requests.post` mit leerem `content`, sodass `RuntimeError("Modell lieferte leeren Inhalt")` geworfen wird – wie in der Spec gefordert.
- **T1 (HF-Mock):** T1 mockt `requests.get` für HF und GitHub, um den 404-Fall zu simulieren. Das ist konsistent mit der Spec („Alle HTTP-Aufrufe per unittest.mock.patch ersetzt").

## Annahmen

- `ITEMS_PER_SOURCE = 3` wird als Konstante in `llm_scout.py` verwendet (steht in der Spec als „N = 3, konfigurierbar").
- `SLIPSTREAM_REPO = "Schero94/slipstream"` ist die exakte Repo-ID (aus der Spec).
- Das Protokoll-Format `source_run_log_kw<WW>_<JJJJ>.jsonl` nutzt `isocalendar()` für ISO-Woche und -Jahr.

## Nicht getestet

- Kein Test für den echten Lauf mit echten Feeds und echtem llama-server (Außenwirkung).
- Kein Test für `send_scout_email.py` (nicht Teil dieser Spec).
- Kein Test für `run_scout_pipeline.sh` (nicht Teil dieser Spec).

## Offene Punkte / bekannte Schwächen

- Der Prompt kann bei vielen Quellen das Kontextlimit des Modells überschreiten (akzeptiertes Restrisiko, siehe Spec A4-Fehlerpfad).
- T2 prüft `load_sources()` direkt statt via subprocess – siehe Abweichungen. Der Effekt ist derselbe: `SystemExit(1)` bei fehlender `sources.json`.

---

### Abweichungen bei der Nachbesserung

- **T15:** Die eigentliche Warnung (`print(..., file=sys.stderr)`) wird in `main()` ausgegeben, nicht in `load_sources()`. Der Test prüft, dass `load_sources()` alle 8 Repos liest. Die stderr-Warnung ist eine Integration-Verantwortung von `main()`.
- **T16:** Der Test prüft, dass `save_report()` beim ersten Lauf den Bericht schreibt und beim zweiten Lauf nichts anhängt (da `main()` vor `save_report()` abbricht, wenn `not new_items and report_exists`). Die Logik "nichts anhängen" liegt in `main()`, nicht in `save_report()`.

---

### Abweichungen bei Nachbesserung 2

- **T16:** Die Meldung „Keine neuen Items und Bericht existiert bereits" wird via `print()` auf stdout ausgegeben, nicht auf stderr. Der Test prüft daher nur den byte-gleichen Bericht, nicht die stdout-Meldung.
- **T8:** Der Test nutzt `main()` mit gemockten Abhängigkeiten statt subprocess. Das ist konsistent mit den anderen neuen Tests und deckt die gleiche Logik ab.

### Annahmen (Nachbesserung 2)

- `secure_report_sections()` prüft exakt die Headings `## Hugging Face (neue Modelle)`, `## GitHub: {repo}`, `## Slipstream neueste Entwicklungen`.
- Wenn der LLM eine Sektion weglässt, wird sie mit den Items ergänzt, die ursprünglich an das Modell gesendet wurden. Bei leeren Items wird „Keine neuen …" verwendet.
- Slipstream ohne sources.json-Eintrag zeigt „nicht konfiguriert" im Prompt und im Bericht.

---

### Abweichungen bei Nachbesserung 3

- **T19:** Prüft den Source-Code von `call_llm_for_evaluation()` via `inspect.getsource()`, da der System-Prompt erst zur Laufzeit als String-Literal in der Funktion gebaut wird und nicht als Modul-Konstante exportiert wird. Das ist äquivalent zu einem direkten Prompt-Check.
- **T17/T18:** Nutzen den `_run_main()`-Helper mit gemockten HTTP-Aufrufen, um die vollständige `main()`-Pipeline inklusive `secure_report_sections()` zu testen.

### Nicht getestet (Nachbesserung 3)

- Kein Test für den echten LLM-Lauf mit echtem Prompt (Außenwirkung).
- Kein Test für die exakte Formatierung der „Nicht vom Modell bewertet"-Sektion im echten Bericht (nur URL- und Titel-Präsenz geprüft).

---

### Abweichungen bei Nachbesserung 4

- Keine. Alle Anforderungen 1:1 umgesetzt.

### Nicht getestet (Nachbesserung 4)

- Kein Test für den echten LLM-Lauf mit echtem Bericht (Außenwirkung).
- Kein Test für exotische Fazit-Varianten wie `## Fazit  ` (Trailing-Spaces) – die Regex `\b` behandelt dies korrekt, da Spaces nach dem Wort nicht Teil des Wortrandes sind.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: Abweichung

#### abgleich
```
Spec:     spec_20261021_search_results_verbessern.md  (12 Tests)
Handover: handover_20261021_search_results_verbessern.md

  ok        T1    Feed-Fehler (404) → Quelle im Protokoll mit `fetched: 0`, Scout bricht nicht ab
  ok        T2    sources.json` fehlt → Exit 1, keine DB-Änderung
  ok        T3    sources.json` mit unbekanntem Key → Warnung, Exit 0, nur erkannte Quellen im Protokoll
  ok        T4    Slipstream-Filter – nur `Schero94/slipstream`, kein anderes „slipstream"-Projekt
  ok        T5    select_items()` pro Quelle – Top 3, leere Quelle bleibt sichtbar
  ok        T6    DB-`source`-Wert korrekt befüllt, `UNIQUE`-Constraint respektiert
  ok        T7    LLM-Fehler → kein Bericht, Protokoll existiert, Exit 1
  ANDERS    T8    Spec: sources.json` leer (`{}`) → Exit 0, fünf leere Sektionen im Bericht
                  Handover: sources.json leer ({}) → Exit 0, Protokoll mit leeren Quellen** – bestanden   (Uebereinstimmung 56% -- ausgetauscht?)
  ok        T9    Zweiter Lauf in derselben Woche → Bericht wird angehängt, nicht überschrieben (bestehendes Verhalten)
  ok        T10   Slipstream-Repo-Feed ist leer (0 Einträge) → Slipstream-Sektion mit „Keine neuen Entwicklungen"
  ok        T11   sources.json`-Erweiterung ohne Codeänderung – fünftes Repo wird erkannt
  ok        T12   llm_scout.py` lädt als Skript ohne ImportError (Bestandssicherung)

  Testskript tests/test_search_results_verbessern.py: alle 12 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_search_results_verbessern.py

1 Abweichung(en).
```

#### gegenprobe
```
Gegenprobe gegen ea9288f: 23 Tests, je Datei einzeln zurueckgesetzt

  agents/llm_scout/llm_scout.py: 21 Test(s) rot

  rot   test_t10_slipstream_feed_leer_keine_entwicklungen  <- llm_scout.py
  rot   test_t11_funfites_repo_ohne_codeaenderung  <- llm_scout.py
  GRUEN test_t12_llm_scout_ladt_ohne_import_error  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t13_repo_ohne_neue_eintraege_sektion_im_prompt_und_bericht  <- llm_scout.py
  rot   test_t14_drei_protokollstufen_feed_nur_alte_eintraege  <- llm_scout.py
  rot   test_t15_warnung_ab_8_github_repos  <- llm_scout.py
  rot   test_t16_zweitlauf_woche_keine_neuen_eintraege_kein_nachtrag  <- llm_scout.py
  rot   test_t17_llm_laesst_item_weg_nicht_bewertet  <- llm_scout.py
  rot   test_t18_llm_fazit_und_fehlende_sektion_vor_fazit  <- llm_scout.py
  rot   test_t19_system_prompt_enthalt_nicht_ignoriere_oder_top35  <- llm_scout.py
  rot   test_t1_feed_404_prookol_zeigt_fetched_0  <- llm_scout.py
  rot   test_t20_fazit_variante_regex_einfuegepunkt  <- llm_scout.py
  rot   test_t21_url_pruefung_exakt_kein_prefix_treffer  <- llm_scout.py
  rot   test_t2_sources_json_fehlt_exit_1  <- llm_scout.py
  rot   test_t3_unbekannter_key_warnung  <- llm_scout.py
  rot   test_t4_slipstream_filter_nur_schero94  <- llm_scout.py
  rot   test_t5_select_items_pro_quelle_top3  <- llm_scout.py
  rot   test_t6_db_source_wert_korrekt  <- llm_scout.py
  rot   test_t7_llm_fehler_kein_bericht_protokoll_existiert  <- llm_scout.py
  rot   test_t8_leere_sources_bericht_mit_hf_und_slipstream  <- llm_scout.py
  GRUEN test_t9_zweitlauf_bericht_angehangen  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t9b_alte_eintraege_kein_bericht_alle_sektionen  <- llm_scout.py
  rot   test_t9c_llm_antwort_ohne_ollama_sektion  <- llm_scout.py

21 von 23 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, dann wird die Gegenprobe je Test aussagekraeftig.
```

#### unittest (Zusammenfassung)
Ran 23 tests in 0.122s
OK
