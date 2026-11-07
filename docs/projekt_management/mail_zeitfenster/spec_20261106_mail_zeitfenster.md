# Spec: mail_zeitfenster

- **Datum:** 2026-11-06
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette_lauf` aus der Chat-UI
- **Betroffene Dateien:** `agents/mail_planung/mail_planung.py` (Import, drei neue Funktionen, `fetch_mails`, `run_dry`, `main`)
- **Änderungsstellen:** 6 (Import; neuer Block direkt vor `fetch_mails`; in `fetch_mails` Kopf/Suche und Schleife/Zusammenfassung; `run_dry`; `main`)

## Ziel

Erste Kette des Piloten „Idee bis Commit“ (`mail_planung` am echten eigenen Postfach, Entscheidung Hawe 02.11.): `mail_planung` holt nicht mehr das ganze Postfach, sondern nur Mails ab einem Stichtag (Standard: heute) und je Lauf höchstens eine Höchstzahl **neuer** Mails (Standard 20, älteste zuerst). Bekannte Mails werden nur an der Kopfzeile `Message-ID` erkannt und nicht vollständig geladen; der Rest kommt beim nächsten Lauf, nichts geht verloren. Heute lädt `fetch_mails` mit `search(None, "ALL")` jede Mail vollständig, und der Trockenlauf schickt jede an das Modell – an einem echten Postfach liefe schon der erste Trockenlauf stundenlang. Entscheidungen Hawe 06.11.: 20 je Lauf, älteste zuerst; nur heute als Standard; erster Echtlauf nur als Trockenlauf.

## Nicht-Ziele

- **`tests/test_mail_zeitfenster.py` ist Vorgabe und wird nicht geändert – keine Zeile.** Ebenso `tests/test_mail_planung.py` (Bestand, 31 Tests, bleibt grün).
- Keine Änderung an `process_mail`, `build_block`, `evaluate_mail`, `atomic_write_plan`, dem DB-Schema, der Projekt-Zuordnung oder `agents/mail_planung/test_imap_server.py`.
- Keine Änderung an den kaputten Umlauten in Kommentaren und Meldungen (`f�r` …), außer in den Zeilen, die ohnehin ersetzt werden.
- Kein Gelesen-Markieren, kein Verschieben, kein Löschen im Postfach; `select("INBOX", readonly=True)` bleibt.
- Kein echter Mailserver, kein Schlüsselbund, kein Modell in Tests. Den Echtlauf startet Hawe selbst.
- Alle bestehenden Tests bleiben grün (`python3 scripts/alle_tests.py`; Altlast `test_scout_kw_doppelversand.py` bleibt rot).

## Schreibbereich

- `agents/mail_planung/mail_planung.py`

## Vorgabe-Tests

- `tests/test_mail_zeitfenster.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** IMAP-Verbindung zum echten Postfach, Zugriff auf den Schlüsselbund (`security find-generic-password`), Aufruf des Modells auf 8080, Schreiben nach `MAIL_PLAN_DIR` (Standard `~/lab`). Alles nur lesend am Postfach.
- **Technische Sperre für Tests:** `imaplib.IMAP4_SSL` wird durch `FakeIMAP` (erfundene Mails im Test) ersetzt, `get_imap_password` und `requests.post` durch Attrappen; `MAIL_PLAN_DIR`, `DB_PATH`, `PLAN_FILE` zeigen je Test auf `tempfile.mkdtemp()`. T8 startet das Skript mit ungültiger Einstellung, `IMAP_HOST=127.0.0.1`, Port 1 und einem nicht vorhandenen Schlüsselbund-Dienst – der Lauf endet vor Schlüsselbund, DB und IMAP.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `agents/mail_planung/mail_planung.py` | `python3 agents/mail_planung/mail_planung.py --dry-run` und ohne Schalter (von Hand, später launchd) | T8 |
| `agents/mail_planung/mail_planung.py` | als Modul (`main`, `run_dry`, `fetch_mails`, `zeitfenster`, `imap_datum`, `bekannte_ids`) | T1–T7 |

## Quellen

- `agents/mail_planung/mail_planung.py` Zeilen 20–75 – Importe und Konstanten (Einfügestelle für `date`, `timedelta`)
- `agents/mail_planung/mail_planung.py` def init_db – Tabelle `processed_mails` (Spalte `message_id`)
- `agents/mail_planung/mail_planung.py` def mark_as_processed – wie Message-IDs gespeichert werden
- `agents/mail_planung/mail_planung.py` def get_message_id – Message-ID wird mit `.strip()` gespeichert; ohne Header synthetisch (braucht den ganzen Text)
- `agents/mail_planung/mail_planung.py` def fetch_mails – Einbaustelle Suche, Schleife, Zusammenfassung
- `agents/mail_planung/mail_planung.py` def run_dry – Einbaustelle Trockenlauf
- `agents/mail_planung/mail_planung.py` def main – Einbaustelle Normallauf
- `tests/test_mail_planung.py` Zeilen 37–90 – Bestand-Testaufbau (Modul neu laden, Pfade umbiegen, Attrappen)
- `tests/test_mail_zeitfenster.py` – Vorgabe-Tests (`FakeIMAP`, Meldetexte wörtlich übernehmen)

