# Spec: git_schutz

- **Datum:** 2026-11-01
- **Modell:** lokales Modell (Messung K12c)
- **Betroffene Dateien:** `mcp-server/kette_werkzeuge.py`, `role-split/kette/kette.py`
- **Änderungsstellen:** 3

## Ziel

Die Kette verhindert, dass der Umsetzer-Agent unbemerkt `.git/config` oder `.git/hooks/` ändert. Bei direkten Schreibversuchen durch den Agenten wird der Zugriff blockiert und der Lauf sofort mit Exit-Code 1 beendet.

## Nicht-Ziele

- Schutz der globalen Git-Konfiguration (`~/.gitconfig`).
- Schutz des gesamten `.git`-Verzeichnisses (zu groß, ändert sich bei jedem Commit).
- Automatisches Zurücksetzen von Änderungen; Meldung reicht.
- Prüfung, ob externe Tools (z. B. `git`-CLI) die Dateien ändern.

## Schreibbereich

- `mcp-server/kette_werkzeuge.py`
- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_git_schutz.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** nichts
- **Technische Sperre für Tests:** Die Tests simulieren den Zugriff über die MCP-Werkzeuge (`replace_in_file` etc.). Es werden keine echten Git-Dateien im Repo geschrieben; der Test prüft, ob das Werkzeug den Schreibvorgang abfängt und einen Fehler wirft, bevor die Datei auf der Platte geändert wird.

## Einstiegspunkte

- `mcp-server/kette_werkzeuge.py` wird von `mcp-server/lab_mcp_server.py` als Werkzeug-Modul importiert und bereitgestellt.
- `role-split/kette/kette.py` enthält die Prüflogik für Handover und Paket, wird von `kette.py` selbst oder `tests/test_*.py` aufgerufen.

| Datei | Wie gestartet | Test |
|---|---|---|
| `mcp-server/kette_werkzeuge.py` | Import als Modul `import mcp_server.kette_werkzeuge` | T1, T2 |
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py paket git_schutz` | T3 |

## Quellen

Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo – **nichts aus dem Gedächtnis**.

- `mcp-server/kette_werkzeuge.py` `def replace_in_file` – Das Werkzeug, das Dateien ändert; muss um die Schutzlogik erweitert werden.
- `mcp-server/kette_werkzeuge.py` `def read_file_bereich` – Liest Dateien; darf unverändert bleiben, aber Zugriff auf geschützte Pfade prüfen.
- `role-split/kette/kette.py` `def _git` – Hilfsfunktion für Git-Befehle; Referenz für Pfadbehandlung.
- `role-split/kette/kette.py` `def gegenprobe` – Prüft, ob Tests den neuen Schutzmechanismus detektieren.

## Anforderungen

### A1: Blockade von `.git/config`
- **Anforderung:** Das Werkzeug `replace_in_file` (und alle anderen Schreibwerkzeuge in `kette_werkzeuge.py`) prüft den Zielpfad. Wenn der Pfad `.git/config` lautet, wird kein Schreibvorgang ausgeführt, sondern ein `ValueError` mit der Meldung ``git_schutz`: Zugriff auf .git/config blockiert` geworfen.
- **Stelle:** `mcp-server/kette_werkzeuge.py`, Funktion `replace_in_file` (und ggf. andere Schreibfunktionen analog).
- **Akzeptanz:** Aufruf des Werkzeugs mit Ziel `.git/config` führt zu einem abgebrochenen Aufruf und der genannten Fehlermeldung.

### A2: Blockade von `.git/hooks/`
- **Anforderung:** Das Werkzeug prüft den Zielpfad. Wenn der Pfad unter `.git/hooks/` beginnt (z. B. `.git/hooks/pre-commit`), wird kein Schreibvorgang ausgeführt, sondern ein `ValueError` mit der Meldung ``git_schutz`: Zugriff auf .git/hooks blockiert` geworfen.
- **Stelle:** `mcp-server/kette_werkzeuge.py`, Funktion `replace_in_file` (und ggf. andere Schreibfunktionen analog).
- **Akzeptanz:** Aufruf des Werkzeugs mit Ziel `.git/hooks/irgendwas` führt zu einem abgebrochenen Aufruf und der genannten Fehlermeldung.

### A3: Schutz der `.git/info/`-Verzeichnisse
- **Anforderung:** Das Werkzeug prüft den Zielpfad. Wenn der Pfad unter `.git/info/` beginnt (z. B. `.git/info/exclude`), wird kein Schreibvorgang ausgeführt, sondern ein `ValueError` mit der Meldung ``git_schutz`: Zugriff auf .git/info blockiert` geworfen.
- **Stelle:** `mcp-server/kette_werkzeuge.py`, Funktion `replace_in_file` (und ggf. andere Schreibfunktionen analog).
- **Akzeptanz:** Aufruf des Werkzeugs mit Ziel `.git/info/irgendwas` führt zu einem abgebrochenen Aufruf und der genannten Fehlermeldung.

### A4: Prüfung im Review-Paket
- **Anforderung:** Die Funktion `paket` in `role-split/kette/kette.py` erkennt geänderte Dateien unter `.git/`. Wenn `.git/config` oder `.git/hooks/` oder `.git/info/` geändert wurden, wird dies im Review-Paket unter „Geänderte Code-Dateien“ explizit als Fehler markiert und das Paket mit Exit-Code 1 abgelehnt.
- **Stelle:** `role-split/kette/kette.py`, Funktion `paket` (bzw. `_diff`/`_aenderungen`, je nach Implementierung der Prüfung).
- **Akzeptanz:** Ein Review-Paket, das Änderungen an geschützten Git-Pfaden enthält, wird nicht erstellt (Exit 1) und gibt eine klare Fehlermeldung aus.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Pfad ist `.git/config` | | `ValueError`: `git_schutz`: Zugriff auf .git/config blockiert | T1 |
| A1 | Pfad ist `.git/config.bak` | | Schreibvorgang erlaubt (nicht geschützt) | T1 |
| A2 | Pfad ist `.git/hooks/pre-commit` | | `ValueError`: `git_schutz`: Zugriff auf .git/hooks blockiert | T2 |
| A2 | Pfad ist `.git/hooks/pre-commit.bak` | | `ValueError`: `git_schutz`: Zugriff auf .git/hooks blockiert | T2 |
| A3 | Pfad ist `.git/info/exclude` | | `ValueError`: `git_schutz`: Zugriff auf .git/info blockiert | T3 |
| A3 | Pfad ist `.git/info/` (Verzeichnis) | | Schreibvorgang nicht möglich, aber Prüfung muss auch Verzeichniszugriffe abfangen oder ignoriert, da nur Dateien geschrieben werden | T3 |
| A4 | `.git/config` wurde geändert | | Paket-Erstellung scheitert mit Exit 1 und Meldung über geschützten Pfad | T4 |
| A4 | `.git/hooks/` wurde geändert | | Paket-Erstellung scheitert mit Exit 1 und Meldung über geschützten Pfad | T4 |

## Testplan

Alle Tests werden als `tests/test_git_schutz.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.

