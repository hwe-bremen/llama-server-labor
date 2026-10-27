# Spec: vorgabe_tests

- **Datum:** 2026-10-27
- **Modell:** Claude (Spec, Vorgabe-Tests und Referenzlösung; Umsetzung durch den lokalen Umsetzer per `kette.py umsetzung-auto`)
- **Betroffene Dateien:** `role-split/kette/kette.py` (eine neue Funktion `tests_pruefen` samt Helfer, drei kleine Stellen in `umsetzung_auto`/`_umsetzung_prompt`, Subparser); Vorgabe `tests/test_vorgabe_tests.py` (schon geschrieben)

## Ziel

Rollenteilung „Tests vorab, Umsetzer schreibt nur Code“ mechanisch absichern: Eine Spec mit dem Abschnitt `## Vorgabe-Tests` erklärt `tests/test_<kurztitel>.py` zur Vorgabe. Neuer Befehl `kette.py tests-pruefen <kurztitel>` prüft solche Tests vor dem Start (je Test-ID eine Methode, Skript lädt, jeder Test rot ohne Umsetzung). `umsetzung-auto` startet einen Erstlauf nur bei bestandener Prüfung, sagt dem Umsetzer im Prompt, dass er die Testdatei nicht ändert, und meldet jede Änderung daran als Verstoß.

## Nicht-Ziele

- **`tests/test_vorgabe_tests.py` ist Vorgabe dieser Kette und wird nicht geändert – keine Zeile.** Die Tests stehen schon; schreib nur den Code in `kette.py`, bis sie grün sind.
- Keine weitere Änderung an `kette.py` außer den Stellen unten. Nichts umbenennen, nichts neu formatieren, nichts löschen.
- Specs ohne `## Vorgabe-Tests` verhalten sich genau wie bisher (Umsetzer darf die Testdatei schreiben).
- Keine Änderung an `prompts/`, `_vorlage_spec.md`, RUNBOOK (macht Claude getrennt).
- Kein `lauf`, keine Größenprüfung (das ist K11b).

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_vorgabe_tests.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts.
- **Technische Sperre für Tests:** T1–T5 arbeiten in `tempfile.TemporaryDirectory()` mit umgebogenem `kette.ROOT`/`kette.PM`. T6–T8 nutzen `Basis` aus `tests/test_umsetzung_auto.py` (eigenes Temp-Git-Repo, Attrappe `role-split/kette/testdata/opencode_fake.py` mit Temp-Sperre, Prüfung am Ende, dass das echte Repo unverändert ist).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py tests-pruefen <kt>` (über `main`) | T1 |
| `role-split/kette/kette.py` | als Modul importiert (`tests_pruefen`, `umsetzung_auto`, `_umsetzung_prompt`) | T1–T8 |

## Quellen

- `role-split/kette/kette.py` def tests_finden – {Test-ID: Titel} aus der Spec (A2)
- `role-split/kette/kette.py` def methoden_pruefen – Hinweise OHNE PRUEF / DOPPELT / SYNTAX (A2)
- `role-split/kette/kette.py` def tests_laufen – Testskript im eigenen Prozess, Ergebnis je Methode (A2)
- `role-split/kette/kette.py` def gegenprobe – Muster für Ausgabezeilen und Abschlusszeile (A2)
- `role-split/kette/kette.py` def abgleich – Abschlusszeile „Keine Abweichung.“ / „n Abweichung(en).“ (A2)
- `role-split/kette/kette.py` def _schreibbereich – Muster, wie ein Spec-Abschnitt erkannt wird (A1)
- `role-split/kette/kette.py` def _umsetzung_prompt – Prompt-Aufbau, Pflichtzeilen, Nachbesserungs-Teil (A4)
- `role-split/kette/kette.py` def umsetzung_auto – Vorab-Prüfungen, Prüfung (b) Schreibbereich (A3)
- `role-split/kette/kette.py` def main – Subparser (A5)
- `tests/test_umsetzung_auto.py` class Basis – Testaufbau T6–T8

## Anforderungen

### A1: Abschnitt „Vorgabe-Tests“ erkennen
- **Anforderung:** Neue Funktion `_vorgabe_tests(spec_text: str) -> bool`: wahr genau dann, wenn eine Zeile `## Vorgabe-Tests` existiert (Leerraum am Zeilenende erlaubt, Muster wie in `_schreibbereich`). Der Inhalt des Abschnitts wird nicht ausgewertet; Vorgabe ist immer `tests/test_<kurztitel>.py`.
- **Stelle:** neue Funktion vor `def spec_commit` (Block „tests-pruefen (K11a)“)
- **Akzeptanz:** T6–T8.

