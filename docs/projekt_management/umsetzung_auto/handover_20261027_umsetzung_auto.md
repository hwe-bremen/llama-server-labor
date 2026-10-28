# Handover: umsetzung_auto

- **Spec:** `docs/projekt_management/spec_20261027_umsetzung_auto.md`
- **Datum:** 2026-10-27
- **Modell / Werkzeug:** Claude (Opus), übernommen nach verworfenem 35B-Lauf; entwickelt und getestet in Claudes Arbeitsumgebung, eingespielt per MCP und `tmp/k10_einbau.py`
- **Rücksetzpunkt:** `3700da7` (Spec umsetzung_auto)

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1 Befehl `umsetzung-auto` | erfüllt | `kette.py`, Subparser `umsetzung-auto` mit `--nacharbeit`, `def umsetzung_auto` |
| A2 Vorab-Prüfungen (Exit 2) | erfüllt | `def umsetzung_auto` (Abschnitt A2.1–A2.6), `_schreibbereich`, `_offene_dateien`, `_opencode_programm` |
| A3 Prompt | erfüllt | `role-split/kette/prompts/umsetzung_nacht.md`, `def _umsetzung_prompt` |
| A4 deny-Regeln Agent | erfüllt | `.opencode/agents/umsetzung_nacht.md` |
| A5 Zeitlimits | erfüllt | `UMSETZUNG_TIMEOUT_STANDARD`, `UMSETZUNG_BASH_MS_STANDARD`, `def _lauf` (Kill der Prozessgruppe) |
| A6 JSON-Auswertung | erfüllt | `def _lauf` (Lesefaden, Rohdaten nach `role-split/results/umsetzung_auto_*.jsonl`) |
| A7 Mechanische Prüfung (a)–(d) | erfüllt | `def umsetzung_auto` nach dem Lauf, `_stand`, `_in_diesem_lauf`, `_im_schreibbereich`, `_ist_vorgabe` |
| A8 Nacharbeit + Halt-Regel | erfüllt | `_protokoll`, `_fortschritt`, `_halt_noetig`, `PROTOKOLL_RE` |
| A9 Lebendsignal | erfüllt | `def _lauf` (Werkzeugzeilen + Herzschlag-Faden) |
| A10 Exit-Codes | erfüllt | `def umsetzung_auto` |
| A11 Ergänzungen (Vorlage, RUNBOOK) | erfüllt | `_vorlage_spec.md` (`## Schreibbereich`), `RUNBOOK.md` |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert – Block „umsetzung-auto (K10)“ vor `# ---- main`, Subparser, Dispatch, Docstring-Zeile, `import signal`; rund 460 Zeilen neu (437 + Nachbesserung 1), keine bestehende Funktion gelöscht.
- `role-split/kette/prompts/umsetzung_nacht.md` – neu – Prompt für den Lauf ohne TUI.
- `.opencode/agents/umsetzung_nacht.md` – geändert – deny für `git commit/reset/checkout/restore/clean/stash/push`, `rm`, `mv`; Vorrang-Absatz gegenüber globalem `AGENTS.md`.
- `role-split/kette/testdata/opencode_fake.py` – neu – Attrappe für `opencode run --format json` mit Temp-Ordner-Sperre (Exit 3 außerhalb).
- `tests/test_umsetzung_auto.py` – neu – 33 Testmethoden (23 + 10 aus Nachbesserung 1).
- `docs/projekt_management/_vorlage_spec.md` – geändert – Abschnitt `## Schreibbereich` vor „Außenwirkung und Sperre“.
- `role-split/kette/RUNBOOK.md` – geändert – Unterabschnitt „Phase B automatisch: `umsetzung-auto` (ab K10)“, Spickzettel-Zeile.

## Abweichungen von der Spec

