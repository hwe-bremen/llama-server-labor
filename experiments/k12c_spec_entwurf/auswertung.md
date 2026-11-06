# K12c-Messung – Auswertung (06.11.2026, Lauf `ergebnisse/20261106_170307`)

Bewertung: Claude, gegen `schluessel.md` (vor dem Lauf committet, `5e1c8a8`). Die mechanische Spalte ist von Hawe
in `uebersicht.md` nachprüfbar; die inhaltliche Bewertung ist Claudes Urteil (Zweitbewertung nur bei knappem
Ergebnis vorgesehen – das Ergebnis ist nicht knapp).

## Ergebnis: trägt nicht

| Kette | mechanisch ok | inhaltlich ok |
|---|---|---|
| git_schutz | 1/3 (#2) | 0/3 |
| spec_pruefen | 0/3 | 0/3 |
| lauf_spec_pruefen | 0/3 | 0/3 |

Maßstab war: in ≥ 2 von 3 Ketten je ≥ 2 von 3 Wiederholungen mechanisch **und** inhaltlich ok. Erreicht: 0 Ketten.

## Betrieb

- 9/9 Läufe vollständig, kein `length`, kein Abbruch. Schritt 1: 5–20 s; Schritt 3: 49–102 s, 1366–2823 Token.
- Ganzer Lauf ~28 min. Tempo ist kein Engpass.
- Die Entwürfe sind kurz (1,4–2,8K Token; Claudes Specs ~5–7K) und flach: Testpläne ohne echte Gegenprobe
  („Keine (neuer Code)“), Fehlerpfade nur der naheliegende Fall.

## Inhaltlich je Kette

**lauf_spec_pruefen – Ziel in 3/3 verfehlt.** Kein Entwurf ändert `automatik.lauf`. #1 baut die Prüfung in
`kette.py pruefen` (nach der Umsetzung, nicht davor), #2 und #3 bauen eine Funktion `kette.py spec_pruefen`, die es
nicht gibt, und ändern `spec_pruefen.py`. LT1–LT6 alle verfehlt; LA1 („vor der Umsetzung“) verletzt.

**spec_pruefen – Zuschnitt 3/3 verfehlt, Kern-A mehrfach verletzt.** Alle drei bauen alles in `kette.py`
(ST1 falsch; R59 im Prompt). #1 dreht die Exit-Semantik um (Offene Fragen „Keine“ → Exit 1; fehlende
Änderungsstellen → Exit 0), #2 prüft allgemein auf `<…>` (ausdrücklich ausgeschlossen) und gewährt Bestandschutz
für alte Specs (Antwort sagte: keine Ausnahme), #3 misst die Größe in Zeichen (> 60.000) statt gegen R59 und lässt
Stelle/Prüft, Schreibbereich und Quellen weg. Keine Wiederverwendung von `automatik.groesse`, `kette.abschnitt`,
`quelle_lesen` (ST2).

**git_schutz – Mechanismus und Einbaustelle 3/3 falsch.** #1 will die Schreibbereich-Prüfung erweitern
(`_im_schreibbereich`) – sieht das Git-Verzeichnis nie – und prüft „vor dem Start, ob `.git/config` vorhanden ist“
(wäre immer rot). #2 (der eine mechanisch ok) vergleicht vorher/nachher, aber in `def pruefen`, das erst nach der
Umsetzung läuft (GT1 falsch), und fest `ROOT/.git` (GT3 falsch). #3 **blockiert** über ein MCP-Werkzeug
`replace_in_file` in `mcp-server/kette_werkzeuge.py` (gibt es dort nicht; der Umsetzer läuft über opencode) –
GA1 verletzt, Funktion erfunden.

**Offene Fragen:** 9/9 „Keine“. Kein Entwurf kennzeichnet Unsicherheit, obwohl die Einbaustellen nicht in den
Quellen standen (R02 verletzt).

## Ursache: Schritt 1 wählt die falschen Quellen

Der Zwei-Schritt trägt nur, wenn Schritt 1 die Einbaustelle anfordert. Das tut er kaum:
- lauf_spec_pruefen: `automatik.py def lauf` in **0/3** angefordert (stattdessen `kette.py def pruefen`,
  `spec_pruefen.pruefe`, erfundenes `kette.py def spec_pruefen`). Schritt 3 hat die Einbaustelle nie gesehen.
- git_schutz: `kette.py def umsetzung_auto` in 1/3; sonst `pruefen`, `gegenprobe`, `paket`, `_diff`.
- spec_pruefen: die wiederverwendbaren Bausteine kaum (`abschnitt` 1/3, `automatik.groesse` 0/3).

Das Modell wählt Namen, die nach dem Thema **klingen** (pruefen, gegenprobe, Schreibbereich), nicht die Stelle, an
der die Entscheidung hängt. Die Funktionsliste im Kontext reicht dafür nicht: Sie zeigt Namen, nicht wer wen
aufruft. Damit bestätigt K12c den Befund aus K12b („Kontext hilft nur, wo der Gegenstand im Kontext steht“) und
zeigt zusätzlich: Das Modell kann den Gegenstand selbst nicht zuverlässig finden.

## Schritt 1 als Rückfragen-Messung (Wiederholung von K12b)

Der Prompt verlangte ausdrücklich Auftraggeber-Entscheidungen. Ergebnis: 8 Fragen in 9 Läufen, davon
**0 Kern-Treffer, 2 schon beantwortet** (git_schutz #2 „auch HEAD/index?“ – Antwort: nicht das ganze Verzeichnis;
spec_pruefen #2 „alte Specs Ausnahme?“ – Antwort: keine Ausnahme), **6 Umsetzungsdetails oder falscher Rahmen**
(Meldung auf stderr oder Log-Datei; „Änderungsstellen“ als eigener Abschnitt; sammeln oder abbrechen …), 1× „Keine
Rückfragen“. Die Anweisung „nur Auftraggeber-Entscheidungen“ wirkt nicht; gegenüber K12b eher schlechter.

## Einschränkungen der mechanischen Spalte

Ein Teil der mechanischen Befunde ist Messartefakt, ändert das Ergebnis aber nicht (inhaltlich 0/9):
- `spec_pruefen`: Entwürfe, die die Platzhalter der Vorlage als **Inhalt** aufzählen, bekommen Platzhalter-Befunde.
- Quellen der Form `` `pfad` NAME – Zweck `` (Konstante ohne Backticks) erkennt `quelle_lesen` nicht (UNKLAR);
  der Prompt zeigte diese Form nicht.

## Folgerung (Vorschlag Claude)

- K12c in dieser Form **nicht** weiterverfolgen; Spec, Rückfragen, Vorgabe-Tests und Referenz bleiben bei Claude.
- Lohnend wäre höchstens ein anderer Hebel als mehr Prompt: Claude nennt die Einbaustellen (wie heute in den
  Quellen), das lokale Modell füllt nur die Fleißteile (Fehlerpfad-Tabelle, Einstiegspunkte) – das wäre eine neue,
  kleinere Messung, kein Fortsetzen von K12c. Nutzen fraglich, weil genau die Einbaustelle der teure Teil ist.
- Kandidat Lernregel (nicht freigegeben): Ein lokales Modell findet die Einbaustelle einer Änderung nicht aus einer
  Funktionsliste; es wählt thematisch klingende Namen. Quellen und Einbaustellen legt Claude fest.
