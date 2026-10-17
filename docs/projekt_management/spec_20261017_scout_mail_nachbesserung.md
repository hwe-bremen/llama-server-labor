# Spec: LLM Scout E-Mail – Nachbesserung

**Datum:** 2026-10-17
**Review-Instanz:** Qwen3.6-27B (unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL)
**Vorgänger-Spec:** `spec_20261017_scout_mail_trockenlauf.md`
**Vorgänger-Verdikt:** `verdict_20261017_scout_mail_trockenlauf_qwen38-27b_lauf2.md` (PASS mit 5 Befunden)
**Geprüfter Code:** `scripts/send_scout_email.py`, `scripts/run_scout_pipeline.sh`

## Ziel

Die fünf Befunde des Verdikts lauf2 (N1–N6) beseitigen. Der Funktionsumfang der Vorgängerspec (A1–A8) bleibt unverändert.

## Nicht-Ziele

- Kein echtes Mailversand-Testing. Den einen echten Versand macht Hawe selbst.
- Keine Änderung an `llm_scout.py` (Exit-Code-Doku aus A6 steht, keine weiteren Änderungen nötig).
- Keine PLIST-Änderung.
- Keine neue Abhängigkeit – `markdown` bleibt das einzige externe Paket.

---

## Anforderungen

### N1 [HOCH] SMTP-Timeout

**Problem:** `smtplib.SMTP(SMTP_HOST, SMTP_PORT)` in `send_email_smtp()` (Zeile 192) hat kein Timeout. Ein SMTP-Server, der die Verbindung annimmt und dann schweigt, lässt den Prozess unbegrenzt hängen. Der Datei-Fallback (A3) greift nie, der launchd-Job endet nie, kein Exit-Code kommt heraus. Vorbestehend aus der ursprünglichen Umsetzung, aber jetzt kritisch, weil der Fehler-Mail-Pfad auf den Fallback angewiesen ist.

**Anforderung:**
- `smtplib.SMTP()` erhält ein explizites `timeout=`-Argument (empfohlen: 30 s). Das Timeout gilt für den gesamten Socket-Verbindungsversuch und alle nachfolgenden Operationen auf derselben Verbindung.
- Ein Timeout löst `smtplib.timeout` (bzw. `socket.timeout`) aus, das vom bestehenden `except Exception` in `mode_fail_mail()` gefangen wird → Datei-Fallback tritt ein.
- Im Normalmodus (`mode_normal()`) landet das Timeout ebenfalls im `except Exception` → Exit 1, Fehlermeldung in stderr.

**Betroffene Stelle:** `scripts/send_scout_email.py`, Funktion `send_email_smtp()`, Zeile 192: `with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:`.

**Akzeptanzkriterium:**
- `send_email_smtp()` bricht nach maximal 30 s ab, wenn der Server antwortet, aber nicht reagiert.
- Im `--fail-mail`-Modus: Datei-Fallback wird ausgelöst, `.eml` wird abgelegt, Exit 0.
- Im Normalmodus: Exit 1, stderr-Meldung enthält Timeout-Information.

**Test ohne echten Versand:**
- Python-Testserver, der die Verbindung annimmt und dann schweigt (kein Daten senden, kein Close):
  ```python
  # test_smtp_timeout.py (nur für den Test, nicht ins Repo)
  import socket, threading
  s = socket.socket(); s.bind(('127.0.0.1', 2599)); s.listen(1)
  conn, _ = s.accept()  # Verbindung annehmen, dann schweigen
  # Hauptprozess: send_scout_email.py mit SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=2599
  # Erwartung: Abbruch nach ~30s, kein ewiges Hängen
  ```
- Aufruf: `SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=2599 timeout 35 .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2`
  - `timeout 35` als äußere Sicherung: wenn der Prozess nach 35 s noch läuft, ist das Timeout nicht wirksam.
  - Erwartung: Exit 0 (Fallback erfolgreich), `outbox/scout_error_*.eml` existiert, Laufzeit < 35 s.
- Gleiches im Normalmodus mit bestehendem Report: Exit 1, stderr enthält Timeout.

---