## Anforderungen

### A1: Einstellungen, IMAP-Datum, bekannte Message-IDs
- **Anforderung:** Import `from datetime import datetime` wird zu `from datetime import date, datetime, timedelta`. Direkt vor `def fetch_mails` neu:
  1. `IMAP_MONATE = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")`.
  2. `zeitfenster() -> tuple` liest **beim Aufruf** (nicht beim Import) `os.getenv("MAIL_SINCE_DAYS", "0")` und `os.getenv("MAIL_MAX_JE_LAUF", "20")`, je `.strip()`, `int(...)`; Mindestwert 0 bzw. 1. Nicht ganzzahlig oder zu klein → `ValueError` mit genau `<NAME> ungültig: '<wert nach strip>' (ganze Zahl ≥ <minimum>)`. Rückgabe `(tage, hoechstens)`.
  3. `imap_datum(tag: date) -> str` → `f"{tag.day:02d}-{IMAP_MONATE[tag.month - 1]}-{tag.year}"`, z. B. `06-Nov-2026`. **Kein `strftime`** (deutsche Locale liefert „Mai“, „Dez“; der IMAP-Server versteht nur englische Monatsnamen).
  4. `bekannte_ids(conn) -> set` → alle `message_id` aus `processed_mails`.
- **Stelle:** `agents/mail_planung/mail_planung.py`, Importzeile `from datetime import datetime`; neuer Block unmittelbar vor `def fetch_mails`.
- **Akzeptanz:** T1, T8.

### A2: `fetch_mails` mit Stichtag, Höchstzahl und bekannten IDs
- **Anforderung:** Signatur `fetch_mails(host, port, user, password, since: Optional[str] = None, max_anzahl: Optional[int] = None, bekannt: Optional[set] = None)`; Aufrufe ohne die neuen Argumente verhalten sich wie bisher (alle Mails, `ALL`).
  1. Nach `select("INBOX", readonly=True)`: `since` gesetzt → `imap.search(None, "SINCE", since)`, sonst `imap.search(None, "ALL")`.
  2. Schleife über die Treffer **in der gelieferten Reihenfolge** (älteste zuerst). Je Treffer zuerst `imap.fetch(mid, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])")`; Message-ID daraus mit `email.message_from_bytes(...).get("Message-ID", "")` und `.strip()`.
  3. Message-ID in `bekannt` → zählt als „schon verarbeitet“, **kein** `(RFC822)`-Abruf, weiter.
  4. Message-ID vorhanden und `max_anzahl` erreicht (schon `max_anzahl` neue geholt) → zählt zum Rest, **kein** `(RFC822)`-Abruf, **weiter** (nicht abbrechen – der Rest muss vollständig gezählt werden).
  5. Sonst `(RFC822)` holen und wie bisher in `mails` aufnehmen; nur Mails **mit** Message-ID zählen zur Höchstzahl. Mails ohne Message-ID werden immer geholt (ihre synthetische ID braucht den ganzen Text; `process_mail` erkennt Bekannte).
  6. Nach `imap.logout()` genau eine Zeile auf stdout: `Postfach: <Treffer> Mails seit <since oder Beginn>, <bekannt> schon verarbeitet, <geholt> geholt, <rest> beim nächsten Lauf.`
- **Stelle:** `agents/mail_planung/mail_planung.py`, `def fetch_mails` (Kopf und `search`; Schleife; Zeile vor `return mails`).
- **Akzeptanz:** T2, T3, T4, T7.

### A3: `main` und `run_dry` verdrahten
- **Anforderung:** Gleiche Reihenfolge in beiden:
  1. `tage, hoechstens = zeitfenster()`; `ValueError` → Meldung auf stderr, `return 1` – **vor** Schlüsselbund, DB und IMAP.
  2. `get_imap_password()`; `RuntimeError` → Meldung auf stderr, `return 1` (in `run_dry` neu: bisher Traceback).
  3. DB öffnen und `init_db` **vor** dem Abruf; dann `fetch_mails(IMAP_HOST, IMAP_PORT, IMAP_USER, password, since=imap_datum(date.today() - timedelta(days=tage)), max_anzahl=hoechstens, bekannt=bekannte_ids(conn))`; Fehler → wie bisher `IMAP-Verbindung fehlgeschlagen: …`, `return 1`.
  4. Danach wie bisher: keine Mails → `Keine neuen Mails`, Exit 0; sonst `process_mail` je Mail (`run_dry`: `dry_run=True`, DB unverändert). Verbindung in `finally` schließen.
