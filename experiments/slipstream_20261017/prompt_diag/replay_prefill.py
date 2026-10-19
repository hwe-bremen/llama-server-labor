#!/usr/bin/env python3
"""Spielt eine protokollierte Sitzung gegen einen laufenden llama-server ab (max_tokens=1, fast kein
Generieren) und zeigt je Anfrage, wie viele Prompt-Token der Server wirklich neu verarbeiten musste.

  python3 replay_prefill.py requests_<zeit>.jsonl [anzahl=15] [http://127.0.0.1:8083]

Wenig neu verarbeitete Token = Cache/Checkpoint wiederverwendet. Fast alle = Server hat zurueckgesetzt.
"""
import json, sys, time, urllib.request

path = sys.argv[1]
anzahl = int(sys.argv[2]) if len(sys.argv) > 2 else 15
base = sys.argv[3] if len(sys.argv) > 3 else "http://127.0.0.1:8083"
rs = [json.loads(l)["body"] for l in open(path, encoding="utf-8") if l.strip()]
rs = [b for b in rs if b.get("tools")][:anzahl]          # Titel-Anfrage ohne Tools ueberspringen

print(f"{'#':>3}  {'Prompt-Tok':>10}  {'neu verarb.':>11}  {'aus Cache':>9}  {'Zeit':>7}  Urteil")
for k, body in enumerate(rs, 1):
    b = {kk: v for kk, v in body.items() if kk in ("messages", "tools", "tool_choice")}
    b.update(max_tokens=1, temperature=0, stream=False, cache_prompt=True)
    req = urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(b).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=3600).read())
    except Exception as e:
        print(f"{k:>3}  Fehler: {e}")
        break
    t = r.get("timings", {})
    u = r.get("usage", {})
    total = u.get("prompt_tokens") or (t.get("prompt_n", 0) + t.get("cache_n", 0))
    neu, cache = t.get("prompt_n"), t.get("cache_n")
    urteil = "-" if neu is None or not total else ("wiederverwendet" if neu < 0.5 * total else "ZURUECKGESETZT")
    print(f"{k:>3}  {total:>10}  {str(neu):>11}  {str(cache):>9}  {time.time()-t0:>6.1f}s  {urteil}", flush=True)
