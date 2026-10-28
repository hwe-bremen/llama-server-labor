# Gesamtbefund: lauf_status

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-28 12:56). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261028_lauf_status_qwen36-35b.md` | PASS |
| `verdict_20261028_lauf_status_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261028_lauf_status_qwen36-35b.md` | niedrig | nein | `automatik.py:103` | Unpräziser Text im nächsten Schritt |
| `verdict_20261028_lauf_status_qwen36-35b.md` | niedrig | nein | `automatik.py:94` | Unpräziser Text in Fehlermeldung |
| `verdict_20261028_lauf_status_qwen36-35b_betrieb.md` | niedrig | ja | `automatik.py:121` | Fehler im Hardcoded-String |