- Prompt enthält zusätzlich eine Leseregel (erst suchen, dann Zeilenbereiche lesen, große Dateien nur gezielt editieren). Anlass: Der 35B-Lauf hat `kette.py` ganz gelesen und den Kontext erschöpft.
- Leerer Abschnitt `## Schreibbereich` (Überschrift ohne Einträge) gilt wie fehlend → Exit 2.
- `FAKE_UNITTEST` der Attrappe nicht gebaut: „rot“ kommt aus der `pruefung_*.md`, die `pruefen` schreibt; im Test wird `kette.pruefen` durch einen Stub ersetzt, der diese Datei schreibt.
- T14 und T20 haben je eine zusätzliche Methode (`test_t14_gegenfall_fortschritt_hebt_halt_auf`, `test_t20_attrappe_sperrt_echtes_repo`), damit die Halt-Regel nicht immer greift bzw. die Attrappen-Sperre selbst geprüft ist.
- T13 prüft zusätzlich zur Spec-Erwartung (neuer Abschnitt `## Nachbesserung 1`), dass der Auftrag im Prompt steht (über `FAKE_ARGS`). Seit Nachbesserung 1 prüft auch `kette.py` selbst in (c), ob der Abschnitt `## Nachbesserung n` im Handover steht (Exit 1, wenn nicht) – das ist strenger als die Spec.
- Signatur `umsetzung_auto(kurztitel, nacharbeit=None)` statt `(kurztitel, nacharbeit=None, datums=None, commit=None)` aus der Spec: Datum kommt aus dem Dateinamen der Spec, Commit aus `spec_commit`; beides ist nicht von außen setzbar.
- `opencode run` bekommt zusätzlich `--title`, damit Läufe in OpenCode wiederzufinden sind.
- Startfehler (Programm lässt sich nicht starten) werden abgefangen und als Befund gemeldet statt als Traceback.
- Nennt der Schreibbereich eine Vorgabe (z. B. `_vorlage_spec.md`), gibt es schon vor dem Start einen Hinweis auf stderr; der Lauf startet trotzdem und endet bei einer Änderung daran in (b) mit Exit 1 (seit Nachbesserung 1).
- Wortlaut fehlgeschlagener/abgelehnter Befehle und die Token-Aufteilung (input/output/reasoning) stehen als eingerückte Unterzeilen unter der Protokollzeile, damit das Zeilenformat aus A6 unverändert bleibt (seit Nachbesserung 1).

## Annahmen

- `step_finish` mit `reason: stop` als letztes Ereignis bedeutet „Modell hat selbst beendet“ (aus Probe P1/P2, `claude/k10-opencode-probe.md`).
- Die Attrappe gibt das Ereignisformat von opencode 1.19.3 wieder, so wie es die Proben gezeigt haben; Abweichungen späterer Versionen sind nicht abgedeckt.

## Getestet (mit echter Ausgabe)

**T1: Vorab-Prüfung – Kurztitel ungültig** – bestanden
**T2: Vorab-Prüfung – kein Spec-Commit** – bestanden
**T3: Vorab-Prüfung – Spec ohne `## Schreibbereich`** – bestanden
**T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)** – bestanden
**T5: Vorab-Prüfung – `opencode` fehlt** – bestanden
**T6: Vorab-Prüfung – Modell kein `llamacpp/`** – bestanden
**T7: Erfolgreicher Lauf, `reason: stop`, alle Prüfungen grün** – bestanden
**T8: Lauf ohne `reason: stop`** – bestanden
**T9: Timeout** – bestanden
**T10: Selbst-Commit** – bestanden
**T11: Datei außerhalb Schreibbereich** – bestanden
**T12: Handover fehlt** – bestanden
**T13: Nacharbeit – Auftrag aus Datei** – bestanden
**T14: Nacharbeit – zwei ohne Fortschritt** – bestanden
**T15: Lebendsignal – Werkzeugzeile** – bestanden
**T16: `pruefen` rot** – bestanden
**T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen** – bestanden
**T18: Schreibbereich – Ordner-Eintrag** – bestanden
**T19: Schreibbereich – Verbotene Dateien** – bestanden
**T20: main() – gleicher Exit wie Funktionsaufruf** – bestanden
**T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)** – bestanden

Ausgabe aus Hawes Lauf am Mac nach Nachbesserung 1 (32 Methoden; mehrere je Test-ID, Zusatztitel in Klammern):

