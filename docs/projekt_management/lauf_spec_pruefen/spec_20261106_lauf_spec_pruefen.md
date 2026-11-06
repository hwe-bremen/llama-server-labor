# Spec: lauf_spec_pruefen

- **Datum:** 2026-11-06
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette_lauf` aus der Chat-UI
- **Betroffene Dateien:** `role-split/kette/automatik.py` (nur `lauf`, Kopf, Konstanten); gelesen: `role-split/kette/spec_pruefen.py`, `role-split/kette/kette.py` (`main`)
- **Änderungsstellen:** 4 (Modul-Docstring, Konstanten, Docstring `lauf`, Größenblock in `lauf`)

## Ziel

K12a2: `kette.py lauf <kt>` prüft die Spec vor der Umsetzung mit `spec-pruefen` (K12a) statt mit der eigenen Größenprüfung 2/6/8. Befunde halten den Lauf vor der Umsetzung an (Exit 3); die Größe hält nicht mehr an, sie erscheint nur noch als R59-Hinweis aus `spec-pruefen`. Entscheidung 05./06.11.: HALT bei Befunden, kein harter Größen-Halt, kein Sonderweg für alte Specs.

## Nicht-Ziele

- **`tests/test_lauf_spec_pruefen.py` und `tests/test_lauf_status.py` sind Vorgabe und werden nicht geändert – keine Zeile.**
- Keine Änderung an `role-split/kette/spec_pruefen.py`, `role-split/kette/kette.py`, den MCP-Werkzeugen, dem RUNBOOK oder den Vorlagen.
- `groesse` bleibt unverändert (Name, Signatur, Rumpf) – `spec_pruefen._groesse` ruft sie auf.
- In `automatik.py` nur die vier genannten Stellen; `stand`, `status` und der Rest von `lauf` bleiben, wie sie sind.
- Kein Schalter, der die Spec-Prüfung umgeht; keine Ausnahme für alte Specs.
- Alle bestehenden Tests bleiben grün (`python3 scripts/alle_tests.py`; Altlast `test_scout_kw_doppelversand.py` bleibt rot).

## Schreibbereich

- `role-split/kette/automatik.py`

## Vorgabe-Tests

- `tests/test_lauf_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Nichts Neues. `lauf` ruft wie bisher `umsetzung_auto` und `review_auto` auf; neu ist nur eine Prüfung, die eine Spec-Datei liest und Text ausgibt.
- **Technische Sperre für Tests:** `kette.umsetzung_auto` und `kette.review_auto` werden in allen Tests durch Attrappen ersetzt (`mock.patch.object`; im frischen Prozess von T5 durch Funktionen mit `sys.exit(99/98)`). T1–T5 biegen `kette.ROOT`/`kette.PM` auf ein `tempfile.TemporaryDirectory()` mit eigenem Git-Repo um. T6 liest den echten Bestand nur und prüft `git status --porcelain` vorher und nachher.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/automatik.py` | `automatik.lauf(kt)` über `kette.main(["lauf", kt])` (Befehlszeile `kette.py lauf`, Chat-UI `kette_lauf`) | T5 |
| `role-split/kette/automatik.py` | als Modul, importiert von `spec_pruefen.py` (`kette.py spec-pruefen` lädt `spec_pruefen` zuerst) | T5 |
| `role-split/kette/automatik.py` | `automatik.lauf(kt)` direkt | T1–T4, T6 |

## Quellen

- `role-split/kette/automatik.py` Zeilen 1–15 – Kopf, Import-Muster, Konstanten `GROESSE_*` und `UMSETZER_VORSCHLAG`
- `role-split/kette/automatik.py` def groesse – bleibt unverändert
- `role-split/kette/automatik.py` def lauf – Einbaustelle, Größenblock wird ersetzt
- `role-split/kette/spec_pruefen.py` Zeilen 1–11 – `spec_pruefen` importiert `automatik` (Grund für den Import im Zweig)
- `role-split/kette/spec_pruefen.py` def spec_pruefen – Ausgabe und Exit 0/1/2
- `role-split/kette/kette.py` Zeilen 2252–2260 – Verteiler: Muster „Import im Zweig“
- `tests/test_lauf_spec_pruefen.py` – Vorgabe-Tests (Meldungstexte wörtlich übernehmen)

## Anforderungen

### A1: lauf ruft spec-pruefen vor der Umsetzung
- **Anforderung:** In `lauf` ersetzt dieser Block den bisherigen Größenblock (von `g = groesse(spec_text)` bis einschließlich `return 3`), also **nach** den Prüfungen Kurztitel, Spec-Commit, Spec-Datei und Vorgabe-Tests (die bleiben unverändert und liefern weiter Exit 2) und **vor** `print(f"Umsetzer: {UMSETZER_VORSCHLAG}")`:
  1. `import spec_pruefen` **im Funktionsrumpf** (nicht am Dateianfang: `spec_pruefen` importiert `automatik`, und `kette.py spec-pruefen` lädt `spec_pruefen` zuerst).
  2. `exit_spec = spec_pruefen.spec_pruefen(kurztitel)` – über das Modul aufrufen, nicht `pruefe`; die Ausgabe ist damit genau die des Einzelbefehls.
  3. `exit_spec == 1` → `print("HALT – Spec-Prüfung mit Befunden: Spec nachbessern, neu committen, dann lauf erneut.")` und `return 3`; kein `status`, keine Zeile `HALT – Entscheidung Hawe.`.
  4. Sonst `exit_spec != 0` → `return exit_spec` ohne weitere Ausgabe.
  5. Sonst (Exit 0, auch mit Hinweisen) weiter wie bisher mit `Umsetzer: 35B`.
- **Stelle:** `role-split/kette/automatik.py`, `lauf`, anstelle des Größenblocks.
- **Akzeptanz:** T1, T3, T4, T5, T6.

### A2: Größen-Halt entfällt
- **Anforderung:** Die Konstanten `GROESSE_DATEIEN`, `GROESSE_ANFORDERUNGEN`, `GROESSE_TESTS` werden gelöscht; `UMSETZER_VORSCHLAG = "35B"` bleibt. `lauf` gibt keine eigene Größenzeile mehr aus und hält bei keiner Größe an. `groesse` bleibt unverändert. Docstrings: Modul-Docstring nennt K12a2 und dass `groesse` nur noch zählt (für `spec_pruefen`); `lauf`-Docstring `Kette: spec-pruefen -> umsetzung-auto -> review-auto -> status -> HALT.`
- **Stelle:** `role-split/kette/automatik.py`, Modul-Docstring, Konstanten am Dateianfang, Docstring von `lauf`.
- **Akzeptanz:** T2, T5.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht | n. a. (kein Netz, kein Modell in der Prüfung) | – | – |
| A1 | Spec mit Befund (offene Frage, Änderungsstellen fehlt) | nichts | Ausgabe von `spec-pruefen`, HALT-Zeile, Exit 3, keine Umsetzung | T1 |
| A1 | alte Spec am echten Bestand (`git_schutz`) | nichts | Exit 3, genau der Befund „Änderungsstellen“ | T6 |
| A1 | Vorgabe-Tests fehlen | nichts | Exit 2 wie bisher, Spec-Prüfung läuft gar nicht | T4 |
| A1 | `spec-pruefen` liefert Exit 2 | nichts | Exit 2, keine Umsetzung, keine HALT-Entscheidung-Zeile | T4 |
| A1 | nur Hinweise (Exit 0) | – | Lauf geht weiter | T2, T3 |
| A1 | Aufruf über `kette.main` in frischem Prozess, auch `spec-pruefen` zuerst geladen | – | kein Traceback (Zirkelimport) | T5 |
| A1 | Absturz mitten im Lauf | unverändert (Umsetzung wie bisher) | – | – |
| A1 | Ziel existiert schon / wird etwas überschrieben | n. a. (Prüfung schreibt nichts) | `git status` unverändert | T6 |
| A2 | Spec über alten Schwellen und über R59 | – | Exit 0, vier R59-Hinweise, keine „teilen“-Meldung | T2 |
| A2 | an der alten Schwelle 2/6/8 | – | läuft wie bisher (Bestand) | `test_lauf_status.py` T3 |
| A2 | Konstanten noch vorhanden / `groesse` entfernt | – | rot | T5 |

## Testplan

Die Tests stehen in `tests/test_lauf_spec_pruefen.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Vorab 6/6 rot; gegen die Referenz 6/6 grün, dreimal stabil (< 1 s). `tests/test_lauf_status.py` (K11b) ist mit dieser Spec von Claude angepasst (Helfer `spec()` liefert eine Spec ohne Befund, T3 prüft nur noch die Schwelle) und vorab wie nachher 8/8 grün. Mutationsprüfung der Referenz: 17 von 17 gefangen (Halt-Exit 1, Halt ohne `return`, Exit 2 nicht durchgereicht, frühes `return` bei Exit 0, Exit 2 als 3, Meldung ohne HALT, Prüfung entfernt, Prüfung vor dem Vorgabe-Check, alte Konstanten, alter Größen-Halt zusätzlich, Umsetzer-Zeile davor, eigene Zusammenfassung statt Einzelbefehl, `groesse` entfernt, Hinweise halten an, falscher Kurztitel, `status` beim Halt, Top-Level-Import aus `spec_pruefen`).

