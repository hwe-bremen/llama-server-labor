#!/usr/bin/env python3
"""
Wissensbreite GGUF — Läufe gegen ein Modell (Einzelanfragen, ohne Tools, ohne Thinking).

Teil A: aufgabe.md als einzige Nutzernachricht -> Code-Block wird als gguf_lesen.py gespeichert.
Teil B: jede Frage aus fragen.json einzeln, mit kurzem Systemprompt -> wissen.json.
Ergebnis: ergebnisse/<JJJJMMTT_HHMM>_<kuerzel>/lauf<N>/{antwort_a.md, gguf_lesen.py, wissen.json, meta.json}

Aufrufe (aus dem Repo-Root; nur Standardbibliothek):
    # Qwen3.6 / Qwen3.8 über den Router (start_eval.command, 1 Modell im Speicher):
    python3 experiments/slipstream_20261017/wissensbreite_gguf/lauf.py --url http://127.0.0.1:8080 \
        --modell "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL"
    # Qwen3-Next über Slipstream (scripts/launch_qwen3next.command, Port 8083):
    python3 experiments/slipstream_20261017/wissensbreite_gguf/lauf.py --url http://127.0.0.1:8083 \
        --modell Qwen3-Coder-Next-80B-A3B
    # nur anzeigen, nichts senden:
    python3 .../lauf.py --modell X --trocken

Der erzeugte Code wird hier NICHT ausgeführt; das macht pruefen.py (mit statischer Prüfung vorab).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUFGABE = HERE / "aufgabe.md"
FRAGEN = HERE / "fragen.json"
ERGEBNISSE = HERE / "ergebnisse"

THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
CODE_RE = re.compile(r"```(?:python|py)?[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def kuerzel(modell: str) -> str:
    try:
        sys.path.insert(0, str(HERE.parents[2] / "role-split"))
        from role_proxy import model_tag          # gleiche Kürzel wie bei Verdikten und Probe
        tag = model_tag(modell)
        if tag:
            return tag
    except Exception:
        pass
    return re.sub(r"[^a-z0-9]+", "-", modell.lower()).strip("-")[:40] or "modell"


def code_aus_antwort(text: str) -> str | None:
    """Längster Code-Block (die Aufgabe verlangt genau einen ```python-Block)."""
    bloecke = CODE_RE.findall(text or "")
    return max(bloecke, key=len).rstrip() + "\n" if bloecke else None


def anfrage(url: str, modell: str, messages: list, max_tokens: int, temperatur: float, timeout: int) -> dict:
    body = {"model": modell, "messages": messages, "max_tokens": max_tokens, "temperature": temperatur,
            "stream": False, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(f"{url}/v1/chat/completions", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        return {"fehler": f"HTTP {e.code}: {e.read()[:300].decode('utf-8', 'replace')}",
                "sekunden": round(time.time() - t0, 1)}
    except Exception as e:  # Timeout, Verbindung
        return {"fehler": f"{type(e).__name__}: {e}", "sekunden": round(time.time() - t0, 1)}
    wahl = (data.get("choices") or [{}])[0]
    msg = wahl.get("message") or {}
    usage = data.get("usage") or {}
    return {"antwort": THINK_RE.sub("", msg.get("content") or "").strip(),
            "reasoning_zeichen": len(msg.get("reasoning_content") or ""),
            "finish": wahl.get("finish_reason"), "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"), "sekunden": round(time.time() - t0, 1)}


def fertiger_ordner(tag: str, laeufe: int) -> Path | None:
    """Ergebnisordner dieses Modells, in dem alle Läufe ein meta.json haben (= abgeschlossen)."""
    for o in sorted(ERGEBNISSE.glob(f"*_{tag}")):
        if all((o / f"lauf{i}" / "meta.json").exists() for i in range(1, laeufe + 1)):
            return o
    return None


def ein_lauf(ordner: Path, a, fragen: dict) -> dict:
    ordner.mkdir(parents=True, exist_ok=False)
    meta = {"modell": a.modell, "url": a.url, "start": datetime.now().isoformat(timespec="seconds"),
            "temperatur": a.temperatur, "max_tokens_a": a.max_tokens, "thinking": "aus (enable_thinking=false)",
            "fragen_version": fragen["version"]}
    if a.nur in (None, "a"):
        r = anfrage(a.url, a.modell, [{"role": "user", "content": AUFGABE.read_text(encoding="utf-8")}],
                    a.max_tokens, a.temperatur, a.timeout)
        meta["teil_a"] = {k: v for k, v in r.items() if k != "antwort"}
        (ordner / "antwort_a.md").write_text(r.get("antwort") or r.get("fehler") or "", encoding="utf-8")
        code = code_aus_antwort(r.get("antwort", ""))
        if code:
            (ordner / "gguf_lesen.py").write_text(code, encoding="utf-8")
        meta["teil_a"]["code_zeilen"] = code.count("\n") if code else 0
        abgeschnitten = " ✂ max_tokens" if r.get("finish") == "length" else ""
        print(f"  A: {r.get('sekunden')} s, {r.get('completion_tokens')} Token, "
              f"{meta['teil_a']['code_zeilen']} Codezeilen{abgeschnitten} {r.get('fehler', '')}")
    if a.nur in (None, "b"):
        wissen = []
        for f in fragen["fragen"]:
            r = anfrage(a.url, a.modell, [{"role": "system", "content": fragen["system"]},
                                          {"role": "user", "content": f["frage"]}],
                        1024, a.temperatur, a.timeout)
            wissen.append({"id": f["id"], "frage": f["frage"], **r})
            print(f"  {f['id']}: {' '.join((r.get('antwort') or r.get('fehler') or '').split())[:110]}")
        (ordner / "wissen.json").write_text(json.dumps(wissen, ensure_ascii=False, indent=1), encoding="utf-8")
    meta["ende"] = datetime.now().isoformat(timespec="seconds")
    (ordner / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Wissensbreite GGUF – Läufe gegen ein Modell")
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--modell", required=True, help="Modell-ID wie in /v1/models")
    ap.add_argument("--kuerzel", help="Ordnerkürzel (Default aus der Modell-ID)")
    ap.add_argument("--laeufe", type=int, default=3)
    ap.add_argument("--temperatur", type=float, default=0.2)
    ap.add_argument("--max-tokens", type=int, default=16000, help="Teil A (Teil B fest 1024)")
    ap.add_argument("--timeout", type=int, default=3600, help="Sekunden je Anfrage (inkl. Laden)")
    ap.add_argument("--nur", choices=["a", "b"])
    ap.add_argument("--trocken", action="store_true")
    ap.add_argument("--ueberspringen-wenn-fertig", action="store_true",
                    help="nichts tun, wenn für dieses Modell schon ein Ordner mit allen Läufen existiert")
    a = ap.parse_args(argv)

    fragen = json.loads(FRAGEN.read_text(encoding="utf-8"))
    tag = a.kuerzel or kuerzel(a.modell)
    if a.ueberspringen_wenn_fertig and (fertig := fertiger_ordner(tag, a.laeufe)):
        print(f"Übersprungen: {a.modell} [{tag}] hat schon {a.laeufe} fertige Läufe in {fertig.name}")
        return 0
    basis = ERGEBNISSE / f"{datetime.now():%Y%m%d_%H%M}_{tag}"
    print(f"Modell {a.modell} [{tag}] · {a.url} · {a.laeufe} Läufe · Temperatur {a.temperatur} · Ziel {basis}")
    if a.trocken:
        print("\n--- Teil A ---\n" + AUFGABE.read_text(encoding="utf-8"))
        print("--- Teil B ---\nSystem: " + fragen["system"])
        for f in fragen["fragen"]:
            print(f"{f['id']}: {f['frage']}")
        return 0
    try:
        urllib.request.urlopen(f"{a.url}/v1/models", timeout=30).read()
    except Exception as e:
        print(f"ABBRUCH: {a.url} nicht erreichbar ({e}). Läuft der Server?")
        return 1
    for i in range(1, a.laeufe + 1):
        print(f"== Lauf {i}")
        ein_lauf(basis / f"lauf{i}", a, fragen)
    print(f"\nFertig: {basis}\nWeiter: pruefen.py bewerten {basis} --dateien <D2> <D3> <D4>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
