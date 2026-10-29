# Gesamtbefund: alle_tests

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-29 08:38). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**PASS** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261029_alle_tests_qwen36-35b.md` | PASS |
| `verdict_20261029_alle_tests_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261029_alle_tests_qwen36-35b.md` | niedrig | nein | `scripts/alle_tests.py:142` | Bei TimeoutExpired wird ein simulierter CompletedProcess mit leerer Ausgabe erstellt. Dies ist korrekt laut Spec („Exit-Code zählt", Ausgabe wird separat geholt). Da die Ausgabe beim Timeout eh nicht vollständig ist, ist dies der beste verfügbare Ansatz. |
| `verdict_20261029_alle_tests_qwen36-35b_betrieb.md` | niedrig | nein | `scripts/alle_tests.py:142` | Bei TimeoutExpired wird ein fiktiver CompletedProcess erstellt. stdout/stderr sind leer. Die Ausgabe des Tails ist leer. |
| `verdict_20261029_alle_tests_qwen36-35b_betrieb.md` | niedrig | nein | `scripts/alle_tests.py:137` | Bei der Ausgabe der letzten Zeilen wird `aufruf` erneut aufgerufen. |
| `verdict_20261029_alle_tests_qwen36-35b_betrieb.md` | niedrig | nein | `scripts/alle_tests.py:118` | `subprocess.run` mit `timeout`. |
| `verdict_20261029_alle_tests_qwen36-35b_betrieb.md` | – | nein | – | keine Befunde |
