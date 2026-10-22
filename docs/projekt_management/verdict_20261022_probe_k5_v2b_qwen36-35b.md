# Verdikt: search_results_verbessern (Probe-Review, v2)

**Modell:** qwen36-35b  
**Datum:** 2026-10-22  
**Urteil:** NACHBESSERN

## Ergebnis

Die Umsetzung erfüllt die Kernziele der Anforderung (Quellenprotokoll, sources.json, Slipstream-Trennung, pro-Quellen-Prompt). Es sind jedoch Befunde mit „hoch" offen, die das Verdikt auf NACHBESSERN setzen.

## Befunde

| Nr. | Anforderung | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Begründung |
|-----|-------------|:---:|:---:|:---:|:---:|-----|
| B1 | A4 | nein | **ja** | — | hoch | A4 verlangt: „Das LLM-Prompt zeigt jede Quelle als eigene, klar beschriftete Sektion." Der Code ruft `build_prompt_sections(items, sources_config)` (Zeile 466), wobei `items` nur die *neuen* Items sind (Zeile 597–600: `new_items = []`). Wenn eine Quelle 0 neue Items hat, erscheint sie trotzdem im Prompt als leere Sektion (Zeile 390–396: `by_source.get(source_key, [])` → leer → „Keine neuen Releases"). Das ist korrekt. **ABER:** Das LLM-Output-Format (System-Prompt Zeile 443–459) verlangt vom LLM, für jede Quelle einen Abschnitt zu schreiben. Der Code prüft **nicht**, ob das LLM das einhält. Es steht nur im Prompt — keine Erzwingung. (Pflichtfrage a: nur verlangt.) |
| B2 | A4 | nein | **ja** | — | hoch | A4 verlangt: „Verwerfe kein Item ohne eine einzeilige Begründung." Der Code stellt diese Anweisung nur im System-Prompt (Zeile 431). Es gibt keine nachgelagerte Prüfung, ob das LLM das einhält. Ein LLM, der Items stillschweigend verwirft, wird nicht erkannt. (Pflichtfrage a: nur verlangt.) |
| B3 | A6 | nein | **ja** | **ja** | hoch | A6 verlangt: „Alle fünf Sektionen sind **immer** vorhanden, unabhängig davon, welche Quelle Items geliefert hat." `build_prompt_sections()` (Zeile 353–408) baut Sektionen aus `sources_config.get("github", [])` (Zeile 384). Wenn `sources.json` leer `{}` ist, ist `github_repos = []`. Die GitHub-Sektionen (inkl. Slipstream) werden **nicht** gebaut. Nur die HF-Sektion erscheint. Der Test T8 (Zeile 343–351) prüft nur `load_sources()` → `{}`, nicht `build_prompt_sections()` mit leerer Config. Das Handover bestätigt: T8 prüft nur `load_sources()`. `build_prompt_sections([], {"github": []})` erzeugt keine GitHub- und keine Slipstream-Sektion. (Pflichtfrage b: leerer Fall nicht geprüft.) |
| B4 | A6 | nein | **ja** | **ja** | hoch | Wie B3: Bei `sources.json = {}` fehlen vier von fünf Sektionen im Prompt und damit im Bericht. Die Anforderung sagt explizit: „Alle fünf Sektionen sind **immer** vorhanden." Das ist ein Verstoß gegen eine harte Vorgabe. |
| B5 | A1 | nein | **ja** | — | hoch | A1 verlangt: „Das Protokoll wird **vor** dem LLM-Aufruf geschrieben." Code Zeile 648: `write_source_run_log(BASE_DIR, source_log_data)` — korrekt vor Zeile 672 `call_llm_for_evaluation()`. **ABER:** Das Protokoll enthält die Stufe `new` (Zeile 634, 643), die auf `len(new_by_source.get(...))` basiert. `new_by_source` wird aus `new_items` gebaut (Zeile 606–609), die erst nach DB-Abgleich (Zeile 597–600) existiert. Das ist korrekt. **ABER:** Die Stufe `sent_to_llm` enthält nur `{url, title}` (Zeile 625–627). Die Spec (A1-Akzeptanz) verlangt: „die konkrete Liste der Items, die an den LLM-Prompt übergeben werden (URL + Titel)". Das ist erfüllt. **ABER:** `write_source_run_log` öffnet die Datei im Append-Modus (Zeile 347: `'a'`). Wenn zwei Läufe parallel sind, kann es zu konkurrierenden Writes kommen. Kein Lock. Bei einem Absturz mitten im Write bleibt die Datei korrupt. (Pflichtfrage d: Absicherung läuft ins Leere — kein Lock, kein atomic write.) |
| B6 | A4 | nein | **ja** | — | hoch | A4 verlangt: „Jede Quelle wird unabhängig bewertet." Das LLM-Prompt (Zeile 468–474) stellt `items_text` (die Sektionen) zusammen, aber der User-Prompt sagt nur „Bitte bewerte jede Quelle getrennt und erstelle das Infopaper." (Zeile 473). Das ist eine Aufforderung, keine Erzwingung. Der Code validiert den LLM-Output nicht. Wenn das LLM alle Quellen in einen Top-Fazit-Block verschmelzt, bleibt das unbemerkt. (Pflichtfrage a: nur verlangt.) |
| B7 | A3 | nein | **ja** | — | mittel | A3 verlangt: „Kein anderes Projekt namens Slipstream darf in dieser Sektion erscheinen." Der Code filtert in `get_source_key_for_repo()` (Zeile 188–190) nur `SLIPSTREAM_REPO == "Schero94/slipstream"`. Das ist korrekt für die Source-Key-Zuordnung. **ABER:** Der Prompt (System-Prompt Zeile 457–459) enthält nur „## Slipstream neueste Entwicklungen" ohne explizite Nennung von `Schero94`. Ein LLM könnte in der Zusammenfassung andere Slipstream-Projekte erwähnen. Der Code erzwingt das nicht im Output. (Pflichtfrage a: nur verlangt.) |
| B8 | T5 | nein | **ja** | — | hoch | T5 verlangt: „Der LLM-Prompt enthält die Sektion für Repo B mit 'Keine neuen Releases in den letzten 7 Tagen.'" Der Test T5 (Zeile 235–255) prüft nur `select_items()` — er testet nicht `build_prompt_sections()`. Er prüft, dass `select_items()` pro Quelle Top-N liefert und leere Quellen 0 Items haben. Er prüft **nicht**, ob die leere Sektion im Prompt erscheint. (Pflichtfrage: Test prüft Bestehendes, nicht die neue Logik.) |
| B9 | T8 | nein | **ja** | — | hoch | T8 (Handover: „ANDERS") prüft nur `load_sources(Path("/tmp")/sources.json)` mit Inhalt `"{}"`. Es wird **kein** `build_prompt_sections()` aufgerufen, **kein** `main()` durchlaufen. Die Anforderung T8 verlangt: „fünf leere Sektionen im Bericht". Der Test belegt das nicht. |
| B10 | T9 | nein | **ja** | — | mittel | T9 (Handover: „GRUEN — wird mit keiner alten Datei rot") prüft nur `save_report()`. Das ist Bestehendes, keine neue Logik. Die Bedingung `if not new_items and report_exists: sys.exit(0)` (Zeile 664–668) wird nicht getestet. |
| B11 | T12 | nein | **ja** | — | mittel | T12 (Handover: „GRUEN — wird mit keiner alten Datei rot") prüft `runpy.run_path()`. Das ist Bestehendes. |
| B12 | T16 | nein | **ja** | — | mittel | T16 (Handover: „GRUEN — wird mit keiner alten Datei rot") prüft nur `save_report()` mit einem Aufruf. Kein zweiter Aufruf, kein `main()`-Pfad. Test ist eine Tautologie. |

## Anforderungen einzeln

### A1: Quellenverteilungsprotokoll (B)
**Erfüllt mit Abweichungen.** Protokoll wird vor LLM-Aufruf geschrieben (Zeile 648 vor 672). Format ist korrekt (fetched, after_filter, new, sent_to_llm). **B5** betrifft das Fehlen eines File-Locks.

### A2: Erweiterte Quellenkonfiguration in sources.json
**Erfüllt.** `load_sources()` liest die Datei, bricht mit Exit 1 bei Fehlen/ungültigem JSON (Zeile 84–93). Unbekannte Keys werden ignoriert mit Warnung (Zeile 100–102). Warnung ab 8 Repos in `main()` (Zeile 559–561).

### A3: Slipstream als eigene, klar abgegrenzte Quelle
**Teilweise erfüllt.** Source-Key-Zuordnung ist korrekt (Zeile 188–190). `build_prompt_sections()` baut eine eigene Slipstream-Sektion (Zeile 400–406). **B1, B7** betreffen die fehlende LLM-Output-Validierung.

### A4: Pro-Quellen-Selektion und getrennte Präsentation
**Teilweise erfüllt.** `select_items()` gruppiert pro Quelle und wählt Top-N (Zeile 304–320). `build_prompt_sections()` baut alle Sektionen (Zeile 353–408). **B1, B2, B6** betreffen die fehlende Erzwingung der LLM-Anweisungen.

### A5: Pro-Quellen-Dedup in der DB
**Erfüllt.** `mark_as_processed()` nutzt UNIQUE-Constraint auf url (Zeile 150–156). `assign_source_tags()` setzt den korrekten source-Wert (Zeile 161–178).

### A6: Bericht zeigt „nichts Neues" pro Quelle
**Nicht erfüllt.** Bei `sources.json = {}` fehlen vier von fünf Sektionen (B3, B4). Die Anforderung verlangt explizit „Alle fünf Sektionen sind **immer** vorhanden."

## Nicht geprüft

- Echter Lauf mit echten Feeds und echtem llama-server (Außenwirkung).
- `send_scout_email.py` (nicht Teil dieser Spec).
- `run_scout_pipeline.sh` (nicht Teil dieser Spec).
- Parallel-Läufe und File-Lock-Verhalten (B5).
- Datum-Konsistenz: `write_source_run_log` nutzt `datetime.now().isocalendar()` (Zeile 343), `save_report` nutzt das übergebene `now`-Objekt (Zeile 521). Wenn `main()` zwischen Zeile 343 und 521 die Zeit wechselt (Mitternacht), könnten Protokoll und Bericht unterschiedliche Wochen-Schlüssel haben.
