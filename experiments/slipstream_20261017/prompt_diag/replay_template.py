#!/usr/bin/env python3
"""Schickt protokollierte Anfragen an /apply-template eines laufenden llama-servers (kein Rechnen,
nur Chat-Template) und vergleicht die fertigen Prompt-Texte aufeinanderfolgender Anfragen.

  python3 replay_template.py requests_<zeit>.jsonl [http://127.0.0.1:8083]

"gut" = der neue Prompt beginnt mit dem alten (bis auf das Ende, an dem die Antwort angesetzt wird).
"ABWEICHUNG" = das Template stellt fruehere Teile anders dar -> der Server muss ab dort neu einlesen.
"""
import json, sys, urllib.request

base = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8083"
rs = [json.loads(l)["body"] for l in open(sys.argv[1], encoding="utf-8") if l.strip()]


def prompt(body):
    b = {k: v for k, v in body.items() if k in ("messages", "tools", "tool_choice", "chat_template_kwargs")}
    req = urllib.request.Request(base + "/apply-template", data=json.dumps(b).encode(),
                                 headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())["prompt"]


prev = None
gut = abw = 0
for k, body in enumerate(rs):
    try:
        p = prompt(body)
    except Exception as e:
        print(f"{k:>3}  Fehler: {e}")
        prev = None
        continue
    if prev is not None:
        n = min(len(prev), len(p))
        j = next((x for x in range(n) if prev[x] != p[x]), n)
        rest = len(prev) - j
        if rest <= 64:
            gut += 1
            print(f"{k:>3}  {len(p):>8} Zeichen  gemeinsam {j:>8}  gut (alter Prompt bis auf {rest} Zeichen am Ende enthalten)")
        else:
            abw += 1
            print(f"{k:>3}  {len(p):>8} Zeichen  gemeinsam {j:>8}  ABWEICHUNG {rest} Zeichen vor dem alten Ende ({j/len(prev):.0%} gemeinsam)")
            print(f"       alt: …{prev[max(0,j-80):j+80]!r}…\n       neu: …{p[max(0,j-80):j+80]!r}…")
    prev = p
print(f"\n{gut} gut, {abw} Abweichungen")
