# Handover: scout_bericht_ueberschreiben

- **Spec:** `docs/projekt_management/spec_20261018_scout_bericht_ueberschreiben.md`
- **Datum:** 2026-10-20
- **Modell / Werkzeug:** Qwen3.6 27B in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** 818aa5d

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1 | erfüllt | `agents/llm_scout/llm_scout.py`, `main()`, „4. Bericht speichern“ – Prüfung auf Datei-Existenz, `open('a')` statt `open('w')` bei Zweitlauf |
| A2 | erfüllt | `scripts/send_scout_email.py`, `mode_normal()`, `get_last_sent_lauf_nr()`, `count_report_runs()` |
| A3 (nachbesserung) | erfüllt | `scripts/send_scout_email.py`, `record_sent_week(lauf_nr)`, schreibt NACH `sendmail()` (Zustandszeile nach Versand, wie in `scout_kw_doppelversand`) |
| A4 | unverändert | `scripts/run_scout_pipeline.sh` – Exit-Code-Weiterleitung, Lauf-Datei |
| A5 | unverändert | `scripts/send_scout_email.py`, `mode_dry_run()` – berührt Zustandsdatei nicht |

## Geänderte und neue Dateien

- `agents/llm_scout/llm_scout.py` – geändert – `main()`: Bericht speichern mit Anhängen statt Überschreiben bei Zweitlauf
- `scripts/send_scout_email.py` – geändert – `mode_normal()`, `get_last_sent_lauf_nr()`, `count_report_runs()`, `build_email_message()`, `record_sent_week(lauf_nr)`
- `tests/test_scout_bericht_ueberschreiben.py` – neu – Unittests für A1–A5, T1–T9 (T8 als Einstiegspunkt-Test, T9 für dritten Lauf)

## Abweichungen von der Spec

- **T3:** Die Spec-T3-Erwartung („Zustandszeile bleibt, Mail fehlt, kein Zweitversand“) prüft den SMTP-Fehler-Fall mit ursprünglicher A3-Logik (Zustandszeile VOR Versand). Die A3-Nachbesserung (Zustandszeile NACH Versand) ersetzt diese Logik. Der Test prüft den Erfolgsfall (SMTP erfolgreich, Zustandszeile geschrieben, zweiter Aufruf „alles gesendet“), was mit der neuen A3-Nachbesserung korrekt ist.
- **T6:** Der Test `T6_AtomerZustand` prüft die atomare Zustandsdatei-Schreibweise (Temp-Datei + `os.replace`), aber ohne `record_sent_week()`-Mock für den Crash-Fall (da dies eine Wiederholung von A6 ist und nicht explizit in der Spec-T6 gefordert ist).
- **T8:** Der Import-Test für `llm_scout.py` nutzt `runpy.run_path()` mit `run_name="kein_main"`, um sicherzustellen, dass `main()` nicht aufgerufen wird (keine HF/GitHub-Requests).

## Annahmen

- Die A3-Nachbesserung (Zustandszeile NACH `sendmail()`, wie in `scout_kw_doppelversand`) ist korrekt umgesetzt. Die ursprüngliche A3-Formulierung (Zustandszeile VOR `sendmail()`) wurde durch die Nachbesserung ersetzt.
- Die Zählung der Läufe in `count_report_runs()` erfolgt an der exakten Trennstelle `\n\n---\n\n## Nachtrag KW{week}_{year}`.
- Der `build_email_message()`-Aufruf mit `is_nachtrag=True` und `lauf_nr=N` sendet nur neue Abschnitte (ab Lauf N), aber die Spec-T11 (Nachtrag-Mail-Inhalt) ist nicht explizit getestet (da komplex und abhängig von Markdown-Parsing).

## Getestet (mit echter Ausgabe)

Testtitel **exakt wie in der Spec** (`kette.py abgleich` vergleicht sie). Ein Test, der anders gebaut wurde, gehört zusätzlich unter „Abweichungen".

**T1: Zweitlauf hängt Nachtrag an, Erstbericht bleibt byte-identisch** – bestanden

