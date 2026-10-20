# Wissensbreite GGUF — Auswertung (20.10.2026)

Volle Auswertung mit Teil-B-Begründungen nur im Claude-Projekt (`claude/wissensbreite-gguf-schluessel.md`),
weil sie die richtigen Antworten enthält. Hier: Punkte und Schlüsse.

## Ergebnis

| Modell | Teil A je Lauf (max 32) | Teil B je Lauf (max 7) | Gesamt je Lauf | Median | Läufe ohne Code | Fallen-Erfindungen (W5+W6, 3 Läufe) |
|---|---|---|---|---|---|---|
| Qwen3.6-27B | 0 · 15 · 0 | 2 · 1,5 · 2 | 2 · 16,5 · 2 | **2** | 1 (Schleife) | 6 / 6 |
| Qwen3.8-27B | 18 · 23 · 0 | 2,5 · 2,5 · 2,5 | 20,5 · 25,5 · 2,5 | **20,5** | 1 (Schleife) | 6 / 6 |
| Mellum2-12B | 0 · 0 · 0 | 0 · 0 · 0 | 0 · 0 · 0 | **0** | 2 (Schleife) | 5 / 6 |
| Qwen3-Coder-Next 80B | 0 · 0 · 0 | 2 · 2 · 2 | 2 · 2 · 2 | **2** | 0 | 6 / 6 |

Siegkriterium „Qwen3-Next gewinnt klar" (vorab festgelegt): Median ≥ 4 über Qwen3.6 → **nein** (2 gegen 2);
Quant-Größen auf D1 in ≥ 2/3 Läufen → **nein** (kein Modell, kein Lauf); Erfindungen ≤ Qwen3.6 → gleich.
**Kein Gewinn. Nachtlauf (Schritt 2) entfällt vorerst.**

## Was passiert ist

- **Qwen3-Next:** alle drei Leser lesen nach den Kopfzählern ein nicht existierendes `alignment`-Feld (u32) und sind
  danach verschoben; ggml-Typtabelle weitgehend erfunden (Q5_0 = 4, „IQ2_0", „IQ5_1", „I4_0_4_4" …), Größen als
  Bits pro Element. Jeder Lauf endet mit Fehler-JSON und Exit 1 → 0 auf allen Dateien. Einziger Pluspunkt:
  3/3 Läufe lieferten Code (keine Schleife).
- **Qwen3.8:** Kopf, Metadaten, Arrays und Tensor-Infos auf den echten Dateien vollständig richtig (6/8 je Datei);
  scheitert an Quant-Größen (erfundene Blockgrößen/Typnamen) und am Alignment 64 der synthetischen Datei.
- **Qwen3.6:** Lauf 2 wie Qwen3.8, aber Arrays falsch (5/8); Lauf 1 bricht ab bzw. läuft in die Zeitgrenze;
  Lauf 3 Endlosschleife in einem Kommentar (Zweierpotenzen bis 16 000 Token).
- **Mellum:** zweimal Schleife ohne Code, einmal Absturz (`print(..., ensure_ascii=False)`); Teil B durchweg falsch.
- **Punkt 7 (Quant-Größen) erreicht kein Modell auf irgendeiner Datei**, obwohl Qwen3.8 und Qwen3-Next in Teil B
  die Q4_K-Blockgröße richtig nennen: Wissen in der Frage-Antwort kommt nicht im Code an.
- Beide Fallen (W5, W6) bedient jedes Modell in jedem Lauf mit einer erfundenen Zahl (Ausnahme: Mellum einmal
  ohne Zahl). Kein Modell sagt „gibt es nicht".

## Vorbehalte

Eine Aufgabe, ein Gebiet, je 3 Läufe bei Temperatur 0,2, ohne Thinking. Schleifenläufe (0 Punkte) bewegen den Median
stark. D4 enthält MXFP4-Tensoren, das spielte hier keine Rolle (alle scheiterten vorher).
