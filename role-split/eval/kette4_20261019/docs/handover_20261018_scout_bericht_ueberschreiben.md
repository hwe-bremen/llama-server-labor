# Handover: scout_bericht_ueberschreiben

- **Spec:** `docs/projekt_management/spec_20261018_scout_bericht_ueberschreiben.md`
- **Datum:** 2026-10-18
- **Modell / Werkzeug:** Qwen3.6-27B in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** `818aa5d`

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1 | erfüllt | `agents/llm_scout/llm_scout.py`, Funktion `save_report()` |
| A2 | erfüllt | `scripts/send_scout_email.py`, Funktionen `get_last_sent_lauf_nr()`, `count_report_runs()` |
| A3 | erfüllt | `scripts/send_scout_email.py`, Funktion `record_sent_week(lauf_nr)`, `mode_normal()` |
| A4 | erfüllt (Bestand unverändert) | `scripts/run_scout_pipeline.sh` – Exit-Code-Weitergabe und Lauf-Datei waren bereits korrekt |
| A5 | erfüllt (Bestand unverändert) | `scripts/send_scout_email.py` – `mode_dry_run()` berührt Versand-Nachweis nicht |

## Geänderte und neue Dateien

- `agents/llm_scout/llm_scout.py` – geändert – Neue Funktion `save_report()` mit Anhäng-Logik; `main()` ruft `save_report()` statt direktem Datei-Schreiben auf.
- `scripts/send_scout_email.py` – geändert – Neuer Versand-Nachweis pro `lauf_nr`: `get_last_sent_lauf_nr()`, `count_report_runs()`, `record_sent_week(lauf_nr)`. `mode_normal()` zählt Läufen, reserviert Zustandszeile vor Versand.
- `tests/test_scout_bericht_ueberschreiben.py` – neu – 9 Tests (T1–T9) als unittest.

## Abweichungen von der Spec

- Keine.

## Annahmen

- Die Zustandsdatei `.sent_state` wird im Report-Verzeichnis (`weekly-reports/`) abgelegt, wie in der Spec beschrieben.
- Der `lauf_nr` wird durch Zählen der `## Nachtrag KW`-Header + 1 (Erstbericht) bestimmt.
- Die `record_sent_week(lauf_nr)`-Funktion wird VOR dem SMTP-Versand aufgerufen (Reservierung), wie in A3 gefordert.

## Getestet (mit echter Ausgabe)

**T1: Zweitlauf hängt Nachtrag an, Erstbericht bleibt byte-identisch** – bestanden

**T2: Fehlender Bericht, ungesendete Woche → Exit 3** – bestanden

**T3: SMTP-Fehler nach Zustands-Reservierung → Zustandszeile bleibt, Mail fehlt, kein Zweitversand** – bestanden

**T4: Alles gesendet → Exit 0, keine Mail** – bestanden

**T5: Dry-Run berührt Zustandsdatei nicht** – bestanden

**T6: Atomarer Zustand – Zustandsdatei bleibt unverändert bei simuliertem os.replace-Fehler** – bestanden

**T7: Pipeline gibt Exit-Code an launchd weiter und schreibt Lauf-Datei** – bestanden

**T8: Import-Test – llm_scout.py lässt sich ohne __main__ importieren** – bestanden

**T9: Dritter Lauf hängt zweiten Nachtrag an** – bestanden

```
$ python3 -m unittest -v tests/test_scout_bericht_ueberschreiben.py
test_t1_zweitlauf_haengt_nachtrag_an_erstbericht_bleibt_byte_identisch (tests.test_scout_bericht_ueberschreiben.TestA1Zweitlauf.test_t1_zweitlauf_haengt_nachtrag_an_erstbericht_bleibt_byte_identisch)
T1: Zweitlauf hängt Nachtrag an, Erstbericht bleibt byte-identisch. ... ok
test_t9_dritter_lauf_haengt_zweiten_nachtrag_an (tests.test_scout_bericht_ueberschreiben.TestA1Zweitlauf.test_t9_dritter_lauf_haengt_zweiten_nachtrag_an)
T9: Dritter Lauf hängt zweiten Nachtrag an. ... ok
test_t2_fehlender_bericht_ungesendete_woche_exit_3 (tests.test_scout_bericht_ueberschreiben.TestA2VersandNachweis.test_t2_fehlender_bericht_ungesendete_woche_exit_3)
T2: Fehlender Bericht, ungesendete Woche → Exit 3. ... ok
test_t4_alles_gesendet_exit_0_keine_mail (tests.test_scout_bericht_ueberschreiben.TestA2VersandNachweis.test_t4_alles_gesendet_exit_0_keine_mail)
T4: Alles gesendet → Exit 0, keine Mail. ... ok
test_t3_smtp_fehler_nach_zustands_reservierung (tests.test_scout_bericht_ueberschreiben.TestA3CrashSafety.test_t3_smtp_fehler_nach_zustands_reservierung)
T3: SMTP-Fehler nach Zustands-Reservierung → Zustandszeile bleibt, Mail fehlt, kein Zweitversand. ... Fehler beim E-Mail-Versand: Verbindung abgebrochen
ok
test_t6_atomarer_zustand_os_replace_fehler (tests.test_scout_bericht_ueberschreiben.TestA3CrashSafety.test_t6_atomarer_zustand_os_replace_fehler)
T6: Atomarer Zustand – Zustandsdatei bleibt unverändert bei simuliertem os.replace-Fehler. ... ok
test_t7_pipeline_gibt_exit_code_weiter_und_schreibt_lauf_datei (tests.test_scout_bericht_ueberschreiben.TestA4Pipeline.test_t7_pipeline_gibt_exit_code_weiter_und_schreibt_lauf_datei)
T7: Pipeline gibt Exit-Code an launchd weiter und schreibt Lauf-Datei. ... ok
test_t5_dry_run_beruehrt_zustandsdatei_nicht (tests.test_scout_bericht_ueberschreiben.TestA5DryRun.test_t5_dry_run_beruehrt_zustandsdatei_nicht)
T5: Dry-Run berührt Zustandsdatei nicht. ... ok
test_t8_import_test_llm_scout_ohne_main (tests.test_scout_bericht_ueberschreiben.TestT8Import.test_t8_import_test_llm_scout_ohne_main)
T8: Import-Test – llm_scout.py lässt sich ohne __main__ importieren. ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.435s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe scout_bericht_ueberschreiben --commit 818aa5d
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests nutzen temporäre Verzeichnisse und mocken SMTP. Kein echter Versand, keine Netzwerkanfragen an externe Ziele.

## Hawe muss ausführen

- Einen echten Pipeline-Lauf mit `bash scripts/run_scout_pipeline.sh` (optional, nur für Integrationstest).
- Einen echten Versand mit `SCOUT_ALLOW_SEND=1 python3 scripts/send_scout_email.py` (optional, nur für Live-Test).

## Nicht getestet

- Kein echter SMTP-Versand ( bewusst nicht getestet, da Außenwirkung).
- Kein echter Scout-Lauf (würde GitHub/HF-API aufrufen).

## Offene Punkte / bekannte Schwächen

- Beim ersten Upgrade auf das neue `.sent_state`-Format: Falls es eine alte `.sent_state` mit nur einem Datum pro Woche gibt (altes Format `YYYY_WW DATE`), ignoriert `get_last_sent_lauf_nr()` diese Zeilen (da sie keinen `lauf_nr`-Teil haben). Das ist beabsichtigt – alte Einträge werden nicht als gesendet gezählt, und die Woche wird neu versendet.
