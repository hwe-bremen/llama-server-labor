# Spec: paket_vollstaendig

- **Datum:** 2026-10-25
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Betroffene Dateien:** `role-split/kette/kette.py`, `role-split/kette/test_kette.py` (gelesen); `docs/projekt_management/anforderung_20261025_paket_vollstaendig.md` (Anforderung); `docs/projekt_management/_vorlage_spec.md` (Vorlage)

## Ziel

`kette.py paket <kurztitel>` nimmt alle Code-Dateien auf, die seit dem Rücksetzpunkt (Commit „Spec <kurztitel>") geändert oder neu sind – auch unter `tests/` und `role-split/` – und wendet eine zweistufige Vorrang-Kürzung an, wenn das Paket zu groß ist. `kette.py gegenprobe` berücksichtigt nach derselben Regel auch `role-split/kette/`. Das Review-Modell sieht damit den Code, den es bewerten soll, statt „keine Code-Dateien". Dateien aus fremden Commits (Commit-Nachricht ohne den Kurztitel) werden nur aufgelistet, nicht eingefügt. Ein Paket ohne Code trotz vorhandener Änderungen ist ein lauter Fehler.

## Nicht-Ziele

- Kein neues Tool oder ein anderer Einstiegspunkt als die bestehenden `kette.py paket` und `kette.py gegenprobe`.
- Keine Änderung der Review-Prompts (`review_api.md`, `review2_api.md`) – die ersetzen `{paket_text}` und sind damit automatisch vollständig.
- Keine Änderung der Spec-Vorlage oder des Review-Verfahrens.
- Kein automatischer Versand oder ein anderes Aufrufmodell als `review-auto` (das `paket` schon heute ruft).

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Nichts. `kette.py paket` und `kette.py gegenprobe` arbeiten rein lokal: sie lesen Git-Metadaten und Dateien im Repo, schreiben `review_paket_<datum>_<kurztitel>.md` nach `docs/projekt_management/` (innerhalb des Repos), und – bei `gegenprobe` – setzen Dateien vorübergehend zurück und laufen Tests in einem Unterprozess. Kein Mail, kein Netz, kein Schlüsselbund, kein launchd.
- **Technische Sperre für Tests:** Alle Tests arbeiten in einem temporären Git-Repo (`tempfile.TemporaryDirectory`) und setzen `kette.ROOT` / `kette.PM` auf das temporäre Verzeichnis. `kette.py` selbst wird in den Tests nie auf das echte Repo angewendet. `gegenprobe` setzt Dateien in dem temporären Repo zurück, nicht im echten. Die `gegenprobe`-Tests in `test_kette.py` (Zeile 144–171) tun das schon so.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `python3 role-split/kette/kette.py paket <kurztitel>` von Hand, oder von `kette.py review-auto <kurztitel>` (Zeile 1232: `if paket(kurztitel) != 0: return 2`) | T7 (paket als Modul importiert und direkt aufgerufen), T8 (gegenprobe als Modul) |
| `role-split/kette/kette.py` (gegenprobe) | `python3 role-split/kette/kette.py pruefen <kurztitel>` (Zeile 382–436, aufgerufen von `pruefen`, Zeile 484–485) | T8 |

Beide Einstiegspunkte sind die gleiche Datei und der gleiche Python-Prozess. Es gibt keinen launchd-Einstieg, keine Pipeline, die `kette.py` direkt startet. `review-auto` ruft `paket` als Modul auf (Zeile 1232), nicht als Unterprozess.

## Quellen

- `role-split/kette/kette.py` `def paket` (Zeile 662–716) – die Hauptfunktion, die geändert wird: Paket bauen, Datei schreiben, Return-Code.
- `role-split/kette/kette.py` `def _diff` (Zeile 601–626) – liefert geänderte/neue Dateien gegen den Rücksetzpunkt und deren Diff-Inhalt. Wird um die Vorrang-Klassifikation und die Kürzungsliste erweitert.
- `role-split/kette/kette.py` `def _kappen` (Zeile 629–638) – kapppt eine einzelne Datei auf die Zeilengrenze. Bleibt, aber wird bei der Vorrang-Kürzung nicht mehr aufgerufen, wenn die Datei komplett weggelassen wird.
- `role-split/kette/kette.py` `def _handover_dateien` (Zeile 641–645) – liefert die Pfade aus dem Handover-Abschnitt. Wird für die Vorrang-1-Erkennung weiterverwendet.
- `role-split/kette/kette.py` `def _bloecke` (Zeile 526–540) – extrahiert Abschnitte aus Markdown. Wird von `_handover_dateien` verwendet, nicht direkt geändert.
- `role-split/kette/kette.py` Zeilen 519–523 – Konstanten `PAKET_DIFF_ZEILEN`, `PAKET_DATEI_ZEILEN`, `PAKET_WARNUNG_ZEICHEN`, `PAKET_NIE`; werden angepasst: `PAKET_NIE` verliert `tests/` und `role-split/`, neue Konstante `KETTE_PAKET_MAX` wird eingeführt.
- `role-split/kette/kette.py` `def gegenprobe` (Zeile 382–436) – setzt geänderte Dateien einzeln zurück. Wird um `role-split/kette/` erweitert (Punkt 5 der Anforderung).
- `role-split/kette/kette.py` Zeilen 451–515 – `_pruefen_teile` und `pruefen` kombinieren Teil-Return-Codes per `max()`. Wichtig für den Exit-1-Fall: `pruefen` meldet `max(codes.values())`, und `review-auto` bricht bei `!= 0` ab (Zeile 1232–1233).
- `role-split/kette/kette.py` `def spec_commit` (Zeile 440–448) – liefert den Rücksetzpunkt-Commit. Nicht geändert.
- `role-split/kette/kette.py` Zeilen 553–598 – `_testliste` und `_testcode` liefern Testmethoden-Liste und Testcode. Nicht geändert, aber Teil des Pakets (Abschnitt 4).
- `role-split/kette/kette.py` `def _pruefung_kurz` (Zeile 648–659) – liefert Kurzfassung der Prüfung. Nicht geändert, Teil des Pakets (Abschnitt 6).
- `role-split/kette/kette.py` Zeilen 1218–1354 – `review_auto` ruft `paket(kurztitel)` auf (Paket-Aufruf Zeile 1230–1241). Nicht geändert, aber der Einstiegspunkt für den echten Lauf.
- `role-split/kette/test_kette.py` `class PruefenTests` (Zeile 174–306) – enthält die bestehenden Paket-Tests (`test_paket_inhalt` Zeile 240, `test_paket_nur_dateien_aus_handover_und_nie_werkzeug` Zeile 255, `test_paket_kleine_aenderung_als_diff` Zeile 268, `test_paket_kappt_lange_dateien` Zeile 282, `test_paket_ohne_spec_schreibt_nichts` Zeile 292). Die Tests, die das alte Verhalten festschreiben, werden angepasst.
- `role-split/kette/test_kette.py` `class GegenprobeTests` (Zeile 144–171) – enthält `test_rot_und_gruen`. Wird um einen Test für `role-split/kette/` erweitert.
- `role-split/kette/prompts/review_api.md` Zeile 7 – `{paket_text}`-Platzhalter. Nicht geändert, aber der Konsument des Pakets.
- `role-split/kette/prompts/review2_api.md` Zeile 7 – `{paket_text}`-Platzhalter. Nicht geändert.

## Anforderungen

### A1: Paket nimmt alle geänderten/neuen Code-Dateien der Kette auf
- **Anforderung:** `kette.py paket <kurztitel>` sammelt alle Dateien, die seit dem Rücksetzpunkt (Commit „Spec <kurztitel>") geändert oder neu sind, aus **drei Quellen**:
  1. Commits nach dem Rücksetzpunkt (`git log`/`git diff <rücksetzpunkt> HEAD --name-only`),
  2. nicht committete Änderungen an versionierten Dateien (`git diff HEAD --name-only`),
  3. **neue, unversionierte Dateien** (`git ls-files --others --exclude-standard`) – OpenCode committet nie; in K8 war die Testdatei zur Review-Zeit genau so eine Datei.
  Ausgenommen sind nur `docs/` und die Dateien, die die Kette selbst erzeugt (Spec, Handover, Prüfung, Verdikte, Anforderung, Quellen, Review-Paket – alle unter `docs/`). `tests/`, `role-split/`, `mcp-server/`, `scripts/`, `agents/` werden aufgenommen. Git-ignorierte Dateien (z. B. `experiments/…` laut `.gitignore`/`.git/info/exclude`) bleiben draußen.
- **Zur Kette gehörig oder fremd (Hawe 25.10.):** Eine Datei **gehört zur Kette**, wenn sie (a) in mindestens einem Commit nach dem Rücksetzpunkt geändert wurde, dessen Commit-Nachricht den Kurztitel enthält, oder (b) nicht committet bzw. unversioniert ist, oder (c) in der Übergabe genannt wird. Sonst ist sie **fremd** (nur in Commits ohne den Kurztitel geändert, z. B. Werkzeug-Commits während der Kette). Fremde Dateien kommen **nicht mit Inhalt** ins Paket, sondern in einen eigenen Abschnitt „Fremde Änderungen (nur Liste)" mit Pfad und Kurz-Hash/Betreff der Commits und dem Hinweis „nicht Teil dieser Kette – nicht bewerten, nur zur Kenntnis".
- **Stelle:** `role-split/kette/kette.py`, `def _diff` (Zeile 601–626) und `def paket` (Zeile 662–716); Konstante `PAKET_NIE` (Zeile 523).
- **Akzeptanz:** Im Test: Datei aus Commit mit Kurztitel, nicht committete Änderung und unversionierte neue Datei stehen mit Inhalt im Paket; eine Datei nur aus einem Commit ohne Kurztitel steht nur in der Liste „Fremde Änderungen". Im echten Lauf `review-auto mail_server_test` (A8) nennt das Paket `agents/mail_planung/mail_planung.py` und die Dateien unter `tests/mail_server_test/`; `role-split/kette/kette.py` (K8-Commits) steht nur in der Fremd-Liste.

### A2: Dateien außerhalb des Handovers werden markiert
- **Anforderung:** Jede **zur Kette gehörige** Datei, die im Paket steht, aber im Handover-Abschnitt „Geänderte und neue Dateien" nicht genannt wird, wird im Paket mit dem Hinweis „nicht in der Übergabe genannt – möglicherweise außerhalb des Auftrags" markiert. Die Markierung gilt für alle Vorrang-Stufen, auch Vorrang 1. (Fremde Dateien stehen ohnehin nur in der Fremd-Liste, A1.)
- **Stelle:** `role-split/kette/kette.py`, `def _diff` (Zeile 601–626) – die Kopfzeile jeder Datei im Paketteil.
- **Akzeptanz:** Im Test: eine Datei, die geändert ist aber nicht im Handover steht, erscheint im Paket mit dem Hinweis. Eine Datei, die im Handover steht, erscheint ohne den Hinweis.

### A3: Zweistufige Vorrang-Kürzung bei Paketgröße > 80 000 Zeichen
- **Anforderung:** Die Dateien werden in drei Vorrang-Stufen eingeordnet:
  - **Vorrang 1 (nie kürzen):** alle Dateien aus dem Handover **und** alle zur Kette gehörigen Dateien außerhalb von `tests/` (also `agents/`, `scripts/`, `role-split/` inkl. `.md`-Prompts und Rollen, `mcp-server/`). Fremde Dateien (A1) zählen nie zu Vorrang 1–3, sie stehen nur in der Fremd-Liste.
  - **Vorrang 2:** Testcode unter `tests/` (`.py`, `.sh`, `.command`).
  - **Vorrang 3:** alles andere unter `tests/` (Testdaten wie `.eml`, `.json`, `.txt`).

  Ist die Gesamtpaketgröße (nach Pro-Datei-Kürzung) größer als `PAKET_WARNUNG_ZEICHEN` (80 000 Zeichen), werden erst Vorrang-3-Dateien als ganze Dateien weggelassen, dann Vorrang-2-Dateien als ganze Dateien, jeweils mit einem Eintrag „weggelassen: `<datei>` – <Grund>" im Paket. Die bestehende Begrenzung pro Datei (`PAKET_DIFF_ZEILEN`, `PAKET_DATEI_ZEILEN`) bleibt.
- **Stelle:** `role-split/kette/kette.py`, `def _diff` (Zeile 601–626) – neue Vorrang-Klassifikation und Kürzungslogik; `def paket` (Zeile 662–716) – neue Sektion „Weggelassen" im Paket.
- **Akzeptanz:** Im Test: ein Paket mit 90 000 Zeichen und drei Vorrang-3-Dateien → die Vorrang-3-Dateien stehen in der „Weggelassen"-Liste, nicht im Code-Teil. Vorrang-1-Dateien stehen immer im Code-Teil.

### A4: Harte Obergrenze KETTE_PAKET_MAX, Exit 1 bei Überschreitung
- **Anforderung:** Neue Konstante `KETTE_PAKET_MAX` (Vorgabe 150 000 Zeichen, einstellbar). Ist das Paket auch nach der Vorrang-Kürzung (Vorrang 3 und 2 weg) größer als `KETTE_PAKET_MAX`, bricht `kette.py paket` mit Exit 1 und der Meldung „Paket passt nicht in den Kontext des Review-Modells, Review in Teilen nötig" ab. Es wird kein Paket geschrieben. Kein stilles Abschneiden.
- **Stelle:** `role-split/kette/kette.py`, `def paket` (Zeile 662–716) – neuer Abbruch vor `ziel.write_text`.
- **Akzeptanz:** Im Test: ein Paket, das nach Kürzung noch > 150 000 Zeichen hat → Exit 1, keine `review_paket_*`-Datei, Meldung in der Ausgabe. `pruefen` meldet `max(codes.values())` = 1, `review-auto` bricht bei `!= 0` ab (Zeile 1232–1233).

### A5: Gegenprobe berücksichtigt role-split/kette/
- **Anforderung:** `kette.py gegenprobe` setzt auch Dateien unter `role-split/kette/` zurück, die seit dem Rücksetzpunkt geändert oder neu sind. Die heutige Ausnahme `role-split/kette/` in der Dateifilterung (Zeile 398) wird entfernt. Es gilt dieselbe Auswahl wie in A1: nur **zur Kette gehörige** Code-Dateien außerhalb von `tests/` und `docs/` (einschließlich unversionierter neuer Dateien); fremde Dateien werden nicht zurückgesetzt.
- **Stelle:** `role-split/kette/kette.py`, `def gegenprobe` (Zeile 382–436), Zeile 396–398 (Dateifilter).
- **Akzeptanz:** Im Test: eine geänderte Datei unter `role-split/kette/` wird von `gegenprobe` einzeln zurückgesetzt und in der rot/grün-Liste aufgeführt.

### A6: Bestehende Tests bleiben grün oder werden bewusst angepasst
- **Anforderung:** Die bestehenden Tests in `role-split/kette/test_kette.py` bleiben grün oder werden bewusst angepasst, wenn sie das alte Verhalten festschreiben. Konkret:
  - `test_paket_nur_dateien_aus_handover_und_nie_werkzeug` (Zeile 255–266) prüft, dass `tests/` und `role-split/` im Paket **nicht** vorkommen. Dieser Test muss angepasst werden: Er darf jetzt `tests/` und `role-split/`-Dateien im Paket erwarten.
  - Alle anderen Paket-Tests (`test_paket_inhalt`, `test_paket_kleine_aenderung_als_diff`, `test_paket_kappt_lange_dateien`, `test_paket_ohne_spec_schreibt_nichts`) sollen weiter grün bleiben.
  - `GegenprobeTests.test_rot_und_gruen` (Zeile 145–171) soll weiter grün bleiben.
- **Stelle:** `role-split/kette/test_kette.py`, `class PruefenTests` (Zeile 174–306), `class GegenprobeTests` (Zeile 144–171).
- **Akzeptanz:** `python3 -m unittest -v tests/test_kette.py` → alle Tests ok. Kein Test wird ohne Grund gelöscht.

### A7: Paket ohne Code trotz Änderungen ist ein lauter Fehler
- **Anforderung:** Gibt es seit dem Rücksetzpunkt Änderungen außerhalb von `docs/` (aus irgendeiner der drei Quellen in A1), aber im Paket steht **keine** Datei mit Inhalt, bricht `paket` mit **Exit 1** ab und schreibt die Meldung „Paket ohne Code trotz Änderungen seit <rücksetzpunkt>: <Anzahl> Datei(en), davon <n> fremd. Commits ohne Kurztitel in der Nachricht? Dann Rücksetzpunkt/Kurztitel prüfen." Es wird kein Paket geschrieben. Die Formulierung „Geaenderte Code-Dateien: keine" darf nur noch erscheinen, wenn es seit dem Rücksetzpunkt tatsächlich keine Änderungen außerhalb von `docs/` gibt.
- **Stelle:** `role-split/kette/kette.py`, `def paket`.
- **Akzeptanz:** Im Test: nur ein Commit **ohne** Kurztitel ändert `mod.py` → Exit 1, Meldung, kein Paket. Keinerlei Änderung außer `docs/` → Exit 0 und „keine Code-Dateien" wie bisher.

### A8: Abnahme – echter Lauf am K7-Stand
- **Anforderung:** Nach grünen Tests startet **Hawe** `python3 role-split/kette/kette.py review-auto mail_server_test 2>&1 | tee /tmp/k9_abnahme.log` gegen den echten Router.
- **Stelle:** kein Code; Ausgabe und erzeugte Dateien gehen an Claude.
- **Akzeptanz:** Das Paket `review_paket_20261023_mail_server_test.md` enthält `agents/mail_planung/mail_planung.py` mit Inhalt und nennt die Dateien unter `tests/mail_server_test/` (mit Inhalt oder in der Weggelassen-Liste); `role-split/kette/kette.py` steht nur in der Fremd-Liste; kein Review-Lauf meldet A4/A5 als „nicht umgesetzt". Danach stellt Hawe die überschriebenen K7-Dateien per `git checkout -- docs/projekt_management/review_paket_20261023_mail_server_test.md docs/projekt_management/gesamt_20261023_mail_server_test.md` wieder her (die neuen Verdikte `_3` bleiben als Nachweis).

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A1 | Git-Fehler (Repo beschädigt, kein `git diff`) | nichts | Exit 2, Meldung „git-Fehler: …", kein Paket | T1 |
| A1 | Kein Commit „Spec <kurztitel>" | nichts | Exit 2, Meldung „Kein Commit 'Spec …' – Ruecksetzpunkt mit --commit angeben", kein Paket | T1 |
| A1 | Keine Spec-Datei | nichts | Exit 2, Meldung „Keine Spec …", kein Paket | T1 |
| A1 | Eingabe ungültig (Kurztitel mit Sonderzeichen) | nichts | Exit 2, Meldung „Kurztitel … ungueltig", kein Paket | T1 |
| A1 | Ziel existiert schon (review_paket_* bereits vorhanden) | altes Paket existiert | Paket wird überschrieben (heutiges Verhalten, Zeile 708). Kein Befund. | T2 |
| A1 | Schalter kombiniert (commit + datum) | nichts | Paket wird mit dem angegebenen Commit gebaut. Unverändert gegenüber heute. | T2 |
| A1 | Lauf ohne Testschalter / gegen echte Daten | nichts | `paket` arbeitet immer lokal, kein externer Aufruf. Unverändert. | T2 |
| A1 | Absturz mitten im Lauf (git-Subprozess bricht ab) | nichts | `subprocess.CalledProcessError` wird gefangen (Zeile 681–682), Exit 2, Meldung. Kein Paket. | T1 |
| A2 | Handover-Datei nicht im Handover genannt (außerhalb `tests/`) | nichts | Datei erscheint im Paket mit dem Hinweis „nicht in der Übergabe genannt". Vorrang 1, nie gekürzt. | T3 |
| A2 | Handover existiert nicht | nichts | `_handover_dateien` liefert `None` (Zeile 645). Alle Dateien werden als „nicht in der Übergabe genannt" markiert. Unverändert gegenüber heute (heute: `nur = None` → alle Dateien). | T3 |
| A2 | Handover-Abschnitt „Geänderte und neue Dateien" leer | nichts | `_handover_dateien` liefert `None`. Wie oben. | T3 |
| A2 | Ziel existiert schon | altes Paket existiert | Paket wird überschrieben. Unverändert. | T2 |
| A2 | Schalter kombiniert | nichts | Unverändert. | T2 |
| A2 | Lauf ohne Testschalter / gegen echte Daten | nichts | Unverändert. | T2 |
| A2 | Absturz mitten im Lauf | nichts | Wie A1. | T1 |
| A3 | Paket genau 80 000 Zeichen | nichts | Kein Kürzen. Paket wird geschrieben. Exit 0. | T4 |
| A3 | Paket 90 000 Zeichen, drei Vorrang-3-Dateien | nichts | Vorrang-3-Dateien werden weggelassen, in der „Weggelassen"-Liste aufgeführt. Restpaket < 80 000 → Exit 0. | T4 |
| A3 | Paket 90 000 Zeichen, nur Vorrang-1-Dateien (kürzen unmöglich) | nichts | Kein Kürzen möglich. Paket bleibt > 80 000. Exit 0, Warnung (Zeile 711–713). | T4 |
| A3 | Paket 200 000 Zeichen, Vorrang 3 und 2 weggelassen, immer noch > 150 000 | nichts | `KETTE_PAKET_MAX` überschritten → Exit 1, Meldung, kein Paket. | T5 |
| A3 | Schalter kombiniert | nichts | Unverändert. | T2 |
| A3 | Lauf ohne Testschalter / gegen echte Daten | nichts | Unverändert. | T2 |
| A3 | Absturz mitten im Lauf | nichts | Wie A1. | T1 |
| A4 | KETTE_PAKET_MAX = 0 (ungültig) | nichts | Konstante ist 150 000, wird nicht zur Laufzeit geändert. Unverändert. | T5 |
| A4 | Paket genau 150 000 Zeichen nach Kürzung | nichts | Kein Abbruch. Paket wird geschrieben. Exit 0. | T5 |
| A4 | Ziel existiert schon | altes Paket existiert | Kein neues Paket wird geschrieben (Exit 1 vor dem Schreiben). Altes Paket bleibt. | T5 |
| A4 | Schalter kombiniert | nichts | Unverändert. | T2 |
| A4 | Lauf ohne Testschalter / gegen echte Daten | nichts | Unverändert. | T2 |
| A4 | Absturz mitten im Lauf | nichts | Wie A1. | T1 |
| A5 | Datei unter role-split/kette/ geändert, Test wird rot | nichts | Datei wird einzeln zurückgesetzt, Test rot, Datei in der rot-Liste. Exit 1. | T6 |
| A5 | Keine geänderten Code-Dateien seit Rücksetzpunkt | nichts | Meldung „Keine geaenderten Code-Dateien", Exit 2. Unverändert gegenüber heute. | T6 |
| A5 | Testskript existiert nicht | nichts | Meldung „Kein Testskript …", Exit 2. Unverändert. | T6 |
| A5 | Schalter kombiniert | nichts | Unverändert. | T6 |
| A5 | Lauf ohne Testschalter / gegen echte Daten | nichts | `gegenprobe` setzt Dateien im temporären Repo zurück, nicht im echten. Unverändert. | T6 |
| A5 | Absturz mitten im Lauf (Tests laufen zu lange) | `tests_laufen` liefert `None` (Timeout) | Meldung „Zeitueberschreitung", Datei wird übersprungen. Unverändert. | T6 |
| A6 | Bestehender Test prüft altes Verhalten (tests/ nicht im Paket) | nichts | Test wird angepasst. `python3 role-split/kette/test_kette.py` → ok. | T7 |
| A1 | neue, unversionierte Datei (nicht committet) | nichts | mit Inhalt im Paket, zur Kette gehörig | T2 |
| A1 | Datei nur in einem Commit ohne Kurztitel (fremd) | nichts | nur in „Fremde Änderungen (nur Liste)", kein Inhalt, nicht in Vorrang 1–3 | T8 |
| A1 | fremde Datei, die die Übergabe nennt | nichts | gehört zur Kette, mit Inhalt | T8 |
| A7 | Änderungen nur in fremden Commits | nichts | Exit 1, Meldung „Paket ohne Code trotz Änderungen …", kein Paket | T9 |
| A7 | gar keine Änderungen außer docs/ | nichts | Exit 0, „keine Code-Dateien" wie bisher | T9 |
| A8 | echter Lauf am K7-Stand | K7-Paket und -Gesamtbefund werden überschrieben | Hawe stellt sie per `git checkout` wieder her | T10 |

## Testplan

Alle Tests werden als `tests/test_kette_paket_vollstaendig.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung. Alle Tests arbeiten in einem temporären Git-Repo und setzen `kette.ROOT` / `kette.PM` auf das temporäre Verzeichnis. Neue Funktionen im Test werden **in der Methode** importiert, nicht am Dateianfang.

### T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)
- **Prüft:** A1, Fehlerpfade „Git-Fehler", „Kein Commit", „Keine Spec", „Eingabe ungültig"
- **Aufbau:** Temporäres Git-Repo mit einer Spec-Datei, einem `mod.py`, und einem Commit „Spec g". Dann: (a) `mod.py` wird geändert und committet, (b) `kette.paket("g")` wird aufgerufen. Für die Fehlerpfade: (a) kein Commit „Spec g", (b) keine Spec-Datei, (c) Kurztitel mit Sonderzeichen.
- **Erwartung:** (a) Exit 0, Paket existiert. (b) Exit 2, „Kein Commit", kein Paket. (c) Exit 2, „Keine Spec", kein Paket. (d) Exit 2, „ungueltig", kein Paket.
- **Warum misst der Test das Richtige?** Wenn die Anforderung NICHT erfüllt ist (z. B. `PAKET_NIE` enthält noch `tests/`), enthält das Paket in (a) nicht die `tests/`-Dateien – der Test T2 würde scheitern, nicht T1. T1 misst nur, dass die Fehlerpfade sauber abbrechen.
- **Gegenprobe:** Keine. T1 prüft Fehlerpfade, nicht die neue Funktionsweise.

### T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte
- **Prüft:** A1, A2
- **Aufbau:** Temporäres Git-Repo: Commit „Spec g", dann `mod.py` geändert und mit der Nachricht „g: mod" committet; `tests/test_g.py` und `tests/testdaten/auspruefen.json` neu und **nicht committet (unversioniert)**; `role-split/kette/hilfs.py` neu und nur `git add` (nicht committet). Handover nennt nur `mod.py`.
- **Erwartung:** Exit 0. Paket enthält `### mod.py`, `### tests/test_g.py`, `### tests/testdaten/auspruefen.json`, `### role-split/kette/hilfs.py`. Die drei Dateien außer `mod.py` tragen den Hinweis „nicht in der Übergabe genannt".
- **Warum misst der Test das Richtige?** Wenn `PAKET_NIE` noch `tests/` oder `role-split/` enthält, fehlen diese Dateien im Paket – der Test scheitert. Wenn die Markierung fehlt, scheitert der Test beim `assertIn("nicht in der Übergabe genannt", …)`.
- **Gegenprobe:** `kette.py` muss die neue `PAKET_NIE`-Liste und die Markierungslogik in `_diff` enthalten. Im alten Code (PAKET_NIE mit `tests/` und `role-split/`) fehlen die Dateien → Test rot.

### T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung
- **Prüft:** A2
- **Aufbau:** Wie T2, aber Handover nennt `mod.py` und `tests/test_g.py`. `role-split/kette/hilfs.py` ist nicht im Handover.
- **Erwartung:** `mod.py` und `tests/test_g.py` im Paket **ohne** den Hinweis. `role-split/kette/hilfs.py` **mit** dem Hinweis.
- **Warum misst der Test das Richtige?** Wenn die Markierungslogik nicht prüft, ob die Datei im Handover steht, fehlen oder fehlen nicht die Hinweise – der Test scheitert.
- **Gegenprobe:** Wie T2.

### T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen
- **Prüft:** A3
- **Aufbau:** Temporäres Git-Repo: Commit „Spec g", dann: `mod.py` geändert (Vorrang 1, ~5000 Zeichen), `tests/test_g.py` neu (Vorrang 2, ~5000 Zeichen), `tests/testdaten/auspruefen.eml` neu (Vorrang 3, ~90 000 Zeichen). Gesamtpaket > 80 000 Zeichen.
- **Erwartung:** Exit 0. Paket enthält `mod.py` und `tests/test_g.py`. `tests/testdaten/auspruefen.eml` steht in der Sektion „Weggelassen" mit „weggelassen: `tests/testdaten/auspruefen.eml` – Testdaten, Paket zu groß". Gesamtpaket < 80 000 Zeichen.
- **Warum misst der Test das Richtige?** Wenn die Vorrang-Kürzung nicht funktioniert, bleibt die `.eml`-Datei im Paket und das Paket ist > 80 000 Zeichen – der Test scheitert.
- **Gegenprobe:** `kette.py` muss die Vorrang-Klassifikation und die Kürzungslogik in `_diff` enthalten. Im alten Code (keine Vorrang-Kürzung) bleibt die `.eml`-Datei → Test rot.

### T5: KETTE_PAKET_MAX überschritten → Exit 1
- **Prüft:** A4
- **Aufbau:** Temporäres Git-Repo: Commit „Spec g", dann: `mod.py` geändert (Vorrang 1, ~200 000 Zeichen). Kein Vorrang 2 oder 3 (nichts zu kürzen). Gesamtpaket > 150 000 Zeichen.
- **Erwartung:** Exit 1. Meldung „Paket passt nicht in den Kontext des Review-Modells, Review in Teilen nötig". Keine `review_paket_*`-Datei.
- **Warum misst der Test das Richtige?** Wenn der Abbruch fehlt, wird das Paket geschrieben – der Test scheitert beim `assertEqual(code, 1)` und beim `assertFalse(ziel.exists())`.
- **Gegenprobe:** `kette.py` muss den Abbruch vor `ziel.write_text` in `paket` enthalten. Im alten Code (kein Abbruch) wird das Paket geschrieben → Test rot.

### T6: Gegenprobe berücksichtigt role-split/kette/
- **Prüft:** A5
- **Aufbau:** Temporäres Git-Repo: Commit „Spec g", dann `role-split/kette/hilfs.py` neu (wird vom Testskript `tests/test_g.py` importiert und getestet), `tests/test_g.py` neu.
- **Erwartung:** `kette.gegenprobe("g", alt)` → Exit 1. Ausgabe enthält „rot   test_t1_hilfs  <- Hilfs.py" (oder ähnlich). `role-split/kette/hilfs.py` wird zurückgesetzt und wiederhergestellt.
- **Warum misst der Test das Richtige?** Wenn die Ausnahme `role-split/kette/` noch in der Dateifilterung (Zeile 398) steht, wird die Datei nicht zurückgesetzt – der Test bleibt grün statt rot – der Test scheitert.
- **Gegenprobe:** `kette.py` muss die Ausnahme `role-split/kette/` aus Zeile 398 entfernt haben. Im alten Code wird die Datei übersprungen → Test rot.

### T7: Bestehende Tests in test_kette.py bleiben grün
- **Prüft:** A6
- **Aufbau:** `python3 role-split/kette/test_kette.py` wird im echten Repo aufgerufen (kein temporäres Repo – die Tests in `test_kette.py` bauen ihre eigenen temporären Repos auf).
- **Erwartung:** Alle Tests `ok`. Kein `FAIL`, kein `ERROR`.
- **Warum misst der Test das Richtige?** Wenn ein bestehender Test das alte Verhalten festschreibt und nicht angepasst wurde, wird er rot – der Test scheitert.
- **Gegenprobe:** `test_kette.py` muss die angepassten Tests enthalten. Im alten Code (mit `test_paket_nur_dateien_aus_handover_und_nie_werkzeug` unanpasst) wird der Test rot → Test scheitert.

### T8: Fremde Commits nur als Liste
- **Prüft:** A1 (zur Kette gehörig / fremd)
- **Aufbau:** Temporäres Git-Repo: Commit „Spec g"; Commit „g: mod" ändert `mod.py`; Commit „Werkzeug: x" (ohne Kurztitel) ändert `werkzeug.py` und `anderes.py`. Handover nennt `mod.py` und `anderes.py`.
- **Erwartung:** `mod.py` und `anderes.py` mit Inhalt im Paket (`anderes.py` gehört über die Übergabe dazu); `werkzeug.py` nur im Abschnitt „Fremde Änderungen (nur Liste)" mit Commit-Betreff „Werkzeug: x", sein Inhalt steht nicht im Paket.
- **Warum misst der Test das Richtige?** Ohne Klassifikation stünde `werkzeug.py` mit Inhalt im Paket (Problem vom 22.10.); ohne Übergabe-Ausnahme fehlte `anderes.py`.
- **Gegenprobe:** Klassifikation entfernen → `werkzeug.py`-Inhalt im Paket → rot.

### T9: Paket ohne Code trotz Änderungen → Exit 1
- **Prüft:** A7
- **Aufbau:** (a) Commit „Spec g", danach nur Commit „Werkzeug: x" (ohne Kurztitel) ändert `mod.py`. (b) Commit „Spec g", danach nur Änderung unter `docs/`.
- **Erwartung:** (a) Exit 1, Meldung enthält „Paket ohne Code trotz Änderungen", keine `review_paket_*`-Datei. (b) Exit 0, Paket mit „keine Code-Dateien".
- **Warum misst der Test das Richtige?** Fall (a) ist genau K7: Paket ohne Code, das trotzdem ans Review ging.
- **Gegenprobe:** Ohne die Prüfung entsteht in (a) ein Paket „keine Code-Dateien" mit Exit 0 → rot.

### T10: Abnahme – echter Lauf am K7-Stand (Hawe, manuell)
- **Prüft:** A8
- **Aufbau:** Lab mit Router; `python3 role-split/kette/kette.py review-auto mail_server_test 2>&1 | tee /tmp/k9_abnahme.log`.
- **Erwartung:** siehe A8 (mail_planung.py mit Inhalt, K8-Dateien nur in der Fremd-Liste, kein Review-Lauf meldet A4/A5 als fehlend).
- **Warum misst der Test das Richtige?** Nur der echte Lauf zeigt, ob das automatische Review jetzt sieht, was es bewerten soll (R14, R34).
- **Gegenprobe:** n. a. (manuell); Claude prüft Paket und Verdikte.

## Offene Fragen

- Geklärt 25.10. (Hawe): Keine harte „muss immer drin"-Liste – die Vorrang-Regel plus die Klassifikation „zur Kette gehörig / fremd" (A1) reicht. `KETTE_PAKET_MAX` = 150 000 Zeichen bleibt, einstellbar. Begründung: Der Rahmen (Anforderung, Spec-Auszug, Übergabe, Prüfung) steckt bereits im Paket; gemessen am K7-Paket ~3 Zeichen/Token (43 096 Zeichen → ~14 800 Prompt-Token) → 150 000 Zeichen ≈ 50 000 Token, plus Prompt und Antwort unter 64K.
- Offen für die Umsetzung: Ob `KETTE_PAKET_MAX` über eine Umgebungsvariable gleichen Namens einstellbar wird (empfohlen, wie `KETTE_LLM_TIMEOUT` in K8).

## Abweichende Meinung

Keine. Die zweistufige Kürzung mit Vorrang 1 = „außerhalb `tests/`" ist die einfachste Regel, die die Abnahme erfüllt, ohne eine harte Liste in `kette.py` zu benötigen. Die harte Obergrenze (Exit 1) ist ein sauberer Ausweg für den Fall, dass selbst Vorrang 1 allein zu groß ist.
- **Nachtrag 25.10. (Claude, Gegenprüfung vor Commit, mit Hawes Zustimmung eingearbeitet):** unversionierte neue Dateien ausdrücklich in A1 (Anforderung Punkt 1); Punkt 4 der Anforderung fehlte (jetzt A7/T9); Abnahme als eigener Schritt (A8/T10); Klassifikation „zur Kette gehörig / fremd" über den Kurztitel in der Commit-Nachricht, damit fremde Commits (z. B. K8 nach dem K7-Spec-Commit) nicht als Vorrang 1 das Paket sprengen; T7 mit richtigem Pfad; Rechnung zu 150 000 Zeichen korrigiert.