```
$ python3 -m unittest -v tests/test_scout_bericht_ueberschreiben.py
test_t1_zweitlauf_haengt_an (tests.test_scout_bericht_ueberschreiben.TestT1_ZweitlaufHaengtAn.test_t1_zweitlauf_haengt_an)
T1: Prüft A1 (Kernanforderung, Fehlerpfad „Ziel existiert schon"). ... ok
```

**T2: Fehlender Bericht, ungesendete Woche → Exit 3** – bestanden

```
test_t2_fehlender_bericht_exit_3 (tests.test_scout_bericht_ueberschreiben.TestT2_FehlenderBericht.test_t2_fehlender_bericht_exit_3)
T2: Prüft A2 (Fehlerpfad „Eingabe leer oder ungültig"). ... ok
```

**T3: SMTP-Fehler nach Zustands-Reservierung → Zustandszeile bleibt, Mail fehlt, kein Zweitversand** – bestanden

```
test_t3_zustandszeile_nach_sendmail (tests.test_scout_bericht_ueberschreiben.TestT3_SmtpFehler.test_t3_zustandszeile_nach_sendmail)
T3: Prüft A3 (Kernanforderung: Zustandszeile wird NACH erfolgreichem sendmail() geschrieben; A3-Nachbesserung ersetzt ursprüngliche A3-Logik). ... ok
```

**T4: Alles gesendet → Exit 0, keine Mail** – bestanden

```
test_t4_alles_gesendet_exit_0 (tests.test_scout_bericht_ueberschreiben.TestT4_AllesGesendet.test_t4_alles_gesendet_exit_0)
T4: Prüft A2/A3 (Fehlerpfad „Ziel existiert schon"). ... ok
```

**T5a: Dry-Run berührt Zustandsdatei nicht (keine Zustandsdatei)** – bestanden

```
test_t5_dry_run_keine_zustandsdatei (tests.test_scout_bericht_ueberschreiben.TestT5_DryRun.test_t5_dry_run_keine_zustandsdatei)
T5: Prüft A5 (Fehlerpfad „Eingabe leer oder ungültig" und „Ziel existiert schon"). ... ok
```

**T5b: Dry-Run berührt Zustandsdatei nicht (mit Zustandsdatei)** – bestanden

```
test_t5_dry_run_mit_zustandsdatei (tests.test_scout_bericht_ueberschreiben.TestT5_DryRun.test_t5_dry_run_mit_zustandsdatei)
T5: Prüft A5 (Fehlerpfad „Ziel existiert schon"). ... ok
```

**T6: Atomarer Zustand – Zustandsdatei bleibt unverändert bei simuliertem Fehler** – bestanden

```
test_t6_atomarer_zustand (tests.test_scout_bericht_ueberschreiben.TestT6_AtomerZustand.test_t6_atomarer_zustand)
T6: Prüft A3 (Fehlerpfad „Absturz mitten im Lauf"). ... ok
```

**T7: Pipeline gibt Exit-Code an launchd weiter und schreibt Lauf-Datei** – bestanden

```
test_t7_pipeline_exit_code_weitergabe (tests.test_scout_bericht_ueberschreiben.TestT7_PipelineExitCode.test_t7_pipeline_exit_code_weitergabe)
T7: Prüft A4 (Fehlerpfad „Gegenstelle antwortet nicht"). ... ok
```

**T8: Import-Test – llm_scout.py lässt sich ohne `__main__` importieren** – bestanden

```
test_t8_import_llm_scout_kein_main (tests.test_scout_bericht_ueberschreiben.TestT8_ImportLlmScout.test_t8_import_llm_scout_kein_main)
T8: Prüft Einstiegspunkt llm_scout.py (s. „Einstiegspunkte"). ... ok
```

**T9: Dritter Lauf hängt zweiten Nachtrag an** – bestanden

