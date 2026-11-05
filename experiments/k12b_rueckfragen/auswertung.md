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

---

# Nachtrag: Varianten C und D (Lauf `ergebnisse/20261105_193503`)

C = A + Projektkontext vom Stand vor der Spec (kette.py-Befehle, Spec-Vorlage, Code-Dateiliste), ~4K Token.
D = C + LERNREGELN.md vom selben Stand, ~8,5K Token.

## Betrieb

- 18/18 Antworten, Form 18/18 ok, 6–25 s je Aufruf (D ~15–25 s, C ~6–16 s). Wiederholbarkeit weiter niedrig.

## Treffer je Kette (6 Läufe C+D, Vergleich A+B in Klammern)

**spec_pruefen – deutlich besser.** Keine YAML/JSON-Missverständnisse mehr, die Fragen sitzen an der Vorlage:
- S4 Offene Fragen erlaubt/Fehler/Warnung: D2 F2 – direkter Treffer (A+B: nur am Rand).
- S3 Befund (Exit 1) oder Hinweis (Exit 0): als allgemeine Exit-Frage 4/6 (C1 F2, C3 F2, D2 F4 mit
  „kritisch Exit 1, geringfügig Exit 0 mit Warnung“) – nicht an R59 gebunden, obwohl R59 in D steht.
- S2 Zuordnung Test → Anforderung: D2 F1 („A1 im Testplan T1 abgedeckt“) als Frage, ob geprüft wird; Format nie.
- S1 Platzhalter: nur angedeutet (C1 F2 „nur Platzhalter-Text“).
- S6 welche Prüfungen: viele gute Neben-Treffer – Schreibbereich (C1 F1, C3 F4, D1 F1 mit R47) und Form der
  Quellen (C1 F3 „Existenz oder nur Format“, C2 F2, D1 F1, D3 F3). Genau das prüft die spätere Spec (A4).
- S5 Änderungsstellen: 0/6 (aus dem Text nicht ableitbar, erwartet).

**git_schutz – kaum besser.**
- G1 melden/blockieren: 0/6 klar (A+B 4/6); G4 Vorbeugen oder Erkennen: D3 F2 (1/6, A+B 1/6).
- G2 Umfang: nur angedeutet (C1 F3 mit falschem Beispiel `.gitignore`, D1 F1); `info/` und `~/.gitconfig` nie.
- Neu: G6 unlesbare `.git/config` (D2 F3, über R20/R24) und G8 Ausführbar-Bit/Rechte (C3 F2, D1 F2) als Neben-Treffer.
- 3× schon beantwortet: „nur config oder auch hooks?“ (C1 F1, D2 F1, D3 F3) – die Aufgabe nennt beide.

**alle_tests – anders, nicht besser.**
- Erstmals Fragen zum Anlass „richtig aufrufen“ (T6): C2 F1 Unterprozess oder Import, D2 F1 `discover` oder
  einzeln; dazu Importfehler (C2 F2, D1 F3, D3 F2) – das war am 28.10. der echte Fehler (Suchpfad).
- T1 Umfang: D3 F3 „nur `tests/` oder alle `test_*.py` im Repo“ – bester Treffer bisher; T5 Ausgabe: D2 F2.
- T2, T3, T4 (Zeitlimit): 0/6 (A+B: Zeitlimit 2/6).
- Neuer Fehler: C liest „Prüfskript“ als statische Prüfung der Testdateien (C1 F2, C3 F1/F3) – vermutlich
  gelenkt von `tests-pruefen` im Kontext.

## Was Hawe beantworten kann

Hawe (05.11.): Ob eine Frage sein Ergebnis verändert hätte, kann er nicht beurteilen. Daraus folgt ein zweiter
Maßstab: Eine Rückfrage an Hawe muss eine Entscheidung des Auftraggebers sein (melden oder blockieren,
Offene Fragen als Fehler, nur `tests/` oder alles), keine Umsetzungsfrage (Unterprozess oder Import,
`discover` oder einzeln, Mocking). In allen vier Varianten ist etwa die Hälfte der Fragen Umsetzungsdetail –
der Prompt steuert das nicht.

## Einschätzung

- Kontext ist der Hebel – aber nur, wo der Gegenstand im Kontext steht: `spec_pruefen` prüft die Spec-Vorlage,
  und die Vorlage stand im Kontext. Bei `git_schutz` und `alle_tests` hängen die Entscheidungen am Code
  (wie `umsetzung-auto` den Schreibbereich prüft, wie Tests aufgerufen werden), der nicht im Kontext stand.
- Das stützt die Vermutung zu K12c: Das Modell braucht die passenden Code-Auszüge (Zwei-Schritt: Quellen
  vorschlagen → `quellen` holt Auszüge → Modell arbeitet). Derselbe Mechanismus würde K12b helfen.
- Als eigenständiger Kettenschritt trägt K12b in dieser Form noch nicht: zu viel Rauschen und zu viele
  Umsetzungsfragen für Hawe; Claude müsste ohnehin filtern.
