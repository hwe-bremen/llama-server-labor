"""Antwortstufe: Top-k-Chunks pro Retriever an ein lokales LLM, Antworten vergleichen.

  python -m bench.answer --chunking avai --retriever faiss hybrid_faiss \\
      --model "jondale/Apertus-8B-Instruct-2509-GGUF:Q4_K_M" --k 5 --per-url 1

Pro (Modell × Retriever × Frage) entsteht ein Datensatz mit Antwort, zitierten
Quellen, Reasoning-Anteil, Latenz und Token. Automatisch geprueft wird:
  - context_has_relevant : stand eine gelabelte URL ueberhaupt im Kontext? (Obergrenze)
  - cites_relevant       : zitiert die Antwort eine gelabelte URL?
  - cites_related        : ... oder deren Eltern-/Kindseite (Kategorie vs. Produkt)
  - abstained            : Verzichtsformel ohne jedes Quellenzitat (auch in eigenen Worten)
                           (richtig bei type=ohne_beleg, falsch sonst)
  - mixed                : Verzichtsformel UND zitierter Inhalt in einer Antwort (widerspruechlich)
Die fachliche Bewertung der Antwort selbst bleibt Handarbeit – dafuer gibt es den
Markdown-Report unter results/answers_<ts>.md.

LLM-Endpunkt: OpenAI-kompatibel, Default llama-server Router (RB_LLM_BASE_URL).
Modelle werden nacheinander verarbeitet (Router laedt on-demand; Wechsel kostet).
--no-think sendet chat_template_kwargs.enable_thinking=false (Qwen); --extra-json
haengt beliebige Request-Felder an.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime

from . import config
from .corpus import load_variant
from .embed import make_embedder
from .retrievers import make_retriever
from .run import dedupe_per_url, load_eval

LLM_BASE_URL = os.environ.get("RB_LLM_BASE_URL", "http://127.0.0.1:8080/v1")

SYSTEM_PROMPT = (
    "Du bist der Produktberater eines Verpackungsversandhandels und beantwortest eine Kundenfrage "
    "anhand der nummerierten Quellen unten. Regeln:\n"
    "1. Antworte in 2 bis 4 eigenen Saetzen auf Deutsch. Beginne direkt mit der Antwort.\n"
    "2. Nenne konkret, was die Quellen hergeben: Produktname, Variante, Eigenschaften, Artikelnummer.\n"
    "3. Schreibe die Quellen NICHT ab und gib keine Listen aus den Quellen wieder.\n"
    "4. Setze hinter jede Aussage die Nummer der Quelle, aus der sie stammt, in eckigen Klammern, z.B. [2].\n"
    "5. Nutze nur, was in den Quellen steht. Erfinde nichts.\n"
    "6. NUR wenn keine Quelle die Frage beantwortet, antworte ausschliesslich mit dem Satz: "
    "'Dazu finde ich in den Unterlagen keine Angabe.' – ohne weitere Saetze davor oder danach."
)

_THINK = re.compile(r"<think>.*?</think>\s*", re.S)
_CITE = re.compile(r"\[(\d{1,2})\]")
_ABSTAIN = re.compile(r"keine Angabe|nicht in den Unterlagen|keine Informationen|keine Hinweise|"
                      r"nicht beantworten|liegen? (mir )?keine|kann ich nicht|enthalten keine|"
                      r"geht nicht hervor|nicht ersichtlich", re.I)


def build_prompt(question: str, ctx_docs) -> tuple[str, list[str]]:
    lines, urls = [], []
    for i, d in enumerate(ctx_docs, 1):
        urls.append(d.url)
        title = d.meta.get("title") or ""
        head = f"[{i}] {d.url}" + (f" — {title}" if title else "")
        lines.append(f"{head}\n{d.text.strip()}\n")
    user = "Quellen:\n\n" + "\n".join(lines) + f"\nKundenfrage: {question}"
    return user, urls


def call_llm(client, model: str, user: str, max_tokens: int, temperature: float | None,
             extra: dict | None = None) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "stream": False,
    }
    if temperature is not None:  # ueberschreibt das Preset aus models.ini fuer diesen Request
        payload["temperature"] = temperature
    if extra:  # z.B. {"chat_template_kwargs": {"enable_thinking": false}} fuer Qwen
        payload.update(extra)
    t0 = time.perf_counter()
    r = client.post("/chat/completions", json=payload)
    dt = time.perf_counter() - t0
    r.raise_for_status()
    data = r.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning_content") or ""
    m = _THINK.search(content)  # Thinking inline statt im Extra-Feld
    if m:
        reasoning = (reasoning + "\n" + m.group(0)).strip()
        content = _THINK.sub("", content)
    usage = data.get("usage") or {}
    return {
        "answer": content.strip(), "reasoning_chars": len(reasoning),
        "finish_reason": data["choices"][0].get("finish_reason"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "latency_s": round(dt, 2),
    }


def _related(u: str, rel: dict) -> bool:
    """Exakt gelabelt ODER Eltern-/Kindseite einer gelabelten URL (Kategorie vs. Produkt)."""
    if u in rel:
        return True
    u = u.rstrip("/")
    return any(u.startswith(r.rstrip("/") + "/") or r.rstrip("/").startswith(u + "/") for r in rel)


def evaluate(answer: str, ctx_urls: list[str], q: dict) -> dict:
    rel = q.get("relevant") or {}
    cited_idx = {int(n) for n in _CITE.findall(answer)}
    cited_urls = [ctx_urls[i - 1] for i in sorted(cited_idx) if 1 <= i <= len(ctx_urls)]
    has_abstain = bool(_ABSTAIN.search(answer))
    # abstained = Verzicht ohne jedes Quellenzitat (auch in eigenen Worten formuliert);
    # mixed = Verzichtsformel neben zitiertem Inhalt (widerspruechlich)
    abstained = has_abstain and not cited_idx
    mixed = has_abstain and bool(cited_idx)
    return {
        "context_has_relevant": any(u in rel for u in ctx_urls),
        "cited_urls": cited_urls,
        "cites_relevant": any(u in rel for u in cited_urls),
        "cites_related": any(_related(u, rel) for u in cited_urls),
        "abstained": abstained,
        "mixed": mixed,
        "abstain_correct": (abstained == (q.get("type") == "ohne_beleg")),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="retrieval-bench Antwortstufe")
    ap.add_argument("--chunking", choices=("avai", "lab"), required=True)
    ap.add_argument("--retriever", nargs="+", default=["faiss", "hybrid_faiss"])
    ap.add_argument("--model", nargs="+", required=True, help="Modell-IDs wie in /v1/models")
    ap.add_argument("--embedder", choices=("fake", "api"), default="api")
    ap.add_argument("--k", type=int, default=5, help="Chunks im Prompt")
    ap.add_argument("--per-url", type=int, default=2)
    ap.add_argument("--candidates", type=int, default=50)
    ap.add_argument("--max-tokens", type=int, default=600)
    ap.add_argument("--temperature", type=float, default=0.2,
                    help="ueberschreibt das models.ini-Preset; -1 = Preset lassen")
    ap.add_argument("--questions", nargs="*", help="nur diese IDs (z.B. q01 q16)")
    ap.add_argument("--limit", type=int, default=0, help="nur die ersten N Fragen")
    ap.add_argument("--dry", action="store_true", help="Prompts bauen, kein LLM-Aufruf")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--no-think", action="store_true",
                    help="chat_template_kwargs.enable_thinking=false mitsenden (Qwen); wird von "
                         "Modellen ohne Thinking ignoriert")
    ap.add_argument("--extra-json", default="", help="zusaetzliche Request-Felder als JSON")
    args = ap.parse_args(argv)

    import httpx
    client = httpx.Client(base_url=LLM_BASE_URL, timeout=args.timeout)
    extra = json.loads(args.extra_json) if args.extra_json else {}
    if args.no_think:
        extra.setdefault("chat_template_kwargs", {})["enable_thinking"] = False

    questions = load_eval()
    if args.questions:
        questions = [q for q in questions if q["id"] in set(args.questions)]
    if args.limit:
        questions = questions[:args.limit]
    print(f"== {len(questions)} Fragen, chunking={args.chunking}, k={args.k}, "
          f"Modelle: {', '.join(args.model)}, LLM @ {LLM_BASE_URL}")

    docs = load_variant(args.chunking)
    by_id = {d.doc_id: d for d in docs}
    embedder = make_embedder(args.embedder)
    needs_vectors = any(r != "bm25" for r in args.retriever)
    vectors = embedder.embed_docs(docs) if needs_vectors else None
    qvecs = {q["question"]: embedder.embed([q["question"]])[0] for q in questions} if needs_vectors else {}

    # Kontexte einmal pro Retriever bauen (unabhaengig vom Modell)
    contexts: dict[str, dict[str, tuple[str, list[str], list]]] = {}
    for kind in args.retriever:
        r = make_retriever(kind, embedder)
        r.index(docs, vectors)
        contexts[r.name] = {}
        for q in questions:
            hits = r.search(q["question"], args.candidates, qvecs.get(q["question"]))
            hits = dedupe_per_url(hits, by_id, args.per_url)[:args.k]
            ctx_docs = [by_id[h.doc_id] for h in hits]
            user, urls = build_prompt(q["question"], ctx_docs)
            contexts[r.name][q["id"]] = (user, urls, ctx_docs)
        print(f"   Kontexte fuer {r.name}: {len(questions)} Prompts, "
              f"~{sum(len(c[0]) for c in contexts[r.name].values()) // len(questions)} Zeichen/Prompt")

    if args.dry:
        name = next(iter(contexts))
        qid = questions[0]["id"]
        print(f"\n--- Beispiel-Prompt ({name}, {qid}) ---\n{contexts[name][qid][0][:1500]}\n...")
        return

    ts = f"{datetime.now():%Y%m%d_%H%M%S}"
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_jsonl = config.RESULTS_DIR / f"answers_{ts}_{args.chunking}.jsonl"
    out_md = config.RESULTS_DIR / f"answers_{ts}_{args.chunking}.md"
    rows = []

    for model in args.model:
        short = model.split("/")[-1].split("-GGUF")[0]
        print(f"\n== Modell {short}")
        for rname, per_q in contexts.items():
            n_ok = n_abst = 0
            t0 = time.perf_counter()
            for q in questions:
                user, urls, ctx_docs = per_q[q["id"]]
                try:
                    res = call_llm(client, model, user, args.max_tokens,
                                   None if args.temperature < 0 else args.temperature, extra)
                except Exception as e:  # noqa: BLE001 – Lauf soll weitergehen, Fehler protokollieren
                    res = {"answer": f"<FEHLER: {type(e).__name__}: {e}>", "reasoning_chars": 0,
                           "finish_reason": "error", "prompt_tokens": None,
                           "completion_tokens": None, "latency_s": None}
                ev = evaluate(res["answer"], urls, q)
                row = {"model": model, "model_short": short + ("-nothink" if args.no_think else ""),
                       "retriever": rname, "no_think": args.no_think,
                       "chunking": args.chunking, "k": args.k, "id": q["id"], "type": q.get("type"),
                       "question": q["question"], "context_urls": urls, **res, **ev}
                rows.append(row)
                n_ok += ev["cites_related"]
                n_abst += ev["abstain_correct"]
                if ev["cites_relevant"]:
                    flag = "✓"
                elif ev["cites_related"]:
                    flag = "≈"
                elif ev["abstain_correct"] and q.get("type") == "ohne_beleg":
                    flag = "·"
                else:
                    flag = "✗"
                if ev["mixed"]:
                    flag += "!"
                print(f"   {flag} {q['id']} {rname:<24} {res['latency_s'] or 0:6.1f}s "
                      f"{(res['completion_tokens'] or 0):>5} tok  {res['answer'][:70].replace(chr(10), ' ')}")
                with out_jsonl.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            print(f"   -> {rname}: zitiert gelabelte/verwandte Quelle {n_ok}/{len(questions)}, "
                  f"Abstain korrekt {n_abst}/{len(questions)}, {time.perf_counter() - t0:.0f}s")

    write_report(rows, questions, out_md)
    print(f"\n   gespeichert: {out_jsonl.name}, {out_md.name}")
    print_summary(rows)


def print_summary(rows):
    from collections import defaultdict
    agg = defaultdict(lambda: {"n": 0, "cites": 0, "rel": 0, "ctx": 0, "abst_ok": 0, "mixed": 0,
                               "lat": [], "tok": []})
    for r in rows:
        a = agg[(r["model_short"], r["retriever"])]
        a["n"] += 1
        a["cites"] += r["cites_related"]
        a["rel"] += r["cites_relevant"]
        a["ctx"] += r["context_has_relevant"]
        a["abst_ok"] += r["abstain_correct"]
        a["mixed"] += r.get("mixed", False)
        if r["latency_s"]:
            a["lat"].append(r["latency_s"])
        if r["completion_tokens"]:
            a["tok"].append(r["completion_tokens"])
    print(f"\n{'modell':<28}{'retriever':<24}{'ctx hat rel':>12}{'zit verwandt':>13}{'zit exakt':>10}"
          f"{'abstain ok':>11}{'mixed':>6}{'s/Antw':>8}{'tok':>6}")
    for (m, rn), a in agg.items():
        lat = sum(a["lat"]) / len(a["lat"]) if a["lat"] else 0
        tok = sum(a["tok"]) / len(a["tok"]) if a["tok"] else 0
        print(f"{m:<28}{rn:<24}{a['ctx']:>7}/{a['n']:<4}{a['cites']:>8}/{a['n']:<4}{a['rel']:>5}/{a['n']:<4}"
              f"{a['abst_ok']:>6}/{a['n']:<4}{a['mixed']:>6}{lat:>8.1f}{tok:>6.0f}")
    print("   zit verwandt = gelabelte URL oder deren Eltern-/Kindseite; mixed = Antwort UND Verzichtssatz")


def write_report(rows, questions, path):
    by_q: dict[str, list[dict]] = {}
    for r in rows:
        by_q.setdefault(r["id"], []).append(r)
    lines = [f"# Antwortvergleich — {datetime.now():%Y-%m-%d %H:%M}", ""]
    lines.append("Bewertung pro Antwort bitte von Hand: richtig / teilweise / falsch / halluziniert.")
    lines.append("")
    for q in questions:
        rel = q.get("relevant") or {}
        lines.append(f"## {q['id']} ({q.get('type')}) — {q['question']}")
        if rel:
            lines.append("Gelabelt: " + ", ".join(f"{u} ({g})" for u, g in rel.items()))
        lines.append("")
        for r in by_q.get(q["id"], []):
            marks = []
            marks.append("ctx✓" if r["context_has_relevant"] else "ctx✗")
            marks.append("zit✓" if r["cites_relevant"] else ("zit≈" if r.get("cites_related") else "zit✗"))
            if r["abstained"]:
                marks.append("ABSTAIN")
            if r.get("mixed"):
                marks.append("MIXED")
            lines.append(f"### {r['model_short']} × {r['retriever']}  [{' '.join(marks)}]  "
                         f"{r['latency_s']}s, {r['completion_tokens']} tok"
                         + (f", reasoning {r['reasoning_chars']} Zeichen" if r["reasoning_chars"] else ""))
            lines.append("")
            lines.append(r["answer"] if r["answer"] else "_(leer)_")
            lines.append("")
            lines.append("Kontext: " + " · ".join(f"[{i}] {u}" for i, u in enumerate(r["context_urls"], 1)))
            lines.append("")
            lines.append("Bewertung: ___")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
