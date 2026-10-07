"""Ergebnisse eines Laufs nach Fragetyp und pro Frage aufschluesseln.

  python scripts/compare_results.py                      # juengste Datei je Chunking
  python scripts/compare_results.py results/2026…_lab.json [results/…_avai.json]

Zeigt pro Datei: Mittelwerte je type × retriever, dann eine Zeile pro Frage
mit recall@k je Retriever und Markierung, wo BM25 dense schlaegt (lex>) oder
hybrid den besten Einzelwert unterbietet (hyb<).
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench import config  # noqa: E402
from bench.run import load_eval  # noqa: E402


def latest_per_chunking() -> list[Path]:
    files = sorted(config.RESULTS_DIR.glob("*.json"))
    seen: dict[str, Path] = {}
    for f in files:
        seen[f.stem.split("_", 2)[-1]] = f  # letzter gewinnt (sortiert = chronologisch)
    return list(seen.values())


def fmt(x) -> str:
    return "  -  " if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:5.2f}"


def short(name: str) -> str:
    if name.startswith("hybrid"):
        return "hybrid"
    return {"faiss": "dense", "qdrant": "qdrant", "bm25": "bm25", "bm25+stem": "bm25s"}.get(name, name[:8])


def analyse(path: Path, qtypes: dict[str, str]):
    runs = json.loads(path.read_text(encoding="utf-8"))
    names = [short(r["retriever"]) for r in runs]
    r0 = runs[0]
    print(f"\n==== {path.name}  (chunking={r0['chunking']}, k={r0['k']}, per_url={r0.get('per_url')}, "
          f"rrf_k={r0.get('rrf_k', '?')}, bm25_stem={r0.get('bm25_stem', '?')})")

    # Werte pro Frage einsammeln
    per_q: dict[str, dict[str, tuple]] = defaultdict(dict)  # qid -> retriever -> (recall, ndcg)
    for r, n in zip(runs, names):
        for pq in r["per_question"]:
            per_q[pq["id"]][n] = (pq["recall"], pq["ndcg"])

    # Mittel je type
    print(f"\n{'type':<13}{'n':>3}  " + "".join(f"{n:>14}" for n in names))
    print(f"{'':<16}  " + "".join(f"{'rec  ndcg':>14}" for _ in names))
    by_type: dict[str, list[str]] = defaultdict(list)
    for qid, t in qtypes.items():
        by_type[t].append(qid)
    for t in sorted(by_type, key=lambda x: -len(by_type[x])):
        qids = [q for q in by_type[t] if q in per_q and any(
            not math.isnan(per_q[q][n][0]) for n in names if n in per_q[q])]
        if not qids:
            continue
        row = f"{t:<13}{len(qids):>3}  "
        for n in names:
            recs = [per_q[q][n][0] for q in qids if n in per_q[q]]
            nds = [per_q[q][n][1] for q in qids if n in per_q[q]]
            row += f"{fmt(sum(recs) / len(recs)):>7}{fmt(sum(nds) / len(nds)):>7}"
        print(row)

    # Pro Frage
    print(f"\n{'id':<5}{'type':<13}" + "".join(f"{n:>8}" for n in names) + "  Hinweis")
    for qid in sorted(per_q):
        vals = per_q[qid]
        recs = {n: vals[n][0] for n in names if n in vals}
        if all(math.isnan(v) for v in recs.values()):
            continue
        hint = []
        lex = recs.get("bm25s", recs.get("bm25"))
        if lex is not None and "dense" in recs and lex > recs["dense"]:
            hint.append("lex>")
        if "hybrid" in recs:
            best_single = max(v for n, v in recs.items() if n != "hybrid")
            if recs["hybrid"] < best_single:
                hint.append("hyb<")
            elif recs["hybrid"] > best_single:
                hint.append("hyb>")
        if all(v == 0 for v in recs.values()):
            hint.append("MISS")
        print(f"{qid:<5}{qtypes.get(qid, '?'):<13}" + "".join(f"{fmt(recs.get(n)):>8}" for n in names)
              + "  " + " ".join(hint))


def main(argv):
    paths = [Path(a) for a in argv] if argv else latest_per_chunking()
    qtypes = {q["id"]: q.get("type", "?") for q in load_eval()}
    for p in paths:
        analyse(p, qtypes)
    print("\nLegende: lex> BM25 schlaegt dense | hyb> Hybrid besser als bester Einzelner | "
          "hyb< Hybrid schlechter als bester Einzelner | MISS kein Retriever findet etwas")


if __name__ == "__main__":
    main(sys.argv[1:])
