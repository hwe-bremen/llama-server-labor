"""Korpus-Lader: liefert eine Liste von Doc-Objekten fuer eine Chunking-Variante.

Varianten:
  avai  - die Chunk-Texte aus reference_embeddings.db (exakt die Grenzen,
          die in AskValentinAI liefen). Nur lesend (mode=ro). Vektoren aus
          der DB werden bewusst NICHT geladen.
  lab   - eigenes Chunking aus den Roh-Markdowns in crawled_data/
          (absatzbasiert, Zielgroesse LAB_CHUNK_CHARS).

Beide Varianten tragen die URL als stabilen Schluessel, damit Relevanz-
urteile im Eval-Set chunking-unabhaengig auf URL-Ebene formuliert werden.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from . import config


@dataclass
class Doc:
    doc_id: str
    text: str
    url: str
    source: str
    meta: dict = field(default_factory=dict)

    @property
    def text_hash(self) -> str:
        return hashlib.sha1(self.text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- avai ----

def load_avai_chunks(db_path: Path = config.REFERENCE_DB) -> list[Doc]:
    if not db_path.exists():
        raise FileNotFoundError(f"Referenz-DB fehlt: {db_path}")
    uri = f"file:{db_path}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        rows = con.execute(
            "SELECT id, url, text, source, file_id, chunk_id, metadata, "
            "embedding_model, embedding_provider, chunk_size_tokens "
            "FROM embeddings ORDER BY id"
        ).fetchall()
    finally:
        con.close()
    docs = []
    for (rid, url, text, source, file_id, chunk_id, metadata,
         emb_model, emb_provider, chunk_tokens) in rows:
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata)
            except (TypeError, ValueError):
                meta = {"raw_metadata": metadata}
        meta.update({
            "file_id": file_id, "chunk_id": chunk_id,
            "ref_embedding_model": emb_model, "ref_embedding_provider": emb_provider,
            "ref_chunk_size_tokens": chunk_tokens,
        })
        docs.append(Doc(doc_id=f"avai:{rid}", text=text, url=url or "",
                        source=source or "", meta=meta))
    return docs


def reference_db_stats(db_path: Path = config.REFERENCE_DB) -> dict:
    """Kennzahlen der Referenz-DB (nur lesend) – fuer scripts/inspect_corpus.py."""
    uri = f"file:{db_path}?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        total = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        by_source = con.execute(
            "SELECT source, COUNT(*) FROM embeddings GROUP BY source ORDER BY 2 DESC").fetchall()
        models = con.execute(
            "SELECT embedding_model, embedding_provider, COUNT(*) FROM embeddings "
            "GROUP BY 1, 2").fetchall()
        urls = con.execute("SELECT COUNT(DISTINCT url) FROM embeddings").fetchone()[0]
        dim_row = con.execute("SELECT length(embedding) FROM embeddings LIMIT 1").fetchone()
        tok = con.execute(
            "SELECT MIN(chunk_size_tokens), AVG(chunk_size_tokens), MAX(chunk_size_tokens) "
            "FROM embeddings").fetchone()
    finally:
        con.close()
    blob_bytes = dim_row[0] if dim_row else 0
    return {
        "chunks": total, "distinct_urls": urls, "by_source": by_source,
        "embedding_models": models, "embedding_blob_bytes": blob_bytes,
        "dim_if_float32": blob_bytes // 4 if blob_bytes else None,
        "chunk_tokens_min_avg_max": tok,
    }


# ----------------------------------------------------------------- lab ----

_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def parse_frontmatter(raw: str) -> tuple[dict, str]:
    m = _FRONTMATTER.match(raw)
    if not m:
        return {}, raw
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"')
    return fm, raw[m.end():]


_NOISE_LINES = {"weiter", "abbrechen", "startseite"}


def clean_markdown(body: str) -> list[str]:
    """Markdown in bereinigte Absaetze zerlegen (Bilder, Navi-Reste, Leerzeilen raus)."""
    paras: list[str] = []
    buf: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("![") or s.lower() in _NOISE_LINES:
            continue
        if not s:
            if buf:
                paras.append(" ".join(buf))
                buf = []
            continue
        buf.append(s)
    if buf:
        paras.append(" ".join(buf))
    # Breadcrumb-Zeilen wie "* [Startseite](...)" entfernen
    return [p for p in paras if not (p.startswith("* [") and len(p) < 200)]


_SENT_SPLIT = re.compile(r"(?<=[.!?;])\s+")


def _split_oversized(p: str, target: int) -> list[str]:
    """Absatz > target an Satzgrenzen in Stuecke <= target zerlegen (Notfall: hart)."""
    if len(p) <= target:
        return [p]
    out, cur = [], ""
    for s in _SENT_SPLIT.split(p):
        while len(s) > target:  # einzelner Monstersatz → hart schneiden
            out.append(s[:target])
            s = s[target:]
        if cur and len(cur) + 1 + len(s) > target:
            out.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        out.append(cur)
    return out


def chunk_paragraphs(paras: list[str], target: int, overlap_paras: int) -> list[str]:
    chunks, cur, cur_len = [], [], 0
    paras = [piece for p in paras for piece in _split_oversized(p, target)]
    for p in paras:
        if cur and cur_len + len(p) > target:
            chunks.append("\n".join(cur))
            carry = cur[-overlap_paras:] if overlap_paras else []
            # Overlap nur, wenn er klein ist – sonst waechst der Chunk auf 2x target
            cur = carry if sum(len(x) for x in carry) <= target // 4 else []
            cur_len = sum(len(x) for x in cur)
        cur.append(p)
        cur_len += len(p)
    if cur:
        chunks.append("\n".join(cur))
    return chunks


def load_lab_chunks(crawl_dir: Path = config.CRAWL_DIR,
                    target: int = config.LAB_CHUNK_CHARS,
                    overlap_paras: int = config.LAB_CHUNK_OVERLAP_PARAS) -> list[Doc]:
    if not crawl_dir.exists():
        raise FileNotFoundError(f"Crawl-Ordner fehlt: {crawl_dir}")
    docs = []
    for md in sorted(crawl_dir.glob("*.md")):
        fm, body = parse_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
        paras = clean_markdown(body)
        title = fm.get("title", "")
        for i, chunk in enumerate(chunk_paragraphs(paras, target, overlap_paras)):
            text = f"{title}\n{chunk}" if title and i == 0 else chunk
            docs.append(Doc(
                doc_id=f"lab:{md.stem}:{i}", text=text, url=fm.get("url", ""),
                source="crawler",
                meta={"title": title, "page_type": fm.get("page_type"), "file": md.name},
            ))
    return docs


def load_artikel_rows(xlsx: Path = config.ARTIKEL_XLSX) -> list[Doc]:
    """Artikelliste als je ein Doc pro Zeile ('Spalte: Wert; ...'). Spalten unbekannt → generisch."""
    if not xlsx.exists():
        return []
    import openpyxl  # lazy import
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else f"col{i}" for i, h in enumerate(next(rows))]
    docs = []
    for n, row in enumerate(rows):
        cells = [(h, v) for h, v in zip(header, row) if v not in (None, "")]
        if not cells:
            continue
        text = "; ".join(f"{h}: {v}" for h, v in cells)
        docs.append(Doc(doc_id=f"artikel:{n}", text=text, url="", source="artikel",
                        meta={"row": n}))
    return docs


VARIANTS = {"avai": load_avai_chunks, "lab": load_lab_chunks}


def load_variant(name: str, include_artikel: bool = False) -> list[Doc]:
    if name not in VARIANTS:
        raise ValueError(f"Unbekannte Chunking-Variante {name!r}; erlaubt: {sorted(VARIANTS)}")
    docs = VARIANTS[name]()
    if include_artikel:
        docs += load_artikel_rows()
    return docs
