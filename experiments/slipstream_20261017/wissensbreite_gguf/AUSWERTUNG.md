# Wissensbreite GGUF — Auswertung (20.10.2026)

Volle Auswertung mit Teil-B-Begründungen nur im Claude-Projekt (`claude/wissensbreite-gguf-schluessel.md`,
`claude/wissensbreite-gguf-quelle.md`), weil sie die richtigen Antworten enthält. Hier: Punkte und Schlüsse.

## Teil 1 — ohne Quelle (Wissen aus dem Gedächtnis)

| Modell | Teil A je Lauf (max 32) | Teil B je Lauf (max 7) | Gesamt je Lauf | Median | Läufe ohne Code | Erfindungen Teil B (3 Läufe: Fallen + falsche IDs) |
|---|---|---|---|---|---|---|
| Qwen3.6-27B | 0 · 15 · 0 | 2 · 1,5 · 2 | 2 · 16,5 · 2 | **2** | 1 (Schleife) | 6 + 13 = 19 |
| Qwen3.8-27B | 18 · 23 · 0 | 2,5 · 2,5 · 2,5 | 20,5 · 25,5 · 2,5 | **20,5** | 1 (Schleife) | 6 + 6 = 12 |
| Mellum2-12B | 0 · 0 · 0 | 0 · 0 · 0 | 0 · 0 · 0 | **0** | 2 (Schleife) | 5 + 14 = 19 |
| Qwen3-Coder-Next 80B | 0 · 0 · 0 | 2 · 2 · 2 | 2 · 2 · 2 | **2** | 0 | 6 + 12 = 18 |

Siegkriterium „Qwen3-Next gewinnt klar" (vorab festgelegt):
1. Median ≥ 4 über Qwen3.6 → **nein** (2 gegen 2)
2. Quant-Größen auf D1 in ≥ 2/3 Läufen → **nein** (kein Modell, kein Lauf)
3. Erfindungen ≤ Qwen3.6 → ja, knapp (18 gegen 19)

**Kein Gewinn. Nachtlauf (Schritt 2) entfällt vorerst.**

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

## Teil 2 — mit Quelle (Formatbeschreibung aus gguf-py im Prompt, `quelle.md`)

Gleiche Aufgabe, angehängt `quelle.md` (Dateiaufbau + Typ-/Blockgrößen-Tabellen, erzeugt aus gguf-py). Nur Teil A,
2 Läufe je Modell. Erwartungen vorab im Claude-Projekt festgelegt.

| Modell | ohne Quelle | mit Quelle | Sekunden je Antwort mit Quelle |
|---|---|---|---|
| Qwen3.6-27B | 0 · 15 · 0 | **32 · 32** | 322 / 295 |
| Qwen3.8-27B | 18 · 23 · 0 | **32 · 32** | 313 / 324 |
| Qwen3-Coder-Next 80B | 0 · 0 · 0 | **0 · 27** | 302 / 206 |

- Qwen3.6 und Qwen3.8: 4 von 4 Läufen fehlerfrei, keine Schleife.
- Qwen3-Next Lauf 1: fehlende Klammer → nicht lauffähig; dazu UINT8/UINT16 als 4 Byte gelesen und Datenbeginn falsch
  abgeleitet, obwohl die Quelle vorlag.
- Qwen3-Next Lauf 2: Kopf, Typen, Tensor-Infos, Alignment und Quant-Größen auf allen Dateien richtig; Arrays eine Ebene
  zu tief verschachtelt (Schema-Abweichung) und Dateiende als Summe der Größen statt über die Offsets (Quelle Punkt 7
  ignoriert) → 27/32. Das Phantomfeld aus Teil 1 ist weg.

## Folgerung

1. Ohne Quelle war **Erinnern** der Engpass — bei allen Modellen. Mit 2 200 Zeichen Formatbeschreibung im Prompt
   erreichen die 27B-Modelle das Maximum. Konstanten (Typ-IDs, Blockgrößen, Flags) gehören als Quelle in den Kontext;
   ein größeres Modell ersetzt das nicht.
2. Mit Quelle setzt **Qwen3-Next schlampiger um** als Qwen3.6/3.8 (Syntaxfehler, Schema-Abweichung, Vorgabe übergangen).
   Kein Hinweis auf einen groben Defekt durch Slipstream (Ausgaben kohärent); ein feiner Qualitätsverlust wäre nur
   per Vergleich mit Temperatur 0 nachweisbar.

## Vorbehalte

Eine Aufgabe, ein Gebiet, 3 bzw. 2 Läufe je Modell bei Temperatur 0,2, ohne Thinking. Qwen3-Next lief mit
llama-server-Standard-Sampling, die Router-Modelle mit ihren Presets (top-k 20, top-p 0.95, min-p 0); Temperatur
für alle gleich. D4 enthält MXFP4-Tensoren (in der Quelle enthalten, mit Quelle von allen richtig gerechnet).
