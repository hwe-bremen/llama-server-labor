# Spec: scout_kw_doppelversand

- **Datum:** 2026-10-18
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Betroffene Dateien:** `agents/llm_scout/llm_scout.py`, `scripts/send_scout_email.py`, `scripts/run_scout_pipeline.sh` (alle vollständig gelesen), `config/launchd/llm_scout.plist` (gelesen), `docs/projekt_management/_vorlage_spec.md` (gelesen)

## Ziel

Die wöchentliche Scout-Mail wird (1) um den ISO-Jahreswechsel herum nicht still ausgelassen, wenn ein Bericht existiert aber nicht gefunden wird, und (2) in derselben Kalenderwoche nicht zweimal gesendet, wenn die Pipeline ein zweites Mal läuft. Dazu bekommt der Versand einen persistenten, pro ISO-Kalenderwoche eindeutigen Versand-Nachweis, und Scout und Versand nutzen eine gemeinsame Funktion für den Wochenschlüssel im Dateinamen.

## Nicht-Ziele

- Die Scout-DB (`llm_scout.db`) und die `processed_items`-Logik in `llm_scout.py` bleiben unberührt. Der Scout markiert weiterhin nur verarbeitete URLs; der Versand-Nachweis ist eine separate Zustandsquelle.
- Der Fehler-Mail-Pfad (`--fail-mail`) und sein Datei-Fallback werden nicht geändert.
- Die `SCOUT_ALLOW_SEND`-Sperre bleibt, wie sie ist.
- Keine Änderungen an der launchd-plist.
- **Keine** dedizierte Fehler-Mail für den Exit-Code 3 (s. A4).

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?**
  - **Echte E-Mail:** `send_scout_email.py` im Normalmodus sendet per SMTP an `smtp.gmail.com` (Default) an `askvalentinai@gmail.com`. Das ist die kritischste Außenwirkung.
  - **Schlüsselbund:** `get_password()` ruft `security find-generic-password -s lab-scout-smtp -w` auf und liest das App-Passwort. Wird bei jedem echten SMTP-Versand berührt.
  - **Netzwerk:** SMTP-Verbindung zum konfigurierten Host (Default Gmail), im Test gegen `127.0.0.1`/`localhost` auf einem lokalen Port.
  - **Keine echten Daten/DB:** Die neue Zustandsdatei liegt im `LAB_DIR` und berührt weder `llm_scout.db` noch sonstige echte Daten.
- **Technische Sperre für Tests:**
  - `LAB_DIR` auf ein temporäres Verzeichnis (`tempfile.mkdtemp()`), sodass alle Zustandsdateien, Berichte und Outbox-Dateien in der Isolation liegen und die echte Datenbank unter `agents/llm_scout/data/` nicht berührt wird.
  - **`get_password()` und `smtplib.SMTP` werden in jedem Test per `unittest.mock` ersetzt.** Kein Test ruft die echte `security`-Funktion auf und öffnet keine echte TCP-Verbindung. `SCOUT_SMTP_HOST` und `SCOUT_SMTP_PORT` werden trotzdem auf `127.0.0.1` bzw. einen toten Port gesetzt, als zweite Sicherungsebene.
  - **Kein Test darf `SCOUT_ALLOW_SEND=1` mit dem echten `smtp.gmail.com` kombinieren.**
  - **Kein Test nutzt `aiosmtpd` oder einen echten lokalen SMTP-Server.**

## Anforderungen

### A1: Eindeutiger Versand-Nachweis pro ISO-Kalenderwoche (Zustandsquelle)
- **Anforderung:** `send_scout_email.py` speichert nach jedem **erfolgreichen** SMTP-Versand eine Zustandszeile in einer Datei im `LAB_DIR` (empfohlen: `weekly-reports/.sent_state`), die den Wochenschlüssel (ISO-Jahr + ISO-Nummer) und das Sendedatum enthält. Der Nachweis wird **nur** geschrieben, nachdem `sendmail()` erfolgreich zurückgekehrt ist.
- **Stelle:** `scripts/send_scout_email.py`, neue Funktion `record_sent_week()` bzw. `SENT_STATE_FILE`-Pfad in `BASE_DIR`; Aufruf in `mode_normal()` nach `send_email_smtp()`.
- **Akzeptanz:** Nach erfolgreichem Versand existiert die Zustandsdatei und enthält genau eine Zeile für die gerade gesendete ISO-Woche. Vor dem ersten Versand existiert die Datei nicht (oder ist leer).

