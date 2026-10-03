"""Recall@k und nDCG@k auf URL-Ebene.

Relevanz wird im Eval-Set pro URL mit Grad angegeben (3 = direkter Beleg,
2 = hilfreich, 1 = am Rande). Mehrere Chunks derselben URL zaehlen als ein
Treffer – so bleibt die Bewertung unabhaengig vom Chunking.
"""
from __future__ import annotations

import math


def urls_in_order(hit_urls: list[str]) -> list[str]:
    seen, out = set(), []
    for u in hit_urls:
        if u and u not in seen:
            seen.add(u)
            out.append(u)
    return out


def recall_at_k(hit_urls: list[str], relevant: dict[str, int], k: int) -> float:
    if not relevant:
        return float("nan")
    top = set(urls_in_order(hit_urls)[:k])
    return len(top & set(relevant)) / len(relevant)


def ndcg_at_k(hit_urls: list[str], relevant: dict[str, int], k: int) -> float:
    if not relevant:
        return float("nan")
    top = urls_in_order(hit_urls)[:k]
    dcg = sum(relevant.get(u, 0) / math.log2(i + 2) for i, u in enumerate(top))
    ideal = sorted(relevant.values(), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def mean(xs: list[float]) -> float:
    xs = [x for x in xs if not math.isnan(x)]
    return sum(xs) / len(xs) if xs else float("nan")


def percentile(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    i = min(len(s) - 1, max(0, round(p / 100 * (len(s) - 1))))
    return s[i]
