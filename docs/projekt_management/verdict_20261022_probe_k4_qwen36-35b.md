# Verdikt: scout_bericht_ueberschreiben (Probe-Review)

**Modell:** qwen36-35b  
**Datum:** 2026-10-22  
**Geprüftes Paket:** experiments/probe_k4/review_paket_probe.md

## Ergebnis

**NACHBESSERN**

Zwei Befunde „hoch" (Unbemerkt: ja): A3-Spec widerspricht sich (Crash-Wiederholung wird nicht umgesetzt), A4-Test prüft nicht die Anforderung. Ein Befund „mittel": A2-Heuristik ist fehleranfällig.

## Befunde

| Nr. | Anforderung | Schwere | Datenverlust | Unbemerkt | Harte Vorgabe | Begründung |
|-----|-----------|---------|-------------|-----------|--------------|------------|
| B1 | A3 | hoch | nein | ja | ja | Spec sagt „wiederholen (Mail geht)", Code liefert Exit 0 (keine Mail). Die Zustandszeile ist geschrieben, `last_sent >= expected_lauf`, kein Wiederholungsversuch. |
| B2 | A4 | hoch | nein | ja | ja | T7 prüft nur `bash -n` und Exit-Code von `send_scout_email.py`. Dass `run_scout_pipeline.sh` den Exit-Code an launchd weitergibt, wird nicht getestet. |
| B3 | A2 | mittel | nein | nein | nein | `count_report_runs()` zählt `content.count("## Nachtrag KW")`. Wenn der LLM-Output diesen Substring enthält, wird falsch gezählt und ein Nachtrag übersprungen. Kein Test dafür. |

## Nicht geprüft

- Echter SMTP-Versand (bewusst nicht, wie im Paket angegeben).
- Echter Scout-Lauf mit GitHub/HF-API (bewusst nicht, wie im Paket angegeben).
- `run_scout_pipeline.sh`-Inhalt und launchd-Integration (nicht im Paket enthalten).
- Upgrade-Szenario: alte `.sent_state` (altes Format) → neue `.sent_state` (zwei E-Mails pro Woche).

## Anforderungen einzeln

**A1** (Zweitlauf hängt nach, statt zu überschreiben): **Erfüllt.**
- a) Erzwungen: Ja. `filepath.exists()` → `open('a')`, sonst `open('w')`. (Code Z. 326–337)
- b) Leerer Fall: Leere Datei existiert → angehängt. Erstbericht bleibt byte-identisch (leer). ✓
- c) Nie gezeigt: Nein. Nachtrag in der Datei, die der Nutzer liest.
- d) Ins Leere: Nein. `filepath.exists()` ist präzise.
- e) Widersprüche: Nein.

**A2** (Versand-Nachweis pro Lauf): **Teilweise erfüllt.**
- a) Erzwungen: Teilweise. `count_report_runs()` nutzt `content.count("## Nachtrag KW")` — eine lose String-Suche, keine strenge Formatprüfung. Wenn der LLM-Output den Substring enthält, wird falsch gezählt. (Code Z. 291–299)
- b) Leerer Fall: Leere Datei → `count` = 0, `expected_lauf` = 1. Korrekt. Altes `.sent_state`-Format → Zeilen ignoriert, Woche erneut gesendet (Doppel-Mail). (Code Z. 267–289)
- c) Nie gezeigt: Nein.
- d) Ins Leere: Nein, aber fragil. `content.count()` findet auch Substrings im Inhalt.
- e) Widersprüche: Nein.
- Test: T4 prüft den Normalfall, aber nicht den Fall, wo der LLM-Output `## Nachtrag KW` enthält.

**A3** (`lauf_nr` vor Versand reserviert): **Teilweise erfüllt.**
- a) Erzwungen: Ja. `record_sent_week(next_lauf)` vor `send_email_smtp(msg)`. (Code Z. 359–364)
- b) Leerer Fall: Crash nach `record_sent_week()`: Zustandszeile existiert, `last_sent >= expected_lauf` → Exit 0, keine Mail. Die Spec sagt „wiederholen (Mail geht)", der Code tut das Gegenteil. (Spec Z. A3 „Akzeptanz: SMTP-Fehler … zweiter Lauf … Exit 0, keine Mail")
- c) Nie gezeigt: Nein.
- d) Ins Leere: Nein.
- e) Widersprüche: Ja. Spec sagt „wiederholen (Mail geht)", Code liefert Exit 0. Die Spec erkennt das später selbst („das bedeutet: keine Mail"), aber die Formulierung „wiederholen" ist falsch. (Spec Z. A3 „Akzeptanz" vs. „Wichtig"-Abschnitt)
- Test: T3 prüft Crash-Szenario und bestätigt Exit 0 beim zweiten Lauf. Der Test ist korrekt, aber die Spec-Beschreibung ist irreführend.

**A4** (Pipeline gibt Exit-Code weiter): **Teilweise erfüllt.**
- a) Erzwungen: Nicht geprüft. T7 testet nur `bash -n` und Exit-Code von `send_scout_email.py` (Exit 3), nicht die Weitergabe an launchd. (Test Z. 449–477)
- b) Leerer Fall: Nicht geprüft.
- c) Nie gezeigt: Ja. Wenn die Pipeline den Exit-Code nicht weitergibt, merkt launchd den Fehler nicht.
- d) Ins Leere: Ja. `bash -n` prüft nur Syntax, nicht das Exit-Code-Handling.
- e) Widersprüche: Nein.

**A5** (Trockenlauf isoliert): **Erfüllt.**
- a) Erzwungen: Ja. `mode_dry_run()` berührt keine Zustandsdatei. (Code Z. 366–382)
- b) Leerer Fall: Keine Datei → Exit 0. ✓
- c) Nie gezeigt: Nein.
- d) Ins Leere: Nein.
- e) Widersprüche: Nein.
- Test: T5 prüft beide Szenarien. ✓

## Abweichende Meinung (qwen36-35b)

Zum bestehenden Verdikt, Befund B1 (A3 Crash-Szenario):

Das bestehende Verdikt bewertet „Datenverlust" als „nein". Ich halte das für falsch, weil die Anforderung wörtlich sagt: „geht etwas verloren" ist das zu verhindernde Szenario. Im Crash-Fall (SMTP-Fehler nach `record_sent_week`) ist die Zustandszeile geschrieben, die Mail nicht gesendet. Der zweite Lauf liefert Exit 0. Der Nachtrag ist im System, aber der Nutzer bekommt ihn **nie**. Das ist inhaltlicher Verlust.

Daher: Datenverlust = **ja** für B1. Das ändert nichts am Urteil (NACHBESSERN bleibt), aber die Schwere-Begründung ist schärfer als im bestehenden Verdikt.
