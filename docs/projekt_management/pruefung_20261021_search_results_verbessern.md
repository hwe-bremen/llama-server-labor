# Pruefung search_results_verbessern

- Zeit: 2026-10-22 11:16
- Ruecksetzpunkt: ea9288f
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: Abweichung

## abgleich  (Exit 1)

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

## unittest  (Exit 0)

```
  RSS https://github.com/Schero94/slipstream/releases.atom: 0 fetched, cutoff: 2026-10-15
  RSS https://github.com/test/repo/releases.atom: 0 fetched, cutoff: 2026-10-15
  RSS https://github.com/test/repo/releases.atom: 3 fetched, cutoff: 2026-10-15
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 0 GH = 0 Items
Neue Items (nach DB-Abgleich): 0
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Bewerte Items (0 neue, 0 fuer LLM)...
Bericht gespeichert unter: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmp0z9bdhvu/weekly-reports/llm_scout_kw43_2026.md
Als verarbeitet markiert: 0 (Rest bleibt fuer die naechste Woche offen)
--- Skript beendet ---
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 0 GH = 0 Items
Neue Items (nach DB-Abgleich): 0
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Bewerte Items (0 neue, 0 fuer LLM)...
Bericht gespeichert unter: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmpl3f6_1ku/weekly-reports/llm_scout_kw43_2026.md
Als verarbeitet markiert: 0 (Rest bleibt fuer die naechste Woche offen)
--- Skript beendet ---
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 0 GH = 0 Items
Neue Items (nach DB-Abgleich): 0
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Keine neuen Items und Bericht existiert bereits. Skript beendet.
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 2 GH = 2 Items
Neue Items (nach DB-Abgleich): 2
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Bewerte Items (2 neue, 2 fuer LLM)...
Bericht gespeichert unter: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmp22onr3rp/weekly-reports/llm_scout_kw43_2026.md
Als verarbeitet markiert: 2 (Rest bleibt fuer die naechste Woche offen)
--- Skript beendet ---
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 0 GH = 0 Items
Neue Items (nach DB-Abgleich): 0
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Bewerte Items (0 neue, 0 fuer LLM)...
Bericht gespeichert unter: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmpjtm4epy_/weekly-reports/llm_scout_kw43_2026.md
Als verarbeitet markiert: 0 (Rest bleibt fuer die naechste Woche offen)
--- Skript beendet ---
  RSS https://github.com/ggml-org/llama.cpp/releases.atom: 1 fetched, cutoff: 2026-10-15
  RSS https://github.com/Schero94/slipstream/releases.atom: 1 fetched, cutoff: 2026-10-15
  RSS https://github.com/chenzhuofu/slipstream/releases.atom: 1 fetched, cutoff: 2026-10-15
Frage wird an LLM (unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL) gestellt...
  HTTP-Status: 200
  Roh-JSON: {
  "choices": [
    {
      "message": {
        "content": ""
      }
    }
  ]
}
  Antwortlänge: 0 Zeichen
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 0 GH = 0 Items
Neue Items (nach DB-Abgleich): 0
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Bewerte Items (0 neue, 0 fuer LLM)...
Bericht gespeichert unter: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmp5lt35xtb/weekly-reports/llm_scout_kw43_2026.md
Als verarbeitet markiert: 0 (Rest bleibt fuer die naechste Woche offen)
--- Skript beendet ---
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 0 GH = 0 Items
Neue Items (nach DB-Abgleich): 0
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Bewerte Items (0 neue, 0 fuer LLM)...
Bericht gespeichert unter: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmp4voxorl6/weekly-reports/llm_scout_kw43_2026.md
Als verarbeitet markiert: 0 (Rest bleibt fuer die naechste Woche offen)
--- Skript beendet ---
--- Local LLM Scout gestartet ---
Hole Daten von Hugging Face und GitHub...
Gesamt gefunden: 0 HF + 0 GH = 0 Items
Neue Items (nach DB-Abgleich): 0
Quellenprotokoll geschrieben: source_run_log_kw*.jsonl
Bewerte Items (0 neue, 0 fuer LLM)...
Bericht gespeichert unter: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmpef8ooru0/weekly-reports/llm_scout_kw43_2026.md
Als verarbeitet markiert: 0 (Rest bleibt fuer die naechste Woche offen)
--- Skript beendet ---
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
T15: Warnung auf stderr ab 8 GitHub-Repos ueber main() pruefen, Skript laeuft weiter. ... ok
test_t16_zweitlauf_woche_keine_neuen_eintraege_kein_nachtrag (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t16_zweitlauf_woche_keine_neuen_eintraege_kein_nachtrag)
T16: zwei main()-Laufe in derselben Woche, der zweite ohne Neues -> Bericht byte-gleich. ... ok
test_t17_llm_laesst_item_weg_nicht_bewertet (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t17_llm_laesst_item_weg_nicht_bewertet)
T17: LLM-Mock liefert alle Ueberschriften, laesst aber ein Item weg -> dessen URL steht im Bericht unter '## Nicht vom Modell bewertet'. ... ok
test_t18_llm_fazit_und_fehlende_sektion_vor_fazit (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t18_llm_fazit_und_fehlende_sektion_vor_fazit)
T18: LLM-Mock mit '## Fazit' und fehlender ollama-Sektion -> ollama-Sektion steht vor '## Fazit'. ... ok
test_t19_system_prompt_enthalt_nicht_ignoriere_oder_top35 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t19_system_prompt_enthalt_nicht_ignoriere_oder_top35)
T19: System-Prompt enthaelt nicht 'ignoriere sie' und nicht 'Top 3-5'. ... ok
test_t1_feed_404_prookol_zeigt_fetched_0 (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t1_feed_404_prookol_zeigt_fetched_0)
T1: Feed-Fehler (404) -> Quelle im Protokoll mit fetched: 0, Scout bricht nicht ab. ... Fehler beim Abrufen von https://github.com/bad/repo404/releases.atom: 404 Not Found
ok
test_t20_fazit_variante_regex_einfuegepunkt (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t20_fazit_variante_regex_einfuegepunkt)
T20: Ueberschriften '## Fazit und Empfehlung', '## Fazit: lohnt sich nicht' und ... ok
test_t21_url_pruefung_exakt_kein_prefix_treffer (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t21_url_pruefung_exakt_kein_prefix_treffer)
T21: Bericht enthaelt nur '.../tag/b11724', evaluated hat '.../tag/b1172' -> ... ok
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
test_t8_leere_sources_bericht_mit_hf_und_slipstream (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t8_leere_sources_bericht_mit_hf_und_slipstream)
T8: leere sources.json {} -> Exit 0, Bericht mit Hugging-Face- und Slipstream-Sektion (via main()). ... ok
test_t9_zweitlauf_bericht_angehangen (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t9_zweitlauf_bericht_angehangen)
T9: Zweiter Lauf in derselben Woche -> Bericht wird angehangen, nicht uberschrieben. ... ok
test_t9b_alte_eintraege_kein_bericht_alle_sektionen (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t9b_alte_eintraege_kein_bericht_alle_sektionen)
Neuer Test: alle Feeds nur mit alten Eintraegen, noch kein Wochenbericht -> Bericht mit allen Sektionen (via main()). ... ok
test_t9c_llm_antwort_ohne_ollama_sektion (tests.test_search_results_verbessern.TestSearchResultsVerbessern.test_t9c_llm_antwort_ohne_ollama_sektion)
Neuer Test: Modell-Antwort ohne die Ollama-Sektion -> Ollama-Sektion steht trotzdem im Bericht (via main()). ... ok

----------------------------------------------------------------------
Ran 23 tests in 0.122s

OK
```

## gegenprobe gegen ea9288f  (Exit 1)

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
