#!/usr/bin/env python3
"""
kette.py — Werkzeug fuer die Kette Spec -> Umsetzung -> Review (-> Tiefenpruefung).

Drei Befehle, nur Standardbibliothek, liest/schreibt nur im Projekt:

  python3 role-split/kette/kette.py prompt <schritt> <kurztitel> [--datum JJJJMMTT] [--commit HASH]
        schritt: spec | umsetzung | review | tief
        Gibt den fertigen Startprompt aus (und kopiert ihn per pbcopy, falls vorhanden).

  python3 role-split/kette/kette.py abgleich <kurztitel> [--datum JJJJMMTT]
        Vergleicht die Test-IDs der Spec mit dem Handover (fehlt, ausgetauscht,
        nicht getestet) und prueft, ob tests/test_<kurztitel>.py je Test eine Methode hat.

  python3 role-split/kette/kette.py urteil <verdikt.md> [--anhaengen]
        Leitet das Urteil mechanisch aus dem Verdikt ab: Ein Befund mit "ja" bei
        Datenverlust / Unbemerkt / Harte Vorgabe ist "hoch"; ein offener Befund "hoch"
        oder eine Anforderung "teilweise"/"nicht" ergibt NACHBESSERN.
        --anhaengen schreibt das Ergebnis als Abschnitt ans Verdikt.

Exit-Codes: 0 = in Ordnung / PASS, 1 = Abweichung / NACHBESSERN, 2 = Datei/Format-Fehler.
Mode B: Lab, beruehrt AskValentinAI nicht.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PM = ROOT / "docs" / "projekt_management"
PROMPTS = HERE / "prompts"
SCHRITTE = ("spec", "umsetzung", "review", "tief")

# ---------------------------------------------------------------- Markdown-Helfer

def abschnitt(text: str, titel: str) -> str:
    """Inhalt unter '## <titel...>' bis zur naechsten '## '-Ueberschrift ('' wenn fehlt)."""
    m = re.search(rf"^##\s+{re.escape(titel)}[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1) if m else ""


def tabelle(block: str) -> list[dict]:
    """Erste Markdown-Tabelle im Block als Liste von Dicts (Spaltennamen kleingeschrieben)."""
    zeilen = [z.strip() for z in block.splitlines() if z.strip().startswith("|")]
    if len(zeilen) < 2:
        return []
    zellen = lambda z: [c.strip() for c in z.strip("|").split("|")]
    kopf = [k.lower() for k in zellen(zeilen[0])]
    daten = []
    for z in zeilen[1:]:
        if re.fullmatch(r"[\s|:\-]+", z):
            continue
        werte = zellen(z)
        daten.append({k: (werte[i] if i < len(werte) else "") for i, k in enumerate(kopf)})
    return daten


def spalte(zeile: dict, *namen: str) -> str | None:
    """Wert der ersten Spalte, deren Name einen der Begriffe enthaelt."""
    for k, v in zeile.items():
        if any(n in k for n in namen):
            return v
    return None


def ja(wert: str | None) -> bool:
    return bool(wert) and wert.strip().strip("*").lower().startswith("ja")

# ---------------------------------------------------------------- urteil

def urteil(pfad: Path, anhaengen: bool = False) -> int:
    if not pfad.is_file():
        print(f"Nicht gefunden: {pfad}"); return 2
    text = pfad.read_text(encoding="utf-8")
    m = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis"))
    modell = m.group(1) if m else None
    hinweise, korrekturen = [], []

    offen = []
    for z in tabelle(abschnitt(text, "Anforderungen")):
        status = (spalte(z, "befund", "status") or "").lower()
        if "teilweise" in status or re.search(r"\bnicht\b", status):
            offen.append(f"{spalte(z, 'nr') or '?'}: {status}")

    befunde = tabelle(abschnitt(text, "Befunde"))
    hoch = []
    kriterien_da = befunde and any(spalte(befunde[0], k) is not None
                                   for k in ("datenverlust", "unbemerkt", "harte"))
    if befunde and not kriterien_da:
        hinweise.append("Altes Format: Befunde ohne Spalten Datenverlust/Unbemerkt/Harte Vorgabe "
                        "-- Schwere wird nur uebernommen, nicht geprueft.")
    for z in befunde:
        nr = spalte(z, "#") or "?"
        schwere = (spalte(z, "schwere") or "").lower()
        if not schwere.strip(" -"):
            continue  # leere Vorlagenzeile
        gruende = [k for k, n in (("Datenverlust", "datenverlust"), ("Unbemerkt", "unbemerkt"),
                                  ("Harte Vorgabe", "harte")) if ja(spalte(z, n))]
        if gruende and "hoch" not in schwere:
            korrekturen.append(f"Befund {nr}: als '{schwere}' eingestuft, aber ja bei "
                               f"{', '.join(gruende)} -> hoch")
            hoch.append(nr)
        elif "hoch" in schwere:
            hoch.append(nr)

    regel = "NACHBESSERN" if (hoch or offen) else "PASS"
    # Die Regel verschaerft nur: ein strengeres Modellurteil bleibt stehen.
    rang = {"PASS": 0, "NACHBESSERN": 1, "FAIL": 2}
    mech = max(regel, modell or "PASS", key=rang.get)

    zeilen = [f"Modell-Urteil:       {modell or 'nicht gefunden'}",
              f"Regel-Urteil:        {regel}",
              f"Es gilt:             {mech}"]
    if hoch:
        zeilen.append(f"  Befunde hoch: {', '.join(hoch)}")
    if offen:
        zeilen.append(f"  Anforderungen offen: {'; '.join(offen)}")
    zeilen += [f"  Korrektur: {k}" for k in korrekturen]
    zeilen += [f"  Hinweis: {h}" for h in hinweise]
    if modell and rang[regel] > rang[modell]:
        zeilen.append(f"  WIDERSPRUCH: Modell sagt {modell}, die Regel verlangt {regel}.")
    elif modell and rang[regel] < rang[modell]:
        zeilen.append(f"  Modell strenger als die Regel -- Begruendung im Verdikt lesen.")
    print("\n".join(zeilen))

    if anhaengen:
        marke = "## Mechanisches Urteil (kette.py)"
        if marke in text:
            print("(Abschnitt existiert schon, nicht erneut angehaengt)")
        else:
            stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            pfad.write_text(text.rstrip("\n") + f"\n\n{marke}\n\n_{stamp}_\n\n```\n"
                            + "\n".join(zeilen) + "\n```\n", encoding="utf-8")
            print(f"Angehaengt an {pfad.name}")
    if modell is None and not befunde:
        return 2
    return 0 if mech == "PASS" else 1

# ---------------------------------------------------------------- abgleich

TEST_ID = r"[A-Z]{0,3}T\d+"
STOP = {"mit", "ohne", "und", "im", "in", "der", "die", "das", "den", "dem", "des", "ein", "eine",
        "einem", "bei", "von", "zu", "auf", "fuer", "für", "als", "nach", "vor", "aus", "oder", "test"}
TAG = re.compile(r"^[a-z]\d+$")   # Anforderungs-Kuerzel wie n6, a3, e1


def tests_finden(text: str) -> dict[str, str]:
    """Test-IDs (T1, NT3 ...) mit Titel aus Ueberschriften, Fettzeilen oder Tabellenzeilen."""
    gefunden: dict[str, str] = {}
    muster = re.compile(rf"^\s*(?:#{{2,5}}\s*|\*\*|\|\s*)({TEST_ID})\b[.:)]?\s*(.*)$")
    for z in text.splitlines():
        m = muster.match(z)
        if not m:
            continue
        titel = m.group(2)
        titel = titel.split("|")[0] if z.lstrip().startswith("|") else titel
        gefunden.setdefault(m.group(1), titel.strip(" *:`"))
    return gefunden


def woerter(titel: str) -> set[str]:
    t = re.sub(r"[`*_\[\]()]", " ", titel.lower())
    return {w for w in re.split(r"[^a-z0-9äöüß]+", t) if w and w not in STOP}


def passt(spec_titel: str, ho_titel: str) -> float:
    s = {w for w in woerter(spec_titel) if not TAG.match(w)}
    if not s:
        return 1.0
    return len(s & woerter(ho_titel)) / len(s)


def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
    if datum:
        p = PM / f"{typ}_{datum}_{kurztitel}.md"
        return p if p.is_file() else None
    treffer = sorted(PM.glob(f"{typ}_*_{kurztitel}.md"))
    return treffer[-1] if treffer else None


def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
    spec, ho = datei_suchen("spec", kurztitel, datum), datei_suchen("handover", kurztitel, datum)
    if not spec or not ho:
        print(f"Spec oder Handover fehlt: spec={spec}, handover={ho}"); return 2
    spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
    ho_text = ho.read_text(encoding="utf-8")
    getestet = tests_finden(abschnitt(ho_text, "Getestet"))
    nicht = set(re.findall(rf"\b({TEST_ID})\b", abschnitt(ho_text, "Nicht getestet")))
    print(f"Spec:     {spec.name}  ({len(spec_tests)} Tests)\nHandover: {ho.name}\n")
    if not spec_tests:
        print("Keine Test-IDs (T1, NT1 ...) in der Spec gefunden."); return 2

    probleme = 0
    for tid, titel in spec_tests.items():
        if tid in getestet:
            q = passt(titel, getestet[tid])
            if q >= schwelle:
                print(f"  ok        {tid:5} {titel}")
            else:
                probleme += 1
                print(f"  ANDERS    {tid:5} Spec: {titel}\n"
                      f"                  Handover: {getestet[tid]}   (Uebereinstimmung {q:.0%} -- ausgetauscht?)")
        elif tid in nicht:
            probleme += 1
            print(f"  NICHT GET {tid:5} {titel}  (unter 'Nicht getestet' -- Grund pruefen)")
        else:
            probleme += 1
            print(f"  FEHLT     {tid:5} {titel}")
    for tid in getestet.keys() - spec_tests.keys():
        print(f"  EXTRA     {tid:5} {getestet[tid]}  (nicht in der Spec)")

    skript = ROOT / "tests" / f"test_{kurztitel}.py"
    if skript.is_file():
        code = skript.read_text(encoding="utf-8")
        ohne = [t for t in spec_tests if not re.search(rf"def\s+test_{t.lower()}(_|\b)", code)]
        if ohne:
            probleme += 1
            print(f"\n  Testskript {skript.relative_to(ROOT)}: keine Methode test_<id> fuer {', '.join(ohne)}")
        else:
            print(f"\n  Testskript {skript.relative_to(ROOT)}: alle {len(spec_tests)} Tests als Methode vorhanden")
            print(f"  Selbst ausfuehren: python3 -m unittest -v {skript.relative_to(ROOT)}")
    else:
        print(f"\n  Kein Testskript tests/test_{kurztitel}.py -- Tests sind nur behauptet, nicht wiederholbar.")
    print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
    return 0 if not probleme else 1

# ---------------------------------------------------------------- prompt

def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None) -> int:
    vorlage = PROMPTS / f"{schritt}.md"
    if not vorlage.is_file():
        print(f"Keine Vorlage: {vorlage}"); return 2
    if not commit:
        try:
            commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            commit = "<HASH>"
    text = (vorlage.read_text(encoding="utf-8")
            .replace("{kurztitel}", kurztitel)
            .replace("{datum}", datum or dt.date.today().strftime("%Y%m%d"))
            .replace("{commit}", commit))
    text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
    print(text)
    if shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=text, text=True)
        print("(in die Zwischenablage kopiert)", file=sys.stderr)
    return 0

# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Werkzeug fuer die Kette Spec -> Umsetzung -> Review")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prompt"); p.add_argument("schritt", choices=SCHRITTE); p.add_argument("kurztitel")
    p.add_argument("--datum"); p.add_argument("--commit")
    a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
    u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "prompt":
        return prompt(args.schritt, args.kurztitel, args.datum, args.commit)
    if args.cmd == "abgleich":
        return abgleich(args.kurztitel, args.datum)
    pfad = Path(args.verdikt)
    if not pfad.is_absolute() and not pfad.exists():
        pfad = PM / pfad.name
    return urteil(pfad, args.anhaengen)


if __name__ == "__main__":
    sys.exit(main())
