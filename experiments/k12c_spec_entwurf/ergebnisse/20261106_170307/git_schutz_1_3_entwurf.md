# Spec: git_schutz

- **Datum:** 2026-11-01
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** `role-split/kette/kette.py`
- **Änderungsstellen:** 3

## Ziel

Schreibbereich und `umsetzung-auto` so erweitern, dass unbemerkte Änderungen an `.git/config`, `.git/hooks/` oder `.git/info/` vom Umsetzer verhindert und gemeldet werden.

## Nicht-Ziele

- Schutz der globalen Git-Konfiguration (`~/.gitconfig`).
- Automatisches Zurücksetzen von Änderungen (Hawe entscheidet).
- Schutz von `.git/index` oder anderen internen Git-Strukturen.
- Prüfung von `.gitattributes`, `.gitignore` (außer `.git/info/exclude`).

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_git_schutz.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** keine (reine Logik-Prüfung)

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py umsetzung-auto git_schutz` | T1 |
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py gegenprobe git_schutz` | T2 |

## Quellen

- `role-split/kette/kette.py` def _git – Git-Befehle ausführen
- `role-split/kette/kette.py` def _im_schreibbereich – Schreibbereich prüfen (hier muss neue Logik integriert werden)
- `role-split/kette/kette.py` def _schreibbereich – Schreibbereich parsen
- `role-split/kette/kette.py` def umsetzung_auto – Hauptfunktion für automatisierte Umsetzung (hier muss Prüfung integriert werden)
- `role-split/kette/kette.py` def gegenprobe – Gegenprobe durchführen (muss neue Prüfung abdecken)
- `role-split/kette/kette.py` def pruefen – Prüfung durchführen
- `tests/test_umsetzung_auto.py` Basis-Klasse für Tests mit Git-Repo-Setup
- `tests/test_vorgabe_tests.py` Struktur der Vorgabe-Tests

## Anforderungen

### A1: Schreibbereich schließt Git-Schutzdateien aus
- **Anforderung:** Der Schreibbereich darf `.git/config`, `.git/hooks/` und `.git/info/` nicht enthalten. Versucht der Umsetzer, eine dieser Dateien zu ändern, ist das ein Schreibbereichsverstoß.
- **Stelle:** `role-split/kette/kette.py` def _im_schreibbereich
- **Akzeptanz:** `_im_schreibbereich(".git/config", ["role-split/kette/"])` gibt `False` zurück.

### A2: Umsetzer prüft auf Änderungen an Git-Schutzdateien
- **Anforderung:** Vor Start von `opencode` prüft `umsetzung_auto`, ob `.git/config`, `.git/hooks/` oder `.git/info/` im Arbeitsstand vorhanden sind oder geändert wurden. Ist das der Fall, bricht der Lauf mit Exit 1 und einer Fehlermeldung auf stderr ab.
- **Stelle:** `role-split/kette/kette.py` def umsetzung_auto
- **Akzeptanz:** Exit 1, Meldung auf stderr enthält „.git/config“ oder „.git/hooks/“ oder „.git/info/“.

### A3: Meldung bei Schreibbereichsverstoß
- **Anforderung:** Wenn der Umsetzer (.git/config, .git/hooks/ oder .git/info/) ändert, wird dies als „Schreibbereich verletzt“ gemeldet. Die Meldung listet die betroffenen Dateien auf.
- **Stelle:** `role-split/kette/kette.py` def umsetzung_auto
- **Akzeptanz:** In der Ausgabe von `umsetzung_auto` steht „Schreibbereich verletzt“ und die jeweilige Datei.

