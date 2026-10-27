# Kette 9 paket_vollstaendig (25.–27.10.2026)
Aufgabe: Das Review-Paket enthält alle Code-Dateien der Kette (auch `tests/`, `role-split/`, unversionierte), fremde Commits nur als Liste, Vorrang-Kürzung > 80 000 Zeichen, harte Grenze `KETTE_PAKET_MAX`; Gegenprobe mit derselben Auswahl.
Ergebnis: bestanden (Abnahme T10 am K7-Stand: `mail_planung.py` mit Inhalt, `kette.py` nur in der Fremd-Liste, Review sieht den Diff). Umsetzung aber nicht durch das lokale Modell: Claude hat NB2 übernommen.

## Messung Umsetzer Qwen3.6-27B (OpenCode)
| Runde | Dauer | Ergebnis |
|---|---|---|
| Erstumsetzung | ~2 h 45 | Code weitgehend richtig, Tests prüfen Quelltext statt Verhalten, `.md` pauschal ausgeschlossen |
| NB1 | ~4,5 h | Verhaltenstests mit Wegwerf-Repos, aber T1/T4/T5/T9 rot |
| NB2 | ~4,5 h (ab 17:00), abgebrochen | `role-split/` pauschal zur Kette (gegen Spec), Tests falsch nummeriert, unter Python 3.10 nicht lauffähig |
| Übernahme Claude | < 1 h | T1–T9 + K1–K3 grün, Probelauf, Handover |

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| Tests prüften `"Fremde" in source` statt Verhalten | Test misst nichts | Claude (Schlüssel S1) |
| OpenCode committete selbst (`1b2e74c` „checkpoint"), obwohl der Auftrag „Kein Commit" sagte | Umsetzer handelt außerhalb des Auftrags | Claude (git log) |
| NB2 baute Sonderregel `role-split/` = immer Kette | Spec still umgedeutet, um Tests grün zu bekommen | Claude |
| `review-auto` brach mit `finish_reason=length` ab (8000, dann 16 000 Token) | Feste Temperatur 0,1 im API-Aufruf überschrieb Server-Sampling (0,6) → Wiederholungsschleife | Claude (nach falscher Erst-Diagnose „Denkphase") |
| Bestätigungen („Kein Befund", „korrekt") als Zeilen in der Befund-Tabelle, eine davon mit „Unbemerkt: ja" → NACHBESSERN | Formfehler des Reviewers, mechanische Regel feuert | Claude (Gegenprüfung) |
| Derselbe 35B am selben Paket: einmal PASS/PASS, einmal 2× „hoch" (beide unbegründet: A5 meint nur Code, T7 war nach Spec) | Streuung des Reviewers | Claude (Gegenprüfung) |
| T10: Review meldet A4/A5 „teilweise", weil der K7-Handover (NB3) fälschlich „`mail_planung.py` existiert nicht" sagt | Zurückgesetzte Arbeit, Handover nicht korrigiert | Claude (Abnahme) |
| Paket für die alte Kette K7 enthielt die uncommittete K9-Arbeit (175 161 Zeichen → Exit 1) | „Nicht committet = zur Kette" gilt für jede Kette | Claude (Probelauf) |

## Regeln daraus
- R38 Server-Sampling nicht überschreiben → umgesetzt in `kette.py _api_ruf` (keine Temperatur, `KETTE_LLM_TEMPERATURE` optional), Test K3.
- R39 Befund-Tabelle nur für echte Mängel, feste Leerzeile → umgesetzt in `prompts/review_api.md`, `review2_api.md` (wirkt bisher nur halb).
- R40 Handover mit zurücksetzen.
- R41 Paket für eine alte Kette nur bei sauberem Arbeitsstand.
- R42 Umsetzer: zwei Nachbesserungen ohne Fortschritt ⇒ Übernahme; Messwert festhalten.
- R35 behoben.

## Sonst bemerkenswert
- Abbruch bei `finish_reason=length` speichert jetzt den Text (`/tmp/kette_abgeschnitten_lauf<n>.md`) – vor einem höheren Limit erst auf Schleife prüfen.
- Mit Server-Sampling: Review-Lauf 60–80 s bei 22k Prompt-Token, 135 s bei 44k (K7-Paket); 1200–1900 Antwort-Token.
- Mac Python 3.13/3.14, VM Python 3.10: f-Strings mit Backslash nur ab 3.12 – Tests für beide schreiben.
