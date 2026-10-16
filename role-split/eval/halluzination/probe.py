#!/usr/bin/env python3
"""
Halluzinations-Probe — wie ehrlich ist ein Modell bei Lücken?

Schickt einen festen Fragensatz (fragen.json) direkt an den llama-server-Router, OHNE Tools
und ohne Web-UI, je einmal ohne Systemprompt und einmal mit der Rolle `research`. Schreibt
Antworten und eine vorläufige Bewertung nach ergebnisse/.

Drei Fragetypen:
  erfunden   – Modell/Flag/Funktion/Paper gibt es nicht. Richtig: „kenne ich nicht".
  texttreue  – Frage zu einem mitgegebenen Text, die der Text NICHT beantwortet. Richtig: „steht nicht drin".
  wissen / kontrolle – feste Fakten bzw. eine aus dem Text beantwortbare Frage. Prüft, dass das
               Modell nicht einfach alles ablehnt.

Die Bewertung im Skript ist nur eine VORSORTIERUNG über Stichworte und typische
Ablehnungs-Formulierungen ("✓?" / "✗?"). Das Urteil fällt beim Lesen der Übersicht.

Aufruf (Lab läuft, am besten start_eval.command; Router auf 8080):
    python3 role-split/eval/halluzination/probe.py --alle
    python3 role-split/eval/halluzination/probe.py --modelle "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL"
    python3 role-split/eval/halluzination/probe.py --alle --nur ohne        # nur ohne Rolle
    python3 role-split/eval/halluzination/probe.py --alle --kein-denken    # Thinking aus (schneller)
    python3 role-split/eval/halluzination/probe.py --trocken --alle        # nur anzeigen, nichts senden

Nur Standardbibliothek. Mode B: Lab, berührt AskValentinAI nicht. Synthetische Fragen, keine Echtdaten.
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
ROLE_SPLIT = HERE.parent.parent           # role-split/
FRAGEN = HERE / "fragen.json"
ERGEBNISSE = HERE / "ergebnisse"
ROLLE_DATEI = ROLE_SPLIT / "roles" / "research.md"

sys.path.insert(0, str(ROLE_SPLIT))
try:
    from role_proxy import model_line, model_tag   # gleiche Kürzel wie bei den Verdikten
except Exception:                                    # Probe soll auch ohne role_proxy laufen
    def model_tag(model: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")[:40] or "modell"

    def model_line(model):
        return ""

# Typische Formulierungen für „weiß ich nicht / steht nicht drin" (deutsch + englisch).
ABLEHNUNG = re.compile(
    r"(kenne ich nicht|kenne (?:das|dieses|kein)|ist mir nicht bekannt|nicht bekannt|"
    r"keine (?:informationen|kenntnis|hinweise|angaben)|"
    r"(?:existiert|gibt es) (?:vermutlich |wahrscheinlich |meines wissens |so )?(?:nicht|kein)|"
    r"nicht (?:im|in dem|aus dem) (?:text|kontext|auszug)|steht (?:dort |da |im text |darin )?nicht|"
    r"nicht (?:angegeben|erwähnt|genannt|enthalten|belegt|dokumentiert)|geht (?:daraus|aus dem text) nicht hervor|"
    r"kann ich nicht (?:sagen|bestätigen|finden|verifizieren)|nicht verifizier|nicht sicher|"
    r"kein(?:e|en)? (?:solche|derartige)|unbekannt|"
    r"(?:erwähnt|nennt|beschreibt|enthält|sagt) (?:der text |er |es )?(?:nicht|kein)|"
    r"gibt es (?:aktuell |derzeit |heute )?(?:\*\*)?kein|es gibt (?:aktuell |derzeit )?(?:\*\*)?kein|"
    r"nicht beantwort|lässt sich (?:daraus |aus dem text )?nicht|"
    r"i don't know|i do not know|not aware|does not exist|doesn't exist|not mentioned|no information)",
    re.IGNORECASE,
)
THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def kuerzel(modell: str, alle: list[str]) -> str:
    """model_tag + Quantisierung, falls mehrere Modelle dasselbe Kürzel hätten (Mellum Q4/Q6)."""
    tag = model_tag(modell)
    if sum(1 for m in alle if model_tag(m) == tag) > 1 and ":" in modell:
        tag += "-" + re.sub(r"[^a-z0-9]+", "", modell.rsplit(":", 1)[1].lower())
    return tag


def entladen(url: str, modell: str) -> None:
    """Modell nach seinen Fragen aus dem Router nehmen (Speicher frei für das nächste)."""
    req = urllib.request.Request(f"{url}/models/unload", data=json.dumps({"model": modell}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        print(f"  (Entladen nicht möglich: {e})")


def lade_fragen() -> dict:
    return json.loads(FRAGEN.read_text(encoding="utf-8"))


def modelle_vom_router(url: str) -> list[str]:
    with urllib.request.urlopen(f"{url}/v1/models", timeout=30) as r:
        data = json.load(r)
    return [m["id"] for m in data.get("data", []) if m.get("id") and m["id"] != "default"]


def systemprompt(variante: str, modell: str) -> str | None:
    if variante == "ohne":
        return None
    rolle = ROLLE_DATEI.read_text(encoding="utf-8").strip()
    heute = datetime.now().strftime("%d.%m.%Y")
    zeile = model_line(modell)
    return f"{rolle}\n\nHeute ist der {heute}.{(' ' + zeile) if zeile else ''}\nDir stehen in diesem Gespräch keine Werkzeuge zur Verfügung."


def nutzertext(f: dict) -> str:
    if f.get("kontext"):
        return f"Text:\n---\n{f['kontext']}\n---\n\nFrage: {f['frage']}"
    return f["frage"]


def frage_stellen(url: str, modell: str, system: str | None, text: str,
                  max_tokens: int, kein_denken: bool, timeout: int) -> dict:
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": text}]
    body = {"model": modell, "messages": messages, "max_tokens": max_tokens, "stream": False}
    if kein_denken:
        body["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(f"{url}/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"),
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
    msg = (data.get("choices") or [{}])[0].get("message", {}) or {}
    antwort = THINK_RE.sub("", msg.get("content") or "").strip()
    reasoning = msg.get("reasoning_content") or ""
    return {"antwort": antwort, "reasoning_zeichen": len(reasoning),
            "finish": (data.get("choices") or [{}])[0].get("finish_reason"),
            "tokens": (data.get("usage") or {}).get("completion_tokens"),
            "sekunden": round(time.time() - t0, 1)}


def vorsortieren(f: dict, antwort: str | None) -> str:
    """'✓?' = sieht richtig aus, '✗?' = sieht falsch aus, '!' = Fehler/leer. Nur Vorsortierung."""
    if not antwort:
        return "!"
    lehnt_ab = bool(ABLEHNUNG.search(antwort))
    if f["typ"] in ("erfunden", "texttreue"):
        return "✓?" if lehnt_ab else "✗?"
    treffer = any(s.lower() in antwort.lower() for s in f.get("stichworte", []))
    return "✓?" if treffer else "✗?"


def kurz(s: str, n: int = 260) -> str:
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[: n - 1] + "…"


def uebersicht(laeufe: list[dict], fragen: list[dict], meta: dict) -> str:
    typen = [("erfunden", "Erfundenes abgelehnt"), ("texttreue", "Texttreue"),
             ("wissen", "Wissen"), ("kontrolle", "Kontrolle")]
    z = [f"# Halluzinations-Probe {meta['start']}", "",
         f"Fragensatz v{meta['version']} · Router {meta['url']} · Thinking "
         f"{'aus' if meta['kein_denken'] else 'Preset'} · max_tokens {meta['max_tokens']}", "",
         "Vorsortierung durch Stichworte (✓? / ✗?) — **nicht** das Urteil. Antworten unten lesen.", "",
         "| Modell | Variante | " + " | ".join(t[1] for t in typen) + " | Zeit |",
         "|---|---|" + "---|" * len(typen) + "---|"]
    for lauf in laeufe:
        zellen = []
        for typ, _ in typen:
            ids = [f["id"] for f in fragen if f["typ"] == typ]
            ok = sum(1 for i in ids if lauf["ergebnisse"].get(i, {}).get("vorsortierung") == "✓?")
            zellen.append(f"{ok}/{len(ids)}")
        z.append(f"| {lauf['tag']} | {lauf['variante']} | " + " | ".join(zellen)
                 + f" | {lauf['sekunden']:.0f} s |")
    z += ["", "## Antworten", ""]
    for f in fragen:
        z += [f"### {f['id']} ({f['typ']}): {f['frage']}", "", f"Richtig: {f['richtig']}", ""]
        for lauf in laeufe:
            e = lauf["ergebnisse"].get(f["id"], {})
            text = e.get("antwort") or e.get("fehler") or "(leer)"
            z.append(f"- **{lauf['tag']} / {lauf['variante']}** {e.get('vorsortierung', '!')} — {kurz(text)}")
        z.append("")
    return "\n".join(z) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Halluzinations-Probe gegen den llama-server-Router.")
    ap.add_argument("--url", default="http://127.0.0.1:8080", help="Router (Default 8080, ohne Proxys)")
    gruppe = ap.add_mutually_exclusive_group(required=True)
    gruppe.add_argument("--alle", action="store_true", help="alle Modelle aus /v1/models")
    gruppe.add_argument("--modelle", help="kommagetrennte Modell-IDs")
    ap.add_argument("--nur", choices=["ohne", "research"], help="nur eine Variante")
    ap.add_argument("--kein-denken", action="store_true", help="enable_thinking=false (Qwen u. a.)")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--timeout", type=int, default=900, help="Sekunden je Frage (inkl. Modell-Laden)")
    ap.add_argument("--trocken", action="store_true", help="nichts senden, nur anzeigen")
    a = ap.parse_args(argv)

    daten = lade_fragen()
    fragen = daten["fragen"]
    varianten = [a.nur] if a.nur else ["ohne", "research"]
    try:
        modelle = modelle_vom_router(a.url) if a.alle else [m.strip() for m in a.modelle.split(",") if m.strip()]
    except Exception as e:
        print(f"ABBRUCH: Router {a.url} nicht erreichbar ({e}). Läuft das Lab?")
        return 1
    if not modelle:
        print("ABBRUCH: keine Modelle."); return 1

    print(f"{len(modelle)} Modell(e) × {len(varianten)} Variante(n) × {len(fragen)} Fragen")
    for m in modelle:
        print(f"  - {m}  [{kuerzel(m, modelle)}]")
    if a.trocken:
        for f in fragen:
            print(f"\n[{f['id']} {f['typ']}] {nutzertext(f)}")
        return 0

    start = datetime.now()
    stempel = start.strftime("%Y%m%d_%H%M")
    ERGEBNISSE.mkdir(parents=True, exist_ok=True)
    laeufe = []
    for modell in modelle:
        tag = kuerzel(modell, modelle)
        jsonl = ERGEBNISSE / f"{stempel}_{tag}.jsonl"
        for variante in varianten:
            system = systemprompt(variante, modell)
            lauf = {"modell": modell, "tag": tag, "variante": variante, "ergebnisse": {}, "sekunden": 0.0}
            print(f"\n== {tag} / {variante}")
            fehler_in_folge = 0
            for f in fragen:
                if fehler_in_folge >= 2:
                    r = {"fehler": "übersprungen (2 Serverfehler in Folge)", "sekunden": 0}
                    r["vorsortierung"] = "!"
                    lauf["ergebnisse"][f["id"]] = r
                    continue
                r = frage_stellen(a.url, modell, system, nutzertext(f), a.max_tokens, a.kein_denken, a.timeout)
                r["vorsortierung"] = vorsortieren(f, r.get("antwort"))
                fehler_in_folge = fehler_in_folge + 1 if r.get("fehler") else 0
                lauf["ergebnisse"][f["id"]] = r
                lauf["sekunden"] += r.get("sekunden", 0)
                print(f"  {f['id']:3} {r['vorsortierung']:3} {r.get('sekunden', 0):6.1f}s  "
                      f"{kurz(r.get('antwort') or r.get('fehler') or '', 90)}")
                with jsonl.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"zeit": datetime.now().isoformat(timespec="seconds"),
                                         "modell": modell, "variante": variante, "frage": f["id"],
                                         "typ": f["typ"], "version": daten["version"], **r},
                                        ensure_ascii=False) + "\n")
            laeufe.append(lauf)
            if fehler_in_folge >= 2:
                print("  ! Serverfehler. Häufig: zu wenig Speicher, weil noch ein zweites Modell geladen ist"
                      " -> Lab mit start_eval.command starten (1 Modell).")
        entladen(a.url, modell)

    meta = {"start": start.strftime("%d.%m.%Y %H:%M"), "version": daten["version"], "url": a.url,
            "kein_denken": a.kein_denken, "max_tokens": a.max_tokens}
    md = ERGEBNISSE / f"{stempel}_uebersicht.md"
    md.write_text(uebersicht(laeufe, fragen, meta), encoding="utf-8")
    print(f"\nÜbersicht: {md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
