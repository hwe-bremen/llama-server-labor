# Review-Paket: paket_vollstaendig


Erzeugt 2026-10-27 08:10 von `kette.py paket`. Ruecksetzpunkt: `84e3bb7`. Geaenderte Code-Dateien: `role-split/kette/kette.py`, `role-split/kette/prompts/review2_api.md`, `role-split/kette/prompts/review_api.md`, `role-split/kette/test_kette.py`, `tests/test_kette_review_auto.py`, `tests/test_paket_vollstaendig.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: paket_vollstaendig

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Das automatische Review (review-auto) ist blind, weil das Review-Paket oft keinen Code enthält. kette.py paket nimmt nur Dateien, die die Übergabe nennt, und lässt tests/ und role-split/ grundsätzlich weg. Im echten Lauf am K7-Stand haben deshalb beide Review-Läufe A4/A5 fälschlich als „nicht umgesetzt“ gemeldet. Das soll sich ändern:
> 1. kette.py paket <kurztitel> nimmt alle Code-Dateien auf, die seit dem Rücksetzpunkt geändert oder neu sind: Commits, nicht committete Änderungen und neue, noch nicht versionierte Dateien. Auch unter tests/ und role-split/. Weggelassen werden nur docs/ und die Dateien, die die Kette selbst erzeugt (Spec, Übergabe, Verdikte usw.).
> 2. Dateien, die geändert sind, aber in der Übergabe nicht genannt werden, kommen trotzdem ins Paket, aber deutlich markiert als „nicht in der Übergabe genannt – möglicherweise außerhalb des Auftrags oder fremder Commit“.
> 3. Bleibt das Paket zu groß, wird nach Vorrang gekürzt: erst Code, dann Tests, dann Testdaten (z. B. .eml, .json). Was gekürzt oder weggelassen wurde, steht ausdrücklich im Paket. Nie still weglassen.
> 4. Steht im Paket trotzdem „keine Code-Dateien“, obwohl es Änderungen gibt, ist das ein lauter Fehler, kein stilles Ergebnis.
> 5. gegenprobe berücksichtigt nach derselben Regel auch role-split/kette/.
> Bestehende Tests in role-split/kette/test_kette.py müssen grün bleiben oder bewusst angepasst werden, wenn sie das alte Verhalten festschreiben. Abnahme: echter Lauf review-auto mail_server_test, A4/A5 dürfen nicht mehr als fehlend gemeldet werden, und das Paket nennt agents/mail_planung/mail_planung.py und die Dateien unter tests/mail_server_test/.
> Lies NUR zwei Dateien: diese Anforderung und docs/projekt_management/spec_paket_20261025_paket_vollstaendig.md (alle nötigen Codestellen mit echten Zeilennummern und gemessenen Fakten). Weitere Stellen nur, wenn wirklich etwas fehlt: search_files, dann read_file mit start_line/end_line, höchstens drei Mal.

## Antworten auf Rueckfragen

**2026-10-25 19:00** — Frage: - **(b)** Die Paketgröße überschreitet 80 000 Zeichen → kürze nur, was **nicht** zur Abnahme gehört (also keine `agents/mail_planung/`, keine `tests/mail_server_test/`-Dateien), und die Abnahme-Dateien bleiben immer drin?

> Puh, das sind ja zwei unlösbare Probleme, was würdest du vorschlagen?

**2026-10-25 19:06** — Frage: **Eine Rückfrage, die das Ergebnis ändert:** Ist `agents/` immer Produktionscode, oder gibt es unter `agents/` auch Test- oder Infrastrukturcode, der nicht zum Auftrag gehört? Wenn ja, muss die Vorrang-1-Regel feiner sein. Wenn nein, ist „unter `agents/` = Vorrang 1" eine saubere, einfache Regel.

> Ich nehme deine zweistufige Kürzung, mit diesen Änderungen:
>
> Vorrang 1, nie weglassen: alle Dateien aus der Übergabe und alle geänderten Dateien außerhalb von tests/, also agents/, scripts/, role-split/ (dort auch .md-Prompts und Rollen), mcp-server/. agents/ ist nicht nur Produktionscode, dort liegt z. B. auch test_imap_server.py. Darum die Trennung „außerhalb oder innerhalb von tests/“.
> Vorrang 2: Testcode unter tests/ (.py, .sh).
> Vorrang 3: alles andere unter tests/, also Testdaten wie .eml und .json.
> Über 80 000 Zeichen: zuerst Vorrang 3, dann Vorrang 2 als ganze Dateien weglassen, jeweils mit Liste im Paket („weggelassen: <datei> – <Grund>“). Die bestehende Begrenzung pro Datei (Diff bzw. Zeilenzahl) bleibt.
> Harte Obergrenze: Ist das Paket auch nach dem Kürzen größer als eine einstellbare Grenze (Vorgabe 150 000 Zeichen, Variable z. B. KETTE_PAKET_MAX), bricht paket mit Exit 1 und klarer Meldung ab: „Paket passt nicht in den Kontext des Review-Modells, Review in Teilen nötig.“ Kein stilles Abschneiden.
> Markierung „nicht in der Übergabe genannt“ gilt weiterhin für jede Datei, die die Übergabe nicht nennt, auch für Vorrang 1.

**2026-10-25 19:32** — Frage: 2. Ist 150 000 Zeichen die richtige Obergrenze, oder soll sie niedriger sein?

> 150 000 Zeichen bleibt als Vorgabe, einstellbar über `KETTE_PAKET_MAX` (Messung K7: ~3 Zeichen/Token, der Rahmen steckt schon im Paket). Keine harte „muss immer drin"-Liste. Fremde Commits: Die Kette erkennt ihre eigenen Commits am Kurztitel in der Commit-Nachricht; Dateien, die nur in fremden Commits geändert wurden, werden nur namentlich aufgelistet (mit Commit, markiert, ohne Inhalt) – außer die Übergabe nennt sie.
> (Von Claude nach Hawes Zustimmung am 25.10. 19:43 eingetragen; ersetzt eine versehentlich mitgeschriebene Terminal-Ausgabe.)

## 2. Spec (Auszug aus `spec_20261025_paket_vollstaendig.md`)

### Ziel
`kette.py paket <kurztitel>` nimmt alle Code-Dateien auf, die seit dem Rücksetzpunkt (Commit „Spec <kurztitel>") geändert oder neu sind – auch unter `tests/` und `role-split/` – und wendet eine zweistufige Vorrang-Kürzung an, wenn das Paket zu groß ist. `kette.py gegenprobe` berücksichtigt nach derselben Regel auch `role-split/kette/`. Das Review-Modell sieht damit den Code, den es bewerten soll, statt „keine Code-Dateien". Dateien aus fremden Commits (Commit-Nachricht ohne den Kurztitel) werden nur aufgelistet, nicht eingefügt. Ein Paket ohne Code trotz vorhandener Änderungen ist ein lauter Fehler.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- Kein neues Tool oder ein anderer Einstiegspunkt als die bestehenden `kette.py paket` und `kette.py gegenprobe`.
- Keine Änderung der Review-Prompts (`review_api.md`, `review2_api.md`) – die ersetzen `{paket_text}` und sind damit automatisch vollständig.
- Keine Änderung der Spec-Vorlage oder des Review-Verfahrens.
- Kein automatischer Versand oder ein anderes Aufrufmodell als `review-auto` (das `paket` schon heute ruft).

### Anforderungen
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

### Testplan (nur Titel und Erwartungen)
### T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)
- **Erwartung:** (a) Exit 0, Paket existiert. (b) Exit 2, „Kein Commit", kein Paket. (c) Exit 2, „Keine Spec", kein Paket. (d) Exit 2, „ungueltig", kein Paket.
### T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte
- **Erwartung:** Exit 0. Paket enthält `### mod.py`, `### tests/test_g.py`, `### tests/testdaten/auspruefen.json`, `### role-split/kette/hilfs.py`. Die drei Dateien außer `mod.py` tragen den Hinweis „nicht in der Übergabe genannt".
### T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung
- **Erwartung:** `mod.py` und `tests/test_g.py` im Paket **ohne** den Hinweis. `role-split/kette/hilfs.py` **mit** dem Hinweis.
### T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen
- **Erwartung:** Exit 0. Paket enthält `mod.py` und `tests/test_g.py`. `tests/testdaten/auspruefen.eml` steht in der Sektion „Weggelassen" mit „weggelassen: `tests/testdaten/auspruefen.eml` – Testdaten, Paket zu groß". Gesamtpaket < 80 000 Zeichen.
### T5: KETTE_PAKET_MAX überschritten → Exit 1
- **Erwartung:** Exit 1. Meldung „Paket passt nicht in den Kontext des Review-Modells, Review in Teilen nötig". Keine `review_paket_*`-Datei.
### T6: Gegenprobe berücksichtigt role-split/kette/
- **Erwartung:** `kette.gegenprobe("g", alt)` → Exit 1. Ausgabe enthält „rot   test_t1_hilfs  <- Hilfs.py" (oder ähnlich). `role-split/kette/hilfs.py` wird zurückgesetzt und wiederhergestellt.
### T7: Bestehende Tests in test_kette.py bleiben grün
- **Erwartung:** Alle Tests `ok`. Kein `FAIL`, kein `ERROR`.
### T8: Fremde Commits nur als Liste
- **Erwartung:** `mod.py` und `anderes.py` mit Inhalt im Paket (`anderes.py` gehört über die Übergabe dazu); `werkzeug.py` nur im Abschnitt „Fremde Änderungen (nur Liste)" mit Commit-Betreff „Werkzeug: x", sein Inhalt steht nicht im Paket.
### T9: Paket ohne Code trotz Änderungen → Exit 1
- **Erwartung:** (a) Exit 1, Meldung enthält „Paket ohne Code trotz Änderungen", keine `review_paket_*`-Datei. (b) Exit 0, Paket mit „keine Code-Dateien".
### T10: Abnahme – echter Lauf am K7-Stand (Hawe, manuell)
- **Erwartung:** siehe A8 (mail_planung.py mit Inhalt, K8-Dateien nur in der Fremd-Liste, kein Review-Lauf meldet A4/A5 als fehlend).