### A2: Zweitlauf in derselben ISO-Woche sendet nicht erneut (Doppelversand-Sperre)
- **Anforderung:** `mode_normal()` prüft **vor** dem Versand, ob die aktuelle ISO-Kalenderwoche bereits im Versand-Nachweis steht. Ist sie das, wird **keine** Mail gesendet, keine Zustandszeile angehängt, und die Funktion gibt Exit-Code 0 zurück mit einer klaren Meldung (z. B. „KW bereits gesendet, kein Zweitversand“).
- **Stelle:** `scripts/send_scout_email.py`, `mode_normal()`.
- **Akzeptanz:** Läuft `send_scout_email.py` normal zweimal in derselben ISO-Woche, wird genau **eine** Mail gesendet. Der zweite Lauf endet mit Exit-Code 0 und meldet, dass bereits gesendet wurde. Es entsteht keine zweite Zustandszeile für dieselbe Woche.

### A3: „Bericht nicht gefunden“ bleibt nicht still, wenn die Woche nicht abgedeckt ist
- **Anforderung:** `mode_normal()` unterscheidet zwei Fälle, wenn `find_current_report()` `None` liefert:
  - Die aktuelle ISO-Woche ist **bereits gesendet** (steht im Nachweis) → Exit-Code 0, Meldung „bereits gesendet“, kein Fehler.
  - Die aktuelle ISO-Woche ist **nicht** gesendet und es fehlt der Bericht → das ist ein **Fehler**: Exit-Code **3** (neuer, dedizierter Code für „Bericht fehlt, Woche nicht abgedeckt“), Meldung auf stderr. Damit wird der Stillstand am Jahreswechsel sichtbar.
- **Abgrenzung „keine neuen Items" vs. „Bericht fehlt":** `llm_scout.py` liefert bei „keine neuen Items" ebenfalls Exit 0 und schreibt keine Bericht-Datei. `send_scout_email.py` kann diese beiden Zustände **nicht** voneinander unterscheiden – und muss das auch nicht. Die Unterscheidung macht der **Zustand**: Bericht-Datei existiert → senden; keine Datei → auf die Zustandsdatei schauen. Ein Scout-Lauf ohne neue Items in einer Woche, die **noch nicht** gesendet wurde, führt damit korrekt zu Exit 3 – das ist kein Fehlalarm, sondern der Hinweis, dass die Woche unvollständig abgedeckt ist (der Scout hat keine neue Items gefunden, aber auch keine Mail wurde gesendet). In einer Woche, die **bereits** gesendet wurde, führt derselbe Zustand zu Exit 0 (s. A3 erster Fall).
- **Stelle:** `scripts/send_scout_email.py`, `mode_normal()`.
- **Akzeptanz:** Ohne Bericht und ohne gesendete Woche liefert `mode_normal()` Exit-Code 3. Mit Bericht liefert es 0 (oder 1 bei SMTP-Fehler). Die Pipeline (`run_scout_pipeline.sh`) gibt diesen Exit-Code 3 an launchd weiter (s. A4).