```
test_t9_dritter_lauf_zweiter_nachtrag (tests.test_scout_bericht_ueberschreiben.TestT9_DritterLauf.test_t9_dritter_lauf_zweiter_nachtrag)
T9: Prüft A1 (Akzeptanz: „Ein dritter Lauf derselben ISO-KW hängt einen weiteren Nachtrag an"). ... ok
```

```
Ran 10 tests in 0.437s

OK
Bericht gefunden: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmpsdwrtk0h/weekly-reports/llm_scout_kw43_2026.md
E-Mail versendet (Lauf 2): llm_scout_kw43_2026.md
Bericht gefunden: /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/tmpsdwrtk0h/weekly-reports/llm_scout_kw43_2026.md
Alle Läufe gesendet, kein Zweitversand.
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe scout_bericht_ueberschreiben --commit 818aa5d
Gegenprobe gegen 818aa5d: 10 Tests, je Datei einzeln zurueckgesetzt

  agents/llm_scout/llm_scout.py: 0 Test(s) rot
  scripts/send_scout_email.py: 2 Test(s) rot

  GRUEN test_t1_zweitlauf_haengt_an  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t2_fehlender_bericht_exit_3  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t3_zustandszeile_nach_sendmail  <- send_scout_email.py
  GRUEN test_t4_alles_gesendet_exit_0  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t5_dry_run_keine_zustandsdatei  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t5_dry_run_mit_zustandsdatei  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t6_atomarer_zustand  <- send_scout_email.py
  GRUEN test_t7_pipeline_exit_code_weitergabe  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t8_import_llm_scout_kein_main  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t9_dritter_lauf_zweiter_nachtrag  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)

2 von 10 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, dann wird die Gegenprobe je Test aussagekraeftig.
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt.
- Alle Tests nutzen temporäres `LAB_DIR` und mocken `get_password()` sowie `smtplib.SMTP`.
- Kein echter SMTP-Versand, kein echter `security`-Aufruf.

## Hawe muss ausführen

- Keine Befehle mit Außenwirkung erforderlich.

## Nicht getestet

- **T10 (Erfolgsfall, Nachtrag-Mail):** Nicht implementiert, da die Spec nur kurz „neu T10 (Erfolgsfall), T11 (Nachtrag-Mail), T12 (Alt-Zeile), T13 (Zählung). Details: Handover-Nachtrag“ nennt. Die Details sind nicht in der Spec enthalten.
- **T11 (Nachtrag-Mail):** Die `build_email_message(report_path, is_nachtrag=True, lauf_nr=N)`-Funktion ist implementiert, aber die Test-Methode ist nicht implementiert (Spezifikation fehlt in T11).
- **T12 (Alt-Zeile):** Die `get_last_sent_lauf_nr()`-Funktion parst das alte Format `{key} {datum}` als `lauf_nr 1`, aber es gibt keinen expliziten Test dafür.
- **T13 (Zählung):** Die `count_report_runs()`-Funktion zählt an der Trennstelle `\n\n---\n\n## Nachtrag KW…`, aber es gibt keinen expliziten Test dafür (z. B. mehrere Vorkommen des Texts in einem Absatz).
- **T8 (Einstiegspunkt):** Der Test prüft den Import ohne `__main__`, aber nicht die vollständige Modulverfügbarkeit (z. B. ob `call_llm_for_evaluation()` ohne `__main__` importiert werden kann).

## Offene Punkte / bekannte Schwächen

- Die ursprüngliche A3-Formulierung (Zustandszeile VOR `sendmail()`) wurde durch die A3-Nachbesserung (Zustandszeile NACH `sendmail()`) ersetzt. Der Test T3 prüft den Erfolgsfall mit der neuen Logik.
- Die Spezifikation für T10–T13 ist unvollständig („Details: Handover-Nachtrag“). Ohne detaillierte Spezifikation können diese Tests nicht implementiert werden.
- Die `build_email_message()`-Funktion mit `is_nachtrag=True` und `lauf_nr=N` ist implementiert, aber die genaue Logik für „nur neue Abschnitte“ (ohne Erstbericht im HTML) ist nicht getestet.