### A2: `tests_pruefen(kurztitel, timeout=300) -> int`
- **Anforderung:** Prüft `tests/test_<kurztitel>.py` gegen die Spec (`datei_suchen("spec", kurztitel, None)`), in dieser Reihenfolge:
  1. Testdatei fehlt → Meldung mit `tests/test_<kurztitel>.py`, Exit 2. Spec fehlt oder hat keine Test-ID (`tests_finden`) → Meldung, Exit 2.
  2. Jeder Hinweis aus `methoden_pruefen` wird als Zeile `  <hinweis>` ausgegeben und zählt als Abweichung.
  3. `tests_laufen(skript, timeout)`; `None` → Zeile `  ZEIT …`, Exit 1.
  4. **Lädt nicht:** Ist unter den Schlüsseln des Ergebnisses keine Testmethode, die im Testskript definiert ist (Namen per `ast`, Präfix `test`; Syntaxfehler = keine), dann Zeile `  LAEDT NICHT …` mit dem Hinweis, neue Funktionen in der Methode zu importieren, Exit 1. (Beim Ladefehler liefert `tests_laufen` nur einen Ersatz-Eintrag statt der Methoden.)
  5. Je Test-ID der Spec in Spec-Reihenfolge: alle Ergebnis-Methoden, deren Name auf `test_<id klein>` gefolgt von `_` oder Ende passt.
     - keine → `  FEHLT     <ID>` (fünf Leerzeichen nach FEHLT), Abweichung;
     - mindestens eine mit Status außer `FAIL`/`ERROR` → `  NICHT ROT <ID>  <methoden>` mit Hinweis „ohne Umsetzung nicht rot“, Abweichung;
     - sonst → `  rot       <ID>` (sieben Leerzeichen nach rot).
  6. Abschlusszeile nach einer Leerzeile: `Keine Abweichung.` bzw. `<n> Abweichung(en).`; Exit 0 bzw. 1.
- „Rot vorab“ heißt: gegen den aktuellen Arbeitsstand (vor der Umsetzung = Stand des Spec-Commits).
- **Stelle:** neue Funktion nach `_vorgabe_tests`
- **Akzeptanz:** T1–T5.

### A3: `umsetzung_auto` mit Vorgabe-Tests
- **Anforderung:**
  - Nach der Prüfung des Arbeitsstands (A2.4) und vor der Suche nach opencode (A2.5): `vorgabe = _vorgabe_tests(<Spec-Text>)`. Wenn wahr:
    - fehlt `tests/test_<kt>.py` → Exit 2 mit Meldung, kein Start;
    - **nur im Erstlauf** (ohne `--nacharbeit`): `tests_pruefen(kurztitel) != 0` → Exit 2 mit Meldung `Vorgabe-Tests nicht in Ordnung (kette.py tests-pruefen <kt>) – kein Lauf.`, kein Start. Die Ausgabe von `tests_pruefen` bleibt sichtbar. Bei Nacharbeit keine Prüfung auf „rot vorab“ (Tests sind dann teils grün).
  - In Prüfung (b) nach dem Lauf, wenn `vorgabe` und die Testdatei in den Änderungen dieses Laufs steht: eigener Befund `Vorgabe-Tests in diesem Lauf geändert: tests/test_<kt>.py (<art>) – nichts zurückgesetzt.` (→ Exit 1). Dieselbe Datei erscheint dann **nicht** zusätzlich unter „Schreibbereich verletzt“, auch wenn der Schreibbereich `tests/` nennt.
  - Ohne `## Vorgabe-Tests` bleibt alles wie bisher.
- **Stelle:** `def umsetzung_auto`
- **Akzeptanz:** T6–T8.

