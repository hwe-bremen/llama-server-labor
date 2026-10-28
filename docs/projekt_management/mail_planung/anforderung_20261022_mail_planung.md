# Anforderung: mail_planung

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Du bist beauftragt einen Mail-server zu erstellen. Er soll hier im Projekt später ein Modul einer weitergehenden Projektplanungsinstanz werden. Was soll rauskommen? Zum Beispiel Aufgaben, Termine, Entscheidungen, offene Fragen pro Projekt, in eine Markdown-Planungsdatei.
> Wie oft und wie gestartet? Von Hand oder per launchd.
>
> Testumgebung: ein lokaler Test-Mailserver mit erfundenen Mails, auch schwierigen (nur HTML, Anhang, leerer Text, Umlaute, Weiterleitungskette, doppelt zugestellt).
> Postfach wird nie verändert: nur lesen, kein Gelesen-Markieren, kein Löschen. Was verarbeitet ist, merkt sich das Werkzeug selbst.
> Nichts geht verloren: Eine Mail gilt erst als erledigt, wenn ihr Ergebnis in der Planungsdatei steht. Schlägt die Auswertung fehl, kommt sie beim nächsten Lauf wieder dran.
> Nichts doppelt: Dieselbe Mail ergibt auch beim zweiten Lauf keinen zweiten Eintrag.
> Mailinhalte sind fremde Eingaben: Das auswertende Modell hat keine Werkzeuge, liefert nur Daten zurück, und Anweisungen in Mails werden nie ausgeführt.
> Zugangsdaten nur aus dem Schlüsselbund, nie in Dateien oder Logs.
> Trockenlauf: zeigt, was eingetragen würde, ohne zu schreiben.

## Antworten auf Rueckfragen

**2026-10-22 20:24** — Frage: **Was genau meint „doppelt zugestellt" in der Testumgebung?** Dieselbe Mail mit identischer Message-ID und identischem Inhalt, oder auch ein Fall, in dem dieselbe Mail neue Message-ID trägt (Relay-Neuversand)?

> Eine Mail darf natürlich nicht verschluckt werden, dann wäre besser eine doppelte ZUstellung

**2026-10-22 20:28** — Frage: Und zur Dedup-Frage: **Wie geht der Planungsinstanz-Lauf mit einem doppelten Eintrag um?** Das ist der zweite Teil: Wenn das Werkzeug trotz Dedup mal doppelt einträgt (Fehlerfall, oder ein Relay-Neuversand mit neuer Message-ID), ist das ein Befund, den die Planungsinstanz wegfiltert, oder muss das M

> Zu 1: Atomar schreiben (a). Eine Mail gilt erst als erledigt, wenn ihr Eintrag sicher in der Datei steht; scheitert das Schreiben, wird sie beim nächsten Lauf erneut verarbeitet.
> Zu 2: Das Mail-Werkzeug muss selbst duplikatfrei sein – gleiche Message-ID nie zweimal. Gleicher Inhalt mit neuer Message-ID wird eingetragen, aber als „mögliches Duplikat“ markiert, nicht weggelassen. Lieber einmal doppelt als einmal verloren.
> Perspektivisch soll das Werkzeug zu einer Mail einen Antwortentwurf vorformulieren und im Entwürfe-Ordner ablegen können. Das ist nicht Teil dieser Aufgabe: Hier bleibt das Postfach nur lesend. Bitte so aufbauen, dass Entwürfe später als eigener Schritt ergänzt werden können.

**2026-10-22 21:32** — Frage: - A5 fehlt die semantische Validierung des LLM-JSON (nicht nur syntaktisch gültig, sondern: sind die Felder sinnvoll befüllt?). Ob das hier oder in der Planungsinstanz steht, ist offen.

> Es sind viele unklare Punkte vorhanden, dein Kontext ist mit 75 % voll, falls Du hier nicht mehr fertig werden kannst, schreibe hier einen Übergabeprompt an die nächste Instanz um die Unklarheiten zu beseitigen.
> (.venv) hans-wernereberhardt@MacBook-Pro-von-Hans-Werner llama-server % python3 role-split/kette/kette.py quellen mail_planung
> 3 Quellen -> /Users/hans-wernereberhardt/PycharmProjects/llama-server/docs/projekt_management/quellen_20261022_mail_planung.md   10 mit FEHLT/VERWEIGERT/ZU LANG/UNKLAR
>   UNKLAR (nicht geholt): - `agents/llm_scout/llm_scout.py` `def init_db` — SQLite-Schema `processed_items` (UNIQUE-Index auf `url`); Muster für `
>   UNKLAR (nicht geholt): - `agents/llm_scout/llm_scout.py` `def is_new_item` — Abfrage „schon verarbeitet?"; Muster für `is_new_mail`
>   UNKLAR (nicht geholt): - `agents/llm_scout/llm_scout.py` `def mark_as_processed` — `INSERT … ON CONFLICT DO NOTHING`; Muster für `mark_as_proce
>   UNKLAR (nicht geholt): - `scripts/send_scout_email.py` `def get_password` — `subprocess.check_output(["security", "find-generic-password", "-s"
>   UNKLAR (nicht geholt): - `scripts/send_scout_email.py` `def record_sent_week` (Zeilen 340–390) — atomares Schreiben: `tempfile.mkstemp` + `os.r
>   UNKLAR (nicht geholt): - `scripts/send_scout_email.py` `def mode_dry_run` (Zeilen 397–414) — Trockenlauf ohne SMTP, ohne Schlüsselbund, schreib
>   UNKLAR (nicht geholt): - `config/launchd/llm_scout.plist` `EnvironmentVariables` — `LAB_DIR` und `SCOUT_ALLOW_SEND` als launchd-Env-Vars; Muste
>   UNKLAR (nicht geholt): - `tests/test_scout_kw_doppelversand.py` `TestBase.setUp` — Mocking-Muster: `patch.object(mod, "get_password", return_va
>   UNKLAR (nicht geholt): - `tests/test_scout_kw_doppelversand.py` `T9_Pipeline` — Pipeline-E2E mit Ersatzskripten (temporäres Verzeichnis, `subpr
>   UNKLAR (nicht geholt): - `agents/llm_scout/requirements.txt` — vorhandene Abhängigkeiten: `feedparser`, `requests`. Für das Mail-Werkzeug kommt

**2026-10-22 22:19** — Frage: Offene Fragen 1-5 der Spec und A5 (inhaltliche Pruefung des LLM-JSON)

> 1. Tests ohne echten Server, Mail-Zugriff im Test ersetzt. Einen echten Testserver nur mit Fundstelle nennen, sonst offener Punkt. 2. Eigene Variablen MAIL_LLM_URL und MAIL_LLM_MODEL, gleiche Standardwerte wie der Scout. 3. Projektzuordnung ueber eine Konfigurationsdatei (Absender, Domain oder Stichwort -> Projekt), Rest Unzugeordnet. Kein LLM fuer die Zuordnung. 4. Das Werkzeug schreibt nur in seine eigene Datei, die ich nicht bearbeite. Vor dem Merker prueft es, ob der Eintrag dort steht. 5. launchd spaeter, jetzt nur Aufruf von Hand und Trockenlauf. A5: Das Werkzeug prueft das LLM-Ergebnis selbst (Pflichtfelder vorhanden, Datum gueltig); ungueltige Ergebnisse werden nicht eingetragen und die Mail bleibt offen.

