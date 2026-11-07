# Spec: pruefen_venv

- **Datum:** 2026-11-07
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette_lauf` aus der Chat-UI
- **Betroffene Dateien:** `role-split/kette/kette.py` (neue Funktion `test_python`, `tests_laufen`, `unittest_lauf` in `_pruefen_teile`)
- **Änderungsstellen:** 3 (neue Funktion direkt vor `def tests_laufen`; Startzeile in `tests_laufen`; Startzeile plus Ausgabezeile in `unittest_lauf`)

## Ziel

Die Prüfungen der Kette starten Tests mit dem Python des Projekts statt mit dem Python, das `kette.py` gerade ausführt. Aus der Chat-UI (`kette_lauf`) läuft `kette.py` mit dem Python des MCP-Servers (`mcp-server/.venv`, ohne Projektpakete wie `requests`). Im Pilot `mail_planung` (07.11.) endeten deshalb beide Läufe nach guter Umsetzung mit Exit 1 (`No module named 'requests'`), Prüfung und Review mussten im Terminal nachgeholt werden. Hawe: Die Kette soll über die Chat-UI funktionieren.

Regel wie `scripts/alle_tests.py` `interpreter()`: nächstes `.venv/bin/python` vom Ordner der Testdatei aufwärts, höchstens bis `ROOT`; sonst `sys.executable`. Die Prüfausgabe nennt das verwendete Python.

## Nicht-Ziele

- **`tests/test_pruefen_venv.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Änderung an `mcp-server/kette_werkzeuge.py`, `scripts/alle_tests.py`, `automatik.py`, `spec_pruefen.py`, dem Umsetzer (opencode) oder dem MCP-venv. Kein Nachinstallieren von Paketen.
- `LAEUFER`, die Auswertung der Testergebnisse, `gegenprobe`, `tests_pruefen` und `pruefen` bleiben unverändert – sie nutzen `tests_laufen`/`unittest_lauf` und bekommen die Änderung dadurch mit.
- Kein `.resolve()` auf dem gefundenen venv-Python (ein venv wirkt nur über seinen eigenen Pfad).
- Kein venv oberhalb von `ROOT`.
- Alle bestehenden Tests bleiben grün (`python3 scripts/alle_tests.py`; Altlast `test_scout_kw_doppelversand.py` bleibt rot).

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_pruefen_venv.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Nichts Neues: Es wird nur ein anderes, lokales Python für Testläufe gestartet.
- **Technische Sperre für Tests:** Alle Tests arbeiten in `tempfile.TemporaryDirectory()` mit eigenem Git-Repo und umgebogenem `kette.ROOT`/`kette.PM`. Das „venv“ ist ein Shell-Skript im Temp-Repo, das seine Aufrufe in eine Datei außerhalb des Repos schreibt und das laufende Python mit zusätzlichem `PYTHONPATH` startet. T1 liest am Ende nur den Standardwert am echten Repo (kein Start).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `kette.main(["pruefen", kt])` (Befehlszeile `kette.py pruefen`, und über `lauf` aus der Chat-UI) | T6 |
| `role-split/kette/kette.py` | als Modul (`test_python`, `tests_laufen`, `_pruefen_teile`) | T1–T5 |

## Quellen

- `role-split/kette/kette.py` Zeilen 370–391 – `LAEUFER` (wird unverändert an das gewählte Python übergeben)
- `role-split/kette/kette.py` def tests_laufen – Einbaustelle 1 (Startzeile), Einfügestelle der neuen Funktion davor
- `role-split/kette/kette.py` def _pruefen_teile – Einbaustelle 2 (`unittest_lauf`)
- `role-split/kette/kette.py` def gegenprobe – nutzt `tests_laufen` (keine Änderung)
- `scripts/alle_tests.py` def interpreter – Muster für die Suchregel
- `mcp-server/kette_werkzeuge.py` def _laeufer – warum `sys.executable` aus der Chat-UI das MCP-venv ist
- `tests/test_pruefen_venv.py` – Vorgabe-Tests (Meldetexte wörtlich übernehmen)

## Anforderungen

