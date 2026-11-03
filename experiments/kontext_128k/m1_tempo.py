#!/usr/bin/env python3
"""M1 Kontext-Messung: Tempo des Umsetzers bei kurzem und langem Kontext.

Lab-Experiment (Mode B, beruehrt AskValentinAI nicht). Nur stdlib.
Schickt an den laufenden Router (Standard 127.0.0.1:8080) je eine Anfrage mit
wachsendem Fuelltext aus Repo-Dateien und gibt die Zeiten aus, die llama-server
in "timings" mitliefert (prompt_n, Prompt-Tempo, Erzeugungs-Tempo).

Aufruf (im Repo-Root):
    python3 experiments/kontext_128k/m1_tempo.py
    python3 experiments/kontext_128k/m1_tempo.py --zeichen 0,200000,380000
"""
import argparse
import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELL = "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL"
QUELLEN = ["role-split/kette/kette.py", "role-split/kette/automatik.py",
           "role-split/role_proxy.py", "docs/learnings/LERNREGELN.md"]


def fuelltext(zeichen: int) -> str:
    """Fuelltext aus Repo-Dateien, bis die Zeichenzahl erreicht ist (keine Echtdaten)."""
    if zeichen <= 0:
        return ""
    teile = []
    for rel in QUELLEN:
        p = ROOT / rel
        if p.is_file():
            teile.append(f"### Datei {rel}\n" + p.read_text(encoding="utf-8", errors="replace"))
    if not teile:
        sys.exit("Keine Quelldateien gefunden – im Repo-Root starten?")
    basis = "\n\n".join(teile)
    text, runde = [], 0
    laenge = 0
    while laenge < zeichen:
        runde += 1
        stueck = f"\n\n## Durchgang {runde}\n" + basis
        text.append(stueck)
        laenge += len(stueck)
    return "".join(text)[:zeichen]


def anfrage(url: str, modell: str, zeichen: int, max_tokens: int, timeout: int) -> dict:
    nonce = f"Messlauf {random.randint(100000, 999999)}\n"
    inhalt = nonce + fuelltext(zeichen) + "\n\nAntworte mit genau einem Satz: Worum geht es in diesem Text?"
    body = {
        "model": modell,
        "messages": [{"role": "user", "content": inhalt}],
        "max_tokens": max_tokens,
        "cache_prompt": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            daten = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"fehler": f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}",
                "sekunden": time.monotonic() - start}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"fehler": f"keine Antwort: {e}", "sekunden": time.monotonic() - start}
    daten["sekunden"] = time.monotonic() - start
    return daten


def zeile(zeichen: int, d: dict) -> str:
    if "fehler" in d:
        return f"{zeichen:>8} Zeichen | FEHLER nach {d['sekunden']:.0f} s: {d['fehler']}"
    t = d.get("timings") or {}
    u = d.get("usage") or {}
    prompt_n = t.get("prompt_n", u.get("prompt_tokens", "?"))
    pps = t.get("prompt_per_second")
    gps = t.get("predicted_per_second")
    pps_s = f"{pps:7.1f} tok/s" if isinstance(pps, (int, float)) else "      ? tok/s"
    gps_s = f"{gps:5.1f} tok/s" if isinstance(gps, (int, float)) else "    ? tok/s"
    return (f"{zeichen:>8} Zeichen | Prompt {prompt_n!s:>7} Token | Prompt {pps_s} | "
            f"Erzeugung {gps_s} | gesamt {d['sekunden']:6.1f} s")


def main() -> int:
    ap = argparse.ArgumentParser(description="M1: Tempo bei kurzem und langem Kontext")
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--modell", default=MODELL)
    ap.add_argument("--zeichen", default="0,200000,380000",
                    help="Kommagetrennte Fuelltext-Laengen in Zeichen (grob 3,2 Zeichen je Token)")
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--timeout", type=int, default=1800)
    a = ap.parse_args()
    try:
        stufen = [int(x) for x in a.zeichen.split(",") if x.strip()]
    except ValueError:
        print("--zeichen: nur ganze Zahlen, kommagetrennt", file=sys.stderr)
        return 2
    print(f"Router {a.url}, Modell {a.modell}")
    print("Aufwaermen (laedt das Modell, Zeit zaehlt nicht) ...", flush=True)
    w = anfrage(a.url, a.modell, 0, 8, a.timeout)
    if "fehler" in w:
        print(f"Aufwaermen fehlgeschlagen: {w['fehler']}", file=sys.stderr)
        return 1
    if "timings" not in w:
        print("Hinweis: Antwort enthaelt kein 'timings' – Tempo dann nur aus dem Server-Log.")
    for z in stufen:
        print(zeile(z, anfrage(a.url, a.modell, z, a.max_tokens, a.timeout)), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