- **Stelle:** `agents/mail_planung/mail_planung.py`, `def run_dry` und `def main`.
- **Akzeptanz:** T5, T6, T7, T8.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Einstellung leer gelassen | – | Standard 0 / 20 | T1 |
| A1 | ungültig (`abc`, `2.5`, `-1`, Max `0`) | nichts | `ValueError` mit Meldung; Lauf Exit 1 vor Schlüsselbund/IMAP, nichts angelegt | T1, T5, T6, T8 |
| A1 | deutsche Locale am Mac | – | englische Monatsnamen (`May`, `Dec`) | T1 |
| A2 | Gegenstelle antwortet nicht / Fehler bei der Suche | – | wie bisher (`status != "OK"` → leer; Ausnahme → Exit 1 in main/run_dry) | – (unverändert) |
| A2 | mehr neue Mails als Höchstzahl | – | älteste zuerst, Rest gezählt, nicht vollständig geladen | T3 |
| A2 | bekannte Mails im Fenster | DB-Einträge | nur Kopfzeile gelesen, übersprungen, zählen nicht zur Höchstzahl | T4 |
| A2 | Mail ohne Message-ID | – | immer geholt, zählt nicht mit | T4 |
| A2 | Aufruf ohne neue Argumente (Bestand) | – | wie bisher `ALL`, alle Mails | T2 |
| A3 | Schlüsselbund-Eintrag fehlt im Trockenlauf | nichts | Exit 1, Meldung, kein Traceback, kein IMAP | T6 |
| A3 | Lauf ohne Testschalter (echtes Postfach) | – | Hawe startet selbst, zuerst `--dry-run` | – |
| A3 | mehrere Läufe hintereinander | Marker der verarbeiteten Mails | jede Mail genau einmal in der Planung, letzter Lauf „Keine neuen Mails“ | T7 |
| A3 | Absturz mitten im Lauf | bis dahin geschriebene Einträge + Marker | unverändert (Marker erst nach Schreiben); fehlende Mails beim nächsten Lauf | T7 (indirekt) |

## Testplan

