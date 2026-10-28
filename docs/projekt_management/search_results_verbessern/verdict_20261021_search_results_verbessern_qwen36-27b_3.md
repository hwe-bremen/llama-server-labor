# Verdikt: search_results_verbessern (Review 3, nach Nachbesserung 2)

- **Spec:** `docs/projekt_management/spec_20261021_search_results_verbessern.md`
- **Handover:** `docs/projekt_management/handover_20261021_search_results_verbessern.md`
- **Datum:** 2026-10-22
- **Modell:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL (Reasoning aus)
- **Hinweis:** Kontext bei 94 % – Verdikt vom Modell nur im Chat ausgegeben (Kurzform), von Claude wörtlich in diese Datei übernommen.

## Ergebnis

**PASS** – Alle sechs Anforderungen (A1–A6) sind im Code erfüllt, die Spec widerspricht der Anforderung nicht, und keine harte Vorgabe wird verletzt.

## Befunde

| # | Schwere | Datei:Zeile | Befund |
|---|---|---|---|
| 1 | niedrig | `llm_scout.py:747` | `secure_report_sections()` hängt fehlende Sektionen am Berichtsende an – das LLM kann die `## Fazit`-Sektion vor ihnen platzieren, wodurch die nachgetragenen Sektionen nach dem Fazit stehen. |
| 2 | niedrig | `tests/test_search_results_verbessern.py:75` | `_run_main()` patcht module-level-Konstanten (`BASE_DIR`, `DB_PATH`) – das funktioniert im Test, simuliert aber nicht den echten Einstieg via `run_scout_pipeline.sh` mit `LAB_DIR`-Umgebungsvariable. |
| 3 | niedrig | `llm_scout.py:633` | Warnung ab 8 Repos nutzt `>= 8` – die Anforderung sagt „Warnung ab 8 Repos", das ist konsistent, aber bei genau 8 Repos warnt der Code, was im Normalbetrieb (4 Repos) nie relevant wird. |

## Nicht geprüft

Echter Lauf mit llama-server, E-Mail-Versand via `send_scout_email.py`, Gegenprobe mit `kette.py gegenprobe` (Hawe ausführen).
