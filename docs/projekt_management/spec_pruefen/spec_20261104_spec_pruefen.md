# Spec: spec_pruefen

- **Datum:** 2026-11-04
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette_lauf` aus der Chat-UI
- **Betroffene Dateien:** neu `role-split/kette/spec_pruefen.py`; `role-split/kette/kette.py` (nur Docstring und `main`)
- **Änderungsstellen:** 4 (neue Datei; in `kette.py` Docstring, `add_parser`, Verteiler)

## Ziel

K12a: `kette.py spec-pruefen <kt>` prüft eine Spec **mechanisch, ohne Modell**, bevor Vorgabe-Tests und Lauf darauf aufbauen – analog zu `pruefen` für die Umsetzung. Geprüft werden Pflichtabschnitte, übrig gebliebene Platzhalter der Vorlage, offene Fragen, Größe samt Änderungsstellen (R55/R59, nur Hinweis), die Zuordnung Anforderung ↔ Stelle ↔ Test, der Schreibbereich (R47) und die Form der Quellen. Grundlage für K12b (Rückfragen) und K12c (Spec-Entwurf als Messung). Zugleich die Probe für R59.

## Nicht-Ziele

- **`tests/test_spec_pruefen.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Änderung an `automatik.py` (`lauf` nutzt `spec-pruefen` erst in einer späteren Kette), an den MCP-Werkzeugen, an Prompt-Vorlagen oder an `docs/projekt_management/_vorlage_spec.md` (die Pflichtzeile „Änderungsstellen“ kommt mit dieser Spec).
- In `kette.py` nur die drei genannten Stellen; keine bestehende Funktion ändern.
- Kein Modellaufruf, keine Datei schreiben, nichts im Repo ändern. Inhaltliche Qualität einer Spec prüft das Werkzeug nicht.
- Alle bestehenden Tests bleiben grün (`python3 scripts/alle_tests.py`).

## Schreibbereich