### A1: `test_python`
- **Anforderung:** Neue Funktion `test_python(skript: Path | str) -> str` unmittelbar vor `def tests_laufen`:
  1. Relativer Pfad → `ROOT / skript`.
  2. `ordner = pfad.resolve().parent`; liegt `ordner` weder gleich `ROOT.resolve()` noch darunter → `sys.executable`.
  3. Von `ordner` aufwärts bis einschließlich `ROOT`: gibt es `ordner / ".venv" / "bin" / "python"` (`.exists()`, ein kaputter Link zählt also nicht) → genau dieser Pfad als `str`, **nicht aufgelöst**.
  4. Bei `ROOT` ohne Fund → `sys.executable`. Nie über `ROOT` hinaus suchen.
- **Stelle:** `role-split/kette/kette.py`, neue Funktion unmittelbar vor `def tests_laufen`.
- **Akzeptanz:** T1.

### A2: Testläufe mit `test_python`
- **Anforderung:**
  1. `tests_laufen`: im `subprocess.run` statt `sys.executable` → `test_python(skript)`; Rest der Zeile unverändert (`"-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul`).
  2. `unittest_lauf` (in `_pruefen_teile`): `python = test_python(skript)`, **vor** dem Start `print(f"Python: {python}")`, dann `subprocess.run([python, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"], …)` wie bisher. Die Zeile `Python: …` ist damit die erste Zeile im Abschnitt `## unittest` der Prüfdatei.
- **Stelle:** `role-split/kette/kette.py`, `def tests_laufen` (Zeile mit `subprocess.run`) und `def _pruefen_teile` → `def unittest_lauf`.
- **Akzeptanz:** T2, T3, T4, T5, T6.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | kein `.venv` im Repo | – | `sys.executable` (Verhalten wie bisher) | T1, T4 |
| A1 | `.venv` oberhalb von `ROOT` | – | ignoriert, `sys.executable` | T1 |
| A1 | näheres `.venv` im Unterordner der Testdatei | – | dieses | T1 |
| A1 | Testdatei außerhalb von `ROOT` | – | `sys.executable`, keine Endlosschleife | T1 |
| A1 | venv-Python ist ein Link / kaputter Link | – | Linkpfad unaufgelöst / `sys.executable` | T1 |
| A2 | Modul nur im venv vorhanden (wie `requests`) | – | mit venv grün; ohne venv Abweichung (Exit 1) mit Modulname in der Ausgabe | T2, T3, T4 |
| A2 | Gegenstelle antwortet nicht / Zeitlimit | – | unverändert (`TimeoutExpired` → `None` bzw. wie bisher) | – |
| A2 | gegenprobe setzt Datei zurück | Sicherung im Temp-Ordner | unverändert, jetzt mit venv-Python | T5 |
| A2 | Aufruf über `main` | Prüfdatei | `## unittest  (Exit 0)` mit erster Zeile `Python: …/.venv/bin/python` | T6 |
| A2 | Absturz mitten im Lauf | – | unverändert | – |

## Testplan

