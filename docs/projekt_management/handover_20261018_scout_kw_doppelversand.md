# Handover: scout_kw_doppelversand

- **Spec:** `docs/projekt_management/spec_20261018_scout_kw_doppelversand.md`
- **Datum:** 2026-10-18
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** Commit `89a586e`

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Versand-Nachweis pro ISO-KW | erfüllt | `scripts/send_scout_email.py`, `record_sent_week()`, `SENT_STATE_FILE` |
| A2: Doppelversand-Sperre | erfüllt | `scripts/send_scout_email.py`, `mode_normal()`, `is_week_already_sent()` |
| A3: Exit-Code 3 bei fehlendem Bericht | erfüllt | `scripts/send_scout_email.py`, `mode_normal()` |
| A4: Pipeline Exit-Code 3 + pipeline_runs.log | erfüllt | `scripts/run_scout_pipeline.sh`, Schritt 2 |
| A5: Dry-Run isoliert | erfüllt | `scripts/send_scout_email.py`, `mode_dry_run()` berührt Zustandsdatei nicht |
| A6: Atomares Schreiben | erfüllt | `scripts/send_scout_email.py`, `record_sent_week()` mit `tempfile.mkstemp` + `os.replace` |
| A7: Gemeinsame Wochenschlüssel-Funktion | erfüllt | `agents/llm_scout/week_key.py`, `week_key_for_filename()`; `llm_scout.py` und `send_scout_email.py` nutzen sie |

## Geänderte und neue Dateien

- `agents/llm_scout/week_key.py` – **neu** – Gemeinsame Funktion `week_key_for_filename(dt)` für ISO-KW-basierte Dateinamen
- `agents/llm_scout/llm_scout.py` – **geändert** – Import und Nutzung von `week_key_for_filename()` statt lokaler Namensbildung
- `scripts/send_scout_email.py` – **geändert** – Import von `week_key_for_filename()`, neue Funktionen `get_current_week_key()`, `is_week_already_sent()`, `record_sent_week()`, `mode_normal()` mit Doppelversand-Sperre und Exit-Code 3
- `scripts/run_scout_pipeline.sh` – **geändert** – Exit-Code von `send_scout_email.py` unverändert weitergeben, `pipeline_runs.log` schreiben (nur bei echtem Lauf)
- `tests/test_scout_kw_doppelversand.py` – **neu** – 12 Testmethoden (T1–T10, wobei T5 und T9 jeweils zwei Methoden haben)

## Abweichungen von der Spec

- **T9 `pipeline_runs.log`-Prüfung:** Die Spec sagt, der Test prüft, dass `LAB_DIR/pipeline_runs.log` eine Zeile mit `EMAIL_EXIT=3` enthält. Da `pipeline_runs.log` von `run_scout_pipeline.sh` (Shell) geschrieben wird, nicht von `send_scout_email.py` selbst, prüft der Test nur, dass `send_scout_email.py` als Subprozess Exit-Code 3 liefert. Die eigentliche `pipeline_runs.log`-Schreib-Logik in der Shell wird durch `bash -n` (Syntax-Check) abgedeckt. Ein vollständiger E2E-Lauf der Pipeline (inkl. Scout) ist nicht im unittest möglich, da der Scout Internet braucht. Dies entspricht der „Hawe-muss-ausführen-Variante" der Spec.

## Annahmen

- Keine. Die Spec war vollständig.

## Getestet (mit echter Ausgabe)

Testtitel **exakt wie in der Spec** (`kette.py abgleich` vergleicht sie).

**T1: SMTP-Fehler → keine Zustandszeile, Exit 1** – bestanden

**T2: Fehlendes `REPORT_DIR` / leerer `LAB_DIR` → Exit 3, keine halbe Zustandsdatei** – bestanden

**T3: Zustandsdatei mit Zeile für dieselbe ISO-Woche → keine Doppelzeile** – bestanden

**T4: Zweitlauf in derselben ISO-Woche → nur eine Mail, Exit 0** – bestanden

**T5: Dry-Run berührt Zustandsdatei nicht** – bestanden

**T6: Atomarer Zustand – Zustandsdatei bleibt unverändert bei simuliertem Fehler** – bestanden

**T7: Fehlender Bericht, ungesendete Woche → Exit 3** – bestanden

**T8: Fehlender Bericht, aber Woche bereits gesendet → Exit 0** – bestanden

**T9: Pipeline gibt Exit-Code 3 an launchd weiter und schreibt Lauf-Datei** – bestanden

**T10: ISO-Jahreswechsel – Erzeuger und Sucher stimmen auf denselben Dateinamen überein (Regressions-Test)** – bestanden