### Offene Fragen
- Geklärt 25.10. (Hawe): Keine harte „muss immer drin"-Liste – die Vorrang-Regel plus die Klassifikation „zur Kette gehörig / fremd" (A1) reicht. `KETTE_PAKET_MAX` = 150 000 Zeichen bleibt, einstellbar. Begründung: Der Rahmen (Anforderung, Spec-Auszug, Übergabe, Prüfung) steckt bereits im Paket; gemessen am K7-Paket ~3 Zeichen/Token (43 096 Zeichen → ~14 800 Prompt-Token) → 150 000 Zeichen ≈ 50 000 Token, plus Prompt und Antwort unter 64K.
- Offen für die Umsetzung: Ob `KETTE_PAKET_MAX` über eine Umgebungsvariable gleichen Namens einstellbar wird (empfohlen, wie `KETTE_LLM_TIMEOUT` in K8).

## 3. Code-Aenderungen gegen `84e3bb7`

### role-split/kette/kette.py (Diff, 309 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index 1f9bb59..ec05576 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -387,15 +387,12 @@ def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
     if not skript.is_file():
         print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
     try:
-        diff = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", commit],
-                              capture_output=True, text=True, check=True).stdout.split()
-        neu = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
-                             capture_output=True, text=True, check=True).stdout.split()
+        kette, _fremd = _aenderungen(commit, kurztitel)
     except subprocess.CalledProcessError as e:
         print(f"git-Fehler: {e.stderr.strip()}"); return 2
-    dateien = sorted({d for d in diff + neu
-                      if d.endswith((".py", ".sh", ".command")) and (ROOT / d).exists()
-                      and not d.startswith(("tests/", "docs/", "role-split/kette/", "experiments/"))})
+    # A5: dieselbe Auswahl wie paket – nur zur Kette gehoerige Code-Dateien, auch role-split/kette/
+    dateien = sorted(d for d in kette
+                     if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))
     if not dateien:
         print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2
 
@@ -519,8 +516,49 @@ def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> in
 PAKET_DIFF_ZEILEN = 700        # je Datei; Rest liest das Review gezielt nach
 PAKET_DATEI_ZEILEN = 900       # bei Umbau: ganze aktuelle Datei statt Diff, hoechstens so viele Zeilen
 PAKET_WARNUNG_ZEICHEN = 80000  # ~23k Token: darueber wird es fuer 64K Kontext eng
-# Werkzeug-/Infrastruktur-Ordner gehoeren nie zur Aufgabe (sonst landen spaetere Werkzeug-Commits im Diff).
-PAKET_NIE = ("docs/", "tests/", "role-split/", "mcp-server/", "experiments/")
+# Nur docs/ und experiments/ gehoeren nie ins Paket. .md-Dateien in role-split/, tests/ etc. werden aufgenommen.
+PAKET_NIE = ("docs/", "experiments/",)
+# Harte Obergrenze: darueber bricht paket mit Exit 1 ab (nach Vorrang-Kuerzung).
+KETTE_PAKET_MAX = int(os.environ.get("KETTE_PAKET_MAX", "150000"))
+
+
+def _git(*a: str) -> str:
+    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
+
+
+def _aenderungen(commit: str, kurztitel: str | None, nur: set[str] | None = None
+                 ) -> tuple[list[str], list[tuple[str, list[tuple[str, str]]]]]:
+    """A1: Alle seit <commit> geaenderten/neuen Dateien (ausser PAKET_NIE), getrennt nach
+    zur Kette gehoerig / fremd. Gemeinsame Auswahl fuer paket und gegenprobe (A5).
+
+    Quellen: Commits <commit>..HEAD, nicht committete Aenderungen (auch vorgemerkt),
+    unversionierte Dateien. Zur Kette gehoert eine Datei, wenn sie (a) in einem Commit mit dem
+    Kurztitel in der Nachricht geaendert wurde, (b) nicht committete oder unversionierte
+    Aenderungen hat oder (c) in der Uebergabe genannt wird. Sonst fremd.
+    Rueckgabe: (kette, fremd) mit fremd = [(datei, [(kurzhash, betreff), ...]), ...]."""
+    committet = set(_git("diff", "--name-only", commit, "HEAD").split())
+    offen = set(_git("diff", "--name-only", "HEAD").split())          # unstaged + staged
+    neu = set(_git("ls-files", "--others", "--exclude-standard").split())
+    alle = sorted(d for d in committet | offen | neu
+                  if not d.startswith(PAKET_NIE) and (ROOT / d).is_file())
+    log = [z.split("\t", 1) for z in _git("log", "--format=%H%x09%s", f"{commit}..HEAD").splitlines()
+           if "\t" in z]
+    # Kurztitel als ganzes Wort (nicht "g" in "gross"): links/rechts kein a-z, 0-9, _
+    muster = re.compile(rf"(?<![a-z0-9_]){re.escape(kurztitel)}(?![a-z0-9_])") if kurztitel else None
+    eigene = {h for h, betreff in log if muster and muster.search(betreff)}
+    kette: list[str] = []
+    fremd: list[tuple[str, list[tuple[str, str]]]] = []
+    for d in alle:
+        if d in offen or d in neu or (nur and d in nur):
+            kette.append(d)
+            continue
+        dc = [z.split("\t", 1) for z in
+              _git("log", "--format=%H%x09%s", f"{commit}..HEAD", "--", d).splitlines() if "\t" in z]
+        if any(h in eigene for h, _ in dc):
+            kette.append(d)
+        else:
+            fremd.append((d, [(h[:7], b) for h, b in dc]))
+    return kette, fremd
 
 
 def _bloecke(text: str, muster: str) -> str:
