# Spec: kette_review_auto

- **Datum:** 2026-10-25
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Betroffene Dateien:** `role-split/kette/kette.py`, `role-split/kette/prompts/review.md`, `role-split/kette/prompts/review2.md`, `role-split/kette/test_kette.py`, `agents/mail_planung/mail_planung.py` (alle gelesen, Fundstellen in „Quellen")

## Ziel

Ein Befehl `python3 role-split/kette/kette.py review-auto <kurztitel>` führt die Review-Phase automatisch aus: `pruefen` (Tests rot → Abbruch), Review-Paket bauen, zwei Review-Läufe über die Router-API (127.0.0.1:8080, Modell Qwen3.6-35B-A3B, Reasoning aus) mit Paket im Prompt und ohne Werkzeuge, Verdikte abspeichern (ohne Überschreiben), auswertbare Befund-Tabelle prüfen, zusammenführen, kurze Zusammenfassung ausgeben.

## Nicht-Ziele

- Kein automatischer Nachbesserungs-Lauf oder dritter Review-Lauf; das Gesamtbefund ist Endpunkt.
- Kein Streamen der Modellantwort. Fortschritt während eines Laufs nur als Herzschlag-Zeile (A4), nicht als Teiltext.
- Die manuelle Phase D (Browser-Chat) bleibt erhalten; `review-auto` ist parallel dazu der automatische Weg.
- Kein Ändern des bestehenden Dateinamen-Schemas für `gesamt_*.md` oder der bestehenden Befehle.
- Kein Retry einzelner Läufe; ein fehlgeschlagener Lauf bricht den ganzen Befehl ab (Exit 1).

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** HTTP-POST an die lokale Router-API `127.0.0.1:8080` (nur Loopback, keine externen Adressen). Die Modellantwort wird nur als Text in `docs/projekt_management/` gespeichert und nie ausgeführt. Keine Mails, keine echten Daten, kein Schlüsselbund, kein launchd.
- **Technische Sperre für Tests:** (1) Die API-Adresse kommt aus der Umgebungsvariable `KETTE_LLM_URL` (Default `http://127.0.0.1:8080`) – Tests setzen `KETTE_LLM_URL` auf einen simulierten HTTP-Server auf `127.0.0.1` in einem freien Port (Temporäres Verzeichnis für alle Verdikt-/Gesamt-Dateien über die bestehende Struktur, `PM` wird im Test umgebungsübergreifend durch einen Temp-Pfad ersetzt, so wie `test_kette.py` mit `tempfile.TemporaryDirectory` arbeitet). (2) Der Modellname und `enable_thinking: false` sind feste Parameter in demselben Aufruf, den der Test gegen den simulierten Server prüft – der Test misst, dass im JSON-Body `enable_thinking` fehlt oder `false` ist und der Modellname exakt stimmt. Eine Regel im Prompt reicht nicht, weil der Test den tatsächlich gesendeten Body prüft. (3) **„Nur 127.0.0.1" ist im Code erzwungen:** Ist der Host in `KETTE_LLM_URL` nicht `127.0.0.1` oder `localhost`, bricht `review-auto` vor jedem Request mit Exit 1 ab (A8, T11). (Korrektur 25.10. nach Gegenprüfung.)

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py review-auto <kurztitel>` von Hand (neuer Subbefehl, wie die bestehenden) | T1, T2, T3, T4, T5, T6, T7 |
| `role-split/kette/kette.py` | Modul-Import für Tests (`import kette`, dann `kette.review_auto(…)`) | T8 |
| `role-split/kette/kette.py` | **Echter Lauf durch Hawe** am K7-Stand: `python3 role-split/kette/kette.py review-auto mail_server_test` gegen den echten Router | T14 |

## Quellen

- `role-split/kette/kette.py` Zeilen 449–493 – Aufruf für Schritt 1 (Tests) per `def pruefen`; Rückgabe `max(codes.values())` über abgleich, unittest und gegenprobe – also auch 1, wenn nur abgleich oder gegenprobe abweichen (in K7 bei jedem Durchgang so). Für A2 wird das Teilergebnis `unittest` gebraucht (siehe A2).
- `role-split/kette/kette.py` Zeilen 640–694 – Aufruf für Schritt 2 per `def paket`; Rückgabe 0 = Paket geschrieben; schreibt `review_paket_<datum>_<kurztitel>.md`.
- `role-split/kette/kette.py` Zeilen 698–704 – Wiederverwendung für die auswertbare-Tabelle-Prüfung (A5) per `def _befunde` und `def _ist_hoch`.
- `role-split/kette/kette.py` Zeilen 84–115 – Parsing der Verdikt-Antwort (Befund-Tabelle erkennen) per `def abschnitt`, `def tabelle`, `def spalte`, `def ja`.
- `role-split/kette/kette.py` Zeilen 707–753 – Aufruf für Schritt 6 per `def zusammenfuehren`; schreibt `gesamt_<datum>_<kurztitel>.md`.
- `role-split/kette/kette.py` Zeilen 1002–1054 – Muster für Prompt-Aufbau (Platzhalter, `<!--`-Zeilen streichen) per `def prompt`.
- `role-split/kette/kette.py` Zeilen 1058–1103 – Muster für Subbefehl-Registrierung im `argparse` per `def main`.
- `role-split/kette/kette.py` Zeilen 253–260 – Rücksetzpunkt bestimmen (Commit „Spec <kurztitel>") per `def datei_suchen`.
- `role-split/kette/kette.py` Zeilen 438–446 – Rücksetzpunkt bestimmen per `def spec_commit`; für die Paket-/Prüfungsschritte.
- `role-split/kette/prompts/review.md` – ganze Datei (Zeilen 1–27) – Basis für die API-Fassung von Lauf 1; enthält die Sätze mit Datei-Zugriff („Lies NUR {paket}", „write_file", „append_file"), die in der API-Fassung gestrichen/ersetzt werden.
- `role-split/kette/prompts/review2.md` – ganze Datei (Zeilen 1–13) – Basis für die API-Fassung von Lauf 2 (Betrieb).
- `agents/mail_planung/mail_planung.py` Zeilen 540–554 – bewährtes Muster für den API-Aufruf: `requests.post` auf `{URL}/v1/chat/completions`, JSON mit `model`, `messages`, `temperature`, `chat_template_kwargs: {"enable_thinking": False}`, `timeout`.
- `docs/projekt_management/_vorlage_verdict.md` – ganze Datei (Zeilen 1–45) – erwartete Form des Verdikts (Abschnitte Ergebnis, Anforderungen einzeln, Befunde mit Spalten Datenverlust/Unbemerkt/Harte Vorgabe), woran die auswertbare-Tabelle-Prüfung gemessen wird.
- `role-split/kette/test_kette.py` Zeilen 1–40 – Muster für die Teststruktur (unittest, `tempfile.TemporaryDirectory`, `redirect_stdout`, `sys.path.insert`).

## Anforderungen

### A1: Neue Prompts ohne Datei-Zugriff
- **Anforderung:** `review-auto` sendet für Lauf 1 und Lauf 2 einen Prompt, der das Review-Paket direkt als Text enthält, und keine Sätze enthält, die Dateizugriff verlangen („Lies NUR {paket}", „write_file", „append_file", „search_files", „Ziel existiert schon …"). Der Prompt verlangt das Verdikt im Format nach `_vorlage_verdict.md` als reine Textantwort.
- **Stelle:** neue Funktion `review_auto` in `role-split/kette/kette.py`; Prompt-Texte auf Basis von `role-split/kette/prompts/review.md` / `review2.md` (neue Vorlagen oder inline-Texte).
- **Akzeptanz:** Der gesendete Prompt (im simulierten Testserver protokolliert) enthält den vollständigen Paket-Text und keine der verbotenen Wendungen; die Antwort des Modells wird nicht als Datei erwartet.

### A2: Prüfen zuerst, nur rote Unit-Tests → Abbruch
- **Anforderung:** `review-auto` führt zuerst die Prüfung aus (abgleich, unittest, gegenprobe; Ausgabe wie bisher nach `pruefung_<datum>_<kurztitel>.md`). **Abgebrochen wird nur, wenn der Teil `unittest` rot ist** (Exit ≠ 0): Meldung „Unit-Tests rot – direkt nachbessern, kein Review nötig", Exit 1, kein Paket, kein Request. Abweichungen in `abgleich` oder `gegenprobe` sind **kein** Abbruchgrund (RUNBOOK Phase C: „im Review/Gegenprüfung ansehen lassen") – sie stehen im Paket. Ein Werkzeugfehler der Prüfung (Teil-Exit 2, z. B. kein Spec-Commit) → Exit 2 mit Meldung.
- **Umsetzung:** `pruefen` wird so aufgeteilt, dass die Teil-Ergebnisse abfragbar sind (z. B. neue Hilfsfunktion `_pruefen_teile(kurztitel, …) -> dict` mit den Schlüsseln `abgleich`, `unittest`, `gegenprobe`; `pruefen` nutzt sie und verhält sich nach außen unverändert – Rückgabe, Ausgabe und Datei wie bisher).
- **Stelle:** `role-split/kette/kette.py` `def pruefen` (Zeilen 449–493) und `def review_auto`.
- **Akzeptanz:** unittest rot → Exit 1, Meldung, kein `review_paket_*.md`, kein Request. unittest grün, abgleich und gegenprobe mit Abweichung → Review läuft. Bestehende Tests von `pruefen` in `test_kette.py` bleiben grün.

### A3: Review-Paket bauen
- **Anforderung:** Nach erfolgreicher Prüfung baut `review-auto` das Paket mit `paket(kurztitel)` (Rückgabe 0). Fehlt eine Voraussetzung (keine Spec, kein Rücksetzpunkt) → Exit 2 mit Meldung.
- **Stelle:** `role-split/kette/kette.py` `def review_auto` (Aufruf von `paket`, Zeilen 640–694).
- **Akzeptanz:** `review_paket_<datum>_<kurztitel>.md` existiert im Test-Verzeichnis; bei `paket`-Rückgabe 2: Exit 2, keine HTTP-Requests.

### A4: Zwei Review-Läufe über die API
- **Anforderung:** `review-auto` ruft nacheinander Lauf 1 (Anforderung) und Lauf 2 (Betrieb) auf `<KETTE_LLM_URL>/v1/chat/completions` auf. Modell aus `KETTE_LLM_MODEL`, Default **`unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL`** (voller Router-Name; nur „Qwen3.6-35B-A3B" findet der Router nicht). `chat_template_kwargs: {"enable_thinking": false}`. Timeout je Lauf aus `KETTE_LLM_TIMEOUT`, Default 1800 s. Beide Läufe bekommen denselben Paket-Text.
- **Fortschritt live:** Vor jedem Lauf „Lauf 1 von 2 (Anforderung) gestartet, erwartet 15–25 min"; **während** des Laufs eine Herzschlag-Zeile alle `KETTE_HERZSCHLAG_S` Sekunden (Default 60), z. B. „Lauf 1: 7 min …" (sofort ausgegeben, ungepuffert). Nach dem Lauf Dauer und `usage.prompt_tokens`/`completion_tokens`, falls geliefert.
- **Stelle:** `role-split/kette/kette.py` `def review_auto`; API-Muster nach `agents/mail_planung/mail_planung.py` Zeilen 540–554 (dort `requests`; ob `kette.py` stdlib bleibt – `urllib.request` – entscheidet die Umsetzung; `kette.py` nutzt bisher nur die stdlib).
- **Akzeptanz:** Der simulierte Server erhält genau 2 Requests, Body mit Modellname aus `KETTE_LLM_MODEL` und `enable_thinking: false`; Herzschlag-Zeilen erscheinen bei kurzem Intervall; kein dritter Request.

### A5: Verdikte speichern, nie überschreiben
- **Anforderung:** Die Antwort jedes Laufs wird als Verdikt-Datei gespeichert: Lauf 1 `verdict_<datum>_<kurztitel>_qwen36-35b.md`, Lauf 2 `verdict_<datum>_<kurztitel>_qwen36-35b_betrieb.md` (Schema wie K7). Existiert der Name schon, wird **automatisch umbenannt** zum ersten freien Namen mit Zähler **`_2`, `_3` …** vor `.md` (nicht `_lauf2` – „Lauf 2" bedeutet bei uns den Betriebs-Lauf). Der Name wird **unmittelbar vor dem Schreiben** gewählt und **exklusiv** angelegt (Öffnen nur, wenn die Datei nicht existiert, z. B. Modus `"x"`); scheitert das, nächster Zähler. Eine vorhandene Datei wird nie verändert.
- **Stelle:** `role-split/kette/kette.py` `def review_auto`.
- **Akzeptanz:** Vorhandene Datei mit dem Basisnamen → neue Datei `…_qwen36-35b_2.md`, alte Datei bitgleich (Hash). Lauf 1 und Lauf 2 erhalten verschiedene Dateien.

### A6: Auswertbare Befund-Tabelle
- **Anforderung:** Für jedes gespeicherte Verdikt prüft `review-auto`, dass eine auswertbare Befund-Tabelle vorliegt: Abschnitt „Befunde" existiert, und die erste Tabelle darin hat die Spalten „#", „Datenverlust", „Unbemerkt", „Harte Vorgabe", „Schwere" (Prüfung mit `abschnitt`/`tabelle`/`spalte`, so wie `zusammenfuehren` liest). Hawes Entscheidung (Rückfrage 12:17, Antwort b): Fehlt sie in einem Lauf, wird **trotzdem** aus den gültigen Läufen zusammengeführt – aber
  - das **Ergebnis im Gesamtbefund lautet „UNVOLLSTÄNDIG"**, nie PASS, auch wenn der gültige Lauf PASS sagt;
  - oben im Gesamtbefund steht der Warnhinweis „Ein Lauf ohne auswertbare Befund-Tabelle: <Datei> – Gesamtbefund beruht nur auf <n> Lauf/Läufen";
  - Exit 1 und laute Meldung („laut abbrechen" aus der Anforderung).
  Sind **beide** Läufe nicht auswertbar: kein Gesamtbefund, Exit 1.
- **Stelle:** `role-split/kette/kette.py` `def review_auto` (Wiederverwendung `abschnitt`, `tabelle`, `spalte`, Zeilen 84–115; Ergebnis-Zeile von `zusammenfuehren` wird für diesen Fall überschrieben oder `zusammenfuehren` bekommt einen Parameter dafür).
- **Akzeptanz:** Lauf 2 ohne Pflicht-Spalten, Lauf 1 gültig mit PASS → Exit 1, Meldung, `gesamt_*.md` mit „UNVOLLSTÄNDIG" und Warnhinweis, ohne „PASS" als Ergebnis; Befunde aus Lauf 1 enthalten.

### A7: Zusammenführen und Zusammenfassung
- **Anforderung:** Nach den Läufen führt `review-auto` die beiden gültigen Verdikte mit `zusammenfuehren` zusammen (Rückgabe wie bisher: 0 = PASS, 1 = NACHBESSERN/FAIL). Am Ende gibt der Befehl eine kurze Zusammenfassung aus: Ergebnis (PASS/NACHBESSERN/FAIL/UNKLAR), Anzahl hoher Befunde, Dateipfade der beiden Verdikte und des Gesamtbefunds.
- **Stelle:** `role-split/kette/kette.py` `def review_auto` (Aufruf von `zusammenfuehren`, Zeilen 707–753).
- **Akzeptanz:** Die Stdout-Protokollierung enthält die drei Angaben; `gesamt_<datum>_<kurztitel>.md` existiert.

### A8: Fehlerfälle
- **Anforderung:** Jeder dieser Fälle → Exit 1 mit **eigener, klarer** Meldung; keine halben Ergebnisse (ein bereits gespeichertes gültiges Verdikt bleibt, das fehlerhafte wird nicht gespeichert, kein Gesamtbefund):
  - Host in `KETTE_LLM_URL` nicht `127.0.0.1`/`localhost` → „Nur 127.0.0.1 erlaubt", **vor** jedem Request;
  - Router nicht erreichbar (Verbindungsfehler) → „Router nicht erreichbar";
  - Zeitüberschreitung (`KETTE_LLM_TIMEOUT`) → „Zeitüberschreitung nach <n> s";
  - HTTP-Fehler, z. B. 400 bei Kontext-Überlauf → „Router meldet HTTP <code>: <erste 200 Zeichen der Antwort>";
  - leere Antwort (`choices` leer, `content` leer/None) → „leere Modellantwort";
  - abgeschnittene Antwort (`finish_reason` = `length`) → „Antwort abgeschnitten (finish_reason=length)" – wird nicht als Verdikt gespeichert.
- **Stelle:** `role-split/kette/kette.py` `def review_auto`.
- **Akzeptanz:** je Fall im simulierten Server: Exit 1, die jeweilige Meldung, keine leere oder halbe Verdikt-Datei.

### A9: Echter Lauf am K7-Stand
- **Anforderung:** Nach grünen Tests startet **Hawe** einmal `python3 role-split/kette/kette.py review-auto mail_server_test` gegen den echten Router (Modell 35B-A3B). Ziel: Ende-zu-Ende-Nachweis (Router, Laufzeit, Herzschlag, Speichern, Zusammenführen) und Vergleich der Befunde mit dem K7-Schlüssel durch Claude.
- **Stelle:** kein Code; Ausgabe des Laufs und die erzeugten Dateien kommen in die Übergabe bzw. an Claude.
- **Akzeptanz:** Lauf endet mit Zusammenfassung; zwei Verdikte und `gesamt_*.md` existieren; vorhandene K7-Verdikte bleiben unverändert (Umbenennung `_2` greift, weil `verdict_20261023_mail_server_test_qwen36-35b.md` schon existiert).

## Fehlerpfade

Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | n. a. | Exit 1, Meldung „Router nicht erreichbar", kein Verdikt geschrieben | T2 |
| A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | n. a. | ungültiger Kurztitel → Exit 2 (wie `pruefen`) | T3 |
| A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | n. a. | Prompt-Text ist im Speicher, keine Datei | n. a. |
| A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | n. a. | kein Trockenlauf definiert; unverändert | n. a. |
| A1 | Lauf ohne Testschalter / gegen echte Daten | n. a. | im Test gegen simulierte Daten; im echten Lauf: nur 127.0.0.1 | n. a. |
| A1 | Absturz mitten im Lauf | n. a. | nichts geschrieben; Exit != 0 | T9 |
| A2 | Gegenstelle antwortet nicht oder schweigt | n. a. | n. a. (pruefen ist lokal) | n. a. |
| A2 | Eingabe leer oder ungültig | n. a. | ungültiger Kurztitel → Exit 2 | T3 |
| A2 | Ziel existiert schon | n. a. | `pruefung_*.md` wird überschrieben (bestehendes Verhalten) | T4 |
| A2 | Schalter kombiniert | n. a. | n. a. | n. a. |
| A2 | Lauf ohne Testschalter / gegen echte Daten | n. a. | pruefen läuft immer | T4 |
| A2 | Absturz mitten im Lauf | n. a. | pruefen bricht, Exit 1, kein Review | T4 |
| A2 | unittest grün, abgleich/gegenprobe mit Abweichung | `pruefung_*.md` | **kein** Abbruch, Review läuft | T4 |
| A2 | Werkzeugfehler der Prüfung (kein Spec-Commit) | n. a. | Exit 2, Meldung | T5 |
| A3 | Gegenstelle antwortet nicht oder schweigt | n. a. | n. a. (lokal) | n. a. |
| A3 | Eingabe leer oder ungültig | n. a. | keine Spec → Exit 2, Meldung | T5 |
| A3 | Ziel existiert schon | `review_paket_*.md` vom letzten Lauf | wird überschrieben (bestehendes Verhalten von `paket`) | T5 |
| A3 | Schalter kombiniert | n. a. | n. a. | n. a. |
| A3 | Lauf ohne Testschalter / gegen echte Daten | n. a. | n. a. | T5 |
| A3 | Absturz mitten im Lauf | Paket ggf. halbschriftlich | `paket` schreibt einmalig am Ende; Exit 2 | T5 |
| A4 | Gegenstelle antwortet nicht oder schweigt | Lauf 1-Vordikt ggf. gespeichert | Exit 1, Meldung „Router nicht erreichbar", Lauf 2-Vordikt nicht gespeichert | T2 |
| A4 | Eingabe leer oder ungültig | n. a. | leere Antwort → Exit 1, Meldung „leere Modellantwort" | T6 |
| A4 | Ziel existiert schon | Vordikt-Datei vom Lauf 1 | Lauf 2 wird automatisch umbenannt (A5) | T7 |
| A4 | Schalter kombiniert | n. a. | kein Schalter | n. a. |
| A4 | Lauf ohne Testschalter / gegen echte Daten | n. a. | im Test gegen simulierten Server | T6 |
| A4 | Absturz mitten im Lauf | Lauf 1-Vordikt gespeichert, Lauf 2 läuft | Exit 1, Meldung, Lauf 1-Vordikt bleibt erhalten, kein Gesamt | T9 |
| A5 | Gegenstelle antwortet nicht oder schweigt | n. a. | n. a. (speichern ist lokal) | n. a. |
| A5 | Eingabe leer oder ungültig | n. a. | leere Antwort → keine Speichern, Exit 1 (A8) | T6 |
| A5 | Ziel existiert schon | Vordikt-Datei existiert | automatisch umbenannt (`_lauf2`), alte Datei unverändert | T7 |
| A5 | Schalter kombiniert | n. a. | n. a. | n. a. |
| A5 | Lauf ohne Testschalter / gegen echte Daten | n. a. | n. a. | T7 |
| A5 | Absturz mitten im Lauf | n. a. | keine halbe Datei (Antwort erst nach vollständigem Empfang) | T9 |
| A6 | Gegenstelle antwortet nicht oder schweigt | n. a. | n. a. (Prüfung ist lokal) | n. a. |
| A6 | Eingabe leer oder ungültig | n. a. | Verdikt ohne Befund-Tabelle → Exit 1, Meldung, Gesamt mit „UNVOLLSTÄNDIG" + Warnung | T8 |
| A6 | beide Verdikte ohne Tabelle | beide Verdikte | kein Gesamt, Exit 1 | T8 |
| A6 | Ziel existiert schon | n. a. | n. a. | n. a. |
| A6 | Schalter kombiniert | n. a. | n. a. | n. a. |
| A6 | Lauf ohne Testschalter / gegen echte Daten | n. a. | n. a. | T8 |
| A6 | Absturz mitten im Lauf | n. a. | n. a. | T8 |
| A7 | Gegenstelle antwortet nicht oder schweigt | n. a. | n. a. (zusammenführen ist lokal) | n. a. |
| A7 | Eingabe leer oder ungültig | n. a. | n. a. | n. a. |
| A7 | Ziel existiert schon | `gesamt_*.md` vom letzten Lauf | wird überschrieben (bestehendes Verhalten) | T10 |
| A7 | Schalter kombiniert | n. a. | n. a. | n. a. |
| A7 | Lauf ohne Testschalter / gegen echte Daten | n. a. | n. a. | T10 |
| A7 | Absturz mitten im Lauf | n. a. | n. a. | T10 |
| A8 | Gegenstelle antwortet nicht oder schweigt | n. a. | Exit 1, Meldung, keine halben Dateien | T2 |
| A8 | Eingabe leer oder ungültig | n. a. | leere Antwort → Exit 1 | T6 |
| A8 | Ziel existiert schon | n. a. | n. a. | n. a. |
| A8 | Schalter kombiniert | n. a. | n. a. | n. a. |
| A8 | Lauf ohne Testschalter / gegen echte Daten | n. a. | fremder Host in `KETTE_LLM_URL` → Exit 1 vor jedem Request | T11 |
| A8 | Antwort abgeschnitten (`finish_reason=length`) / HTTP 400 | n. a. | Exit 1, eigene Meldung, kein Verdikt | T12 |
| A4 | Lauf dauert lange, keine Ausgabe | n. a. | Herzschlag-Zeile je Intervall | T13 |
| A9 | echter Router, echtes Modell | K7-Verdikte vorhanden | Umbenennung `_2`, K7-Dateien unverändert, Zusammenfassung | T14 |
| A8 | Absturz mitten im Lauf | n. a. | Exit 1, keine halben Dateien | T9 |

## Testplan

Alle Tests werden als `tests/test_kette_review_auto.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung. Die Tests importieren `kette` wie `test_kette.py` (Zeilen 10–11) und ersetzen `kette.PM` durch ein `tempfile.TemporaryDirectory` sowie `KETTE_LLM_URL` durch einen simulierten HTTP-Server auf `127.0.0.1`. `KETTE_LLM_TIMEOUT` und `KETTE_HERZSCHLAG_S` werden auf wenige Sekunden gesetzt, damit kein Test lange wartet.

### T1: Endergebnis bei zwei gültigen Läufen
- **Prüft:** A1, A2, A3, A4, A5, A6, A7
- **Aufbau:** Simulierter Server liefert für beide Läufe ein gültiges Verdikt (alle Pflicht-Spalten, mindestens ein Befund); `pruefen` wird monkey-patcht auf Exit 0; Test-Verzeichnis für `PM`.
- **Erwartung:** Exit-Code 0 (oder 1 bei NACHBESSERN, je nach Inhalt); Stdout enthält „Ergebnis", „hohe Befunde", zwei Verdikt-Pfade und den Gesamt-Pfad; genau 2 HTTP-Requests; `gesamt_*.md` existiert.
- **Warum misst der Test das Richtige?** Scheitert, wenn einer der Schritte fehlt (z. B. kein Zusammenführen, kein Umbenennen, keine Fortschrittsmeldung).
- **Gegenprobe:** Im alten Code gibt es `review_auto` nicht – der Test scheitert sofort mit `AttributeError`; alle anderen Prüfungen (Request-Format, Datei-Namen) scheitern erst, wenn die Umsetzung die Schritte in der falschen Reihenfolge oder ohne Umbenennung macht.

### T2: Router nicht erreichbar
- **Prüft:** A4, A8, Fehlerpfad „Gegenstelle antwortet nicht"
- **Aufbau:** Simulierter Server wird nicht gestartet (Port nicht erreichbar); `pruefen` auf Exit 0 gepatcht.
- **Erwartung:** Exit-Code 1; Meldung enthält „Router nicht erreichbar" (oder „verbin"); keine Verdikt-Dateien im Test-Verzeichnis.
- **Warum misst der Test das Richtige?** Scheitert, wenn der Code den Connection-Error verschluckt oder weitermacht.
- **Gegenprobe:** Ohne `try/except` um den `requests.post` oder mit falscher Fehlerbehandlung bricht der Code mit unbeherrschtem Exception ab (Traceback statt klarer Meldung) – der Test prüft die klare Meldung und den Exit-Code.