### A4: Gegenprobe deckt neue Prüfung ab
- **Anforderung:** Die Gegenprobe muss sicherstellen, dass Tests für die neue Prüfung rot werden, wenn die Implementierung entfernt wird.
- **Stelle:** `role-split/kette/kette.py` def gegenprobe
- **Akzeptanz:** Bei Entfernung der neuen Prüflogik wird mindestens ein Test in der Gegenprobe rot.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | .git/config existiert | | `_im_schreibbereich` gibt False zurück | T3 |
| A1 | .git/hooks/ existiert | | `_im_schreibbereich` gibt False zurück | T3 |
| A1 | .git/info/ existiert | | `_im_schreibbereich` gibt False zurück | T3 |
| A1 | .git/hooks/test-hook (Datei in Ordner) | | `_im_schreibbereich` gibt False zurück | T3 |
| A2 | .git/config wurde geändert | | Exit 1, stderr enthält „.git/config“ | T4 |
| A2 | .git/hooks/ wurde geändert | | Exit 1, stderr enthält „.git/hooks/“ | T4 |
| A2 | .git/info/ wurde geändert | | Exit 1, stderr enthält „.git/info/“ | T4 |
| A2 | Keine Änderungen an Git-Dateien | | Lauf startet normal | T5 |
| A3 | Umsetzer ändert .git/config | | Meldung „Schreibbereich verletzt“ mit Datei | T6 |
| A3 | Umsetzer ändert .git/hooks/ | | Meldung „Schreibbereich verletzt“ mit Datei | T6 |
| A3 | Umsetzer ändert .git/info/ | | Meldung „Schreibbereich verletzt“ mit Datei | T6 |
| A4 | Neue Prüfung wird entfernt | | Mindestens ein Test wird rot | T7 |

## Testplan

Alle Tests werden als `tests/test_git_schutz.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.

### T1: Umsetzer startet bei sauberem Git-Status
- **Prüft:** A2
- **Aufbau:** Temp-Git-Repo, kein .git/config/hook/info geändert
- **Erwartung:** Exit 0, opencode wird aufgerufen
- **Warum misst der Test das Richtige?** Wenn die Prüfung nicht existiert, startet der Lauf auch bei veränderten Git-Dateien – das ist der Fehler.
- **Gegenprobe:** Keine (Test prüft Normalfall)

### T2: Gegenprobe deckt neue Prüfung ab
- **Prüft:** A4
- **Aufbau:** Temp-Git-Repo, neue Prüfung implementiert
- **Erwartung:** Gegenprobe läuft durch, mindestens ein Test wird rot, wenn Prüfung entfernt wird
- **Warum misst der Test das Richtige?** Wenn die Gegenprobe nicht rot wird, wurde die neue Prüfung nicht getestet.
- **Gegenprobe:** .git/config wird im alten Zustand geprüft

### T3: _im_schreibbereich blockiert Git-Dateien
- **Prüft:** A1
- **Aufbau:** Temp-Repo, _im_schreibbereich mit Schreibbereich ["role-split/kette/"]
- **Erwartung:** False für .git/config, .git/hooks/, .git/info/, .git/hooks/test-hook
- **Warum misst der Test das Richtige?** Wenn True zurückgegeben wird, könnte der Umsetzer die Datei ändern.
- **Gegenprobe:** .git/config wird im alten Zustand geprüft

### T4: Umsetzer bricht bei geänderter Git-Datei ab
- **Prüft:** A2
- **Aufbau:** Temp-Git-Repo, .git/config geändert, umsetzung_auto aufrufen
- **Erwartung:** Exit 1, stderr enthält „.git/config“
- **Warum misst der Test das Richtige?** Wenn Exit 0 zurückgegeben wird, wird die Änderung nicht gemeldet.
- **Gegenprobe:** .git/config wird im alten Zustand geprüft

### T5: Umsetzer startet bei keiner Git-Änderung
- **Prüft:** A2
- **Aufbau:** Temp-Git-Repo, keine Git-Dateien geändert, umsetzung_auto aufrufen
- **Erwartung:** Exit 0, opencode wird aufgerufen
- **Warum misst der Test das Richtige?** Wenn Exit 1 zurückgegeben wird, blockiert die Prüfung den Normalbetrieb.
- **Gegenprobe:** Keine (Test prüft Normalfall)

### T6: Umsetzer meldet Schreibbereichsverstoß
- **Prüft:** A3
- **Aufbau:** Temp-Git-Repo, .git/config geändert, umsetzung_auto aufrufen
- **Erwartung:** Ausgabe enthält „Schreibbereich verletzt“ und „.git/config“
- **Warum misst der Test das Richtige?** Wenn die Meldung fehlt, weiß Hawe nicht, was passiert ist.
- **Gegenprobe:** .git/config wird im alten Zustand geprüft

### T7: Neue Prüfung wird in Gegenprobe rot
- **Prüft:** A4
- **Aufbau:** Temp-Git-Repo, neue Prüfung implementiert, dann Prüfung entfernen
- **Erwartung:** Mindestens ein Test wird rot
- **Warum misst der Test das Richtige?** Wenn kein Test rot wird, wurde die neue Prüfung nicht getestet.
- **Gegenprobe:** .git/config wird im alten Zustand geprüft

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