### A4: Prompt nennt die Vorgabe
- **Anforderung:** `_umsetzung_prompt` hängt bei einer Spec mit `## Vorgabe-Tests` **nach** den Pflichtzeilen und **vor** einem Nachbesserungs-Teil an: eine Leerzeile, `## Vorgabe-Tests`, eine Leerzeile und den Text
  `Abweichend von den Testregeln oben: Die Tests stehen schon in tests/test_<kt>.py. Du änderst diese Datei nicht – keine Zeile. Schreib nur den Code, bis python3 -m unittest -v tests/test_<kt>.py grün ist. Passt ein Test nicht zur Spec, nenne ihn im Handover unter „Abweichungen“.`
  Ohne den Abschnitt wird nichts angehängt.
- **Stelle:** `def _umsetzung_prompt`
- **Akzeptanz:** T6 (Text), T7 (Gegenfall), T8 (Nacharbeit).

### A5: Befehl `tests-pruefen`
- **Anforderung:** Subparser `tests-pruefen` mit `kurztitel` und `--timeout` (int, Vorgabe 300); `main` gibt den Rückgabewert von `tests_pruefen` zurück. Eine Zeile in der Befehlsliste des Moduldocstrings.
- **Stelle:** `def main`, Docstring am Dateianfang
- **Akzeptanz:** T1.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A2 | Testdatei fehlt | nichts | Exit 2, Meldung nennt `tests/test_<kt>.py` | T5 |
| A2 | Spec fehlt / ohne Test-ID | nichts | Exit 2 | T5 |
| A2 | Test-ID ohne Methode | nichts | `FEHLT`, Exit 1 | T2 |
| A2 | Test ohne Umsetzung schon grün | nichts | `NICHT ROT`, Exit 1 | T3 |
| A2 | Import auf Dateiebene scheitert | nichts | `LAEDT NICHT`, Exit 1, keine `rot`-Zeilen | T4 |
| A2 | Testskript hängt | nichts | `ZEIT`, Exit 1 | – (wie gegenprobe) |
| A3 | Erstlauf, Testprüfung scheitert | nichts geschrieben, opencode nicht gestartet | Exit 2 | T6 |
| A3 | Umsetzer ändert die Vorgabe-Tests | Lauf ist gelaufen, Protokollzeile | Befund, Exit 1, nichts zurückgesetzt | T7 |
| A3 | Nacharbeit mit teils grünen Tests | Handover, Nacharbeitsdatei offen | Lauf startet, keine Prüfung „rot vorab“ | T8 |
| A3 | Spec ohne `## Vorgabe-Tests` | – | Verhalten unverändert | T7 (Gegenfall) |
| A1–A5 | Absturz mitten im Lauf | n. a. (keine Außenwirkung) | – | – |

## Testplan

Die Tests stehen schon in `tests/test_vorgabe_tests.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Neue Funktionen werden in der Methode importiert. Jeder Test ist mit dem alten `kette.py` rot (geprüft: 8/8).

### T1: tests-pruefen – alle Vorgabe-Tests vorhanden und rot vorab
- **Prüft:** A2, A5
- **Aufbau:** Temp-Verzeichnis, Spec `k` mit T1, T2 und `## Vorgabe-Tests`; `tests/test_k.py` mit zwei Methoden, die eine nicht vorhandene Funktion in der Methode importieren. Aufruf `tests_pruefen("k")`, dann `kette.main(["tests-pruefen", "k"])`.
- **Erwartung:** Exit 0, `rot       T1`, `rot       T2`, `Keine Abweichung.`; `main` gibt 0 zurück.
- **Warum misst der Test das Richtige?** Ohne A2/A5 gibt es weder Funktion noch Befehl.
- **Gegenprobe:** alter `kette.py` → rot (Import scheitert).

### T2: tests-pruefen – Test-ID ohne Methode
- **Prüft:** A2, Fehlerpfad „Test-ID ohne Methode“
- **Aufbau:** wie T1, aber ohne Methode für T2.
- **Erwartung:** Exit 1, `FEHLT     T2`, `rot       T1`.
- **Warum misst der Test das Richtige?** Eine Prüfung, die nur rote Tests zählt, übersieht fehlende.
- **Gegenprobe:** alter `kette.py` → rot.

### T3: tests-pruefen – Test ohne Umsetzung schon grün
- **Prüft:** A2, Fehlerpfad „schon grün“
- **Aufbau:** wie T1, T1-Methode prüft nur `1 == 1`.
- **Erwartung:** Exit 1, `NICHT ROT T1`, `rot       T2`.
- **Warum misst der Test das Richtige?** Genau dieser Fall (Test prüft nichts Neues) soll vor der Umsetzung auffallen.
- **Gegenprobe:** alter `kette.py` → rot.