- `role-split/kette/spec_pruefen.py`
- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Nichts. Das Werkzeug liest genau eine Spec-Datei und gibt Text aus.
- **Technische Sperre für Tests:** T1–T7 prüfen Texte direkt oder biegen `kette.PM` per `mock.patch.object` auf ein `tempfile.TemporaryDirectory()` um. T8 ruft das echte Werkzeug am echten Repo nur lesend auf und prüft, dass `git status --porcelain` vorher und nachher gleich ist.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py spec-pruefen <kt>` (Befehlszeile, auch aus anderem Arbeitsordner) | T8 |
| `role-split/kette/kette.py` | `kette.main(["spec-pruefen", kt])` | T7 |
| `role-split/kette/spec_pruefen.py` | als Modul (`PFLICHT`, `PLATZHALTER`, `R59`, `aenderungsstellen`, `pruefe`, `spec_pruefen`) | T1–T8 |

## Quellen

- `role-split/kette/automatik.py` Zeilen 1–16 – Kopf und Import-Muster (Modul importiert `kette`, nicht umgekehrt)
- `role-split/kette/automatik.py` def groesse – Dateien/Anforderungen/Tests, wird unverändert wiederverwendet
- `role-split/kette/kette.py` def abschnitt – Inhalt eines Abschnitts (Präfix-Treffer, ohne Groß/klein)
- `role-split/kette/kette.py` Zeilen 235–252 – `TEST_ID` und `tests_finden`
- `role-split/kette/kette.py` def datei_suchen – Spec finden (Ablage-Ordner, sonst flach)
- `role-split/kette/kette.py` def quelle_lesen – eine Quellen-Zeile lesen (`None` = nicht lesbar)
- `role-split/kette/kette.py` Zeilen 1203–1208 – Schleife in quellen: Muster für „sieht nach Fundstelle aus, Form unklar“
- `role-split/kette/kette.py` def _schreibbereich – Einträge des Schreibbereichs (`None` = Abschnitt fehlt)
- `role-split/kette/kette.py` def _ist_vorgabe – Vorgabe-Dateien
- `role-split/kette/kette.py` Zeilen 647–648 – `PAKET_NIE`
- `role-split/kette/kette.py` Zeilen 64–69 – Docstring: Einfügestelle für den neuen Befehl
- `role-split/kette/kette.py` def main – Einbaustelle Parser und Verteiler
- `tests/test_spec_pruefen.py` Zeilen 22–47 – `PFLICHT_ERWARTET` und `PLATZHALTER_ERWARTET`: Werte für `PFLICHT` und `PLATZHALTER`, **Zeichen für Zeichen** übernehmen (Gedankenstrich, Auslassungszeichen, Umlaute, „ und ")
- `docs/projekt_management/_vorlage_spec.md` – Vorlage, aus der die Platzhalter stammen

## Anforderungen

### A1: Modul, Befehl und Ausgabe
- **Anforderung:** Neue Datei `role-split/kette/spec_pruefen.py`, Kopf wie `automatik.py` (`import re`, `import sys`, `import automatik`, `import kette`). Konstanten:
  - `PFLICHT` = Tupel wie `PFLICHT_ERWARTET`, `PLATZHALTER` = Tupel wie `PLATZHALTER_ERWARTET` (Quelle `tests/test_spec_pruefen.py`).
  - `R59 = {"dateien": 1, "anforderungen": 4, "tests": 8, "stellen": 9}`.

  `spec_pruefen(kurztitel: str) -> int`:
  1. Kurztitel nicht `[a-z0-9_]+` (`re.fullmatch`) → auf **stderr** `Kurztitel '<kt>' ungültig (nur a-z, 0-9, _).`, Exit 2, nichts auf stdout.
  2. `spec_p = kette.datei_suchen("spec", kurztitel, None)`; `None` → stdout `Keine spec_*_<kt>.md`, Exit 2.
  3. `befunde, hinweise, g = pruefe(spec_p.read_text(encoding="utf-8"))`. Ausgabe genau so (zwei Leerzeichen Einrückung; nach `BEFUND` drei, nach `HINWEIS` zwei Leerzeichen), erst alle Befunde, dann alle Hinweise:
     ```
     Spec-Prüfung <kt>: <spec_p.name>
       Größe: <dateien> Datei(en), <anforderungen> Anforderungen, <tests> Tests, <stellen oder ?> Änderungsstellen (R59 1/4/8/9, vorläufig)
       BEFUND   <text>
       HINWEIS  <text>
     ```
     Schlusszeile: mit Befunden `<n> Befund(e), <m> Hinweis(e).` und Exit 1; ohne Befunde `Keine Befunde (<m> Hinweis(e)).` und Exit 0 – **Hinweise ändern den Exit-Code nie**.

  In `kette.py`:
  - (a) Docstring: direkt vor der Zeile `Exit-Codes: 0 = …` ein Absatz `  python3 role-split/kette/kette.py spec-pruefen <kurztitel>` mit Kurzbeschreibung.
  - (b) `main`: unmittelbar nach `st.add_argument("kurztitel")` die Zeilen `sp = sub.add_parser("spec-pruefen", help=…)` und `sp.add_argument("kurztitel")`.
  - (c) Verteiler: unmittelbar vor `if args.cmd == "einsortieren":` die Zeilen `if args.cmd == "spec-pruefen":`, `import spec_pruefen` und `return spec_pruefen.spec_pruefen(args.kurztitel)` (Import im Zweig, wie bei `automatik`).
- **Stelle:** neue Datei `role-split/kette/spec_pruefen.py`, Funktion `spec_pruefen` am Dateiende; in `kette.py` Docstring vor `Exit-Codes:`, `main` nach `st.add_argument("kurztitel")` und vor `if args.cmd == "einsortieren":`.
- **Akzeptanz:** T1, T7, T8.

### A2: Abschnitte, Platzhalter, offene Fragen
- **Anforderung:** `pruefe(spec_text: str) -> tuple[list[str], list[str], dict]` gibt `(befunde, hinweise, groesse)` zurück, liest und schreibt keine Datei. Zuerst werden **alle HTML-Kommentare** entfernt (`re.sub(r"<!--.*?-->", "", spec_text, flags=re.S)`); alle Prüfungen (A2–A4) laufen auf diesem Text. Befunde werden in dieser Reihenfolge angehängt: A2, A3, A4.
  1. Für jeden Titel aus `PFLICHT`, in dieser Reihenfolge: keine Zeile passt auf `rf"^##\s+{re.escape(titel)}"` (`re.M | re.I`) → `Abschnitt „## <titel>“ fehlt`; sonst `kette.abschnitt(text, titel).strip()` leer → `Abschnitt „## <titel>“ ist leer`.
  2. Für jeden Eintrag `p` aus `PLATZHALTER`, in dieser Reihenfolge: `p in text` → `Platzhalter aus der Vorlage: <p>`. **Nur diese wörtlichen Texte**, keine allgemeine Prüfung auf spitze Klammern (echte Specs enthalten `<rel>`, `<kt>`, `<neu|weg|geaendert>`).
  3. Offene Fragen: die nicht leeren, gestrippten Zeilen von `kette.abschnitt(text, "Offene Fragen")`. Sind es keine, gibt es hier keinen Befund (Fall 1 hat ihn schon). Sonst gilt der Abschnitt als geklärt **nur**, wenn es genau eine Zeile ist und sie auf `r"^(?:[-*]\s*)?Keine\b"` (`re.I`) passt; andernfalls `Offene Fragen nicht geklärt – erst beantworten, dann „Keine“`.