Die Tests stehen in `tests/test_pruefen_venv.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Vorab 6/6 rot; gegen die Referenz 6/6 grün, dreimal stabil (< 1 s). Alle 14 Testdateien, die `kette` berühren, alt und neu grün (R65). Mutationsprüfung ohne Bytecode-Cache (R66): 11 von 12 gefangen (u. a. `tests_laufen`/`unittest` bleiben bei `sys.executable`, Python-Zeile fehlt oder steht hinter der Ausgabe, venv-Pfad aufgelöst, Suche über `ROOT` hinaus, fehlender Schutz außerhalb `ROOT` – endet als Hänger –, nur `ROOT/.venv`, relativer Pfad nicht an `ROOT`, kaputter Link zählt, frühes `return`); der Überlebende `test_python("tests")` statt `test_python(skript)` ist für `tests/test_<kt>.py` gleichwertig.

### T1: Auswahl des Pythons
- **Prüft:** A1
- **Aufbau:** Temp-Repo mit `.venv`; Unterordner mit eigenem `.venv`; Datei außerhalb; `.venv` oberhalb von `ROOT`; Link und kaputter Link; am Ende echtes Repo (nur Standardwert, kein Start).
- **Erwartung:** jeweils der in A1 beschriebene Pfad; echtes Repo: `.venv/bin/python`, wenn vorhanden, sonst `sys.executable` – für relativen und absoluten Pfad gleich.
- **Warum misst der Test das Richtige?** Ein aufgelöster Pfad zeigt auf das System-Python, und die Pakete des venv fehlen wieder.
- **Gegenprobe:** alter Stand → rot (Funktion fehlt).

### T2: `tests_laufen` mit venv
- **Prüft:** A2
- **Aufbau:** Testdatei importiert ein Modul, das nur über das venv-Python erreichbar ist; mit und ohne `.venv`.
- **Erwartung:** mit venv `{"test_t1_wert": "ok"}` und Aufruf mit `-X pycache_prefix=` protokolliert; ohne venv kein `ok`, `ERROR`, kein weiterer venv-Aufruf.
- **Warum misst der Test das Richtige?** Bildet genau den Fehler aus dem Pilot nach (`requests`).
- **Gegenprobe:** alter Stand → rot.

### T3: `unittest` mit venv
- **Prüft:** A2
- **Aufbau:** `_pruefen_teile("k")` im Temp-Repo mit Commit „Spec k“.
- **Erwartung:** `unittest` Exit 0; Ausgabe beginnt mit `Python: <ROOT>/.venv/bin/python`; Aufruf `-m unittest -v tests/test_k.py` protokolliert.
- **Warum misst der Test das Richtige?** Ohne die Zeile sieht Hawe in `kette_ergebnis` nicht, womit geprüft wurde.
- **Gegenprobe:** alter Stand → rot.

### T4: `unittest` ohne venv
- **Prüft:** A2, A1
- **Aufbau:** wie T3, `.venv` entfernt.
- **Erwartung:** Exit 1; Ausgabe beginnt mit `Python: <sys.executable>`; Modulname `nur_im_venv` in der Ausgabe; kein venv-Aufruf.
- **Warum misst der Test das Richtige?** Ohne venv bleibt alles wie bisher, nur sichtbar.
- **Gegenprobe:** alter Stand → rot (keine Python-Zeile).

### T5: gegenprobe mit venv
- **Prüft:** A2
- **Aufbau:** wie T3, Abschnitt `gegenprobe`.
- **Erwartung:** Exit 0; `1 von 1 Tests werden durch eine einzelne alte Datei rot.`; `code_k.py` genannt; mindestens zwei venv-Aufrufe.
- **Warum misst der Test das Richtige?** Mit dem falschen Python bricht gegenprobe ab („läuft auf dem aktuellen Stand nicht grün“).
- **Gegenprobe:** alter Stand → rot.

### T6: über `main`
- **Prüft:** A2 (R58: echter Aufruf)
- **Aufbau:** `kette.main(["pruefen", "k"])` im Temp-Repo.
- **Erwartung:** Prüfdatei enthält `## unittest  (Exit 0)` mit erster Zeile `Python: <ROOT>/.venv/bin/python`; Ausgabe `unittest: ok` und `gegenprobe: ok`.
- **Warum misst der Test das Richtige?** So ruft `lauf` (auch aus der Chat-UI) die Prüfung auf.
- **Gegenprobe:** alter Stand → rot.

## Offene Fragen

- Keine

## Abweichende Meinung

- Die Änderung wirkt erst ab der **nächsten** Kette: Der laufende Prozess dieser Kette hat das alte `kette.py` schon geladen. Ihre eigene Prüfung braucht nichts aus dem venv und läuft auch so durch.
- Der Umsetzer (opencode) startet seine eigenen Testläufe weiter selbst; das betrifft nur seine Arbeitsweise, nicht die Prüfung der Kette.
- Ist das Repo-`.venv` kaputt oder fehlt ein Paket dort, schlägt die Prüfung jetzt mit dem venv fehl – richtig so, denn dort laufen auch Hawes Werkzeuge.
