# Verdikt: scout_mail_trockenlauf

- **Spec:** `spec_20261017_scout_mail_trockenlauf.md`
- **Handover:** `handover_20261017_scout_mail_trockenlauf.md`
- **Datum:** 2026-10-17
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `scripts/send_scout_email.py` (voll), `scripts/run_scout_pipeline.sh` (voll), `agents/llm_scout/llm_scout.py` (voll), `config/launchd/llm_scout.plist`, `.gitignore`; dazu `git status`/`git diff` (geänderte Dateien: genau die vier im Handover genannten, PLIST nicht berührt). Hinweis: Im selben Dateinamen lag bereits ein früheres Verdikt desselben Modells (Ergebnis NACHBESSERN); es wurde durch dieses ersetzt, der Dissens ist in „Abweichende Meinung" festgehalten.

## Ergebnis

**PASS** – Alle Anforderungen A1–A8 und der `.gitignore`-Punkt sind im Code erfüllt, die Fehlerpfade (SMTP-Fehler, Fallback-Fehler, Scout-Fehler, Email-Fehler, fehlender Report) enden mit sichtbaren Meldungen und den spezifikationskonformen Exit-Codes. Offene Befunde sind fünf, alle „niedrig" (Robustheit, teils vorbestehend); keiner verliert Daten, lässt einen Fehler unbemerkt oder widerspricht dem Sinn einer Anforderung.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | `--dry-run`: Mail komplett bauen, `.eml` nach `outbox/` (`{name}.eml`), kein SMTP-Handshake, kein Schlüsselbund, Exit 0/1, `.gitignore`-Eintrag | erfüllt | `scripts/send_scout_email.py:219-236` (`mode_dry_run`), `:174-182` (`save_email_to_file`, Ordner bei Bedarf), `:228-231` (kein `smtplib`/`get_password` auf diesem Pfad), `.gitignore:38-39` |
| A2 | `--fail-mail --exit-code <n>`: Betreff `LLM Scout FEHLER KW{KW} {JJJJ} – Exit-Code {n}`, 6 Zeilen Inhalt, Semantik-Tabelle (2/1/sonst), gleiche Absender/Konstanten, kein Report-Lesefehler, eigener Exit 0/1 | erfüllt | `scripts/send_scout_email.py:45-48` (Tabelle, Strings wortgleich mit Spec), `:133-171` (`build_fail_email`, Zeilen 1–6 inkl. Leerzeile `<p></p>`), `:147` (Betreff), `:239-271` (Modus), `:297-301` (CLI-Dispatch) |
| A3 | Datei-Fallback bei jedem SMTP-Fehler: `scout_error_{JJJJMMDD}_{HHMM}.eml`, max. ein Versuch, Exit 0 danach, Exit 1 + stderr wenn beide scheitern, stderr-Meldung in beiden Fällen | erfüllt | `scripts/send_scout_email.py:250-271` (ein `try` um `send_email_smtp`, genau ein Fallback-Versuch; stderr-Zeilen `:253` SMTP-OK, `:261-264` Fallback mit outbox-Pfad, `:267-270` Doppelscheitern) |
| A4 | Kein Report → Normal- und Trockenlauf Exit 0, keine Mail, keine `.eml`; Scout-Exit 0 ohne neue Items → Pipeline-Exit 0 | erfüllt | `scripts/send_scout_email.py:202-205`, `:221-224`; `scripts/run_scout_pipeline.sh:31-37`, `:43-48` (Exit 0 → Step 2 → „keine Datei" → 0). T8 end-zu-end nicht gelaufen, Pfad durch Code-Lektüre belegt (siehe „Nicht geprüft") |
| A5 | Wrapper: Scout-Fehler → stderr-Echo + `--fail-mail --exit-code ${SCOUT_EXIT}` unter `|| :`, Wrapper gibt originalen Scout-Exit weiter; Step 2-Fehler → stderr-Echo, kein `--fail-mail`, `exit ${EMAIL_EXIT}` | erfüllt | `scripts/run_scout_pipeline.sh:30-37` (Fang per `|| SCOUT_EXIT=$?` und `|| :`, `exit ${SCOUT_EXIT}`), `:43-48` (Step 2 unverändert, git-diff zeigt nur die Step-1-Änderung) |
| A6 | `llm_scout.py`: nur Doku-Kommentar zur Exit-Code-Semantik, keine Logik-Änderung | erfüllt | `agents/llm_scout/llm_scout.py`, Kommentarblock als erste Zeilen von `main()`; git-diff: genau diese vier Kommentarzeilen, nichts sonst |
| A7 | Kein Passwort in Code, Log, PLIST, `.eml`; `get_password()` nur im echten Versand und in `--fail-mail` | erfüllt | `scripts/send_scout_email.py:51-65` (keine Klartext-Credentials, Fehlermeldungen ohne Passwort), `:190` (`get_password` nur in `send_email_smtp`; diese nur aus `mode_normal`/`mode_fail_mail` erreichbar), PLIST unberührt (git status), keine Auth-Header im Message-Body |
| A8 | PLIST unverändert | erfüllt | `config/launchd/llm_scout.plist` nicht in `git status`-Änderungsliste; Inhalt stimmt mit dem Spec-„Bestand" überein |
| – | `.gitignore` um `agents/llm_scout/data/outbox/` ergänzen | erfüllt | `.gitignore:38-39` |

