# Verdikt: search_results_verbessern

- **Spec:** `spec_20261021_search_results_verbessern.md`
- **Handover:** `handover_20261021_search_results_verbessern.md`
- **Datum:** 2026-10-21
- **Modell:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `agents/llm_scout/llm_scout.py` (vollständig), `agents/llm_scout/sources.json`, `tests/test_search_results_verbessern.py`, `docs/projekt_management/anforderung_20261021_search_results_verbessern.md`, `docs/projekt_management/spec_20261021_search_results_verbessern.md`, `docs/projekt_management/quellen_20261021_search_results_verbessern.md`

*(Korrekturversion: Befund-Tabelle bereinigt, NameError-Prüfung präzisiert)*

## Ergebnis

**FAIL** – Zwei Befunde „hoch": Slipstream wird doppelt abgerufen (Doppel-HTTP-Request, Inkonsistenz im Protokoll) und T8 testet nicht die in der Spec geforderte Erwartung.

## Spec gegen Anforderung

Die Spec widerspricht der Anforderung an einer Stelle:

- **Anforderung:** "nur agents/llm_scout/sources.json im Repo, kein Fallback; fehlt sie, Exit 1."
- **Spec A2:** "Fehlt die Datei oder ist sie ungültig, bricht der Scout mit einer klaren Fehlermeldung ab (Exit 1) und schreibt keine DB-Änderungen." – Das passt.
- **Code:** `main()` ruft `load_sources()` auf und wirft `SystemExit` weiter → Exit 1. Das passt. **ABER:** `fetch_github_releases()` und `fetch_slipstream()` rufen `load_sources()` separat auf und fangen `SystemExit` ab, um auf `GITHUB_RELEASES_RSS` bzw. eine Standard-URL zurückzugreifen. Diese Funktionen werden im `main()`-Flow nicht aufgerufen (die Repos werden direkt iteriert), bleiben aber als öffentliche Funktionen mit Fallback-Verhalten im Modul. Das ist kein akuter Bug im Hauptfluss, aber ein Design-Widerspruch zur Anforderung.

Fehlerpfad-Prüfung: Was passiert beim nächsten Lauf, wenn `sources.json` fehlt? `main()` bricht mit Exit 1 ab → Anforderung erfüllt. Die Fallback-Funktionen werden nicht erreicht.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Quellenverteilungsprotokoll (JSONL, pro Quelle, vor LLM) | erfüllt | `llm_scout.py:370-395` (write_source_run_log), `main():734` |
| A2 | sources.json – ohne Codeänderung erweiterbar, Exit 1 bei Fehlen | teilweise erfüllt | Fallback in `fetch_github_releases()` (Zeilen 300-311) widerspricht "kein Fallback"; `main()` selbst bricht korrekt ab |
| A3 | Slipstream als eigene, klar abgegrenzte Quelle | teilweise erfüllt | Slipstream wird **doppelt** abgerufen: in der GitHub-Schleife (Zeilen 645-651) und separat via `fetch_slipstream()` (Zeile 654) |
| A4 | Pro-Quellen-Selektion und getrennte Präsentation | erfüllt | `select_items()` (Zeilen 355-367), `build_prompt_sections()` (Zeilen 400-445) |
| A5 | Pro-Quellen-Dedup in DB | erfüllt | `assign_source_tags()` (Zeilen 170-185), `get_source_key_for_repo()` (Zeilen 188-196) |
| A6 | Bericht zeigt „nichts Neues" pro Quelle | erfüllt | `build_prompt_sections()` und `build_empty_sections()` zeigen leere Sektionen; `call_llm_for_evaluation()` ruft bei `items=[]` `build_empty_sections()` auf |

## Handover gegen Code