### T1: Blockade von `.git/config`
- **Prüft:** A1
- **Aufbau:** Importiert `replace_in_file` aus `mcp_server.kette_werkzeuge`. Ruft das Werkzeug mit `datei=".git/config"` auf.
- **Erwartung:** `ValueError` mit der Meldung `git_schutz`: Zugriff auf .git/config blockiert`.
- **Warum misst der Test das Richtige?** Wenn die Prüfung fehlt, würde das Werkzeug versuchen, `.git/config` zu lesen/schreiben (oder erfolgreich sein), was den Schutz umgeht.
- **Gegenprobe:** Keine (Schutzlogik ist neu).

### T2: Blockade von `.git/hooks/`
- **Prüft:** A2
- **Aufbau:** Importiert `replace_in_file`. Ruft das Werkzeug mit `datei=".git/hooks/pre-commit"` auf.
- **Erwartung:** `ValueError` mit der Meldung `git_schutz`: Zugriff auf .git/hooks blockiert`.
- **Warum misst der Test das Richtige?** Ohne die Prüfung für `.git/hooks/` würde der Schreibvorgang durchgehen.
- **Gegenprobe:** Keine.

### T3: Blockade von `.git/info/`
- **Prüft:** A3
- **Aufbau:** Importiert `replace_in_file`. Ruft das Werkzeug mit `datei=".git/info/exclude"` auf.
- **Erwartung:** `ValueError` mit der Meldung `git_schutz`: Zugriff auf .git/info blockiert`.
- **Warum misst der Test das Richtige?** Ohne die Prüfung für `.git/info/` würde der Schreibvorgang durchgehen.
- **Gegenprobe:** Keine.

### T4: Review-Paket lehnt Änderungen an geschützten Pfaden ab
- **Prüft:** A4
- **Aufbau:** Simuliert ein Git-Repo mit einer geänderten `.git/config`-Datei (oder prüft die Logik von `paket`/`_diff` direkt, indem geprüft wird, ob die Funktion geschützte Pfade erkennt). Da `paket` Git-Status auswertet, wird getestet, ob die Funktion `paket` (oder die zugrundeliegende `_diff`-Logik) bei Änderungen in `.git/config` einen Fehler zurückgibt.
- **Erwartung:** Die Funktion `paket` (oder `_diff`) erkennt die Änderung und gibt Exit-Code 1 oder eine Fehlermeldung zurück.
- **Warum misst der Test das Richtige?** Wenn `paket` Änderungen an `.git/` ignoriert, wird der Fehler im Review nicht erkannt.
- **Gegenprobe:** Keine.

## Offene Fragen

- Keine