### N2 [NIEDRIG] SCOUT_SMTP_PORT-Validierung beim Import

**Problem:** `SMTP_PORT = int(os.getenv("SCOUT_SMTP_PORT", "587"))` (Zeile 39) läuft modulglobal beim Import. Ist die Umgebungsvariable gesetzt, aber leer oder nicht numerisch, stirbt der Prozess mit `ValueError` – in **allen** Modi, auch `--dry-run`, bevor `argparse` läuft. Kein Schlüsselbund-Zugriff (Prozess stirbt vorher), kein Datenverlust, aber ein unerwarteter Traceback statt einer sauberen Fehlermeldung.

**Anforderung:**
- `SMTP_PORT` wird nicht mehr beim Import geparst. Stattdessen: Lazy-Evaluation in `send_email_smtp()` – dort wird `os.getenv("SCOUT_SMTP_PORT", "587")` gelesen, mit `int()` geparst, und ein `ValueError` wird wie jeder andere SMTP-Fehler behandelt.
- Im `--fail-mail`-Modus landet ein Parse-Fehler im Datei-Fallback (Exit 0, `.eml` abgelegt).
- Im Normalmodus endet ein Parse-Fehler mit Exit 1 und stderr-Meldung.
- Im `--dry-run`-Modus wird `SMTP_PORT` nie gelesen → kein Crash.

**Betroffene Stelle:** `scripts/send_scout_email.py`, Zeile 39: `SMTP_PORT = int(os.getenv("SCOUT_SMTP_PORT", "587"))`.

**Akzeptanzkriterium:**
- `SCOUT_SMTP_PORT="" .venv/bin/python3 scripts/send_scout_email.py --dry-run` → Exit 0, Trockenlauf läuft normal.
- `SCOUT_SMTP_PORT="" .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2` → Exit 0, Fallback-Datei abgelegt, stderr enthält Parse-Fehler.
- `SCOUT_SMTP_PORT="abc" .venv/bin/python3 scripts/send_scout_email.py` → Exit 1, stderr enthält Fehlermeldung (kein Traceback).

**Test ohne echten Versand:**
- Drei Aufrufe wie oben, jeweils mit `--dry-run`, `--fail-mail` und Normalmodus. Kein SMTP-Server nötig.

---

### N3 [MITTEL] --dry-run gewinnt gegen --fail-mail

**Problem:** Wenn `--dry-run` und `--fail-mail` gleichzeitig übergeben werden, entscheidet die `if/elif`-Reihenfolge in `main()` (Zeile 297–301), dass `--fail-mail` gewinnt. Das führt zu einem echten SMTP-Versand-Versuch – im Widerspruch zum Sicherheitsversprechen des Trockenlaufs.

**Anforderung:**
- `--dry-run` hat Vorrang vor `--fail-mail`. Wenn beide Flags gesetzt sind, wird der Trockenlauf ausgeführt. Der `--exit-code`-Parameter wird ignoriert.
- Eine Warnung in stderr informiert den Nutzer: „Trockenlauf aktiv – Fehler-Mail-Versand übersprungen."

**Betroffene Stelle:** `scripts/send_scout_email.py`, Funktion `main()`, Zeilen 297–301 (if/elif-Dispatch).

**Akzeptanzkriterium:**
- `--dry-run --fail-mail --exit-code 2` → Trockenlauf wird ausgeführt, kein SMTP-Handshake, Exit 0.
- stderr enthält Warnung „Trockenlauf aktiv".
- `outbox/` enthält die normale `.eml` (vom Trockenlauf), keine `scout_error_*.eml`.

**Test ohne echten Versand:**
- Aufruf mit `--dry-run --fail-mail --exit-code 2` und bestehendem Report.
- Erwartung: Exit 0, `outbox/llm_scout_kw{KW}_{JJJJ}.eml` existiert, stderr enthält Warnung.
- Kein TCP-Port 587 (oder konfigurierter Test-Port) wurde geöffnet.

---

### N4 [NIEDRIG] Fallback-Dateiname mit Sekunden