### T3: Ungültiger Kurztitel
- **Prüft:** A2, Fehlerpfad „Eingabe leer oder ungültig"
- **Aufbau:** `pruefen`/`_pruefen_teile` werden gepatcht, sodass sie **nichts** prüfen und „grün" melden; dann `kette.review_auto("Ungültig-Titel")`.
- **Erwartung:** Exit-Code 2; Meldung „ungültig"; kein HTTP-Request, keine Dateien.
- **Warum misst der Test das Richtige?** Weil die Prüfung gepatcht ist, kann nur `review_auto` selbst den Titel abweisen.
- **Gegenprobe:** Ohne eigene Prüfung in `review_auto` läuft der Befehl weiter und sendet Requests → rot.

### T4: Nur rote Unit-Tests brechen ab
- **Prüft:** A2
- **Aufbau:** Zwei Fälle mit gepatchten Teil-Ergebnissen. (a) `unittest` rot, abgleich ok → Abbruch erwartet. (b) `unittest` grün, `abgleich` und `gegenprobe` mit Abweichung (Exit 1) → **kein** Abbruch, simulierter Server liefert gültige Verdikte.
- **Erwartung:** (a) Exit 1, Meldung „Unit-Tests rot – direkt nachbessern, kein Review nötig", kein Paket, keine Requests. (b) 2 Requests, `gesamt_*.md` existiert.
- **Warum misst der Test das Richtige?** Fall (b) ist der Normalfall aus K7; bricht der Code dort ab, ist der Befehl nutzlos.
- **Gegenprobe:** Abbruch an `pruefen() != 0` statt am Teil `unittest` → Fall (b) rot.

