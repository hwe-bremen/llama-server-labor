# Gesamtbefund: paket_vollstaendig

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-26 07:55). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261025_paket_vollstaendig_qwen36-35b.md` | NACHBESSERN |
| `verdict_20261025_paket_vollstaendig_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261025_paket_vollstaendig_qwen36-35b.md` | hoch | ja | `kette.py:715-730` | A3 nicht erfüllt |
| `verdict_20261025_paket_vollstaendig_qwen36-35b.md` | hoch | ja | `kette.py:860-862` | A4 nicht erfüllt |
| `verdict_20261025_paket_vollstaendig_qwen36-35b.md` | niedrig | nein | `kette.py:745-750` | A2 teilweise |
| `verdict_20261025_paket_vollstaendig_qwen36-35b_betrieb.md` | niedrig | nein | `kette.py:645-655` | Fremde Erkennung bei gemischten Commits |
| `verdict_20261025_paket_vollstaendig_qwen36-35b_betrieb.md` | mittel | ja | `test_paket_vollstaendig.py:87-90` | Indirekte Tests |
