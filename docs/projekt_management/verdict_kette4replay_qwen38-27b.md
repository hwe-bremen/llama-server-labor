# Verdikt: kette4replay

- **Spec:** `role-split/eval/kette4_20261019/docs/spec_20261018_scout_bericht_ueberschreiben.md`
- **Handover:** `role-split/eval/kette4_20261019/docs/handover_20261018_scout_bericht_ueberschreiben.md`
- **Datum:** 2026-10-19
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `role-split/eval/kette4_20261019/anforderung_hawe.md`, `role-split/eval/kette4_20261019/docs/spec_20261018_scout_bericht_ueberschreiben.md`, `role-split/eval/kette4_20261019/docs/handover_20261018_scout_bericht_ueberschreiben.md`, `role-split/eval/kette4_20261019/agents/llm_scout/llm_scout.py`, `role-split/eval/kette4_20261019/agents/llm_scout/week_key.py`, `role-split/eval/kette4_20261019/scripts/send_scout_email.py`, `role-split/eval/kette4_20261019/scripts/run_scout_pipeline.sh`, `role-split/eval/kette4_20261019/tests/test_scout_bericht_ueberschreiben.py`

## Ergebnis

**FAIL** – Die Mail-Hälfte der Anforderung ist nicht erfüllt. Ein SMTP-Fehler nach der Zustandsreservierung (A3) führt dazu, dass ein Eintrag nie per Mail ankommt: Der Fehlerpfad wird von der Spec als „bekanntes Restrisiko" und „Doppelversand-Risiko" bezeichnet, ist aber ein Ein-Verlust ohne Doppelversand und widerspricht der wörtlichen Vorgabe „jeder gefundene Eintrag soll genau einmal per Mail ankommen". T3 kodiert genau dieses Verhalten als erwartete Test-Expected Value. Zusätzlich nimmt `select_items()` die Top 3 pro Quelle aus *allen* Items ohne DB-Filter, wodurch der Zweitlauf bereits gemailte Items in den Nachtrag aufnimmt und neue Items von der Top-3-Begrenzung verdrängt werden können.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Zweitlauf hängt Nachtrag an, Erstbericht bleibt byte-identisch | erfüllt | `llm_scout.py:256-270` (`save_report`), Tests T1/T9 (`test_scout_bericht_ueberschreiben.py:37-106`) |
| A2 | Versand-Nachweis pro Lauf, nicht pro Woche | teilweise | `send_scout_email.py:296-357` (`get_last_sent_lauf_nr`, `count_report_runs`, `record_sent_week`), `mode_normal` (`send_scout_email.py:359-394`); T3 setzt den Fehlerpfad als „erwartet" fest |
| A3 | Zustandszeile vor Versand reserviert (Crash-Safety) | nicht erfüllt | `send_scout_email.py:396-434` (`record_sent_week` wird vor `send_email_smtp` aufgerufen, `send_scout_email.py:388`); die nachfolgende „alles gesendet"-Prüfung in `mode_normal` (`send_scout_email.py:375-377`) führt dazu, dass nach einem SMTP-Fehler die Mail nie erneut gesendet wird; T3 (`test_scout_bericht_ueberschreiben.py:196-247`) kodiert dieses Verhalten als erwartet |
| A4 | Pipeline gibt Exit-Code unverändert weiter | erfüllt (Bestand) | `run_scout_pipeline.sh:58-62`, `run_scout_pipeline.sh:76-82`; T7 prüft nur `bash -n` und den Exit-3-Code des Email-Skripts, nicht die eigentliche Weitergabe durch die Pipeline |
| A5 | Dry-Run bleibt vom Versand-Nachweis isoliert | erfüllt (Bestand) | `send_scout_email.py:396-412` (`mode_dry_run`), Test T5 |

## Handover gegen Code