**Problem:** Der Fallback-Dateiname `scout_error_{JJJJMMDD}_{HHMM}.eml` (Zeile 259) ist nur minutengenau. Zwei `--fail-mail`-Ausfälle in derselben Minute überschreiben den ersten. Bei wöchentlichem Rhythmus unwahrscheinlich, aber bei manuellem Nachlauf oder Debugging relevant.

**Anforderung:**
- Dateiname wird sekundengenau: `scout_error_{JJJJMMDD}_{HHMMSS}.eml`.
- Bei bereits existierender Datei (gleicher Sekundenstempel, z. B. bei extrem schnellem Nachlauf) wird ein Zähler angehängt: `_1`, `_2` usw., bis ein freier Name gefunden wird.

**Betroffene Stelle:** `scripts/send_scout_email.py`, Funktion `mode_fail_mail()`, Zeile 259: `eml_filename = f"scout_error_{now.strftime('%Y%m%d')}_{now.strftime('%H%M')}.eml"`.

**Akzeptanzkriterium:**
- Einzelner Aufruf: `scout_error_20261017_080030.eml`.
- Zwei schnelle Aufrufe in derselben Sekunde: `scout_error_20261017_080030.eml` und `scout_error_20261017_080030_1.eml`.
- Keine Dateiüberschreibung.

**Test ohne echten Versand:**
- `SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9 .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2` zweimal nacheinander (Sekunde != 0).
- Erwartung: Zwei verschiedene Dateien in `outbox/`, Dateiname enthält Sekunden.
- Für Zähler-Test: Python-Skript, das `datetime.now` mockt auf denselben Timestamp, und zwei Aufrufe von `save_email_to_file()` mit gleichem Namen ausführt.

---

### N5 [MITTEL] Pipeline-Schalter --dry-run

**Problem:** `run_scout_pipeline.sh` hat keinen Trockenlauf-Schalter. Pipeline-Tests sind nur über `SCOUT_SMTP_HOST`-Umleitung sicher – aufwendig und fehleranfällig.

**Anforderung:**
- Neuer Shell-Schalter `--dry-run` für `run_scout_pipeline.sh`.
- Mit `--dry-run`:
  - Step 1 (Scout) läuft wie normal. Der Scout selbst hat keinen Trockenlauf – er generiert den Bericht wie immer.
  - Step 2 (Email) wird mit `--dry-run` aufgerufen: `${PYTHON} scripts/send_scout_email.py --dry-run`.
  - Bei Scout-Fehler (Step 1 ≠ 0): **kein** `--fail-mail`-Aufruf (Trockenlauf-Modus: kein SMTP). Stattdessen: stderr-Meldung „Trockenlauf: Fehler-Mail übersprungen (Scout Exit-Code ${SCOUT_EXIT})".
  - Pipeline-Exit-Code bleibt der originale Scout-Exit-Code (oder 0 bei Scout-Erfolg).
- Ohne `--dry-run`: Verhalten exakt wie heute (keine Regression).

**Betroffene Stelle:** `scripts/run_scout_pipeline.sh`, ab Zeile 21 (Step 1) und Zeile 36 (Step 2).

**Akzeptanzkriterium:**
- `bash scripts/run_scout_pipeline.sh --dry-run` mit bestehendem Report: Exit 0, `outbox/llm_scout_kw{KW}_{JJJJ}.eml` existiert, kein SMTP-Handshake.
- `bash scripts/run_scout_pipeline.sh --dry-run` mit Scout-Fehler: Exit-Code = Scout-Exit, stderr enthält „Fehler-Mail übersprungen", keine `scout_error_*.eml`.
- `bash scripts/run_scout_pipeline.sh` (ohne Flag): Verhalten wie heute.

**Test ohne echten Versand:**
- Trockenlauf mit erfolgreichem Scout: wie oben.
- Trockenlauf mit Scout-Fehler: `LLAMA_SERVER_URL=http://localhost:9 bash scripts/run_scout_pipeline.sh --dry-run` → Exit 2, stderr enthält „Fehler-Mail übersprungen", `outbox/` leer (kein Report vorhanden bei Exit 2, und `--fail-mail` wird nicht aufgerufen).

---

### N6 [NIEDRIG] import markdown lazy

