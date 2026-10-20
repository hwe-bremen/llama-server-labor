#!/usr/bin/env python3
"""Vergleicht die Antworten der Laufzeittests (runtime_runs/*_fixed*) Byte für Byte.

Gedanke: Mit Temperatur 0 und festem Seed darf die PGRN-Cachegröße (12/18/24 GiB) oder ein kalter/warmer Start
die Antwort nicht verändern – der Cache bestimmt nur, welche Experten nachgeladen werden, nicht was gerechnet wird.
Identische Antworten über alle Läufe sind ein Beleg, dass Staging und Korrektur (pgrn_empty_ubatch_fix) die Rechnung
nicht verfälschen. Sie belegen NICHT Gleichheit mit einem Lauf ganz ohne PGRN (der passt nicht in den Speicher).

Aufruf (Repo-Root):  python3 experiments/slipstream_20261017/qwen3next_reproducible_build/vergleich_laeufe.py
Nur Standardbibliothek, liest nur.
"""
import difflib
import hashlib
import json
import sys
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runtime_runs"


def antworten(lauf: Path) -> dict:
    out = {}
    for f in sorted(lauf.glob("response_*.json")):
        test = f.stem.split("_", 1)[1]
        d = json.loads(f.read_text(encoding="utf-8"))
        out[test] = {"text": d["choices"][0]["message"].get("content") or "",
                     "tokens": (d.get("usage") or {}).get("completion_tokens")}
    return out


def main() -> int:
    laeufe = sorted(p for p in RUNS.glob("*_fixed*") if p.is_dir() and list(p.glob("response_*.json")))
    if len(laeufe) < 2:
        print("Weniger als zwei Läufe mit Antworten gefunden."); return 1
    daten = {l.name: antworten(l) for l in laeufe}
    tests = sorted({t for a in daten.values() for t in a})
    alles_gleich = True
    for t in tests:
        print(f"\n== Test {t}")
        basis_name, basis = None, None
        for name, a in daten.items():
            if t not in a:
                print(f"  {name}: fehlt"); continue
            h = hashlib.sha256(a[t]["text"].encode("utf-8")).hexdigest()[:16]
            print(f"  {name}: {a[t]['tokens']} Token, sha256 {h}")
            if basis is None:
                basis_name, basis = name, a[t]["text"]
            elif a[t]["text"] != basis:
                alles_gleich = False
                print(f"    ABWEICHUNG gegenüber {basis_name}:")
                for z in difflib.unified_diff(basis.splitlines(), a[t]["text"].splitlines(), lineterm="", n=1):
                    print("     ", z)
    print("\nErgebnis:", "alle Antworten identisch" if alles_gleich else "Antworten weichen ab (siehe oben)")
    return 0 if alles_gleich else 2


if __name__ == "__main__":
    sys.exit(main())
