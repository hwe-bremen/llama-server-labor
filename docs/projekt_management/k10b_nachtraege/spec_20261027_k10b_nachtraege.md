# Spec: k10b_nachtraege

- **Datum:** 2026-10-27
- **Modell:** Claude (geschrieben und mit einer Referenzlösung gegengerechnet; Umsetzung durch den lokalen Umsetzer per `kette.py umsetzung-auto`)
- **Betroffene Dateien:** `role-split/kette/kette.py` (vier kleine Stellen), neu `tests/test_k10b_nachtraege.py`

## Ziel

Vier kleine Nachträge aus der K10-Abnahme in `kette.py`: Der Umsetzer-Prompt nennt die Pflichtzeilen des Handovers, `abgleich` wertet Bereiche wie „T1–T5“ nicht als Einzelnennung, das Protokoll zeigt die Token-Spitze, und `zusammenfuehren` zählt vom Modell selbst zurückgezogene Befunde nicht als hoch.

## Nicht-Ziele

- Keine weitere Änderung an `kette.py` außer den vier Stellen unten. Nichts umbenennen, nichts neu formatieren, nichts löschen.
- `urteil` (Einzelverdikt) bleibt unverändert.
- Das Format der Protokoll-Hauptzeile (A6 aus K10, `PROTOKOLL_RE`) bleibt unverändert.
- Keine Änderung an Prompts unter `role-split/kette/prompts/`.

## Schreibbereich

- `role-split/kette/kette.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts.
- **Technische Sperre für Tests:** Alle Tests arbeiten in `tempfile.TemporaryDirectory()` und biegen `kette.ROOT`/`kette.PM` dorthin um. A3 läuft über die Attrappe `role-split/kette/testdata/opencode_fake.py` (sperrt sich außerhalb des Temp-Ordners) und die Testklasse `Basis` aus `tests/test_umsetzung_auto.py` (prüft am Ende, dass das echte Repo unverändert ist).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | als Modul importiert (`_umsetzung_prompt`, `abgleich`, `zusammenfuehren`, `umsetzung_auto`) | T1–T4 |

## Quellen

- `role-split/kette/kette.py` def tests_finden – liefert {Test-ID: Titel} aus einer Spec (für A1)
- `role-split/kette/kette.py` def abgleich – Stelle „Nicht getestet“ (für A2)
- `role-split/kette/kette.py` def _umsetzung_prompt – Prompt-Aufbau (für A1)
- `role-split/kette/kette.py` def _lauf – Auswertung von `step_finish` und `info` (für A3)
- `role-split/kette/kette.py` Zeilen 1888–1906 – Protokollzeile, Unterzeilen, Zusammenfassung auf stdout (für A3)
- `role-split/kette/kette.py` def _ist_hoch – Regel „hoch“ (für A4)
- `role-split/kette/kette.py` def zusammenfuehren – Gesamtbefund (für A4)
- `tests/test_umsetzung_auto.py` class Basis – Testaufbau mit Attrappe für einen ganzen `umsetzung_auto`-Lauf (für T3)
- `docs/projekt_management/verdict_20261027_umsetzung_auto_qwen36-35b_betrieb.md` Zeilen 35–40 – Format der Befund-Tabelle (für T4)

## Anforderungen

### A1: Pflichtzeilen des Handovers im Umsetzer-Prompt
- **Anforderung:** `_umsetzung_prompt` liest die Spec des Kurztitels (`datei_suchen("spec", kurztitel, None)`) und holt die Test-IDs mit `tests_finden`. Gibt es mindestens eine Test-ID, hängt die Funktion **nach** dem Grundtext und **vor** einem eventuellen Nachbesserungs-Teil diesen Abschnitt an:
  - eine Leerzeile, dann die Überschrift `## Pflichtzeilen im Handover`;
  - den Satz `Unter „## Getestet“ steht für jede Test-ID genau eine dieser Zeilen (Titel unverändert, Status wählen):`;
  - je Test-ID in Spec-Reihenfolge eine Zeile `**<ID>: <Titel>** – bestanden | fehlgeschlagen` (Titel genau wie von `tests_finden` geliefert);
  - zum Schluss den Satz `Unter „## Nicht getestet“ nur Test-IDs, die wirklich nicht getestet sind – keine Sammelangaben wie „T1–T5“.`
  
  Hat die Spec keine Test-ID (oder gibt es keine Spec), wird nichts angehängt.
- **Stelle:** `def _umsetzung_prompt`
- **Akzeptanz:** T1.

### A2: Bereiche unter „Nicht getestet“
- **Anforderung:** In `abgleich` werden vor dem Suchen der Test-IDs im Abschnitt „Nicht getestet“ alle Bereichsangaben der Form `<ID>–<ID>` oder `<ID>-<ID>` (Gedankenstrich oder Bindestrich, Leerzeichen dazwischen erlaubt, ID nach dem vorhandenen Muster `TEST_ID`) entfernt. Einzeln genannte IDs zählen weiter.
- **Stelle:** `def abgleich`, die Zeile mit `nicht = set(re.findall(...))`
- **Akzeptanz:** T2.

