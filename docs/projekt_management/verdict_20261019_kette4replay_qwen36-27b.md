# Verdikt: kette4 Replay – Scout Bericht Ueberschreiben

- **Spec:** `docs/spec_20261018_scout_bericht_ueberschreiben.md`
- **Handover:** `docs/handover_20261018_scout_bericht_ueberschreiben.md`
- **Datum:** 2026-10-19
- **Modell:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `agents/llm_scout/llm_scout.py`, `agents/llm_scout/week_key.py`, `scripts/send_scout_email.py`, `scripts/run_scout_pipeline.sh`, `tests/test_scout_bericht_ueberschreiben.py`, `docs/spec_20261018_scout_bericht_ueberschreiben.md`, `anforderung_hawe.md`, `README.md`

Dateiname: `verdict_20261019_kette4replay_qwen36-27b.md`

## Ergebnis

**FAIL** – Zwei harte Verstoße gegen die Anforderung: Der Erstbericht kommt in der Nachtrag-Mail zum zweiten Mal an (Doppelversand desselben Inhalts), und nach einem SMTP-Crash geht der Nachtrag nie per Mail an. Kein Test prüft, dass jeder Eintrag genau einmal per Mail ankommt.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Zweitlauf hängt nach, Erstbericht bleibt in Datei | erfüllt | `llm_scout.py:230–244` (`save_report()`) |
| A2 | Jeder Eintrag genau einmal per Mail; bereits gesendeter Bericht nicht erneut | nicht erfüllt | `send_scout_email.py:178–186` (`build_email_message()` liest gesamte Datei) |
| A3 | Zustandszeile vor Versand (Crash-Safety) | teilweise erfüllt | `send_scout_email.py:302` (Zustandszeile vor Versand, aber Nachtrag geht nach Crash nie per Mail) |
| A4 | Pipeline gibt Exit-Code weiter | erfüllt | `run_scout_pipeline.sh:78–88` |
| A5 | Dry-Run isoliert vom Versand-Nachweis | erfüllt | `send_scout_email.py:339–353` (`mode_dry_run()`) |

## Handover gegen Code

