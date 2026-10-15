# Handover: scout_email_versand

- **Spec:** `docs/projekt_management/spec_20261015_scout_email_versand.md`
- **Datum:** 2026-10-15
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** Commit `b3eb852` (arbeitsverwar war clean)

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| 1. `pip install markdown` | erfüllt | `.venv`, Version 3.11.1 |
| 2. `scripts/send_scout_email.py` | erfüllt | neu erstellt |
| 3. `scripts/run_scout_pipeline.sh` + chmod +x | erfüllt | neu erstellt, `-rwxr-xr-x` |
| 4. PLIST anpassen auf Pipeline-Wrapper | erfüllt | `config/launchd/llm_scout.plist` geändert |
| 5. Keine Änderung an `llm_scout.py` | erfüllt | Datei unverändert |

## Geänderte und neue Dateien

- `scripts/send_scout_email.py` – neu – Liest KW-Bericht, konvertiert MD→HTML, versendet per SMTP/Gmail. Credentials aus Schlüsselbund (`lab-scout-smtp`).
- `scripts/run_scout_pipeline.sh` – neu – Shell-Wrapper: Scout → bei Erfolg E-Mail. Setzt `LAB_DIR` und nutzt venv-Interpreter.
- `config/launchd/llm_scout.plist` – geändert – ProgramArguments zeigt nun auf `run_scout_pipeline.sh` statt direkt auf `llm_scout.py`.

## Abweichungen von der Spec

- **Keine.** Umsetzung folgt der Spec 1:1.

## Annahmen

- Der `LAB_DIR`-Pfad aus der PLIST (`agents/llm_scout/data`) gilt auch für das E-Mail-Skript. Der Shell-Wrapper setzt `LAB_DIR` explizit, sodass beide Skripte denselben Pfad nutzen.
- Das Gmail-App-Passwort wird vom Nutzer im Schlüsselbund abgelegt (noch nicht geschehen).
- Die HTML-E-Mail enthält minimales CSS für bessere Lesbarkeit im Mail-Client (nicht in der Spec, aber sinnvoll).

## Getestet (mit echter Ausgabe)

### markdown-Installation

```
$ .venv/bin/python3 -c "import markdown; print(markdown.__version__)"
3.11.1
```

### py_compile

```
$ python3 -m py_compile scripts/send_scout_email.py && echo "OK"
OK
```

### bash -n

```
$ bash -n scripts/run_scout_pipeline.sh && echo "OK"
OK
```

### PlistBuddy

```
$ /usr/libexec/PlistBuddy -c "Print" config/launchd/llm_scout.plist
Dict {
    StandardOutPath = /Users/hans-wernereberhardt/PycharmProjects/llama-server/logs/llm_scout_out.log
    EnvironmentVariables = Dict {
        LAB_DIR = /Users/hans-wernereberhardt/PycharmProjects/llama-server/agents/llm_scout/data
    }
    StartCalendarInterval = Array {
        Dict {
            Weekday = 1
            Hour = 8
            Minute = 0
        }
    }
    ProgramArguments = Array {
        /usr/bin/bash
        /Users/hans-wernereberhardt/PycharmProjects/llama-server/scripts/run_scout_pipeline.sh
    }
    StandardErrorPath = /Users/hans-wernereberhardt/PycharmProjects/llama-server/logs/llm_scout_err.log
    WorkingDirectory = /Users/hans-wernereberhardt/PycharmProjects/llama-server
    Label = de.hawe.lab.llm_scout
}
```

### Manueller Test send_scout_email.py (mit LAB_DIR, ohne Schlüsselbund-Eintrag)

```
$ LAB_DIR=/Users/hans-wernereberhardt/PycharmProjects/llama-server/agents/llm_scout/data .venv/bin/python3 scripts/send_scout_email.py 2>&1
Bericht gefunden: /Users/hans-wernereberhardt/PycharmProjects/llama-server/agents/llm_scout/data/weekly-reports/llm_scout_kw42_2026.md
Fehler beim E-Mail-Versand: Schlüsselbund-Eintrag 'lab-scout-smtp' nicht gefunden (security exit code 44)
EXIT: 1
```

Das Skript findet die KW42-Datei korrekt und bricht mit Exit 1 ab, weil das App-Passwort noch nicht im Schlüsselbund liegt. Verhalten entspricht der Spec.

## Nicht getestet

- **E-Mail-Versand mit gültigen Credentials:** Der Schlüsselbund-Eintrag `lab-scout-smtp` existiert nicht. Hawe muss das App-Passwort ablegen, bevor ein vollständiger Test möglich ist.
- **Pipeline-End-to-End:** `run_scout_pipeline.sh` wurde nicht durchlaufen, da der Scout einen laufenden llama-server braucht und der E-Mail-Versand Credentials.
- **launchd-Ausführung:** Die PLIST wurde nicht neu geladen.

## Offene Punkte / bekannte Schwächen

- **Schlüsselbund-Eintrag fehlt:** Hawe muss noch ausführen:
  ```bash
  security add-generic-password -a askvalentinai@gmail.com -s lab-scout-smtp -w <APP_PASSWORD>
  ```
  Ohne diesen Schritt schlägt der E-Mail-Versand mit Exit 1 fehl.
- **Gmail App-Passwort erforderlich:** `askvalentinai@gmail.com` braucht ein Gmail-App-Passwort (nicht das normale Passwort). Unter [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) zu erstellen.
- **llm_scout.py muss erfolgreich sein:** Wenn der Scout fehlschlägt (z. B. llama-server nicht erreichbar), wird kein Versand ausgelöst. Das ist beabsichtigt, aber der launchd-Job beendet sich dann mit Exit != 0.

## Aktivierung

Nachdem das App-Passwort im Schlüsselbund liegt:

```bash
# PLIST neu laden (falls bereits geladen, vorher unload)
launchctl unload config/launchd/llm_scout.plist 2>/dev/null
launchctl load config/launchd/llm_scout.plist

# Sofortiger Test (ohne auf Montag zu warten)
launchctl kickstart -k gui/501/de.hawe.lab.llm_scout
```