### A3: Token-Spitze
- **Anforderung:** `_lauf` merkt sich in `info["tokens_spitze"]` (Startwert 0) den größten `part.tokens.total` eines einzelnen `step_finish`. `info["tokens"]` (Summe) bleibt wie bisher.
  - Die Unterzeile im Protokoll wird zu `  - Tokens: input <i>, output <o>, reasoning <r>, spitze <s>` (nur `, spitze <s>` angehängt).
  - Die Zusammenfassung auf stdout zeigt statt `Tokens <summe>` jetzt `Tokens <summe> (Spitze <s>)`; der Rest der Zeile bleibt.
- **Stelle:** `def _lauf`; Unterzeile und Zusammenfassung in `def umsetzung_auto` (Zeilen aus den Quellen)
- **Akzeptanz:** T3. Mit der Attrappe (zwei `step_finish` mit total 100 und 50) ergibt das `Tokens 150 (Spitze 100)` und `spitze 100`.

### A4: Zurückgezogene Befunde in `zusammenfuehren`
- **Anforderung:** Neue Funktion `_zurueckgezogen(text: str) -> bool`: Entfernt alle `*` aus dem Befundtext, dann rechts Leerraum; wahr, wenn der Rest auf `Korrekt.` oder auf `Befund entfällt.` endet.
  - In `zusammenfuehren` gilt eine Zeile nur dann als hoch, wenn `_ist_hoch` wahr ist **und** `_zurueckgezogen(<Befundtext>)` falsch.
  - Zeilen, die nach `_ist_hoch` hoch wären, aber zurückgezogen sind, stehen weiter im Gesamtbefund (nichts weglassen), in der Spalte „hoch nach Regel“ mit `nein (zurückgezogen)` statt `nein`.
  - Die Zusammenfassung auf stdout lautet `<n> Befunde aus <m> Läufen, davon <h> hoch, <z> zurückgezogen -> <Ergebnis>`; der Teil `, <z> zurückgezogen` entfällt bei z = 0.
  - Die übrige Ergebnisregel bleibt: Ein `NACHBESSERN` im Ergebnis eines Laufs gilt weiter.
- **Stelle:** neue Funktion direkt vor `def zusammenfuehren`; `def zusammenfuehren`
- **Akzeptanz:** T4.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Spec fehlt oder hat keine Test-ID | nichts | kein Abschnitt angehängt | T1 |
| A1 | Nacharbeit | – | Pflichtzeilen vor dem Nachbesserungs-Teil | – (Reihenfolge, nicht eigens getestet) |
| A2 | Bereich und Einzelnennung gemischt | nichts | Einzelnennung zählt, Bereich nicht | T2 |
| A3 | kein `step_finish` | – | Spitze 0 | – |
| A4 | Befund hoch und nicht zurückgezogen | Gesamtbefund wird geschrieben | `hoch nach Regel: ja`, NACHBESSERN, Exit 1 | T4 |
| A4 | Befund zurückgezogen, beide Läufe PASS | Gesamtbefund wird geschrieben | PASS, Exit 0, Zeile bleibt mit `nein (zurückgezogen)` | T4 |
| A1–A4 | Absturz mitten im Lauf | n. a. (keine Außenwirkung) | – | – |

## Testplan

Alle Tests als `tests/test_k10b_nachtraege.py` (unittest), je Test-ID eine Methode `test_<id>_…`. Kein Test hat Außenwirkung. Neue Funktionen **in der Methode** importieren. Jeder Test muss mit dem alten `kette.py` rot werden; deshalb steht der Gegenfall jeweils **in derselben Methode** (eine eigene Methode nur für den Gegenfall bliebe in der Gegenprobe grün).

Gemeinsamer Aufbau für T1, T2, T4: Klasse mit `setUp`, die ein `tempfile.TemporaryDirectory()` anlegt, darin `docs/projekt_management/`, und `kette.ROOT`/`kette.PM` per `setattr` dorthin umbiegt (mit `addCleanup` zurück). Ausgaben mit `redirect_stdout`/`redirect_stderr` auffangen.

