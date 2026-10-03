"""Embeddings erzeugen – OpenAI-kompatibler Endpunkt (llama-server) oder Fake.

Cache: pro (Embedder-Name, Text-Hash) ein Vektor in cache/<name>.npz, damit
wiederholte Laeufe und verschiedene Retriever dieselben Vektoren nutzen und
nicht jedes Mal neu embedden.

Der 'fake'-Embedder liefert deterministische Zufallsvektoren aus dem Text-Hash.
Er ist NUR fuer Pipeline-Tests gedacht; Ergebnisse damit sind inhaltsleer.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import numpy as np

from . import config
from .corpus import Doc


class Embedder:
    name: str = "base"
    dim: int | None = None

    def embed(self, texts: list[str]) -> np.ndarray:  # (n, dim) float32, L2-normalisiert
        raise NotImplementedError

    # -- Cache ------------------------------------------------------------
    def _cache_path(self) -> Path:
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        slug = "".join(c if c.isalnum() or c in "-_." else "_" for c in self.name)
        return config.CACHE_DIR / f"emb_{slug}.npz"

    def embed_docs(self, docs: list[Doc], verbose: bool = True) -> np.ndarray:
        path = self._cache_path()
        cache: dict[str, np.ndarray] = {}
        if path.exists():
            z = np.load(path)
            cache = {k: z[k] for k in z.files}
        missing = [d for d in docs if d.text_hash not in cache]
        if missing:
            t0 = time.perf_counter()
            for i in range(0, len(missing), config.EMBED_BATCH):
                batch = missing[i:i + config.EMBED_BATCH]
                vecs = self.embed([d.text for d in batch])
                for d, v in zip(batch, vecs):
                    cache[d.text_hash] = v
                if verbose:
                    done = min(i + config.EMBED_BATCH, len(missing))
                    print(f"  embed {self.name}: {done}/{len(missing)}", end="\r", flush=True)
            np.savez(path, **cache)
            if verbose:
                print(f"\n  embed {self.name}: {len(missing)} neu in "
                      f"{time.perf_counter() - t0:.1f}s, Cache {path.name}")
        return np.stack([cache[d.text_hash] for d in docs]).astype(np.float32)


def _normalize(a: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(a, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (a / n).astype(np.float32)


class FakeEmbedder(Embedder):
    def __init__(self, dim: int = 64):
        self.dim = dim
        self.name = f"fake{dim}"

    def embed(self, texts: list[str]) -> np.ndarray:
        out = []
        for t in texts:
            seed = int(hashlib.sha1(t.encode("utf-8")).hexdigest()[:8], 16)
            out.append(np.random.default_rng(seed).standard_normal(self.dim))
        return _normalize(np.array(out))


class OpenAICompatEmbedder(Embedder):
    """POST {base}/embeddings  {"model": ..., "input": [...]}"""

    def __init__(self, base_url: str = config.EMBED_BASE_URL, model: str = config.EMBED_MODEL):
        import httpx
        self._client = httpx.Client(base_url=base_url, timeout=120.0)
        self.model = model
        self.name = f"api_{model or 'default'}"

    def embed(self, texts: list[str]) -> np.ndarray:
        payload = {"input": texts}
        if self.model:
            payload["model"] = self.model
        r = self._client.post("/embeddings", json=payload)
        r.raise_for_status()
        data = sorted(r.json()["data"], key=lambda x: x["index"])
        vecs = np.array([d["embedding"] for d in data], dtype=np.float32)
        if self.dim is None:
            self.dim = vecs.shape[1]
        return _normalize(vecs)


def make_embedder(kind: str) -> Embedder:
    if kind == "fake":
        return FakeEmbedder()
    if kind == "api":
        return OpenAICompatEmbedder()
    raise ValueError(f"Unbekannter Embedder {kind!r} (fake|api)")