- **Stelle:** `spec_pruefen.py`, Hilfsfunktion `_abschnitte(text, befunde)` vor `pruefe`; `pruefe` direkt vor `spec_pruefen`.
- **Akzeptanz:** T1, T2, T3, T8.

### A3: Größe, Änderungsstellen, Zuordnung
- **Anforderung:**
  1. `aenderungsstellen(spec_text: str) -> int | None`: erste Zeile, die auf `r"^\s*[-*]\s*\*\*Änderungsstellen:\*\*\s*(\d+)"` (`re.M`) passt → die Zahl, sonst `None` (auch bei Text statt Zahl).
  2. `groesse = automatik.groesse(text)` plus Schlüssel `"stellen": aenderungsstellen(text)` – genau die vier Schlüssel `dateien`, `anforderungen`, `tests`, `stellen`. `stellen` ist `None` → Befund `Zeile „- **Änderungsstellen:** n“ fehlt`.
  3. Hinweise, in dieser Reihenfolge, je Wert über `R59` (`>`; `None` zählt nicht): `Größe über R59 (vorläufig): Dateien <n> > 1`, `… Anforderungen <n> > 4`, `… Tests <n> > 8`, `… Änderungsstellen <n> > 9`. Nur Hinweise, nie Befunde (R59 ist vorläufig).
  4. Anforderungen = Überschriften `r"^###\s+([A-Za-z]+\d+):\s"` (`re.M`) in `kette.abschnitt(text, "Anforderungen")`; Rumpf = Text bis zur nächsten solchen Überschrift. Je Anforderung, in Reihenfolge: keine Zeile `r"^\s*[-*]\s*\*\*Stelle:\*\*[ \t]*\S"` (`re.M`; **`[ \t]`, nicht `\s`**, sonst zählt die Folgezeile) → `<id> ohne „Stelle:“`.
  5. Tests = Überschriften `rf"^###\s+({kette.TEST_ID})\b"` (`re.M`) in `kette.abschnitt(text, "Testplan")`, Rumpf ebenso. Je Test, in Reihenfolge: keine Zeile `r"^\s*[-*]\s*\*\*Prüft:\*\*(.*)$"` → `<tid> ohne „Prüft:“`. Sonst aus dem Rest der Zeile erst Klammerzusätze `\([^)]*\)`, dann Code in Backticks `` `[^`]*` `` durch Leerzeichen ersetzen; genannt sind alle `re.findall(r"\b([A-Za-z]+\d+)(?:\.\d+)*", rest)`, **die als Anforderung vorkommen** (Unterpunkte `A3.2` → `A3`, Bereich `A4.2–A4.4` → `A4`). Keiner → `<tid> prüft keine Anforderung der Spec`. Unbekannte IDs (z. B. `R58`) sind kein Befund.
  6. Danach je Anforderung, in Reihenfolge, die in keinem Test genannt ist: `<id> von keinem Test geprüft`.
- **Stelle:** `spec_pruefen.py`, `aenderungsstellen` direkt hinter den Konstanten; Hilfsfunktionen `_groesse` und `_zuordnung` hinter `_abschnitte`.
- **Akzeptanz:** T1, T4, T5, T8.

### A4: Schreibbereich und Quellen
- **Anforderung:**
  1. `eintraege = kette._schreibbereich(text)`; `None` → nichts (A2 meldet). `[]` → `Schreibbereich ohne Eintrag`. Je Eintrag `e`: `e.startswith(kette.PAKET_NIE)` → `Schreibbereich unter <erster Pfadteil>/: <e> (R47)` (z. B. `Schreibbereich unter docs/: docs/x.py (R47)`); `kette._ist_vorgabe(e)` → `Schreibbereich enthält Vorgabe-Datei: <e>`.
  2. Je Zeile `z` von `kette.abschnitt(text, "Quellen")`: `kette.quelle_lesen(z)` liefert etwas → erkannt; sonst, wenn `z` auf `` r"^\s*[-*]\s*`[^`]+/[^`]*`" `` passt (dasselbe Muster wie in `quellen`) → `Quelle nicht lesbar: <z.strip() bis 120 Zeichen>`. Gibt es den Abschnitt (`^##\s+Quellen`, `re.M | re.I`), aber keine erkannte Zeile → `Quellen ohne Fundstelle der Form - `pfad` …`.