### T5: Paket-Voraussetzung fehlt
- **Prüft:** A3
- **Aufbau:** `paket` wird monkey-patcht auf Rückgabe 2; `pruefen` auf Exit 0.
- **Erwartung:** Exit-Code 2; Meldung enthält „Paket" (oder die Meldung von `paket`); keine HTTP-Requests.
- **Warum misst der Test das Richtige?** Scheitert, wenn der Code die `paket`-Rückgabe ignoriert.
- **Gegenprobe:** Ohne Rückgabewert-Prüfung würde der Code mit leerem/nicht vorhandenem Paket-Text weitermachen und 2 Requests senden – der Test misst die Request-Anzahl.

### T6: Leere Modellantwort
- **Prüft:** A4, A8, Fehlerpfad „Eingabe leer oder ungültig"
- **Aufbau:** Simulierter Server liefert `{"choices": []}` bzw. `choices[0].message.content = ""`.
- **Erwartung:** Exit-Code 1; Meldung enthält „leere" (oder „keine Antwort"); keine halbe Verdikt-Datei mit leerem Inhalt (Dateien, die existieren, sind gültig oder gar nicht geschrieben).
- **Warum misst der Test das Richtige?** Scheitert, wenn der Code leere `content`-Strings als gültiges Verdikt speichert.
- **Gegenprobe:** Ohne Prüfung auf `choices`/`content` würde eine leere Datei `verdict_…_qwen36-35b.md` mit leerem Inhalt entstehen – der Test prüft, dass die Datei fehlt oder gültig ist.

