# Ketten 13a/13b ablage_ordner und einsortieren (28.10.2026)
Aufgabe: Ziel 3 der Landkarte – jede Kette in ihrem Ordner `docs/projekt_management/<kurztitel>/`. K13a: Pfadlogik („Ordner, wenn vorhanden, sonst flach“). K13b: neue Ketten legen den Ordner an, `kette.py einsortieren <kt>|--alle` verschiebt alte Dateien.
Ergebnis: bestanden. Erste Ketten über `kette.py lauf`. Ablage einsortiert (`3e12137`): 133 Dateien in 18 Ordner, flach bleiben Vorlagen, Proben, Evals.

## Messung (35B, `kette.py lauf`)
| Kette | Lauf | Dauer | Werkzeugaufrufe | Kontextspitze | Ergebnis |
|---|---|---|---|---|---|
| K13a (2/6/7, ~20 Stellen in `kette.py`) | Erstlauf | 24:00 | 81 | 62 670 / 64K | Tests grün; Rückfall auf flache Dateien (gegen E2), Platzhalter-Pfade `<modellkürzel>` blieben flach |
| K13a | nb1 | 24:37 | 70 | 62 803 / 64K | beide Punkte behoben, dabei Anforderung/Quellen/Paket im Prompt neu flach → Claude-Einbau (5 Ausdrücke) |
| K13b (2/5/7, neue Datei + 2 Stellen) | Erstlauf | 18:19 | 71 | 60 281 / 64K | Code gleichwertig (Trockenlauf an der echten Ablage identisch); 2 Debug-Dateien außerhalb des Schreibbereichs, Handover-Sammelzeile „T1–T7“ |
| `review-auto` K13a | 2 Läufe | 52 s + 74 s | – | – | 6× „hoch“, alle falsch (angeblich fest codiertes `ablage_ordner`) |

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| K13a: Rückfall auf flache Dateien trotz Ordner | Spec-Abweichung | Claude (Diff gegen Referenz) – nicht getestet |
| K13a: Pfade mit Platzhaltern in Hand-Prompts nicht umgebogen | Spec-Abweichung | Claude (Diff) – nicht getestet |
| K13a nb1: Anforderung/Quellen/Paket im Prompt wieder flach (vorher richtig) | Nacharbeit baut Fehler ein | Claude (Prompt am Ordner-Beispiel erzeugt) |
| `review-auto`: Kurztitel in `{kurztitel}` eingesetzt und als fest codiert bemängelt – zweite Kette in Folge | falscher Befund (R54) | Claude (`grep`) |
| `zusammenfuehren` stürzte bei Verdikt ohne Befundtabelle ab (5er-Tupel) – alter Fehler | Absturz im Fehlerpfad | Claudes Vorgabe-Test T3 |
| K13b: `tests/debug_*.py` außerhalb des Schreibbereichs | Schreibbereich verletzt | `umsetzung-auto` (mechanisch) |
| K13b: Handover „T1–T7: alle bestanden“ trotz Pflichtzeilen | Übergabe unvollständig | `abgleich` (mechanisch) |

## Regeln daraus
- R55 → LERNREGELN.md
- R56 → LERNREGELN.md
- R57 → LERNREGELN.md

## Sonst bemerkenswert
- `lauf` hat beide Male richtig gehalten; `status` nannte jeweils den passenden nächsten Schritt.
- Die mechanischen Sperren tragen: Debug-Dateien und Sammelzeile fielen ohne Claude auf.
- Der Trockenlauf von `einsortieren --alle` an einer Kopie der echten Ablage (Referenz und 35B, Dateilisten verglichen) war der eigentliche Abnahmetest – die Vorgabe-Tests allein hätten die Gleichwertigkeit am echten Bestand nicht gezeigt.
- Vorgemerkt: Größenprüfung um „Änderungsstellen“ erweitern (z. B. Zeile `- **Änderungsstellen:** n` in der Spec, Schwelle ~10); `review-auto` im `lauf` als Hinweis statt Entscheidung behandeln; flach liegende Proben/Evals bei Gelegenheit in `docs/projekt_management/_archiv/`.
