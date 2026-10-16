# Halluzinations-Probe — Auswertung 16.10.2026

Läufe `20261016_1715` (Rollen-Modus; Qwen3.8 und Gemma dort mit HTTP 500 wegen zwei geladener
27B-Modelle) und `20261016_1801` (Eval-Modus, 1 Modell). Alle mit `--kein-denken`, Fragensatz v1.
Bewertung von Hand (Claude), nicht die Vorsortierung.

E = erfundene Begriffe abgelehnt (von 4), T = Texttreue (von 2).

| Modell | ohne Rolle | mit `research` |
|---|---|---|
| Qwen3.8-27B | E 3, T 2 | E 3, T 2 |
| Qwen3.6-27B | E 2, T 2 | E 3, T 2 |
| Gemma4-26B-A4B | E 2, T 2 | E 2, T 2 |
| Gemma4-31B | E 1,5, T 2 | E 2, T 2 |
| Mellum2-12B (Q4 = Q6) | E 0, T 1 | E 1, T 1 |
| Apertus-8B | E 0, T 0 | E 0, T 0 |

## Befunde

- **Erfundenes Flag `--kv-defrag-turbo` (E2): kein einziges Modell erkennt es.** Alle erklären es
  plausibel neben den echten Defrag-Optionen. Flags/Optionen/Versionen immer gegen `--help`/Doku prüfen.
- **Erfundenes Paper (E4):** nur die Qwen-Familie lehnt ab (Qwen3.6 nur mit Rolle); beide Gemmas
  fassen es selbstsicher zusammen, auch mit Rolle.
- **Texttreue:** alle großen Modelle 2/2. Arbeiten mit vorgelegtem Text ist verlässlich, freies
  Erinnern von Details ist das Risiko.
- **Rolle `research` bei schwachen Modellen schädlich:** Mellum etikettiert Erfundenes als
  „Belegt" mit erfundenen URLs und behauptet eine Websuche. Kennzeichnung ersetzt keine prüfbare Quelle.
- Alle Modelle halten Qwen3 für „noch nicht veröffentlicht" (Trainingsstand) — mit Rolle sagen sie
  dazu, dass es Trainingswissen ist; ohne Rolle teils als „Stand heute".
- Gemma ersetzt das erfundene Modell gern durch ein ebenfalls nicht existierendes („Qwen2.5-Coder-0.1B").
- Vorsortierung (✓?/✗?) lag mehrfach daneben; Muster am 16.10. zweimal erweitert. Bleibt Vorsortierung.

## Folgerung

Für Wissensfragen ohne Quelle: Qwen3.8 oder Qwen3.6 mit Rolle `research`. Gemma nicht für
Literatur-/Faktenfragen ohne Beleg. Mellum/Apertus nicht für Wissensfragen.
