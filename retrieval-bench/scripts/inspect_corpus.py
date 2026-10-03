"""Bestandsaufnahme des Henne-Korpus – rein lesend.

  python scripts/inspect_corpus.py

Beantwortet: Wie viele Chunks/URLs in der Referenz-DB, welches Embedding-
Modell lief dort, wie gross sind die Chunks, und wie sieht das Lab-Chunking
im Vergleich aus.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench import config  # noqa: E402
from bench.corpus import load_artikel_rows, load_lab_chunks, reference_db_stats  # noqa: E402


def main():
    print("== Referenz-DB (AskValentinAI-Chunking, nur lesend)")
    if config.REFERENCE_DB.exists():
        s = reference_db_stats()
        print(f"   Chunks: {s['chunks']}   distinct URLs: {s['distinct_urls']}")
        print(f"   Embedding-Blob: {s['embedding_blob_bytes']} Bytes "
              f"→ {s['dim_if_float32']} Dimensionen, falls float32")
        print(f"   chunk_size_tokens min/avg/max: {s['chunk_tokens_min_avg_max']}")
        print("   nach source:")
        for src, n in s["by_source"]:
            print(f"     {src!s:<20}{n:>6}")
        print("   Embedding-Modelle:")
        for model, prov, n in s["embedding_models"]:
            print(f"     {model!s} / {prov!s}: {n}")
    else:
        print(f"   fehlt: {config.REFERENCE_DB}")

    print("\n== Crawl (Roh-Markdown)")
    mds = sorted(config.CRAWL_DIR.glob("*.md"))
    print(f"   {len(mds)} Dateien, {sum(p.stat().st_size for p in mds) / 1e6:.1f} MB")

    print(f"\n== Lab-Chunking (target={config.LAB_CHUNK_CHARS} Zeichen)")
    docs = load_lab_chunks()
    lens = [len(d.text) for d in docs]
    print(f"   {len(docs)} Chunks aus {len({d.url for d in docs})} URLs; "
          f"Zeichen min/avg/max: {min(lens)}/{sum(lens) // len(lens)}/{max(lens)}")
    pt = Counter(d.meta.get("page_type") for d in docs)
    print(f"   page_type: {dict(pt)}")

    print("\n== Artikelliste")
    rows = load_artikel_rows()
    print(f"   {len(rows)} Zeilen")
    if rows:
        print(f"   Beispiel: {rows[0].text[:200]}")


if __name__ == "__main__":
    main()
