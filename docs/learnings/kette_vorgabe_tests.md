# Ketten 11a/11a2 vorgabe_tests und vorgabe_nachtrag (27.–28.10.2026)
Aufgabe: Rollenteilung „Tests vorab, Umsetzer schreibt nur Code“ mechanisch absichern (`## Vorgabe-Tests`, `tests-pruefen`, Schutz in `umsetzung-auto`), danach Nachträge aus der Gegenprüfung (`(Bestand)`-Tests, Nacharbeit-Sperre).
Ergebnis: K11a bestanden mit Claudes Referenz (Lauf des 35B verworfen); K11a2 bestanden mit Code vom 35B – erster Lauf mit Vorgabe-Tests, Testdatei unverändert.

## Messung (Qwen3.6-35B-A3B, `umsetzung-auto`)
| Kette | Dauer | Werkzeugaufrufe | Kontextspitze | Ergebnis |
|---|---|---|---|---|
| K11a (alter Prompt: „Die Tests der Spec schreibst du …“) | 12:40 | 32 | 57 439 / 64K | Vorgabe-Tests komplett neu geschrieben; `tests_pruefen` verlangt grün statt rot vorab; Prüfung in jeden Lauf eingebaut → 22 von 37 bestehenden Tests rot; A3-Verstoß und A4 fehlen. Gegen die echten Vorgabe-Tests 1/8 grün. |
| K11a Übernahme Claude | – | – | – | Referenz per Einbauskript mit Prüfsummen; `pruefen` ok, Gegenprobe 8/8; frische Instanz: PASS, 2 mittlere Befunde an den Vorgabe-Tests |
| K11a2 (neuer Prompt mit Abschnitt `## Vorgabe-Tests`) | 12:28 | 37 | 57 617 / 64K | Code gleichwertig zur Referenz (+32/−3 statt +28/−3), Testdatei unverändert, `pruefen` ok, alle bisherigen Tests grün |

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| 35B schreibt die Vorgabe-Tests passend zu seinem Code um (K11a) | Vorgabe still geändert (R09) | `abgleich` (8× ANDERS), Prüfsumme |
| „rot vorab“ als „grün vorab“ verstanden (K11a) | Spec umgedeutet | Claude (Lauf gegen echte Vorgabe-Tests) |
| neue Prüfung auch ohne `## Vorgabe-Tests` aktiv → Regression (K11a) | Normalbetrieb verboten (R05) | Claude (alle Testdateien) – `pruefen` sieht nur die Tests der Kette |
| T5 deckte „Spec ohne Test-ID“ nicht ab, obwohl in der Fehlerpfad-Tabelle (Claudes Tests) | Test misst nichts (R10) | frische Instanz, Mutation bestätigt |
| Nacharbeit übernimmt geschwächte Vorgabe-Tests aus dem Erstlauf ungeprüft (Claudes Spec) | Lücke im Ablauf | frische Instanz |
| Ausnahme in Prüfung (b) wirkungslos, Spec-Begründung beschrieb den alten Code falsch (Claude) | totes Stück Code | frische Instanz, Mutation bestätigt |

## Regeln daraus
- R48 → LERNREGELN.md; umgesetzt in `kette.py` (`## Vorgabe-Tests`, `tests-pruefen`, Prompt-Abschnitt, Verstoß-Befund)
- R49 → LERNREGELN.md; umgesetzt in `kette.py` (`(Bestand)` in `tests_pruefen` und `gegenprobe`), `_vorlage_spec.md`
- R50 → LERNREGELN.md
- R51 → LERNREGELN.md

## Sonst bemerkenswert
- Ein Lade-Fehler auf Dateiebene liefert in `tests_laufen` einen Ersatz-Eintrag `test_<modul>` statt der Methoden; `tests_pruefen` gleicht deshalb gegen die per `ast` gefundenen Methoden ab.
- Hilfsmethoden im Test, die mit `test` beginnen, sammelt unittest als Test ein (Claude selbst passiert).
- Kontextspitze in beiden Läufen ~57K; in K11a2 ohne Schaden – Vermutung: das feste Ziel durch vorgegebene Tests macht den knappen Kontext verkraftbar.
- Vorgemerkt: gleichnamige Testmethoden in zwei Klassen fallen in `tests_laufen` zusammen; `## Vorgabe-Tests` in einem Codeblock wird mit erkannt (Exit 2, harmlos); leere Bestand-Menge macht das Regex in `gegenprobe` zu `test_()(_|$)`; Hinweistext „ohne Umsetzung nicht rot“ liest sich nach einem Lauf irreführend.