@@ -598,38 +636,45 @@ def _testcode(skript: Path, auffaellig: set[str], grenze: int = 60) -> str:
     return "\n\n".join(teile)
 
 
-def _diff(commit: str, nur: set[str] | None = None) -> tuple[str, list[str]]:
-    """Code-Aenderungen gegen commit. Nie Werkzeug-/Doku-/Testordner (PAKET_NIE).
-    nur: wenn gesetzt (aus dem Handover), nur diese Dateien.
-    Kleine Aenderung -> Diff; Umbau (Diff laenger als die Datei) oder neue Datei -> aktuelle Datei mit
-    Zeilennummern (kuerzer und lesbarer)."""
-    def git(*a):
-        return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
-    geaendert = git("diff", "--name-only", commit).split()
-    neu = git("ls-files", "--others", "--exclude-standard").split()
-    def code(d):
-        return (not d.startswith(PAKET_NIE) and not d.endswith(".md") and (ROOT / d).is_file()
-                and (nur is None or d in nur))
-    teile, dateien = [], []
-    for d in sorted({x for x in geaendert + neu if code(x)}):
+def _vorrang(d: str, nur: set[str] | None) -> int:
+    """A3: 1 = Uebergabe oder ausserhalb tests/ (nie kuerzen), 2 = Testcode, 3 = Testdaten."""
+    if (nur and d in nur) or not d.startswith("tests/"):
+        return 1
+    return 2 if d.endswith((".py", ".sh", ".command")) else 3
+
+
+def _diff(commit: str, nur: set[str] | None = None, kurztitel: str | None = None
+          ) -> tuple[dict[str, tuple[str, int]], list[str], list[str]]:
+    """Inhalte der zur Kette gehoerigen Dateien gegen <commit>.
+    Rueckgabe: (eintraege {datei: (abschnitt, vorrang)}, fremd_zeilen, kette_dateien)."""
+    kette, fremd = _aenderungen(commit, kurztitel, nur)
+    neu = set(_git("ls-files", "--others", "--exclude-standard").split())
+    eintraege: dict[str, tuple[str, int]] = {}
+    for d in kette:
+        nicht_genannt = nur is None or d not in nur
         aktuell = (ROOT / d).read_text(encoding="utf-8", errors="replace").splitlines()
         nummeriert = [f"{i:4d}  {z}" for i, z in enumerate(aktuell, 1)]
-        if d in neu and d not in geaendert:
-            teile.append(_kappen(d, nummeriert, "neu", PAKET_DATEI_ZEILEN))
+        if d in neu:
+            inhalt = _kappen(d, nummeriert, "neu", PAKET_DATEI_ZEILEN, nicht_genannt)
         else:
-            diff = git("diff", "-U3", commit, "--", d).splitlines()
+            diff = _git("diff", "-U3", commit, "--", d).splitlines()
             if len(diff) > len(aktuell):
-                teile.append(_kappen(d, nummeriert, "umbau", PAKET_DATEI_ZEILEN))
+                inhalt = _kappen(d, nummeriert, "umbau", PAKET_DATEI_ZEILEN, nicht_genannt)
             else:
-                teile.append(_kappen(d, diff, "diff", PAKET_DIFF_ZEILEN))
-        dateien.append(d)
-    return "\n\n".join(teile) or "(keine Code-Aenderungen gegen den Ruecksetzpunkt)", dateien
+                inhalt = _kappen(d, diff, "diff", PAKET_DIFF_ZEILEN, nicht_genannt)
+        eintraege[d] = (inhalt, _vorrang(d, nur))
+    fremd_zeilen = [f"- `{d}` – " + (", ".join(f"`{h}` ({b})" for h, b in dc) or "ohne Commit-Angabe")
+                    + " – nicht Teil dieser Kette, nicht bewerten, nur zur Kenntnis"
+                    for d, dc in fremd]
+    return eintraege, fremd_zeilen, kette
 
 
-def _kappen(datei: str, zeilen: list[str], art: str, grenze: int) -> str:
+def _kappen(datei: str, zeilen: list[str], art: str, grenze: int, nicht_genannt: bool = False) -> str:
     was = {"neu": "neue Datei, mit Zeilennummern", "umbau": "stark umgebaut – aktuelle Datei mit Zeilennummern",
            "diff": "Diff"}[art]
     kopf = f"### {datei} ({was}, {len(zeilen)} Zeilen)"
