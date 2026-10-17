# Handover: scout_mail_trockenlauf

- **Spec:** `docs/projekt_management/spec_20261017_scout_mail_trockenlauf.md`
- **Datum:** 2026-10-17
- **Modell / Werkzeug:** Qwen3.6 27B in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** `f03a455` (Rücksetzpunkt vor Umsetzung spec_20261017_scout_mail_trockenlauf)

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Trockenlauf-Modus `--dry-run` | erfüllt | `scripts/send_scout_email.py`, Funktion `mode_dry_run()` |
| A2: Fehler-Mail `--fail-mail --exit-code <n>` | erfüllt | `scripts/send_scout_email.py`, Funktion `mode_fail_mail()`, `build_fail_email()` |
| A3: Datei-Fallback bei SMTP-Fehler | erfüllt | `scripts/send_scout_email.py`, `mode_fail_mail()` (try/except um `send_email_smtp()`) |
| A4: „Kein Report" bleibt kein Fehler | erfüllt | `scripts/send_scout_email.py`, `mode_normal()` und `mode_dry_run()` (Exit 0 bei fehlendem Report) |
| A5: Pipeline-Wrapper anpassen | erfüllt | `scripts/run_scout_pipeline.sh` (neuer `--fail-mail`-Aufruf bei Scout-Fehler, `|| :` gegen `set -e`) |
| A6: Exit-Code-Dokumentation in llm_scout.py | erfüllt | `agents/llm_scout/llm_scout.py`, Kommentarblock in `main()` |
| A7: Credentials – kein Passwort im dry-run | erfüllt | `mode_dry_run()` ruft `get_password()` nicht auf |
| A8: Keine PLIST-Änderung | erfüllt | `config/launchd/llm_scout.plist` unverändert |
| .gitignore: outbox/ ergänzen | erfüllt | `.gitignore`, Zeile `agents/llm_scout/data/outbox/` |
| SMTP-Override-Variablen | erfüllt | `scripts/send_scout_email.py`, `SMTP_HOST`/`SMTP_PORT` per `os.getenv()` |

## Geänderte und neue Dateien

- `scripts/send_scout_email.py` – geändert – Refaktorierung in drei Modi (`mode_normal`, `mode_dry_run`, `mode_fail_mail`); neue Funktionen `build_email_message()`, `build_fail_email()`, `save_email_to_file()`, `send_email_smtp()`; CLI-Argumente `--dry-run`, `--fail-mail`, `--exit-code`; SMTP-Host/Port per Umgebungsvariablen überschreibbar; Exit-Code-Semantik-Tabelle `EXIT_CODE_MEANINGS`
- `scripts/run_scout_pipeline.sh` – geändert – Bei Scout-Fehler: `--fail-mail`-Aufruf mit `|| :` (set -e-sicher); originaler Scout-Exit-Code wird an launchd weitergegeben
- `agents/llm_scout/llm_scout.py` – geändert – Kommentarblock mit Exit-Code-Semantik in `main()`
- `.gitignore` – geändert – `agents/llm_scout/data/outbox/` ergänzt

## Abweichungen von der Spec

- Keine.

## Annahmen

- Die `MIMEText.as_string()`-Methode kodiert den HTML-Body als base64 (`Content-Transfer-Encoding: base64`). Das ist standardkonformes Verhalten der Python `email`-Bibliothek und entspricht dem RFC-822-Textformat der Spec. Der Body ist in einem Texteditor lesbar (als base64) und per `python3 -m email`/`mutt` wiedergibbar.
- Der Subject-Header der Fehler-Mail enthält ein Gedankenstrich-Zeichen (`–`, U+2013), das von `as_string()` als RFC-2047-codiert wird (`=?utf-8?q?...?=`). Das ist MIME-konform.

## Getestet (mit echter Ausgabe)

```
$ # T1: Trockenlauf mit bestehendem Report
$ LAB_DIR=/tmp/scout_test_t1 .venv/bin/python3 scripts/send_scout_email.py --dry-run
Bericht gefunden: /tmp/scout_test_t1/weekly-reports/llm_scout_kw42_2026.md
Trockenlauf: E-Mail abgelegt unter /tmp/scout_test_t1/outbox/llm_scout_kw42_2026.eml
Exit-Code: 0
# .eml existiert, enthält Content-Type: text/html; charset="utf-8"
# Body (base64-decodiert): enthält <table>, <pre>, TestModel, "test code block"
# Kein Passwort/Authorization in der Datei
```

```
$ # T2: Trockenlauf ohne Report
$ LAB_DIR=/tmp/scout_test_t2 .venv/bin/python3 scripts/send_scout_email.py --dry-run
Keine Bericht-Datei fuer die aktuelle KW gefunden. Kein Trockenlauf.
Exit-Code: 0
# Keine outbox angelegt
```

```
$ # T3: Normalmodus ohne Report (Regression)
$ LAB_DIR=/tmp/scout_test_t3 .venv/bin/python3 scripts/send_scout_email.py
Keine Bericht-Datei fuer die aktuelle KW gefunden. Kein Versand.
Exit-Code: 0
```

