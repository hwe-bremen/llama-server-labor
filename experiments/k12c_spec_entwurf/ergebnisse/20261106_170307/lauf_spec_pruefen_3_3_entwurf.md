# Spec: lauf_spec_pruefen

- **Datum:** 2026-11-06
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** `role-split/kette/kette.py`
- **Änderungsstellen:** 3

## Ziel

`kette.py spec-pruefen` soll das bestehende Tool `spec_pruefen.py` nutzen, um die Spec mechanisch zu prüfen. Bisher wird nur `groesse` aufgerufen. Bei Fehlern (Exit 1) soll `spec-pruefen` die Befunde sammeln und am Ende zusammenfassen, nicht sofort abbrechen. Die Größenprüfung bleibt als Hinweis erhalten, aber kein Sonderweg mehr für alte Specs.

## Nicht-Ziele

- Änderungen an `spec_pruefen.py` selbst (außer ggf. API, falls nötig, aber hier nur Aufruf anpassen).
- Änderungen an der Logik von `spec_pruefen.py`.
- Änderungen an anderen `kette.py`-Befehlen.

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

Mit diesem Abschnitt ist `tests/test_lauf_spec_pruefen.py` Vorgabe: Sie wird mit der Spec committet, vor dem Erstlauf von `kette.py tests-pruefen <kurztitel>` geprüft (je Test-ID eine Methode, Skript lädt, jeder Test rot vorab) und darf von der Umsetzung nicht geändert werden. Tests für bestehendes Verhalten tragen `(Bestand)` im Titel und müssen vorab grün sein (R49).

- `tests/test_lauf_spec_pruefen.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** keine (reine Logik-Änderung)

## Einstiegspunkte

Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
`runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py spec-pruefen <kurztitel>` | T1 |

## Quellen

Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo –
**nichts aus dem Gedächtnis**. Eine Zeile je Quelle, Pfad in Backticks, dann `Zeilen a–b` oder `def Name` / `class Name`
(ohne Angabe: ganze Datei, max. 400 Zeilen), dann Zweck. `kette.py quellen <kurztitel>` holt die Auszüge danach
maschinell und wörtlich nach `quellen_<JJJJMMTT>_<kurztitel>.md`. Was nicht im Repo steht (externe Doku, Format
eines Fremdprogramms), kommt unter „Offene Fragen" – Hawe legt die Quelle dann als Datei ins Repo.

- `role-split/kette/kette.py` def spec_pruefen – Aufrufmechanismus für den Befehl
- `role-split/kette/kette.py` def abgleich – Vergleichslogik (als Referenz für Konsistenz)
- `role-split/kette/spec_pruefen.py` def pruefe – wie Befunde gesammelt werden
- `role-split/kette/spec_pruefen.py` PFLICHT – welche Abschnitte zwingend sind

## Anforderungen

### A1: Nutzung von spec_pruefen.py
- **Anforderung:** `kette.py spec-pruefen` ruft `spec_pruefen.pruefe(spec_text)` auf und wertet die Rückgabe aus.
- **Stelle:** `role-split/kette/kette.py` def spec_pruefen
- **Akzeptanz:** Der Befehl gibt Befunde und Hinweise aus, die aus `spec_pruefen.py` stammen.

### A2: Sammlung aller Befunde
- **Anforderung:** `spec-pruefen` sammelt alle Befunde aus `spec_pruefen.py` und gibt sie am Ende zusammengefasst aus. Es bricht nicht bei der ersten Abweichung ab.
- **Stelle:** `role-split/kette/kette.py` def spec_pruefen
- **Akzeptanz:** Exit-Code ist 1, wenn mindestens ein Befund vorliegt, aber alle Befunde werden ausgegeben.

### A3: Größenprüfung als Hinweis
- **Anforderung:** Die Größenprüfung (`groesse`) wird weiterhin aufgerufen, aber als Hinweis ausgegeben, nicht als Fehler, der den Befehl mit Exit 1 beendet (es sei denn, es gibt andere Fehler).
- **Stelle:** `role-split/kette/kette.py` def spec_pruefen
- **Akzeptanz:** Die Ausgabe enthält einen Hinweis zur Größe, aber der Exit-Code wird nur durch Befunde aus `spec_pruefen.py` bestimmt.

## Fehlerpfade

Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | `spec_pruefen.py` existiert nicht | | Exit 2, Fehlermeldung | T1 |
| A1 | `spec_pruefen.py` hat keine `pruefe`-Funktion | | Exit 2, Fehlermeldung | T1 |
| A2 | Spec hat mehrere Fehler | | Exit 1, alle Fehler ausgegeben | T2 |
| A2 | Spec hat keine Fehler | | Exit 0, keine Fehler | T2 |
| A3 | Spec ist zu groß | | Exit 0 (wenn keine anderen Fehler), Hinweis auf Größe | T3 |

## Testplan

Alle Tests werden als `tests/test_lauf_spec_pruefen.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.

### T1: Prüfung mit defekten Quellen
- **Prüft:** A1
- **Aufbau:** Temporäre Spec-Datei, die auf eine nicht existierende `spec_pruefen.py` verweist (oder die Funktion fehlt).
- **Erwartung:** Exit-Code 2, Fehlermeldung, dass `spec_pruefen.py` defekt ist.
- **Warum misst der Test das Richtige?** Wenn A1 nicht erfüllt ist, wird die Funktion nicht aufgerufen oder falsch behandelt.
- **Gegenprobe:** Keine (Test prüft Bestehendes, da `spec_pruefen.py` immer existiert)

### T2: Sammlung aller Befunde
- **Prüft:** A2
- **Aufbau:** Temporäre Spec-Datei mit mehreren Fehlern (z. B. Platzhalter, offene Fragen).
- **Erwartung:** Exit-Code 1, alle Fehler in der Ausgabe.
- **Warum misst der Test das Richtige?** Wenn A2 nicht erfüllt ist, werden nur einige Fehler ausgegeben oder der Befehl bricht ab.
- **Gegenprobe:** Keine (Test prüft Bestehendes, da die Logik vor der Änderung alle Fehler sammelt)

### T3: Größenprüfung als Hinweis
- **Prüft:** A3
- **Aufbau:** Temporäre Spec-Datei, die groß ist (über der Grenze).
- **Erwartung:** Exit-Code 0 (wenn keine anderen Fehler), Hinweis auf Größe in der Ausgabe.
- **Warum misst der Test das Richtige?** Wenn A3 nicht erfüllt ist, wird die Größe als Fehler gewertet oder ignoriert.
- **Gegenprobe:** Keine (Test prüft Bestehendes, da die Größenprüfung bereits als Hinweis existiert)

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