- **"A3 erfüllt"**: Handover behauptet, Slipstream sei als eigene Quelle umgesetzt. Code: Slipstream wird doppelt abgerufen (GitHub-Schleife + `fetch_slipstream()`), was zu doppelten HTTP-Requests und potenziellen Inkonsistenzen führt.
- **T8-Abweichung**: Handover bestätigt "T8: sources.json leer ({}) → Exit 0, Protokoll mit leeren Quellen". Spec verlangt "fünf leere Sektionen im Bericht". Test prüft nur `load_sources({})` → `{}`, nicht den Bericht.
- **Tests mit Ausgabe**: Handover zeigt 12/12 Tests grün. Ausgabe im Handover belegt das.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | nein | **hoch** | `llm_scout.py:645-660` | **Slipstream wird doppelt abgerufen.** In `main()` wird (a) in der Schleife über `github_repos` auch `Schero94/slipstream` abgerufen (`gh_items_by_repo["slipstream"]`), und (b) separat `fetch_slipstream()` aufgerufen. Das sind zwei HTTP-GET auf denselben Feed. Die Items aus (a) werden zwar durch `if source_key == "slipstream": continue` aus `all_items` ausgeschlossen, aber (b) fügt sie erneut hinzu. Das Protokoll zählt `fetched` aus `gh_items_by_repo`, während `all_items` die Items aus `fetch_slipstream()` enthält. Bei unterschiedlichen Feed-Inhalten zwischen den beiden Aufrufen (z. B. weil ein neues Release dazwischen erscheint) sind Protokoll und Bericht inkonsistent. | `fetch_slipstream()` aufrufen und das Ergebnis in `gh_items_by_repo["slipstream"]` speichern. Die Schleife über `github_repos` dann um den Slipstream-Eintrag ergänzen (oder Slipstream aus der Schleife ausschließen und nur `fetch_slipstream()` verwenden). |
| 2 | nein | ja | ja | **hoch** | `tests/test_search_results_verbessern.py:441-447` | **T8 testet nicht die Spec-Anforderung.** Spec T8: "sources.json leer ({}) → Exit 0, **fünf leere Sektionen im Bericht**". Test T8 prüft nur `load_sources({})` → `{}`. Es wird nicht geprüft, dass der Scout mit Exit 0 endet und der Bericht fünf leere Sektionen enthält. Ein Test, der die eigentliche Erwartung gar nicht prüft, ist ein Befund. | T8 um einen vollständigen `main()`-Aufruf (oder `subprocess`) mit leerer `sources.json` erweitern, der Exit 0 und die fünf leeren Sektionen im Bericht prüft. |
| 3 | nein | nein | ja | mittel | `llm_scout.py:300-311`, `llm_scout.py:323-335` | **Fallback in `fetch_github_releases()` und `fetch_slipstream()` widerspricht Anforderung.** Anforderung: "kein Fallback; fehlt sie, Exit 1". Beide Funktionen fangen `SystemExit` ab und verwenden `GITHUB_RELEASES_RSS` bzw. eine Standard-URL. Im `main()`-Flow werden diese Funktionen nicht aufgerufen (Repos werden direkt iteriert), aber als öffentliche Module-Funktionen ermöglichen sie einen Fallback. | Fallback-Logik aus beiden Funktionen entfernen. Bei fehlender `sources.json` soll `SystemExit(1)` weitergeworfen werden. |
| 4 | nein | ja | ja | niedrig | `agents/llm_scout/llm_scout.py` (gesamt) | **Warnung ab 8 Repos fehlt.** Anforderung OQ7: "Keine Grenze, Warnung ab 8 Repos". Spec erwähnt das, aber im Code gibt es keine Prüfung und keine Warnung. | In `load_sources()` nach dem Laden prüfen: `if len(data.get("github", [])) > 8: print("Warnung: ...", file=sys.stderr)`. |

## Mechanische Prüfungen (Gegenprobe)

- **12/12 Tests grün:** Bestätigt durch Handover-Ausgabe.
- **T9 (Zweitlauf, Bestandssicherung):** Testet `save_report()` mit zwei Aufrufen und prüft Anhäng-Verhalten. Im alten Code existiert dieselbe Logik → **grün erwartet**. Bestätigt.
- **T12 (Import, Bestandssicherung):** Testet `runpy.run_path()` ohne ImportError. Im alten Code lädt das Skript ebenfalls erfolgreich → **grün erwartet**. Bestätigt.
- **T8 (ANDERS):** Spec verlangt "fünf leere Sektionen im Bericht", Handover/Test prüfen nur `load_sources({})` → `{}`. **Befund #2.**

## Nicht geprüft

- **Kann Hawe selbst prüfen:**
  - Echten Lauf mit `sources.json` und echtem llama-server (Außenwirkung).
  - Gegenprobe mit `kette.py gegenprobe search_results_verbessern --commit ea9288f` (Handover bittet Hawe darum).
  - Ob der E-Mail-Versand (`send_scout_email.py`) den neuen Bericht mit pro-Quellen-Sektionen korrekt rendert.
- **Braucht externe Quelle:**
  - Ob der Atom-Feed `https://github.com/Schero94/slipstream/releases.atom` existiert und gültig ist.

## Abweichende Meinung

- **Slipstream als separates `fetch_slipstream()` war überflüssig.** Da Slipstream in `sources.json` unter `github` als `Schero94/slipstream` konfiguriert ist, hätte die GitHub-Schleife in `main()` es bereits abgerufen. Die separate Funktion `fetch_slipstream()` führt nur zum Doppelabruf (Befund #1). Eine saubere Lösung: Slipstream in der GitHub-Schleife verarbeiten und im Prompt/Bericht die Sektion `## Slipstream neueste Entwicklungen` basierend auf dem source-Key `slipstream` rendern. Keine separate Fetch-Funktion nötig.
- **T8 sollte einen Integrationstest sein.** Die Spec beschreibt T8 als Test des vollständigen Laufs mit leerer `sources.json`. Die Umsetzung prüft nur `load_sources()` isoliert. Das ist zu wenig: Es wird nicht geprüft, dass der Scout tatsächlich Exit 0 liefert und fünf leere Sektionen im Bericht schreibt.

## Mechanisches Urteil (kette.py)

_2026-10-21 15:44_

```
Modell-Urteil:       FAIL
Regel-Urteil:        NACHBESSERN
Es gilt:             FAIL
  Befunde hoch: 1, 2, 3, 4
  Anforderungen offen: A2: teilweise erfüllt; A3: teilweise erfüllt
  Korrektur: Befund 3: als 'mittel' eingestuft, aber ja bei Harte Vorgabe -> hoch
  Korrektur: Befund 4: als 'niedrig' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
  Modell strenger als die Regel -- Begruendung im Verdikt lesen.
```