### T7: Automatisches Umbenennen
- **Prüft:** A5, Fehlerpfad „Ziel existiert schon"
- **Aufbau:** Vorab wird `verdict_<datum>_<kurztitel>_qwen36-35b.md` mit bekanntem Inhalt angelegt; simulierte Server liefert gültige Verdikte.
- **Erwartung:** Exit-Code 0/1 (je nach Inhalt); die neue Datei trägt den Namen `…_qwen36-35b_2.md` (liegt auch `_2` schon da: `_3`); die vorherige Datei ist bitweise unverändert (Hash-Vergleich); beide Läufe erhalten ihren eigenen Namen.
- **Warum misst der Test das Richtige?** Scheitert, wenn der Code überschreibt (alte Datei geändert) oder abbricht statt umzubenennen.
- **Gegenprobe:** Ohne Umbenennungslogik überschreibt `write_text` die vorhandene Datei – der Hash-Vergleich schlägt fehl.

### T8: Fehlende Befund-Tabelle
- **Prüft:** A6
- **Aufbau:** Simulierter Server liefert für Lauf 1 ein gültiges Verdikt, für Lauf 2 ein Verdikt ohne „Befunde"-Abschnitt (oder mit Tabelle ohne die Pflicht-Spalten).
- **Erwartung:** Exit-Code 1; Meldung enthält „Befund-Tabelle" (oder „nicht auswertbar"); `gesamt_*.md` existiert, Ergebnis **„UNVOLLSTÄNDIG"** (Lauf 1 liefert bewusst PASS – „PASS" darf nicht als Ergebnis erscheinen), Warnhinweis vorhanden, Befunde aus Lauf 1 enthalten. Zweiter Fall: beide ohne Tabelle → kein `gesamt_*.md`, Exit 1.
- **Warum misst der Test das Richtige?** Scheitert, wenn der Code komplett abbricht (kein Gesamt) oder die fehlende Tabelle nicht erkennt.
- **Gegenprobe:** Ohne die Spalten-Prüfung (nur `tabelle()`-Aufruf) würde ein beliebiger Text als Tabelle durchgehen – der Test liefert bewusst eine Tabelle ohne die Pflicht-Spalten.