- **Stelle:** `spec_pruefen.py`, Hilfsfunktion `_bereich_quellen` hinter `_zuordnung`, aufgerufen als letzte Prüfung in `pruefe`.
- **Akzeptanz:** T1, T6.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Kurztitel ungültig | nichts | stderr „ungültig“, stdout leer, Exit 2 | T7 |
| A1 | Spec fehlt | nichts | `Keine spec_*_<kt>.md`, Exit 2, keine Datei angelegt | T7 |
| A1 | Spec flach statt im Ablage-Ordner | – | gefunden (über `datei_suchen`) | T7 |
| A1 | nur Hinweise | – | Exit 0, `Keine Befunde (<m> Hinweis(e)).` | T4 |
| A1 | Lauf schreibt etwas | – | nein: Temp-Ordner und `git status` unverändert | T1, T7, T8 |
| A1 | Aufruf aus anderem Arbeitsordner | – | Spec über `kette.PM`, nicht über cwd | T8 |
| A2 | Abschnitt fehlt / nur Kommentar / nur Leerzeichen | – | `fehlt` bzw. `ist leer`, nicht beides | T2 |
| A2 | Platzhalter der Vorlage übrig | – | je Platzhalter ein Befund | T3 |
| A2 | `<rel>`, `<kt>`, `<neu|weg|geaendert>`, Platzhalter im HTML-Kommentar | – | kein Befund | T1, T8 |
| A2 | Offene Fragen „Keine“ mit Punkt, Stern, Klammerzusatz | – | kein Befund | T3 |
| A2 | „Keine“ plus weitere Frage | – | Befund | T3 |
| A3 | Änderungsstellen fehlt / Text statt Zahl | – | Befund, `?` in der Größenzeile | T4, T7 |
| A3 | Werte über R59 | – | nur Hinweise, Exit 0; genau 9 Stellen kein Hinweis | T4 |
| A3 | `Stelle:` fehlt oder leer | – | Befund | T5 |
| A3 | `Prüft:` fehlt / nur Klammer- und Backtick-Zusätze / Bereich mit Unterpunkten | – | Befund / Befund / gezählt | T5 |
| A4 | Schreibbereich unter `docs/`, `experiments/`, Vorgabe-Datei, ohne Eintrag | – | je ein Befund | T6 |
| A4 | Quellen-Zeile unlesbar, nur Prosa | – | je ein Befund | T6 |
| A2–A4 | echte Specs `git_schutz`, `alle_tests` | – | nur der Befund „Änderungsstellen“ (alte Specs), keine Fehlalarme | T8 |

## Testplan

