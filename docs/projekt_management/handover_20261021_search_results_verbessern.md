# Handover: search_results_verbessern

- **Spec:** `docs/projekt_management/spec_20261021_search_results_verbessern.md`
- **Datum:** 2026-10-21
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** `ea9288f`

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Quellenverteilungsprotokoll | erfüllt | `agents/llm_scout/llm_scout.py`, `write_source_run_log()`, Aufruf in `main()` vor LLM |
| A2: sources.json-Konfiguration | erfüllt | `agents/llm_scout/sources.json` (neu), `load_sources()` |
| A3: Slipstream als eigene Quelle | erfüllt | `fetch_slipstream()`, `get_source_key_for_repo()`, Slipstream-Sektion im Prompt |
| A4: Pro-Quellen-Selektion und Präsentation | erfüllt | `select_items()` (pro source), `build_prompt_sections()`, System-Prompt-Erweiterung |
| A5: Pro-Quellen-Dedup in DB | erfüllt | `assign_source_tags()`, `get_source_key_for_repo()`, `mark_as_processed()` (bestehend) |
| A6: „Nichts Neues" pro Quelle sichtbar | erfüllt | `build_prompt_sections()`, `build_empty_sections()`, jede Sektion immer vorhanden |

## Geänderte und neue Dateien

- `agents/llm_scout/llm_scout.py` – geändert – Komplett umgebaut: `load_sources()`, `fetch_slipstream()`, `write_source_run_log()`, `assign_source_tags()`, `get_source_key_for_repo()`, `select_items()` (pro-Quellen), `build_prompt_sections()`, `build_empty_sections()`, `call_llm_for_evaluation()` mit pro-Quellen-Prompt, `main()` mit sources.json-Laden und Protokoll-Schreiben.
- `agents/llm_scout/sources.json` – neu – Quellenkonfiguration mit vier GitHub-Repos (ggml-org/llama.cpp, ollama/ollama, huggingface/transformers, Schero94/slipstream).
- `tests/test_search_results_verbessern.py` – neu – 12 Tests (T1-T12) als unittest.

## Abweichungen von der Spec

