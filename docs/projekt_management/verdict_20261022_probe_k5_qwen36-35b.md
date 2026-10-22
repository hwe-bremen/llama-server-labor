# Verdikt: search_results_verbessern (Probe-Review)

**Modell:** qwen36-35b (unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL)  
**Datum:** 2026-10-22  
**Geprüft:** experiments/probe_k5_nb1/review_paket_probe.md  
**Urteil:** NACHBESSERN

## Ergebnis

Die Umsetzung ist strukturell sauber: `sources.json` löst die hartkodierten URLs ab, das Quellenprotokoll wird vor dem LLM-Aufruf geschrieben, Slipstream wird korrekt als eigene Quelle behandelt, und die DB-Deduplizierung funktioniert.

Zwei wesentliche Schwächen verhindern PASS:
1. A6 (Bericht zeigt "nichts Neues" pro Quelle) ist **teilweise erfüllt** – der Code baut den Prompt mit leeren Sektionen, aber der Bericht ist der LLM-Output. Das LLM kann die Sektionen ignorieren oder zusammenfassen.
2. T8 und T16 sind unvollständig getestet – der Test prüft `load_sources()` bzw. `save_report()` isoliert, nicht die Integration in `main()`.

## Befunde

| # | Anforderung | Schwere | Datenverlust | Unbemerkt | Harte Vorgabe | Begründung | Lösungsweg |
|---|---|---|---|---|---|---|---|
| B1 | A4 | mittel | nein | ja | nein | Die Anweisung "Bewerte jede Quelle getrennt" (Zeile 429–431) steht nur im System-Prompt. Der Code erzwingt nicht, dass das LLM ihr folgt. Ein LLM kann alles mischen. | Prompt-Anweisung allein genügt nicht. Entweder Output-Validierung nach dem LLM oder deterministischer Report-Bau ohne LLM. |
| B2 | A6 | hoch | nein | ja | ja | A6 verlangt: "Der Bericht enthält für jede konfigurierte Quelle eine eigene Sektion." Der Bericht ist der LLM-Output (Zeile 672). Der Code kontrolliert den LLM-Output nicht. Wenn das LLM die Sektionen ignoriert, ist A6 nicht erfüllt. | Deterministischer Report-Bau (ohne LLM) für die Sektionsstruktur, oder LLM-Output-Parsing und Ergänzung fehlender Sektionen. |
| B3 | T8 | mittel | nein | ja | nein | Spec T8 verlangt "fünf leere Sektionen im Bericht". Der Test prüft nur `load_sources({})` (Zeile 343–353), nicht den vollen Lauf. Die Bedingung `if not new_items and report_exists` in Zeile 664 wird nicht getestet. | Integrationstest: sources.json leer → main() durchlaufen → prüfen, ob Bericht fünf Sektionen enthält. |
| B4 | T16 | mittel | nein | ja | nein | Spec T16 verlangt: "Zweiter Lauf ohne neue Items → kein Anhängen." Der Test (Zeile 592–614) prüft `save_report()` direkt, nicht `main()`. Die Bedingung `if not new_items and report_exists: sys.exit(0)` (Zeile 664) wird nicht getestet. | Integrationstest: main() mit existierendem Bericht und neuen Items = 0 aufrufen → prüfen, ob kein Nachtrag. |
| B5 | T12 | niedrig | nein | nein | nein | "GRUEN" in der gegenprobe: prüft Import, der bereits vorher bestand. Test misst keine Änderung. | Kein Handlungsbedarf. |

## Anforderungen einzeln

- **A1 (Quellenverteilungsprotokoll):** ERFÜLLT. Protokoll wird vor LLM-Aufruf geschrieben (Zeile 648), alle Quellen erscheinen auch mit `fetched: 0`.
- **A2 (sources.json):** ERFÜLLT. Datei wird geladen, Exit 1 bei Fehlern, ohne Codeänderung erweiterbar.
- **A3 (Slipstream als eigene Quelle):** ERFÜLLT. `Schero94/slipstream` → `"slipstream"`, andere "slipstream"-Repos → `"github:..."`. Sektion immer vorhanden.
- **A4 (Pro-Quellen-Prompt):** TEILWEISE ERFÜLLT. Prompt enthält Sektionen (erzwungen), aber LLM-Anweisung "jede Quelle getrennt" (Zeile 429–431) wird nicht erzwungen.
- **A5 (Pro-Quellen-Dedup):** ERFÜLLT. `UNIQUE`-Constraint auf `url`, `source`-Wert korrekt.
- **A6 (Bericht zeigt "nichts Neues"):** TEILWEISE ERFÜLLT. Prompt enthält Sektionen, aber Bericht (LLM-Output) wird nicht kontrolliert. Wenn das LLM Sektionen zusammenfasst oder weglässt, ist A6 nicht erfüllt.

## Nicht geprüft

- Echter Lauf mit echten Feeds und echtem llama-server (Außenwirkung).
- `send_scout_email.py` (nicht Teil dieser Spec).
- `run_scout_pipeline.sh` (nicht Teil dieser Spec).
- T3: Unbekannter Key in sources.json – Warnung auf stderr geprüft, aber nicht im Integrationstest.
- T4: Slipstream-Filter – unit-testet `get_source_key_for_repo()` und `fetch_github_releases_for_repo()`, aber nicht im vollen `main()`-Kontext.