**Problem:** `import markdown` steht modulglobal (Zeile 20). Fehlt das Paket (z. B. auf einer Maschine ohne venv), stirbt der Import – auch in Modi, die `markdown` nicht brauchen. Konkret: `--fail-mail` baut die Fehler-Mail aus reinen Parametern, ohne Markdown zu lesen. Der Import-Crash verhindert auch die Fehler-Mail.

**Anforderung:**
- `import markdown` wird aus dem modulglobalen Bereich entfernt und in `build_email_message()` verschoben (lokaler Import).
- `build_fail_email()` importiert `markdown` nicht.
- Fehlt `markdown` im `--fail-mail`-Modus: kein Crash, Fehler-Mail wird gebaut und versendet (oder gefallbackt).
- Fehlt `markdown` im Normal- oder Trockenlauf: `build_email_message()` wirft `ModuleNotFoundError`, das vom bestehenden `except Exception` in `mode_normal()`/`mode_dry_run()` gefangen wird → Exit 1, stderr-Meldung.

**Betroffene Stelle:** `scripts/send_scout_email.py`, Zeile 20: `import markdown` (global) und Zeile 116: `markdown.markdown(...)` (Verwendung in `build_email_message()`).

**Akzeptanzkriterium:**
- `--fail-mail` funktioniert ohne `markdown`-Paket (simulierbar durch Umbenennung des Pakets im venv oder durch einen temporären `sys.path`-Trick).
- `--dry-run` mit fehlendem `markdown`: Exit 1, stderr enthält „ModuleNotFoundError".
- Normalmodus mit vorhandenem `markdown`: keine Regression.

**Test ohne echten Versand:**
- `--fail-mail`-Test: `SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9` → Fallback. Vorher: `markdown`-Paket im venv umbenennen (`lib/python3.x/site-packages/markdown` → `markdown.bak`). Aufruf: `.venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2` → Exit 0, Fallback-Datei existiert. Danach: Paket zurückbenennen.
- Alternativ (ohne Paket-Manipulation): Test-Skript, das `sys.modules["markdown"]` auf `None` setzt und dann `send_scout_email.py` via `runpy` aufruft.

---

## Wechselwirkungen

| Kombination | Bewertung |
|---|---|
| N1 (Timeout) + N2 (lazy Port) | Kein Konflikt. Timeout wird in `send_email_smtp()` gesetzt, Port wird dort lazy geparst. Beide Änderungen im selben Funktionsumfang. |
| N1 (Timeout) + N4 (Sekunden-Dateiname) | Kein Konflikt. Timeout beschleunigt den Fallback-Eintritt; Sekunden verhindern Überschreibung. |
| N3 (dry-run gewinnt) + N5 (Pipeline --dry-run) | Synergie. Pipeline-Schalter setzt `--dry-run` am Email-Skript; N3 stellt sicher, dass dieser Flag auch gegen `--fail-mail` gewinnt. |
| N2 (lazy Port) + N6 (lazy markdown) | Kein Konflikt. Beide verschieben modulglobale Effekte in die jeweilige Funktion. |
| N5 (Pipeline dry-run, kein fail-mail) + N3 (dry-run gewinnt) | Konsistent. Pipeline überspringt `--fail-mail` ganz; N3 ist eine zusätzliche Absicherung, falls jemand das Python-Skript manuell mit beiden Flags aufruft. |
| Timeout (N1) + Pipeline-Exit-Code | Kein Konflikt. Timeout löst Exception → Fallback (Exit 0 im `--fail-mail`-Modus) → Pipeline gibt originalen Scout-Exit weiter. Das Timeout ändert nur die Dauer, nicht den Exit-Pfad. |

---

## Testplan (ohne echten Versand)

Alle Tests laufen mit dem Projekt-venv und setzen `LAB_DIR` auf ein temporäres Verzeichnis.

### NT1. SMTP-Timeout (N1)

- **Vorbereitung:** Python-Socket-Server, der verbindet und schweigt (Port 2599). `timeout 35` als äußere Sicherung.
- **Aufruf:** `SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=2599 timeout 35 .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2`
- **Erwartung:** Exit 0, `outbox/scout_error_*.eml` existiert, Laufzeit < 35 s.