- **„A3 erfüllt":** Der Handover behauptet A3 als erfüllt. Der Code stützt die *Reservierung vor Versand* (`record_sent_week` wird auf `send_scout_email.py:388` vor `send_email_smtp` auf `send_scout_email.py:389` aufgerufen), aber der dazugehörige Fehlerpfad – nach einem SMTP-Fehler wird die Mail nie erneut gesendet – widerspricht der harten Vorgabe „jeder Eintrag genau einmal per Mail". A3 ist dadurch nicht als erfüllt zu werten; die Spec hat den Fehlerpfad als „akzeptiertes Restrisiko" markiert, die Anforderung akzeptiert ihn nicht.
- **„A2 erfüllt":** `count_report_runs()` (`send_scout_email.py:330-337`) zählt „## Nachtrag KW"-Header + 1. Das funktioniert nur, solange jeder LLM-Lauf exakt einen neuen Nachtrag mit genau diesem Header erzeugt. Bei leeren LLM-Ausgaben ohne neuen Header oder bei einem fehlenden Bericht im Zweitlauf (Scout findet keine neuen Items → kein Anhängen) ist die Zählung falsch bzw. irrelevant, weil `mode_normal` dann `last_sent >= expected_lauf` trifft und Exit 0 liefert – der neue Eintrag kommt nie per Mail an.
- **Tests „bestanden" mit echter unittest-Ausgabe:** Die unittest-Ausgabe im Handover zeigt 9 Tests, die alle als `ok` gemeldet werden. Die Ausgabe ist plausibel und mit dem Code konsistent (alle Tests prüfen die aktuell vorhandene Logik). Ein möglicher Mangel: T7 (`test_scout_bericht_ueberschreiben.py:251-280`) prüft nicht, dass `run_scout_pipeline.sh` den Exit-Code von `send_scout_email.py` weiterleitet – es wird nur `bash -n` ausgeführt und der Exit-3-Code des Email-Skripts geprüft. Der Test misst also nicht, was A4 verlangt (Exit-Code-Weitergabe durch die Pipeline), und bleibt grün, auch wenn die Pipeline den Exit-Code falsch weitergibt. Das ist ein Test, der nichts misst, aber da die Pipeline-Logik (`set -euo pipefail`, `exit ${EMAIL_EXIT}`) im Code korrekt ist, ist das ein Test-Schwachstelle, kein Code-Defekt.
- **„Keine Abweichungen von der Spec":** Stimmt. Der Code entspricht der Spec in allen dokumentierten Punkten. Die Abweichung ist zwischen Spec und Anforderung, nicht zwischen Code und Spec.
- **Gegenprobe:** Der Handover enthält einen leeren Placeholder für die `kette.py gegenprobe`-Ausgabe (`<Ausgabe>`). Die Gegenprobe wurde nicht ausgeführt. Die Tests sind nicht durch eine Gegenprobe gegen einen älteren Commit belegt.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | ja | ja | ja | hoch | `send_scout_email.py:388` (`record_sent_week` vor `send_email_smtp`), `send_scout_email.py:375-377` (`last_sent >= expected_lauf → Exit 0`); Spec A3 und „Abweichende Meinung"; T3 (`test_scout_bericht_ueberschreiben.py:196-247`) | Nach einem SMTP-Fehler bleibt die Zustandszeile `lauf N` reserviert. Jeder weitere Lauf derselben Woche liefert Exit 0 („alles gesendet"), die Mail wird nie erneut gesendet. Der Eintrag kommt nie per Mail an. Die Spec bezeichnet das als „bekanntes Restrisiko" und „Doppelversand-Risiko" – es ist ein Ein-Verlust ohne Doppelversand und verstößt gegen „jeder gefundene Eintrag soll genau einmal per Mail ankommen". T3 kodiert dieses Verhalten als erwartete Test-Expected Value und bleibt grün. | Zustandszeile erst nach erfolgreichem `sendmail()` schreiben (Rückbau auf die `scout_kw_doppelversand`-Logik). Alternativ: Zustandszeile vor Versand, aber mit einer separaten „pending"-Markierung, die bei einem nachfolgenden Lauf mit gleichem `lauf_nr` und fehlender Mail-Erfolgs-Datei erneut ausgelöst wird. T3 entsprechend ändern: nach SMTP-Fehler soll der zweite Aufruf die Mail erneut versuchen (sendmail 2x), nicht Exit 0 liefern. |
| 2 | ja | ja | ja | hoch | `llm_scout.py:167-172` (`select_items`: `[i for i in items if i['source'] == 'huggingface'][:3]` ohne DB-Filter), `llm_scout.py:301-305` (`mark_as_processed` markiert alle Items in `evaluated`, auch solche, die bereits in `processed_items` stehen) | `select_items()` nimmt die Top 3 pro Quelle aus *allen* Items ohne Rücksicht auf die `processed_items`-DB. Beim Zweitlauf sind dadurch bereits in Lauf 1 gemailte Items in der Auswahl. Der LLM erzeugt einen Nachtrag, der diese Duplikate enthält → doppelte Mail. Gleichzeitig können neue Items von der Top-3-Begrenzung verdrängt werden, weil alte, bereits gemailte Items die Top-3-Plätze belegen → der neue Eintrag fehlt in der Mail. | `select_items()` muss nur Items verwenden, die nicht bereits in `processed_items` stehen. Konkret: die `new_items`-Liste (bereits DB-gefiltert) statt `all_items` übergeben, oder in `select_items()` eine DB-Prüfung einbauen. Alternativ: die DB-Filterung (`is_new_item`) auch in der Selektion anwenden, sodass nur unmarkierte Items in die Top-3-Auswahl kommen. |
| 3 | nein | ja | ja | mittel | `llm_scout.py:289-291` (`if not new_items: conn.close(); sys.exit(0)` vor `save_report`), `send_scout_email.py:375-377` (`last_sent >= expected_lauf → Exit 0`) | Wenn der Zweitlauf keine neuen Items findet (alle URLs in `processed_items`), beendet `llm_scout.py` mit Exit 0, ohne die Datei anzufassen. `send_scout_email.py` zählt die Läufen in der Datei (Erstbericht, keine Nachträge) und vergleicht mit `last_sent`. Ist `last_sent >= 1`, liefert er Exit 0. Jeder Eintrag, der in Lauf 1 gefunden und in die Datei geschrieben wurde, aber per Mail nicht zugestellt wurde (z. B. SMTP-Fehler in Lauf 1), kommt nie per Mail an. Die Datei-Hälfte ist intakt, aber die Mail-Hälfte der Anforderung ist verletzt. | Dies ist ein Teilaspekt von Befund 1. Mit der Korrektur von Befund 1 (Zustandszeile nach Versand oder pending-Markierung) wird dieser Fall abgefangen. Zusätzlich sollte `llm_scout.py` bei fehlenden neuen Items einen Hinweis ausgeben, dass die Mail-Prüfung im Email-Skript stattfindet, um das Verhalten für den Betreiter transparent zu machen. |
| 4 | nein | ja | nein | niedrig | `test_scout_bericht_ueberschreiben.py:251-280` (T7) | T7 prüft `bash -n` (Syntax) und den Exit-3-Code des Email-Skripts, aber nicht, dass `run_scout_pipeline.sh` den Exit-Code von `send_scout_email.py` an launchd weitergibt. Der Test bleibt grün, auch wenn die Pipeline den Exit-Code falsch weitergibt. Er misst also nicht, was A4 verlangt. Die Pipeline-Logik ist im Code korrekt (`set -euo pipefail`, `exit ${EMAIL_EXIT}`), daher ist dies eine Test-Schwachstelle, kein Code-Defekt. | T7 sollte die Pipeline mit einem kontrollierten Email-Skript-Aufruf ausführen (z. B. Scout-Schritt per `LLAMA_SERVER_URL` auf eine tote URL gesetzt, Email-Schritt per Subprozess mit erwartetem Exit-Code) und prüfen, dass der Pipeline-Exit-Code und der Eintrag in `pipeline_runs.log` (`EMAIL_EXIT=<n>`) korrekt sind. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:**
  - Echten Pipeline-Lauf: `bash scripts/run_scout_pipeline.sh` mit `SCOUT_ALLOW_SEND=1` – prüft, ob die Mail tatsächlich ankommt und ob der Zustands-Write nach dem Versand erfolgt (Befund 1).
  - Zweitlauf-Simulation: Manuell eine Bericht-Datei mit einem Nachtrag anlegen, Zustandsdatei mit `lauf 1` belegen, `SCOUT_ALLOW_SEND=1 python3 scripts/send_scout_email.py` ausführen – prüft, ob die Mail für `lauf 2` gesendet wird.
  - `select_items`-Prüfung: `python3 -c "import llm_scout; print(llm_scout.select_items([...]))"` mit einer Mischung aus bereits verarbeiteten und neuen Items – prüft, ob bereits verarbeitete Items in die Auswahl kommen (Befund 2).
  - Testlauf: `python3 -m unittest -v tests/test_scout_bericht_ueberschreiben.py` – die unittest-Ausgabe im Handover ist plausibel, aber die Gegenprobe (älterer Commit) wurde nicht ausgeführt.