Die Tests stehen in `tests/test_spec_pruefen.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Vorab 8/8 rot (Modul fehlt); gegen die Referenz 8/8 grün, dreimal stabil (< 1 s). Mutationsprüfung der Referenz: 36 von 36 gefangen (u. a. fehlender Pflichttitel, Umlaut/Gedankenstrich/Auslassungszeichen falsch geschrieben, Kommentare nicht entfernt, „fehlt“ und „leer“ doppelt, allgemeine Prüfung auf spitze Klammern, „Keine“ plus Frage, Größe als Befund, `>=` statt `>`, `\s` statt `[ \t]` bei „Stelle:“, Klammer-/Backtick-Zusätze mitgezählt, Unterpunkt als eigene ID, Prüfung auf `PAKET_NIE`/Vorgabe/Quellen fehlt, Exit bei Hinweisen, nur flach gesucht, Hinweise vor Befunden, Verteiler in `kette.py` fehlt).

### T1: Gültige Spec – keine Befunde, genaue Ausgabe, nichts geschrieben
- **Prüft:** A1, A2, A3, A4
- **Aufbau:** Muster-Spec `GUT` mit allen Abschnitten, `<rel>`/`<kt>`/`<neu|weg|geaendert>` im Text, Vorlagen-Kommentar mit Platzhaltern, `Prüft:` mit Klammer- und Backtick-Zusatz und Bereich; Temp-`PM` mit Ablage-Ordner.
- **Erwartung:** `pruefe` → `([], [], {"dateien": 1, "anforderungen": 2, "tests": 2, "stellen": 3})`; `spec_pruefen` Exit 0, genau drei Ausgabezeilen; Temp-Ordner unverändert.
- **Warum misst der Test das Richtige?** Jeder Fehlalarm oder eine falsche Ausgabezeile macht ihn rot.
- **Gegenprobe:** alter Stand → rot (Modul fehlt).

### T2: Pflichtabschnitte fehlen oder sind leer
- **Prüft:** A2.1
- **Aufbau:** je Pflichtabschnitt eine Fassung ohne ihn; Fehlerpfade nur mit Kommentar; Nicht-Ziele nur Leerzeichen.
- **Erwartung:** je `Abschnitt „## <titel>“ fehlt` und nicht zusätzlich `ist leer`; `ist leer` statt `fehlt`; bei Nicht-Ziele und bei leeren Offenen Fragen genau dieser eine Befund.
- **Warum misst der Test das Richtige?** Ein vergessener Titel in `PFLICHT` oder ein nicht entfernter Kommentar fällt auf.
- **Gegenprobe:** alter Stand → rot.

### T3: Platzhalter der Vorlage und offene Fragen
- **Prüft:** A2.2, A2.3
- **Aufbau:** je Platzhalter in den Zielsatz eingefügt; Offene Fragen in sechs Fassungen.
- **Erwartung:** je Platzhalter genau sein Befund; vier „Keine“-Fassungen ohne Befund, zwei mit genau dem Befund „Offene Fragen nicht geklärt …“.
- **Warum misst der Test das Richtige?** Ein Lauf auf einer halb ausgefüllten Vorlage oder mit offener Frage muss auffallen.
- **Gegenprobe:** alter Stand → rot.

### T4: Änderungsstellen Pflicht, Größe über R59 nur Hinweis
- **Prüft:** A3.1–A3.3, A1 (Exit 0 bei Hinweisen)
- **Aufbau:** `GUT` ohne Zeile; Text statt Zahl; „12 (verteilt)“ mit 2 Dateien und 5 Anforderungen; genau 9 Stellen; Lauf über Temp-`PM`.
- **Erwartung:** genau der Befund „Zeile … fehlt“, `stellen` `None`; drei Hinweise in Reihenfolge, keine Befunde; 9 → kein Hinweis; Exit 0, Schlusszeile `Keine Befunde (3 Hinweis(e)).`; mit Befund und Hinweisen Exit 1, genaue Ausgabe (Befunde vor Hinweisen).
- **Warum misst der Test das Richtige?** Entscheidung Hawe 04.11.: R59 vorläufig, Überschreitung nur Hinweis.
- **Gegenprobe:** alter Stand → rot.

