# Spec: scout_bericht_ueberschreiben

- **Datum:** 2026-10-18
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Betroffene Dateien:** `agents/llm_scout/llm_scout.py`, `scripts/send_scout_email.py`, `scripts/run_scout_pipeline.sh`, `agents/llm_scout/week_key.py` (alle vollständig gelesen), `docs/projekt_management/_vorlage_spec.md` (gelesen), `docs/projekt_management/spec_20261018_scout_kw_doppelversand.md` (gelesen, als Kontext)

## Ziel

Ein Zweitlauf des LLM-Scouts in derselben ISO-Kalenderwoche darf nichts verlieren, was ein erster Lauf gefunden und bewertet hat. Konkret: Der erste Bericht bleibt in der Datei vollständig erhalten, der zweite Lauf hängt einen klar gekennzeichneten Nachtrag an dieselbe Datei an, und jeder gefundene Eintrag kommt genau einmal per Mail an.

## Nicht-Ziele

- **Keine Änderung an der Selektionslogik** (`select_items()`, Top-3 pro Quelle). Das ist ein bewusstes Design (Kontext sparen), kein Bug.
- **Keine Änderung an der `processed_items`-DB-Logik in `llm_scout.py`.** Die DB bleibt die Quelle für „schon bewertet oder nicht". Der Versand-Nachweis und die Bericht-Datei sind separate Zustandsquellen.
- **Kein Zusammenführen des neuen LLM-Outputs mit dem alten Bericht** zu einem neuen, komplett neu generierten Infopaper. Das würde das LLM-Verhalten berühren und ist nicht nötig, um den Datenverlust zu stoppen.
- **Keine Änderung an der launchd-plist.**
- **Keine Änderung am Fehler-Mail-Pfad** (`--fail-mail`) und seinem Datei-Fallback.
- **Keine Änderung an der `SCOUT_ALLOW_SEND`-Sperre.**

## Entscheidung: Nachtrag statt Neu-Generierung (begründet)

**Problem:** `llm_scout.py` schreibt den Bericht mit `open(filepath, 'w')` (Blind-Overwrite). `week_key_for_filename()` liefert für dieselbe ISO-KW denselben Dateinamen. Zweiter Lauf derselben Woche → gleiche Datei → `open('w')` ersetzt den gesamten ersten Bericht.

**Zwei Optionen:**
- **(a) Zusammenführen:** Erstbericht einlesen, dem LLM als Kontext geben, neues Gesamt-Infopaper generieren.
- **(b) Anhängen:** Erstbericht unverändert belassen, neuen LLM-Output als klar markierten Nachtrag hinter den Erstbericht anhängen.

**Entscheidung: (b) Anhängen.**