### A4: Pipeline gibt den neuen Exit-Code 3 an launchd weiter und macht ihn sichtbar
- **Anforderung:** `run_scout_pipeline.sh` übergibt den Exit-Code von `send_scout_email.py` (Schritt 2) unverändert an launchd, auch wenn er 3 ist. Es wird **keine** Fehler-Mail für Exit-Code 3 ausgelöst (denn „keine Items diese Woche" wäre sonst ebenfalls eine Mail, und wir wollten keine zusätzliche Mail). Stattdessen schreibt `run_scout_pipeline.sh` bei **jedem** Lauf (Erfolg und Fehler) eine Zustandszeile in eine Pipeline-Lauf-Datei (`LAB_DIR/pipeline_runs.log`), die den Scout-Exit-Code, den Mail-Exit-Code und das Gesamtergebnis enthält. Damit ist der Exit 3 in dieser Datei und in den launchd-Logs (`llm_scout_err.log`) sichtbar.
- **Stelle:** `scripts/run_scout_pipeline.sh`, Schritt 2 (`EMAIL_EXIT`) und neuer Schreibblock in die Lauf-Datei.
- **Akzeptanz:** `bash run_scout_pipeline.sh` (ohne `--dry-run`) mit fehlendem Bericht und ungesendeter Woche beendet sich mit Exit-Code 3. Die Datei `LAB_DIR/pipeline_runs.log` enthält eine Zeile mit `EMAIL_EXIT=3`. Es wird **keine** Fehler-Mail ausgelöst. Mit `--dry-run` bleibt der Dry-Run-Pfad bestehen (s. A5).

### A5: Trockenlauf (`--dry-run`) bleibt vom Versand-Nachweis isoliert
- **Anforderung:** `mode_dry_run()` liest und schreibt **nicht** den Versand-Nachweis. Der Dry-Run speichert weiterhin nur die `.eml` in der Outbox und meldet „Trockenlauf“. Er sendet nie per SMTP und berührt nie die Zustandsdatei. So bleibt der Dry-Run mit temporärem `LAB_DIR` (mktemp) vollständig konsistent.
- **Stelle:** `scripts/send_scout_email.py`, `mode_dry_run()`.
- **Akzeptanz:** `send_scout_email.py --dry-run` ändert die Zustandsdatei nicht (existiert sie vorher nicht, existiert sie danach nicht; existiert sie vorher, ändert sich ihr Inhalt nicht). Der Dry-Run sendet nie per SMTP.

### A6: Zustandsdatei ist atomar und kollisionsfest
- **Anforderung:** Das Schreiben der Zustandszeile ist atomar (schreiben nach Temp-Datei + atomares `os.replace`) und prüft per `FileExistsError`-Logik bzw. `O_EXCL`, dass derselbe Wochenschlüssel nicht doppelt eingetragen wird. Ein parallel gestarteter Zweitlauf, der den Versand überlebt hat, darf keine zweite Zustandszeile für dieselbe Woche erzeugen.
- **Stelle:** `scripts/send_scout_email.py`, `record_sent_week()`.
- **Akzeptanz:** Zwei hintereinander laufende `mode_normal()`-Aufrufe in derselben Woche erzeugen genau eine Zustandszeile. Ein atomarer Schreibfehler (z. B. voller Datenträger) führt zu Exit-Code 1, nicht zu einer halben Zustandsdatei.

### A7: Gemeinsame Funktion für den Wochenschlüssel im Berichtsdateinamen
- **Anforderung:** Eine gemeinsame Funktion (empfohlen: `week_key_for_filename()` in `send_scout_email.py` oder in einem neuen Modul `agents/llm_scout/week_key.py`), die aus einem `datetime`-Objekt den Dateinamen für den Wochenbericht bildet: `llm_scout_kw{iso_week}_{iso_year}.md`, wobei `iso_year` und `iso_week` aus `.isocalendar()` des übergebenen Datums stammen. **Beide** Seiten nutzen diese Funktion:
  - `llm_scout.py` (Erzeuger): Die Zeile, die aktuell `f"llm_scout_kw{week_number}_{datetime.now().strftime('%Y')}.md"` bildet, wird ersetzt durch einen Aufruf der gemeinsamen Funktion mit `datetime.now()`.
  - `send_scout_email.py` (Sucher): `find_current_report()` nutzt dieselbe Funktion.
- **Stelle:** Neue Funktion (gemeinsam); `agents/llm_scout/llm_scout.py` (Erzeuger-Seite); `scripts/send_scout_email.py`, `find_current_report()` (Sucher-Seite).
- **Akzeptanz:** Für **jedes** Datum (inkl. aller ISO-Jahreswechsel-Grenztage) erzeugen `llm_scout.py` und `find_current_report()` denselben Dateinamen. Der Regressions-Test T10 prüft das für selbst berechnete Grenztage (s. T10).

## Fehlerpfade

Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht oder schweigt (SMTP-Server) | Nichts – Versand-Nachweis wird erst nach erfolgreichem `sendmail()` geschrieben | Exit-Code 1, stderr-Fehlermeldung, **keine** Zustandszeile für die Woche | T1 |
| A1 | Eingabe leer oder ungültig (LAB_DIR nicht gesetzt / `REPORT_DIR` fehlt) | `REPORT_DIR` wird bei Import erstellt (bestandene Logik); Zustandsdatei nicht angelegt | Exit-Code 3 (je nach A3-Logik), keine halbe Zustandsdatei | T2 |
| A1 | Ziel existiert schon (Zustandsdatei mit Zeile für dieselbe ISO-Woche) | Zustandsdatei existiert mit Zeile für die aktuelle Woche | Nichts wird überschrieben; `record_sent_week()` verweigert oder ignoriert die Doppelzeile | T3 |
| A1 | Schalter kombiniert (`--dry-run` + Zustandslogik) | n. a. – Dry-Run berührt Zustandsdatei nie | Exit-Code 0, `.eml` in Outbox, Zustandsdatei unverändert | T5 |
| A1 | Lauf ohne Testschalter / gegen echte Daten (echter `smtp.gmail.com` + `SCOUT_ALLOW_SEND=1`) | n. a. – kein Test darf das auslösen | Kein Test läuft mit echter Gmail. Mock ersetzt `get_password()` und `smtplib.SMTP` | – (kein Test, durch Sperre abgedeckt) |
| A1 | Absturz mitten im Lauf (z. B. `KeyboardInterrupt` zwischen `sendmail()` und `os.replace()`) | Mail ist bereits gesendet, Zustandszeile noch nicht atomar geschrieben | Zustandsdatei nicht angefasst oder vollständig (atomares `os.replace`); kein halber Eintrag; bei manuellem Neustart der Woche: Mail könnte theoretisch doppelt gesendet werden – dokumentiert als bekanntes Restrisiko (s. „Abweichende Meinung“) | T6 |
| A2 | Gegenstelle antwortet nicht (SMTP) | Nichts | Exit-Code 1, keine Zustandszeile, kein Zweitversand möglich (weil nichts gesendet wurde) | T1 |
| A2 | Eingabe leer oder ungültig (Zustandsdatei existiert nicht) | Nichts | Zustandsdatei wird neu angelegt (nicht als Fehler) | T3 |
| A2 | Ziel existiert schon (Zustandszeile für die ISO-Woche vorhanden) | Zustandszeile für die Woche existiert | Exit-Code 0, Meldung „KW bereits gesendet“, keine Mail, keine zweite Zustandszeile | T4 |
| A2 | Schalter kombiniert (`--dry-run` + bereits gesendete Woche) | n. a. – Dry-Run prüft Zustandsdatei nicht | Exit-Code 0, `.eml` abgelegt (Dry-Run ignoriert Nachweis) | T5 |
| A2 | Lauf ohne Testschalter / gegen echte Daten | n. a. – kein Test mit echter Gmail | – | – |
| A2 | Absturz mitten im Lauf (Zweitlauf startet, während Erster noch SMTP sendet) | Erster Lauf: Mail gesendet, Zustandszeile noch nicht geschrieben | Zweiter Lauf liest Zustandsdatei ohne Zeile → sendet erneut → **Doppelversand**. Dokumentiert als bekanntes Restrisiko, nicht in Test abgedeckt (s. „Abweichende Meinung“) | – (kein Test, Restrisiko) |
| A3 | Gegenstelle antwortet nicht (SMTP) | n. a. – A3 greift erst, wenn `find_current_report()` `None` liefert; SMTP ist irrelevant | Exit-Code 3 (Bericht fehlt, Woche nicht abgedeckt), stderr-Meldung | T7 |
| A3 | Eingabe leer oder ungültig (`REPORT_DIR` leer, kein Bericht, keine Zustandszeile) | Nichts | Exit-Code 3, stderr-Meldung „Bericht fehlt, Woche nicht abgedeckt“ | T7 |
| A3 | Ziel existiert schon (Bericht fehlt, aber Zustandszeile für Woche vorhanden) | Zustandszeile für Woche existiert | Exit-Code 0, Meldung „bereits gesendet“, kein Fehler | T8 |
| A3 | Schalter kombiniert (`--dry-run` + fehlender Bericht) | n. a. | Exit-Code 0, Meldung „Keine Bericht-Datei … Kein Trockenlauf“ (bestandene Logik) | T5 |
| A3 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A3 | Absturz mitten im Lauf | n. a. – A3 ist eine reine Prüfungslogik, kein Schreiben | n. a. | – |
| A4 | Gegenstelle antwortet nicht (SMTP) | n. a. – Pipeline-Schritt 2 übergibt nur den Exit-Code; Lauf-Datei wird geschrieben | Pipeline beendet mit Exit-Code 3, `pipeline_runs.log` enthält `EMAIL_EXIT=3`, **keine** Fehler-Mail | T9 |
| A4 | Eingabe leer oder ungültig (kein `LAB_DIR` gesetzt, Default `~/lab`) | n. a. | Pipeline nutzt Default, gibt Exit-Code weiter, Lauf-Datei unter `~/lab/pipeline_runs.log` | T9 |
| A4 | Ziel existiert schon (Bericht + Zustandszeile vorhanden) | Zustandszeile vorhanden | `send_scout_email.py` Exit 0, Pipeline Exit 0, Lauf-Datei enthält `EMAIL_EXIT=0` | T4 |
| A4 | Schalter kombiniert (`--dry-run` + fehlender Bericht) | n. a. | Pipeline `--dry-run` überspringt Fehler-Mail, Exit-Code wie im Dry-Run, Lauf-Datei wird **nicht** geschrieben (Dry-Run ist kein echter Lauf) | T9 |
| A4 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A4 | Absturz mitten im Lauf (Pipeline-Crash zwischen Schritt 1 und 2) | Bericht geschrieben, keine Zustandszeile | Pipeline bricht ab, kein Exit-Code 3 (weil Schritt 2 nie lief); Lauf-Datei enthält nur den Scout-Exit; beim Neustart: Schritt 1 überspringt bereits verarbeitete URLs, Schritt 2 prüft Zustandsdatei | – (kein Test, Bestand) |
| A5 | Gegenstelle antwortet nicht (SMTP) | n. a. – Dry-Run sendet nie per SMTP | Exit-Code 0, `.eml` in Outbox, Zustandsdatei unverändert | T5 |
| A5 | Eingabe leer oder ungültig (kein Bericht, Dry-Run) | n. a. | Exit-Code 0, Meldung „Keine Bericht-Datei … Kein Trockenlauf“ | T5 |
| A5 | Ziel existiert schon (`.eml` in Outbox mit gleichem Namen) | `.eml` existiert | Wird überschrieben (bestandene Logik von `save_email_to_file()`), Zustandsdatei unverändert | T5 |
| A5 | Schalter kombiniert (`--dry-run` + `--fail-mail`) | n. a. | `--dry-run` gewinnt (bestandene Logik N3), Zustandsdatei unverändert | T5 |
| A5 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A5 | Absturz mitten im Lauf | n. a. | Zustandsdatei nie berührt | – |
| A6 | Gegenstelle antwortet nicht (SMTP) | Mail nicht gesendet → kein Zustandszugriff | Exit-Code 1, Zustandsdatei unverändert | T1 |
| A6 | Eingabe leer oder ungültig (Zustandsdatei existiert nicht) | Nichts | Zustandsdatei wird neu angelegt (atomar) | T3 |
| A6 | Ziel existiert schon (Zustandsdatei + Zeile für dieselbe Woche) | Zustandszeile existiert | `record_sent_week()` verweigert/ignoriert Doppelzeile (per `O_EXCL` oder Prüflogik) | T3 |
| A6 | Schalter kombiniert (n. a.) | n. a. | n. a. | – |
| A6 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A6 | Absturz mitten im Lauf (zwischen Temp-Write und `os.replace()`) | Temp-Datei existiert, Zustandsdatei noch nicht ersetzt | Zustandsdatei bleibt unverändert (atomares `os.replace`); Temp-Datei bleibt als Orphan zurück – dokumentiert, kein Test | T6 |
| A7 | Gegenstelle antwortet nicht (SMTP) | n. a. – A7 ist eine reine Namenslogik, kein SMTP | n. a. | T10 |
| A7 | Eingabe leer oder ungültig (`datetime`-Objekt ungültig) | n. a. | n. a. – Funktion wird nur mit gültigem `datetime` aufgerufen | – |
| A7 | Ziel existiert schon (Berichtsdatei mit gleichem Namen) | Berichtsdatei existiert | Wird überschrieben (bestandene Logik in `llm_scout.py`), `find_current_report()` findet sie | T10 |
| A7 | Schalter kombiniert (n. a.) | n. a. | n. a. | – |
| A7 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A7 | Absturz mitten im Lauf | n. a. – A7 ist eine reine Namenslogik | n. a. | – |

## Testplan

Alle Tests werden als `tests/test_scout_kw_doppelversand.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung. **Kein Test darf hart eingegebene ISO-Wochenwerte für Grenztage verwenden.** Alle erwarteten ISO-Jahre/-Wochen werden im Test selbst aus dem jeweiligen `datetime` via `.isocalendar()` berechnet und dann mit dem Ergebnis des Codes verglichen.

Gemeinsamer Testaufbau (Setup/Teardown jeder Testklasse):
- Temporäres `LAB_DIR` via `tempfile.mkdtemp()`, als `os.environ["LAB_DIR"]` gesetzt.
- `os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"` und `os.environ["SCOUT_SMTP_PORT"] = "9"` (toter Port) als zweite Sicherungsebene.
- **`get_password()` wird per `unittest.mock.patch` ersetzt** und liefert ein festes Dummy-Passwort. **Kein Test ruft `security` auf.**
- **`smtplib.SMTP` wird per `unittest.mock.patch` ersetzt.** Der Mock zählt aufrufe von `sendmail()` und wirft optional eine `smtplib.SMTPException` (um SMTP-Fehler zu simulieren). **Kein Test öffnet eine echte TCP-Verbindung.** **Kein `aiosmtpd`.**
- `weekly-reports/`-Unterordner im `LAB_DIR` bei Bedarf angelegt.
- Zustandsdatei-Pfad (z. B. `LAB_DIR/weekly-reports/.sent_state`) im Test direkt manipuliert, um Zustände vorzubauen.

### T1: SMTP-Fehler → keine Zustandszeile, Exit 1
- **Prüft:** A1 (Fehlerpfad „Gegenstelle antwortet nicht“), A6
- **Aufbau:** Temporäres `LAB_DIR`, Bericht-Datei für die aktuelle ISO-Woche (Name via gemeinsamer Funktion A7 aus `datetime.now().isocalendar()` berechnet) in `weekly-reports/`, kein Versand-Nachweis vorhanden. `smtplib.SMTP`-Mock wirft `smtplib.SMTPException`.
- **Erwartung:** `mode_normal()` liefert Exit-Code 1. Die Zustandsdatei existiert **nicht** (oder ist leer). stderr enthält eine Fehlermeldung. Der `sendmail()`-Mock wurde **einmal** aufgerufen.
- **Warum misst der Test das Richtige?** Wenn die Anforderung NICHT erfüllt ist (Zustandszeile wird vor dem SMTP-Versand geschrieben), existiert die Zustandsdatei nach einem SMTP-Fehler, und der Test schlägt fehl.

### T2: Fehlendes `REPORT_DIR` / leerer `LAB_DIR` → Exit 3, keine halbe Zustandsdatei
- **Prüft:** A1 (Fehlerpfad „Eingabe leer oder ungültig“), A3
- **Aufbau:** Temporäres `LAB_DIR` **ohne** `weekly-reports/`-Ordner und **ohne** Zustandsdatei.
- **Erwartung:** `mode_normal()` liefert Exit-Code 3 (Bericht fehlt, Woche nicht abgedeckt). Die Zustandsdatei existiert nicht. stderr-Meldung.
- **Warum misst der Test das Richtige?** Wenn A3 NICHT erfüllt ist (Exit 0 statt 3 bei fehlendem Bericht), liefert der Test 0 und schlägt fehl.

### T3: Zustandsdatei mit Zeile für dieselbe ISO-Woche → keine Doppelzeile
- **Prüft:** A1 (Fehlerpfad „Ziel existiert schon“), A2, A6
- **Aufbau:** Temporäres `LAB_DIR`, Zustandsdatei wird per Test-Setup manuell mit genau einer Zeile für die **aktuelle** ISO-Woche (Wochenschlüssel via gemeinsamer Funktion A7 aus `datetime.now().isocalendar()` berechnet) vorab befüllt. Bericht-Datei vorhanden.
- **Erwartung:** `mode_normal()` liefert Exit-Code 0 (KW bereits gesendet). Die Zustandsdatei enthält **genau eine** Zeile (keine zweite für dieselbe Woche). Der `smtplib.SMTP`-Mock wurde **nicht** aufgerufen (SMTP-Verbindungsaufbau wird nicht ausgeführt, da die Zustandsprüfung vor dem Versand steht).
- **Warum misst der Test das Richtige?** Wenn A2/A6 NICHT erfüllt ist (Zweitlauf sendet erneut), wird eine zweite Zustandszeile geschrieben oder der `sendmail()`-Mock wird aufgerufen; der Test schlägt fehl.

### T4: Zweitlauf in derselben ISO-Woche → nur eine Mail, Exit 0
- **Prüft:** A2 (Kernanforderung), A4
- **Aufbau:** Temporäres `LAB_DIR`, Bericht-Datei vorhanden. **Kein** Versand-Nachweis. `smtplib.SMTP`-Mock wird aufgerufen und zählt `sendmail()`-Aufrufe.
- **Erwartung:** Erster `mode_normal()`-Aufruf: Exit 0, `sendmail()`-Mock wird **genau einmal** aufgerufen, Zustandsdatei erhält eine Zeile. Zweiter `mode_normal()`-Aufruf: Exit 0, Meldung „KW bereits gesendet“, `sendmail()`-Mock wird **insgesamt genau einmal** aufgerufen (keine zweite Mail). Zustandsdatei enthält genau **eine** Zeile.
- **Warum misst der Test das Richtige?** Wenn A2 NICHT erfüllt ist (kein Zweitlauf-Check), wird der `sendmail()`-Mock zweimal aufgerufen und der Test schlägt fehl.

### T5: Dry-Run berührt Zustandsdatei nicht
- **Prüft:** A5 (alle Fehlerpfade von A5)
- **Aufbau:** Temporäres `LAB_DIR`, Bericht-Datei vorhanden. Zwei Szenarien:
  - (a) Zustandsdatei existiert **nicht** vor dem Dry-Run.
  - (b) Zustandsdatei existiert **mit** einer Zeile für die aktuelle Woche.
- **Erwartung:** In beiden Szenarien: `mode_dry_run()` liefert Exit-Code 0, legt die `.eml` in `outbox/` ab. Der `smtplib.SMTP`-Mock wird **nie** aufgerufen. Nach dem Dry-Run: Szenario (a) Zustandsdatei existiert **nicht**; Szenario (b) Zustandsdatei enthält **genau eine** Zeile (unverändert).
- **Warum misst der Test das Richtige?** Wenn A5 NICHT erfüllt ist (Dry-Run schreibt/liest Zustandsdatei), verändert sich der Inhalt oder die Existenz der Zustandsdatei, und der Test schlägt fehl.

### T6: Atomarer Zustand – Zustandsdatei bleibt unverändert bei simuliertem Fehler
- **Prüft:** A1 (Fehlerpfad „Absturz mitten im Lauf“), A6
- **Aufbau:** Temporäres `LAB_DIR`, Bericht vorhanden. Die Funktion `record_sent_week()` wird direkt aufgerufen (Unit-Test-Stufe), mit einem monkeypatched `os.replace`, der eine `OSError` wirft (simuliert voller Datenträger).
- **Erwartung:** Die Zustandsdatei existiert **nicht** (oder bleibt in ihrem Zustand vor dem Aufruf). Kein halber Eintrag. Die `OSError` wird an `mode_normal()` weitergereicht → Exit 1.
- **Warum misst der Test das Richtige?** Wenn A6 NICHT erfüllt ist (kein atomares Schreiben, z. B. direktes `open(..., "a")`), entsteht bei simuliertem Fehler eine halbe Zustandsdatei, und der Test schlägt fehl.

### T7: Fehlender Bericht, ungesendete Woche → Exit 3
- **Prüft:** A3 (Kernanforderung, Fehlerpfad „Eingabe leer oder ungültig“ und „Gegenstelle antwortet nicht“)
- **Aufbau:** Temporäres `LAB_DIR`, `weekly-reports/` vorhanden aber **ohne** Bericht-Datei für die aktuelle ISO-Woche (Name via gemeinsamer Funktion A7 berechnet). **Keine** Zustandsdatei.
- **Erwartung:** `mode_normal()` liefert Exit-Code **3**. stderr-Meldung, die auf den fehlenden Bericht und die ungesendete Woche hinweist.
- **Warum misst der Test das Richtige?** Wenn A3 NICHT erfüllt ist (Exit 0 statt 3 bei fehlendem Bericht und ungesendeter Woche), liefert der Test 0 und schlägt fehl. Das ist genau der Jahreswechsel-Stillstand.

### T8: Fehlender Bericht, aber Woche bereits gesendet → Exit 0
- **Prüft:** A3 (Fehlerpfad „Ziel existiert schon“)
- **Aufbau:** Temporäres `LAB_DIR`, **kein** Bericht-Datei für die aktuelle ISO-Woche. Zustandsdatei **mit** einer Zeile für die aktuelle ISO-Woche (vorab per Test-Setup geschrieben, Wochenschlüssel via gemeinsamer Funktion A7 berechnet).
- **Erwartung:** `mode_normal()` liefert Exit-Code **0**. Meldung „bereits gesendet“ (oder vergleichbar). **Kein** Exit 3. Der `smtplib.SMTP`-Mock wird **nicht** aufgerufen.
- **Warum misst der Test das Richtige?** Wenn A3 NICHT erfüllt ist (kein Unterschied zwischen „bereits gesendet“ und „Bericht fehlt“), liefert der Test Exit 3 und schlägt fehl.

### T9: Pipeline gibt Exit-Code 3 an launchd weiter und schreibt Lauf-Datei
- **Prüft:** A4 (Fehlerpfad „Gegenstelle antwortet nicht“ und „Eingabe leer oder ungültig“)
- **Höhe:** **Shell-Test auf Python-Ebene**, ohne den echten Scout auszuführen. Der echte Scout holt HF/GitHub per `requests` (Internetzugriff) und ist daher nicht im unittest isolierbar.
- **Aufbau:** Temporäres `LAB_DIR`, **kein** Bericht, **keine** Zustandsdatei. Der Test ruft `send_scout_email.py` **als Subprozess** auf (`subprocess.run([sys.executable, "scripts/send_scout_email.py"])`), mit `LAB_DIR` auf das temporäre Verzeichnis und mit `smtplib.SMTP` per `unittest.mock` **nicht** relevant (da kein Bericht, wird SMTP nie aufgerufen). Der Exit-Code des Subprozesses wird abgefragt.
  - **Zusätzlich:** Der Test prüft, dass `run_scout_pipeline.sh` den Exit-Code von `send_scout_email.py` weiterleitet, indem er das Skript mit einem **gesteuerten** `send_scout_email.py`-Aufruf ausführt (der Scout-Schritt wird per `LLAMA_SERVER_URL` auf eine tote URL gesetzt, sodass der Scout mit Exit 2 endet – das ist **kein** Internetzugriff, sondern eine kontrollierte Verbindungsaufnahme an einen toten lokalen Port). **Alternativ (empfohlen):** Der Test prüft nur die Weiterleitung des Exit-Codes von `send_scout_email.py` (Subprozess), nicht den gesamten Pipeline-Lauf.
- **Erwartung:** `send_scout_email.py` (Subprozess) liefert Exit-Code **3**. `LAB_DIR/pipeline_runs.log` enthält eine Zeile mit `EMAIL_EXIT=3`. Es wird **keine** Fehler-Mail ausgelöst (der `smtplib.SMTP`-Mock wird **nicht** aufgerufen).
- **Warum misst der Test das Richtige?** Wenn A4 NICHT erfüllt ist (Pipeline gibt Exit 0 oder 1 statt 3, oder schreibt keine Lauf-Datei), beendet sich das Skript mit einem anderen Code oder die Lauf-Datei fehlt, und der Test schlägt fehl.
- **Hawe-muss-ausführen-Variante (optional, für kompletten E2E):** Wenn ein vollständiger End-to-End-Lauf der Pipeline gewünscht ist (inkl. echtem Scout mit HF/GitHub-Zugriff), muss Hawe den Lauf **manuell** ausführen: `bash scripts/run_scout_pipeline.sh` (ohne `--dry-run`), mit `LAB_DIR` auf ein temporäres Verzeichnis, und dann prüfen, ob `LAB_DIR/pipeline_runs.log` eine Zeile mit `EMAIL_EXIT=3` enthält (wenn kein Bericht existiert und keine Zustandszeile vorliegt). **Dieser E2E-Lauf ist nicht Teil des unittest und wird nicht automatisch ausgeführt.**

### T10: ISO-Jahreswechsel – Erzeuger und Sucher stimmen auf denselben Dateinamen überein (Regressions-Test)
- **Prüft:** A7 (Kernanforderung) – der Kern des Jahreswechsel-Standbeins
- **Aufbau:** **Kein** hart eingegebener Grenztage-Wert. **Kein** festes Beispiel wie „28.12.2026". Stattdessen:
  1. Der Test schleift über die Tage um den Jahreswechsel von **mehreren Jahren** (z. B. 2024–2029, jeweils 20 Tage vor und nach dem 01.01.).
  2. Für jeden Tag wird `iso_year`, `iso_week` und `cal_year` (Kalenderjahr) via `.isocalendar()` bzw. `.year` berechnet.
  3. Der Test wählt **alle** Tage aus, bei denen `iso_year != cal_year` (ISO-Jahr ≠ Kalenderjahr). Davon werden **mindestens** zwei ausgewählt: **ein Dezember-Tage** (monatlich Dezember, `iso_year > cal_year`) und **ein Januar-Tage** (monatlich Januar, `iso_year < cal_year`).
  4. Für jedes ausgewählte Testdatum:
     - Der **Erzeuger-Dateiname** wird **so gebildet, wie `llm_scout.py` ihn aktuell schreibt** (per Mock der Erzeuger-Funktion oder durch direkten Aufruf der Namensbildung aus `llm_scout.py`). **Wichtig:** Der Test muss den **tatsächlichen Erzeuger-Code** aufrufen, nicht eine eigene, „korrekte" Namensbildung. So misst der Test die **tatsächliche** Inkonsistenz, nicht eine hypothetische.
     - Eine Bericht-Datei mit dem **Erzeuger-Dateinamen** im temporären `LAB_DIR/weekly-reports/` angelegt.
     - `datetime.now()` per Monkeypatch (`unittest.mock.patch`) auf das gewählte Datum gesetzt.
     - `find_current_report()` aufgerufen.
- **Erwartung:** `find_current_report()` liefert für **alle** ausgewählten Testdaten die gerade angelegte Bericht-Datei zurück (`is not None`). Das bedeutet: Erzeuger und Sucher stimmen auf denselben Dateinamen überein.
- **Warum misst der Test das Richtige?** Wenn die Namenskonvention von Erzeuger und Sucher **nicht** übereinstimmt (z. B. Erzeuger nutzt `strftime('%Y')`, Sucher nutzt `isocalendar()[0]` für das Jahr), liefert `find_current_report()` für das Dezemberschwanz-Datum `None` (weil die Datei unter dem Kalenderjahr-Name liegt, der Sucher aber nach dem ISO-Jahr-Name sucht), und der Test schlägt fehl. **Der Test misst also exakt den Jahreswechsel-Stillstand, ohne dass ein Grenztage-Wert hart eingetragen ist. Und: Der Test schlägt fehl, solange A7 nicht umgesetzt ist (d. h. der Test ist heute **rot**, wird grün, wenn A7 umgesetzt ist).**

## Offene Fragen

- **Keine.** Beide offenen Fragen aus der vorherigen Fassung sind entschieden:
  - A7 (Namenskonvention) wird **ergänzt** (entschieden: ja).
  - Restrisiko paralleler Zweitlauf wird **akzeptiert** und so dokumentiert (entschieden: akzeptiert).

## Abweichende Meinung

- **Restrisiko paralleler Zweitlauf (akzeptiert, dokumentiert):** Die Zustandsprüfung vor dem Versand deckt den Hauptfall ab (Zweitlauf **nach** erfolgreichem Erstem). Das Fenster zwischen `sendmail()` und atomarem `os.replace()` ist klein, aber nicht null. In diesem Fenster könnte ein paralleler Zweitlauf die Mail erneut senden. **Entscheidung von Hawe:** Akzeptiert. Die Spec behandelt das als bekanntes Restrisiko, nicht als Anforderung. Eine stärkere Synchronisation (Lock-Datei) wird nicht umgesetzt.

- **A7 (Namenskonvention, entschieden):** Die gemeinsame Funktion `week_key_for_filename()` wird in `send_scout_email.py` (oder einem neuen Modul `agents/llm_scout/week_key.py`) implementiert und von **beiden** Seiten genutzt. Der Erzeuger in `llm_scout.py` ersetzt die aktuelle Zeile `f"llm_scout_kw{week_number}_{datetime.now().strftime('%Y')}.md"` durch einen Aufruf der gemeinsamen Funktion. Der Sucher in `find_current_report()` nutzt dieselbe Funktion. Der Regressions-Test T10 ist **heute rot** und wird **grün**, wenn A7 umgesetzt ist.
