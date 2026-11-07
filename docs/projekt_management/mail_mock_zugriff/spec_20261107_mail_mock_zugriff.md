# Spec: mail_mock_zugriff

- **Datum:** 2026-11-07
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Betroffene Dateien:** `agents/mail_planung/mail_planung.py`, `tests/mail_server_test/start_test_mailserver.sh`, `tests/mail_server_test/einliefern.py`, `tests/test_mail_server_test.py`, `agents/mail_planung/test_imap_server.py`, `.gitignore`
- **Änderungsstellen:** 6

## Ziel

Der Mail-Client liest IMAP-Passwörter ausschließlich aus dem macOS-Keychain. Auf expliziten Wunsch (Umgebungsvariable) kann zusätzlich eine lokale, nicht versionierte Datei als zweite Quelle dienen; der Default bleibt Keychain. Der Testpfad (Mock auf 127.0.0.1) bleibt vollständig ohne echte Credentials; ein Test verriegelt, dass kein Codepfad Credentials in Git-gepflegte Artefakte schreibt.

## Nicht-Ziele

- Keine echte Mail im Lauf senden (kein SMTP-Versand, kein `server.sendmail`).
- Keine echten Postfächer in CI/Tests anbinden (Tests nutzen GreenMail auf 127.0.0.1 + Mock-Patch).
- Kein Passwort im Auftrag, in dieser Spec, im Protokoll oder im Commit.
- Kein IMAP-Schreiben: `select(readonly=True)` bleibt; kein `IMAP4.logout()` mit `expunge`, kein `STORAGE`, kein `EXPUNGE`.
- Kein LLM-Aufruf im Testpfad (LLM wird in Tests per `MagicMock` ersetzt, wie bereits in `tests/test_mail_server_test.py`).
- Keine `IMAP_USER`-Änderung: User bleibt per `os.getenv("IMAP_USER")` konfiguriert; nur das *Passwort* wird hier beschränkt.

## Schreibbereich

- `agents/mail_planung/mail_planung.py`
- `tests/mail_server_test/`
- `tests/test_mail_server_test.py`
- `agents/mail_planung/test_imap_server.py`
- `.gitignore`

## Vorgabe-Tests