Die Tests stehen in `tests/test_mail_zeitfenster.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Vorab 8/8 rot; gegen die Referenz 8/8 grün, dreimal stabil (< 1 s); `tests/test_mail_planung.py` 31/31 grün mit altem und neuem Code. Mutationsprüfung der Referenz: 20 von 20 gefangen (u. a. immer `ALL`, `strftime` mit Locale, Bekannte zählen zur Höchstzahl, Bekannte voll geladen, ohne Message-ID zählt mit, Rest nicht gezählt, `break` statt `continue`, neueste zuerst, `>` statt `>=`, Einstellungen nach Schlüsselbund, `bekannt` nicht übergeben, Schlüsselbund-Fehler in `run_dry` nicht gefangen, Einstellung beim Import gelesen, Max 0 erlaubt, Tage addiert/ignoriert, Standard 50, anderer Meldetext).

### T1: Einstellungen und IMAP-Datum
- **Prüft:** A1
- **Aufbau:** Umgebungsvariablen gesetzt/entfernt; `date`-Unterklasse, deren `strftime`/Format-Angabe fehlschlägt; zusätzlich deutsche Locale, wenn vorhanden.
- **Erwartung:** `(0, 20)` ohne Variablen, `(3, 5)` für `" 3 "`/`"5"`; fünf ungültige Werte mit genauer Meldung; `06-Nov-2026`, `01-May-2026`, `31-Mar-2027`, `09-Dec-2026`.
- **Warum misst der Test das Richtige?** Ein `strftime("%d-%b-%Y")` bestünde am englischen System, aber nicht am Mac mit deutscher Einstellung – die Unterklasse fängt das überall.
- **Gegenprobe:** alter Stand → rot (Funktionen fehlen).

### T2: Suche mit SINCE und Bestand-Aufruf
- **Prüft:** A2
- **Aufbau:** `FakeIMAP` mit drei Mails; einmal mit `since`, einmal ohne.
- **Erwartung:** Suche `("SINCE", "06-Nov-2026")` bzw. `("ALL",)`; `select` read-only; ohne Argumente alle drei vollständig.
- **Warum misst der Test das Richtige?** Ohne SINCE holt das Werkzeug wieder das ganze Postfach.
- **Gegenprobe:** alter Stand → rot (`since` unbekannt).

### T3: Höchstzahl, älteste zuerst, Zusammenfassung
- **Prüft:** A2
- **Aufbau:** 25 neue Mails, Höchstzahl 20.
- **Erwartung:** Mails 1–20 in dieser Reihenfolge, nur diese vollständig geladen; Zeile `Postfach: 25 Mails seit 06-Nov-2026, 0 schon verarbeitet, 20 geholt, 5 beim nächsten Lauf.`
- **Warum misst der Test das Richtige?** Ein `break` beim Erreichen der Höchstzahl liefert dieselben 20 Mails, aber den falschen Rest.
- **Gegenprobe:** alter Stand → rot.

### T4: Bekannte und Mails ohne Message-ID
- **Prüft:** A2
- **Aufbau:** 6 Mails, Mail 1 und 2 bekannt, Mail 4 ohne Message-ID, Höchstzahl 2.
- **Erwartung:** geholt 3, 4, 5 (nur diese vollständig), Kopfzeile von allen 6; Zeile `… 6 Mails seit 06-Nov-2026, 2 schon verarbeitet, 3 geholt, 1 beim nächsten Lauf.`
- **Warum misst der Test das Richtige?** Zählten Bekannte zur Höchstzahl, käme der Lauf nie über die ersten Mails hinaus.
- **Gegenprobe:** alter Stand → rot.

### T5: `main` – Reihenfolge und Werte
- **Prüft:** A3, A1
- **Aufbau:** `MAIL_MAX_JE_LAUF=abc`; dann `7` und `MAIL_SINCE_DAYS=2` mit einem DB-Eintrag, `fetch_mails` als Attrappe.
- **Erwartung:** Exit 1, Meldung auf stderr, Schlüsselbund und IMAP nicht berührt; sonst `since` = Datum von vorgestern, `max_anzahl` 7, `bekannt` = `{"<alt@test>"}`.
- **Warum misst der Test das Richtige?** Prüft die Verdrahtung über den echten Aufruf (R58), nicht nur die Hilfsfunktionen.
- **Gegenprobe:** alter Stand → rot.

### T6: `run_dry` – Verdrahtung und Fehler
- **Prüft:** A3
- **Aufbau:** DB mit Mail 1; drei Mails, Höchstzahl 1; dann Schlüsselbund-Fehler; dann `MAIL_SINCE_DAYS=-2`.
- **Erwartung:** Suche mit heutigem Datum, nur Mail 2 geladen, eine Vorschau, DB und Planung unverändert; Schlüsselbund-Fehler Exit 1 ohne IMAP; ungültige Tage Exit 1 mit Meldung.
- **Warum misst der Test das Richtige?** Der erste Echtlauf ist ein Trockenlauf – genau dieser Pfad muss begrenzt sein.
- **Gegenprobe:** alter Stand → rot.

### T7: Nichts geht verloren
- **Prüft:** A3, A2
- **Aufbau:** 5 Mails, Höchstzahl 2, vier Läufe von `main` nacheinander (Modell durch Attrappe ersetzt).
- **Erwartung:** vollständig geladen `[1, 2]`, `[3, 4]`, `[5]`, `[]`; jede Mail genau einmal in der Planung und in der DB; letzter Lauf „Keine neuen Mails“.
- **Warum misst der Test das Richtige?** Bildet Hawes Entscheidung nach: Der Rest kommt beim nächsten Lauf, nichts doppelt, nichts verloren.
- **Gegenprobe:** alter Stand → rot (alle 5 im ersten Lauf).

### T8: Als Skript
- **Prüft:** A3, A1 (R58: echter Einstieg)
- **Aufbau:** Unterprozess `python3 agents/mail_planung/mail_planung.py --dry-run` und ohne Schalter, `MAIL_MAX_JE_LAUF=abc`, leeres `MAIL_PLAN_DIR`.
- **Erwartung:** je Exit 1, Meldung auf stderr, kein Traceback, keine Schlüsselbund-Meldung, `MAIL_PLAN_DIR` bleibt leer.
- **Warum misst der Test das Richtige?** So startet Hawe den Echtlauf; eine falsche Einstellung darf nichts anfassen.
- **Gegenprobe:** alter Stand → rot (Einstellung unbekannt, Schlüsselbund wird gefragt).

## Offene Fragen

- Keine

## Abweichende Meinung

- „Heute“ meint das Eingangsdatum auf dem Mailserver (IMAP `SINCE`), nicht den `Date`-Kopf der Mail; Mails kurz nach Mitternacht können je nach Server-Zeitzone einen Tag früher oder später fallen.
- Mails ohne Message-ID werden bei jedem Lauf im Fenster vollständig geladen und zählen nicht zur Höchstzahl – selten, und nur so bleibt die synthetische ID erhalten.
- Der Trockenlauf markiert nichts; wiederholte Trockenläufe zeigen dieselben ersten 20 Mails. Gewollt (Vorschau ohne Wirkung).
- Kaputte Umlaute in bestehenden Meldungen (`f�r`) bleiben – eigene kleine Kette, falls es stört.
