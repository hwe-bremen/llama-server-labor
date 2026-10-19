# Verdikt: eval_scout

- **Spec:** keine (Anforderungen im Handover)
- **Handover:** `role-split/eval/scout_20261014/handover_20261014_llm_scout_automation.md`
- **Datum:** 2026-10-18
- **Modell:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `role-split/eval/scout_20261014/llm_scout.py`, `role-split/eval/scout_20261014/llm_scout.plist`, `role-split/eval/scout_20261014/logs/llm_scout_out.log`, `role-split/eval/scout_20261014/logs/llm_scout_err.log`

Dateiname: `verdict_20261014_eval_scout_qwen36-27b_v2.md`

## Ergebnis

**NACHBESSERN** – Anforderung 1b (sys.exit(1) bei Fehler) ist teilweise nicht erfüllt: Ein LLM-Timeout endet mit Exit-Code 0 und bleibt für launchd unbemerkt. Die Logs belegen, dass dies in der Praxis auftritt.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1a | os.makedirs vor Report-Schreiben | erfüllt | `llm_scout.py:305` |
| 1b | sys.exit(0) bei Erfolg, sys.exit(1) bei Fehler | **teilweise erfüllt** | `llm_scout.py:220–231` (LLM-Fehler → Exit 0) |
| 1c | Shebang | erfüllt | `llm_scout.py:1` |
| 2 | chmod +x | erfüllt | Handover (ls -la Ausgabe) |
| 3 | launchd plist | erfüllt | `llm_scout.plist` |
| 4 | logs/ Ordner | erfüllt | `logs/` existiert mit Log-Dateien |

## Handover gegen Code

- **„os.makedirs vor Report-Schreiben, Zeile 304"**: Der Code zeigt Zeile 305 (Zählung kann je nach Editor variieren). Inhalt stimmt: `os.makedirs(REPORT_DIR, exist_ok=True)` vor dem `open()`. Keine Abweichung.
- **„sys.exit(0) bei Erfolg, sys.exit(1) bei Fehler, Zeilen 270-318"**: Der try/except-Block existiert. Aber `call_llm_for_evaluation()` fängt Exceptions intern ab und gibt einen Fehler-String zurück. Dieser wird als Report gespeichert und endet mit `sys.exit(0)`. Das Handover erwähnt diese Lücke nicht.
- **„getestet: py_compile OK"**: Ausgabe vorhanden, Test belegt. Aber py_compile prüft nur Syntax – kein Test für Exit-Codes oder Fehlerbehandlung.
- **„chmod +x erfüllt, -rwxr-xr-x"**: ls-Ausgabe im Handover belegt. Im eval-Ordner nicht überprüfbar (keine Metadaten), aber plausibel.
- **„Spec-Datei existiert nicht"**: Im Handover selbst dokumentiert. Keine Abweichung.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | **hoch** | `llm_scout.py:220–231` | LLM-Timeout/ConnectionError wird in `call_llm_for_evaluation()` abgefangen, Fehler-String zurückgegeben. `main()` speichert ihn als Report und beendet mit `sys.exit(0)`. launchd erkennt keinen Fehler. Logs bestätigen: err.log enthält Timeout, out.log endet mit `--- Skript beendet ---`. | `call_llm_for_evaluation()` soll bei API-Fehlern eine Exception werfen. Oder `main()` prüft den Report-Inhalt auf Fehlermarker und beendet dann mit `sys.exit(1)`. |
| 2 | nein | nein | nein | niedrig | `llm_scout.py:27,305` | `REPORT_DIR.mkdir()` auf Modulebene (Import) und `os.makedirs()` in `main()` erstellen denselben Ordner doppelt. Nicht schädlich, aber redundant. | Eine der beiden Stellen entfernen – entweder Modulebene (dann erst beim ersten Lauf) oder nur in `main()`. |
| 3 | nein | ja | nein | niedrig | Handover | Nur `py_compile` als Test. Kein Test prüft, ob `sys.exit(1)` bei einem Fehlerfall tatsächlich aufgerufen wird. Der LLM-Timeout-Fehler wäre durch einen solchen Test auffällig gewesen. | Mindestens einen Test für den Fehlerpfad (z. B. llama-server nicht erreichbar → Exit-Code prüfen). |

## Nicht geprüft

- **Kann Hawe selbst prüfen:** `launchctl load` und `launchctl kickstart` zum echten launchd-Test; Dateirechte mit `ls -la` im Projektordner prüfen; Report-Inhalt in `~/lab/weekly-reports/` ansehen.
- **Braucht externe Quelle:** Keine.

## Abweichende Meinung

- **Interpreter in der plist:** Das Handover begründet die Wahl des venv-Interpreters (`/Users/.../.venv/bin/python3`) statt Shebang+Skript damit, launchd setze keine `$PATH`. Das ist korrekt. Alternativ wäre ein `EnvironmentVariables`-Block mit `PATH` möglich gewesen, aber der venv-Interpreter ist die robustere Wahl. Kein Einwand.
- **LAB_DIR-Default:** Das Handover dokumentiert korrekt, dass ohne `LAB_DIR` die DB in `~/lab/` landet. Ich halte das für ein echtes Problem im Produktivbetrieb: launchd setzt keine benutzerdefinierten Variablen, also landet die DB immer in `~/lab/`, es sei denn, die plist wird erweitert. Das Handover listet es als „offener Punkt" – ich würde es als **muss-behoben** einstufen, bevor der Job aktiviert wird. Aber da es kein Teil der expliziten Anforderungen ist, stufe ich es hier als Abweichende Meinung ein.
