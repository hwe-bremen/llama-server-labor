# Kette 6 mail_planung (22./23.10.2026)
Aufgabe: Werkzeug holt Mails per IMAP (nur lesend), lokales Modell extrahiert Aufgaben/Termine/Entscheidungen/Fragen in eine Planungsdatei.
Ergebnis: nicht bestanden – Giftmail und JSON-Code-Zäune gingen am Review Lauf 1 vorbei.

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| „Giftmail": Auswertung scheitert dauerhaft → Mail bleibt offen, jeder Lauf neu, unbemerkt | wiederkehrender Fehler ohne Sichtbarkeit | Claude; später Lauf 2 „Betrieb" |
| Modell-JSON mit Code-Zäunen, ohne `enable_thinking: false` | echtes Modell ≠ Attrappe | Claude; Lauf 2 |
| Prüfung vor dem Marker suchte nur `"## {date}"` | Absicherung läuft ins Leere | **lokales Review** (erstmals, Pflichtfrage d) |
| Umsetzer legte eigene Übergabe-Datei an | Dateiname nicht exakt | `kette.py` (danach `datei_suchen` exakt) |

## Regeln daraus
- R21 dauerhafte vs. vorübergehende Fehler (umgesetzt: Block „⚠ Auswertung fehlgeschlagen" + Marker; transient → Exit 1, kein Marker)
- R28 Qwen3.x per API · R17 Lauf 2 „Betrieb" + `kette.py zusammenfuehren` (umgesetzt, RUNBOOK Phase D)

## Sonst bemerkenswert
- Mail-Inhalte sind nicht vertrauenswürdig (Prompt-Injection): Das auswertende Modell hat keine Werkzeuge und liefert nur Daten.
- Unter dem Mock blieb ungeprüft: echter IMAP-Server + echtes Modell → Anlass für K7.