### NT2. SMTP-Timeout im Normalmodus (N1)

- **Vorbereitung:** Wie NT1, Report vorhanden.
- **Aufruf:** `SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=2599 timeout 35 .venv/bin/python3 scripts/send_scout_email.py`
- **Erwartung:** Exit 1, stderr enthält Timeout-Information, keine `.eml`.

### NT3. Dry-run mit leerem SCOUT_SMTP_PORT (N2)

- **Aufruf:** `SCOUT_SMTP_PORT="" .venv/bin/python3 scripts/send_scout_email.py --dry-run`
- **Erwartung:** Exit 0, Trockenlauf normal, keine Exception.

### NT4. Fail-mail mit leerem SCOUT_SMTP_PORT (N2)

- **Aufruf:** `SCOUT_SMTP_PORT="" .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2`
- **Erwartung:** Exit 0, Fallback-Datei, stderr enthält Parse-Fehler.

### NT5. Dry-run + fail-mail (N3)

- **Aufruf:** `.venv/bin/python3 scripts/send_scout_email.py --dry-run --fail-mail --exit-code 2`
- **Erwartung:** Exit 0, Trockenlauf-Datei in `outbox/`, stderr-Warnung, kein SMTP.

### NT6. Pipeline --dry-run (N5)

- **Vorbereitung:** Report vorhanden.
- **Aufruf:** `bash scripts/run_scout_pipeline.sh --dry-run`
- **Erwartung:** Exit 0, `outbox/llm_scout_kw{KW}_{JJJJ}.eml` existiert, kein SMTP.

### NT7. Pipeline --dry-run mit Scout-Fehler (N5)

- **Vorbereitung:** `LLAMA_SERVER_URL=http://localhost:9`.
- **Aufruf:** `LLAMA_SERVER_URL=http://localhost:9 bash scripts/run_scout_pipeline.sh --dry-run`
- **Erwartung:** Exit 2, stderr „Fehler-Mail übersprungen", keine `scout_error_*.eml`.

### NT8. Fallback-Dateiname mit Sekunden (N4)

- **Aufruf:** Zwei schnelle `--fail-mail`-Aufrufe mit `SCOUT_SMTP_PORT=9`.
- **Erwartung:** Zwei verschiedene Dateien, Dateiname enthält Sekunden.

### NT9. Fail-mail ohne markdown-Paket (N6)

- **Vorbereitung:** `markdown`-Paket im venv temporär umbenennen.
- **Aufruf:** `SCOUT_SMTP_HOST=localhost SCOUT_SMTP_PORT=9 .venv/bin/python3 scripts/send_scout_email.py --fail-mail --exit-code 2`
- **Erwartung:** Exit 0, Fallback-Datei existiert, kein Import-Crash.

---

## Offene Fragen

- Keine.

## Abweichende Meinung (Review-Instanz)

- **N6 (lazy markdown) ist korrekt, aber geringen Nutzens.** Im produktiven Einsatz läuft alles im venv mit installiertem `markdown`. Der Nutzen zeigt sich nur bei fehlendem Paket – ein Konfigurationsfehler, kein Laufzeitfehler. Ich halte die Änderung für sauber, weil sie die Modus-Isolation verbessert, aber sie hat die niedrigste Priorität aller Punkte.
- **N4 (Sekunden im Dateiname) ist sinnvoll, aber der Zähler (`_1`, `_2`) ist Overengineering.** Bei wöchentlichem Rhythmus und sekundengenauem Stempel ist eine Kollision praktisch unmöglich. Ich halte den Zähler für falsch: Er macht den Dateinamen unvorhersehbar und erschwert das Parsen in Logs oder Skripten. Sekunden allein reichen. Wenn Hawe den Zähler trotzdem will: kein Einwand gegen die Umsetzbarkeit, aber ich halte ihn für unnötig.
- **N1 (Timeout) ist der einzige Punkt, der wirklich kritisch ist.** Die anderen fünf sind Robustheitsverbesserungen, die den Code besser machen, aber keinen Produktionsfehler beheben. Ich würde sie in dieser Reihenfolge umsetzen: N1 → N3 → N5 → N2 → N4 → N6. Aber die Spec verlangt alle – kein Widerspruch dazu.