### T9: Abbruch bei Lauf 2 (Lauf 1 bleibt erhalten)
- **Prüft:** A8, Fehlerpfad „Absturz mitten im Lauf"
- **Aufbau:** Simulierter Server liefert für Lauf 1 ein gültiges Verdikt, für Lauf 2 keine Antwort innerhalb von `KETTE_LLM_TIMEOUT` (im Test 2 s; Server wartet länger).
- **Erwartung:** Exit-Code 1; klare Meldung; die Lauf-1-Verdikt-Datei existiert mit vollständigem Inhalt; kein `gesamt_*.md`; keine halbe Lauf-2-Datei.
- **Warum misst der Test das Richtige?** Scheitert, wenn der Code Lauf 1 löscht oder eine halbe Datei schreibt.
- **Gegenprobe:** Ohne „Antwort erst nach vollständigem Empfang" (d. h. wenn der Code streamen würde) gäbe es eine halbe Datei – der Test misst die Datei-Inhalte.

### T10: Zusammenfassung und Gesamt-Datei
- **Prüft:** A7
- **Aufbau:** Wie T1, aber Fokus auf die Ausgabeseite.
- **Erwartung:** Stdout enthält exakt: Ergebnis (PASS/NACHBESSERN/FAIL), Anzahl hoher Befunde (Zahl), Pfad Lauf 1, Pfad Lauf 2, Pfad Gesamt; `gesamt_*.md` existiert.
- **Warum misst der Test das Richtige?** Scheitert, wenn eine der drei Angaben fehlt.
- **Gegenprobe:** Ohne die Zusammenfassungszeile am Ende fehlt sie in der Stdout – der Test misst sie per `assertIn`.

