# Verdikt: search_results_verbessern (Probe-Review, Paket v2)

**Modell:** qwen36-35b | **Datum:** 2026-10-22

## Ergebnis

**NACHBESSERN**

## Befunde

| Nr. | Anm. | Beschreibung | DV | Unb. | HV | Schw. |
|-----|------|-------------|:--:|:--:|:--:|:--:|
| B1 | A1 | HF-Filter 30 Tage statt 7 (Code Z.221 `timedelta(days=30)`) | nein | ja | ja | hoch |
| B2 | A4 | System-Prompt widerspricht sich: "Top 3-5" vs. "JEDES Item" (Z.440 vs.432) | nein | ja | nein | hoch |
| B3 | A6 | Leere `sources.json` → Slipstream zeigt "nicht konfiguriert" statt "Keine neuen…" (Z.407) | nein | ja | nein | hoch |
| B4 | T8 | `test_t8` prüft nur `load_sources({})`, nicht Exit 0 + fünf leere Sektionen | nein | ja | nein | mittel |
| B5 | T16 | `test_t16` prüft `save_report()` direkt, nicht `main()`-Abbruch bei `not new_items` | nein | ja | nein | mittel |
| B6 | T5 | Testname "leere Quelle sichtbar", prüft aber nur `select_items()`, nicht `build_prompt_sections()` | nein | ja | nein | mittel |
| B7 | T7 | Test prüft `call_llm_for_evaluation()` direkt, nicht Exit 1 + Protokoll von `main()` | nein | ja | nein | mittel |
| B8 | T15 | Test prüft nicht die stderr-Warnung bei 8+ Repos (liegt in `main()`) | nein | ja | nein | niedrig |

## Anforderungen einzeln

**A1:** Teilweise erfüllt. Protokoll vor LLM geschrieben (Z.648), korrekt. Aber HF nutzt 30-Tage-Filter statt 7 (B1).

**A2:** Erfüllt. `load_sources()` bricht bei Fehlern mit Exit 1 (Z.84–93). Unbekannte Keys mit Warnung ignoriert.

**A3:** Erfüllt. `get_source_key_for_repo()` mapt `Schero94/slipstream` → `"slipstream"`, alles andere → `github:<repo>`.

**A4:** Teilweise erfüllt. `select_items()` und `build_prompt_sections()` korrekt. Prompt-Widerspruch (B2). Absicherung `secure_report_sections()` (echter Code) trägt fehlende Sektionen nach.

**A5:** Erfüllt. `UNIQUE`-Constraint auf `url` (Z.129), Duplikate ignoriert.

**A6:** Teilweise erfüllt. Alle Sektionen gebaut, aber bei leerer `sources.json` falscher Slipstream-Text (B3). Absicherung `secure_report_sections()` im echten Code, aber nicht getestet.

## Nicht geprüft

Echter Lauf mit echten Feeds/llama-server, `send_scout_email.py`, `run_scout_pipeline.sh`, `secure_report_sections()`-Tests.