```
$ python3 -m unittest -v tests/test_umsetzung_auto.py
test_t20_attrappe_sperrt_echtes_repo (tests.test_umsetzung_auto.EinstiegTests.test_t20_attrappe_sperrt_echtes_repo)
T20 Absicherung (kein main()-Aufruf): Attrappe sperrt das echte Repo und Ziele außerhalb von Temp ... ok
test_t20_main_gleicher_exit_wie_funktionsaufruf (tests.test_umsetzung_auto.EinstiegTests.test_t20_main_gleicher_exit_wie_funktionsaufruf)
T20: main() – gleicher Exit wie Funktionsaufruf ... ok
test_t10_selbst_commit (tests.test_umsetzung_auto.LaufTests.test_t10_selbst_commit)
T10: Selbst-Commit ... ok
test_t11_datei_ausserhalb_schreibbereich (tests.test_umsetzung_auto.LaufTests.test_t11_datei_ausserhalb_schreibbereich)
T11: Datei außerhalb Schreibbereich ... ok
test_t12_handover_fehlt (tests.test_umsetzung_auto.LaufTests.test_t12_handover_fehlt)
T12: Handover fehlt ... ok
test_t15_fehlgeschlagener_befehl_mit_wortlaut (tests.test_umsetzung_auto.LaufTests.test_t15_fehlgeschlagener_befehl_mit_wortlaut)
T15: Lebendsignal – Werkzeugzeile (fehlgeschlagener, nicht abgelehnter Befehl mit Wortlaut) ... ok
test_t15_herzschlag (tests.test_umsetzung_auto.LaufTests.test_t15_herzschlag)
T15: Lebendsignal – Werkzeugzeile (Herzschlag während einer langen Pause) ... ok
test_t15_lebendsignal_werkzeugzeile (tests.test_umsetzung_auto.LaufTests.test_t15_lebendsignal_werkzeugzeile)
T15: Lebendsignal – Werkzeugzeile ... ok
test_t16_pruefen_rot (tests.test_umsetzung_auto.LaufTests.test_t16_pruefen_rot)
T16: pruefen rot ... ok
test_t18_schreibbereich_ordner_eintrag (tests.test_umsetzung_auto.LaufTests.test_t18_schreibbereich_ordner_eintrag)
T18: Schreibbereich – Ordner-Eintrag ... ok
test_t19_schreibbereich_verbotene_dateien (tests.test_umsetzung_auto.LaufTests.test_t19_schreibbereich_verbotene_dateien)
T19: Schreibbereich – Verbotene Dateien ... ok
test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen (tests.test_umsetzung_auto.LaufTests.test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen)
T7: Erfolgreicher Lauf, reason: stop, alle Prüfungen grün ... ok
test_t7_exitcode_von_opencode_wird_ignoriert (tests.test_umsetzung_auto.LaufTests.test_t7_exitcode_von_opencode_wird_ignoriert)
T7: Erfolgreicher Lauf, reason: stop (opencode-Exit ≠ 0 zählt nicht, nur das JSON) ... ok
test_t8_kein_gueltiges_json (tests.test_umsetzung_auto.LaufTests.test_t8_kein_gueltiges_json)
T8: Lauf ohne reason: stop (Strom ohne gültiges JSON) ... ok
test_t8_lauf_ohne_reason_stop (tests.test_umsetzung_auto.LaufTests.test_t8_lauf_ohne_reason_stop)
T8: Lauf ohne reason: stop ... ok
test_t9_timeout (tests.test_umsetzung_auto.LaufTests.test_t9_timeout)
T9: Timeout ... ok
test_t9_timeout_beendet_unterprozesse (tests.test_umsetzung_auto.LaufTests.test_t9_timeout_beendet_unterprozesse)
T9: Timeout (auch Kindprozesse von opencode werden beendet) ... ok
test_t13_nacharbeit_auftrag_aus_datei (tests.test_umsetzung_auto.NacharbeitTests.test_t13_nacharbeit_auftrag_aus_datei)
T13: Nacharbeit – Auftrag aus Datei ... ok
test_t13_nummer_aus_handover (tests.test_umsetzung_auto.NacharbeitTests.test_t13_nummer_aus_handover)
T13: Nacharbeit – Auftrag aus Datei (Nummer n = bestehende Abschnitte im Handover + 1) ... ok
test_t13_ohne_neuen_abschnitt_nicht_in_ordnung (tests.test_umsetzung_auto.NacharbeitTests.test_t13_ohne_neuen_abschnitt_nicht_in_ordnung)
T13: Nacharbeit – Auftrag aus Datei (Handover ohne neuen Abschnitt → Exit 1) ... ok
test_t14_gegenfall_fortschritt_hebt_halt_auf (tests.test_umsetzung_auto.NacharbeitTests.test_t14_gegenfall_fortschritt_hebt_halt_auf)
T14: Nacharbeit – zwei ohne Fortschritt (Gegenfall: einer mit Fortschritt) ... ok
test_t14_nacharbeit_zwei_ohne_fortschritt (tests.test_umsetzung_auto.NacharbeitTests.test_t14_nacharbeit_zwei_ohne_fortschritt)
T14: Nacharbeit – zwei ohne Fortschritt ... ok
test_t17_handover_anderes_datum_ist_fremd (tests.test_umsetzung_auto.NacharbeitTests.test_t17_handover_anderes_datum_ist_fremd)
T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen (Handover mit anderem Datum) ... ok
test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen (tests.test_umsetzung_auto.NacharbeitTests.test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen)
T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen ... ok
test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei (tests.test_umsetzung_auto.NacharbeitTests.test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei)
T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2) ... ok
test_t1_vorab_pruefung_kurztitel_ungueltig (tests.test_umsetzung_auto.VorabTests.test_t1_vorab_pruefung_kurztitel_ungueltig)
T1: Vorab-Prüfung – Kurztitel ungültig ... ok
test_t2_vorab_pruefung_kein_spec_commit (tests.test_umsetzung_auto.VorabTests.test_t2_vorab_pruefung_kein_spec_commit)
T2: Vorab-Prüfung – kein Spec-Commit ... ok
test_t3_vorab_pruefung_leerer_schreibbereich (tests.test_umsetzung_auto.VorabTests.test_t3_vorab_pruefung_leerer_schreibbereich)
T3: Vorab-Prüfung – Spec ohne ## Schreibbereich (Abweichung 2: leerer Abschnitt gilt wie fehlend) ... ok
test_t3_vorab_pruefung_spec_ohne_schreibbereich (tests.test_umsetzung_auto.VorabTests.test_t3_vorab_pruefung_spec_ohne_schreibbereich)
T3: Vorab-Prüfung – Spec ohne ## Schreibbereich ... ok
test_t4_vorab_pruefung_unrunder_arbeitsstand (tests.test_umsetzung_auto.VorabTests.test_t4_vorab_pruefung_unrunder_arbeitsstand)
T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf) ... ok
test_t5_vorab_pruefung_opencode_fehlt (tests.test_umsetzung_auto.VorabTests.test_t5_vorab_pruefung_opencode_fehlt)
T5: Vorab-Prüfung – opencode fehlt ... ok
test_t6_vorab_pruefung_modell_kein_llamacpp (tests.test_umsetzung_auto.VorabTests.test_t6_vorab_pruefung_modell_kein_llamacpp)
T6: Vorab-Prüfung – Modell kein llamacpp/ ... ok

----------------------------------------------------------------------
Ran 32 tests in 9.085s

OK
```