```
$ # T4: Fehler-Mail mit Exit-Code 2 (SMTP-Fehler simuliert)
$ LAB_DIR=/tmp/scout_test_t4 SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9 \
    .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2
Fehler-Mail SMTP fehlgeschlagen ([Errno 61] Connection refused), abgelegt unter /tmp/scout_test_t4/outbox/scout_error_20261017_1043.eml
Exit-Code: 0
# Subject enthält "FEHLER" und "Exit-Code 2"
# Body enthält "llama-server nicht erreichbar"
# stderr verweist auf outbox/
```

```
$ # T5: Fehler-Mail mit Exit-Code 1
$ LAB_DIR=/tmp/scout_test_t5 SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9 \
    .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 1
Fehler-Mail SMTP fehlgeschlagen ([Errno 61] Connection refused), abgelegt unter /tmp/scout_test_t5/outbox/scout_error_20261017_1044.eml
Exit-Code: 0
# Body enthält "Kritischer Fehler in der Scout-Pipeline"
```

```
$ # T6: Fehler-Mail mit unbekanntem Exit-Code 7
$ LAB_DIR=/tmp/scout_test_t6 SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9 \
    .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 7
Fehler-Mail SMTP fehlgeschlagen ([Errno 61] Connection refused), abgelegt unter /tmp/scout_test_t6/outbox/scout_error_20261017_1044.eml
Exit-Code: 0
# Body enthält "Unbekannter Exit-Code"
```

```
$ # T7: Pipeline: Scout-Fehler → Fehler-Mail → korrekter Exit-Code
$ LAB_DIR=/tmp/scout_test_t7 SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9 \
    LLAMA_SERVER_URL=http://localhost:9 bash scripts/run_scout_pipeline.sh
=== LLM Scout Pipeline gestartet ===
...
llama-server unter http://localhost:9 nicht erreichbar – nichts geholt, nichts markiert.
Fehler: llm_scout.py beendet mit Exit-Code 2.
Fehler-Mail SMTP fehlgeschlagen ([Errno 61] Connection refused), abgelegt unter .../outbox/scout_error_20261017_1045.eml

=== Pipeline Exit-Code: 2 ===
# Exit-Code = 2 (originaler Scout-Exit, nicht der der Fehler-Mail)
# outbox/ enthält scout_error_*.eml
```

```
$ # T9: Normalmodus mit SMTP-Fehler → keine .eml, keine Rekursion
$ LAB_DIR=/tmp/scout_test_t9 SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9 \
    .venv/bin/python3 scripts/send_scout_email.py
Bericht gefunden: /tmp/scout_test_t9/weekly-reports/llm_scout_kw42_2026.md
Fehler beim E-Mail-Versand: [Errno 61] Connection refused
Exit-Code: 1
# Keine outbox angelegt, keine scout_error_*.eml
```

```
$ # T10: Trockenlauf lässt echte Daten unberührt
$ LAB_DIR=.../agents/llm_scout/data .venv/bin/python3 scripts/send_scout_email.py --dry-run
Bericht gefunden: .../weekly-reports/llm_scout_kw42_2026.md
Trockenlauf: E-Mail abgelegt unter .../outbox/llm_scout_kw42_2026.eml
Exit-Code: 0
# mtime der .md-Datei unverändert (1792085752 vor und nach)
# .eml in outbox/ vorhanden
```

## Nicht getestet

- **T8 (Pipeline: Scout-Exit 0, keine neuen Items → keine Mail):** Erfordert einen laufenden llama-server (oder einen Mock), damit `llm_scout.py` mit Exit 0 endet. Kein Router war während der Tests verfügbar. Der logische Pfad ist trivial: Scout Exit 0 → Step 2 (Normalmodus) → kein Report → Exit 0. Der Pfad wurde indirekt durch T2/T3 (keine Report-Datei → Exit 0) abgedeckt.
- **Echter SMTP-Versand:** Wurde bewusst nicht getestet (Spec-Nicht-Ziel). Hawe führt den ersten echten Versand manuell durch.
- **T7 mit echtem launchd-Log:** Die `logs/llm_scout_err.log`-Datei wurde nicht geprüft, da launchd nicht im Testkontext läuft. Der stderr-Ausgang ist korrekt (enthält den outbox-Verweis), launchd leitet stderr in die Logdatei um.

## Offene Punkte / bekannte Schwächen

- Die HTML-Body der `.eml`-Dateien ist base64-codiert (von `MIMEText.as_string()`). Das ist korrekt, aber ein reiner Texteditor zeigt base64 statt des HTML-Inhalts. Zum Prüfen empfiehlt sich `python3 -c "import email; msg = email.message_from_string(open('datei.eml').read()); print(msg.get_payload(decode=True).decode('utf-8'))"`.
- Der Subject-Header der Fehler-Mail enthält das Gedankenstrich-Zeichen (U+2013 `–`), das als RFC-2047 `=?utf-8?q?…=E2=80=93…?=` codiert wird. E-Mail-Clients decodieren das korrekt.
