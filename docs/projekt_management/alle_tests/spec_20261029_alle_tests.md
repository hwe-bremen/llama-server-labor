# Spec: alle_tests

- **Datum:** 2026-10-29
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette_lauf` aus der Chat-UI
- **Betroffene Dateien:** neu `scripts/alle_tests.py`

## Ziel

Ein Skript, das **alle Testdateien des Repos richtig aufruft** und nach Exit-Code bewertet (R50: nach jedem Lauf alle Testdateien). Anlass 28.10.: Von Hand aufgerufen, scheiterte `role-split/test_role_proxy.py` am Suchpfad, `mcp-server/test_tool_log.py` (Skript, braucht den Server-Pfad) endete in einer Rekursion, und `tail -1` zeigte bei mehreren Dateien Druckausgaben statt des Ergebnisses. Zugleich die erste Kette, die komplett aus der Chat-UI läuft (Stufe 4).

## Nicht-Ziele

- **`tests/test_alle_tests.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Änderung an bestehenden Testdateien, auch nicht an roten (Altlast `tests/test_scout_kw_doppelversand.py` bleibt rot – das Skript soll das zeigen).
- Keine Einbindung in `kette.py`, `automatik.py` oder die MCP-Werkzeuge (eigener späterer Schritt).
- Kein paralleles Ausführen, keine Filteroption, keine farbige Ausgabe. Nur Standardbibliothek.

## Schreibbereich

- `scripts/alle_tests.py`

## Vorgabe-Tests