### T1: Befunde halten vor der Umsetzung
- **Prüft:** A1
- **Aufbau:** Temp-Repo, Spec mit offener Frage, dann Spec ohne Zeile „Änderungsstellen“ (wie alte Specs); Attrappen.
- **Erwartung:** je Exit 3, keine Umsetzung; Ausgabe mit `Spec-Prüfung k: …`, dem jeweiligen Befund und `HALT – Spec-Prüfung mit Befunden`; weder `Umsetzer:` noch `HALT – Entscheidung Hawe.`.
- **Warum misst der Test das Richtige?** Ohne die Prüfung läuft die Umsetzung an; mit falschem Exit-Code verwechselt Hawe den Halt mit einem Umsetzungsfehler.
- **Gegenprobe:** alter Stand → rot (Umsetzung läuft, Exit 0).

### T2: Größe nur noch Hinweis
- **Prüft:** A2, A1 (Exit 0 bei Hinweisen)
- **Aufbau:** Spec mit 3 Dateien, 7 Anforderungen, 9 Tests, 12 Änderungsstellen, sonst gültig.
- **Erwartung:** Exit 0, Umsetzung und Review laufen; vier Hinweise `Größe über R59 (vorläufig): …`; kein „teilen“.
- **Warum misst der Test das Richtige?** Bliebe der alte Größen-Halt, wäre es Exit 3.
- **Gegenprobe:** alter Stand → rot (Exit 3).