### T5: Stelle und Prüft-Zuordnung
- **Prüft:** A3.4–A3.6
- **Aufbau:** `Stelle:` entfernt bzw. leer; `Prüft:` entfernt; `Prüft:` nur mit `(A1)`, `` `A1` ``, `R58`; Bereich `A1.2–A2.4 (Bestand: A9)`.
- **Erwartung:** genau die Befunde in Reihenfolge; Bereich ohne Befund.
- **Warum misst der Test das Richtige?** Bildet die Schreibweisen aus `git_schutz`/`alle_tests` nach (`A3.2`, `A4.2–A4.4`, Klammerzusätze).
- **Gegenprobe:** alter Stand → rot.

### T6: Schreibbereich und Quellen
- **Prüft:** A4
- **Aufbau:** Schreibbereich `docs/x.py`, `experiments/neu/`, `role-split/kette/spec_alt.md`, nur Text; Quellen-Zeile ohne Trenner; Quellen nur Prosa.
- **Erwartung:** je genau der angegebene Befund.
- **Warum misst der Test das Richtige?** R47: Schreibbereich unter `docs/` blendet Paket und Gegenprobe aus.
- **Gegenprobe:** alter Stand → rot.

### T7: Aufruf über `kette.main` und Fehlerpfade
- **Prüft:** A1
- **Aufbau:** `kette.main(["spec-pruefen", …])` mit ungültigem Kurztitel, ohne Spec, mit Spec flach und im Ablage-Ordner.
- **Erwartung:** Exit 2/stderr „ungültig“/stdout leer; Exit 2 `Keine spec_*_fehlt.md`, Temp-Ordner leer; je Exit 1 mit genau vier Ausgabezeilen.
- **Warum misst der Test das Richtige?** Ohne Verteiler in `kette.py` gibt es den Befehl nicht (R58: über den Aufruf testen).
- **Gegenprobe:** alter Stand → rot.

### T8: Standardwerte und Trockenlauf am echten Bestand
- **Prüft:** A1, A2, A3 (R58, R57: echter Pfad, echter Bestand)
- **Aufbau:** echte Konstanten und `kette.PM`; echte Vorlage; `python3 role-split/kette/kette.py spec-pruefen <kt>` mit Arbeitsordner `docs/` für `git_schutz`, `alle_tests` und diese Spec; `git status --porcelain` vorher/nachher.
- **Erwartung:** `R59`, `PFLICHT`, `PLATZHALTER` wie vorgegeben, jeder Platzhalter steht in der Vorlage, Vorlage hat die Zeile „Änderungsstellen“; `git_schutz` Exit 1 mit nur dem Befund „Änderungsstellen“ und ohne Hinweis; `alle_tests` ebenso plus genau Hinweis `Anforderungen 5 > 4`; diese Spec Exit 0 ohne Befund; Arbeitsstand unverändert.
- **Warum misst der Test das Richtige?** Er zeigt, dass spitze Klammern wie `<rel>` und `Prüft`-Zusätze in echten Specs keinen Fehlalarm geben und dass das Werkzeug über die Befehlszeile läuft.
- **Gegenprobe:** alter Stand → rot (Befehl unbekannt, Exit 2).

## Offene Fragen

- Keine

## Abweichende Meinung

- Alte Specs (vor dieser Kette) bekommen immer den Befund „Änderungsstellen fehlt“. Das ist gewollt (Pflicht für neue Specs); eine Ausnahme nach Datum hätte mehr Logik als Nutzen.
- Probe am übrigen Bestand (Referenz, 04.11.): `ablage_ordner` und `einsortieren` melden zusätzlich echte Lücken („ohne Stelle:“ bei E1–E6 bzw. G2–G5); `lauf_status`, `mcp_kette` nur den Änderungsstellen-Befund und Größen-Hinweise. Keine Fehlalarme gefunden.
- Diese Spec selbst bekommt den Hinweis „Dateien 2 > 1“ (neue Datei plus drei kleine Stellen in `kette.py`, Muster K13b). Bewusst so, damit der Befehl in `kette.py` erreichbar ist.