+    if nicht_genannt:
+        kopf += "\n> **nicht in der Uebergabe genannt** – moeglicherweise ausserhalb des Auftrags"
     rest = ""
     if len(zeilen) > grenze:
         rest = (f"\n[... {len(zeilen) - grenze} weitere Zeilen gekuerzt – bei Bedarf gezielt "
@@ -677,40 +722,87 @@ def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, s
     spec = spec_p.read_text(encoding="utf-8")
     nur = _handover_dateien(ho_p.read_text(encoding="utf-8")) if ho_p else None
     try:
-        diff, dateien = _diff(commit, nur)
+        eintraege, fremd_zeilen, kette = _diff(commit, nur, kurztitel)
     except subprocess.CalledProcessError as e:
         say(f"git-Fehler: {(e.stderr.strip().splitlines() or ['?'])[0]}"); return 2
-    teile = [
-        f"# Review-Paket: {kurztitel}\n",
-        f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
-        f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in dateien) or 'keine'}.\n"
-        "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
-        "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
-        "## 1. Anforderung (verbindlich, woertlich)\n\n"
-        + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
-        f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
-        f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
-        f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
-        f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
-        f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
-        f"## 3. Code-Aenderungen gegen `{commit}`\n\n{diff}",
-        f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(ROOT / 'tests' / f'test_{kurztitel}.py')}"
-        + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if (tc := _testcode(
-            ROOT / "tests" / f"test_{kurztitel}.py",
-            _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())) else ""),
-        "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
-        + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
-            or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
-        f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
-    ]
-    text = "\n\n".join(teile).rstrip() + "\n"
+
+    def bauen(drin: dict[str, tuple[str, int]], weg: list[str]) -> str:
+        code = "\n\n".join(drin[d][0] for d in sorted(drin)) or "(keine Code-Aenderungen gegen den Ruecksetzpunkt)"
+        weg_zeilen = []
+        for d in sorted(weg):
+            grund = {2: "Testcode", 3: "Testdaten"}.get(_vorrang(d, nur), "?")
+            zusatz = " (nicht in der Uebergabe genannt)" if nur is None or d not in nur else ""
+            weg_zeilen.append(f"- `{d}` – {grund}, Paket zu gross{zusatz}")
+        teile = [
+            f"# Review-Paket: {kurztitel}\n",
+            f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
+            f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in sorted(drin)) or 'keine'}.\n"
+            "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
+            "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
+            "## 1. Anforderung (verbindlich, woertlich)\n\n"
+            + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
+            f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
+            f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
+            f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
+            f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
+            f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
+            f"## 3. Code-Aenderungen gegen `{commit}`\n\n{code}",
+        ]
+        if fremd_zeilen:
+            teile.append("## 3a. Fremde Aenderungen (nur Liste)\n\nDiese Dateien wurden nur in Commits ohne den "
+                         f"Kurztitel `{kurztitel}` geaendert. Sie gehoeren nicht zur Aufgabe – nicht bewerten.\n\n"
+                         + "\n".join(fremd_zeilen))
+        if weg_zeilen:
+            teile.append("## 3b. Weggelassen (Paket zu gross)\n\nTeil der Kette, aber wegen der Paketgroesse "
+                         "ohne Inhalt. Bei Bedarf gezielt nachlesen.\n\n" + "\n".join(weg_zeilen))
+        skript = ROOT / "tests" / f"test_{kurztitel}.py"
+        tc = _testcode(skript, _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())
+        teile += [
+            f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(skript)}"
+            + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if tc else ""),
+            "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
+            + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
+                or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
+            f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
+        ]
+        return "\n\n".join(teile).rstrip() + "\n"
+
+    # A7: Aenderungen ausserhalb docs/, aber nichts davon gehoert zur Kette -> lauter Fehler
+    if not eintraege and fremd_zeilen:
+        say(f"Paket ohne Code trotz Aenderungen seit {commit}: {len(fremd_zeilen)} Datei(en), davon "
+            f"{len(fremd_zeilen)} fremd. Commits ohne Kurztitel '{kurztitel}' in der Nachricht? "
+            "Dann Ruecksetzpunkt/Kurztitel pruefen. Exit 1, kein Paket.")
+        return 1
+
+    # A3: nach Gesamtgroesse kuerzen – erst Vorrang 3, dann 2; Vorrang 1 nie
+    drin, weg = dict(eintraege), []
+    text = bauen(drin, weg)
+    for stufe in (3, 2):
+        if len(text) <= PAKET_WARNUNG_ZEICHEN:
+            break
+        for d in sorted(x for x, (_, v) in drin.items() if v == stufe):
+            weg.append(d); del drin[d]
+            text = bauen(drin, weg)
+            if len(text) <= PAKET_WARNUNG_ZEICHEN:
+                break
+
+    # A7 (Fall b): Kette-Dateien vorhanden, aber nach der Kuerzung keine mit Inhalt
+    if eintraege and not drin:
+        say("Paket ohne Code trotz Aenderungen: alle Dateien der Kette mussten weggelassen werden. Exit 1, kein Paket.")
+        return 1
+
+    groesse = len(text)
+    # A4: harte Obergrenze vor dem Schreiben
+    if groesse > KETTE_PAKET_MAX:
+        say(f"Paket passt nicht in den Kontext des Review-Modells, Review in Teilen noetig "
+            f"({groesse} Zeichen > KETTE_PAKET_MAX {KETTE_PAKET_MAX}). Exit 1, kein Paket.")
+        return 1
     ziel = PM / f"review_paket_{datum}_{kurztitel}.md"
     ziel.write_text(text, encoding="utf-8")
-    groesse = len(text)
-    say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)")
+    say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)"
+        + (f", {len(weg)} Datei(en) weggelassen" if weg else "") + (f", {len(fremd_zeilen)} fremd" if fremd_zeilen else ""))
     if groesse > PAKET_WARNUNG_ZEICHEN:
-        say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen – fuer 64K Kontext eng. "
-            "Review dann eher in Teilen (z. B. erst Anforderungen A1–A3).")
+        say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen (nur noch Vorrang 1) – fuer 64K Kontext eng.")
     if not pr_p:
         say("Hinweis: keine pruefung_*-Datei – erst `kette.py pruefen <kurztitel>` laufen lassen.")
     return 0
@@ -1102,6 +1194,11 @@ def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None,
 KETTE_LLM_URL = os.environ.get("KETTE_LLM_URL", "http://127.0.0.1:8080")
 KETTE_LLM_MODEL = os.environ.get("KETTE_LLM_MODEL", "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL")
 KETTE_LLM_TIMEOUT = int(os.environ.get("KETTE_LLM_TIMEOUT", "1800"))
+KETTE_LLM_MAX_TOKENS = int(os.environ.get("KETTE_LLM_MAX_TOKENS", "8000"))
+# Leer = Sampling-Werte des Servers (config/models.ini, fuer Qwen 0.6/0.95/20). Frueher fest 0.1:
+# niedrige Temperatur ohne Denkphase fuehrte beim 35B zu Wiederholungsschleifen bis max_tokens.
+KETTE_LLM_TEMPERATURE = os.environ.get("KETTE_LLM_TEMPERATURE", "")
+KETTE_ABGESCHNITTEN = Path(os.environ.get("KETTE_ABGESCHNITTEN", "/tmp"))
 KETTE_HERZSCHLAG_S = int(os.environ.get("KETTE_HERZSCHLAG_S", "60"))
 
 
@@ -1144,12 +1241,15 @@ def _api_ruf(prompt_text: str, lauf_nummer: int) -> tuple[str | None, dict]:
     if hostname not in ("127.0.0.1", "localhost"):
         print(f"Nur 127.0.0.1 erlaubt, Host '{hostname}' abgelehnt."); return None, {}
 
-    body = json.dumps({
+    nutzlast = {
         "model": KETTE_LLM_MODEL,
         "messages": [{"role": "user", "content": prompt_text}],
-        "temperature": 0.1,
+        "max_tokens": KETTE_LLM_MAX_TOKENS,
         "chat_template_kwargs": {"enable_thinking": False},
-    }).encode("utf-8")
+    }
+    if KETTE_LLM_TEMPERATURE:
+        nutzlast["temperature"] = float(KETTE_LLM_TEMPERATURE)
+    body = json.dumps(nutzlast).encode("utf-8")
     req = urllib.request.Request(url + "/v1/chat/completions", data=body,
                                  headers={"Content-Type": "application/json"})
     try:
@@ -1176,7 +1276,15 @@ def _api_ruf(prompt_text: str, lauf_nummer: int) -> tuple[str | None, dict]:
         print("leere Modellantwort"); return None, {}
     finish = (choices[0].get("finish_reason") or "")
     if finish == "length":
