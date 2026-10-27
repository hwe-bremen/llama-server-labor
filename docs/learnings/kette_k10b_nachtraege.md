# Kette 10b k10b_nachtraege (27.10.2026)
Aufgabe: vier kleine Nachträge in `kette.py` (Pflichtzeilen im Umsetzer-Prompt, Bereiche in `abgleich`, Token-Spitze, zurückgezogene Befunde in `zusammenfuehren`). Erster echter Einsatz von `umsetzung-auto` inkl. `--nacharbeit`.
Ergebnis: bestanden (`pruefen` ok, `review-auto` PASS/PASS). Code vom 35B, Tests und Handover von Claude (R42).

## Messung (Qwen3.6-35B-A3B, `umsetzung-auto`)
| Lauf | Dauer | Werkzeugaufrufe | Ergebnis |
|---|---|---|---|
| Erstlauf | 21:34 | 79 | A2–A4 richtig, A1 mit `sorted()` (Textsortierung); Tests in 7 statt 4 Methoden, 4 GRUEN in der Gegenprobe, erfundene Attrappen-Variablen; Handover-Titel umformuliert |
| NB1 | 29:25 | 94 | `sorted()` behoben (eine Zeile, sonst nichts); Tests und Titel unverändert falsch, obwohl Auftrag und Pflichtzeilen es wörtlich vorgaben; Kontextspitze 58 118 / 64K |
| Übernahme Claude | < 15 min | – | 4 Tests nach Spec, Gegenprobe 4/4 |
| `review-auto` | 26 s Betrieb | – | PASS/PASS, ein niedriger Befund (schon als Abweichung im Handover) |

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| `sorted(spec_tests)` statt Spec-Reihenfolge | Vorgabe still geändert (R09) | Claude (Diff) |
| Gegenfall als eigene Methode trotz ausdrücklicher Vorgabe → GRUEN in der Gegenprobe | Test misst nichts (R10) | `pruefen` |
| T2 prüfte nur T1 (im alten Code ohnehin ok) | Test misst nichts | Claude |
| T3 mit erfundenen Variablen `FAKE_TOTAL_1` und „Exit 0 oder 1 ist OK“ | Prüfung läuft ins Leere | Claude |
| Handover NB1 mit erfundenen Änderungen („Schreibbereich hinzugefügt“, „Regex passt nicht zu qwen36-35b“) | falsche Übergabe (R08) | Claude |

## Regeln daraus
- R43 bestätigt: kleine gezielte Änderungen in einer großen Datei schafft der 35B mit der Leseregel (nur die verlangten Stellen, keine Löschungen).
- Neu beobachtet: Code ja, Tests nach Vorgabe nein – zweimal in Folge, auch mit wörtlicher Vorgabe. Kandidat für eine Regel nach K11 (Tests vorab, Umsetzer schreibt nur Code).
- Mechanische Pflichtzeilen im Prompt allein reichen nicht; `abgleich` bleibt die Sicherung.
- `zusammenfuehren` (A4) wirkte sofort im eigenen Review.
