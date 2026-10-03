# retrieval-bench

Standalone-Experiment: Lohnt sich Hybrid Retrieval (dense + BM25 + RRF) und/oder
Qdrant gegenüber FAISS dense – gemessen am Henne-Korpus (öffentliche Katalog-
daten, Herkunft siehe `corpus/henne/PROVENANCE.md`).

Die Matrix trennt zwei Hebel, die das Ausgangspapier vermischt:

|                 | faiss | qdrant | bm25 | hybrid (qdrant+bm25) | hybrid_faiss (Kontrolle) |
|-----------------|-------|--------|------|----------------------|--------------------------|
| chunking=avai   |       |        |      |                      |                          |
| chunking=lab    |       |        |      |                      |                          |

* **avai** = Chunk-Texte aus `reference_embeddings.db` (exakt die Grenzen aus
  AskValentinAI; nur die Texte, keine Vektoren).
* **lab** = eigenes absatzbasiertes Chunking aus `crawled_data/*.md`.
* Alle Dense-Varianten nutzen dieselben, hier frisch erzeugten Embeddings
  (Cache in `cache/`), daher misst faiss-vs-qdrant nur die Datenbank, nicht das Modell.

## Setup

    bash setup.sh
    source .venv/bin/activate
    python scripts/inspect_corpus.py          # Bestandsaufnahme, rein lesend

## Läufe

    # Pipeline ohne Modell prüfen
    python -m bench.run --chunking lab --retriever bm25 --show 3

    # Echt: llama-server mit Embedding-Modell auf :8080 (RB_EMBED_MODEL setzen, falls Router)
    RB_EMBED_MODEL="<embedding-gguf-id>" python -m bench.run --chunking avai \
        --retriever faiss qdrant bm25 hybrid hybrid_faiss --embedder api

    # Qdrant als Server statt eingebettet
    RB_QDRANT_URL=http://127.0.0.1:6333 python -m bench.run ...

Ergebnisse landen als JSON in `results/`. Metriken: Recall@10, nDCG@10 auf
URL-Ebene, Latenz p50/p95 pro Suche (ohne LLM).

## Offen / nächste Stufen

1. Eval-Set labeln (`eval/README.md`) – ohne Labels sind recall/ndcg `nan`.
2. Embedding-Modell im Router: welches GGUF, und läuft `/v1/embeddings` im
   `--models-preset`-Modus? Muss am Build verifiziert werden.
3. Qdrant-natives Sparse/BM25 statt rank_bm25 (dann echte Qdrant-Hybrid-Query).
4. Reranker als eigene Stufe, erst nach Bewertung von Hybrid.
5. Qdrant Edge als isolierter Versuch (Beta).
