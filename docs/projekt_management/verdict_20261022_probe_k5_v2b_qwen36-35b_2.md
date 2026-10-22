# Verdikt: search_results_verbessern (Probe-Review, v2)

**Modell:** qwen36-35b  
**Datum:** 2026-10-22  
**Urteil:** NACHBESSERN

## Ergebnis

Kernziele (Quellenprotokoll, sources.json, Slipstream-Trennung, pro-Quellen-Prompt) erfüllt. Drei Befunde „hoch" aus A6 (fünf Sektionen immer vorhanden) und A4 (LLM-Anweisungen nicht erzwungen).

## Befunde

| Nr. | Anm. | DV | UB | HV | Schwere | Begründung |
|-----|------|:--:|:--:|:--:|:--:|-----|
| B1 | A6 | nein | ja | ja | hoch | Bei `sources.json = {}` fehlen vier von fünf Sektionen. `build_prompt_sections()` baut Sektionen nur aus `sources_config.get("github", [])` (Zeile 384). Leere Config → keine GitHub- und keine Slipstream-Sektion. Anforderung: „Alle fünf Sektionen sind **immer** vorhanden." |
| B2 | A4 | nein | ja | — | hoch | „Bewerte jede Quelle getrennt" und „Verwerfe kein Item ohne Begründung" (System-Prompt Zeile 429–431) stehen nur im Prompt. Code prüft LLM-Output nicht. Ein LLM, der Quellen verschmelzt oder Items stillschweigend verwirft, bleibt unbemerkt. |
| B3 | A4 | nein | ja | — | hoch | T5 (Zeile 235) prüft nur `select_items()`, nicht `build_prompt_sections()` mit leeren Quellen. T8 (Zeile 343) prüft nur `load_sources()`, nicht die Prompt-Bildung. Kein Test belegt A6 bei leerer Config. |

## Anforderungen einzeln

**A1 (Quellenprotokoll):** Erfüllt. Protokoll vor LLM-Aufruf (Zeile 648 vor 672). Format korrekt. Kein File-Lock (Parallelrisiko).  
**A2 (sources.json):** Erfüllt. Fehlen/Ungültig → Exit 1 (Zeile 84–93). Unbekannte Keys ignoriert mit Warnung.  
**A3 (Slipstream):** Erfüllt. Source-Key-Zuordnung korrekt (Zeile 188–190). Eigene Sektion (Zeile 400–406).  
**A4 (Pro-Quellen-Prompt):** Teilweise erfüllt. `select_items()` und `build_prompt_sections()` bauen Sektionen. LLM-Output nicht validiert (B2, B3).  
**A5 (DB-Dedup):** Erfüllt. UNIQUE auf url (Zeile 150–156). `assign_source_tags()` setzt korrekten source-Wert.  
**A6 (Sektionen immer vorhanden):** Nicht erfüllt. Leere sources.json → nur HF-Sektion (B1).

## Nicht geprüft

Echter Lauf mit echten Feeds/llama-server, `send_scout_email.py`, `run_scout_pipeline.sh`, Parallel-Läufe, Mitternachtsgrenze (Protokoll nutzt `datetime.now()`, Bericht übergebenes `now` — Risiko bei KW-Wechsel).
