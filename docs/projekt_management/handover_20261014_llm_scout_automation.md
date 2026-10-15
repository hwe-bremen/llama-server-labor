# Handover: llm_scout_automation

- **Spec:** `docs/projekt_management/spec_20261014_llm_scout_automation.md` (Datei existiert nicht im Repo; Anweisungen direkt von Hawe)
- **Datum:** 2026-10-14
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** Commit `287f0f5` (arbeitsverwar war clean, kein expliziter Rücksetzcommit nötig)

## Umgesetzt

| Anforderung | Status | Wo im Code |
|---|---|---|
| 1a. os.makedirs vor Report-Schreiben | erfüllt | `agents/llm_scout/llm_scout.py`, Zeile 304, in `main()` |
| 1b. sys.exit(0) bei Erfolg, sys.exit(1) bei Fehler | erfüllt | `agents/llm_scout/llm_scout.py`, Zeilen 270-318, try/except in `main()` |
| 1c. Shebang | bereits vorhanden | Zeile 1: `#!/usr/bin/env python3` (keine Änderung nötig) |
| 2. chmod +x | erfüllt | Datei ist nun `-rwxr-xr-x` |
| 3. launchd plist | erfüllt | `config/launchd/llm_scout.plist` (neu) |
| 4. logs/ Ordner | erfüllt | `logs/` erstellt |

## Geänderte und neue Dateien

- `agents/llm_scout/llm_scout.py` – geändert – os.makedirs() vor Report-Schreiben eingefügt; main() in try/except gehüllt mit sys.exit(0)/sys.exit(1); Rechte auf ausführbar gesetzt
- `config/launchd/llm_scout.plist` – neu – launchd-Job: monatags 08:00 Uhr, venv-Interpreter, absolute Pfade
- `logs/` – neu – Ordner für stdout/stderr Logs der launchd-Jobs

## Abweichungen von der Spec

- **Interpreter in plist:** Die Spec empfiehlt Shebang + direkter Pfad zum Skript. Ich habe stattdessen den venv-Interpreter (`.venv/bin/python3`) als erstes ProgramArgument verwendet. Grund: launchd setzt keine `$PATH`-Umgebung, der Shebang `#!/usr/bin/env python3` würde dann auf den system-Python (3.9.6) zeigen, der `feedparser` und `requests` nicht hat. Der venv-Interpreter garantiert, dass die Dependencies verfügbar sind.
- **Spec-Datei:** Die Datei `spec_20261014_llm_scout_automation.md` existiert nicht im Repo. Die Anforderungen kamen als direkte Anweisung.

## Annahmen

- Der Job soll auf dem M4 MacBook Pro laufen (Pfade basieren auf `/Users/hans-wernereberhardt/PycharmProjects/llama-server`).
- Der llama-server muss zum Ausführungszeitpunkt (montags 08:00) erreichbar sein, damit `call_llm_for_evaluation()` funktioniert. Falls nicht, gibt es eine Fehlermeldung im Report (existierendes Verhalten).
- Die `LAB_DIR`-Umgebungsvariable wird von launchd nicht gesetzt; der Code fällt auf `Path.home() / "lab"` zurück. Das bedeutet: DB und Reports landen in `~/lab/`, nicht im Projektordner. Das ist das bestehende Verhalten und wurde nicht geändert.

## Getestet (mit echter Ausgabe)

```
$ python3 -m py_compile agents/llm_scout/llm_scout.py && echo "py_compile: OK"
py_compile: OK
```

```
$ /usr/libexec/PlistBuddy -c "Print" config/launchd/llm_scout.plist
Dict {
    ProgramArguments = Array {
        /Users/hans-wernereberhardt/PycharmProjects/llama-server/.venv/bin/python3
        /Users/hans-wernereberhardt/PycharmProjects/llama-server/agents/llm_scout/llm_scout.py
    }
    WorkingDirectory = /Users/hans-wernereberhardt/PycharmProjects/llama-server
    Label = de.hawe.lab.llm_scout
    StartCalendarInterval = Array {
        Dict {
            Weekday = 1
            Hour = 8
            Minute = 0
        }
    }
    StandardOutPath = /Users/hans-wernereberhardt/PycharmProjects/llama-server/logs/llm_scout_out.log
    StandardErrorPath = /Users/hans-wernereberhardt/PycharmProjects/llama-server/logs/llm_scout_err.log
}
```

```
$ ls -la agents/llm_scout/llm_scout.py
-rwxr-xr-x@ 1 hans-wernereberhardt  staff  10833 Oct 14 21:35 agents/llm_scout/llm_scout.py
```

## Nicht getestet

- **launchd-Ausführung:** Der Job wurde nicht tatsächlich über launchd gestartet. Dazu wäre `launchctl load` nötig, was Hawe manuell ausführen muss.
- **End-to-End-Ausführung:** Das Skript wurde nicht durchlaufen (es braucht Netzwerkzugriff auf Hugging Face, GitHub RSS und einen laufenden llama-server).
- **chmod +x in git:** Die Rechteänderung ist lokal gemacht. Git auf macOS trackt execute-Rechte korrekt (`git add` staged die Änderung), aber der Commit steht noch aus.

## Offene Punkte / bekannte Schwächen

- **LAB_DIR-Default:** launchd setzt keine benutzerdefinierten Umgebungsvariablen. Ohne `LAB_DIR` landet die DB in `~/lab/llm_scout.db` und die Reports in `~/lab/weekly-reports/`. Falls Hawe das im Projektordner haben will, braucht die plist einen `<key>EnvironmentVariables</key>`-Block mit `LAB_DIR`.
- **llama-server muss laufen:** Der Job wird montags 08:00 ausgeführt, unabhängig davon, ob der llama-server läuft. Falls nicht, enthält der Report eine Fehlermeldung statt einer Bewertung.
- **Kein RestartOnError:** Die plist hat keinen `RunAtLoad` oder `KeepAlive` Key. Der Job läuft einmal pro Montag. Bei Fehlern gibt es keinen automatischen Retry.

## Aktivierung

Hawe muss den Job manuell aktivieren:

```bash
launchctl load config/launchd/llm_scout.plist
```

Zum Deaktivieren:

```bash
launchctl unload config/launchd/llm_scout.plist
```

Zum sofortigen Test (ohne auf montags zu warten):

```bash
launchctl kickstart -k gui/501/de.hawe.lab.llm_scout
```
