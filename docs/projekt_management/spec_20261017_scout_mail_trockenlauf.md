# Spec: LLM Scout E-Mail – Trockenlauf und Fehler-Mail

**Datum:** 2026-10-17
**Review-Instanz:** Qwen3.8-27B (unsloth/Qwen3.8-27B-GGUF:Q4_K_XL)
**Vorgänger-Spec:** `spec_20261015_scout_email_versand.md`

## Ziel

1. Die E-Mail des LLM Scouts kann **gebaut, aber nicht gesendet** werden (Trockenlauf): Die fertige MIME-Mail wird als Datei abgelegt, sodass der Versand ohne echte Mail geprüft werden kann.
2. Wenn die Pipeline scheitert, kommt **stattdessen eine kurze Fehler-Mail** statt Schweigen. Scheitert auch deren Versand, wird sie als Datei abgelegt und die Pipeline endet trotzdem mit Fehler-Code.

## Nicht-Ziele

- Kein echter Mailversand in Tests. Den einen echten Versand macht Hawe selbst am Ende.
- Kein zweiter Zustellkanal (kein `osascript`, kein Push, kein SMS). Die Fehler-Mail nutzt denselben SMTP-Kanal (Gmail) wie die normale Mail.
- Keine Zustellungsbestätigung, kein Tracking.
- Keine Änderung am Inhalt, am Modell oder am Zeitplan des Scouts.
- „Kein Report" (Scout lief erfolgreich, aber keine neuen Items) bleibt ein stilles, erfolgreiches Ende – keine Fehler-Mail.

## Bestand (kurz, geprüft)

