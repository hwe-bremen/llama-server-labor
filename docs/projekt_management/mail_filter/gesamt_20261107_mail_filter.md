# Gesamtbefund: mail_filter

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-11-07 13:25). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**PASS** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261107_mail_filter_qwen36-35b.md` | PASS |
| `verdict_20261107_mail_filter_qwen36-35b_betrieb.md` | PASS |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261107_mail_filter_qwen36-35b.md` | niedrig | nein | `mail_planung.py:252` | Geringfuegige Unsauberkeit |
| `verdict_20261107_mail_filter_qwen36-35b.md` | niedrig | nein | `mail_planung.py:270` | Geringfuegige Unsauberkeit |
| `verdict_20261107_mail_filter_qwen36-35b_betrieb.md` | niedrig | nein | `mail_planung.py:245-256` | `projekt_absender` lädt die Konfigurationsdatei bei *jeder* geprüften Mail neu. Dies ist ineffizient, aber funktional korrekt und verstößt nicht gegen die Spec. |
| `verdict_20261107_mail_filter_qwen36-35b_betrieb.md` | niedrig | nein | `mail_planung.py:688-691` | Der Prompt ist textlich korrekt, aber die Garantie, dass das LLM dem folgt, liegt beim Modell, nicht am Code. |
| `verdict_20261107_mail_filter_qwen36-35b_betrieb.md` | – | nein | – | keine Befunde |