- `tests/test_mail_server_test.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?**
  - Echter manueller Aufruf: IMAP-Lesezugriff auf das konfigurierte Postfach (IMAP4_SSL, Port 993; unverschlüsselt nur auf 127.0.0.1).
  - Test-Aufruf: GreenMail-Docker-Container auf 127.0.0.1, Test-Keychain-Eintrag (`lab-mail-imap-test`), Test-`.eml`-Dateien aus `tests/mail_server_test/mails/`.
  - Die Umsetzung selbst sendet **keine** Mails und schreibt **keine** echten Daten.

- **Technische Sperre für Tests:**
  1. `MAIL_IMAP_UNENCRYPTED=1` ist in `start_test_mailserver.sh` gesetzt; der Client (`mail_planung.py` `Zeilen 187–190`) erlaubt unverschlüsseltes IMAP **nur** wenn `host in ("127.0.0.1", "localhost")`, sonst `sys.exit(1)`.
  2. Alle Tests in `tests/test_mail_server_test.py` patchen `fetch_mails` und `get_imap_password` per `unittest.mock.patch.object`. Kein Test ruft `imaplib.IMAP4*` ohne Mock.
  3. **Neu (T18):** Ein Test prüft, dass `get_imap_password()` bei leerem Keychain `RuntimeError` wirft und dass `main()`/`run_dry()` bei leerem Keychain **vor** dem IMAP-Call `RuntimeError` abfangen und Exit-Code 1 liefern, **ohne** dass `fetch_mails` aufgerufen wird. Das verriegelt den Pfad „Credentials fehlen → kein IMAP-Call → kein Passwort in Logs".
  4. **Neu (T19):** Ein Test prüft, dass `get_imap_password()` ohne `MAIL_IMAP_CRED_SOURCE=file` **keine** Datei öffnet (per `unittest.mock.patch` auf `open`/`pathlib.Path.read_text` → `assert_not_called`).
  5. `start_test_mailserver.sh` räumt per `trap cleanup EXIT` den Keychain-Eintrag und den Docker-Container auf, auch bei Fehler-Exit.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `agents/mail_planung/mail_planung.py` | `python3 agents/mail_planung/mail_planung.py [--dry-run]` (manuell oder `start_test_mailserver.sh` Schritt 6/7/9) | T1–T7, T18, T19 |
| `tests/mail_server_test/start_test_mailserver.sh` | `bash tests/mail_server_test/start_test_mailserver.sh` (manuell, Docker) | T1, T2, T3 (Skript-Inhaltsprüfung) |
| `tests/mail_server_test/einliefern.py` | `python3 tests/mail_server_test/einliefern.py --smtp-host 127.0.0.1 --smtp-port 3025 --rcpt testuser@lab.local` (ongerufen von `start_test_mailserver.sh` Schritt 5) | T3 |

## Quellen

- `agents/mail_planung/mail_planung.py` `def get_imap_password` (Zeilen 76–95) – aktuelles Keychain-Loading; hier wird `MAIL_IMAP_CRED_SOURCE`-Branch ergänzt.
- `agents/mail_planung/mail_planung.py` `Zeilen 54–59` – `IMAP_HOST`, `IMAP_PORT`, `IMAP_USER`, `KEYCHAIN_SERVICE`, `MAIL_IMAP_UNENCRYPTED`; hier wird `MAIL_IMAP_CRED_SOURCE` und `MAIL_IMAP_CRED_FILE` ergänzt.
- `agents/mail_planung/mail_planung.py` `def fetch_mails` (Zeilen 180–205) – IMAP-Login; zeigt, dass Passwort nur als Argument durchgereicht wird, kein Logging.
- `agents/mail_planung/mail_planung.py` `def main` (Zeilen 784–826) und `def run_dry` (Zeilen 748–777) – beide rufen `get_imap_password()` als ersten Schritt; hier wird `RuntimeError`-Handling ergänzt.
- `tests/mail_server_test/start_test_mailserver.sh` `Zeilen 22–33` – Keychain-Setup für Test; zeigt Muster für Test-Credentials.
- `tests/mail_server_test/einliefern.py` `def main` – CLI-Argumente für SMTP-Einlieferung; Referenz für `--password`-Argument (bleibt unbenutzt, nur dokumentiert).
- `tests/test_mail_server_test.py` `class TestT4KeychainService` (Zeilen 50–67) – Muster für Keychain-Tests; hier werden T18/T19 ergänzt.
- `.gitignore` `Zeilen 1–41` – aktueller Stand; hier wird `.env` und `*.credentials` ergänzt.
- `agents/mail_planung/test_imap_server.py` (ganze Datei, 38 Zeilen) – Fundstelle/Platzhalter; wird um kurze Beschreibung der Test-Mock-Strategie ergänzt.

## Anforderungen

### A1: Default-Modus = nur Keychain
- **Anforderung:** Ohne `MAIL_IMAP_CRED_SOURCE` (oder mit Wert ≠ `file`) ruft `get_imap_password()` ausschließlich `security find-generic-password` auf. Kein Datei-Zugriff.
- **Stelle:** `agents/mail_planung/mail_planung.py`, `def get_imap_password`
- **Akzeptanz:** T19 zeigt, dass `open`/`Path.read_text` nicht aufgerufen wird, wenn `MAIL_IMAP_CRED_SOURCE` nicht `file` ist.

### A2: Optionales Datei-Modus via `MAIL_IMAP_CRED_SOURCE=file`
- **Anforderung:** Wenn `MAIL_IMAP_CRED_SOURCE=file` gesetzt ist, liest `get_imap_password()` das Passwort aus der Datei, deren Pfad in `MAIL_IMAP_CRED_FILE` steht. Die Datei wird nicht in Git committet (`.gitignore` enthält den Pfad oder ein Pattern).
- **Stelle:** `agents/mail_planung/mail_planung.py`, `def get_imap_password` (neuer Branch)
- **Akzeptanz:** T20 zeigt, dass bei `MAIL_IMAP_CRED_SOURCE=file` + `MAIL_IMAP_CRED_FILE=<tmp>` der Dateiinhalt als Passwort zurückgegeben wird.

### A3: `.gitignore` schützt lokale Credential-Dateien
- **Anforderung:** `.gitignore` enthält `.env` und ein Pattern für lokale Credential-Dateien (z. B. `*.credentials` oder `mail_imap_cred*`).
- **Stelle:** `.gitignore`
- **Akzeptanz:** T21 prüft per String-Abgleich, dass `.gitignore` die relevanten Pfade enthält.

### A4: Fehlerpfad „Keychain leer" → Exit-Code 1, kein IMAP-Call
- **Anforderung:** Wenn `get_imap_password()` `RuntimeError` wirft (Keychain-Eintrag fehlt oder ist leer), geben `main()` und `run_dry()` Exit-Code 1 zurück **vor** dem Aufruf von `fetch_mails`.
- **Stelle:** `agents/mail_planung/mail_planung.py`, `def main` (Zeilen 795–800) und `def run_dry` (Zeile 754)
- **Akzeptanz:** T18 zeigt, dass `fetch_mails` nicht aufgerufen wird, wenn `get_imap_password` `RuntimeError` wirft.

### A5: Testpfad bleibt ohne echte Credentials
- **Anforderung:** Kein Test in `tests/test_mail_server_test.py` liest ein echtes IMAP-Passwort. Alle Tests patchen `get_imap_password` oder `fetch_mails`.
- **Stelle:** `tests/test_mail_server_test.py`
- **Akzeptanz:** Bestehende Tests T1–T17 (Bestand) + neue T18–T21. T19 verriegelt, dass ohne `file`-Schalter keine Datei geöffnet wird.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Gegenstelle antwortet nicht (Keychain-`security`-Befehl schweigt/Timeout) | Nichts | `RuntimeError`, Exit-Code 1, `fetch_mails` nicht aufgerufen | T18 |
| A1 | Eingabe ungültig (Keychain-Eintrag leer) | Nichts | `RuntimeError` („Schlüsselbund-Eintrag ist leer"), Exit-Code 1 | T18 |
| A1 | Ziel existiert schon (Keychain-Eintrag vorhanden) | Nichts (nur lesen) | Passwort wird gelesen, IMAP-Call erfolgt | Bestehende Tests (Bestand) |
| A1 | Schalter kombiniert (`MAIL_IMAP_CRED_SOURCE` leer + `MAIL_IMAP_UNENCRYPTED=1`) | Nichts | Normaler Keychain-Pfad; unverschlüsseltes IMAP nur localhost | T5 (Bestand) |
| A1 | Lauf ohne Testschalter / gegen echte Daten (manueller Aufruf) | Nichts | Keychain-Pfad, IMAP4_SSL, Exit-Code 0 bei Erfolg | Manuell (Hawe) |
| A1 | Absturz mitten im Lauf (LLM-Crash nach IMAP) | DB-Init erfolgt, keine Mail verarbeitet | Exit-Code 1, Planungsdatei unverändert | T7 (Bestand) |
| A2 | Gegenstelle antwortet nicht (Datei nicht lesbar / Pfad leer) | Nichts | `RuntimeError`, Exit-Code 1, `fetch_mails` nicht aufgerufen | T18 (adaptiert) |
| A2 | Eingabe ungültig (`MAIL_IMAP_CRED_FILE` nicht gesetzt) | Nichts | `RuntimeError` („MAIL_IMAP_CRED_FILE nicht gesetzt"), Exit-Code 1 | T18 (adaptiert) |
| A2 | Ziel existiert schon (Datei vorhanden, Passwort leer) | Nichts | `RuntimeError` („Passwort-Datei ist leer"), Exit-Code 1 | T18 (adaptiert) |
| A2 | Schalter kombiniert (`MAIL_IMAP_CRED_SOURCE=file` + `MAIL_IMAP_UNENCRYPTED=1`) | Nichts | Datei-Pfad; unverschlüsseltes IMAP nur localhost | T20 |
| A2 | Lauf ohne Testschalter / gegen echte Daten | Datei wird gelesen, nicht verändert | IMAP-Call mit Datei-Passwort, Exit-Code 0 bei Erfolg | Manuell (Hawe) |
| A2 | Absturz mitten im Lauf | Nichts (Datei nur gelesen) | Exit-Code 1, Datei unverändert | T20 (adaptiert) |
| A3 | `.gitignore`-Pattern fehlt | Nichts | Credential-Datei landet im Commit | T21 |
| A4 | Keychain leer | Nichts | Exit-Code 1, `fetch_mails` nicht aufgerufen | T18 |
| A5 | Test ohne Mock (falsche Test-Implementierung) | Nichts | Test würde echtes Passwort lesen → T19 rot | T19 |

## Testplan

Alle Tests in `tests/test_mail_server_test.py` (unittest). Keine Außenwirkung.

### T18: Keychain leer → Exit-Code 1, kein IMAP-Call
- **Prüft:** A4, A1-Fehlerpfad
- **Aufbau:** `patch.object(mod, "get_imap_password", side_effect=RuntimeError("..."))`, `patch.object(mod, "fetch_mails")`; `MAIL_PLAN_DIR` = temporäres Verzeichnis.
- **Erwartung:** `mod.main()` liefert 1; `fetch_mails.assert_not_called()`.
- **Warum misst der Test das Richtige?** Wenn `main()` den `RuntimeError` nicht fängt oder `fetch_mails` trotzdem aufruft, wird der Test rot.
- **Gegenprobe:** In `main()` fehlt der `try/except RuntimeError`-Block → `fetch_mails` wird aufgerufen → Test rot.

### T19: Ohne `MAIL_IMAP_CRED_SOURCE=file` wird keine Datei geöffnet
- **Prüft:** A1, A5
- **Aufbau:** `patch.dict(os.environ, {}, clear=True)`; `patch("pathlib.Path.read_text")` und `patch("builtins.open")` → `assert_not_called`.
- **Erwartung:** `get_imap_password()` wirft `RuntimeError` (Keychain nicht gefunden im Test); `open`/`read_text` nicht aufgerufen.
- **Warum misst der Test das Richtige?** Wenn ein Codepfad ohne `file`-Schalter eine Datei öffnet, wird der Test rot.
- **Gegenprobe:** In `get_imap_password` fehlt der `if MAIL_IMAP_CRED_SOURCE == "file"`-Guard → `open` wird aufgerufen → Test rot.

### T20: `MAIL_IMAP_CRED_SOURCE=file` liest Passwort aus Datei
- **Prüft:** A2
- **Aufbau:** Temporäre Datei mit Inhalt `"testpass123"`; `MAIL_IMAP_CRED_SOURCE=file`, `MAIL_IMAP_CRED_FILE=<tmp>`.
- **Erwartung:** `get_imap_password()` liefert `"testpass123"`.
- **Warum misst der Test das Richtige?** Wenn der Datei-Branch fehlt, wird `RuntimeError` geworfen → Test rot.
- **Gegenprobe:** In `get_imap_password` fehlt der `if MAIL_IMAP_CRED_SOURCE == "file"`-Branch → `RuntimeError` → Test rot.

### T21: `.gitignore` enthält Credential-Patterns
- **Prüft:** A3
- **Aufbau:** `Path(".gitignore").read_text()`; String-Abgleich.
- **Erwartung:** `.env` und `*.credentials` (oder `mail_imap_cred*`) sind enthalten.
- **Warum misst der Test das Richtige?** Wenn das Pattern fehlt, kann eine Credential-Datei committet werden → Test rot.
- **Gegenprobe:** `.gitignore` ohne `.env` → Test rot.

### T1–T17 (Bestand)
- **Prüft:** Bestehendes Verhalten (Keychain-Default, Unverschlüsseltes IMAP nur localhost, Dry-Run, Real-Run, GreenMail-Setup).
- **Erwartung:** Vor der Umsetzung grün, nach der Umsetzung weiter grün.
- **Gegenprobe:** keine – Tests prüfen Bestehendes.

## Offene Fragen

- **Bestätigte Entscheidung (b):** Lade-Reihenfolge = Keychain exklusiv im Default; Datei nur über `MAIL_IMAP_CRED_SOURCE=file`. Begründung: Default bleibt die schärfere Sicherheitseigenschaft; ein Test (T19) verriegelt, dass ohne Schalter keine Datei gelesen wird. Hawe hat (b) empfohlen.
- **Lese-Only:** Bleibt wie bereits (`select("INBOX", readonly=True)`). Kein SMTP-Versand. Bestätigt, keine offene Frage.
- **Nur INBOX:** Bleibt wie bereits (`select("INBOX")`). Bestätigt, keine offene Frage.
- **Restrisiko bei `MAIL_IMAP_CRED_SOURCE=file`:** Wenn Hawe versehentlich eine Credential-Datei committet, die `MAIL_IMAP_CRED_FILE`-Pfad im Repo liegt, ist das Passwort im Git. T21 prüft nur `.gitignore`-Patterns, nicht ob eine Datei tatsächlich committet wurde. Empfehlung: `MAIL_IMAP_CRED_FILE`-Pfad immer außerhalb des Repo legen (z. B. `~/.config/lab/mail_imap_cred.txt`).

## Abweichende Meinung

- Keine. Die Aufgabe ist weitgehend erfüllt; die Spec ergänzt die fehlenden Lücken (Datei-Modus, `.gitignore`, T18–T21).
