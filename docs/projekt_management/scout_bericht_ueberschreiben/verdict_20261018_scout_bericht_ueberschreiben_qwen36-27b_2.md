# Verdikt: scout_bericht_ueberschreiben

- **Spec:** `spec_20261018_scout_bericht_ueberschreiben.md`
- **Handover:** `handover_20261018_scout_bericht_ueberschreiben.md`
- **Datum:** 2026-10-18
- **Modell:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `agents/llm_scout/llm_scout.py` (vollständig), `scripts/send_scout_email.py` (vollständig), `tests/test_scout_bericht_ueberschreiben.py` (vollständig), `git diff` gegen 818aa5d

Dateiname: `verdict_20261018_scout_bericht_ueberschreiben_qwen36-27b_2.md`

## Ergebnis

**NACHBESSERN** – Drei Tests (T1, T4, T7) messen nicht vollständig, was die Spec verlangt. T7 ist der schwerwiegendste Befund: Der Test führt die Pipeline nie aus und prüft nicht die Lauf-Datei.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Zweitlauf hängt Nachtrag an | erfüllt | `llm_scout.py:295-318` (`save_report`) |
| A2 | Versand-Nachweis pro `lauf_nr` | erfüllt | `send_scout_email.py:251-285` (`get_last_sent_lauf_nr`, `count_report_runs`) |
| A3 | `lauf_nr` vor Versand reserviert | erfüllt | `send_scout_email.py:366-367` (Reservierung vor `send_email_smtp`) |
| A4 | Pipeline Exit-Code weiter | erfüllt (Bestand) | `run_scout_pipeline.sh` (keine Änderung im Diff) |
| A5 | Dry-Run isoliert | erfüllt (Bestand) | `send_scout_email.py:380-395` (`mode_dry_run`) |

## Handover gegen Code

- **„A1 erfüllt – `save_report()`"**: Stimmt. Funktion existiert, wird von `main():361` aufgerufen.
- **„A2 erfüllt – `get_last_sent_lauf_nr()`, `count_report_runs()`"**: Stimmt. Beide Funktionen vorhanden.
- **„A3 erfüllt – `record_sent_week(lauf_nr)`, `mode_normal()`"**: Stimmt. Reservierung vor Versand.
- **„A4 erfüllt (Bestand unverändert)"**: Stimmt, kein Diff an Pipeline.
- **„A5 erfüllt (Bestand unverändert)"**: Stimmt.
- **„Keine Abweichungen von der Spec"**: **Falsch.** Siehe Befunde: T1, T4, T7 messen nicht vollständig, was die Spec verlangt.
- **„Getestet (mit echter Ausgabe)"**: Ausgabe aller 9 Tests als „ok" gezeigt. Ich wiederhole den Test nicht, nehme die Ausgabe als Behauptung des Umsetzers.

## Befunde

Für jeden Befund drei Fragen mit ja/nein. Ein „ja" macht den Befund „hoch".

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `tests/test_scout_bericht_ueberschreiben.py:218-252` (T7) | T7 prüft nicht die Pipeline-Lauf-Datei (`pipeline_runs.log`). Der Test führt `send_scout_email.py` direkt auf (Exit 3) und macht `bash -n` (Syntaxcheck) auf `run_scout_pipeline.sh`. Die Pipeline wird nie ausgeführt, die Lauf-Datei wird nie geprüft. Die Spec verlangt explizit: „`LAB_DIR/pipeline_runs.log` enthält eine Zeile mit `EMAIL_EXIT=3`." | Test muss `run_scout_pipeline.sh` als Subprozess ausführen (mit gesteuertem `send_scout_email.py`-Verhalten, z. B. `LLAMA_SERVER_URL` auf tote URL) und die Lauf-Datei auf `EMAIL_EXIT=3` prüfen. |
| 2 | nein | ja | ja | mittel | `tests/test_scout_bericht_ueberschreiben.py:50-73` (T1) | T1 prüft nicht die Dateilänge. Die Spec verlangt: „Die Datei-Länge ist `len(erstbericht) + len(trenner_zeile) + len(nachtrag_header) + len(nachtrag_inhalt)`." Der Test prüft nur `startswith`, `assertIn` Header, `endswith`. Ein versehentliches zusätzliches `\n` bliebe unbemerkt. | Längenprüfung ergänzen: `len(content)` gegen erwartete Summe prüfen. |
| 3 | nein | ja | ja | niedrig | `tests/test_scout_bericht_ueberschreiben.py:155-188` (T4) | T4 kann nicht prüfen, ob `sendmail()` nicht aufgerufen wurde, da er `send_scout_email.py` als Subprozess ausführt. Die Spec verlangt: „`sendmail()`-Mock wird **nicht** aufgerufen." Ein Subprozesstest kann nicht in den Python-Mock eindringen. | Entweder `mode_normal()` als Funktion direkt aufrufen (mit SMTP-Mock) statt als Subprozess, oder die Lücke dokumentieren. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** Gegenprobe mit `kette.py gegenprobe scout_bericht_ueberschreiben --commit 818aa5d` (im Handover als TODO markiert). Echter Pipeline-Lauf mit `bash scripts/run_scout_pipeline.sh`. Echter Versand mit `SCOUT_ALLOW_SEND=1 python3 scripts/send_scout_email.py`.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

- **T7-Testdesign:** Ich halte den Ansatz „nur `bash -n` prüfen" für zu schwach. Die Spec verlangt einen Test, der die Exit-Code-Weiterleitung und die Lauf-Datei misst. `bash -n` prüft nur Syntax, nicht Verhalten. Ein Subprozesstest der Pipeline mit kontrolliertem `send_scout_email.py`-Verhalten wäre machbar (z. B. `LLAMA_SERVER_URL` auf tote URL setzen, Scout endet mit Exit 2, Pipeline schreibt Lauf-Datei). Das wäre ein echter Test statt eines Syntaxchecks.
- **A3 – Zustandszeile vor Versand:** Ich teile die Entscheidung der Spec. Zustandszeile vor Versand ist besser als nach Versand, weil es Datenverlust verhindert. Das Restrisiko „Nachtrag fehlt in der Mail nach Crash" akzeptiere ich ebenfalls.

## Mechanisches Urteil (kette.py)

_2026-10-19 06:53_

```
Modell-Urteil:       NACHBESSERN
Regel-Urteil:        NACHBESSERN
Es gilt:             NACHBESSERN
  Befunde hoch: 1, 2, 3
  Korrektur: Befund 2: als 'mittel' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
  Korrektur: Befund 3: als 'niedrig' eingestuft, aber ja bei Unbemerkt, Harte Vorgabe -> hoch
```
