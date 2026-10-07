"""Eval-Set pruefen: JSON gueltig? IDs eindeutig? type bekannt? URLs im Crawl vorhanden?

  python scripts/check_eval.py

Gibt pro Problem eine Zeile aus und am Ende eine Verteilung nach type.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bench import config  # noqa: E402
from bench.corpus import parse_frontmatter  # noqa: E402

TYPES = {"sinngemaess", "exakt", "mehrdeutig", "high_level", "ohne_beleg"}


def crawl_urls() -> set[str]:
    urls = set()
    for md in config.CRAWL_DIR.glob("*.md"):
        fm, _ = parse_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
        if fm.get("url"):
            urls.add(fm["url"])
    return urls


def main():
    known = crawl_urls()
    problems = 0
    ids: Counter = Counter()
    types: Counter = Counter()
    labeled = 0
    for n, line in enumerate(config.EVAL_FILE.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            q = json.loads(s)
        except json.JSONDecodeError as e:
            print(f"Zeile {n}: kein gueltiges JSON ({e.msg} an Position {e.pos})")
            problems += 1
            continue
        qid = q.get("id", f"<Zeile {n}>")
        ids[qid] += 1
        for key in ("id", "type", "question", "relevant"):
            if key not in q:
                print(f"{qid}: Feld '{key}' fehlt")
                problems += 1
        if q.get("type") not in TYPES:
            print(f"{qid}: type {q.get('type')!r} unbekannt (erlaubt: {sorted(TYPES)})")
            problems += 1
        types[q.get("type")] += 1
        rel = q.get("relevant") or {}
        if rel:
            labeled += 1
        if q.get("type") == "ohne_beleg" and rel:
            print(f"{qid}: type ohne_beleg, aber relevant ist nicht leer")
            problems += 1
        if q.get("type") not in ("ohne_beleg", None) and not rel:
            print(f"{qid}: noch nicht gelabelt (relevant leer)")
        for url, grade in rel.items():
            if grade not in (1, 2, 3):
                print(f"{qid}: Grad {grade!r} fuer {url} – erlaubt sind 1, 2, 3")
                problems += 1
            if url not in known:
                hint = ""
                if url.rstrip("/") in known:
                    hint = " (Schraegstrich am Ende entfernen)"
                elif url.split("?")[0] in known:
                    hint = " (Query-String '?…' entfernen)"
                elif url.replace("http://", "https://") in known:
                    hint = " (https statt http)"
                print(f"{qid}: URL nicht im Crawl: {url}{hint}")
                problems += 1
    for qid, c in ids.items():
        if c > 1:
            print(f"ID {qid} kommt {c}x vor")
            problems += 1
    print(f"\n{sum(ids.values())} Fragen, {labeled} gelabelt, {problems} Probleme")
    print("Verteilung:", dict(types))


if __name__ == "__main__":
    main()