-        print("Antwort abgeschnitten (finish_reason=length)"); return None, {}
+        n = (data.get("usage") or {}).get("completion_tokens")
+        ziel = KETTE_ABGESCHNITTEN / f"kette_abgeschnitten_lauf{lauf_nummer}.md"
+        try:
+            ziel.write_text(content, encoding="utf-8")
+        except OSError:
+            ziel = None
+        print(f"Antwort abgeschnitten (finish_reason=length) nach {n} Token "
+              f"(KETTE_LLM_MAX_TOKENS={KETTE_LLM_MAX_TOKENS}). Text: {ziel} – "
+              f"auf Wiederholungsschleife pruefen, bevor das Limit erhoeht wird."); return None, {}
 
     usage = (data.get("usage") or {})
     return content, {"prompt_tokens": usage.get("prompt_tokens"),
```

### role-split/kette/prompts/review2_api.md (Diff, 16 Zeilen)
> **nicht in der Uebergabe genannt** – moeglicherweise ausserhalb des Auftrags

```diff
diff --git a/role-split/kette/prompts/review2_api.md b/role-split/kette/prompts/review2_api.md
index 6c86ad9..80151a4 100644
--- a/role-split/kette/prompts/review2_api.md
+++ b/role-split/kette/prompts/review2_api.md
@@ -46,6 +46,11 @@ ob die Schaechte schon vorher bestand. `kette.py urteil` prueft das nach.
 - **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Haenger, Schweigen, falscher Exit-Code, Test misst nichts)?
 - **Harte Vorgabe:** Verstoesst es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?
 
+In diese Tabelle gehoeren **nur echte Maengel**. Was du nachgeprueft und fuer korrekt befunden hast
+(„kein Befund", „korrekt umgesetzt", „ist gewollt"), gehoert in die Anforderungstabelle oder unter
+„Handover gegen Code" – nicht hierher, auch nicht als Zeile mit „nein". Gibt es keinen Mangel, schreibe
+genau diese eine Zeile: `| – | nein | nein | nein | – | – | keine Befunde | – |`
+
 | # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
 |---|---|---|---|---|---|---|---|
 | 1 | ja / nein | ja / nein | ja / nein | hoch / mittel / niedrig | | | |
```

### role-split/kette/prompts/review_api.md (Diff, 16 Zeilen)
> **nicht in der Uebergabe genannt** – moeglicherweise ausserhalb des Auftrags

```diff
diff --git a/role-split/kette/prompts/review_api.md b/role-split/kette/prompts/review_api.md
index 438385e..2b893d1 100644
--- a/role-split/kette/prompts/review_api.md
+++ b/role-split/kette/prompts/review_api.md
@@ -52,6 +52,11 @@ ob die Schaechte schon vorher bestand. `kette.py urteil` prueft das nach.
 - **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Haenger, Schweigen, falscher Exit-Code, Test misst nichts)?
 - **Harte Vorgabe:** Verstoesst es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?
 