## Handover gegen Code

- Umsetzungs-Tabelle und „Geänderte und neue Dateien" stimmen mit Code und `git status`/`git diff` überein; es sind genau die vier genannten Dateien geändert, keine unbekannten weiteren.
- „Abweichungen von der Spec: Keine" – in diesem Verdikt bestätigt (zur base64-Nuance: siehe Befund-Liste und „Abweichende Meinung", es ist keine Abweichung von der Spec-Definition).
- Testausgaben T1–T7, T9, T10: vorhanden und mit dem Code konsistent (stderr-Wortlaut, Dateinamen `llm_scout_kw42_2026.eml` / `scout_error_20261017_1043.eml`, Exit-Codes). Die Ausgaben sind transkribiert; ohne Shell-Zugriff konnte ich sie hier nicht neu ausführen. Als Beleg der Ausführung akzeptiert, als unabhängiger Nachweis nicht.
- T8 und der launchd-Log-Verweis in T7 sind im Handover **nicht** als getestet ausgegeben, sondern unter „Nicht getestet" mit Begründung genannt – damit kein unbelegter Test. Der stderr-Verweis auf `outbox/` existiert im Code (`send_scout_email.py:262`); dass er in `logs/llm_scout_err.log` landet, ist PLIST-Seite (`StandardErrorPath`) und läuft nur unter launchd.
- Annahmen (base64-`Content-Transfer-Encoding`, RFC-2047-Betreff): technisch korrekt. `MIMEText(html, "html", "utf-8")` kodiert den Body stets base64; die Spec-Definition der `.eml`-Datei („RFC-822-Textformat, das, was `msg.as_string()` liefert", inkl. Header) ist damit erfüllt. Die T1-Erwartung „enthält die HTML-Tabelle und den `<pre>`-Block" gilt nur für den base64-dekodierten Body – Nuance, keine Verletzung.

## Befunde

| # | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|
| 1 | niedrig | `scripts/send_scout_email.py:39` | `SMTP_PORT = int(os.getenv("SCOUT_SMTP_PORT", "587"))` läuft modulglobal beim Import. Ist die Variable gesetzt, aber leer oder nicht numerisch, stirbt der Prozess in **allen** Modi (auch `--dry-run`) mit `ValueError`, bevor `argparse` läuft. Kein Schlüsselbund-Zugriff (der Prozess endet vor jeder Funktion), kein Datenverlust, Fehler sichtbar (Traceback, Exit 1); auslösend ist nur ein explizit kaputtes Test-Env – Wrapper und PLIST setzen die Variable nicht. | Port und Host erst in `send_email_smtp()` auflösen und Parse-Fehler wie jeden anderen SMTP-Fehler behandeln; im `--fail-mail`-Pfad landet das dann im Datei-Fallback statt im Import-Crash. |
| 2 | niedrig | `scripts/send_scout_email.py:259` | Zwei `--fail-mail`-Ausfälle in derselben Minute erzeugen denselben Namen `scout_error_{JJJJMMDD}_{HHMM}.eml`; der zweite überschreibt den ersten. Bei wöchentlichem Rhythmus praktisch nur durch einen sofortigen manuellen Nachlauf erreichbar; beide Ereignisse bleiben in `logs/llm_scout_err.log` erhalten. Der Dateiname ist von der Spec wortgleich vorgegeben. | Bei bereits existierender Datei Zähler anhängen (`_1`, `_2`) oder Sekundengrundlage – beides wäre eine Spec-Anpassung, kein Umsetzungsfehler. |
| 3 | niedrig | `scripts/send_scout_email.py:192` | `smtplib.SMTP(SMTP_HOST, SMTP_PORT)` ohne Socket-Timeout: ein hängender (nicht verweigerter) SMTP-Host lässt Normal- **und** Fehler-Mail unendlich hängen, der in A3 als Trigger genannte Fall „Timeout" kann nie eintreten. Vorbestehend (alte `send_email()` identisch), keine Spec-Anforderung. | `timeout=` an `smtplib.SMTP` übergeben (z. B. 30 s), damit hängende Verbindungen in den Fallback-Pfad fallen. |
| 4 | niedrig | `scripts/run_scout_pipeline.sh:35` | `--exit-code ${SCOUT_EXIT}` ist ungequote. In der Praxis sicher (Wert stammt aus `$?`, immer Zahl), aber konsequent gequote wäre der Standard unter `set -u`. | `${SCOUT_EXIT}` in Anführungszeichen setzen. |
| 5 | niedrig | `scripts/send_scout_email.py:181`, `:230` | `write_text` ist nicht atomar: ein Abbruch mitten im Write hinterlässt eine halbe `.eml`. `name.replace(".md", ".eml")` ersetzt alle Vorkommen der Teilzeichenkette (für die reale Namgebung `llm_scout_kw{KW}_{JJJJ}.md` ohne Auswirkung). | In eine Temp-Datei schreiben und per `os.replace` umbenennen; für den Namen `removesuffix(".md")` statt `replace` verwenden. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:**
  - T1–T7, T9, T10 neu ausführen (Handover-Ausgaben sind transkribiert).
  - T8 ohne echtes LLM: `router_ready()` prüft nur `GET /v1/models` auf Status 200 (`agents/llm_scout/llm_scout.py`, Funktion `router_ready`); ein statischer Server (z. B. `python3 -m http.server` mit leerer Datei `v1/models`) reicht, und bei nicht erreichbaren HF-/GitHub-Feeds fangen beide Fetcher ihre Exceptions und der Scout endet mit „Keine neuen Items" auf Exit 0 ohne Report – beide Voraussetzungen sind im Code verifiziert.
  - Befund 1 reproduzieren: `SCOUT_SMTP_PORT="" .venv/bin/python3 scripts/send_scout_email.py --dry-run` → heute `ValueError`/Exit 1; nach Fix muss es grün laufen.
  - Trockenlauf auf einer Maschine **ohne** Schlüsselbund-Eintrag `lab-scout-smtp`: muss ohne Interaktion grün bleiben (im Code ist `get_password` auf dem dry-run-Pfad unerreichbar, der Lauf ist der endgültige Beleg).
  - `.eml`-Dateien in `outbox/` in einem Editor/Mail-Client öffnen (Handover liefert die base64-Decode-einzeiler).
- **Braucht externe Quelle:**
  - T7 unter echtem launchd: dass der outbox-Verweis tatsächlich in `logs/llm_scout_err.log` landet (launchd lief im Testkontext nicht).
  - Echter SMTP-Versand (bewusstes Nicht-Ziel, macht Hawe).
  - RFC-2047/base64-Darstellung im konkreten Mail-Client.

## Abweichende Meinung

- **Dissens mit dem früheren Verdikt desselben Modells (NACHBESSERN, Befund #1 „hoch").** Dieses einstufte den modulglobalen `int()`-Parse von `SCOUT_SMTP_PORT` als hoch, weil der dry-run-Pfad „über `send_email_smtp` → `get_password`" den Schlüsselbund berühren könne. Ich widerspreche: In `mode_dry_run()` gibt es **keinen** Code-Pfad zu `send_email_smtp()`/`get_password()` – die Funktionen `find_current_report`, `build_email_message` und `save_email_to_file` rufen sie nicht auf. Auch im Crash-Szenario berührt der Trockenlauf den Schlüsselbund nicht, weil der Prozess beim Import stirbt, bevor irgendeine Funktion läuft. Der Parse-Fehler bricht nur den Start bei explizit kaputtem Test-Env (Wrapper und PLIST setzen die Variable nicht), ist sichtbar und wird von der Spec nicht gedeckt (sie definiert die Override-Variablen als Test-Support ohne Fehlerfall-Vorgabe). Damit ist der Befund „niedrig", nicht „hoch", und der zentrale Sicherheitsversprechen-Befund der alten Fassung entfällt.
- **base64-Body:** Ich hätte `quoted-printable` (oder einen 7-bit-sicheren Pfad) bevorzugt, damit die T1-Erwartung „enthält die HTML-Tabelle" wörtlich im Texteditor wahr ist. Die Spec-Definition (`as_string()`/RFC-822 inkl. Header) ist erfüllt und die Annahme ist im Handover dokumentiert – akzeptabel.
- **Stärkster verbleibender Punkt des Konzepts** (nicht der Umsetzung): „Statt Schweigen" deckt den Fall „llama-server down **und** Gmail tot" nur über die Datei-Ablage in `outbox/` ab, die erst wirkt, wenn jemand hinsieht. Die Spec räumt das selbst ein; die Umsetzung hält sich korrekt an das Nicht-Ziel „kein zweiter Kanal". Kein Einwand an den Code.
