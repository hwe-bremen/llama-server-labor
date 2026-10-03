"""Retriever hinter einer gemeinsamen Schnittstelle.

  faiss   - FAISS IndexFlatIP (exakte Cosine-Suche auf normalisierten Vektoren)
  qdrant  - Qdrant Dense (eingebettet ':memory:' oder Server per RB_QDRANT_URL)
  bm25    - lexikalisch (rank_bm25, einfache deutsche Tokenisierung)
  hybrid  - Reciprocal Rank Fusion aus qdrant + bm25
  hybrid_faiss - RRF aus faiss + bm25 (Kontrollgruppe: Hybrid ohne Qdrant)

Alle liefern list[Hit] mit doc_id, score, rank (1-basiert).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

import numpy as np

from . import config
from .corpus import Doc
from .embed import Embedder


@dataclass
class Hit:
    doc_id: str
    score: float
    rank: int


class Retriever:
    name = "base"

    def index(self, docs: list[Doc], vectors: np.ndarray | None) -> None:
        raise NotImplementedError

    def search(self, query: str, k: int, qvec: np.ndarray | None = None) -> list[Hit]:
        """qvec: vorberechneter Query-Vektor (spart den Embedding-Roundtrip in der Messung)."""
        raise NotImplementedError


# ------------------------------------------------------------------ dense --

class _DenseBase(Retriever):
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self.docs: list[Doc] = []

    def _qvec(self, query: str, qvec: np.ndarray | None = None) -> np.ndarray:
        if qvec is not None:
            return qvec.astype(np.float32)
        return self.embedder.embed([query])[0].astype(np.float32)


class FaissDense(_DenseBase):
    name = "faiss"

    def index(self, docs, vectors):
        import faiss
        self.docs = docs
        self.idx = faiss.IndexFlatIP(vectors.shape[1])
        self.idx.add(np.ascontiguousarray(vectors, dtype=np.float32))

    def search(self, query, k, qvec=None):
        q = self._qvec(query, qvec)[None, :]
        scores, ids = self.idx.search(q, k)
        return [Hit(self.docs[i].doc_id, float(s), r + 1)
                for r, (s, i) in enumerate(zip(scores[0], ids[0])) if i >= 0]


class QdrantDense(_DenseBase):
    name = "qdrant"
    collection = "henne_bench"

    def index(self, docs, vectors):
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
        self.docs = docs
        url = config.QDRANT_URL
        self.client = QdrantClient(location=url) if url == ":memory:" else QdrantClient(url=url)
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            self.collection,
            vectors_config=VectorParams(size=vectors.shape[1], distance=Distance.COSINE),
        )
        points = [
            PointStruct(id=i, vector=vectors[i].tolist(),
                        payload={"doc_id": d.doc_id, "url": d.url, "source": d.source,
                                 "text": d.text[:500]})
            for i, d in enumerate(docs)
        ]
        for i in range(0, len(points), 256):
            self.client.upsert(self.collection, points[i:i + 256], wait=True)

    def search(self, query, k, qvec=None):
        res = self.client.query_points(self.collection, query=self._qvec(query, qvec).tolist(),
                                       limit=k, with_payload=["doc_id"])
        return [Hit(p.payload["doc_id"], float(p.score), r + 1)
                for r, p in enumerate(res.points)]


# ------------------------------------------------------------------ bm25 ---

_TOKEN = re.compile(r"[a-zäöüß0-9]+(?:[-/,.][a-zäöüß0-9]+)*", re.I)
_PART = re.compile(r"[-/,.]")


def tokenize(text: str) -> list[str]:
    """Kleinschreibung, Umlaute bleiben. Verbundene Begriffe wie 'DPD-Zertifizierung',
    'abc-123' oder '0,75l' liefern das Ganze UND die Teile ('dpd-zertifizierung',
    'dpd', 'zertifizierung'), damit sowohl Artikelnummern als auch getrennt
    geschriebene Komposita matchen. Kein Stemming – Baseline bleibt nachvollziehbar."""
    out = []
    for tok in _TOKEN.findall(text.lower()):
        out.append(tok)
        if _PART.search(tok):
            out.extend(part for part in _PART.split(tok) if len(part) > 1)
    return out


class BM25(Retriever):
    name = "bm25"

    def index(self, docs, vectors=None):
        from rank_bm25 import BM25Okapi
        self.docs = docs
        self.bm = BM25Okapi([tokenize(d.text) for d in docs])

    def search(self, query, k, qvec=None):
        scores = self.bm.get_scores(tokenize(query))
        top = np.argsort(-scores)[:k]
        return [Hit(self.docs[i].doc_id, float(scores[i]), r + 1)
                for r, i in enumerate(top) if scores[i] > 0]


# ---------------------------------------------------------------- fusion ---

def rrf(result_lists: list[list[Hit]], k: int, rrf_k: int = config.RRF_K) -> list[Hit]:
    """Reciprocal Rank Fusion: score = Σ 1/(rrf_k + rank). Rohwerte werden ignoriert."""
    acc: dict[str, float] = {}
    for hits in result_lists:
        for h in hits:
            acc[h.doc_id] = acc.get(h.doc_id, 0.0) + 1.0 / (rrf_k + h.rank)
    ranked = sorted(acc.items(), key=lambda x: -x[1])[:k]
    return [Hit(d, s, r + 1) for r, (d, s) in enumerate(ranked)]


class Hybrid(Retriever):
    def __init__(self, dense: Retriever, lexical: Retriever, candidates: int = 50):
        self.dense, self.lexical, self.candidates = dense, lexical, candidates
        self.name = f"hybrid({dense.name}+{lexical.name})"

    def index(self, docs, vectors):
        self.dense.index(docs, vectors)
        self.lexical.index(docs, None)

    def search(self, query, k, qvec=None):
        return rrf([self.dense.search(query, self.candidates, qvec),
                    self.lexical.search(query, self.candidates)], k)


# --------------------------------------------------------------- factory ---

def make_retriever(kind: str, embedder: Embedder) -> Retriever:
    if kind == "faiss":
        return FaissDense(embedder)
    if kind == "qdrant":
        return QdrantDense(embedder)
    if kind == "bm25":
        return BM25()
    if kind == "hybrid":
        return Hybrid(QdrantDense(embedder), BM25())
    if kind == "hybrid_faiss":
        return Hybrid(FaissDense(embedder), BM25())
    raise ValueError(f"Unbekannter Retriever {kind!r}")


RETRIEVERS = ("faiss", "qdrant", "bm25", "hybrid", "hybrid_faiss")


def timed_search(r: Retriever, query: str, k: int,
                 qvec: np.ndarray | None = None) -> tuple[list[Hit], float]:
    """Reine Suchzeit in ms – ohne Query-Embedding, wenn qvec uebergeben wird."""
    t0 = time.perf_counter()
    hits = r.search(query, k, qvec)
    return hits, (time.perf_counter() - t0) * 1000.0
