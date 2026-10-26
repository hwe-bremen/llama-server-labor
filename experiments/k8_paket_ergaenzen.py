#!/usr/bin/env python3
"""K8-Notbehelf (Claude, 25.10.): Diff von role-split/kette/kette.py ins Review-Paket einfuegen.

Grund: kette.py paket nimmt role-split/ nie auf (PAKET_NIE) - bei K8 ist genau kette.py der Code.
Aufruf NACH jedem `kette.py prompt review|review2 kette_review_auto` (der baut das Paket neu):
    python3 experiments/k8_paket_ergaenzen.py
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
f = ROOT / "docs/projekt_management/review_paket_20261025_kette_review_auto.md"
s = f.read_text(encoding="utf-8")
if "Von Claude von Hand eingefügt" in s:
    print("Paket enthaelt den Diff schon - nichts zu tun."); sys.exit(0)
a = s.index("## 3. Code-Aenderungen gegen `a74e250`")
b = s.index("## 4. Testskript")
diff = subprocess.run(["git", "-C", str(ROOT), "diff", "a74e250", "--", "role-split/kette/kette.py"],
                      capture_output=True, text=True, check=True).stdout
if not diff.strip():
    print("FEHLER: kein Diff fuer role-split/kette/kette.py gefunden."); sys.exit(1)
neu = ("## 3. Code-Aenderungen gegen `a74e250`\n\n"
       "**Von Claude von Hand eingefügt (25.10.):** `kette.py paket` nimmt Dateien unter `role-split/` nie ins Paket "
       "(`PAKET_NIE`) – bei dieser Kette ist aber genau `role-split/kette/kette.py` der geänderte Code. "
       "Darum hier der vollständige Diff gegen den Rücksetzpunkt.\n\n```diff\n" + diff + "```\n\n")
s = s[:a] + neu + s[b:]
s = s.replace("Geaenderte Code-Dateien: keine.",
              "Geaenderte Code-Dateien: role-split/kette/kette.py (von Hand ergänzt, siehe Abschnitt 3).")
f.write_text(s, encoding="utf-8")
print(f"Diff eingefuegt: {f.name} jetzt {len(s)} Zeichen")
