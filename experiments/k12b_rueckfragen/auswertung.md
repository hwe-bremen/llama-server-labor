# K12b-Messung – Auswertung (05.11.2026, Lauf `ergebnisse/20261105_083657`)

Bewertung: Claude, gegen `schluessel.md` (vor dem Lauf committet, `533b832`). Ob eine Frage Hawes Ergebnis
verändert hätte, beurteilt nur Hawe (Spalte in `uebersicht.md`).

## Betrieb

- 18/18 Aufrufe mit Antwort, 4–21 s je Aufruf, ganzer Lauf ~3,5 min (geschätzt waren 20–40 min).
- Prompt 420–449 Token (A) bzw. 5427–5456 (B), Antwort 210–1031 Token. Kein `length`.
- Form 17/18 ok. Der Ausreißer (`alle_tests_B_1`) korrigiert sich mitten in den Annahmen selbst
  („*Korrektur*: … F4 hinzufügen“) und hängt F4 hinter die Annahmen – die Formprüfung hat das richtig gemeldet.
- Wiederholbarkeit niedrig: Die drei Wiederholungen derselben Eingabe stellen meist verschiedene Fragen.

## Treffer auf Kern-Einträge (Anzahl Läufe von 6, A = 3, B = 3)

| Kette | Kern | Treffer | Wo |
|---|---|---|---|
| git_schutz | G1 melden oder blockieren | 4/6 | A1 F3, A2 F2, A3 F2, B3 F2 |
| git_schutz | G2 Umfang (ganz `.git/`?) | 2/6 | A2 F3, B3 F3 – `info/` nie |
| git_schutz | G3 `~/.gitconfig` | 0/6 | nur still als Annahme (B2) |
| git_schutz | G4 Vorher/Nachher vs. Laufzeit | 1/6 | B1 F1 – genau die Lücke der „Abweichenden Meinung“ |
| alle_tests | T1 Umfang Ordner | 2/6 | A1 F2, B1 F1/F4 – beide nur `tests/` gedacht, die vier Fundorte nie |
| alle_tests | T2 Altlast / T3 Einbindung / T5 Ausgabe | 0/6 | – |
| alle_tests | T4 Zeitlimit | 2/6 | nur B (B1 F2, B3 F3, beide mit R36) |
| spec_pruefen | S1 Platzhalter / S2 Prüft-Format / S5 Änderungsstellen | 0/6 | – |
| spec_pruefen | S3 Befund oder Hinweis | teilweise 1/6 | B3 F1 (Exit ≠ 0 oder Warnung, aber für Widersprüche statt Größe) |
| spec_pruefen | S4 Offene Fragen | teilweise 2/6 | B1 F5, B2 F2 (leere Abschnitte, nicht „≠ Keine“) |

Die eigentlichen Anlässe fehlen ganz: bei `alle_tests` „richtig aufrufen“ (Suchpfad, Sonderargument,
venv – T6), bei `spec_pruefen` alle fünf Entscheidungen vom 04.11.

## Fehlerarten

- **Schon beantwortet gefragt (B), 4×:** `alle_tests_A_2` F1 „nur Exit-Code oder auch Ausgabe?“ (steht in der
  Aufgabe); `alle_tests_B_2` F1/F2 und `B_3` F2 „nur aktuelle Kette oder alle Testdateien?“ (Aufgabe: „alle“).
- **Falscher Rahmen ohne Repo-Wissen (U):** git_schutz als Pre-Commit-Hook gedacht (A1 F2, B1/B3 Annahmen) –
  nutzlos, weil der Umsetzer genau die Hooks ändern kann; Spec als YAML/JSON (spec_pruefen A1–A3);
  „Trockenlauf an git_schutz“ als Commit-Simulation missverstanden (A2, A3); `pytest` angenommen (alle_tests B3).
- **Lernregeln lenken ab:** In spec_pruefen B fragt das Modell nach Mutanten, Gegenprobe und
  Testgenerierung (R51, R62, R10) – Themen der Vorgabe-Tests, nicht von `spec-pruefen`.
- **Annahmen-Abschnitt:** zeigt still Entschiedenes (G3 in git_schutz B2; „nur `tests/`“ in alle_tests B1/B3) –
  der Zusatz hat sich gelohnt.

## Varianten A und B

B (mit LERNREGELN.md) bringt die Zeitlimit-Frage (R36) und bei git_schutz den Treffer G4, aber auch mehr
Rauschen (Mutanten-Fragen). Keine Variante trifft die Kern-Entscheidungen von `spec_pruefen`.

## Einschätzung

- Modell, Tempo und Form sind kein Engpass (Sekunden, 17/18 formgerecht).
- Der Engpass ist der Kontext: Ein Aufruf mit Anforderung (+ Lernregeln) kennt weder das Spec-Format noch den
  Code, an dem sich die Entscheidungen festmachen. Deshalb kommen allgemeine Fragen (melden/blockieren,
  parallel/sequentiell) und falsche Rahmen.
- In dieser Form trägt die Messung K12b als Kette **nicht**: Von den 14 Kern-Einträgen trifft ein einzelner
  Lauf meist 0–2, die Vereinigung aller 6 Läufe einer Kette höchstens die Hälfte.
- Vermutung (ungeprüft): Ein fester, kleiner Projektkontext (Spec-Vorlage, Liste der `kette.py`-Befehle,
  Verzeichnisübersicht) hebt die Trefferquote deutlich. Prüfbar mit einer Variante C für wenige Minuten
  Laufzeit.
