# Verdikt: llm_scout_automation

- **Spec:** keine (Anforderungen direkt aus Handover)
- **Handover:** `handover_20261014_llm_scout_automation.md`
- **Datum:** 2026-10-18
- **Modell:** hawes (Review-Instanz)
- **Geprüfte Dateien:** `llm_scout.py`, `llm_scout.plist`, `logs/llm_scout_out.log`, `logs/llm_scout_err.log`

## Ergebnis

**NACHBESSERN** – Die Anforderung `sys.exit(1) bei Fehler` ist nicht erfüllt, weil `call_llm_for_evaluation` bei Verbindungsfehlern keine Exception wirft und `sys.exit(1)` fehlt. Zudem verweist die plist auf das falsche Skript.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| 1a | os.makedirs vor Report-Schreiben | erfüllt | `llm_scout.py:270` |
| 1b | sys.exit(0) bei Erfolg, sys.exit(1) bei Fehler | nicht erfüllt | `llm_scout.py:195–214` (Fehlerfall in call_llm_for_evaluation) |
| 1c | Shebang vorhanden | erfüllt | `llm_scout.py:1` |
| 2 | chmod +x | erfüllt | Skriptausführung im Log belegt, keine Permission denied |
| 3 | launchd plist | erfüllt, aber mit falschem Pfad | `llm_scout.plist:10` (falscher Skriptpfad) |
| 4 | logs/ Ordner | erfüllt | `logs/` existiert, Dateien vorhanden |

## Handover gegen Code

- Handover behauptet, `sys.exit(1)` sei in Zeile 270–318 eingefügt. Tatsächlich ist der except-Block an Zeile 315 vorhanden, aber `call_llm_for_evaluation` wirft bei Verbindungsfehlern keine Exception (sondern gibt eine Fehlermeldung als String zurück). Deshalb wird `sys.exit(1)` nie erreicht.
- Handover behauptet, die plist sei korrekt umgestellt. Tatsächlich verweist die plist auf `/Users/hans-wernereberhardt/PycharmProjects/llama-server/agents/llm_scout/llm_scout.py`, nicht auf die Datei im eval-Ordner.
- Handover behauptet, `os.makedirs(REPORT_DIR, exist_ok=True)` sei vor dem Schreiben. Das ist korrekt (`llm_scout.py:270`), steht aber **nach** `report_content = call_llm_for_evaluation(...)`, nicht vor dem Abruf der Daten. Das Handover ist irreführend.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | ja | ja | ja | hoch | `llm_scout.py:195–214` | Bei Verbindungsfehlern gibt `call_llm_for_evaluation` eine Fehlermeldung als String zurück, wirft aber keine Exception. In `main()` wird der Rückgabewert direkt in den Bericht geschrieben und `sys.exit(0)` aufgerufen – der Fehler bleibt unbemerkt. | `call_llm_for_evaluation` muss bei Fehler `None` oder `raise` verwenden, `main()` muss prüfen, ob `report_content` eine Fehlermeldung ist, und `sys.exit(1)` aufrufen. |
| 2 | ja | ja | ja | hoch | `llm_scout.py:275–277` | Der Report wird mit einer Fehlermeldung (z. B. „Read timed out") überschrieben, aber das Skript beendet sich mit `sys.exit(0)`. Der alte Bericht geht verloren, der Fehler wird nicht bemerkt. | siehe Befund 1 |
| 3 | nein | ja | ja | hoch | `llm_scout.plist:10` | Die plist verweist auf das falsche Skript (`agents/llm_scout/llm_scout.py` statt `scout_20261014/llm_scout.py`). launchd würde das falsche Skript ausführen, wenn die plist geladen wird. | Plist auf `role-split/eval/scout_20261014/llm_scout.py` aktualisieren. |

## Nicht geprüft

- **Kann Hawe selbst prüfen:**  
  - Startet das Skript mit `python3 llm_scout.py`?  
  - Wie sieht der aktuelle Bericht in `~/lab/weekly-reports/` aus?  
  - Ist die plist mit `launchctl list` geladen?
- **Braucht externe Quelle:**  
  - Die aktuelle Spec-Datei `spec_20261014_llm_scout_automation.md` existiert nicht – keine externen Quellen nötig.

## Abweichende Meinung

- Keine. Die Schwächen sind eindeutig und entsprechen den harten Vorgaben aus dem Handover.