### T11: Nur 127.0.0.1
- **Prüft:** A8, Sperre (3)
- **Aufbau:** `KETTE_LLM_URL=http://192.0.2.1:8080` (Dokumentations-Adresse, nie erreichbar) und `http://example.com:8080`; Prüfung gepatcht auf grün.
- **Erwartung:** Exit 1, Meldung „Nur 127.0.0.1 erlaubt"; kein Verbindungsversuch (Request-Funktion gepatcht und nicht aufgerufen).
- **Warum misst der Test das Richtige?** Die Anforderung „nur 127.0.0.1" ist sonst nur verlangt.
- **Gegenprobe:** Ohne Host-Prüfung wird die Request-Funktion aufgerufen → rot.

### T12: Abgeschnittene Antwort und HTTP-Fehler
- **Prüft:** A8
- **Aufbau:** Simulierter Server liefert (a) `finish_reason: "length"` mit Text, (b) HTTP 400 mit Fehlertext.
- **Erwartung:** je Exit 1 mit eigener Meldung („abgeschnitten" bzw. „HTTP 400"); kein Verdikt gespeichert.
- **Warum misst der Test das Richtige?** Ein abgeschnittenes Verdikt sähe sonst wie ein gültiges aus; ein Kontext-Überlauf würde als „nicht erreichbar" fehlgedeutet.
- **Gegenprobe:** Ohne Auswertung von `finish_reason` wird (a) gespeichert → rot.