- Handover sagt „A2 erfüllt" – Code sendet aber die gesamte Datei (Erstbericht + Nachtrag) in jeder Mail. Handover stimmt nicht mit Code überein.
- Handover sagt „A3 erfüllt" – Code reserviert Zustandszeile vor Versand, aber nach einem SMTP-Fehler geht der Nachtrag nie per Mail. Das ist kein erfüllter Anspruch „jeder Eintrag kommt genau einmal per Mail an".
- Handover listet alle 9 Tests als bestanden – die Ausgabe ist im Handover enthalten. Tests sind belegt.
- Handover sagt „Keine Abweichungen von der Spec" – das stimmt. Aber die Spec selbst widerspricht der Anforderung.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | nein | ja | hoch | `send_scout_email.py:178–186` | `build_email_message()` liest die gesamte Bericht-Datei, inklusive Erstbericht. Wenn die Datei einen Nachtrag enthält, geht der Erstbericht in der Nachtrag-Mail erneut per Mail an. Das widerspricht der Anforderung „jeder bereits gesendete Bericht wird nicht erneut verschickt". | Die Nachtrag-Mail muss nur den neuen Nachtrag enthalten, nicht den gesamten Dateiinhalt. Entweder: Nur den Teil nach dem letzten „---"-Trenner in die Mail packen, oder eine separate Funktion fuer Nachtrag-Mails, die nur den aktuellen Nachtrag liest. |
| 2 | ja | ja | ja | hoch | `send_scout_email.py:302–310` (`mode_normal()`), `send_scout_email.py:256–280` (`record_sent_week()`) | Zustandszeile wird vor dem SMTP-Versand geschrieben. Bei SMTP-Fehler bleibt die Zustandszeile, aber die Mail geht nicht. Ein Neustart erkennt `last_sent >= expected_lauf` und sendet nicht erneut. Der Nachtrag kommt nie per Mail an – das ist Datenverlust aus Sicht der Anforderung „jeder Eintrag kommt genau einmal per Mail an". | Entweder: Zustandszeile erst nach erfolgreichem Versand schreiben (wie in `scout_kw_doppelversand`), oder einen Wiederholungsmechanismus einbauen, der bei fehlender Mail nach einem Crash den Nachtrag erneut sendet. |
| 3 | nein | ja | ja | hoch | `tests/test_scout_bericht_ueberschreiben.py:177–216` (T3) | T3 schreibt das falsche Verhalten als Test-Erwartung fest: Nach SMTP-Fehler + Zustands-Reservierung wird kein Zweitversand erwartet. Das ist genau das Verhalten, das der Anforderung widerspricht (Befund 2). Der Test validiert Datenverlust. | T3 muss so geaendert werden, dass nach einem SMTP-Fehler die Zustandszeile rueckgenommen wird oder der naechste Aufruf den Versand wiederholt. Alternativ: T3 prueft, dass die Zustandszeile erst nach erfolgreichem Versand geschrieben wird. |
| 4 | nein | ja | ja | hoch | `tests/test_scout_bericht_ueberschreiben.py` (kein Test) | Kein Test prueft, dass eine Nachtrag-Mail nicht den Erstbericht enthaelt. Die Anforderung „jeder Eintrag kommt genau einmal per Mail" wird fuer den Mail-Inhalt nicht getestet. Wenn jemand die Mail-Logik aendert, so dass sie nur den Nachtrag sendet, gibt es keinen Test, der das prueft. | Einen Test hinzufuegen, der eine Nachtrag-Mail aufbaut und prueft, dass der Erstbericht-Inhalt nicht enthalten ist. Alternativ: Einen Test, der `build_email_message()` mit einer Datei mit Nachtrag aufruft und prueft, dass nur der Nachtrag im Body ist. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** Einen echten Pipeline-Lauf mit zwei Läufen in derselben Woche ausführen und prüfen, ob die zweite Mail den Erstbericht enthält. Gegenprobe mit `kette.py gegenprobe` auf Commit `818aa5d`.
- **Braucht externe Quelle:** Keine. Alle Befunde sind aus Code und Anforderung ableitbar.

## Abweichende Meinung

- **A3 – Zustandszeile vor Versand:** Die Spec bricht bewusst die Anforderung von `scout_kw_doppelversand` („Zustandszeile nur nach `sendmail()`") auf. Ich halte das für falsch. Bei einfachen Wochenberichten (kein Nachtrag) ist die Nach-Versand-Logik korrekt: Crash → keine Zustandszeile → nächster Lauf sendet erneut → kein Datenverlust. Bei Nachträgen argumentiert die Spec, dass der Scout keine neuen Items findet und daher keinen neuen Bericht schreibt. Das ist aber irrelevant: Die Datei hat den Nachtrag schon, und `send_scout_email.py` sendet sie einfach erneut. Es gibt keinen Datenverlust, wenn die Zustandszeile nach dem Versand kommt. Die Spec hat hier ein falsches Szenario konstruiert.

- **A2 – Doppelversand des Erstberichts:** Die Spec erkennt das Problem nicht. Sie sagt „Ein URL-Item, das in Lauf 1 bewertet und gemailt wurde, wird in Lauf 2 nicht erneut gemailt." Das ist eine Umdeutung der Anforderung von „URL-Item nicht doppelt bewerten" zu „Mail-Inhalt". Die Anforderung ist aber über den Mail-Empfang formuliert: „jeder gefundene Eintrag soll genau einmal per Mail bei mir ankommen". Der Erstbericht kommt in der Nachtrag-Mail zum zweiten Mal an.

## Mechanisches Urteil (kette.py)

_2026-10-19 09:23_

```
Modell-Urteil:       FAIL
Regel-Urteil:        NACHBESSERN
Es gilt:             FAIL
  Befunde hoch: 1, 2, 3, 4
  Anforderungen offen: A2: nicht erfüllt; A3: teilweise erfüllt
  Modell strenger als die Regel -- Begruendung im Verdikt lesen.
```
