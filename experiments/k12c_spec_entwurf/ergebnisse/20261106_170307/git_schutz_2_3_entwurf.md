# Spec: git_schutz

- **Datum:** 2026-11-01
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** `role-split/kette/kette.py`
- **Änderungsstellen:** 4

## Ziel

Prüfen, ob `.git/config`, `.git/hooks/` oder `.git/info/` während eines `kette.py`-Laufs verändert wurden. Bei Abweichung das Tool mit Exit 1 beenden und die Differenz melden.

## Nicht-Ziele

- Schutz von `.git/HEAD`, `.git/index` oder anderen Unterverzeichnissen von `.git/`.
- Schutz der globalen Git-Konfiguration (`~/.gitconfig`).
- Automatisches Zurücksetzen oder Abbrechen der Kette (nur Meldung).

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_git_schutz.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** Tests prüfen nur die Dateiinhalte im Dateisystem; es werden keine echten Git-Operationen durchgeführt, die das Repo ändern.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | Import als Modul, Aufruf von `git_schutz_pruefen` | T1, T2, T3, T4 |

## Quellen

- `role-split/kette/kette.py` Zeilen 1–50 – Struktur der Datei, Importe
- `role-split/kette/kette.py` def _git – wie Git-Befehle aktuell ausgeführt werden (Referenz für Exit-Code-Handling)
- `role-split/kette/kette.py` def gegenprobe – Prinzip der Gegenprobe (wichtig für T3, T4)
- `role-split/kette/kette.py` def pruefen – Einbettung der neuen Prüfung in den bestehenden Ablauf

## Anforderungen

### A1: Schutz von .git/config
- **Anforderung:** Vor und nach dem Hauptlauf wird der Inhalt von `.git/config` geprüft. Weicht er ab, wird die Differenz ausgegeben und das Tool mit Exit 1 beendet.
- **Stelle:** `role-split/kette/kette.py` def pruefen
- **Akzeptanz:** Exit 1 bei Änderung, Ausgabe der Differenz, Kette stoppt.

### A2: Schutz von .git/hooks/
- **Anforderung:** Vor und nach dem Hauptlauf wird geprüft, ob Dateien im Verzeichnis `.git/hooks/` hinzugekommen, entfernt oder geändert wurden. Bei Abweichung wird die Differenz ausgegeben und das Tool mit Exit 1 beendet.
- **Stelle:** `role-split/kette/kette.py` def pruefen
- **Akzeptanz:** Exit 1 bei Änderung, Ausgabe der Differenz, Kette stoppt.

### A3: Schutz von .git/info/
- **Anforderung:** Vor und nach dem Hauptlauf wird geprüft, ob Dateien im Verzeichnis `.git/info/` (z. B. `exclude`) hinzugekommen, entfernt oder geändert wurden. Bei Abweichung wird die Differenz ausgegeben und das Tool mit Exit 1 beendet.
- **Stelle:** `role-split/kette/kette.py` def pruefen
- **Akzeptanz:** Exit 1 bei Änderung, Ausgabe der Differenz, Kette stoppt.

### A4: Fehlerbehandlung bei fehlendem Verzeichnis
- **Anforderung:** Wenn `.git/config` oder die Verzeichnisse `.git/hooks/` oder `.git/info/` nicht existieren, wird dies ignoriert (kein Fehler, kein Exit 1).
- **Stelle:** `role-split/kette/kette.py` def _git_schutz_pruefen (neu)
- **Akzeptanz:** Exit 0 bei Nichtvorhandensein, keine Meldung.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | .git/config wird geändert (z. B. user.name) | Inhalt vor Lauf wird gemerkt | Exit 1, Ausgabe der git diff, Kette stoppt | T1 |
| A1 | .git/config existiert nicht | Nichts markiert | Exit 0, keine Meldung | T4 |
| A2 | .git/hooks/ wird geändert (neue Hook) | Inhalt vor Lauf wird gemerkt | Exit 1, Ausgabe der git diff, Kette stoppt | T2 |
| A2 | .git/hooks/ existiert nicht | Nichts markiert | Exit 0, keine Meldung | T4 |
| A3 | .git/info/ wird geändert | Inhalt vor Lauf wird gemerkt | Exit 1, Ausgabe der git diff, Kette stoppt | T3 |
| A3 | .git/info/ existiert nicht | Nichts markiert | Exit 0, keine Meldung | T4 |

## Testplan

Alle Tests werden als `tests/test_git_schutz.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung. Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.

### T1: Schutz von .git/config bei Änderung
- **Prüft:** A1
- **Aufbau:** Temporäres Git-Repo erstellen, `.git/config` vor und nach der Prüfung lesen, zwischenzeitlich modifizieren.
- **Erwartung:** Exit 1, Meldung enthält die geänderte Zeile.
- **Warum misst der Test das Richtige?** Der Test simuliert die exakte Situation, die in der Aufgabe beschrieben ist (35B setzt user.name). Ohne Schutz würde der Test grün sein.
- **Gegenprobe:** `role-split/kette/kette.py` muss die neue Funktion `_git_schutz_pruefen` aufrufen und den Exit-Code prüfen.

### T2: Schutz von .git/hooks/ bei Änderung
- **Prüft:** A2
- **Aufbau:** Temporäres Git-Repo erstellen, `.git/hooks/` vor und nach der Prüfung lesen, zwischenzeitlich eine neue Hook-Datei erstellen.
- **Erwartung:** Exit 1, Meldung enthält die neue Datei.
- **Warum misst der Test das Richtige?** Der Test prüft, ob neue Hook-Dateien erkannt werden, die z. B. automatische Tests auslösen könnten.
- **Gegenprobe:** `role-split/kette/kette.py` muss die neue Funktion `_git_schutz_pruefen` aufrufen und den Exit-Code prüfen.

### T3: Schutz von .git/info/ bei Änderung
- **Prüft:** A3
- **Aufbau:** Temporäres Git-Repo erstellen, `.git/info/` vor und nach der Prüfung lesen, zwischenzeitlich `exclude` ändern.
- **Erwartung:** Exit 1, Meldung enthält die geänderte Zeile.
- **Warum misst der Test das Richtige?** Der Test prüft, ob Änderungen an `info/exclude` erkannt werden, die `git status` verstecken.
- **Gegenprobe:** `role-split/kette/kette.py` muss die neue Funktion `_git_schutz_pruefen` aufrufen und den Exit-Code prüfen.

### T4: Fehlende Verzeichnisse werden ignoriert
- **Prüft:** A4
- **Aufbau:** Temporäres Verzeichnis ohne `.git/` erstellen, Prüfung durchführen.
- **Erwartung:** Exit 0, keine Meldung.
- **Warum misst der Test das Richtige?** Der Test prüft, dass das Tool robust ist und nicht abstürzt, wenn kein Git-Repo vorliegt.
- **Gegenprobe:** Keine (Bestehendes wird nicht geprüft, da die Funktion neu ist).

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
