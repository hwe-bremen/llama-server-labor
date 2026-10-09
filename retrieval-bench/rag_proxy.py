"""RAG-Proxy: schaltet Henne-Retrieval transparent vor den llama-server Router.

Web-UI ueber den Proxy oeffnen (Standard http://127.0.0.1:8090) – alle Anfragen
werden 1:1 an den Router weitergereicht; nur POST /v1/chat/completions wird
abgefangen: letzte Nutzerfrage -> Hybrid-Retrieval -> Top-k-Chunks als
System-Kontext -> Router. Antwort wird gestreamt durchgereicht, am Ende haengt
der Proxy eine Quellenliste an. Jede Runde landet in results/chatlog_<datum>.jsonl.

  python rag_proxy.py                      # avai-Chunking, hybrid, k=5
  RB_CHUNKING=lab RB_RETRIEVER=faiss RB_K=3 python rag_proxy.py

Voraussetzungen: Router laeuft (scripts/launch_lab.command), Ollama fuer bge-m3.
Nur lesend; keine Schreibtools. Bindet nur an 127.0.0.1.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import httpx  # noqa: E402

from bench import config  # noqa: E402
from bench.answer import SYSTEM_PROMPT, build_prompt  # noqa: E402
from bench.corpus import load_variant  # noqa: E402
from bench.embed import make_embedder  # noqa: E402
from bench.retrievers import make_retriever  # noqa: E402
from bench.run import dedupe_per_url  # noqa: E402

ROUTER = os.environ.get("RB_LLM_BASE_URL", "http://127.0.0.1:8080/v1").rsplit("/v1", 1)[0]
LISTEN_PORT = int(os.environ.get("RB_PROXY_PORT", "8090"))
CHUNKING = os.environ.get("RB_CHUNKING", "avai")
RETRIEVER = os.environ.get("RB_RETRIEVER", "hybrid_faiss")
K = int(os.environ.get("RB_K", "5"))
PER_URL = int(os.environ.get("RB_PER_URL", "1"))
NO_THINK = os.environ.get("RB_NO_THINK", "1") == "1"
APPEND_SOURCES = os.environ.get("RB_APPEND_SOURCES", "1") == "1"

HOP_HEADERS = {"connection", "keep-alive", "transfer-encoding", "content-length", "host",
               "accept-encoding", "content-encoding"}


class Rag:
    def __init__(self):
        print(f"[rag] lade Korpus {CHUNKING} …", flush=True)
        self.docs = load_variant(CHUNKING)
        self.by_id = {d.doc_id: d for d in self.docs}
        self.embedder = make_embedder("api")
        vectors = self.embedder.embed_docs(self.docs)
        self.retriever = make_retriever(RETRIEVER, self.embedder)
        self.retriever.index(self.docs, vectors)
        print(f"[rag] {len(self.docs)} Docs, Retriever {self.retriever.name}, k={K}, per_url={PER_URL}",
              flush=True)

    def context(self, question: str) -> tuple[str, list[str]]:
        hits = self.retriever.search(question, 50)
        hits = dedupe_per_url(hits, self.by_id, PER_URL)[:K]
        ctx_docs = [self.by_id[h.doc_id] for h in hits]
        user, urls = build_prompt(question, ctx_docs)
        # build_prompt liefert "Quellen: … Kundenfrage: …"; hier nur den Quellenblock nutzen
        sources_block = user.rsplit("\nKundenfrage:", 1)[0]
        return sources_block, urls


RAG: Rag | None = None
CLIENT = httpx.Client(base_url=ROUTER, timeout=httpx.Timeout(900.0, connect=10.0))


def last_user_text(messages: list[dict]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            c = m.get("content")
            if isinstance(c, list):  # multimodal-Format
                return " ".join(p.get("text", "") for p in c if isinstance(p, dict))
            return c or ""
    return ""


def log_round(entry: dict):
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RESULTS_DIR / f"chatlog_{datetime.now():%Y%m%d}.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"  # Verbindung schliesst am Ende -> einfaches Streaming ohne Chunked-Encoding

    def log_message(self, fmt, *args):  # nur Chat-Runden loggen, nicht jeden Asset-Request
        pass

    # -- generisches Durchreichen ------------------------------------------
    def _forward(self, body: bytes | None):
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_HEADERS}
        try:
            with CLIENT.stream(self.command, self.path, headers=headers, content=body) as r:
                self.send_response(r.status_code)
                for k, v in r.headers.items():
                    if k.lower() not in HOP_HEADERS:
                        self.send_header(k, v)
                self.end_headers()
                for chunk in r.iter_raw():
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except httpx.HTTPError as e:
            self.send_error(502, f"Router nicht erreichbar: {e}")

    def do_GET(self):
        self._forward(None)

    def do_OPTIONS(self):
        self._forward(None)

    def do_DELETE(self):
        self._forward(None)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        if self.path.rstrip("/").endswith("/v1/chat/completions"):
            return self._chat(body)
        self._forward(body)

    # -- RAG-Injektion -------------------------------------------------------
    def _chat(self, body: bytes):
        try:
            payload = json.loads(body or b"{}")
        except json.JSONDecodeError:
            return self._forward(body)
        messages = payload.get("messages") or []
        question = last_user_text(messages).strip()
        t0 = time.perf_counter()
        sources_block, urls = RAG.context(question) if question else ("", [])
        t_retrieval = time.perf_counter() - t0

        system = SYSTEM_PROMPT + "\n\n" + sources_block
        # vorhandene System-Nachrichten des UI entfernen, eigene voranstellen
        new_messages = [{"role": "system", "content": system}] + [m for m in messages if m.get("role") != "system"]
        payload["messages"] = new_messages
        if NO_THINK:
            payload.setdefault("chat_template_kwargs", {})["enable_thinking"] = False
        stream = bool(payload.get("stream"))
        headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP_HEADERS}
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")

        answer_parts: list[str] = []
        sources_text = ""
        if APPEND_SOURCES and urls:
            sources_text = "\n\n---\nQuellen:\n" + "\n".join(f"[{i}] {u}" for i, u in enumerate(urls, 1))

        try:
            with CLIENT.stream("POST", "/v1/chat/completions", headers=headers, content=data) as r:
                self.send_response(r.status_code)
                for k, v in r.headers.items():
                    if k.lower() not in HOP_HEADERS:
                        self.send_header(k, v)
                self.end_headers()
                if not stream:
                    raw = r.read()
                    try:
                        obj = json.loads(raw)
                        msg = obj["choices"][0]["message"]
                        answer_parts.append(msg.get("content") or "")
                        if sources_text:
                            msg["content"] = (msg.get("content") or "") + sources_text
                        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
                    except (ValueError, KeyError, IndexError):
                        pass
                    self.wfile.write(raw)
                else:
                    model_id, buf = "", b""
                    for chunk in r.iter_raw():
                        buf += chunk
                        while b"\n" in buf:
                            line, buf = buf.split(b"\n", 1)
                            s = line.decode("utf-8", "replace").strip()
                            if s.startswith("data: ") and s != "data: [DONE]":
                                try:
                                    obj = json.loads(s[6:])
                                    model_id = obj.get("model", model_id)
                                    delta = obj["choices"][0].get("delta", {})
                                    if delta.get("content"):
                                        answer_parts.append(delta["content"])
                                except (ValueError, KeyError, IndexError):
                                    pass
                            if s == "data: [DONE]" and sources_text:
                                extra = {"id": "rag-sources", "object": "chat.completion.chunk",
                                         "model": model_id,
                                         "choices": [{"index": 0, "delta": {"content": sources_text},
                                                      "finish_reason": None}]}
                                self.wfile.write(f"data: {json.dumps(extra, ensure_ascii=False)}\n\n".encode())
                            self.wfile.write(line + b"\n")
                            self.wfile.flush()
                    if buf:
                        self.wfile.write(buf)
                        self.wfile.flush()
        except httpx.HTTPError as e:
            self.send_error(502, f"Router nicht erreichbar: {e}")
            return
        finally:
            answer = "".join(answer_parts)
            answer = re.sub(r"<think>.*?</think>\s*", "", answer, flags=re.S)
            log_round({"ts": datetime.now().isoformat(timespec="seconds"), "question": question,
                       "chunking": CHUNKING, "retriever": RAG.retriever.name, "k": K,
                       "context_urls": urls, "retrieval_s": round(t_retrieval, 3),
                       "model": payload.get("model"), "answer": answer.strip(),
                       "total_s": round(time.perf_counter() - t0, 1)})
            print(f"[rag] {len(urls)} Quellen in {t_retrieval * 1000:.0f} ms | "
                  f"{time.perf_counter() - t0:.1f}s | {question[:60]!r}", flush=True)


def main():
    global RAG
    RAG = Rag()
    srv = ThreadingHTTPServer(("127.0.0.1", LISTEN_PORT), Handler)
    print(f"[rag] Proxy auf http://127.0.0.1:{LISTEN_PORT}  ->  Router {ROUTER}", flush=True)
    print(f"[rag] Web-UI im Browser: http://127.0.0.1:{LISTEN_PORT}   (Ctrl+C beendet)", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[rag] beendet")


if __name__ == "__main__":
    main()
