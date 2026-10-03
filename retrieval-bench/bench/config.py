"""Zentrale Pfade und Einstellungen fuer retrieval-bench.

Alles relativ zum Ordner retrieval-bench/, damit das Projekt auf MacBook
und Mac mini ohne Anpassung laeuft. Werte sind per Umgebungsvariable
ueberschreibbar (RB_*).
"""
from __future__ import annotations

import os
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = BENCH_ROOT / "corpus" / "henne"
CRAWL_DIR = CORPUS_ROOT / "crawled_data"
HIGH_LEVEL_DIR = CORPUS_ROOT / "high_level"
QA_DIR = CORPUS_ROOT / "qa_booster"
ARTIKEL_XLSX = CORPUS_ROOT / "artikel.xlsx"
REFERENCE_DB = CORPUS_ROOT / "reference_embeddings.db"

CACHE_DIR = BENCH_ROOT / "cache"
RESULTS_DIR = BENCH_ROOT / "results"
EVAL_FILE = BENCH_ROOT / "eval" / "questions.jsonl"

# Embedding-Endpunkt: OpenAI-kompatibel (llama-server Router oder anderes Backend).
# Welches GGUF als Embedding-Modell laeuft, entscheidet models.ini / der Router.
EMBED_BASE_URL = os.environ.get("RB_EMBED_BASE_URL", "http://127.0.0.1:8080/v1")
EMBED_MODEL = os.environ.get("RB_EMBED_MODEL", "")  # leer = Server-Default
EMBED_BATCH = int(os.environ.get("RB_EMBED_BATCH", "32"))

# Qdrant: ":memory:" = eingebettet im Prozess (kein Server noetig),
# sonst z.B. "http://127.0.0.1:6333" fuer einen Docker-/Binary-Server.
QDRANT_URL = os.environ.get("RB_QDRANT_URL", ":memory:")

# Lab-Chunking
LAB_CHUNK_CHARS = int(os.environ.get("RB_LAB_CHUNK_CHARS", "1200"))
LAB_CHUNK_OVERLAP_PARAS = int(os.environ.get("RB_LAB_CHUNK_OVERLAP_PARAS", "1"))

# Reciprocal Rank Fusion
RRF_K = int(os.environ.get("RB_RRF_K", "60"))
