# Kette 11b lauf_status (28.10.2026)
Aufgabe: `kette.py lauf <kt>` (Spec mit Vorgabe-Tests → Größenprüfung → `umsetzung-auto` → `review-auto` → Halt mit Status) und `kette.py status <kt>` im neuen Modul `automatik.py`.
Ergebnis: bestanden. Tests von Claude (Vorgabe), Code vom 35B (Erstlauf + eine Nacharbeit), `review-auto` PASS/PASS, ein „hoch“ von Claude widerlegt.

## Messung
| Schritt | Modell | Dauer | Ergebnis |
|---|---|---|---|
| Vorgabe-Tests schreiben (Messung) | 27B (Qwen3.6-27B-MTP) | 32:45 | nur die Testdatei geschrieben, 8/8 vorab rot; mit Claudes Referenz 6/8 grün – T3 zählte Einträge unter `## Vorgabe-Tests` statt Test-IDs, T7 erfand ein Protokollformat; 8/18 Mutanten (die 10 übrigen alle im Bereich von T3/T7) |
| Vorgabe-Tests schreiben | Claude | – | 8/8 vorab rot, 17/18 Mutanten (überlebt: Kurztitel-Prüfung ohne eigene Wirkung) |
| Erstlauf `umsetzung-auto` | 35B | 8:41 | 189 Zeilen, `pruefen` ok, alle Testdateien grün; zwei Abweichungen: `UNVOLLSTAENDIG` ohne Umlaut, voller Pfad statt Dateiname |
| Nacharbeit 1 (Tests vorher ergänzt und committet) | 35B | 4:44 | genau die zwei Zeilen plus Import, Testdatei unverändert |
| `review-auto` 1. Versuch | 35B | ~4 min | Echo: Prompt und Paket Wort für Wort zurückgegeben, bei 8000 Token abgeschnitten |
| `review-auto` 2. Versuch | 35B | 33 s + 34 s | PASS/PASS, 3 Befunde, einer „hoch“ – alle drei falsch |

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| 27B-Tests prüfen etwas anderes als die Spec (T3, T7); `tests-pruefen` hätte sie durchgelassen | Test misst das Falsche | Claude (Lauf gegen Referenz) |
| `UNVOLLSTAENDIG` statt `UNVOLLSTÄNDIG` → unvollständiges Review als „kein Review“ angezeigt | Vorgabe still geändert (R09) | Claude (Diff) – Claudes Tests deckten den Wert nicht ab |
| Spec-Zeile zeigt Pfad statt Dateiname | Spec-Abweichung | Claude (Diff) – nicht getestet |
| Review-Befund „fest codiertes `lauf_status`“ – kommt in `automatik.py` nicht vor; „hoch“ nur über „Harte Vorgabe: ja“ | falscher Befund (R39) | Claude (`grep`) |
| Antwort von `review-auto` = Echo des Prompts, gemeldet als „auf Wiederholungsschleife prüfen“ | falsche Diagnose im Werkzeug | Claude (Textvergleich, Tippfehler „Schaechte“ aus dem Prompt im Echo) |

## Regeln daraus
- R52 → LERNREGELN.md
- R53 → LERNREGELN.md
- R54 → LERNREGELN.md; Prompt-Tippfehler „Schaechte“ in `review_api.md`/`review2_api.md` behoben

## Sonst bemerkenswert
- Der Ablauf Tests ergänzen → committen → `--nacharbeit` hat die Sperre aus K11a2 genutzt; erste Nacharbeit mit Vorgabe-Tests, klein und sauber.
- Zwei missverständliche Stellen der Spec (T3 „9 Tests“, T7 Protokollformat) nach R44 direkt präzisiert. Ob der 27B mit der präzisierten Spec richtig läge, ist nicht gemessen.
- `status` erstmals an der eigenen Kette benutzt: zeigte korrekt `erst Exit 0, nb1 Exit 0`, danach „Review NACHBESSERN – gegenprüfen“.
- Vorgemerkt: `review-auto` soll ein Echo selbst erkennen (Antwort beginnt wie der Prompt) und „Echo“ melden; Größenschwellen 2/6/8 an weiteren Läufen kalibrieren (K11b lag mit 2/5/8 knapp darunter, 189 Zeilen gingen gut).