---

## Ergänzung nach Gegenprüfung (Hawe/Claude, 17.10. 16:15) — gilt vor dem Text oben

Der Text oben bleibt unverändert. Wo er dieser Ergänzung widerspricht, gilt die Ergänzung.

**E1 — Pipeline-Trockenlauf darf die echten Scout-Daten nicht verändern (zu N5, wichtig).**
`run_scout_pipeline.sh` setzt `LAB_DIR` fest auf `agents/llm_scout/data`. Der Scout trägt jeden gefundenen Eintrag in `llm_scout.db` als verarbeitet ein. Ein Pipeline-Trockenlauf mit funktionierendem Router würde also echte Einträge „verbrauchen". Der nächste echte Montagslauf fände dann nichts Neues und bliebe still (vgl. B2). Außerdem greift „Alle Tests mit temporärem `LAB_DIR`" für NT6/NT7 nicht, weil der Wrapper den Wert überschreibt.
- Anforderung: Der Wrapper übernimmt ein vorher gesetztes `LAB_DIR` (`export LAB_DIR="${LAB_DIR:-${REPO_ROOT}/agents/llm_scout/data}"`).
- Mit `--dry-run` und ohne gesetztes `LAB_DIR` legt der Wrapper ein temporäres Verzeichnis an (`mktemp -d`), kopiert `llm_scout.db` hinein, falls vorhanden, und nutzt dieses. Den Pfad gibt er aus. Die echte DB und `weekly-reports/` bleiben unberührt.
- Test (zusätzlich zu NT6): Prüfsumme von `agents/llm_scout/data/llm_scout.db` vor und nach `run_scout_pipeline.sh --dry-run` vergleichen; sie muss gleich bleiben.

**E2 — Testserver für N1 muss offen bleiben (zu N1/NT1/NT2).**
Das Beispielskript nimmt die Verbindung an und endet sofort. Damit wird die Verbindung geschlossen, der Client sieht sofort einen Abbruch, und der Test wird grün, ohne dass ein Timeout gemessen wurde. Der Testserver muss die Verbindung halten (z. B. `time.sleep(120)` nach `accept()`) und für NT2 erneut annehmen (Schleife). Zusätzlich die Laufzeit messen: Abbruch frühestens nach etwa 30 s, also nicht sofort.
Hinweis: `timeout=` in `smtplib.SMTP` gilt je Socket-Operation, nicht für die Gesamtdauer. Für den Fall „Server schweigt" reicht das.

**E3 — N4: Zähler bleibt (Widerspruch zur abweichenden Meinung).**
Die Anforderung lautet „keine Überschreibung". Sekunden allein garantieren das nicht, und NT8 („zwei schnelle Aufrufe") landet oft in derselben Sekunde, der Test würde also ohne Zähler scheitern. Umsetzung: Datei mit Modus `"x"` (exklusiv) anlegen; bei `FileExistsError` `_1`, `_2` … anhängen.

**E4 — N2: Port vor dem Passwort prüfen.**
In `send_email_smtp()` den Port parsen, **bevor** `get_password()` aufgerufen wird. Ein ungültiger Port soll den Schlüsselbund gar nicht erst berühren.

**E5 — N6/NT9: venv nicht anfassen.**
Kein Umbenennen im venv. Nur die Variante über `sys.modules["markdown"] = None` + `runpy` (bzw. einen kleinen Testaufruf).

**E6 — Korrekturen:**
- Zeilennummern: `import markdown` steht in Zeile 28 (nicht 20), `markdown.markdown(` in Zeile 95 (nicht 116).
- Es sind sechs Befunde (N1–N6), nicht fünf.

**E7 — Schlüsselbund in Tests.** Normalmodus-Tests (NT2, N2 „abc") lesen auf dem Mac den echten Schlüsselbund-Eintrag. Das ist erlaubt, ein Versand ist ausgeschlossen, weil kein Login am Testserver zustande kommt. Im Handover ausdrücklich nennen.
