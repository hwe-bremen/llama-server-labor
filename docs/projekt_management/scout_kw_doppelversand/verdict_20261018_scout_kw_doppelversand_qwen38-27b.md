# Verdikt: scout_kw_doppelversand

- **Spec:** `spec_20261018_scout_kw_doppelversand.md`
- **Handover:** `handover_20261018_scout_kw_doppelversand.md`
- **Datum:** 2026-10-18
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `scripts/send_scout_email.py`, `scripts/run_scout_pipeline.sh`, `agents/llm_scout/week_key.py`, `agents/llm_scout/llm_scout.py`, `tests/test_scout_kw_doppelversand.py`, `config/launchd/llm_scout.plist`, Diff gegen `89a586e`

## Ergebnis

**NACHBESSERN** – Die Kernanforderungen A1, A2, A3, A5, A7 sind erfüllt und die Tests T1–T8, T10 messen das Richtige. A4 ist nur teilweise erfüllt: `pipeline_runs.log` wird nicht bei jedem Lauf geschrieben, sondern nur wenn `send_scout_email.py` Exit-Code 0 liefert. Die fehlende Log-Zeile bei Exit 3 ist genau das, was die Spec verhindern soll („damit ist der Exit 3 in dieser Datei sichtbar“).

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Versand-Nachweis pro ISO-KW, nur nach erfolgreichem SMTP | erfüllt | `scripts/send_scout_email.py:229-269` (`record_sent_week`), `:309-311` (Aufruf nach `send_email_smtp`) |
| A2 | Zweitlauf in derselben ISO-Woche sendet nicht erneut | erfüllt | `scripts/send_scout_email.py:241-255` (`is_week_already_sent`), `:279-281` (Prüfung vor Versand) |
| A3 | „Bericht fehlt“ bleibt nicht still (Exit 3) | erfüllt | `scripts/send_scout_email.py:283-293` (Exit 3 bei fehlendem Bericht, ungesendeter Woche) |
| A4 | Pipeline gibt Exit 3 weiter und schreibt `pipeline_runs.log` | teilweise | `scripts/run_scout_pipeline.sh:75-80` (Log-Block), `:82-85` (Exit-Code-Weitergabe). Log wird nur bei `EMAIL_EXIT=0` geschrieben. |
| A5 | Dry-Run bleibt vom Versand-Nachweis isoliert | erfüllt | `scripts/send_scout_email.py:316-335` (`mode_dry_run` berührt `SENT_STATE_FILE` nicht) |
| A6 | Zustandsdatei atomar, keine Doppelzeile | erfüllt | `scripts/send_scout_email.py:248-269` (`record_sent_week` mit `tempfile.mkstemp` + `os.replace` + Prüflogik) |
| A7 | Gemeinsame Funktion für Wochenschlüssel | erfüllt | `agents/llm_scout/week_key.py:14-31`, `agents/llm_scout/llm_scout.py:336`, `scripts/send_scout_email.py:84-87` |

## Handover gegen Code

- **A4 „Pipeline Exit-Code 3 + pipeline_runs.log“ → erfüllt:** Der Code stützt diese Aussage nicht. `run_scout_pipeline.sh:75-80` schreibt die Log-Zeile, aber `:82-84` bricht bei `EMAIL_EXIT != 0` ab, **bevor** die Log-Zeile in die Datei gelangt. Tatsächlich wird `pipeline_runs.log` nur bei `EMAIL_EXIT=0` geschrieben. Das Handover hätte hier „teilweise“ stehen müssen.
- **T9 „Pipeline gibt Exit-Code 3 an launchd weiter und schreibt Lauf-Datei“ → bestanden:** Der Test `test_t9_pipeline_runs_log` prüft nur, dass `send_scout_email.py` als Subprozess Exit 3 liefert. Er prüft **nicht**, dass `run_scout_pipeline.sh` eine Zeile mit `EMAIL_EXIT=3` in `pipeline_runs.log` schreibt. Die Spec verlangt genau diese Prüfung („LAB_DIR/pipeline_runs.log enthält eine Zeile mit EMAIL_EXIT=3“). Der Test misst also nicht, was die Spec verlangt.
- **Alle anderen Aussagen** (A1, A2, A3, A5, A6, A7, T1–T8, T10) sind durch den Code und die Testausgabe im Handover gestützt. Keine weiteren Abweichungen gefunden.

## Befunde

Für **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja“ macht den Befund „hoch“, unabhängig davon, ob die Schwäche schon vorher bestand. `kette.py urteil` prüft das nach.
- **Datenverlust:** Kann Daten verlieren, überschreiben oder echte Daten verändern?
- **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Hänger, Schweigen, falscher Exit-Code, Test misst nichts)?
- **Harte Vorgabe:** Verstößt es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `scripts/run_scout_pipeline.sh:75-85` | A4 verletzt: Bei `EMAIL_EXIT=3` bricht die Pipeline ab, **bevor** die Log-Zeile in `pipeline_runs.log` geschrieben wird. Genau dieser Exit-3-Fall ist aber der, den die Spec sichtbar machen will („damit ist der Exit 3 in dieser Datei und in den launchd-Logs sichtbar“). Ohne Log-Zeile ist der Fehler in der Pipeline-Lauf-Datei unsichtbar. | Den Log-Schreibblock vor die `if [ ${EMAIL_EXIT} -ne 0 ]`-Prüfung versetzen, sodass die Zeile **immer** geschrieben wird (auch bei Fehler). Die Exit-Code-Weitergabe bleibt danach unverändert. |
| 2 | nein | ja | ja | mittel | `tests/test_scout_kw_doppelversand.py:413-431` | T9 misst nicht, was die Spec verlangt. Die Spec verlangt, dass der Test prüft, dass `LAB_DIR/pipeline_runs.log` eine Zeile mit `EMAIL_EXIT=3` enthält. Der Test prüft nur, dass `send_scout_email.py` Exit 3 liefert. Ein Test, der nichts misst, ist ein Befund. | T9 so ergänzen, dass `run_scout_pipeline.sh` mit einem kontrollierten `send_scout_email.py`-Aufruf ausgeführt wird (z. B. durch Override von `PYTHON` oder Mock des Scout-Schritts), und dann `pipeline_runs.log` auf `EMAIL_EXIT=3` prüfen. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** Vollständiger E2E-Lauf der Pipeline mit `LAB_DIR=/tmp/scout_e2e_test bash scripts/run_scout_pipeline.sh` (wie im Handover „Hawe muss ausführen“ beschrieben). Danach `cat /tmp/scout_e2e_test/pipeline_runs.log` prüfen, ob eine Zeile mit `EMAIL_EXIT=3` steht.
- **Braucht externe Quelle:** Keine. Alle Prüfungen können lokal erfolgen.

## Abweichende Meinung

- **T9 „Hawe-muss-ausführen-Variante“:** Das Handover argumentiert, dass ein vollständiger E2E-Lauf nicht im unittest möglich sei, weil der Scout Internet braucht. Das ist korrekt, aber die Spec bietet eine Alternative an: „Der Test prüft nur die Weiterleitung des Exit-Codes von `send_scout_email.py` (Subprozess), nicht den gesamten Pipeline-Lauf.“ Das reicht aber nicht, um die Log-Datei zu prüfen. Ein Shell-Test, der `run_scout_pipeline.sh` mit einem kontrollierten `send_scout_email.py`-Aufruf ausführt (z. B. durch Override von `PYTHON`), wäre möglich und hätte die Spec erfüllt. Ich hätte T9 so umgesetzt.