### T1: Prompt nennt je Test-ID eine Pflichtzeile
- **Prüft:** A1, Fehlerpfad „keine Test-ID“
- **Aufbau:** `spec_20261027_k.md` mit `"# Spec: k\n\n## Testplan\n\n### T1: Erster\n- x\n\n### T2: Zweiter Fall\n- y\n"`; Aufruf `_umsetzung_prompt("k", "20261027", "abc1234", None, 1)`. Danach dieselbe Datei mit `"# Spec: k\n\n## Ziel\nx\n"` überschreiben und erneut aufrufen.
- **Erwartung:** Erster Aufruf enthält `## Pflichtzeilen im Handover`, `**T1: Erster** – bestanden | fehlgeschlagen` und `**T2: Zweiter Fall** – bestanden | fehlgeschlagen`. Zweiter Aufruf enthält `Pflichtzeilen` nicht.
- **Warum misst der Test das Richtige?** Ohne A1 fehlt der Abschnitt; ein Abschnitt ohne Spec-Titel oder trotz fehlender Tests fällt ebenfalls auf.
- **Gegenprobe:** alter `kette.py` → rot (Abschnitt fehlt).

### T2: abgleich – Bereich unter „Nicht getestet“ ist keine Einzelnennung
- **Prüft:** A2
- **Aufbau:** Spec wie in T1 (zwei Tests). Handover `handover_20261027_k.md` mit `## Getestet (mit echter Ausgabe)` und nur der Zeile `**T1: Erster** – bestanden`, darunter `## Nicht getestet` mit `- Nichts, alle Tests (T1–T2) laufen grün.`. Aufruf `kette.abgleich("k")`. Danach denselben Handover mit `- T2: braucht einen echten Server.` unter „Nicht getestet“ schreiben und erneut aufrufen.
- **Erwartung:** Erster Aufruf: Ausgabe enthält `FEHLT     T2` (fünf Leerzeichen nach FEHLT), enthält `NICHT GET` nicht, Rückgabe 1. Zweiter Aufruf: Ausgabe enthält `NICHT GET T2`.
- **Warum misst der Test das Richtige?** Mit dem alten Code steht im ersten Aufruf `NICHT GET T2`; wird die Einzelnennung mit entfernt, fehlt sie im zweiten.
- **Gegenprobe:** alter `kette.py` → rot (erster Aufruf).

### T3: Tokens – Spitze je Schritt im Protokoll und auf stdout
- **Prüft:** A3
- **Aufbau:** Testklasse leitet von `Basis` aus `tests/test_umsetzung_auto.py` ab (`from tests.test_umsetzung_auto import Basis, HANDOVER` am Dateianfang; vorher `sys.path` um den Repo-Stamm und `role-split/kette` ergänzen). Lauf mit `self.lauf(FAKE_HANDOVER=HANDOVER)`.
- **Erwartung:** Rückgabe 0; Ausgabe enthält `Tokens 150 (Spitze 100)`; `self.protokoll()` enthält `  - Tokens: input 130, output 18, reasoning 2, spitze 100`.
- **Warum misst der Test das Richtige?** Die Attrappe liefert zwei Schritte mit total 100 und 50; Summe 150 und Spitze 100 unterscheiden sich, eine Verwechslung fällt auf.
- **Gegenprobe:** alter `kette.py` → rot (`(Spitze` fehlt).

### T4: zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht
- **Prüft:** A4, beide Fehlerpfade
- **Aufbau:** Zwei Verdikte in `PM`: `verdict_20261027_k_qwen36-35b.md` und `verdict_20261027_k_qwen36-35b_betrieb.md`, je `# V\n\n## Ergebnis\n\nPASS\n\n## Befunde\n\n` plus Tabellenkopf `| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |` und Trennzeile. Erstes Verdikt mit zwei Zeilen:
  `| 1 | nein | nein | nein | hoch | `x.py:1` | Prüfung X ist da. **Befund entfällt.** | – |` und
  `| 2 | nein | ja | nein | hoch | `x.py:2` | Fall Y: Exit 2. **Korrekt.** | – |`;
  zweites Verdikt mit der Leerzeile `| – | nein | nein | nein | – | – | keine Befunde | – |`. Aufruf `kette.zusammenfuehren([p1, p2])`.
  Danach das erste Verdikt nur mit der Zeile `| 1 | nein | nein | nein | hoch | `x.py:1` | Timeout fehlt, Lauf hängt unbegrenzt. | – |` neu schreiben und erneut aufrufen.
- **Erwartung:** Erster Aufruf: Rückgabe 0; Ausgabe enthält `davon 0 hoch, 2 zurückgezogen -> PASS`; `gesamt_20261027_k.md` enthält genau zweimal `| nein (zurückgezogen) |` und den Text `Befund entfällt.`. Zweiter Aufruf: Rückgabe 1; Ausgabe enthält `davon 1 hoch -> NACHBESSERN`.
- **Warum misst der Test das Richtige?** Mit dem alten Code ergibt der erste Aufruf NACHBESSERN (2 hoch); wird zu viel ausgefiltert, bleibt der zweite fälschlich PASS; fehlt eine Zeile im Gesamtbefund, stimmt die Zählung nicht.
- **Gegenprobe:** alter `kette.py` → rot (erster Aufruf).

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