### T3: Ausgabe wie der Einzelbefehl
- **Prüft:** A1
- **Aufbau:** gültige Spec; erst `spec_pruefen.spec_pruefen("k")` allein, dann `lauf`; danach Umsetzung rot.
- **Erwartung:** `lauf`-Ausgabe beginnt mit genau der Ausgabe des Einzelbefehls, direkt danach `Umsetzer: 35B`; keine Zeile `Schwellen 2/6/8`; Exit 0 bzw. Exit 1 bei roter Umsetzung (wie bisher).
- **Warum misst der Test das Richtige?** Eine eigene Zusammenfassung oder die alte Größenzeile weicht vom Einzelbefehl ab.
- **Gegenprobe:** alter Stand → rot (Ausgabe beginnt mit `Größe: …(Schwellen 2/6/8`).

### T4: Vorbedingungen und Exit 2
- **Prüft:** A1
- **Aufbau:** Spec ohne Vorgabe-Tests; dann gültige Spec mit `spec_pruefen.spec_pruefen` als Attrappe (Exit 2, dann Exit 1).
- **Erwartung:** ohne Vorgabe-Tests Exit 2 und keine Spec-Prüfung in der Ausgabe; Attrappe mit Kurztitel `k` aufgerufen; Exit 2 → `lauf` Exit 2 ohne Umsetzung und ohne `HALT – Entscheidung Hawe.`; Exit 1 → Exit 3.
- **Warum misst der Test das Richtige?** Fängt falsche Reihenfolge, verschluckten Exit 2 und Aufruf ohne das Modul.
- **Gegenprobe:** alter Stand → rot (Attrappe nie aufgerufen).

### T5: Standardwerte und echter Aufruf
- **Prüft:** A2, A1 (R58: echter Pfad)
- **Aufbau:** echte Module; frischer Python-Prozess, der `kette.ROOT` auf das Temp-Repo setzt und `kette.main(["lauf", "k"])` bzw. `kette.main(["spec-pruefen", "k"])` aufruft.
- **Erwartung:** keine Konstanten `GROESSE_*`; `groesse` zählt wie bisher; `UMSETZER_VORSCHLAG` `35B`; `spec_pruefen.R59` unverändert; `lauf` Exit 3 mit HALT-Zeile, `spec-pruefen` Exit 1, beide ohne Traceback.
- **Warum misst der Test das Richtige?** Ein Top-Level-Import aus `spec_pruefen` in `automatik.py` geht im `lauf` gut, bricht aber `spec-pruefen` im frischen Prozess (Zirkelimport).
- **Gegenprobe:** alter Stand → rot (Konstanten vorhanden).

### T6: Trockenlauf am echten Bestand
- **Prüft:** A1 (R57: echter Bestand)
- **Aufbau:** echtes `kette.ROOT`/`kette.PM`, Attrappen für Umsetzung und Review; `lauf("git_schutz")` und `lauf("spec_pruefen")`; `git status --porcelain` vorher/nachher.
- **Erwartung:** `git_schutz` Exit 3 mit genau dem Befund „Änderungsstellen“, keine Umsetzung; `spec_pruefen` Exit 0, „Keine Befunde“, Umsetzung und Review je einmal; Arbeitsstand unverändert.
- **Warum misst der Test das Richtige?** Zeigt am echten Bestand, dass alte Specs halten und eine saubere Spec durchläuft.
- **Gegenprobe:** alter Stand → rot (`git_schutz` läuft durch).

## Offene Fragen

- Keine

## Abweichende Meinung

- Alte Specs halten jetzt immer an (Trockenlauf 06.11.: von den Specs mit Vorgabe-Tests nur `spec_pruefen` ohne Befund; `alle_tests`, `git_schutz`, `lauf_status`, `mcp_kette`, `vorgabe_tests` nur „Änderungsstellen fehlt“; `ablage_ordner`, `einsortieren` zusätzlich „ohne Stelle:“; `vorgabe_nachtrag` zusätzlich „B4 von keinem Test geprüft“). Für einen Wiederholungslauf die Zeile nachtragen und committen – der Rücksetzpunkt bleibt der älteste Commit „Spec <kt>“.
- Eine übergroße Spec startet trotzdem. Der Schutz liegt darin, dass Claude `spec-pruefen` vor dem Spec-Commit laufen lässt und die Hinweise nennt.
- RUNBOOK (Abschnitt `lauf`, Exit 3) passt Claude nach dem Lauf an; nicht Teil des Schreibbereichs.
