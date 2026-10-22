# Verdikt: scout_bericht_ueberschreiben (Probe-Review)

**Modell:** qwen36-35b  
**Datum:** 2026-10-22  
**Geprüftes Paket:** experiments/probe_k4/review_paket_probe.md

## Ergebnis

**NACHBESSERN**

Zwei Befunde „hoch" (Unbemerkt: ja), einer „mittel".

## Befunde

| Nr. | Anfor. | Schwere | Datenverl. | Unbemerkt | Harte Vorg. | Begründung |
|-----|--------|---------|-----------|-----------|-------------|------------|
| B1 | A3 | hoch | nein | ja | ja | Spec sagt „wiederholen (Mail geht)", Code liefert Exit 0 (keine Mail). Crash nach `record_sent_week()`: `last_sent >= expected_lauf`, kein Wiederholungsversuch. |
| B2 | A4 | hoch | nein | ja | ja | T7 prüft nur `bash -n` und Exit 3 von `send_scout_email.py`. Die Weitergabe an launchd wird nicht getestet. |
| B3 | A2 | mittel | nein | nein | nein | `count_report_runs()` nutzt `content.count("## Nachtrag KW")` — wenn LLM-Output diesen Substring enthält, wird falsch gezählt und ein Nachtrag übersprungen. Kein Test dafür. |

## Anforderungen einzeln

**A1 (Zweitlauf hängt nach): Erfüllt.**
- a) Erzwungen: Ja. `exists()` → `'a'`, sonst `'w'`. (llm_scout.py Z. 326–337)
- b) Leer: Leere Datei existiert → angehängt, Erstbericht byte-identisch (leer).
- c) Nie gezeigt: Nein. Nachtrag in der Nutzer-Datei.
- d) Ins Leere: Nein. `exists()` ist präzise.
- e) Widersprüche: Nein.

**A2 (Versand-Nachweis pro Lauf): Teilweise erfüllt.**
- a) Erzwungen: Teilweise. `content.count("## Nachtrag KW")` ist lose String-Suche. (send_scout_email.py Z. 291–299)
- b) Leer: Leere Datei → `expected_lauf=1`, korrekt. Altes `.sent_state`-Format → Zeilen ignoriert, Doppel-Mail.
- c) Nie gezeigt: Nein.
- d) Ins Leere: Nein, aber fragil.
- e) Widersprüche: Nein.

**A3 (`lauf_nr` vor Versand): Teilweise erfüllt.**
- a) Erzwungen: Ja. `record_sent_week()` vor `send_email_smtp()`. (Z. 359–364)
- b) Leer/Crash: Crash nach `record_sent_week()`: Exit 0, keine Mail. Spec sagt „wiederholen", Code tut das Gegenteil.
- c) Nie gezeigt: Nein.
- d) Ins Leere: Nein.
- e) Widersprüche: Ja. Spec „Akzeptanz" sagt „wiederholen", „Wichtig"-Abschnitt sagt „keine Mail".

**A4 (Pipeline Exit-Code): Teilweise erfüllt.**
- a) Erzwungen: Nicht geprüft. T7 testet nur `bash -n` und Exit 3. (Test Z. 449–477)
- b) Leer: Nicht geprüft.
- c) Nie gezeigt: Ja. launchd-Fehler bei nicht weitergegebenem Exit-Code.
- d) Ins Leere: Ja. `bash -n` prüft nur Syntax.
- e) Widersprüche: Nein.

**A5 (Trockenlauf isoliert): Erfüllt.**
- a) Erzwungen: Ja. `mode_dry_run()` berührt keine Zustandsdatei. (Z. 366–382)
- b–e: Kein Befund. T5 prüft beide Szenarien.

## Nicht geprüft

- Echter SMTP-Versand (bewusst nicht).
- Echter Scout-Lauf mit API (bewusst nicht).
- `run_scout_pipeline.sh`-Inhalt und launchd-Integration.
- Upgrade-Szenario: alte `.sent_state` → neue (zwei E-Mails pro Woche).