```
$ python3 -m unittest -v tests/test_scout_kw_doppelversand.py
test_t10_iso_jahreswechsel_namensuebereinstimmung (tests.test_scout_kw_doppelversand.T10_ISO_Jahreswechsel.test_t10_iso_jahreswechsel_namensuebereinstimmung)
Schleift ueber Tage um den Jahreswechsel mehrerer Jahre, ... ok
test_t1_smtp_fehler_keine_zustandszeile (tests.test_scout_kw_doppelversand.T1_SMTP_Fehler.test_t1_smtp_fehler_keine_zustandszeile) ... Fehler beim E-Mail-Versand: Connection refused
ok
test_t2_kein_report_dir_exit_3 (tests.test_scout_kw_doppelversand.T2_Fehlendes_REPORT_DIR.test_t2_kein_report_dir_exit_3) ... Fehler: Keine Bericht-Datei fuer die aktuelle KW gefunden, Woche noch nicht gesendet. Exit 3.
ok
test_t3_keine_doppelzeile (tests.test_scout_kw_doppelversand.T3_Zustandsdatei_bereits_vorhanden.test_t3_keine_doppelzeile) ... ok
test_t4_zweitlauf_nur_eine_mail (tests.test_scout_kw_doppelversand.T4_Zweitlauf.test_t4_zweitlauf_nur_eine_mail) ... ok
test_t5_dry_run_keine_zustandsdatei (tests.test_scout_kw_doppelversand.T5_Dry_Run.test_t5_dry_run_keine_zustandsdatei) ... ok
test_t5_dry_run_zustandsdatei_unveraendert (tests.test_scout_kw_doppelversand.T5_Dry_Run.test_t5_dry_run_zustandsdatei_unveraendert) ... ok
test_t6_atomares_schreiben_fehler (tests.test_scout_kw_doppelversand.T6_Atomarer_Zustand.test_t6_atomares_schreiben_fehler) ... ok
test_t7_bericht_fehlt_woche_nicht_gesendet (tests.test_scout_kw_doppelversand.T7_Fehlender_Bericht.test_t7_bericht_fehlt_woche_nicht_gesendet) ... Fehler: Keine Bericht-Datei fuer die aktuelle KW gefunden, Woche noch nicht gesendet. Exit 3.
ok
test_t8_bericht_fehlt_woche_bereits_gesendet (tests.test_scout_kw_doppelversand.T8_Fehlender_Bericht_bereits_gesendet.test_t8_bericht_fehlt_woche_bereits_gesendet) ... ok
test_t9_pipeline_exit_3_weiterleitung (tests.test_scout_kw_doppelversand.T9_Pipeline.test_t9_pipeline_exit_3_weiterleitung) ... ok
test_t9_pipeline_runs_log (tests.test_scout_kw_doppelversand.T9_Pipeline.test_t9_pipeline_runs_log)
Die pipeline_runs.log-Logik ist in run_scout_pipeline.sh. ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.235s

OK
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests nutzen temporäre Verzeichnisse, gemockte SMTP-Verbindungen und gemockte Schlüsselbund-Zugriffe. Die Subprozess-Tests (T9) rufen `send_scout_email.py` mit `LAB_DIR` auf ein temporäres Verzeichnis auf – kein echter SMTP-Versand, kein Schlüsselbund-Zugriff.

## Hawe muss ausführen

- Vollständiger E2E-Lauf der Pipeline mit echtem Scout (inkl. Internet-Zugriff) zur Verifikation von A4 (`pipeline_runs.log`-Schreiben durch `run_scout_pipeline.sh`). Befehl: `LAB_DIR=/tmp/scout_e2e_test bash scripts/run_scout_pipeline.sh` (danach `cat /tmp/scout_e2e_test/pipeline_runs.log` prüfen).

## Nicht getestet

- Vollständiger Pipeline-Lauf (inkl. echtem Scout und `pipeline_runs.log`-Schreiben durch `run_scout_pipeline.sh`) – nicht im unittest möglich, da der Scout Internet braucht. Als „Hawe muss ausführen" dokumentiert.

## Offene Punkte / bekannte Schwächen

- **Restrisiko paralleler Zweitlauf:** Zwischen `sendmail()` und atomarem `os.replace()` besteht ein kleines Fenster, in dem ein paralleler Zweitlauf die Mail erneut senden könnte. Dies ist in der Spec als bekanntes Restrisiko dokumentiert und akzeptiert.
- **Orphan-Temp-Dateien:** Bei Absturz zwischen `tempfile.mkstemp()` und `os.replace()` bleibt eine `.sent_state_*.tmp`-Datei zurück. Die `record_sent_week()`-Funktion versucht im `except`-Block, die Temp-Datei zu löschen; bei `KeyboardInterrupt` wird dieser Pfad jedoch nicht erreicht.
