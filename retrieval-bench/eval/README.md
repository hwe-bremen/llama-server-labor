# Eval-Set

`questions.jsonl` – eine Frage pro Zeile. Ziel: 20–30 Fragen in fünf Typen:

| type         | Bedeutung                                            |
|--------------|------------------------------------------------------|
| sinngemaess  | Frage ohne exakte Begriffe der Zielseite             |
| exakt        | Produktname, Variante, Artikelnummer, Zahl           |
| mehrdeutig   | Begriff mit mehreren Treffern im Sortiment           |
| high_level   | Antwort steckt in high_level/ (PDF/JSON), nicht im Crawl |
| ohne_beleg   | keine Antwort im Korpus – misst, ob Treffer leer/schwach bleiben |

Relevanz wird **pro URL** vergeben, nicht pro Chunk, damit beide Chunking-
Varianten gegen dasselbe Urteil laufen. Grade: 3 direkter Beleg, 2 hilfreich,
1 am Rande. Eine Seite kann mehrere Belege enthalten – das ist gewollt.

Workflow zum Labeln:

    python -m bench.run --chunking lab --retriever bm25 --show 10
    python -m bench.run --chunking lab --retriever faiss --embedder api --show 10

Kandidaten aus beiden Listen ansehen, URL ins `relevant`-Objekt eintragen.
Fragen vom Typ `ohne_beleg` behalten `relevant: {}` dauerhaft; sie werden in
den Metriken ausgelassen und dienen später der Antwortbewertung.