- `tests/test_alle_tests.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Das Skript selbst nichts. Es startet die vorhandenen Testdateien; deren Außenwirkung ist ihre eigene (alle liefen am 28.10. ohne Außenwirkung: Mail-/Scout-Tests nutzen Temp-Ordner und Trockenlauf).
- **Technische Sperre für Tests:** T1–T7 biegen `alle_tests.ROOT` auf ein `tempfile.TemporaryDirectory()` mit kleinen Ersatz-Testdateien um. T8 ruft das echte Skript nur mit `--liste` auf – das führt keine Testdatei aus (T7 prüft das). Kein Vorgabe-Test startet den vollen Lauf am echten Repo (er enthielte sich selbst).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `scripts/alle_tests.py` | `python3 scripts/alle_tests.py [--liste] [--timeout N]` (Befehlszeile, auch aus anderem Arbeitsordner) | T8 |
| `scripts/alle_tests.py` | als Modul (`finden`, `art`, `interpreter`, `aufruf`, `main`) | T1–T7 |

## Quellen

- `role-split/test_role_proxy.py` Zeilen 1–20 – importiert das Nachbarmodul `role_proxy` (Suchpfad = Ordner der Datei)
- `mcp-server/test_tool_log.py` Zeilen 1–30 – Skript-Test, erwartet den Server-Pfad als erstes Argument
- `mcp-server/test_append_file.py` Zeilen 1–15 – importiert das Nachbarmodul `test_search_files`
- `scripts/test_mcp_deny.py` Zeilen 1–20 – Skript-Test, läuft aus dem Repo-Root (`Path("mcp-server/...")`)
- `role-split/kette/kette.py` def tests_laufen – so startet die Kette heute Tests (nur zur Orientierung, nicht ändern)

## Anforderungen

### A1: Testdateien finden
- **Anforderung:** Konstanten `ROOT = Path(__file__).resolve().parent.parent` (Repo-Root; `scripts/` liegt direkt darunter), `FUNDORTE = ("tests", "role-split", "mcp-server", "scripts")`, `AUSGESCHLOSSEN = {".venv", "venv", "__pycache__", "testdata"}`, `TIMEOUT = 300`, `SCHWANZ = 20`, `SONDERAUFRUFE = {"mcp-server/test_tool_log.py": ["mcp-server/lab_mcp_server.py"]}`. Alle Konstanten werden **zur Aufrufzeit** gelesen (Tests biegen `ROOT` um). `finden() -> list[str]`: alle Dateien `test_*.py` rekursiv unter `ROOT/<Fundort>` (fehlende Fundorte überspringen), deren Ordnerteile keinen Namen aus `AUSGESCHLOSSEN` enthalten (auf **jeder** Ebene); Rückgabe relative POSIX-Pfade zu `ROOT`, sortiert, ohne Doppelte.
- **Stelle:** `scripts/alle_tests.py`
- **Akzeptanz:** T1, T8.

### A2: Art und Aufruf
- **Anforderung:** `art(rel) -> "unittest" | "skript"`: `unittest`, wenn eine Zeile mit `import unittest` oder `from unittest` beginnt (führende Leerzeichen erlaubt, Regex mit `re.M`), sonst `skript`. `aufruf(rel) -> (argv, env)`: unittest → `[python, "-m", "unittest", rel]`; Skript → `[python, rel, *SONDERAUFRUFE.get(rel, [])]`. `env` = Kopie von `os.environ`, `PYTHONPATH` = absoluter Ordner der Testdatei, bei vorhandenem `PYTHONPATH` gefolgt von `os.pathsep` und dem alten Wert.
- **Stelle:** `art`, `aufruf`
- **Akzeptanz:** T2, T4.

### A3: Interpreter
- **Anforderung:** `interpreter(rel) -> str`: vom Ordner der Testdatei aufwärts bis einschließlich `ROOT` das erste existierende `<ordner>/.venv/bin/python` (als String, nicht aufgelöst); keins → `sys.executable`.
- **Stelle:** `interpreter`
- **Akzeptanz:** T3.

### A4: Lauf und Ausgabe
- **Anforderung:** `main(argv=None) -> int` mit argparse: `--liste` (Schalter), `--timeout` (int, Standard `TIMEOUT`; `< 1` → `ap.error`, also Exit 2).
  1. Keine Testdateien → `Keine Testdateien gefunden.`, Exit 2 (auch mit `--liste`).
  2. Lauf: Kopfzeile `Testdateien: <n> (Zeitlimit <t> s je Datei)`. Je Datei nacheinander `subprocess.run(argv, cwd=ROOT, env=env, stdin=DEVNULL, capture_output, text, errors="replace", timeout=t)` und sofort eine Zeile: Exit 0 → `  ok    <rel>  (<s mit 1 Nachkommastelle> s)`; sonst `  ROT   <rel>  Exit <code>  (<s> s)`; Zeitlimit → `  ZEIT  <rel>  nach <t> s abgebrochen`. **Bewertet wird nur der Exit-Code.**
  3. Danach für jede ROT-/ZEIT-Datei in Lauf-Reihenfolge: Leerzeile, `--- <rel> – letzte <k> Zeilen ---` und die letzten `SCHWANZ` Zeilen von stdout+stderr (rechts gestrippt; `k` = Anzahl gezeigter Zeilen).
  4. Schluss: Leerzeile, `<n> Datei(en): <ok> ok, <rot> rot, <zeit> Zeit.` Exit 0 nur, wenn `rot` und `zeit` 0 sind, sonst 1.
- **Stelle:** `main`, `laufen`
- **Akzeptanz:** T4, T5, T6, T7.

### A5: `--liste`
- **Anforderung:** Führt **nichts** aus. Kopfzeile `Testdateien: <n>`, dann je Datei `  <art linksbündig 8> <rel>  [<interpreter>]` und bei Skripten mit Sonderargumenten ein Leerzeichen plus die Argumente. `<interpreter>` als Pfad relativ zu `ROOT`, wenn er darin liegt, sonst `python`. Exit 0.
- **Stelle:** `liste`
- **Akzeptanz:** T7, T8.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | `test_*.py` in `.venv`, `venv`, `__pycache__`, `testdata` (auch tiefer) oder außerhalb der Fundorte | – | nicht gefunden | T1 |
| A1 | Fundort fehlt | – | übersprungen | T1 (Temp ohne `agents/`-Fundort), T7 |
| A2 | Test importiert Nachbarmodul, Ordnername mit Bindestrich | – | grün dank `PYTHONPATH` | T4 |
| A2 | Skript-Test braucht Argument (`test_tool_log.py`) | – | Sonderargument wird angehängt | T2, T4 |
| A2 | `PYTHONPATH` schon gesetzt | – | Ordner vorn, Rest bleibt | T2 |
| A3 | `.venv` im Ordner und im Root | – | nächstes gewinnt | T3 |
| A4 | Test druckt „OK“, endet aber rot | – | `ROT` (Exit-Code zählt) | T5 |
| A4 | Testdatei hängt | – | `ZEIT`, Rest läuft weiter, Exit 1 | T6 |
| A4 | `--timeout 0` | nichts | Exit 2 | T6 |
| A4 | keine Testdateien | nichts | Exit 2 | T7 |
| A5 | `--liste` | – | keine Datei ausgeführt | T7 |
| A1 | Aufruf aus anderem Arbeitsordner | – | `ROOT` aus `__file__`, nicht aus cwd | T8 |
| A4 | Testdatei startet selbst Kindprozesse, die das Zeitlimit überleben | – | direkter Kindprozess wird beendet; Enkel evtl. nicht | – (bewusst offen) |

## Testplan

Die Tests stehen in `tests/test_alle_tests.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Vorab 8/8 rot (Modul fehlt); gegen die Referenz 8/8 grün, dreimal stabil (~2 s). Mutationsprüfung der Referenz: 21 von 21 gefangen.

### T1: finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert
- **Prüft:** A1
- **Aufbau:** Temp-Repo mit Treffern in allen vier Fundorten, Nicht-Treffern (`hilfe.py`, `x_test.py`, `tmp/`, `agents/`) und ausgeschlossenen Ordnern auf verschiedenen Ebenen.
- **Erwartung:** genau die sechs Treffer, sortiert; `FUNDORTE` wie spezifiziert.
- **Warum misst der Test das Richtige?** Eine `test_*.py` in `testdata/` oder `.venv` würde fremden Code als Test starten.
- **Gegenprobe:** alter Stand → rot (Modul fehlt).