### T4: tests-pruefen – Testskript lädt nicht
- **Prüft:** A2, Fehlerpfad „Import auf Dateiebene“
- **Aufbau:** wie T1, zusätzlich Import der nicht vorhandenen Funktion am Dateianfang.
- **Erwartung:** Exit 1, `LAEDT NICHT`, keine Zeile `rot       T1`.
- **Warum misst der Test das Richtige?** Ein Ladefehler macht alle Tests „rot“, ohne dass einer etwas prüft – das darf nicht als bestanden gelten.
- **Gegenprobe:** alter `kette.py` → rot.

### T5: tests-pruefen – Testdatei oder Spec fehlt
- **Prüft:** A2, Fehlerpfade „Testdatei fehlt“, „Spec fehlt“
- **Aufbau:** erst ohne Testdatei, dann mit Testdatei, aber Spec gelöscht.
- **Erwartung:** beide Male Exit 2; erste Meldung nennt `tests/test_k.py`.
- **Warum misst der Test das Richtige?** Fehlende Voraussetzung muss Exit 2 sein, nicht „Abweichung“.
- **Gegenprobe:** alter `kette.py` → rot.

### T6: umsetzung-auto – Erstlauf startet nur mit bestandener Testprüfung
- **Prüft:** A1, A3, A4
- **Aufbau:** `Basis`; Spec `g` mit `## Vorgabe-Tests`, committete Testdatei mit einem grünen Test; Lauf. Danach Testdatei mit rotem Test (Import in der Methode) committen; Lauf.
- **Erwartung:** Erster Lauf Exit 2, opencode nicht gestartet, Ausgabe enthält `NICHT ROT T1`. Zweiter Lauf Exit 0, gestartet, Prompt enthält `## Vorgabe-Tests` und `Du änderst diese Datei nicht`.
- **Warum misst der Test das Richtige?** Ohne A3 startet auch der erste Lauf; ohne A4 fehlt der Text.
- **Gegenprobe:** alter `kette.py` → rot (erster Lauf startet).

### T7: umsetzung-auto – Änderung an Vorgabe-Tests ist ein Verstoß
- **Prüft:** A3, A4, Gegenfall „ohne Vorgabe-Tests“
- **Aufbau:** `Basis`; erst ohne `## Vorgabe-Tests` ein Lauf, in dem die Attrappe `tests/test_g.py` ändert; committen; dann Spec mit `## Vorgabe-Tests` (Schreibbereich nennt `tests/`) und rote Testdatei committen; Lauf, in dem die Attrappe `tests/test_g.py` ändert.
- **Erwartung:** Erster Lauf Exit 0, Ausgabe ohne `Vorgabe-Tests`, Prompt ohne `## Vorgabe-Tests`. Zweiter Lauf Exit 1, Ausgabe enthält `Vorgabe-Tests in diesem Lauf geändert: tests/test_g.py`, aber nicht `Schreibbereich verletzt`.
- **Warum misst der Test das Richtige?** Der Schreibbereich `tests/` würde die Änderung sonst erlauben; der Gegenfall zeigt, dass ohne Abschnitt nichts strenger wird.
- **Gegenprobe:** alter `kette.py` → rot (zweiter Lauf Exit 0).

### T8: umsetzung-auto – Nacharbeit prüft nicht auf rot vorab, Prompt nennt Vorgabe
- **Prüft:** A3 (Nacharbeit), A4
- **Aufbau:** `Basis`; Spec mit `## Vorgabe-Tests`, committete Testdatei mit grünem Test; Handover und Nacharbeitsdatei vorbereiten; Lauf mit `--nacharbeit`.
- **Erwartung:** gestartet, Exit 0, keine Zeile `NICHT ROT`, Prompt enthält `## Vorgabe-Tests`.
- **Warum misst der Test das Richtige?** Würde die Nacharbeit „rot vorab“ verlangen, könnte sie nie starten; ohne A4 fehlt der Hinweis im Nacharbeits-Prompt.
- **Gegenprobe:** alter `kette.py` → rot (Prompt ohne Abschnitt).

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