- **Braucht externe Quelle:**
  - SMTP-Fehler-Simulation gegen einen echten Gmail-Server (z. B. durch Unterbrechen der Verbindung während des Versands) – die Mock-Tests (T3) können den realen SMTP-Verhalten nicht vollständig abbilden.
  - Prüfung, ob der launchd-Job (`de.hawe.lab.llm_scout`) die Pipeline korrekt startet und den Exit-Code an launchd weitergibt – benötigt Zugriff auf `launchctl`.

## Abweichende Meinung

- **A3 – Zustandszeile vor Versand:** Ich halte die Entscheidung „Zustandszeile vor Versand" für falsch. Die Spec begründet sie mit „Datenverlust-Risiko ohne Reservierung" und „Doppelversand-Risiko mit Reservierung". Aber: (1) Ohne Reservierung crasht die Pipeline zwischen Datei-Schreib und Zustands-Write → Zustandszeile fehlt → nächster Lauf sendet erneut. Das ist ein *Doppelversand*, kein Datenverlust, und ist bei wöchentlichem Betrieb und robustem SMTP akzeptabel. (2) Mit Reservierung crasht die Pipeline zwischen Zustands-Write und `sendmail()` → Zustandszeile existiert, Mail fehlt → nächster Lauf: Exit 0, keine Mail. Das ist ein *Ein-Verlust*, kein Doppelversand. Die Spec hat die beiden Szenarien verwechselt: Sie nennt das erste „Datenverlust" (falsch, es ist Doppelversand) und das zweite „Doppelversand-Risiko" (falsch, es ist Ein-Verlust). Die harte Vorgabe lautet „jeder gefundene Eintrag soll genau einmal per Mail ankommen" – Ein-Verlust ist der gravierendere Verstoß. Ich hätte die Zustandszeile nach dem erfolgreichen `sendmail()` geschrieben (Rückbau auf die `scout_kw_doppelversand`-Logik) und das akzeptierte Restrisiko „Doppelversand bei Crash zwischen Datei-Schreib und Zustands-Write" als bewusste Entscheidung dokumentiert.

