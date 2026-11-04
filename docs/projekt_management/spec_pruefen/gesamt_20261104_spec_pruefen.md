# Gesamtbefund: spec_pruefen

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-11-04 21:57). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261104_spec_pruefen_qwen36-35b.md` | PASS |
| `verdict_20261104_spec_pruefen_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261104_spec_pruefen_qwen36-35b.md` | hoch | ja | `spec_pruefen.py:236`, `spec_pruefen.py:250` | Ausgabe zeigt immer 'spec_pruefen' statt dynamischem Kurztitel. |
| `verdict_20261104_spec_pruefen_qwen36-35b.md` | niedrig | nein | `spec_pruefen.py:189` | Regex für Quellen-Prüfung ist restriktiver als `quelle_lesen` (erwartet Backticks, `quelle_lesen` könnte auch ohne kommen). |
| `verdict_20261104_spec_pruefen_qwen36-35b_betrieb.md` | niedrig | ja | `spec_pruefen.py:236` | Die Fehlermeldung bei ungültigem Kurztitel ist hardcodiert auf `'spec_pruefen'` statt den übergebenen `<kt>`. Die Spec verlangt: `Kurztitel '<kt>' ungültig...`. Dies ist ein Verstoß gegen die wörtliche Vorgabe in A1. |
| `verdict_20261104_spec_pruefen_qwen36-35b_betrieb.md` | niedrig | nein | `spec_pruefen.py:168` | Die Ausgabe für Schreibbereich unter `PAKET_NIE` verwendet `e.split('/')[0]`. Wenn der Pfad relativ ist (z.B. `role-split/kette/...`), ist das Ergebnis korrekt. Wenn der Pfad absolut ist, ist der erste Teil `/`. Die Spec sagt: `z.B. Schreibbereich unter docs/: docs/x.py`. Dies ist eine Annahme, dass Pfade relativ zum Projektroot oder zumindest so formatiert sind, dass der erste Teil der relevante Ordner ist. Da `kette._schreibbereich` typischerweise relative Pfade zurückgibt, ist dies in der Regel korrekt, aber bei absoluten Pfaden könnte es seltsam aussehen. |
