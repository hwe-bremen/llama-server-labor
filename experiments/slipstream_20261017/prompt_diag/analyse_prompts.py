#!/usr/bin/env python3
"""Zeigt fuer aufeinanderfolgende Anfragen, ob die neue nur die alte verlaengert (Cache nutzbar)
oder weiter vorne abweicht (Server muss ab dort neu einlesen).

  python3 analyse_prompts.py requests_<zeit>.jsonl
"""
import json, sys


def render(body):
    """Grobe, modellunabhaengige Textfassung: Tools + Nachrichten in Reihenfolge."""
    teile = [("tools", json.dumps(body.get("tools", []), ensure_ascii=False, sort_keys=True))]
    for i, m in enumerate(body.get("messages", [])):
        inhalt = m.get("content")
        if not isinstance(inhalt, str):
            inhalt = json.dumps(inhalt, ensure_ascii=False, sort_keys=True)
        extra = json.dumps({k: v for k, v in m.items() if k not in ("role", "content")}, ensure_ascii=False, sort_keys=True)
        teile.append((f"msg{i}:{m.get('role')}", inhalt + extra))
    return teile


def main(path):
    reqs = [json.loads(l)["body"] for l in open(path, encoding="utf-8") if l.strip()]
    print(f"{len(reqs)} Anfragen\n")
    print(f"{'#':>3}  {'Nachr.':>6}  {'Zeichen':>8}  {'gemeinsam':>9}  Ergebnis")
    for k in range(1, len(reqs)):
        a, b = render(reqs[k - 1]), render(reqs[k])
        gesamt_b = sum(len(t) for _, t in b)
        pos, diff_at = 0, None
        for (na, ta), (nb, tb) in zip(a, b):
            if na != nb or ta != tb:
                j = next((x for x in range(min(len(ta), len(tb))) if ta[x] != tb[x]), min(len(ta), len(tb)))
                diff_at = (nb, j, ta[max(0, j - 60):j + 80], tb[max(0, j - 60):j + 80])
                pos += j
                break
            pos += len(ta)
        if diff_at is None:
            print(f"{k:>3}  {len(b)-1:>6}  {gesamt_b:>8}  {pos:>9}  nur verlaengert (gut)")
            continue
        name, j, alt, neu = diff_at
        anteil = pos / max(gesamt_b, 1)
        art = "nur verlaengert (gut)" if len(a) <= len(b) and name == a[-1][0] and j >= len(a[-1][1]) else \
              f"ABWEICHUNG in {name} bei Zeichen {j} ({anteil:.0%} des Prompts gemeinsam)"
        print(f"{k:>3}  {len(b)-1:>6}  {gesamt_b:>8}  {pos:>9}  {art}")
        if art.startswith("ABWEICHUNG"):
            print(f"       alt: …{alt!r}…\n       neu: …{neu!r}…")


if __name__ == "__main__":
    main(sys.argv[1])