- **T3 – SMTP-Fehler nach Zustands-Reservierung:** Der Test kodiert das falsche Verhalten als erwartet. Nach einem SMTP-Fehler soll der zweite Aufruf die Mail erneut versuchen (sendmail 2x), nicht Exit 0 liefern. Mit der Korrektur von Befund 1 (Zustandszeile nach Versand) wäre T3: Zustandsdatei nach SMTP-Fehler hat nur `lauf 1` (die `lauf 2`-Zeile wurde nicht geschrieben, weil `sendmail` fehlgeschlagen ist). Zweiter Aufruf: `last_sent=1 < expected=2` → sendmail wird erneut aufgerufen (sendmail 2x), Zustandszeile `lauf 2` wird geschrieben, Exit 0.

## Mechanisches Urteil (kette.py)

_2026-10-19 10:16_

```
Modell-Urteil:       FAIL
Regel-Urteil:        NACHBESSERN
Es gilt:             FAIL
  Befunde hoch: 1, 2, 3, 4
  Anforderungen offen: A2: teilweise; A3: nicht erfüllt
  Korrektur: Befund 3: als 'mittel' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
  Korrektur: Befund 4: als 'niedrig' eingestuft, aber ja bei Unbemerkt -> hoch
  Modell strenger als die Regel -- Begruendung im Verdikt lesen.
```
