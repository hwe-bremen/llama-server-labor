# Kette 5 search_results_verbessern (21./22.10.2026)
Aufgabe: Scout-Bericht soll je Quelle eine Sektion zeigen und kein Item ohne Begründung verwerfen; Protokoll der Abrufe.
Ergebnis: nicht bestanden – lokales Review meldete in Runde 3 PASS bei hohem Befund.

## Was durchrutschte (oder fast)
| Defekt | Fehlerklasse | Gefunden durch |
|---|---|---|
| Sektionen nur im LLM-Prompt verlangt, im Bericht nicht abgesichert | verlangt, aber nicht abgesichert | Claude |
| Ohne neue Items gar kein Bericht; Test T8 inhaltlich ausgetauscht | leerer Fall | Claude |
| Alter Prompt-Satz „ignoriere kleine Bugfixes" blieb stehen – widersprach „kein Item verwerfen"; weggelassene Items trotzdem als verarbeitet markiert | widersprüchliche Anweisungen / markiert, aber nie gezeigt | Claude |
| Absicherung selbst: `"## Fazit" in …` + exakte Ersetzung `"\n## Fazit\n"` → bei „## Fazit und Empfehlung" alles still verloren | Absicherung läuft ins Leere | Claude (Probelauf mit 7 Fazit-Varianten) |
| Kontext 64K beim Überarbeiten der Spec voll | Kontext | technisch |

## Regeln daraus
- R18 Pflichtfragen (umgesetzt in `prompts/review.md`, `roles/review.md`) · R22 exakte Marker
- R30 Kontext: Review-Paket (umgesetzt: `kette.py paket`), `append_file`, später `replace_in_file`

## Sonst bemerkenswert
- Eng umrissene Korrekturen mit präzisem Prompt setzt Qwen3.6 beim ersten Versuch um; Fehler entstehen beim offenen Umsetzen.
- Werkzeug-Ertrag: `kette.py pruefen` (abgleich + unittest + gegenprobe, Rücksetzpunkt aus Commit „Spec <kurztitel>").
