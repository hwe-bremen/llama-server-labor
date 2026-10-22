# Verdikt: search_results_verbessern (Probe-Review, Paket v2)

**Modell:** qwen36-35b  
**Datum:** 2026-10-22  
**Basis:** review_paket_probe_v2.md + Code `agents/llm_scout/llm_scout.py` (692 Zeilen im Paket, echter Code gelesen)

## Ergebnis

**NACHBESSERN**

Zwei harte Vorgaben-Verstöße (HF 30-Tage-Filter statt 7, widersprüchlicher Prompt), drei Tests, die die neue Logik nicht prüfen, und ein Fehlerpfad, bei dem die Slipstream-Sektion den falschen Text ausgibt.

## Befunde

| Nr. | Anforderung | Beschreibung | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere |
|-----|-------------|-------------|:---:|:---:|:---:|:---:|
| B1 | A1 | HF-Filter: 30 Tage statt 7 Tage (Code Zeile 221: `timedelta(days=30)`) | nein | ja | ja | hoch |
| B2 | A4 | System-Prompt widerspricht sich: "Top 3-5" vs. "JEDES Item auflisten" (Zeilen 440 vs. 432) | nein | ja | nein | hoch |
| B3 | A6 | Leere `sources.json` → Slipstream-Sektion zeigt "nicht konfiguriert" statt "Keine neuen Entwicklungen" (Code Zeile 407) | nein | ja | nein | hoch |
| B4 | T8 | `test_t8` prüft nur `load_sources({})`, nicht Exit 0 + fünf leere Sektionen im Bericht | nein | ja | nein | mittel |
| B5 | T16 | `test_t16` prüft `save_report()` direkt, nicht `main()`-Abbruch bei `not new_items and report_exists` | nein | ja | nein | mittel |
| B6 | T5 | Testname "leere Quelle bleibt sichtbar", aber Test prüft nur `select_items()`, nicht `build_prompt_sections()` | nein | ja | nein | mittel |
| B7 | T7 | Test prüft `call_llm_for_evaluation()` direkt, nicht Exit 1 + kein Bericht + Protokoll von `main()` | nein | ja | nein | mittel |
| B8 | T15 | Test prüft nicht die stderr-Warnung bei 8+ Repos (liegt in `main()`, nicht in `load_sources()`) | nein | ja | nein | niedrig |

## Anforderungen einzeln

**A1 (Quellenverteilungsprotokoll):** Teilweise erfüllt. Der Code schreibt das Protokoll vor dem LLM-Aufruf (Zeile 648), korrekt. Aber der HF-Filter nutzt 30 Tage statt 7 (B1). Die Spec sagt explizit "7-Tage-Filter".

**A2 (sources.json):** Erfüllt. `load_sources()` liest die Datei, bricht bei Fehlern mit Exit 1 (Zeilen 84–93). Unbekannte Keys werden ignoriert mit Warnung (Zeile 101). B3 betrifft den Sonderfall leerer sources.json, wo die Slipstream-Sektion "nicht konfiguriert" zeigt.

**A3 (Slipstream als eigene Quelle):** Erfüllt. `get_source_key_for_repo()` mapt `Schero94/slipstream` auf `"slipstream"`, alles andere auf `github:<repo>`.

**A4 (Pro-Quellen-Selektion und Prompt):** Teilweise erfüllt. `select_items()` (Zeile 304) und `build_prompt_sections()` (Zeile 353) arbeiten korrekt. Aber der System-Prompt enthält widersprüchliche Anweisungen (B2). Die Absicherung durch `secure_report_sections()` (im echten Code, nicht im Paket) trägt fehlende Sektionen nach.

**A5 (Pro-Quellen-Dedup in der DB):** Erfüllt. `UNIQUE`-Constraint auf `url` (Zeile 129), `mark_as_processed()` (Zeile 147) ignoriert Duplikate.

**A6 (Bericht zeigt "nichts Neues" pro Quelle):** Teilweise erfüllt. `build_prompt_sections()` baut alle Sektionen (Zeilen 371–408), aber bei leerer `sources.json` zeigt Slipstream "nicht konfiguriert" statt der erwarteten Meldung (B3). Die Absicherung durch `secure_report_sections()` (echter Code) würde das nachtragen, aber der Test prüft das nicht.

## Nicht geprüft

- Echter Lauf mit echten Feeds und echtem llama-server (Außenwirkung).
- `send_scout_email.py` (nicht Teil dieser Spec).
- `run_scout_pipeline.sh` (nicht Teil dieser Spec).
- `secure_report_sections()` im echten Code: Ich habe den Code gelesen, aber keine Tests dafür gefunden. Die Funktion ist eine wichtige Absicherung für A6, aber nicht in den Tests abgedeckt.
- `router_ready()` (Zeile 536): Was passiert, wenn der llama-server zwischen `router_ready()` und `call_llm_for_evaluation()` abstürzt? Der `except Exception` in `main()` (Zeile 686) fängt das ab → Exit 1. Das Protokoll wurde bereits geschrieben (Zeile 648). Das ist korrekt.
