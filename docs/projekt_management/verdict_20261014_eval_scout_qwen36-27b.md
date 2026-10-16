# Verdikt: eval_scout

- **Spec:** Keine (Anforderungen stammen aus dem Handover)
- **Handover:** `role-split/eval/scout_20261014/handover_20261014_llm_scout_automation.md`
- **Datum:** 2026-10-15
- **Modell:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
- **Geprüfte Dateien:**
  - `role-split/eval/scout_20261014/llm_scout.py`
  - `role-split/eval/scout_20261014/llm_scout.plist`
  - `role-split/eval/scout_20261014/logs/llm_scout_out.log`
  - `role-split/eval/scout_20261014/logs/llm_scout_err.log`

Dateiname: `verdict_20261014_eval_scout_qwen36-27b.md`

## Ergebnis

**NACHBESSERN** – Die strukturellen Anforderungen (makedirs, exit-Codes, Shebang, plist, logs) sind erfüllt. Zwei inhaltliche Mängel erfordern Nachbesserung: (1) LLM-Timeout erzeugt einen falschen Erfolgs-Exit-Code, (2) RSS-Feeds liefern 0 Einträge, was auf tote Quellen oder zu engen Filter hindeutet.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1a | os.makedirs vor Report-Schreiben | erfüllt | `llm_scout.py:300` (Handover sagt 304, leicht ungenau) |
| 1b | sys.exit(0) bei Erfolg, sys.exit(1) bei Fehler | teilweise erfüllt | `llm_scout.py:283,308` exit(0); `llm_scout.py:312` exit(1). LLM-Fehler wird aber als exit(0) beendet (Befund 1) |
| 1c | Shebang | erfüllt | `llm_scout.py:1` |
| 2 | chmod +x | nicht im eval-Ordner überprüfbar | Handover-Test zeigt `-rwxr-xr-x` für Originalpfad; eval-Kopie nicht geprüft |
| 3 | launchd plist | erfüllt | `llm_scout.plist` – Montag 08:00, venv-Interpreter, absolute Pfade |
| 4 | logs/ Ordner | erfüllt | `logs/` existiert mit zwei Logdateien |

## Handover gegen Code

- **Zeilenangabe 1a:** Handover nennt Zeile 304, `os.makedirs` steht in Zeile 300. Unwesentliche Ungenauigkeit.
- **chmod +x:** Testausgabe bezieht sich auf `agents/llm_scout/llm_scout.py` (Originalpfad), nicht auf die eval-Kopie. Die Behauptung ist für den Originalpfad belegt.
- **Plist-Pfade:** Handover sagt „Pfade auf die Dateien in diesem Ordner umgestellt", aber die plist verweist weiterhin auf `/Users/hans-wernereberhardt/PycharmProjects/llama-server/...`. Das ist konsistent mit der Kopfzeile „Eingefrorene Kopie … sonst wörtlich wie am 14.10.2026", aber der Satz „Pfade … umgestellt" ist irreführend. Die Pfade wurden nicht umgestellt.
- **Test-Ausgabe py_compile:** Belegt, bezieht sich auf Originalpfad.
- **Test-Ausgabe PlistBuddy:** Belegt, Inhalt stimmt mit plist überein.

## Befunde

| # | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|
| 1 | hoch | `llm_scout.py:213-232` | `call_llm_for_evaluation()` fängt LLM-Fehler ab und gibt einen Fehlerstring zurück. Dieser wird in Zeile 303-304 als Reportinhalt geschrieben, und das Skript beendet sich mit `sys.exit(0)` (Erfolg). launchd meldet also Erfolg, obwohl keine Evaluation stattgefunden hat. Die Logs bestätigen: `llm_scout_err.log` zeigt Timeout, `llm_scout_out.log` zeigt „Bericht gespeichert" und „Skript beendet". | `call_llm_for_evaluation()` so ändern, dass es bei LLM-Fehlern eine Exception wirft (statt einen Fehlerstring zurückzugeben). Die Exception wird dann vom except-Block in `main()` gefangen und führt zu `sys.exit(1)`. Alternativ: Einen expliziten Check nach Fehlerstring vor dem Report-Schreiben einbauen. |
| 2 | mittel | `logs/llm_scout_out.log` | Alle drei RSS-Feeds (llama.cpp, ollama, transformers) liefern 0 Einträge. Das bedeutet: Der Scout sammelt nur HuggingFace-Daten, aber keine GitHub-Releases. Entweder sind die RSS-URLs tot oder `feedparser` parst sie nicht wie erwartet. | Die drei RSS-URLs manuell im Browser oder mit `curl` prüfen. Falls die URLs tot sind, aktualisieren. Falls die URLs funktionieren, `feedparser.parse()`-Ergebnis debuggen (evtl. `feed.bozo` prüfen). |
| 3 | niedrig | `llm_scout.py:22` | `REPORT_DIR.mkdir(parents=True, exist_ok=True)` läuft auf Modulebene (beim Import), zusätzlich zu `os.makedirs(REPORT_DIR, exist_ok=True)` in `main()` Zeile 300. Nicht schädlich, aber redundant. | Entweder das Modul-Level-`mkdir` entfernen (falls `main()` immer aufgerufen wird) oder das `os.makedirs` in `main()` entfernen. |
| 4 | niedrig | `llm_scout.py:87` | `__import__('datetime').timezone.utc` im Funktionskörper statt einer sauberen Import-Struktur. `timezone` ist nicht auf Modulebene importiert. | `timezone` zum Modul-Import hinzufügen: `from datetime import datetime, timedelta, timezone`. Dann `datetime.now(tz=timezone.utc)` verwenden. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:**
  - `chmod +x` auf der eval-Kopie (`ls -la role-split/eval/scout_20261014/llm_scout.py`)
  - Ob der Report `~/lab/weekly-reports/llm_scout_kw42_2026.md` tatsächlich nur den Fehlerstring enthält
  - Ob die RSS-URLs im Browser erreichbar sind
  - launchd-Ausführung (`launchctl load` + `launchctl kickstart`)
- **Braucht externe Quelle:**
  - Ob die drei GitHub-RSS-URLs (`releases.atom`) noch gültig sind (GitHub hat RSS-Endpunkte in der Vergangenheit geändert)

## Abweichende Meinung

- **Interpreter in plist:** Der Umsetzung hat den venv-Interpreter (`.venv/bin/python3`) statt Shebang + direkter Skript-Pfad gewählt. Das ist die richtige Entscheidung. launchd setzt `$PATH` nicht, `#!/usr/bin/env python3` würde auf System-Python zeigen, der `feedparser` und `requests` nicht hat. Ich hätte den gleichen Weg gewählt.
- **LAB_DIR-Default:** Die Annahme, dass Reports in `~/lab/` landen, ist korrekt dokumentiert. Ich halte es für besser, die plist um einen `EnvironmentVariables`-Block mit `LAB_DIR` zu ergänzen, damit die Reports im Projektordner liegen und versionierbar sind. Das ist jedoch eine Verbesserung, kein Fehler.