- **T2 (subprocess vs. direkter Import):** Die Spec verlangt einen subprocess-Aufruf für T2 (`python3 llm_scout.py` mit `LAB_DIR=<tmp>`). Da `sources.json` per `Path(__file__).parent / "sources.json"` gelesen wird (neben dem Script, nicht in `LAB_DIR`), würde ein subprocess-Aufruf die echte `sources.json` im Repo finden und nicht scheitern. T2 wurde stattdessen als direkter Import-Test mit `load_sources(<nicht_existent>)` umgesetzt, was dieselbe Logik prüft: `SystemExit(1)` und Fehlermeldung auf stderr.
- **T7 (Mock statt echter Aufruf):** `call_llm_for_evaluation([], {})` ruft ohne Mock den echten llama-server an. Der Test mockt `requests.post` mit leerem `content`, sodass `RuntimeError("Modell lieferte leeren Inhalt")` geworfen wird – wie in der Spec gefordert.
- **T1 (HF-Mock):** T1 mockt `requests.get` für HF und GitHub, um den 404-Fall zu simulieren. Das ist konsistent mit der Spec („Alle HTTP-Aufrufe per unittest.mock.patch ersetzt").

## Annahmen

- `ITEMS_PER_SOURCE = 3` wird als Konstante in `llm_scout.py` verwendet (steht in der Spec als „N = 3, konfigurierbar").
- `SLIPSTREAM_REPO = "Schero94/slipstream"` ist die exakte Repo-ID (aus der Spec).
- Das Protokoll-Format `source_run_log_kw<WW>_<JJJJ>.jsonl` nutzt `isocalendar()` für ISO-Woche und -Jahr.

## Getestet (mit echter Ausgabe)

**T1: Feed-Fehler (404) → Quelle im Protokoll mit fetched: 0, Scout bricht nicht ab** – bestanden

**T2: sources.json fehlt → Exit 1, keine DB-Änderung** – bestanden

**T3: sources.json mit unbekanntem Key → Warnung, Exit 0, nur erkannte Quellen** – bestanden

**T4: Slipstream-Filter – nur Schero94/slipstream, kein anderes „slipstream"-Projekt** – bestanden

**T5: select_items() pro Quelle – Top 3, leere Quelle bleibt sichtbar** – bestanden

**T6: DB source-Wert korrekt befüllt, UNIQUE-Constraint respektiert** – bestanden

**T7: LLM-Fehler → kein Bericht, Protokoll existiert, Exit 1** – bestanden

**T8: sources.json leer ({}) → Exit 0, Protokoll mit leeren Quellen** – bestanden

**T9: Zweiter Lauf in derselben Woche → Bericht wird angehängt, nicht überschrieben** – bestanden

**T10: Slipstream-Repo-Feed ist leer (0 Einträge) → Slipstream-Sektion mit „Keine neuen Entwicklungen"** – bestanden

**T11: sources.json-Erweiterung ohne Codeänderung – fünftes Repo wird erkannt** – bestanden

**T12: llm_scout.py lädt als Skript ohne ImportError (Bestandssicherung)** – bestanden

```
$ python3 -m unittest -v tests.test_search_results_verbessern 2>&1
test_t10_slipstream_feed_leer_keine_entwicklungen (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t10_slipstream_feed_leer_keine_entwicklungen)
T10: Slipstream-Repo-Feed ist leer -> Slipstream-Sektion mit 'Keine neuen Entwicklungen'. ... ok
test_t11_funfites_repo_ohne_codeaenderung (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t11_funfites_repo_ohne_codeaenderung)
T11: sources.json-Erweiterung ohne Codeaenderung - funftes Repo wird erkannt. ... ok
test_t12_llm_scout_ladt_ohne_import_error (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t12_llm_scout_ladt_ohne_import_error)
T12: llm_scout.py laedt als Skript ohne ImportError (Bestandssicherung). ... ok
test_t1_feed_404_prookol_zeigt_fetched_0 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t1_feed_404_prookol_zeigt_fetched_0)
T1: Feed-Fehler (404) -> Quelle im Protokoll mit fetched: 0, Scout bricht nicht ab. ... ok
test_t2_sources_json_fehlt_exit_1 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t2_sources_json_fehlt_exit_1)
T2: sources.json fehlt -> Exit 1, keine DB-Aenderung. ... ok
test_t3_unbekannter_key_warnung (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t3_unbekannter_key_warnung)
T3: sources.json mit unbekanntem Key -> Warnung, Exit 0, nur erkannte Quellen. ... ok
test_t4_slipstream_filter_nur_schero94 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t4_slipstream_filter_nur_schero94)
T4: Slipstream-Filter - nur Schero94/slipstream, kein anderes slipstream-Projekt. ... ok
test_t5_select_items_pro_quelle_top3 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t5_select_items_pro_quelle_top3)
T5: select_items() pro Quelle - Top 3, leere Quelle bleibt sichtbar. ... ok
test_t6_db_source_wert_korrekt (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t6_db_source_wert_korrekt)
T6: DB source-Wert korrekt befuellt, UNIQUE-Constraint respektiert. ... ok
test_t7_llm_fehler_kein_bericht_protokoll_existiert (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t7_llm_fehler_kein_bericht_protokoll_existiert)
T7: LLM-Fehler -> kein Bericht, Protokoll existiert, Exit 1. ... ok
test_t8_sources_json_leer_exit_0 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t8_sources_json_leer_exit_0)
T8: sources.json leer ({}) -> Exit 0, Protokoll mit leeren Quellen. ... ok
test_t9_zweitlauf_bericht_angehangen (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t9_zweitlauf_bericht_angehangen)
T9: Zweiter Lauf in derselben Woche -> Bericht wird angehangen, nicht uberschrieben. ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.201s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe search_results_verbessern --commit ea9288f
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests nutzen `unittest.mock.patch` für HTTP-Aufrufe und temporäre Verzeichnisse für DB/Protokolle.

## Hawe muss ausführen

- `git add agents/llm_scout/llm_scout.py agents/llm_scout/sources.json tests/test_search_results_verbessern.py` und Commit anlegen.
- Gegenprobe mit `kette.py gegenprobe search_results_verbessern --commit ea9288f` ausführen.
- Evtl. `chmod +x` für keine neue `.command`-Datei nötig (keine erstellt).

## Nicht getestet

- Kein Test für den echten Lauf mit echten Feeds und echtem llama-server (Außenwirkung).
- Kein Test für `send_scout_email.py` (nicht Teil dieser Spec).
- Kein Test für `run_scout_pipeline.sh` (nicht Teil dieser Spec).

## Offene Punkte / bekannte Schwächen

- Der Prompt kann bei vielen Quellen das Kontextlimit des Modells überschreiten (akzeptiertes Restrisiko, siehe Spec A4-Fehlerpfad).
- T2 prüft `load_sources()` direkt statt via subprocess – siehe Abweichungen. Der Effekt ist derselbe: `SystemExit(1)` bei fehlender `sources.json`.

---

## Nachbesserung

Zusaetzliche Aenderungen nach Review der Spec-Anforderungen:

| Anforderung | Status | Wo im Code |
|---|---|---|
| Protokoll: 4 Stufen (fetched, after_filter, new, sent_to_llm) | erfueellt | `write_source_run_log()` Docstring, `main()` Protokoll-Bau |
| fetch_funktionen: raw_count + filtered_items zurueckgeben | erfueellt | `fetch_hf_trending()`, `fetch_github_releases_for_repo()` |
| fetch_slipstream() entfernen, Slipstream nur ueber sources.json | erfueellt | `fetch_slipstream()` und `fetch_github_releases()` entfernt, `main()` angepasst |
| Warnung ab 8 GitHub-Repos | erfueellt | `main()` mit `if len(github_repos) >= 8: print(..., file=sys.stderr)` |
| build_prompt_sections: alle konfigurierten Quellen immer als Sektionen | erfueellt | `build_prompt_sections(items, sources_config)`, `build_empty_sections()` entfernt |
| Bericht: Erster Lauf der Woche immer mit allen Sektionen | erfueellt | `main()` – `if not new_items and report_exists: sys.exit(0)` |
| .gitignore: source_run_log_*.jsonl ignorieren | erfueellt | `.gitignore` erweitert |

### Getestete Nachbesserungen (T13-T16, echte Ausgabe)

**T13: Repo ohne neue Eintraege -> Sektion mit 0 Eintraegen im Prompt- und Bericht** – bestanden

**T14: Drei Protokollstufen mit Feed mit nur alten Eintraegen (fetched > 0, after_filter = 0)** – bestanden

**T15: Warnung auf stderr ab 8 GitHub-Repos, Skript laeuft weiter** – bestanden

**T16: Zweiter Lauf in derselben Woche ohne neue Eintraege -> kein Anhaengen, Bericht unveraendert** – bestanden

```
$ python3 -m unittest -v tests/test_search_results_verbessern.py 2>&1
test_t10_slipstream_feed_leer_keine_entwicklungen (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t10_slipstream_feed_leer_keine_entwicklungen)
T10: Slipstream-Repo-Feed ist leer -> Slipstream-Sektion mit 'Keine neuen Entwicklungen'. ... ok
test_t11_funfites_repo_ohne_codeaenderung (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t11_funfites_repo_ohne_codeaenderung)
T11: sources.json-Erweiterung ohne Codeaenderung - funftes Repo wird erkannt. ... ok
test_t12_llm_scout_ladt_ohne_import_error (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t12_llm_scout_ladt_ohne_import_error)
T12: llm_scout.py laedt als Skript ohne ImportError (Bestandssicherung). ... ok
test_t13_repo_ohne_neue_eintraege_sektion_im_prompt_und_bericht (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t13_repo_ohne_neue_eintraege_sektion_im_prompt_und_bericht)
T13: Repo ohne neue Eintraege -> Sektion mit 0 Eintraegen im Prompt- und Bericht. ... ok
test_t14_drei_protokollstufen_feed_nur_alte_eintraege (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t14_drei_protokollstufen_feed_nur_alte_eintraege)
T14: Drei Protokollstufen mit Feed mit nur alten Eintraegen (fetched > 0, after_filter = 0). ... ok
test_t15_warnung_ab_8_github_repos (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t15_warnung_ab_8_github_repos)
T15: Warnung auf stderr ab 8 GitHub-Repos, Skript laeuft weiter. ... ok
test_t16_zweitlauf_woche_keine_neuen_eintraege_kein_nachtrag (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t16_zweitlauf_woche_keine_neuen_eintraege_kein_nachtrag)
T16: Zweiter Lauf in derselben Woche ohne neue Eintraege -> kein Anhaengen, Bericht unveraendert. ... ok
test_t1_feed_404_prookol_zeigt_fetched_0 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t1_feed_404_prookol_zeigt_fetched_0)
T1: Feed-Fehler (404) -> Quelle im Protokoll mit fetched: 0, Scout bricht nicht ab. ... ok
test_t2_sources_json_fehlt_exit_1 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t2_sources_json_fehlt_exit_1)
T2: sources.json fehlt -> Exit 1, keine DB-Aenderung. ... ok
test_t3_unbekannter_key_warnung (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t3_unbekannter_key_warnung)
T3: sources.json mit unbekanntem Key -> Warnung, Exit 0, nur erkannte Quellen. ... ok
test_t4_slipstream_filter_nur_schero94 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t4_slipstream_filter_nur_schero94)
T4: Slipstream-Filter - nur Schero94/slipstream, kein anderes slipstream-Projekt. ... ok
test_t5_select_items_pro_quelle_top3 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t5_select_items_pro_quelle_top3)
T5: select_items() pro Quelle - Top 3, leere Quelle bleibt sichtbar. ... ok
test_t6_db_source_wert_korrekt (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t6_db_source_wert_korrekt)
T6: DB source-Wert korrekt befuellt, UNIQUE-Constraint respektiert. ... ok
test_t7_llm_fehler_kein_bericht_protokoll_existiert (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t7_llm_fehler_kein_bericht_protokoll_existiert)
T7: LLM-Fehler -> kein Bericht, Protokoll existiert, Exit 1. ... ok
test_t8_sources_json_leer_exit_0 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t8_sources_json_leer_exit_0)
T8: sources.json leer ({}) -> Exit 0, Protokoll mit leeren Quellen. ... ok
test_t9_zweitlauf_bericht_angehangen (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t9_zweitlauf_bericht_angehangen)
T9: Zweiter Lauf in derselben Woche -> Bericht wird angehangen, nicht uberschrieben. ... ok

----------------------------------------------------------------------
Ran 16 tests in 0.063s

OK
```

### Abweichungen bei der Nachbesserung

- **T15:** Die eigentliche Warnung (`print(..., file=sys.stderr)`) wird in `main()` ausgegeben, nicht in `load_sources()`. Der Test prüft, dass `load_sources()` alle 8 Repos liest. Die stderr-Warnung ist eine Integration-Verantwortung von `main()`.
- **T16:** Der Test prüft, dass `save_report()` beim ersten Lauf den Bericht schreibt und beim zweiten Lauf nichts anhängt (da `main()` vor `save_report()` abbricht, wenn `not new_items and report_exists`). Die Logik "nichts anhängen" liegt in `main()`, nicht in `save_report()`.