### T13: Herzschlag während des Laufs
- **Prüft:** A4 (Fortschritt live)
- **Aufbau:** `KETTE_HERZSCHLAG_S=1`; simulierter Server antwortet nach 3 s.
- **Erwartung:** Ausgabe enthält mindestens zwei Herzschlag-Zeilen für Lauf 1 vor der Fertig-Meldung.
- **Warum misst der Test das Richtige?** 20 Minuten ohne Ausgabe sehen aus wie ein Hänger (K7).
- **Gegenprobe:** Ohne Herzschlag nur Start- und Endzeile → rot.

### T14: Echter Lauf am K7-Stand (Hawe, manuell)
- **Prüft:** A9
- **Aufbau:** Lab mit Router, Modell 35B-A3B ladbar; `python3 role-split/kette/kette.py review-auto mail_server_test 2>&1 | tee /tmp/k8_review_auto.log`.
- **Erwartung:** Zusammenfassung am Ende; zwei neue Verdikte mit Zähler `_2`; `gesamt_*.md`; vorhandene K7-Verdikte bitgleich.
- **Warum misst der Test das Richtige?** Nur der echte Router zeigt Modellwechsel, Laufzeit, echtes Antwortformat und echte Tabellenform (R14).
- **Gegenprobe:** n. a. (manuell); Claude vergleicht die Befunde mit dem K7-Schlüssel.

