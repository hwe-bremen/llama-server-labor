# Qwen3-Coder-Next 80B als Umsetzer, Lauf 2 (19./20.10.2026, Claude)

Gleiche Aufgabe wie Lauf 1 (`k4next_ergebnis/`), Worktree `../llama-server-k4next2` auf `818aa5d` + korrigierte Spec.
Unterschiede: Kontext 131072 (opencode.json-Limit ebenso), Cache auto = 20 GiB, Agent „umsetzung" (fragt bei bash).
Eingriff Hawe 22:14: Klärung T7 (echte Pipeline in Wegwerf-Ordner mit Platzhaltern) + „bei Unklarheiten selbst entscheiden".

## Zeitprofil (Server-Log serve_20261019T211332_c20.log)
| | Lauf 1 (65k, 18 GiB) | Lauf 2 (131k, 20 GiB) |
|---|---|---|
| aktive Zeit | ~7,5 h | ~7,4 h (74 min abends + ~6,1 h am 20.10.; Nacht im Wartezustand auf Freigabe) |
| Prompt einlesen | 188 min | 128 min |
| Generieren | 77 min / 34k Token | 101 min / 44k Token (7,4 tok/s, Cache 85,5 %) |
| größter Kontext | ~63k | 122k |
- Größerer Kontext beseitigt die teuren Compactions weitgehend (−60 min Prefill), das Modell generiert aber mehr. 5 große Prefills ~12,6k (wiederholtes Lesen der Spec), 1× 35k nach der Nacht (Ursache offen).
- Am Ende Testwiederholungen ohne Abschluss (letzte 20 Anfragen je 17–900 neue Token), von Hawe abgebrochen.

## Verhalten (mit Mocks geprüft)
| Fall | Lauf 1 | Lauf 2 |
|---|---|---|
| D1 SMTP-Fehler → nächster Lauf sendet nach | ✓ | ✓ |
| D2 Nachtrag-Mail nur mit Neuem | ✓ | ✗ **schickt Erstbericht erneut und lässt Nachtrag 1 weg** (Off-by-one in `build_email_message`: `parts[0]` immer, Nachträge erst ab Index `lauf_nr`) → neue Einträge kommen nie an |
| Zwei offene Nachträge | ✗ einer pro Lauf | ✗ nur Nachtrag 2 gesendet, Nachtrag 1 verloren, Merker 2 |
| Alt-Zeile `KEY DATUM` | ✓ | ✗ zählt nicht → Erstbericht doppelt (im Handover als bekannt genannt) |
| „## Nachtrag KW" im Text | ✓ | ✓ |

## Tests und Handover
- Eigene Tests: 10; laufen in der VM 9/10 — **T3 ruft `get_password()` ungemockt auf**, liest am Mac also den echten Schlüsselbund (Kopfkommentar behauptet „Mocken get_password()"). Am Mac deshalb grün.
- T7 prüft trotz ausdrücklicher Klärung weiterhin nur `send_scout_email.py`, nicht die Pipeline.
- Kein Test auf den Inhalt der Nachtrag-Mail → D2-Fehler unentdeckt.
- `save_report()` fehlt erneut (Anhängen inline in `main()`), Claudes Referenz-T1/T9/T8 scheitern daran.
- Handover: „Alle 10 Tests bestehen" stimmt am Mac, „Umsetzung vollständig" stimmt nicht (D2).

## Einordnung
Lauf 2 ist inhaltlich schlechter als Lauf 1 (D2 kaputt, T3 mit echtem Schlüsselbund), bei gleicher Dauer.
Qwen3-Next als Umsetzer in OpenCode: derzeit weder schneller noch verlässlicher als Qwen3.6. Größe/Breite zahlt sich bei dieser Aufgabe nicht aus.
