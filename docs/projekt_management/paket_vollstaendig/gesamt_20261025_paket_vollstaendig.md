# Gesamtbefund: paket_vollstaendig

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-27 08:12). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261025_paket_vollstaendig_qwen36-35b_3.md` | NACHBESSERN |
| `verdict_20261025_paket_vollstaendig_qwen36-35b_betrieb_3.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261025_paket_vollstaendig_qwen36-35b_3.md` | hoch | ja | `kette.py:394` | Gegenprobe ignoriert `.md`-Dateien unter `role-split/kette/` |
| `verdict_20261025_paket_vollstaendig_qwen36-35b_3.md` | mittel | ja | `test_paket_vollstaendig.py:180` | Test `test_t7` prüft nicht die neue Logik |
| `verdict_20261025_paket_vollstaendig_qwen36-35b_betrieb_3.md` | niedrig | nein | `kette.py:640` | mittel |
| `verdict_20261025_paket_vollstaendig_qwen36-35b_betrieb_3.md` | niedrig | nein | `kette.py:745-756` | niedrig |