### T2: art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad
- **Prüft:** A2
- **Aufbau:** `import unittest`, nur `from unittest import TestCase`, Skript, `mcp-server/test_tool_log.py`; `PYTHONPATH` vorher gesetzt.
- **Erwartung:** Arten und argv wie spezifiziert; `PYTHONPATH` beginnt mit dem Ordner der Datei, alter Wert hängt hinten an.
- **Warum misst der Test das Richtige?** Genau diese beiden Aufrufe sind am 28.10. von Hand schiefgegangen.
- **Gegenprobe:** alter Stand → rot.

### T3: interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable
- **Prüft:** A3
- **Aufbau:** ohne `.venv`; dann `.venv` in `mcp-server/` und im Root (Symlink auf `sys.executable`).
- **Erwartung:** `sys.executable`; danach `mcp-server/.venv/bin/python` für `mcp-server/`, Root-`.venv` für die übrigen.
- **Warum misst der Test das Richtige?** Die MCP-Tests brauchen das `mcp`-Paket aus ihrem venv.
- **Gegenprobe:** alter Stand → rot.

### T4: Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0
- **Prüft:** A2, A4.2, A4.4
- **Aufbau:** `role-split/test_n.py` importiert `role-split/nachbar.py`; Skript-Test prüft sein Argument; normaler unittest.
- **Erwartung:** Kopfzeile mit 300 s, drei `ok`-Zeilen, `3 Datei(en): 3 ok, 0 rot, 0 Zeit.`, kein Ausgabeblock, Exit 0.
- **Warum misst der Test das Richtige?** Bildet den `test_role_proxy`-Fall vom 28.10. nach.
- **Gegenprobe:** alter Stand → rot.

### T5: Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende
- **Prüft:** A4.2–A4.4
- **Aufbau:** unittest, der „OK“ druckt und scheitert; Skript mit Exit 3; grüner Test; danach Skript mit 50 Zeilen.
- **Erwartung:** zwei `ROT`-Zeilen mit Exit-Code, ein `ok`, Ausgabeblöcke mit Inhalt, Schlusszeile `1 ok, 2 rot`, Exit 1; bei 50 Zeilen genau `z30`–`z49`.
- **Warum misst der Test das Richtige?** `tail -1` hat am 28.10. rote Dateien verdeckt.
- **Gegenprobe:** alter Stand → rot.

### T6: Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter
- **Prüft:** A4.2, A4.4, `--timeout`
- **Aufbau:** Datei schläft 30 s; `--timeout 1`; danach `--timeout 0`.
- **Erwartung:** Dauer < 15 s, `ZEIT`-Zeile, zweite Datei `ok`, `1 ok, 0 rot, 1 Zeit.`, Exit 1; `--timeout 0` → Exit 2.
- **Warum misst der Test das Richtige?** Eine hängende Datei darf den Prüflauf nicht blockieren.
- **Gegenprobe:** alter Stand → rot.

### T7: --liste führt nichts aus; keine Testdateien → Exit 2
- **Prüft:** A4.1, A5
- **Aufbau:** leeres Temp-Repo; dann zwei Dateien, die beim Ausführen eine Marke anlegen würden.
- **Erwartung:** Exit 2 mit Meldung (auch `--liste`); danach `--liste` Exit 0, keine Marke, Zeilen mit `[python]` und Sonderargument.
- **Warum misst der Test das Richtige?** T8 verlässt sich darauf, dass `--liste` am echten Repo nichts startet.
- **Gegenprobe:** alter Stand → rot.

### T8: Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile
- **Prüft:** A1, A5, Einstiegspunkt (R58-Vorschlag: Standardwerte prüfen, wenn Tests sie umbiegen)
- **Aufbau:** `ROOT` und `TIMEOUT` des echten Moduls; `python3 scripts/alle_tests.py --liste` mit Arbeitsordner `docs/`.
- **Erwartung:** `ROOT` = Repo-Root, `TIMEOUT` = 300; Exit 0; Liste enthält `tests/test_alle_tests.py`, `role-split/test_role_proxy.py` als unittest, `mcp-server/test_tool_log.py` als Skript mit Server-Pfad; nichts aus `.venv/lib` oder `__pycache__`.
- **Warum misst der Test das Richtige?** Bei `mcp_kette` waren genau die umgebogenen Standardwerte falsch (ROOT = `mcp-server/`), und kein Test sah es.
- **Gegenprobe:** alter Stand → rot.

## Offene Fragen

- Keine

## Abweichende Meinung

- `scripts/test_mcp_deny.py` (Kirby-Zeit, Dry-Run) wird als Skript-Test mitgenommen. Falls er veraltet und rot ist, zeigt das Skript das – Entscheidung behalten oder archivieren bleibt bei Hawe.