- `scripts/send_scout_email.py`: Findet die Report-Datei der aktuellen KW (`llm_scout_kw{KW}_{JJJJ}.md` in `agents/llm_scout/data/weekly-reports/`), konvertiert Markdown→HTML (`markdown`-Paket), baut MIME (HTML, utf-8), liest App-Passwort aus Schlüsselbund (`security find-generic-password -s lab-scout-smtp -w`), sendet an `smtp.gmail.com:587` (STARTTLS), Betreff `LLM Scout KW{KW} {JJJJ}`, Absender = Empfänger = `askvalentinai@gmail.com`. Exit 0 bei Erfolg oder fehlender Datei, 1 bei Fehler.
- `scripts/run_scout_pipeline.sh`: `set -euo pipefail`, setzt `LAB_DIR`, Step 1 `llm_scout.py`, Step 2 `send_scout_email.py`. Scout-Exit ≠ 0 → `exit ${SCOUT_EXIT}` **ohne Meldung**, Email-Exit ≠ 0 → `exit ${EMAIL_EXIT}` mit `echo` nach stderr, aber **ohne Meldung**.
- `agents/llm_scout/llm_scout.py`: Exit 0 = Erfolg (inkl. „keine neuen Items"), Exit 1 = kritischer Fehler (z. B. leere LLM-Antwort, DB-Fehler), Exit 2 = llama-server nicht erreichbar. **Diese Semantik steht nur in der Implementierung, in keinem Kommentar und in keiner Doku** – für die Fehler-Mail-Botschaft ist sie aber die einzige verlässliche Quelle.
- `config/launchd/llm_scout.plist`: `de.hawe.lab.llm_scout`, Montag 08:00, `StandardOutPath`/`StandardErrorPath` → `logs/llm_scout_{out,err}.log`.
- `.gitignore`: `agents/llm_scout/data/*.db` ist lokal; Berichte unter `data/weekly-reports/` bleiben im Git. `logs/*.log` ist gitignored.

---

## Anforderungen

### A1. Trockenlauf-Modus in `send_scout_email.py`

- Neues Kommandozeilen-Flag: `--dry-run`. Ohne Flag: Verhalten exakt wie heute (echter Versand), kein Default-Wechsel.
- Mit `--dry-run`: Die E-Mail wird **komplett** gebaut – Markdown lesen, HTML-Konvertierung, MIME-Message inkl. Betreff/From/To/HTML-Körper – und als **eine Datei** abgelegt. Es darf dabei **kein SMTP-Handshake** stattfinden.
- **Schlüsselbund:** Im Trockenlauf wird **nicht** auf den macOS-Schlüsselbund zugegriffen. Begründung: Der Trockenlauf muss ohne installiertes App-Passwort laufen (z. B. bei Erstinstallation oder auf einer zweiten Maschine) und darf nie eine Interaktion mit dem Schlüsselbund auslösen. `get_password()` wird in diesem Pfad nicht aufgerufen.
- **Speicherort:** `{LAB_DIR}/outbox/` (also `agents/llm_scout/data/outbox/`), Ordner wird bei Bedarf angelegt.
- **Dateiname:** `{Originaldateiname}.eml`, z. B. `llm_scout_kw42_2026.md` → `llm_scout_kw42_2026.eml`.
- **Inhalt:** Die Datei enthält die MIME-Mail im **RFC-822-Textformat** (das, was `msg.as_string()` liefert: Header inkl. `MIME-Version`, `Content-Type: text/html; charset="utf-8"`, `Subject`, `From`, `To` und HTML-Körper). Damit ist sie prüfbar in einem Texteditor und per `python3 -m email` / `mutt` / `mail -e` wiedergibbar.
- **Exit-Code:** 0 bei abgelegter Mail, 1 bei Fehler (z. B. Report-Datei existiert trotz Trockenlauf nicht? → Nein: „keine Datei" bleibt Exit 0, siehe A4).
- **Kein Passwort in der Datei:** Da im Trockenlauf kein Login stattfindet, enthält die `.eml` kein Passwort. Die Dateisicherung selbst ist damit unkritisch.
- **Ablage überlebt Neustarts:** `.gitignore` wird um `agents/llm_scout/data/outbox/` ergänzt (Trockenlauf-Artefakte sind lokal, nicht Teil des Repos). Begründung: Die `.eml`-Dateien sind Test-/Entwicklungsartefakte, kein Teil des Berichts.

### A2. Fehler-Mail bei Pipeline-Scheitern

- Trigger: `llm_scout.py` beendet sich mit Exit-Code **1 oder 2** (oder einem anderen ≠ 0, ≠ „keine neuen Items"-Exit 0).
- **Nicht-Trigger:** `send_scout_email.py` scheitert selbst → **keine** Fehler-Mail (sonst Rekursion: der kaputte Kanal wird per demselben Kanal gemeldet). Begründung: Der Fehler „SMTP nicht erreichbar" kann nicht per SMTP gemeldet werden. Dieser Fall wird durch A3 (Datei-Fallback) abgedeckt.
- **Ort:** `send_scout_email.py` bekommt einen neuen Modus `--fail-mail --exit-code <n>` (zweite CLI-Form). Der Pipeline-Wrapper (`run_scout_pipeline.sh`) ruft ihn auf, wenn Step 1 (Scout) fehlschlägt.
- **Betreff:** `LLM Scout FEHLER KW{KW} {JJJJ} – Exit-Code {n}`.
- **Inhalt (HTML, deutsch, kurz – max. ~15 Zeilen):**
  - Zeile 1: `Die LLM-Scout-Pipeline vom {JJJJ-MM-TT} ist fehlgeschlagen.`
  - Zeile 2: `Exit-Code: {n}`
  - Zeile 3: `Mögliche Ursache (nach Exit-Code-Semantik): {Text}`
  - Zeile 4 (leer)
  - Zeile 5: `Details: logs/llm_scout_err.log (und llm_scout_out.log)`
  - Zeile 6: `Letzter Scout-Aufruf: {Timestamp}`
- **Exit-Code-Semantik für „Mögliche Ursache"** (wird als statische Mapping-Tabelle im Code gepflegt; diese Tabelle ist in der Spec verankert und Teil der Prüfung):
  - `2` → „llama-server nicht erreichbar (kein Server unter der konfigurierten URL)"
  - `1` → „Kritischer Fehler in der Scout-Pipeline (API-Abruf, LLM-Evaluation oder DB-Fehler) – Details im Log"
  - andere `n` → „Unbekannter Exit-Code – Details im Log"
- **Empfänger/Absender/SMTP:** wie die normale Mail (gleiche Konstanten, gleicher Schlüsselbund-Eintrag).
- **Kein Report-Lesefehler:** Die Fehler-Mail hängt nicht an einer Report-Datei. Sie wird aus den Parametern (`exit_code`, aktueller KW, Zeitstempel) gebaut.
- **Exit-Code des `--fail-mail`-Aufrufs selbst:** 0 bei erfolgreichem Versand oder erfolgreichem Datei-Fallback (A3), 1 wenn **beide** fehlschlagen. Der Pipeline-Wrapper übergibt den **originale** Scout-Exit-Code an launchd, nicht den Exit-Code des Fehler-Mail-Versands.

### A3. Datei-Fallback, wenn der SMTP-Versand der Fehler-Mail scheitert

- Trifft, wenn im `--fail-mail`-Modus **irgendein** Fehler beim SMTP-Versand auftritt (Auth, DNS, Timeout, Verbindung).
- Die fertige MIME-Fehler-Mail wird als **eine Datei** unter `{LAB_DIR}/outbox/` abgelegt: `scout_error_{JJJJMMDD}_{HHMM}.eml` (z. B. `scout_error_20261019_0800.eml`).
- Nach dem erfolgreichen Datei-Fallback beendet sich der `--fail-mail`-Aufruf mit Exit 0 (die Meldung kam an, wenn auch nur auf der Festplatte).
- **Keine stille Schleife:** Der Datei-Fallback wird pro `--fail-mail`-Aufruf maximal **einmal** versucht. Wenn auch der Datei-Fallback fehlschlägt (z. B. `outbox/` nicht beschreibbar), endet der Aufruf mit Exit 1 und der Fehler wird in stderr geschrieben.
- **Logausgabe:** Die stderr-Zeile des `--fail-mail`-Aufrufs enthält in beiden Fällen (SMTP-OK und Datei-Fallback) eine kurze Meldung, damit `logs/llm_scout_err.log` den Verweis enthält.

### A4. „Kein Report" bleibt kein Fehler

- `send_scout_email.py` (ohne `--dry-run`, ohne `--fail-mail`): Wenn keine Report-Datei für die aktuelle KW existiert, Exit 0 und stderr-Meldung (wie heute). **Keine** Fehler-Mail, keine `.eml`-Ablage.
- `llm_scout.py`: Wenn keine neuen Items gefunden werden, Exit 0 (wie heute). Der Pipeline-Wrapper behandelt Exit 0 als Erfolg und ruft `send_scout_email.py` im Normalmodus auf, der dann mit „keine Datei" Exit 0 endet. Gesamtergebnis: Exit 0, kein E-Mail-Versand, keine Fehler-Mail.

### A5. Pipeline-Wrapper `run_scout_pipeline.sh`

- **Step 1** (Scout) läuft wie heute.
- **Step 1 ≠ 0:**
  1. `echo` des Scout-Exit-Codes nach stderr (wie heute, bleibt).
  2. **Neu:** Aufruf `${PYTHON} scripts/send_scout_email.py --fail-mail --exit-code ${SCOUT_EXIT}`.
  3. Der Exit-Code dieses Aufrufs wird **nicht** an launchd weitergegeben. Der Wrapper gibt den **originalen** `${SCOUT_EXIT}` zurück.
  4. Begründung: launchd soll den echten Fehler sehen. Ob die Fehler-Mail ankam, ist zweitrangig und in den Logs + `outbox/` nachvollziehbar.
- **Step 1 = 0:** Step 2 (Email-Normalmodus) wie heute.
- **Step 2 ≠ 0:** `echo` (wie heute), **kein** `--fail-mail`-Aufruf (verhindert Rekursion, siehe A2), Wrapper gibt `${EMAIL_EXIT}` zurück.
- `set -euo pipefail` bleibt aktiv. Der neue `--fail-mail`-Aufruf wird unter `|| true` oder mit explizitem `|| :` gefangen, damit `set -e` den Wrapper nicht bricht, wenn die Fehler-Mail selbst fehlschlägt.

### A6. `llm_scout.py` – nur Dokumentation, keine Logik

- **Kein Ändern von Logik, Exit-Codes oder Ablauf.**
- **Einzige Änderung:** Ein kurzer Kommentarblock über `main()` (oder in der Modul-Docstring), der die Exit-Code-Semantik dokumentiert: `0 = Erfolg (inkl. keine neuen Items), 1 = kritischer Fehler, 2 = llama-server nicht erreichbar`. Begründung: Die Fehler-Mail (A2) referenziert diese Semantik. Aktuell steht sie nur implizit in der Implementierung (llm_scout.py:389, :223, :318). Ein einzeiliger Kommentar reicht; kein Refactoring.

### A7. Credentials (bleibt)

- Das App-Passwort bleibt im Schlüsselbund (`lab-scout-smtp`), wird im echten Versand **und** im `--fail-mail`-Modus gelesen. Im `--dry-run`-Modus nicht (A1).
- Das Passwort erscheint nicht in Code, Log, PLIST, Doku **oder in `.eml`-Dateien in `outbox/`** (da im Trockenlauf kein Login; im Fehler-Mail-Fallback wird nur die fertige Mail ohne Passwort gespeichert).

### A8. Keine PLIST-Änderung

- `config/launchd/llm_scout.plist` bleibt unverändert. Der Wrapper-Pfad und die Umgebungsvariablen bleiben gleich.

---

## Testplan (ohne echten Versand)

Alle Tests laufen mit dem Projekt-venv und setzen `LAB_DIR` auf ein temporäres Verzeichnis, damit die echten Daten nicht berührt werden. Der Schlüsselbund-Eintrag `lab-scout-smtp` muss **nicht** für Trockenlauf-Tests existieren (A1 verbietet den Zugriff). Für die `--fail-mail`-Tests wird der SMTP-Server per `SCOUT_SMTP_HOST`/`SCOUT_SMTP_PORT` auf einen nicht erreichbaren Port (z. B. `localhost:9`) gelegt, damit der Fallback (A3) deterministisch eintritt, ohne dass der echte Gmail-Server kontaktiert wird. (Die Umgebungsvariablen sind optional und überschreiben die Konstanten; Default bleibt `smtp.gmail.com:587`.)

### T1. Trockenlauf mit bestehendem Report

- **Vorbereitung:** `LAB_DIR=/tmp/scout_test`, Report `llm_scout_kw{aktuelleKW}_{aktuellesJahr}.md` anlegen (Inhalt: beliebiger Markdown-Text mit einer Tabelle und einem Code-Block).
- **Aufruf:** `${PYTHON} scripts/send_scout_email.py --dry-run`
- **Erwartung:**
  - Exit 0.
  - `outbox/llm_scout_kw{KW}_{JJJJ}.eml` existiert.
  - Die Datei beginnt mit `Content-Type: text/html` und enthält die HTML-Tabelle und den `<pre>`-Block.
  - In der Datei ist **keinerlei** Passworteintrag oder `Authorization`-Header.
  - **Kein** TCP-Port 587 wurde geöffnet (per `lsof -i :587` während des Aufrufs oder durch einen Mock-Server, der keine Verbindung sieht, verifizierbar).
  - Kein Aufruf von `security find-generic-password` (verifizierbar durch `strace`/`dtruss` auf macOS oder durch das Setzen eines leeren Schlüsselbund-Eintrags, der nicht existiert – der Test muss trotzdem grün bleiben).

### T2. Trockenlauf ohne Report

- **Vorbereitung:** `LAB_DIR=/tmp/scout_test_2`, `weekly-reports/` leer.
- **Aufruf:** `${PYTHON} scripts/send_scout_email.py --dry-run`
- **Erwartung:** Exit 0, stderr enthält „Keine Bericht-Datei", **keine** `.eml`-Datei in `outbox/`.

### T3. Normalmodus ohne Report (regression)

- **Aufruf:** `${PYTHON} scripts/send_scout_email.py` (ohne Flag)
- **Erwartung:** Exit 0, keine `.eml`-Datei, kein SMTP-Handshake (wie T2, aber ohne `--dry-run`).

### T4. Fehler-Mail wird gebaut und abgelegt (SMTP-Fehler simuliert)

- **Vorbereitung:** `LAB_DIR=/tmp/scout_test_4`, `SCOUT_SMTP_HOST=localhost`, `SCOUT_SMTP_PORT=9` (kein Server dort).
- **Aufruf:** `${PYTHON} scripts/send_scout_email.py --fail-mail --exit-code 2`
- **Erwartung:**
  - Exit 0 (Datei-Fallback erfolgreich).
  - `outbox/scout_error_{JJJJMMDD}_{HHMM}.eml` existiert.
  - Betreff enthält `LLM Scout FEHLER` und `Exit-Code 2`.
  - Inhalt enthält „llama-server nicht erreichbar".
  - stderr-Meldung verweist auf `outbox/`.

### T5. Fehler-Mail mit Exit-Code 1

- **Vorbereitung:** wie T4, `--exit-code 1`.
- **Erwartung:** wie T4, aber Inhalt enthält „Kritischer Fehler in der Scout-Pipeline".

### T6. Fehler-Mail mit unbekanntem Exit-Code

- **Vorbereitung:** wie T4, `--exit-code 7`.
- **Erwartung:** wie T4, aber Inhalt enthält „Unbekannter Exit-Code".

### T7. Pipeline: Scout-Fehler → Fehler-Mail → korrekter Exit-Code

- **Vorbereitung:** `LAB_DIR=/tmp/scout_test_7`, `SCOUT_SMTP_HOST=localhost:9`. `llm_scout.py` wird per `LLAMA_SERVER_URL=http://localhost:9` auf einen nicht erreichbaren Server gezeigt (→ Exit 2).
- **Aufruf:** `bash scripts/run_scout_pipeline.sh`
- **Erwartung:**
  - Wrapper-Exit-Code = **2** (der originale Scout-Exit, nicht der des Fehler-Mail-Versands).
  - `outbox/` enthält eine `scout_error_*.eml`.
  - `logs/llm_scout_err.log` enthält den Verweis auf `outbox/`.

### T8. Pipeline: Scout-Exit 0, keine neuen Items → keine Mail, keine Fehler-Mail

- **Vorbereitung:** `llm_scout.py` simuliert „keine neuen Items" (Exit 0). Kein Report in `weekly-reports/`.
- **Aufruf:** `bash scripts/run_scout_pipeline.sh`
- **Erwartung:** Wrapper-Exit-Code = 0. Keine `.eml`-Datei in `outbox/`. Kein SMTP-Handshake.

### T9. Pipeline: Scout-OK, Report vorhanden, Email-Fehler → keine Fehler-Mail (Rekursions-Schutz)

- **Vorbereitung:** `LAB_DIR=/tmp/scout_test_9`, Report vorhanden, `SCOUT_SMTP_HOST=localhost:9`.
- **Aufruf:** `bash scripts/run_scout_pipeline.sh`
- **Erwartung:**
  - Step 1 Exit 0, Step 2 (Email) Exit 1 (SMTP-Fehler).
  - Wrapper-Exit-Code = 1.
  - `outbox/` enthält **keine** `scout_error_*.eml` (Rekursions-Schutz greift).
  - stderr enthält die Email-Fehlermeldung, aber keinen `--fail-mail`-Aufruf.

### T10. Trockenlauf lässt echte Daten unberührt

- **Vorbereitung:** `LAB_DIR` zeigt auf das echte Repo-Verzeichnis. Eine echte `llm_scout_kw{KW}_{JJJJ}.md` existiert.
- **Aufruf:** `${PYTHON} scripts/send_scout_email.py --dry-run`
- **Erwartung:** Exit 0. Die echte `.md`-Datei ist unverändert (mtime/Inhalt). In `outbox/` liegt die neue `.eml`. **Kein** echter Mailversand.

---

## Abhängigkeiten

- `markdown` (bereits im `.venv`, keine neue Abhängigkeit).
- Keine neuen Pip-Pakete.
- `email.mime` und `smtplib` sind Standardbibliothek.

## Offene Fragen

- Keine. Die SMTP-Host/Port-Override-Variablen (`SCOUT_SMTP_HOST`, `SCOUT_SMTP_PORT`) sind ein Test-Feature und kein Produkt-Feature; sie überschreiben nur die bestehenden Konstanten und haben keine eigene Doku.

## Abweichende Meinung (Review-Instanz)

- **Fehler-Mail via SMTP ist der schwächste Punkt des Vorhabens.** Der häufigste Pipeline-Fehler (llama-server down, Exit 2) und der häufigste Email-Fehler (SMTP-Auth/DNS) überschneiden sich nicht – aber wenn beides gleichzeitig auftritt (Server down **und** Gmail nicht erreichbar), hilft die Datei-Ablage (A3) nur, wenn jemand danach schaut. Das Vorhaben löst „Statt Schweigen" nicht in diesem Fall. Akzeptiert als bewusste Entscheidung: ein zweiter Kanal war explizit ein Nicht-Ziel.
- **Trockenlauf deckt den SMTP-Handshake nicht ab.** Das ist eine Komfort-Funktion, kein Sicherheitsgewinn. Der echte Versand (einmalig, von Hawe) ist der einzige Test des Versandpfads. Die Spec stellt das klar, damit die Erwartung nicht enttäuscht wird.
- **Exit-Code-Semantik war ungeschrieben.** Sie existierte nur implizit in `llm_scout.py`. Die Spec verankert sie jetzt in A2 (Tabelle) und A6 (Doku-Kommentar). Ohne diese Verankerung wäre die Fehler-Mail-Meldung willkürlich.
