# Anforderung: mail_mock_zugriff

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Der Mail-Demo-/Mock muss so ausgebaut werden, dass er optional ein echtes IMAP-Postfach ausliest, ohne dass das Passwort je in Git, Logs, Paketen, Tests oder dem Review-Protokoll landet. Ziel: Lokale Mailfunktion bleibt testbar, echte Zugangsdaten bleiben nur lokal.
> Erster Schritt (diese Kette): IMAP-Zugriff konfigurierbar machen, aber Credentials ausschließlich aus macOS-Keychain oder einer lokalen nicht versionierten Datei laden; Testpfad bleibt vollständig mit Mock/127.0.0.1.
> Nicht-Ziele: Keine echte Mail im Lauf senden, keine echten Postfächer in CI/Tests anbinden, kein Passwort im Auftrag, Spec, Protokoll oder Commit.
> Außenwirkung: Beim echten manuellen Aufruf: IMAP-Lesezugriff auf das konfigurierte Postfach; technisch müssen Tests mit Mock und totem Port/127.0.0.1 laufen und das echte Passwort dürfen nicht lesen.
> Erkennbar fertig, wenn: Ein lokal getesteter Aufruf zeigt die ersten Betreffzeilen aus dem konfigurierten Postfach, während `git grep` kein Passwort enthält und alle Tests ohne echte Credentials laufen.
> Offene Entscheidungen: Keychain vs. lokale `.env`; Lese-Only oder auch Senden erlaubt; ob nur Inbox oder weitere Ordner.
> Lies keine großen Dateien ganz. Erst search_files (liefert Zeilennummern), dann read_file mit start_line/end_line.

## Antworten auf Rueckfragen

**2026-11-07 10:22** — Frage: **Lade-Reihenfolge der Credentials für den echten (manuellen) Aufruf:** Soll der Client (a) **Keychain zuerst, und nur wenn der Keychain-Eintrag fehlt, die lokale Datei** nachfragen, oder (b) **Keychain exklusiv** belassen und die lokale Datei nur als *alternative* Quelle über einen expliziten Schal

> Wichtig noch für dich zur grundsätzlichen Arbeitsweise:
> Lies keine großen Dateien ganz. Erst search_files (liefert Zeilennummern), dann read_file mit start_line/end_line. Sag vorher, was du lesen willst und warum.
>
> Ich tendiere auch zu b aber entscheidet Claude letztendlich


## Status (Claude, 07.11.2026)

**Nicht umgesetzt – Pilot-Protokoll.** Erster Durchlauf „Idee bis Commit“ aus der Chat-UI (`@idee` → `@review Neue Aufgabe`). Gegenlesen Claude:
- Gegenstand verrutscht: Der Demo-Mock (`tests/mail_server_test/`, GreenMail) ist der Testserver und soll nie an das echte Postfach. Das echte Postfach liest `agents/mail_planung/mail_planung.py` – Schlüsselbund, read-only und nur INBOX gibt es dort schon (das hat `@review` selbst festgestellt).
- Die vorgeschlagene zweite Passwort-Quelle (Datei über `MAIL_IMAP_CRED_SOURCE=file`) wird nicht gebaut: Sie erzeugt die Klartext-Passwortdatei, vor der sie schützen soll. Schlüsselbund bleibt einzige Quelle (Entscheidung Claude, von Hawe überlassen).
- Die eigentliche Lücke für „erste Betreffzeilen aus dem Postfach“ – `fetch_mails` lädt das ganze Postfach, der Trockenlauf schickt jede Mail ans Modell – fand keiner der beiden Schritte. Sie wird mit `mail_zeitfenster` geschlossen (dort auch der Treffer A4: `run_dry` fängt den fehlenden Schlüsselbund-Eintrag).
- Die Spec `spec_20261107_mail_mock_zugriff.md` schrieb das lokale Modell, weil der `@review`-Auftrag (`role-split/kette/prompts/spec.md`) das verlangt – entgegen R64. Folgekette vorgemerkt: `@review` stoppt nach Anforderung und Rückfragen.