+In diese Tabelle gehoeren **nur echte Maengel**. Was du nachgeprueft und fuer korrekt befunden hast
+(„kein Befund", „korrekt umgesetzt", „ist gewollt"), gehoert in die Anforderungstabelle oder unter
+„Handover gegen Code" – nicht hierher, auch nicht als Zeile mit „nein". Gibt es keinen Mangel, schreibe
+genau diese eine Zeile: `| – | nein | nein | nein | – | – | keine Befunde | – |`
+
 | # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
 |---|---|---|---|---|---|---|---|
 | 1 | ja / nein | ja / nein | ja / nein | hoch / mittel / niedrig | | | |
```

### role-split/kette/test_kette.py (Diff, 41 Zeilen)

```diff
diff --git a/role-split/kette/test_kette.py b/role-split/kette/test_kette.py
index 614f98d..a8aaf00 100644
--- a/role-split/kette/test_kette.py
+++ b/role-split/kette/test_kette.py
@@ -252,18 +252,31 @@ class PruefenTests(unittest.TestCase):
             self.assertNotIn(nicht, text, nicht)
         self.assertIn("Zeichen, ca.", out)
 
-    def test_paket_nur_dateien_aus_handover_und_nie_werkzeug(self):
+    def test_paket_alle_kette_dateien_mit_markierung_und_fremde_liste(self):
+        """K9: alle zur Kette gehoerigen Dateien (auch role-split/, unversioniert) mit Inhalt;
+        nicht in der Uebergabe genannte markiert; Dateien nur aus fremden Commits nur als Liste."""
         self._paket_vorbereiten()
         (self.root / "role-split").mkdir()
-        (self.root / "role-split" / "werkzeug.py").write_text("W = 1\n")
+        (self.root / "role-split" / "werkzeug.py").write_text("W = 1\n")      # unversioniert -> Kette
+        (self.root / "fremd.py").write_text("F = 1\n")
+        self.git("add", "fremd.py"); self.git("commit", "-qm", "Werkzeug: anderes")   # ohne Kurztitel -> fremd
         ho = kette.PM / "handover_20261022_g.md"
         ho.write_text(ho.read_text(encoding="utf-8") + "\n## Geänderte und neue Dateien\n- `neu_modul.py` – neu\n",
                       encoding="utf-8")
         lauf(kette.paket, "g")
         text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
-        self.assertIn("### neu_modul.py", text)
-        self.assertNotIn("### mod.py", text)
-        self.assertNotIn("werkzeug.py", text.split("## 3.")[1].split("## 4.")[0])
+        code_teil = text.split("## 3. ")[1].split("## 3a.")[0]
+        self.assertIn("### neu_modul.py", code_teil)
+        self.assertIn("### mod.py", code_teil)                       # Commit "Spec g" -> Kette
+        self.assertIn("### role-split/werkzeug.py", code_teil)
+        ng = code_teil.split("### ")
+        markiert = {b.split(" ")[0] for b in ng if "nicht in der Uebergabe genannt" in b}
+        self.assertNotIn("neu_modul.py", markiert)
+        self.assertIn("mod.py", markiert)
+        self.assertIn("role-split/werkzeug.py", markiert)
+        self.assertNotIn("F = 1", text)                              # fremd: kein Inhalt
+        self.assertIn("`fremd.py`", text.split("## 3a.")[1].split("## 4.")[0])
+        self.assertIn("Werkzeug: anderes", text)
 
     def test_paket_kleine_aenderung_als_diff(self):
         self._paket_vorbereiten()
```

### tests/test_kette_review_auto.py (Diff, 69 Zeilen)

```diff
diff --git a/tests/test_kette_review_auto.py b/tests/test_kette_review_auto.py
index b11b5d3..0f5d4ed 100644
--- a/tests/test_kette_review_auto.py
+++ b/tests/test_kette_review_auto.py
@@ -28,11 +28,13 @@ class _MiniServer(http.server.BaseHTTPRequestHandler):
 
     antworten = []          # Liste von dicts, pro Request wird das nächste genommen
     anzahl_rufe = 0
+    koerper = []            # empfangene Request-Bodies (fuer K-Test max_tokens)
 
     def do_POST(self):
         _MiniServer.anzahl_rufe += 1
         length = int(self.headers.get("Content-Length", 0))
         body = json.loads(self.rfile.read(length))
+        _MiniServer.koerper.append(body)
         # Antwort zusammenbauen
         idx = (_MiniServer.anzahl_rufe - 1) % max(len(_MiniServer.antworten), 1)
         resp = _MiniServer.antworten[idx]
@@ -79,6 +81,8 @@ class ReviewAutoTests(unittest.TestCase):
         self.tmp = tempfile.TemporaryDirectory()
         self.addCleanup(self.tmp.cleanup)
         kette.PM = Path(self.tmp.name)
+        self.addCleanup(setattr, kette, "KETTE_ABGESCHNITTEN", kette.KETTE_ABGESCHNITTEN)
+        kette.KETTE_ABGESCHNITTEN = Path(self.tmp.name)
         self._orig_url = os.environ.get("KETTE_LLM_URL")
         self._orig_model = os.environ.get("KETTE_LLM_MODEL")
         self._orig_timeout = os.environ.get("KETTE_LLM_TIMEOUT")
@@ -88,6 +92,7 @@ class ReviewAutoTests(unittest.TestCase):
         os.environ["KETTE_HERZSCHLAG_S"] = "1"
         _MiniServer.antworten = []
         _MiniServer.anzahl_rufe = 0
+        _MiniServer.koerper = []
 
     def tearDown(self):
         if self._orig_url is not None:
@@ -142,6 +147,33 @@ class ReviewAutoTests(unittest.TestCase):
         gesamt = list(kette.PM.glob("gesamt_*.md"))
         self.assertTrue(bool(gesamt))
 
+    # --- K3 (K9): max_tokens wird im API-Aufruf mitgeschickt ---
+
+    def test_k3_max_tokens_im_api_aufruf(self):
+        port = _freier_port()
+        url = f"http://127.0.0.1:{port}"
+        os.environ["KETTE_LLM_URL"] = url
+        kette.KETTE_LLM_URL = url
+        _MiniServer.antworten = [
+            {"choices": [{"message": {"content": KOPF.format(u="PASS", anf="| A1 | x | erfüllt | x |", bef="| 1 | nein | nein | ja | niedrig | x.py:1 | x | y |")}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}},
+        ]
+        _server_thread(port)
+        orig_teile = kette._pruefen_teile
+        kette._pruefen_teile = lambda *a, **kw: {"unittest": (0, ""), "abgleich": (0, ""), "gegenprobe": (0, "")}
+        self.addCleanup(setattr, kette, "_pruefen_teile", orig_teile)
+        orig_paket = kette.paket
+        kette.paket = lambda *a: 0
+        self.addCleanup(setattr, kette, "paket", orig_paket)
+        orig_max = kette.KETTE_LLM_MAX_TOKENS
+        kette.KETTE_LLM_MAX_TOKENS = 1234
+        self.addCleanup(setattr, kette, "KETTE_LLM_MAX_TOKENS", orig_max)
+        with redirect_stdout(io.StringIO()):
+            kette.review_auto("test1")
+        self.assertTrue(_MiniServer.koerper)
+        for body in _MiniServer.koerper:
+            self.assertEqual(body.get("max_tokens"), 1234)
+            self.assertNotIn("temperature", body)       # Server-Sampling gilt (models.ini)
+
     # --- T2: Router nicht erreichbar ---
 
     def test_t2_router_nicht_erreichbar(self):
```

### tests/test_paket_vollstaendig.py (stark umgebaut – aktuelle Datei mit Zeilennummern, 228 Zeilen)

```
   1  #!/usr/bin/env python3
   2  """Tests fuer Spec paket_vollstaendig (K9), Testplan T1–T9 plus Zusatztests K1–K2.
   3  
   4  Jeder Test baut ein Wegwerf-Git-Repo und prueft Verhalten (Paketinhalt, Exit-Code, Gegenprobe),
   5  nicht den Quelltext. Laeuft ab Python 3.10. Geschrieben von Claude (Uebernahme NB2, 26.10.).
   6  """
   7  import io
   8  import subprocess
   9  import sys
  10  import tempfile
  11  import unittest
  12  from contextlib import redirect_stdout
  13  from pathlib import Path
  14  
  15  PROJ = Path(__file__).resolve().parent.parent
  16  sys.path.insert(0, str(PROJ / "role-split" / "kette"))
  17  import kette  # noqa: E402
  18  
  19  
  20  def lauf(fn, *a, **kw):
  21      buf = io.StringIO()
  22      with redirect_stdout(buf):
  23          code = fn(*a, **kw)
  24      return code, buf.getvalue()
  25  
  26  
  27  class Basis(unittest.TestCase):
  28      """Repo mit Spec-Datei und Commit 'Spec g' als Ruecksetzpunkt."""
  29  
  30      def setUp(self):
  31          d = tempfile.TemporaryDirectory()
  32          self.addCleanup(d.cleanup)
  33          self.root = Path(d.name)
  34          self.git("init", "-q")
  35          self.pm = self.root / "docs" / "projekt_management"
  36          self.pm.mkdir(parents=True)
  37          (self.pm / "spec_20261026_g.md").write_text(
  38              "# Spec\n\n## Ziel\nZ\n\n## Nicht-Ziele\nN\n\n## Anforderungen\n### A1: Eins\nX\n\n"
  39              "## Testplan\n### T1: Erster\n- **Erwartung:** E\n\n## Offene Fragen\nO\n", encoding="utf-8")
  40          self.schreibe("mod.py", "def f():\n    return 1\n")
  41          self.git("add", "-A")
  42          self.git("commit", "-qm", "Spec g")
  43          self.spec_commit = self.git("rev-parse", "--short", "HEAD").strip()
  44          for name, wert in (("ROOT", self.root), ("PM", self.pm)):
  45              alt = getattr(kette, name)
  46              setattr(kette, name, wert)
  47              self.addCleanup(setattr, kette, name, alt)
  48  
  49      def git(self, *a):
  50          return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
  51                                check=True, capture_output=True, text=True).stdout
  52  
  53      def schreibe(self, rel, inhalt):
  54          p = self.root / rel
  55          p.parent.mkdir(parents=True, exist_ok=True)
  56          p.write_text(inhalt, encoding="utf-8")
  57  
  58      def commit(self, nachricht, **dateien):
  59          for rel, inhalt in dateien.items():
  60              self.schreibe(rel.replace("__", "/"), inhalt)
  61          self.git("add", "-A")
  62          self.git("commit", "-qm", nachricht)
  63  
  64      def handover(self, *dateien):
  65          zeilen = "".join(f"- `{d}` – x\n" for d in dateien)
  66          (self.pm / "handover_20261026_g.md").write_text(
  67              f"# HO\n## Geänderte und neue Dateien\n{zeilen}\n## Abweichungen\nkeine\n", encoding="utf-8")
  68  
  69      def paket(self, **kw):
  70          code, out = lauf(kette.paket, "g", **kw)
  71          ziel = self.pm / "review_paket_20261026_g.md"
  72          text = ziel.read_text(encoding="utf-8") if ziel.exists() else None
  73          return code, out, text
  74  
  75      @staticmethod
  76      def code_teil(text):
  77          rest = text.split("## 3. Code-Aenderungen")[1]
  78          for ende in ("## 3a.", "## 3b.", "## 4."):
  79              if ende in rest:
  80                  rest = rest.split(ende)[0]
  81          return rest
  82  
  83      @staticmethod
  84      def markiert(code_teil):
  85          return {b.split(" ")[0] for b in code_teil.split("### ")[1:] if "nicht in der Uebergabe genannt" in b}
  86  
  87  
  88  class TestPaketVollstaendig(Basis):
  89  
  90      def test_t1_fehlerpfade_von_paket(self):
  91          """T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)"""
  92          code, out = lauf(kette.paket, "G-1")
  93          self.assertEqual(code, 2); self.assertIn("ungueltig", out)
  94          code, out = lauf(kette.paket, "nichtda")
  95          self.assertEqual(code, 2); self.assertIn("Keine Spec", out)
  96          (self.pm / "spec_20261026_ohne.md").write_text("# Spec\n", encoding="utf-8")
  97          code, out = lauf(kette.paket, "ohne")
  98          self.assertEqual(code, 2); self.assertIn("Kein Commit 'Spec ohne'", out)
  99          code, out = lauf(kette.paket, "g", commit="deadbeefdeadbeef")
 100          self.assertEqual(code, 2); self.assertIn("git-Fehler", out)
 101          self.assertEqual(list(self.pm.glob("review_paket_*")), [])
 102  
 103      def test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte(self):
 104          """T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte"""
 105          self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
 106          self.schreibe("tests/test_g.py", "import unittest\n")                       # unversioniert
 107          self.schreibe("tests/daten/x.json", '{"a": 1}\n')                            # unversioniert
 108          self.schreibe("role-split/kette/hilfs.py", "H = 1\n")
 109          self.git("add", "role-split/kette/hilfs.py")                                 # nur vorgemerkt
 110          self.schreibe("role-split/rollen/r.md", "# Rolle R\n")                       # .md unter role-split
 111          self.handover("mod.py")
 112          code, out, text = self.paket()
 113          self.assertEqual(code, 0, out)
 114          teil = self.code_teil(text)
 115          for d in ("mod.py", "tests/test_g.py", "tests/daten/x.json", "role-split/kette/hilfs.py",
 116                    "role-split/rollen/r.md"):
 117              self.assertIn(f"### {d} ", teil, d)
 118          self.assertEqual(self.markiert(teil), {"tests/test_g.py", "tests/daten/x.json",
 119                                                 "role-split/kette/hilfs.py", "role-split/rollen/r.md"})
 120  
 121      def test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung(self):
 122          """T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung"""
 123          self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
 124          self.schreibe("tests/test_g.py", "import unittest\n")
 125          self.schreibe("role-split/kette/hilfs.py", "H = 1\n")
 126          self.handover("mod.py", "tests/test_g.py")
 127          code, out, text = self.paket()
 128          self.assertEqual(code, 0, out)
 129          self.assertEqual(self.markiert(self.code_teil(text)), {"role-split/kette/hilfs.py"})
 130  
 131      def test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen(self):
 132          """T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen"""
 133          self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
 134          self.schreibe("tests/test_g.py", "import unittest\n")
 135          zeile = "Testzeile mit Inhalt fuer eine grosse Datei\n"
 136          self.schreibe("tests/daten/gross.eml", zeile * 2500)          # ~110 000 Zeichen, Vorrang 3
 137          alt = kette.PAKET_DATEI_ZEILEN
 138          kette.PAKET_DATEI_ZEILEN = 5000
 139          self.addCleanup(setattr, kette, "PAKET_DATEI_ZEILEN", alt)
 140          self.handover("mod.py")
 141          code, out, text = self.paket()
 142          self.assertEqual(code, 0, out)
 143          teil = self.code_teil(text)
 144          self.assertIn("### mod.py ", teil)
 145          self.assertIn("### tests/test_g.py ", teil)                    # Vorrang 2 bleibt, reicht schon
 146          self.assertNotIn("gross.eml", teil)
 147          weg = text.split("## 3b.")[1].split("## 4.")[0]
 148          self.assertIn("`tests/daten/gross.eml` – Testdaten", weg)
 149          self.assertLessEqual(len(text), kette.PAKET_WARNUNG_ZEICHEN)
 150  
 151      def test_t5_kette_paket_max_ueberschritten_exit_1(self):
 152          """T5: KETTE_PAKET_MAX überschritten → Exit 1"""
 153          self.commit("g: mod", **{"mod.py": "".join(f"def f{i}():\n    return {i}\n" for i in range(300))})
 154          self.handover("mod.py")
 155          alt = kette.KETTE_PAKET_MAX
 156          kette.KETTE_PAKET_MAX = 3000
 157          self.addCleanup(setattr, kette, "KETTE_PAKET_MAX", alt)
 158          code, out, text = self.paket()
 159          self.assertEqual(code, 1, out)
 160          self.assertIn("passt nicht in den Kontext", out)
 161          self.assertIsNone(text)
 162  
 163      def test_t6_gegenprobe_beruecksichtigt_role_split_kette(self):
 164          """T6: Gegenprobe berücksichtigt role-split/kette/"""
 165          self.commit("Werkzeug: fremd", **{"fremd.py": "F = 5\n"})
 166          self.commit("g: hilfs", **{"role-split__kette__hilfs.py": "H = 7\n"})
 167          self.schreibe("tests/test_g.py",
 168                        "import sys, unittest\nfrom pathlib import Path\n"
 169                        "R = Path(__file__).resolve().parent.parent\n"
 170                        "sys.path.insert(0, str(R / 'role-split' / 'kette')); sys.path.insert(0, str(R))\n"
 171                        "class T(unittest.TestCase):\n"
 172                        "    def test_t1_hilfs(self):\n        import hilfs\n        self.assertEqual(hilfs.H, 7)\n"
 173                        "    def test_t2_fremd(self):\n        import fremd\n        self.assertEqual(fremd.F, 5)\n")
 174          code, out = lauf(kette.gegenprobe, "g", self.spec_commit)
 175          self.assertIn("rot   test_t1_hilfs  <- hilfs.py", out)
 176          self.assertIn("GRUEN test_t2_fremd", out)                     # fremde Datei nicht zurueckgesetzt
 177          self.assertNotIn("fremd.py:", out)
 178          self.assertEqual((self.root / "role-split/kette/hilfs.py").read_text(), "H = 7\n")
 179  
 180      def test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen(self):
 181          """T7: Bestehende Tests in test_kette.py bleiben grün"""
 182          r = subprocess.run([sys.executable, str(PROJ / "role-split" / "kette" / "test_kette.py")],
 183                             capture_output=True, text=True, timeout=300)
 184          self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
 185  
 186      def test_t8_fremde_commits_nur_als_liste(self):
 187          """T8: Fremde Commits nur als Liste"""
 188          self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
 189          self.commit("Werkzeug: x", **{"werkzeug.py": "GEHEIMER_INHALT = 1\n", "anderes.py": "A = 1\n"})
 190          self.handover("mod.py", "anderes.py")
 191          code, out, text = self.paket()
 192          self.assertEqual(code, 0, out)
 193          teil = self.code_teil(text)
 194          self.assertIn("### mod.py ", teil)
 195          self.assertIn("### anderes.py ", teil)                          # fremd, aber in der Uebergabe
 196          self.assertNotIn("GEHEIMER_INHALT", text)
 197          fremd = text.split("## 3a.")[1].split("## 4.")[0]
 198          self.assertIn("`werkzeug.py`", fremd)
 199          self.assertIn("Werkzeug: x", fremd)
 200          self.assertNotIn("anderes.py", fremd)
 201  
 202      def test_t9_paket_ohne_code_trotz_aenderungen_exit_1(self):
 203          """T9: Paket ohne Code trotz Änderungen → Exit 1"""
 204          self.commit("Werkzeug: x", **{"mod.py": "def f():\n    return 9\n"})
 205          code, out, text = self.paket()
 206          self.assertEqual(code, 1, out)
 207          self.assertIn("Paket ohne Code trotz Aenderungen", out)
 208          self.assertIsNone(text)
 209  
 210      def test_k1_nur_docs_geaendert_exit_0(self):
 211          """K1: Nur docs/ geaendert -> Exit 0, 'keine Code-Dateien'"""
 212          self.commit("g: doku", **{"docs__notiz.md": "x\n"})
 213          code, out, text = self.paket()
 214          self.assertEqual(code, 0, out)
 215          self.assertIn("Geaenderte Code-Dateien: keine", text)
 216  
 217      def test_k2_kurztitel_als_ganzes_wort(self):
 218          """K2: Kurztitel 'g' trifft nicht 'gross' -> Datei aus 'gross init' ist fremd"""
 219          self.commit("gross init", **{"gross.py": "G = 1\n"})
 220          self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
 221          code, out, text = self.paket()
 222          self.assertEqual(code, 0, out)
 223          self.assertIn("`gross.py`", text.split("## 3a.")[1].split("## 4.")[0])
 224          self.assertNotIn("### gross.py", self.code_teil(text))
 225  
 226  
 227  if __name__ == "__main__":
 228      unittest.main()
```

## 4. Testskript `tests/test_paket_vollstaendig.py` (Methoden)

- `test_t1_fehlerpfade_von_paket` (Zeile 90): T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)
- `test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte` (Zeile 103): T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte
- `test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung` (Zeile 121): T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung
- `test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen` (Zeile 131): T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen
- `test_t5_kette_paket_max_ueberschritten_exit_1` (Zeile 151): T5: KETTE_PAKET_MAX überschritten → Exit 1
- `test_t6_gegenprobe_beruecksichtigt_role_split_kette` (Zeile 163): T6: Gegenprobe berücksichtigt role-split/kette/
- `test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen` (Zeile 180): T7: Bestehende Tests in test_kette.py bleiben grün
- `test_t8_fremde_commits_nur_als_liste` (Zeile 186): T8: Fremde Commits nur als Liste
- `test_t9_paket_ohne_code_trotz_aenderungen_exit_1` (Zeile 202): T9: Paket ohne Code trotz Änderungen → Exit 1
- `test_k1_nur_docs_geaendert_exit_0` (Zeile 210): K1: Nur docs/ geaendert -> Exit 0, 'keine Code-Dateien'
- `test_k2_kurztitel_als_ganzes_wort` (Zeile 217): K2: Kurztitel 'g' trifft nicht 'gross' -> Datei aus 'gross init' ist fremd

### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)

#### test_t1_fehlerpfade_von_paket

```
  90      def test_t1_fehlerpfade_von_paket(self):
  91          """T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)"""
  92          code, out = lauf(kette.paket, "G-1")
  93          self.assertEqual(code, 2); self.assertIn("ungueltig", out)
  94          code, out = lauf(kette.paket, "nichtda")
  95          self.assertEqual(code, 2); self.assertIn("Keine Spec", out)
  96          (self.pm / "spec_20261026_ohne.md").write_text("# Spec\n", encoding="utf-8")
  97          code, out = lauf(kette.paket, "ohne")
  98          self.assertEqual(code, 2); self.assertIn("Kein Commit 'Spec ohne'", out)
  99          code, out = lauf(kette.paket, "g", commit="deadbeefdeadbeef")
 100          self.assertEqual(code, 2); self.assertIn("git-Fehler", out)
 101          self.assertEqual(list(self.pm.glob("review_paket_*")), [])
```

#### test_k1_nur_docs_geaendert_exit_0

```
 210      def test_k1_nur_docs_geaendert_exit_0(self):
 211          """K1: Nur docs/ geaendert -> Exit 0, 'keine Code-Dateien'"""
 212          self.commit("g: doku", **{"docs__notiz.md": "x\n"})
 213          code, out, text = self.paket()
 214          self.assertEqual(code, 0, out)
 215          self.assertIn("Geaenderte Code-Dateien: keine", text)
```

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- **Nicht committete/unversionierte Dateien zählen immer zur Kette** (Spec A1). Folge: Wer ein Paket für eine *alte* Kette baut, während andere Arbeit uncommittet herumliegt, bekommt diese Arbeit mit ins Paket. Probe: `paket mail_server_test` mit uncommittetem K9-Stand → 175 161 Zeichen → Exit 1. **Vor T10 also K9 committen.**
- Keine Code-Änderung überhaupt (nur docs/) → Exit 0 mit „Geaenderte Code-Dateien: keine" (wie bisher), nicht Exit 1.

## Annahmen

- Vorrang 1 = in der Übergabe genannt **oder** außerhalb `tests/`; Vorrang 2 = `.py/.sh/.command` unter `tests/`; Vorrang 3 = übrige Testdaten.
- Die Übergabe-Liste kommt aus dem neuesten Handover der Kette.

## Nicht getestet

- **T10: Abnahme – echter Lauf am K7-Stand (Hawe, manuell)** – braucht Router + 35B, macht Hawe.

## Offene Punkte

- Phase G: Messwerte 27B (Erstumsetzung 2 h 45, NB1 ~4,5 h, NB2 ~4,5 h ohne Abschluss) und OpenCode-Selbstcommit `1b2e74c` in die Learnings.
- Nach K9: `experiments/k8_paket_ergaenzen.py` löschen.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: Abweichung

#### abgleich
```
Spec:     spec_20261025_paket_vollstaendig.md  (10 Tests)
Handover: handover_20261026_paket_vollstaendig.md

  ok        T1    Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)
  ok        T2    Paket enthält Dateien unter tests/ und role-split/, auch unversionierte
  ok        T3    Handover-Datei ohne Markierung, fremde Datei mit Markierung
  ok        T4    Vorrang-Kürzung – Vorrang 3 wird weggelassen
  ok        T5    KETTE_PAKET_MAX überschritten → Exit 1
  ok        T6    Gegenprobe berücksichtigt role-split/kette/
  ok        T7    Bestehende Tests in test_kette.py bleiben grün
  ok        T8    Fremde Commits nur als Liste
  ok        T9    Paket ohne Code trotz Änderungen → Exit 1
  NICHT GET T10   Abnahme – echter Lauf am K7-Stand (Hawe, manuell)  (unter 'Nicht getestet' -- Grund pruefen)

  Testskript tests/test_paket_vollstaendig.py: keine Methode test_<id> fuer T10
  Selbst ausfuehren: python3 -m unittest -v tests/test_paket_vollstaendig.py

2 Abweichung(en).
```

#### gegenprobe
```
Gegenprobe gegen 84e3bb7: 11 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 9 Test(s) rot
  role-split/kette/test_kette.py: 1 Test(s) rot

  GRUEN test_k1_nur_docs_geaendert_exit_0  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_k2_kurztitel_als_ganzes_wort  <- kette.py
  GRUEN test_t1_fehlerpfade_von_paket  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte  <- kette.py
  rot   test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung  <- kette.py
  rot   test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen  <- kette.py
  rot   test_t5_kette_paket_max_ueberschritten_exit_1  <- kette.py
  rot   test_t6_gegenprobe_beruecksichtigt_role_split_kette  <- kette.py
  rot   test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen  <- kette.py, test_kette.py
  rot   test_t8_fremde_commits_nur_als_liste  <- kette.py
  rot   test_t9_paket_ohne_code_trotz_aenderungen_exit_1  <- kette.py

9 von 11 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, dann wird die Gegenprobe je Test aussagekraeftig.
```

#### unittest (Zusammenfassung)
Ran 11 tests in 2.937s
OK