**Begründung:**
1. **Kein LLM-Verhalten im Spiel.** Bei (a) hängt das Ergebnis davon ab, ob das LLM den alten Bericht korrekt einbettet, gewichtet oder weglässt. Das ist nicht deterministisch prüfbar und würde `call_llm_for_evaluation()` ändern. Bei (b) ist der Erstbericht buchstäblich byte-identisch erhalten – der Datenverlust ist mechanisch ausgeschlossen.
2. **„Nichts verlieren" ist strikt erfüllt.** Die Anforderung lautet: ein Zweitlauf darf nichts verlieren, was ein Lauf gefunden hat. (b) garantiert das per Dateistruktur, nicht per LLM-Güte. (a) garantiert es nur statistisch.
3. **Kleinere Änderungen.** (b) berührt nur das Schreiben (ein `open(..., 'a')` statt `open(..., 'w')` plus eine Prüfungszeile) und die Mail-Nachweis-Logik. (a) berührt zusätzlich `call_llm_for_evaluation()`, den Prompt und die Selektion.
4. **E-Mail-Semantik bleibt sauber.** Mit (b) kann die Mail-Logik pro Lauf entscheiden: Erstbericht → normale Mail, Nachtrag → Nachtrag-Mail. Bei (a) würde der Zweitlauf dieselbe Datei mit neuem Inhalt überschreiben, und die `.sent_state`-Logik („einmal pro Woche") müsste entweder brechen oder den Zweitbericht nie mailen.

**Abgrenzung zu „jeder Eintrag kommt genau einmal per Mail an":** Die `processed_items`-DB stellt sicher, dass ein URL-Item in Lauf 2 nicht erneut bewertet wird, wenn es in Lauf 1 schon markiert war. Die Mail-Sperre (`.sent_state`) stellt sicher, dass der Erstbericht nicht zweimal per Mail geht. Der Nachtrag wird **zusätzlich** per Mail gesendet (s. A2), weil er **neue** Inhalte enthält, die noch nicht zugestellt wurden. „Jeder Eintrag kommt genau einmal an" heißt: Ein URL-Item, das in Lauf 1 bewertet und gemailt wurde, wird in Lauf 2 nicht erneut gemailt. Ein URL-Item, das in Lauf 2 **neu** bewertet wurde, wird genau einmal gemailt – in der Nachtrag-Mail.

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?**
  - **Echte E-Mail:** `send_scout_email.py` im Normalmodus sendet per SMTP an `smtp.gmail.com` (Default) an `askvalentinai@gmail.com`. Der neue Nachtrag-Mail-Pfad (A2) sendet ebenfalls per SMTP. Das ist die kritischste Außenwirkung.
  - **Schlüsselbund:** `get_password()` ruft `security find-generic-password -s lab-scout-smtp -w` auf. Wird bei jedem echten SMTP-Versand berührt, inkl. Nachtrag-Mail.
  - **Netzwerk:** SMTP-Verbindung zum konfigurierten Host (Default Gmail). Im Test gegen `127.0.0.1`/`localhost`.
  - **Keine echten Daten/DB außerhalb von `LAB_DIR`:** Die Bericht-Datei und der Versand-Nachweis liegen im `LAB_DIR`. `llm_scout.db` wird nicht von dieser Spec berührt.
- **Technische Sperre für Tests:**
  - `LAB_DIR` auf ein temporäres Verzeichnis (`tempfile.mkdtemp()`), sodass Berichte, Zustandsdateien und Outbox-Dateien isoliert liegen.
  - **`get_password()` und `smtplib.SMTP` werden in jedem Test per `unittest.mock` ersetzt.** Kein Test ruft `security` auf oder öffnet eine echte TCP-Verbindung. `SCOUT_SMTP_HOST` und `SCOUT_SMTP_PORT` werden zusätzlich auf `127.0.0.1` bzw. einen toten Port gesetzt.
  - **Kein Test darf `SCOUT_ALLOW_SEND=1` mit dem echten `smtp.gmail.com` kombinieren.**
  - **`llm_scout.py` wird in Tests nie komplett ausgeführt** (der Scout holt HF/GitHub per `requests` → Internetzugriff). Tests importieren nur die relevanten Funktionen oder ersetzen sie per Mock.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `agents/llm_scout/llm_scout.py` | `python3 agents/llm_scout/llm_scout.py` aus `run_scout_pipeline.sh` (Schritt 1) | T5, T6 (Import-Test ohne `__main__`, plus gezielter Funktions-Test der Schreiblogik) |
| `scripts/send_scout_email.py` | `python3 scripts/send_scout_email.py` aus `run_scout_pipeline.sh` (Schritt 2), auch mit `--dry-run` | T1–T4, T7–T9 (Subprozess-Aufruf, Mocked SMTP) |
| `scripts/run_scout_pipeline.sh` | `bash scripts/run_scout_pipeline.sh` aus launchd (`de.hawe.lab.llm_scout`) | T8, T9 (Pipeline-Weiterleitung, Lauf-Datei) |
| `agents/llm_scout/week_key.py` | Modul, von `llm_scout.py` und `send_scout_email.py` importiert | T6 (Indirekt über Import-Test) |

**Wichtiger Hinweis zum Import-Test:** Die Vorlage verlangt, dass jeder Einstiegspunkt einen Test hat, der ihn **so startet wie im Betrieb** (ohne Außenwirkung). Für `llm_scout.py` bedeutet das: Der Test darf `llm_scout.py` **nicht** als Skript mit `__main__` ausführen (das würde HF/GitHub per `requests` abfragen). Stattdessen importiert der Test die Module als Modul (`runpy` oder `importlib`) mit `run_name="kein_main"` bzw. prüft, dass `main()` nicht aufgerufen wird. Die Schreiblogik (A1) wird dann als isolierte Funktionstest gegen einen temporären Pfad geprüft.

## Anforderungen

### A1: Zweitlauf hängt nach, statt zu überschreiben
- **Anforderung:** `llm_scout.py` prüft vor dem Schreiben des Berichts, ob die Ziel-Datei (Name via `week_key_for_filename(datetime.now())`) bereits existiert.
  - Existiert sie **nicht**: Die Datei wird angelegt und der LLM-Output als Erstbericht geschrieben (wie bisher, aber ohne `open('w')`-Semantik, sondern explizit `open('w')` weil die Datei neu ist – äquivalent, aber klarer dokumentiert).
  - Existiert sie **schon** (Zweitlauf derselben ISO-KW): Die Datei wird **nicht** überschrieben. Der LLM-Output wird als **Nachtrag** an die bestehende Datei **angehängt**. Der Nachtrag beginnt mit einer klaren Trennung und Kennzeichnung:
    ```
    <bestehender Inhalt unverändert>

    ---

    ## Nachtrag KW{week}_{year} ({datum %Y-%m-%d %H:%M})

    {LLM-Output}
    ```
    Die Header-Zeile „Nachtrag KW…" ist zwingend, damit ein Mensch (oder ein Tool) den Erstbericht vom Nachtrag unterscheiden kann.
- **Stelle:** `agents/llm_scout/llm_scout.py`, `main()`, Abschnitt „4. Bericht speichern".
- **Akzeptanz:**
  - Erstlauf: Die Datei existiert danach und enthält **genau** den LLM-Output (keine „Nachtrag"-Kennzeichnung).
  - Zweitlauf (gleiche ISO-KW): Die Datei enthält **den kompletten Erstbericht byte-identisch vor dem angehängten Nachtrag**. Der Nachtrag enthält die „Nachtrag KW…"-Zeile. Die Länge der Datei ist `len(erstbericht) + len(nachtrag_zeile) + len(llm_output)`.
  - Ein dritter Lauf derselben ISO-KW hängt einen weiteren Nachtrag an (die Datei enthält dann Erstbericht + Nachtrag 1 + Nachtrag 2).

### A2: Versand-Nachweis pro Lauf, nicht pro Woche (Nachtrag-Mail)
- **Anforderung:** Der Versand-Nachweis in `send_scout_email.py` muss zwischen „Erstbericht gesendet" und „Nachtrag gesendet" unterscheiden. Der Zustand ist nicht „KW X ist gesendet", sondern **„KW X, Bericht-Lauf N ist gesendet"**.
  - **Umsetzung:** Die Zustandsdatei `.sent_state` enthält pro Zeile: `{iso_year}_{iso_week:02d} {lauf_nr} {datum}`.
    - `lauf_nr` ist ein fortlaufender Zähler pro ISO-KW, beginnend bei 1. Er wird **vor** dem Versand incrementiert (s. A3 für den Crash-Fall).
    - Beim Erstbericht ist `lauf_nr = 1`. Beim ersten Nachtrag `lauf_nr = 2`, beim zweiten Nachtrag `lauf_nr = 3`, usw.
  - **`is_week_already_sent()`** wird ersetzt/ergänzt durch **`get_last_sent_lauf_nr()`**, die die höchste `lauf_nr` für die aktuelle ISO-KW aus der Zustandsdatei liest (0, wenn keine Zeile existiert).
  - **`mode_normal()`** prüft vor dem Versand: Wie viele Berichts-Läufe hat die **aktuelle Bericht-Datei** (Erstbericht + alle Nachträge)? Die Anzahl der „Nachtrag KW…"-Header in der Datei + 1 (für den Erstbericht) ergibt die erwartete `lauf_nr`. Ist die gesendete `lauf_nr` **kleiner** als die erwartete, gibt es einen ungesendeten Nachtrag → senden. Ist sie **gleich**, ist alles gesendet → Exit 0, kein Versand.
- **Stelle:** `scripts/send_scout_email.py`, `SENT_STATE_FILE`-Format, `record_sent_week()`, `is_week_already_sent()` → `get_last_sent_lauf_nr()`, `mode_normal()`.
- **Akzeptanz:**
  - Erstlauf (kein Nachtrag in Datei): Zustandszeile `{jahr}_{ww} 1 {datum}` wird geschrieben, Mail gesendet.
  - Zweitlauf (ein Nachtrag in Datei, `lauf_nr=1` schon gesendet): Zustandszeile `{jahr}_{ww} 2 {datum}` wird **zusätzlich** geschrieben (erste Zeile bleibt), Mail gesendet (Nachtrag-Mail).
  - Drittlauf (zwei Nachträge in Datei, `lauf_nr=2` schon gesendet): Zustandszeile `{jahr}_{ww} 3 {datum}` wird geschrieben, Mail gesendet.
  - Viertlauf (zwei Nachträge in Datei, `lauf_nr=3` schon gesendet, keine neuen Items → kein neuer Lauf geschrieben): **Keine** Mail, Exit 0, Meldung „alles gesendet".

### A3: `lauf_nr` wird vor dem Versand in der Zustandsdatei reserviert (Crash-Safety)
- **Anforderung:** `record_sent_week()` (umbenannt oder ergänzt) schreibt die neue Zustandszeile **vor** dem SMTP-Versand, nicht danach. Damit ist im Crash-Fall zwischen Zustands-Write und `sendmail()`:
  - Die Zustandsdatei enthält die Zeile für `lauf_nr N`.
  - Die Mail ist **nicht** gesendet.
  - Ein Neustart der Pipeline merkt: Zustandszeile für `lauf_nr N` existiert, Mail noch nicht gesendet → **wiederholen** (die Mail geht).
  - Das ist ein **bewusstes Doppelversand-Risiko im Crash-Fall** (Mail geht doppelt), gegen ein **Datenverlust-Risiko ohne Reservierung** (Nachtrag geht nie, weil Zustandszeile fehlt und der Lauf nicht wiederholt wird). Die Entscheidung liegt bei Hawe: **Doppelversand ist akzeptiert, Datenverlust nicht.**
  - **Abgrenzung zu `scout_kw_doppelversand`:** Die dortige Anforderung „Zustandszeile nur nach erfolgreichem `sendmail()`" wird hier **bewusst aufgebrochen**, weil sie bei Nachträgen zum Datenverlust führen würde (s. Fehlerpfad-Tabelle, A3 „Absturz mitten im Lauf").
- **Stelle:** `scripts/send_scout_email.py`, `record_sent_week()`.
- **Akzeptanz:**
  - `record_sent_week(lauf_nr=N)` wird **vor** `send_email_smtp()` aufgerufen.
  - Nach einem erfolgreichen Versand: Zustandszeile für `lauf_nr N` existiert, Mail gesendet.
  - Nach einem SMTP-Fehler (Crash): Zustandszeile für `lauf_nr N` existiert **bereits**, Mail **nicht** gesendet. Ein zweiter Lauf wiederholt den Versand (s. A2: `lauf_nr N` ist gesendet, aber die Datei hat `lauf_nr N` Nachträge → erwartete `lauf_nr = N` → eigentlich alles gesendet → **aber**: der zweite Lauf sieht, dass Zustandszeile `N` existiert und die Datei `N` Läufe hat → alles abgestimmt → Exit 0, **keine** Mail).
  - **Wichtig:** Das bedeutet: Im Crash-Fall geht der Nachtrag **nicht** erneut per Mail. Die Zustandszeile ist geschrieben, die Mail fehlt. Das ist ein **bekanntes Restrisiko** (s. „Abweichende Meinung"). Es ist **besser** als das alternative Szenario (keine Zustandszeile → nächster Lauf denkt, `lauf_nr N` sei ungesendet → sendet, aber der Lauf wurde in `llm_scout.py` nicht neu geschrieben, weil die Items markiert sind → keine Mail, kein Inhalt verloren, aber der Nachtrag fehlt in der Mail).
  - **Akzeptanz-Test (T7):** Simulierter SMTP-Fehler nach `record_sent_week()`. Erwartung: Zustandszeile existiert, `sendmail()`-Mock wurde einmal aufgerufen, `mode_normal()` liefert Exit 1. Ein zweiter `mode_normal()`-Aufruf liefert Exit 0 („alles gesendet"), `sendmail()`-Mock wird **nicht** erneut aufgerufen.

### A4: Pipeline gibt den Exit-Code unverändert weiter
- **Anforderung:** `run_scout_pipeline.sh` übergibt den Exit-Code von `llm_scout.py` (Schritt 1) und `send_scout_email.py` (Schritt 2) unverändert an launchd. Die Lauf-Datei (`LAB_DIR/pipeline_runs.log`) wird bei jedem Lauf (Erfolg und Fehler) geschrieben, wie in `scout_kw_doppelversand` A4.
- **Stelle:** `scripts/run_scout_pipeline.sh`.
- **Akzeptanz:** Unverändert gegenüber `scout_kw_doppelversand` A4. Dieser Test prüft nur, dass die Pipeline die Exit-Codes korrekt weiterleitet und die Lauf-Datei schreibt.

### A5: Trockenlauf bleibt vom Versand-Nachweis isoliert
- **Anforderung:** `mode_dry_run()` liest und schreibt **nicht** den Versand-Nachweis. Der Dry-Run speichert weiterhin nur die `.eml` in der Outbox. Er sendet nie per SMTP und berührt nie die Zustandsdatei.
- **Stelle:** `scripts/send_scout_email.py`, `mode_dry_run()`.
- **Akzeptanz:** Unverändert gegenüber `scout_kw_doppelversand` A5.

## Fehlerpfade

Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht oder schweigt (llama-server) | Nichts – `router_ready()` schlägt fehl, `main()` beendet mit Exit 2, **nichts** wird geschrieben oder markiert | Exit-Code 2, Bericht-Datei **nicht** angefasst (existiert sie vorher, bleibt sie unverändert), DB **nicht** markiert | – (kein Test, bestandene Logik) |
| A1 | Eingabe leer oder ungültig (LLM liefert leeren Inhalt) | Nichts – `call_llm_for_evaluation()` wirft `RuntimeError("Modell lieferte leeren Inhalt")` | Exit-Code 1, Bericht-Datei **nicht** angefasst, DB **nicht** markiert | – (kein Test, bestandene Logik) |
| A1 | Ziel existiert schon (Berichts-Datei für dieselbe ISO-KW vorhanden) | Erstbericht existiert in der Datei | Erstbericht bleibt **byte-identisch**, Nachtrag wird angehängt mit „Nachtrag KW…"-Header | T1 |
| A1 | Schalter kombiniert (n. a. – `llm_scout.py` hat keine Schalter) | n. a. | n. a. | – |
| A1 | Lauf ohne Testschalter / gegen echte Daten | n. a. – kein Test führt den Scout komplett aus (HF/GitHub-Zugriff) | – | – |
| A1 | Absturz mitten im Lauf (z. B. `KeyboardInterrupt` während des Anhängens) | Erstbericht existiert, Nachtrag teils geschrieben (Datei-Handle offen) | Datei enthält Erstbericht + **teilweise** Nachtrag. Beim nächsten Lauf: Der teilweise Nachtrag wird **nicht** automatisch bereinigt. **Bekanntes Restrisiko** (s. „Abweichende Meinung"). Nächster Lauf hängt einen weiteren Nachtrag an, der teilweise Nachtrag bleibt in der Datei. | – (kein Test, Restrisiko) |
| A2 | Gegenstelle antwortet nicht (SMTP) | Zustandszeile für `lauf_nr N` **bereits** geschrieben (A3) | Exit-Code 1, Zustandszeile für `lauf_nr N` existiert, Mail **nicht** gesendet. Nächster Lauf: Exit 0 („alles gesendet"), **keine** Mail (s. A3) | T3 |
| A2 | Eingabe leer oder ungültig (Zustandsdatei existiert nicht, keine Bericht-Datei) | Nichts | Exit-Code 3 (Bericht fehlt, Woche nicht abgedeckt – s. `scout_kw_doppelversand` A3), keine Zustandszeile | T2 |
| A2 | Ziel existiert schon (Zustandszeile für `lauf_nr N` vorhanden, Datei hat `N` Läufe) | Zustandszeile existiert, Bericht-Datei hat `N` Läufe (Erstbericht + `N-1` Nachträge) | Exit-Code 0, „alles gesendet", **keine** Mail, keine zweite Zustandszeile | T4 |
| A2 | Schalter kombiniert (`--dry-run` + Zustandslogik) | n. a. – Dry-Run berührt Zustandsdatei nie | Exit-Code 0, `.eml` in Outbox, Zustandsdatei unverändert | T5 |
| A2 | Lauf ohne Testschalter / gegen echte Daten | n. a. – kein Test mit echter Gmail | – | – |
| A2 | Absturz mitten im Lauf (Crash zwischen Zustands-Write und `sendmail()`) | Zustandszeile für `lauf_nr N` geschrieben, Mail nicht gesendet | Zustandszeile bleibt, Mail fehlt. Nächster Lauf: Exit 0, keine Mail (s. A3). **Bekanntes Restrisiko:** Nachtrag fehlt in der Mail. | T3 |
| A3 | Gegenstelle antwortet nicht (SMTP) | Zustandszeile für `lauf_nr N` geschrieben (vor `sendmail()`) | Exit-Code 1, Zustandszeile existiert, Mail nicht gesendet | T3 |
| A3 | Eingabe leer oder ungültig (Zustandsdatei existiert nicht) | Nichts | Zustandsdatei wird neu angelegt mit Zeile für `lauf_nr N` (vor dem Versand) | T3 |
| A3 | Ziel existiert schon (Zustandszeile für `lauf_nr N` vorhanden) | Zustandszeile existiert | `record_sent_week(lauf_nr=N)` **verweigert** die zweite Zeile für dieselbe `lauf_nr` (per Prüflogik: Zeile für `(jahr, ww, lauf_nr)` existiert → nichts tun) | T4 |
| A3 | Schalter kombiniert (n. a.) | n. a. | n. a. | – |
| A3 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A3 | Absturz mitten im Lauf (zwischen Zustands-Write und `os.replace()`) | Temp-Datei existiert, Zustandsdatei noch nicht ersetzt | Zustandsdatei bleibt unverändert (atomares `os.replace`); Temp-Datei bleibt als Orphan. **Keine** halbe Zustandsdatei. Nächster Lauf: Zustandszeile für `lauf_nr N` fehlt → `lauf_nr N` wird erneut reserviert → Mail gesendet (falls SMTP klappt) → kein Datenverlust | T6 |
| A4 | Gegenstelle antwortet nicht (SMTP) | n. a. – Pipeline übergibt nur den Exit-Code | Pipeline beendet mit dem Exit-Code von `send_scout_email.py`, Lauf-Datei geschrieben | T7 |
| A4 | Eingabe leer oder ungültig (kein `LAB_DIR` gesetzt) | n. a. | Pipeline nutzt Default `~/lab`, Lauf-Datei unter `~/lab/pipeline_runs.log` | T7 |
| A4 | Ziel existiert schon (Bericht + Zustandszeile vorhanden) | Zustandszeile vorhanden | `send_scout_email.py` Exit 0, Pipeline Exit 0, Lauf-Datei enthält `EMAIL_EXIT=0` | T4 |
| A4 | Schalter kombiniert (`--dry-run` + fehlender Bericht) | n. a. | Pipeline `--dry-run` überspringt Fehler-Mail, Lauf-Datei wird **nicht** geschrieben | T7 |
| A4 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A4 | Absturz mitten im Lauf (Pipeline-Crash zwischen Schritt 1 und 2) | Bericht geschrieben (ggf. mit Nachtrag), keine Zustandszeile | Pipeline bricht ab. Beim Neustart: Scout überspringt bereits verarbeitete URLs (DB), `send_scout_email.py` prüft Zustandsdatei | – (kein Test, Bestand) |
| A5 | Gegenstelle antwortet nicht (SMTP) | n. a. – Dry-Run sendet nie per SMTP | Exit-Code 0, `.eml` in Outbox, Zustandsdatei unverändert | T5 |
| A5 | Eingabe leer oder ungültig (kein Bericht, Dry-Run) | n. a. | Exit-Code 0, Meldung „Keine Bericht-Datei … Kein Trockenlauf" | T5 |
| A5 | Ziel existiert schon (`.eml` in Outbox mit gleichem Namen) | `.eml` existiert | Wird überschrieben (bestandene Logik), Zustandsdatei unverändert | T5 |
| A5 | Schalter kombiniert (`--dry-run` + `--fail-mail`) | n. a. | `--dry-run` gewinnt (bestandene Logik) | T5 |
| A5 | Lauf ohne Testschalter / gegen echte Daten | n. a. | – | – |
| A5 | Absturz mitten im Lauf | n. a. | Zustandsdatei nie berührt | – |

## Testplan

Alle Tests werden als `tests/test_scout_bericht_ueberschreiben.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.

**Wichtige Test-Regel:** Neue Funktionen (z. B. die neue Anhäng-Logik in `llm_scout.py`, `get_last_sent_lauf_nr()` in `send_scout_email.py`) werden **in der Testmethode** importiert, nicht am Dateianfang. So lädt das Testskript auch mit dem alten Code und die Gegenprobe (`kette.py gegenprobe`) sagt je Test, ob der Test rot wird.

Gemeinsamer Testaufbau (Setup/Teardown jeder Testklasse):
- Temporäres `LAB_DIR` via `tempfile.mkdtemp()`, als `os.environ["LAB_DIR"]` gesetzt.
- `os.environ["SCOUT_SMTP_HOST"] = "127.0.0.1"` und `os.environ["SCOUT_SMTP_PORT"] = "9"` (toter Port) als zweite Sicherungsebene.
- **`get_password()` wird per `unittest.mock.patch` ersetzt.** Kein Test ruft `security` auf.
- **`smtplib.SMTP` wird per `unittest.mock.patch` ersetzt.** Der Mock zählt `sendmail()`-Aufrufe und wirft optional eine `smtplib.SMTPException`. Kein Test öffnet eine echte TCP-Verbindung. Kein `aiosmtpd`.
- `weekly-reports/`-Unterordner im `LAB_DIR` bei Bedarf angelegt.
- Bericht-Datei-Namen werden **immer** via `week_key_for_filename(datetime.now())` berechnet, nie hart eingegeben.

### T1: Zweitlauf hängt Nachtrag an, Erstbericht bleibt byte-identisch
- **Prüft:** A1 (Kernanforderung, Fehlerpfad „Ziel existiert schon")
- **Aufbau:**
  - Temporäres `LAB_DIR`, `weekly-reports/` angelegt.
  - **Erstlauf simuliert:** Eine Bericht-Datei mit dem Namen `week_key_for_filename(datetime.now())` wird manuell mit einem festen Inhalt „ERSTBERICHT_INHALT" angelegt.
  - **Zweitlauf simuliert:** Die neue Anhäng-Funktion aus `llm_scout.py` (in der Methode importiert) wird aufgerufen mit `report_content="NACHTRAG_INHALT"`. Die Funktion soll prüfen, ob die Datei existiert, und dann anhängen.
  - **Gegenprobe:** Die Funktion wird **in der Methode** importiert (`from llm_scout import append_report` oder ähnlich, je nach Umsetzung). Mit altem Code (blinde `open('w')`) wird der Inhalt „ERSTBERICHT_INHALT" **überschrieben** durch „NACHTRAG_INHALT".
- **Erwartung:**
  - Die Datei existiert.
  - Der Inhalt der Datei beginnt **exakt** mit „ERSTBERICHT_INHALT" (byte-identisch, kein einziger Byte anders).
  - Der Inhalt enthält die Zeile „## Nachtrag KW" (mit der richtigen ISO-KW und dem Jahr).
  - Der Inhalt endet mit „NACHTRAG_INHALT".
  - Die Datei-Länge ist `len("ERSTBERICHT_INHALT") + len(trenner_zeile) + len(nachtrag_header) + len("NACHTRAG_INHALT")`.
- **Warum misst der Test das Richtige?** Wenn A1 NICHT erfüllt ist (blinde `open('w')`), enthält die Datei **nur** „NACHTRAG_INHALT", der Test schlägt fehl.
- **Gegenprobe:** Die Datei `agents/llm_scout/llm_scout.py` muss die neue Anhäng-Logik enthalten (Prüfung auf `filepath.exists()` + `open(..., 'a')` statt `open(..., 'w')`). Mit altem Code ist der Test rot.

### T2: Fehlender Bericht, ungesendete Woche → Exit 3
- **Prüft:** A2 (Fehlerpfad „Eingabe leer oder ungültig")
- **Aufbau:** Temporäres `LAB_DIR`, `weekly-reports/` vorhanden aber **ohne** Bericht-Datei für die aktuelle ISO-KW. **Keine** Zustandsdatei. `send_scout_email.py` wird als Subprozess aufgerufen.
- **Erwartung:** Exit-Code **3**. stderr-Meldung. Zustandsdatei existiert nicht.
- **Warum misst der Test das Richtige?** Wenn A2 NICHT erfüllt ist (Exit 0 statt 3), schlägt der Test fehl.
- **Gegenprobe:** Die Datei `scripts/send_scout_email.py` muss die Exit-3-Logik enthalten (bestandene Logik aus `scout_kw_doppelversand`). Mit altem Code ohne Exit-3-Logik ist der Test rot.

### T3: SMTP-Fehler nach Zustands-Reservierung → Zustandszeile bleibt, Mail fehlt, kein Zweitversand
- **Prüft:** A3 (Kernanforderung, Fehlerpfad „Gegenstelle antwortet nicht" und „Absturz mitten im Lauf")
- **Aufbau:**
  - Temporäres `LAB_DIR`, Bericht-Datei mit **zwei** Läufen vorhanden (Erstbericht + ein Nachtrag, also erwartete `lauf_nr = 2`).
  - Zustandsdatei mit Zeile für `lauf_nr = 1` (Erstbericht gesendet).
  - `smtplib.SMTP`-Mock wirft `smtplib.SMTPException` beim ersten `sendmail()`-Aufruf.
  - `mode_normal()` aufgerufen.
- **Erwartung:**
  - `mode_normal()` liefert Exit-Code **1**.
  - Zustandsdatei enthält **zwei** Zeilen: `lauf_nr 1` **und** `lauf_nr 2` (die Zustandszeile für `lauf_nr 2` wurde **vor** dem SMTP-Versand geschrieben, A3).
  - `sendmail()`-Mock wurde **genau einmal** aufgerufen.
  - **Zweiter Aufruf** von `mode_normal()`: Liefert Exit-Code **0** („alles gesendet"). `sendmail()`-Mock wird **nicht** erneut aufgerufen (insgesamt immer noch genau einmal).
- **Warum misst der Test das Richtige?** Wenn A3 NICHT erfüllt ist (Zustandszeile wird **nach** dem SMTP-Versand geschrieben), existiert nach dem Fehler nur die Zustandszeile für `lauf_nr 1`. Der zweite Aufruf sieht: Zustandszeile `lauf_nr 1`, Datei hat 2 Läufe → `lauf_nr 2` ungesendet → sendet erneut. Der Mock wird **zweimal** aufgerufen, der Test schlägt fehl.
- **Gegenprobe:** Die Datei `scripts/send_scout_email.py` muss `record_sent_week(lauf_nr=N)` **vor** `send_email_smtp()` aufrufen. Mit altem Code (Zustandszeile nach Versand) ist der Test rot.

### T4: Alles gesendet → Exit 0, keine Mail
- **Prüft:** A2 (Fehlerpfad „Ziel existiert schon"), A3 (Fehlerpfad „Ziel existiert schon")
- **Aufbau:**
  - Temporäres `LAB_DIR`, Bericht-Datei mit **zwei** Läufen (Erstbericht + ein Nachtrag, erwartete `lauf_nr = 2`).
  - Zustandsdatei mit Zeilen für `lauf_nr 1` **und** `lauf_nr 2`.
  - `send_scout_email.py` als Subprozess aufgerufen.
- **Erwartung:** Exit-Code **0**. Meldung „alles gesendet" (oder vergleichbar). `sendmail()`-Mock (falls relevant) wird **nicht** aufgerufen. Zustandsdatei enthält **genau zwei** Zeilen (keine dritte).
- **Warum misst der Test das Richtige?** Wenn A2 NICHT erfüllt ist (keine `lauf_nr`-Logik, nur „KW gesendet"), sendet der Code erneut oder verhält sich undefiniert. Der Test schlägt fehl.
- **Gegenprobe:** Die Datei `scripts/send_scout_email.py` muss `get_last_sent_lauf_nr()` und die Vergleichslogik in `mode_normal()` enthalten. Mit altem Code (nur `is_week_already_sent()`) ist der Test rot.

### T5: Dry-Run berührt Zustandsdatei nicht
- **Prüft:** A5 (alle Fehlerpfade von A5)
- **Aufbau:**
  - Temporäres `LAB_DIR`, Bericht-Datei vorhanden (mit einem Nachtrag).
  - Zwei Szenarien:
    - (a) Zustandsdatei existiert **nicht** vor dem Dry-Run.
    - (b) Zustandsdatei existiert **mit** Zeilen für `lauf_nr 1` und `lauf_nr 2`.
  - `send_scout_email.py --dry-run` als Subprozess aufgerufen.
- **Erwartung:** In beiden Szenarien: Exit-Code 0, `.eml` in `outbox/`. Zustandsdatei: Szenario (a) existiert **nicht**; Szenario (b) enthält **genau zwei** Zeilen (unverändert). `sendmail()`-Mock wird **nie** aufgerufen.
- **Warum misst der Test das Richtige?** Wenn A5 NICHT erfüllt ist (Dry-Run schreibt/liest Zustandsdatei), verändert sich der Inhalt oder die Existenz, der Test schlägt fehl.
- **Gegenprobe:** Bestande Logik aus `scout_kw_doppelversand`. Test ist grün, wenn `mode_dry_run()` die Zustandsdatei nicht berührt.

### T6: Atomarer Zustand – Zustandsdatei bleibt unverändert bei simuliertem Fehler
- **Prüft:** A3 (Fehlerpfad „Absturz mitten im Lauf")
- **Aufbau:**
  - Temporäres `LAB_DIR`, Bericht vorhanden.
  - `record_sent_week(lauf_nr=N)` wird direkt aufgerufen (Unit-Test-Stufe).
  - `os.replace` wird per `unittest.mock.patch` ersetzt und wirft eine `OSError` (simuliert voller Datenträger).
- **Erwartung:** Die Zustandsdatei existiert **nicht** (oder bleibt in ihrem Zustand vor dem Aufruf). Kein halber Eintrag. Die `OSError` wird weitergereicht.
- **Warum misst der Test das Richtige?** Wenn A3 NICHT erfüllt ist (kein atomares Schreiben, z. B. direktes `open(..., "a")`), entsteht bei simuliertem Fehler eine halbe Zustandsdatei, der Test schlägt fehl.
- **Gegenprobe:** Bestande Logik aus `scout_kw_doppelversand` (atomares `os.replace`). Test ist grün, wenn `record_sent_week()` atomar schreibt.

### T7: Pipeline gibt Exit-Code an launchd weiter und schreibt Lauf-Datei
- **Prüft:** A4 (Fehlerpfad „Gegenstelle antwortet nicht" und „Eingabe leer oder ungültig")
- **Höhe:** **Shell-Test auf Python-Ebene**, ohne den echten Scout auszuführen.
- **Aufbau:**
  - Temporäres `LAB_DIR`, **kein** Bericht, **keine** Zustandsdatei.
  - Der Test prüft, dass `run_scout_pipeline.sh` den Exit-Code von `send_scout_email.py` weiterleitet, indem er das Skript mit einem **gesteuerten** `send_scout_email.py`-Aufruf ausführt (der Scout-Schritt wird per `LLAMA_SERVER_URL` auf eine tote URL gesetzt, sodass der Scout mit Exit 2 endet).
  - **Alternativ (empfohlen):** Der Test prüft nur die Weiterleitung des Exit-Codes von `send_scout_email.py` (Subprozess), nicht den gesamten Pipeline-Lauf.
- **Erwartung:** `send_scout_email.py` (Subprozess) liefert Exit-Code **3**. `LAB_DIR/pipeline_runs.log` enthält eine Zeile mit `EMAIL_EXIT=3`. Es wird **keine** Fehler-Mail ausgelöst.
- **Warum misst der Test das Richtige?** Wenn A4 NICHT erfüllt ist (Pipeline gibt Exit 0 oder 1 statt 3, oder schreibt keine Lauf-Datei), schlägt der Test fehl.
- **Gegenprobe:** Bestande Logik aus `scout_kw_doppelversand`. Test ist grün, wenn die Pipeline den Exit-Code weiterleitet und die Lauf-Datei schreibt.

### T8: Import-Test – `llm_scout.py` lässt sich ohne `__main__` importieren
- **Prüft:** Einstiegspunkt-Test für `llm_scout.py` (s. „Einstiegspunkte")
- **Aufbau:**
  - Temporäres `LAB_DIR` gesetzt.
  - `llm_scout.py` wird per `importlib` oder `runpy` mit `run_name="kein_main"` importiert.
- **Erwartung:** Der Import **ohne** Fehler. `main()` wird **nicht** aufgerufen (keine HF/GitHub-Requests, kein `sys.exit()`). Das Modul ist verfügbar.
- **Warum misst der Test das Richtige?** Wenn `llm_scout.py` beim Import `main()` aufruft oder einen Import-Fehler wirft (z. B. relativer Import, fehlende Abhängigkeit), schlägt der Test fehl.
- **Gegenprobe:** Die Datei `agents/llm_scout/llm_scout.py` muss das `if __name__ == "__main__":`-Guard enthalten und keine Seiteneffekte beim Import haben. Mit altem Code ohne Guard oder mit Import-Fehler ist der Test rot.

### T9: Dritter Lauf hängt zweiten Nachtrag an
- **Prüft:** A1 (Akzeptanz: „Ein dritter Lauf derselben ISO-KW hängt einen weiteren Nachtrag an")
- **Aufbau:**
  - Temporäres `LAB_DIR`, `weekly-reports/` angelegt.
  - Bericht-Datei manuell angelegt mit Inhalt: „ERSTBERICHT_INHALT" + Nachtrag 1 (mit „## Nachtrag KW…"-Header + „NACHTRAG1_INHALT").
  - Die Anhäng-Funktion aus `llm_scout.py` wird aufgerufen mit `report_content="NACHTRAG2_INHALT"`.
- **Erwartung:**
  - Die Datei enthält „ERSTBERICHT_INHALT" (byte-identisch am Anfang).
  - Die Datei enthält „NACHTRAG1_INHALT" (byte-identisch).
  - Die Datei enthält eine **zweite** „## Nachtrag KW…"-Header-Zeile.
  - Die Datei endet mit „NACHTRAG2_INHALT".
- **Warum misst der Test das Richtige?** Wenn A1 NICHT erfüllt ist (z. B. die Funktion überschreibt bei Zweitlauf, statt anzuhängen), ist der Inhalt nicht wie erwartet. Der Test schlägt fehl.
- **Gegenprobe:** Wie T1 – die neue Anhäng-Logik muss in `llm_scout.py` vorhanden sein.

## Offene Fragen

- **Keine.** Die zentrale offene Frage (Nachtrag vs. Zusammenführen) ist entschieden (Nachtrag, s. „Entscheidung"). Die A3-Abgrenzung (Zustandszeile vor Versand) ist als bewusste Abweichung von `scout_kw_doppelversand` dokumentiert und begründet.

## Abweichende Meinung

- **A3 – Zustandszeile vor Versand (bewusste Abweichung von `scout_kw_doppelversand` A1):** Die dortige Anforderung „Zustandszeile nur nach erfolgreichem `sendmail()`" wird hier **aufgebrochen**. Begründung: Bei Nachträgen führt die Nach-Verdikt-Logik zum Datenverlust. Szenario: Lauf 2 schreibt den Nachtrag in die Datei, Zustandszeile wird **nach** dem SMTP-Versand geschrieben. Zwischen Datei-Schreib und Zustands-Write crasht die Pipeline. Nächster Lauf: Zustandszeile fehlt → `send_scout_email.py` denkt, `lauf_nr 2` sei ungesendet → sendet. Aber `llm_scout.py` schreibt **keinen** neuen Nachtrag (die Items sind markiert, kein neuer Lauf), also: Die Mail geht, aber sie enthält **keinen** neuen Inhalt – oder schlimmer: Der Scout findet keine neuen Items, beendet mit Exit 0, und `send_scout_email.py` sendet den **alten** Bericht erneut (Doppelversand des Erstberichts). Mit Zustands-Write **vor** Versand: Crash → Zustandszeile existiert, Mail fehlt → nächster Lauf: Exit 0, keine Mail. **Datenverlust: kein.** **Doppelversand: nein.** **Verlust:** Der Nachtrag fehlt in der Mail (wird nie gesendet). Das ist das kleinere Übel. **Entscheidung:** Zustandszeile vor Versand. Das Restrisiko „Nachtrag fehlt in der Mail nach Crash" wird akzeptiert und ist in der Fehlerpfad-Tabelle (A3, „Absturz mitten im Lauf") dokumentiert.

- **A1 – Teilweiser Nachtrag nach Crash (Restrisiko):** Ein `KeyboardInterrupt` oder OOM während des Anhängens kann eine Datei mit teilweisem Nachtrag hinterlassen. Die nächste Lauf-Anhäng-Logik erkennt den teilweise Nachtrag **nicht** und hängt einen weiteren an. Die Datei enthält dann einen kaputten Nachtrag + einen kompletten. **Entscheidung:** Akzeptiert. Die Wahrscheinlichkeit ist gering (das Anhängen ist ein einzelner `f.write()`-Aufruf), und die Bereinigung würde eine Parsing-Logik für Markdown erfordern, die überproportional ist. Die Datei bleibt lesbar, der Erstbericht ist intakt.
