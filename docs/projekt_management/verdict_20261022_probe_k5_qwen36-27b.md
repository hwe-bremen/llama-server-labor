# Verdikt: search_results_verbessern (Probe-Review)

- **Spec:** `spec_20261021_search_results_verbessern.md` (im Review-Paket)
- **Handover:** `handover_20261021_search_results_verbessern.md` (im Review-Paket)
- **Datum:** 2026-10-22
- **Modell:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `experiments/probe_k5_nb1/agents/llm_scout/llm_scout.py`, `experiments/probe_k5_nb1/agents/llm_scout/sources.json`, `experiments/probe_k5_nb1/review_paket_probe.md`

Dateiname: `verdict_20261022_probe_k5_qwen36-27b.md`

## Ergebnis

**NACHBESSERN** – Drei Befunde „hoch": (1) Hugging Face nicht in `sources.json` konfigurierbar, widerspricht Anforderung „ohne Codeänderung erweiterbar"; (2) `GITHUB_RELEASES_RSS` hart kodiert, wird aber nicht genutzt – veraltet und irreführend; (3) Items, die selektiert und an LLM gesendet, aber nach LLM-Fehler nie markiert werden (korrekt), doch das Protokoll sagt `sent_to_llm`, als wären sie verarbeitet – begriffliche Verwirrung, kein Datenverlust.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | ja | hoch | `llm_scout.py:38-39` | `HF_API_URL` hart kodiert; Hugging Face steht nicht in `sources.json`. Anforderung A2 verlangt „ohne Codeänderung erweiterbar" – HF ist eine Quelle, die nur durch Codeänderung entfernt/ergänzt werden kann. | `sources.json` um einen Key `huggingface` erweitern; HF-URL aus Config lesen; `GITHUB_RELEASES_RSS` entfernen. |
| 2 | nein | ja | ja | hoch | `llm_scout.py:40-44` | `GITHUB_RELEASES_RSS` hart kodiert und wird im neuen Code nicht referenziert. Veraltete Konstante, die bei Code-Reviews irreführt und bei versehentlichem Re-Referenzieren einen Parallel-Pfad öffnet. | Konstante entfernen. |
| 3 | nein | nein | nein | niedrig | `llm_scout.py:625-627` | `sent_to_llm` im Protokoll listet Items, die an das LLM gesendet wurden – nicht Items, die im Bericht erschienen sind. Bei LLM-Fehler nach Protokoll-Schrieb (Zeile 648) stehen die Items als `sent_to_llm`, wurden aber nicht bewertet. Begriffe „gesendet" vs. „verarbeitet" sind im Protokoll nicht trennscharf. | Protokoll um Feld `evaluated` ergänzen (Items, die tatsächlich im Bericht landen). |
## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Quellenprotokoll JSONL, vor LLM-Aufruf | erfüllt | `llm_scout.py:325-348`, Aufruf Zeile 648 |
| A2 | sources.json, ohne Codeänderung erweiterbar | **teilweise** | `llm_scout.py:38-39`: HF hart kodiert, nicht in sources.json |
| A3 | Slipstream eigene Sektion, nur Schero94/slipstream | erfüllt | `llm_scout.py:188-190`, `387-406` |
| A4 | Pro-Quellen-Prompt, jede Quelle separat | erfüllt | `llm_scout.py:353-408`, `411-510` |
| A5 | DB source-Wert korrekt, UNIQUE | erfüllt | `llm_scout.py:147-156`, `181-190` |
| A6 | „Nichts Neues" pro Quelle im Bericht | **teilweise** | `llm_scout.py:429-431`: Nur im Prompt verlangt, nicht erzwert. LLM kann Sektion weglassen. |

**Pflichtfragen pro Anforderung:**

- **A1 (a) Erzwungen:** Ja – Code schreibt Protokoll deterministisch (Zeile 648).
- **A1 (b) Leer:** Leere Quelle → `fetched: 0, after_filter: 0, sent_to_llm: []` (Zeilen 631-645). OK.
- **A1 (c) Markiert, nicht gezeigt:** `sent_to_llm` kann Items enthalten, die nach LLM-Fehler nie bewertet wurden. Kein Nutzer sieht diese Diskrepanz. (Befund #3)
- **A1 (d) Ins Leere:** Nein.

- **A2 (a) Erzwungen:** Nein – HF ist hart kodiert, nicht in sources.json. (Befund #1)
- **A2 (b) Leer:** `{}` → `github_repos` ist `[]`, nur HF-Sektion im Prompt (Zeile 374-381). OK, aber HF fehlt aus Config.
- **A2 (c/d):** Nicht relevant.

- **A3 (a) Erzwungen:** Ja – `get_source_key_for_repo()` filtert exakt `Schero94/slipstream` (Zeile 188).
- **A3 (b) Leer:** Kein Slipstream-Feed → Sektion mit „Keine neuen Entwicklungen" (Zeile 406). OK.
- **A3 (c/d):** Kein Problem.

- **A4 (a) Erzwungen:** Prompt-Sektionen sind erzwungen (Code baut sie), aber LLM-Ausgabe ist nur im Prompt verlangt (Zeile 429-431). (Befund A6 teilweise)
- **A4 (b) Leer:** Leere Quelle → „Keine neuen Releases..." im Prompt (Zeile 396). OK.
- **A4 (c) Markiert, nicht gezeigt:** Items in `evaluated` werden markiert (Zeile 679-680), auch wenn LLM sie im Bericht weglässt. Das ist beabsichtigt (A4-Akzeptanz 4: „Begründung für verworfene Items").
- **A4 (d) Ins Leere:** Nein.

- **A5 (a) Erzwungen:** Ja – `mark_as_processed()` setzt source explizit (Zeile 150-152).
- **A5 (b-d):** Kein Problem.

- **A6 (a) Erzwungen:** Nein – „Keine neuen Entwicklungen" steht nur im System-Prompt (Zeile 429-431). LLM kann Sektion weglassen.
- **A6 (b) Leer:** Prompt zeigt Sektion, aber LLM-Output ist unkontrolliert.
- **A6 (c/d):** Kein Problem.

## Handover gegen Code

- T2-Abweichung (direkter Import statt subprocess): Im Handover begründet, Code bestätigt (Zeile 84-86). In Ordnung.
- T7-Mock: Handover sagt Mock mit leerem content → `RuntimeError`. Code Zeile 508-509 bestätigt. In Ordnung.
- „Kein Test für echten Lauf": Im Handover genannt. Bestätigt.

**Tests:** T9, T12, T16 sind GRUEN in der Gegenprobe (werden mit alter Datei nicht rot). T9 prüft bestehendes Anhängen-Verhalten (in Ordnung). T12 prüft ImportError (Bestandssicherung, in Ordnung). T16 prüft, dass Zweiterlauf ohne neue Items nichts anhängt – prüft Bestehendes (in Ordnung).
## Nicht geprüft

- **Kann Hawe selbst prüfen:** Echter Lauf mit llama-server, Prüfung ob LLM tatsächlich alle Sektionen im Output liefert (A6).
- **Braucht externe Quelle:** Ob `chenzhuofu/slipstream` im realen Feed auftaucht (T4-Szenario).

## Abweichende Meinung

- Keine.