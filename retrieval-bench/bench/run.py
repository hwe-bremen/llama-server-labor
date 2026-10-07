"""CLI: einen Benchmark-Lauf ausfuehren.

Beispiele (aus retrieval-bench/, venv aktiv – oder bequemer: bash retrieval-bench/rb.command run lab):

  # Pipeline-Test ohne Modell:
  python -m bench.run --chunking lab --retriever bm25 --show 3
  python -m bench.run --chunking lab --retriever hybrid --embedder fake --show 3

  # Echter Lauf (Embedding-Endpunkt per RB_EMBED_BASE_URL / RB_EMBED_MODEL):
  python -m bench.run --chunking avai --retriever faiss qdrant hybrid hybrid_faiss --embedder api

  # URL-Dedupe: 50 Kandidaten holen, max. 2 Chunks pro URL, dann Top-10
  python -m bench.run --chunking avai --retriever faiss bm25 --embedder api --per-url 2

Weitere Stellschrauben per Umgebung: RB_RRF_K (Default 60), RB_BM25_STEM (Default 1).
Ergebnis: Tabelle auf stdout + JSON unter results/<timestamp>_<chunking>.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime

from . import config
from .corpus import load_variant
from .embed import make_embedder
from .metrics import mean, ndcg_at_k, percentile, recall_at_k, urls_in_order
from .retrievers import RETRIEVERS, make_retriever, timed_search


def load_eval(path=config.EVAL_FILE) -> list[dict]:
    if not path.exists():
        print(f"Eval-Set fehlt: {path}", file=sys.stderr)
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            items.append(json.loads(line))
    return items


def dedupe_per_url(hits, by_id, per_url: int):
    """Hoechstens per_url Chunks je URL behalten (Reihenfolge bleibt). Docs ohne URL
    (z.B. Artikelzeilen) werden nicht zusammengefasst."""
    seen: dict[str, int] = {}
    out = []
    for h in hits:
        url = by_id[h.doc_id].url
        if not url:
            out.append(h)
            continue
        if seen.get(url, 0) < per_url:
            seen[url] = seen.get(url, 0) + 1
            out.append(h)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="retrieval-bench Lauf")
    ap.add_argument("--chunking", choices=("avai", "lab"), required=True)
    ap.add_argument("--retriever", nargs="+", choices=RETRIEVERS, default=["bm25"])
    ap.add_argument("--embedder", choices=("fake", "api"), default="fake")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--include-artikel", action="store_true",
                    help="Artikelliste (xlsx) als zusaetzliche Docs aufnehmen")
    ap.add_argument("--show", type=int, default=0,
                    help="pro Frage die Top-N URLs ausgeben (hilft beim Labeln)")
    ap.add_argument("--repeat", type=int, default=1, help="Wiederholungen fuer Latenzmessung")
    ap.add_argument("--per-url", type=int, default=0,
                    help="max. Chunks pro URL in den Top-k (0 = aus). Holt --candidates Treffer, "
                         "dedupliziert nach URL, schneidet dann auf k")
    ap.add_argument("--candidates", type=int, default=50,
                    help="Kandidaten vor dem URL-Dedupe (nur mit --per-url)")
    args = ap.parse_args(argv)

    print(f"== Korpus: chunking={args.chunking} include_artikel={args.include_artikel}")
    docs = load_variant(args.chunking, include_artikel=args.include_artikel)
    print(f"   {len(docs)} Docs, {len({d.url for d in docs if d.url})} URLs")
    by_id = {d.doc_id: d for d in docs}

    questions = load_eval()
    labeled = [q for q in questions if q.get("relevant")]
    print(f"== Eval: {len(questions)} Fragen, davon {len(labeled)} gelabelt")

    needs_vectors = any(r != "bm25" for r in args.retriever)
    embedder = make_embedder(args.embedder)
    vectors = None
    if needs_vectors:
        if args.embedder == "fake":
            print("   WARNUNG: fake-Embedder – Dense-Ergebnisse sind inhaltsleer (nur Pipeline-Test)")
        vectors = embedder.embed_docs(docs)

    # Query-Vektoren einmal pro Frage berechnen und die Zeit getrennt ausweisen
    qvecs, embed_ms = {}, []
    if needs_vectors:
        for q in questions:
            t0 = time.perf_counter()
            qvecs[q["question"]] = embedder.embed([q["question"]])[0]
            embed_ms.append((time.perf_counter() - t0) * 1000.0)
        print(f"== Query-Embedding ({embedder.name}): p50 {percentile(embed_ms, 50):.1f} ms, "
              f"p95 {percentile(embed_ms, 95):.1f} ms – zaehlt NICHT in die Suchzeit unten")

    summary = []
    for kind in args.retriever:
        r = make_retriever(kind, embedder)
        t0 = time.perf_counter()
        r.index(docs, vectors)
        t_index = time.perf_counter() - t0
        print(f"\n== Retriever {r.name}: Index in {t_index:.2f}s")
        if questions:  # Warm-up: erste Suche traegt Kaltstart-Kosten, nicht in die Messung
            r.search(questions[0]["question"], args.k, qvecs.get(questions[0]["question"]))

        fetch_k = args.candidates if args.per_url else max(args.k, 10)
        rec, ndcg, lat, per_q = [], [], [], []
        for q in questions:
            for _ in range(args.repeat):
                hits, ms = timed_search(r, q["question"], fetch_k, qvecs.get(q["question"]))
                lat.append(ms)
            if args.per_url:
                hits = dedupe_per_url(hits, by_id, args.per_url)[:args.k]
            urls = [by_id[h.doc_id].url for h in hits]
            rel = q.get("relevant") or {}
            rk, nd = recall_at_k(urls, rel, args.k), ndcg_at_k(urls, rel, args.k)
            rec.append(rk)
            ndcg.append(nd)
            per_q.append({"id": q.get("id"), "recall": rk, "ndcg": nd,
                          "top_urls": urls_in_order(urls)[:args.k]})
            if args.show:
                print(f"\n  [{q.get('id')}] {q['question']}")
                for i, u in enumerate(urls_in_order(urls)[:args.show], 1):
                    mark = f" (rel={rel[u]})" if u in rel else ""
                    print(f"     {i}. {u}{mark}")

        row = {"retriever": r.name, "chunking": args.chunking, "embedder": embedder.name,
               "k": args.k, "per_url": args.per_url or None, "rrf_k": config.RRF_K,
               "bm25_stem": config.BM25_STEM, "n_docs": len(docs), "n_questions": len(questions),
               "n_labeled": len(labeled), "recall@k": mean(rec), "ndcg@k": mean(ndcg),
               "search_ms_p50": percentile(lat, 50), "search_ms_p95": percentile(lat, 95),
               "query_embed_ms_p50": percentile(embed_ms, 50) if embed_ms else None,
               "index_s": t_index, "per_question": per_q}
        summary.append(row)

    opts = f"rrf_k={config.RRF_K}, bm25_stem={int(config.BM25_STEM)}"
    if args.per_url:
        opts += f", per_url={args.per_url}, candidates={args.candidates}"
    print(f"\n== Zusammenfassung ({opts})")
    print(f"{'retriever':<24}{'recall@k':>10}{'ndcg@k':>10}{'such p50':>10}{'such p95':>10}")
    for s in summary:
        print(f"{s['retriever']:<24}{s['recall@k']:>10.3f}{s['ndcg@k']:>10.3f}"
              f"{s['search_ms_p50']:>10.2f}{s['search_ms_p95']:>10.2f}")
    if embed_ms:
        print(f"   + Query-Embedding p50 {percentile(embed_ms, 50):.1f} ms bei allen Dense-/Hybrid-Varianten")
    if not labeled:
        print("   (recall/ndcg = nan, weil noch keine Frage gelabelt ist – siehe eval/README.md)")

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = config.RESULTS_DIR / f"{datetime.now():%Y%m%d_%H%M%S}_{args.chunking}.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"   gespeichert: {out.relative_to(config.BENCH_ROOT)}")


if __name__ == "__main__":
    main()