## Offene Fragen

- Geklärt 25.10. (Gegenprüfung, Hawe einverstanden): Teil-Gesamtbefund heißt „UNVOLLSTÄNDIG", Exit 1 (A6). Modellname über `KETTE_LLM_MODEL`, Default voller Router-Name (A4). Timeout 1800 s über `KETTE_LLM_TIMEOUT` (A4). Kürzel `qwen36-35b` wie in K7 (A5). Umbenennung mit `_2`, `_3` (A5).
- Offen für die Umsetzung: `requests` oder stdlib (`urllib.request`) – `kette.py` nutzt bisher nur die stdlib; stdlib bevorzugt, damit `kette.py` ohne venv läuft.

## Abweichende Meinung

- Keinerlei Abweichung: Die Diskussion (Umbenennen statt abbrechen; Gesamt mit Warnung statt hartem Abbruch) ist zwischen uns entschieden und in A5/A6 eingearbeitet. Mein ursprünglicher Vorschlag „abbrechen mit Exit 1 bei fehlender Tabelle" (Variante a) wurde durch deine Antwort (b) ersetzt – die Spec trägt (b) mit dem Exit-Code, wie oben unter „Offene Fragen" als letzte Klärung ausstehend markiert.
- **Nachtrag 25.10. (Claude, Gegenprüfung vor Commit, mit Hawes Zustimmung eingearbeitet):** A2 brach bei jeder Abgleich-/Gegenprobe-Abweichung ab (Anforderung: nur rote Unit-Tests); der verlangte echte Lauf fehlte (jetzt A9/T14); Teil-Gesamtbefund konnte PASS zeigen; „nur 127.0.0.1" war nicht erzwungen; Modellname für den Router unvollständig; Fortschritt während des Laufs fehlte; Timeout nicht testbar; abgeschnittene Antwort / HTTP 400 nicht unterschieden; `_lauf2` verwechselbar mit Lauf 2.