Alte Suiten am Mac, unverändert grün: `role-split/kette/test_kette.py`, `tests/test_kette_review_auto.py`, `tests/test_paket_vollstaendig.py` zusammen 67 Tests OK (vor und nach Nachbesserung 1).

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

Stand vor Nachbesserung 1 (23 Methoden). Die aktuelle Gegenprobe steht in `pruefung_20261027_umsetzung_auto.md`.

```
$ python3 role-split/kette/kette.py gegenprobe umsetzung_auto --commit 3700da7
Gegenprobe gegen 3700da7: 23 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 22 Test(s) rot
  role-split/kette/testdata/opencode_fake.py: 16 Test(s) rot

  rot   test_t10_selbst_commit  <- kette.py, opencode_fake.py
  rot   test_t11_datei_ausserhalb_schreibbereich  <- kette.py, opencode_fake.py
  rot   test_t12_handover_fehlt  <- kette.py, opencode_fake.py
  rot   test_t13_nacharbeit_auftrag_aus_datei  <- kette.py, opencode_fake.py
  rot   test_t14_gegenfall_fortschritt_hebt_halt_auf  <- kette.py
  rot   test_t14_nacharbeit_zwei_ohne_fortschritt  <- kette.py, opencode_fake.py
  rot   test_t15_lebendsignal_werkzeugzeile  <- kette.py, opencode_fake.py
  rot   test_t16_pruefen_rot  <- kette.py, opencode_fake.py
  rot   test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen  <- kette.py
  rot   test_t18_schreibbereich_ordner_eintrag  <- kette.py, opencode_fake.py
  rot   test_t19_schreibbereich_verbotene_dateien  <- kette.py, opencode_fake.py
  rot   test_t1_vorab_pruefung_kurztitel_ungueltig  <- kette.py
  rot   test_t20_attrappe_sperrt_echtes_repo  <- opencode_fake.py
  rot   test_t20_main_gleicher_exit_wie_funktionsaufruf  <- kette.py, opencode_fake.py
  rot   test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei  <- kette.py, opencode_fake.py
  rot   test_t2_vorab_pruefung_kein_spec_commit  <- kette.py
  rot   test_t3_vorab_pruefung_spec_ohne_schreibbereich  <- kette.py
  rot   test_t4_vorab_pruefung_unrunder_arbeitsstand  <- kette.py
  rot   test_t5_vorab_pruefung_opencode_fehlt  <- kette.py
  rot   test_t6_vorab_pruefung_modell_kein_llamacpp  <- kette.py, opencode_fake.py
  rot   test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen  <- kette.py, opencode_fake.py
  rot   test_t8_lauf_ohne_reason_stop  <- kette.py, opencode_fake.py
  rot   test_t9_timeout  <- kette.py, opencode_fake.py

23 von 23 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Die Tests laufen in temporären Git-Repos; jeder Test prüft am Ende, dass HEAD und `git status` des echten Repos unverändert sind. Die Attrappe verweigert jede Arbeit außerhalb des Temp-Ordners.

## Hawe muss ausführen

- Commit der Umsetzung (nach `review-auto` und Gegenprüfung).
- Abnahme: echter `umsetzung-auto`-Lauf mit dem 35B auf einer kleinen, von Claude geschriebenen Mini-Spec; Dauer messen.
- Aufräumen nach Commit: `tmp/k10_einbau.py`, `tmp/k10_entwurf.md`, `tmp/k10_35b/`, `docs/projekt_management/_to_delete/`.

## Nicht getestet

- Kein echter `opencode run`-Lauf mit Modell: alle Tests laufen gegen die Attrappe. Ob die deny-Regeln im Agenten im echten Lauf greifen und ob der Ereignisstrom einer echten Sitzung so ausgewertet wird wie erwartet, zeigt erst die Abnahme.
- Verhalten bei mehr als zwei Nacharbeiten nur über die Protokoll-Auswertung geprüft, nicht über echte Folgeläufe.
- Der Timeout-Zweig „opencode reagiert 30 s nach SIGKILL nicht“ ist nicht getestet (lässt sich mit der Attrappe nicht erzeugen).

## Offene Punkte / bekannte Schwächen

- Die Schreibbereichs-Prüfung erkennt Änderungen über Snapshots von `git status`; eine Datei, die im Lauf geändert und exakt zurückgesetzt wird, bleibt unsichtbar (gewollt, aber zu wissen).
- Vermutung: Der Selbst-Commit aus K9 stammt aus Schritt 2 des Agenten `umsetzung`, nicht aus `umsetzung_nacht`; nicht geprüft.
- Dateien unter gitignorierten Pfaden (z. B. `tmp/`, `role-split/results/`) sind für die Schreibbereichs-Prüfung (b) unsichtbar – spec-konform, aber zu wissen.
- Kettendatei-Erkennung ist bei Kurztiteln mit gemeinsamem Anfang unscharf: `verdict_<datum>_umsetzung_auto.md` gilt auch als Kettendatei des Kurztitels `umsetzung` (wie die Spec-Glob `*_<kurztitel>*.md`); niedrig.
- `opencode.db` ist 1,6 GB groß – für die Vormerkungen.

## Nachbesserung 1

Auftrag: Gegenprüfung durch frische Instanz (R42), Ergebnis NACHBESSERN. `review-auto` vorher: formal NACHBESSERN, aber 26 der 27 „hoch“-Zeilen vom Modell selbst zurückgezogen („Korrekt.“/„Befund entfällt.“); einziger echter Befund niedrig (`proc.wait()` nach SIGKILL). Eingespielt mit `tmp/k10_nb1.py` (Prüfsummen vorher/nachher je Datei).

| Punkt | Änderung | Test |
|---|---|---|
| M1 | Nummer `n` = Anzahl `## Nachbesserung`-Abschnitte im Handover + 1 (nicht mehr aus dem Protokoll) | `test_t13_nummer_aus_handover` |
| M2 | Fehlgeschlagene und abgelehnte Befehle mit Wortlaut auf stdout und im Protokoll | `test_t15_fehlgeschlagener_befehl_mit_wortlaut` |
| M3 | (c) prüft bei Nacharbeit den Abschnitt `## Nachbesserung n`; Attrappe schreibt ihn mit `FAKE_NACHBESSERUNG` | `test_t13_nacharbeit_auftrag_aus_datei`, `test_t13_ohne_neuen_abschnitt_nicht_in_ordnung` |
| Handover-Präfix | `handover` aus `KETTEN_PRAEFIXE` entfernt; nur `handover_<Spec-Datum>_<kt>.md` erlaubt | `test_t17_handover_anderes_datum_ist_fremd` |
| Tokens | input/output/reasoning zusätzlich zu total erfasst und protokolliert | `test_t7_exitcode_von_opencode_wird_ignoriert` |
| N1 | Attrappe prüft jedes Schreibziel gegen den Temp-Ordner | `test_t20_attrappe_sperrt_echtes_repo` (eigener TMPDIR, damit auch die alte Attrappe in der Gegenprobe nicht hinausschreibt) |
| N2 | Schutz des echten Repos vergleicht zusätzlich Prüfsummen der offenen Dateien | alle (Cleanup) |
| N3 | `./` als Präfix entfernt (`[2:]` statt `lstrip`) | – (eine Zeile, ungetestet) |
| N4 | Hinweis vor dem Start, wenn der Schreibbereich eine Vorgabe nennt | – (nur stderr-Hinweis, ungetestet) |
| Härtung Timeout | scheitert `killpg`: `proc.kill()`, danach `wait(timeout=30)`, sonst Befund | – |
| Lücken (empfohlen) | Kindprozess-Kill, Herzschlag, kaputter Strom, opencode-Exit ≠ 0, leerer Schreibbereich | `test_t9_timeout_beendet_unterprozesse`, `test_t15_herzschlag`, `test_t8_kein_gueltiges_json`, `test_t7_exitcode_von_opencode_wird_ignoriert`, `test_t3_vorab_pruefung_leerer_schreibbereich` |

Lokal (Claude) zusätzlich als Mutanten geprüft: `killpg` → `proc.kill()` macht `test_t9_timeout_beendet_unterprozesse` rot; ohne `herz.start()` wird `test_t15_herzschlag` rot. Mit dem Stand vor Nachbesserung 1 werden die Tests zu M1, M2, M3, Tokens/Exit und Handover-Präfix rot.

Nachtrag nach PASS der Gegenprüfung (niedriger Fund, durch M2 entstanden): `_protokoll` wertet nur noch Laufzeilen aus (`- **`), damit fremder Befehlstext in den Unterzeilen die Halt-Regel nicht täuscht; Zeilenumbrüche im Wortlaut werden durch Leerzeichen ersetzt. Test `test_t14_unterzeilen_zaehlen_nicht` (mit altem `_protokoll` rot, lokal geprüft).

Aus der Gegenprüfung offen gelassen, mit Beleg: `--title` steht in `opencode run --help` (1.19.3) und „letzte passende Regel gewinnt“ ist durch Probe P6 gemessen – beides in `claude/k10-opencode-probe.md`.
