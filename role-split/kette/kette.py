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

  python3 role-split/kette/kette.py gegenprobe <kurztitel> --commit <ruecksetzpunkt>
        Setzt die geaenderten Code-Dateien voruebergehend auf den Stand von <commit>
        zurueck, laesst das Testskript laufen und stellt danach alles wieder her.
        Jeder Test, der dabei gruen bleibt, prueft die Aenderung nicht.

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
import ast
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
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


PRUEF_AUFRUFE = re.compile(r"^(assert\w*|fail\w*)$")


def methoden_pruefen(code: str) -> list[str]:
    """Findet Testmethoden ohne Pruefung und Testmethoden mit identischem Rumpf.
    (17./18.10.: T9 bestand aus zwei identischen Methoden; ein Test ohne assert misst nichts.)"""
    try:
        baum = ast.parse(code)
    except SyntaxError as e:
        return [f"SYNTAX    Testskript laesst sich nicht parsen: {e}"]
    hinweise, ruempfe = [], {}
    for knoten in ast.walk(baum):
        if not isinstance(knoten, ast.FunctionDef) or not knoten.name.startswith("test"):
            continue
        prueft = any(
            (isinstance(n, ast.Assert)) or
            (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and PRUEF_AUFRUFE.match(n.func.attr)) or
            (isinstance(n, ast.Raise))
            for n in ast.walk(knoten))
        if not prueft:
            hinweise.append(f"OHNE PRUEF {knoten.name}: kein assert/fail -- der Test kann nicht rot werden")
        koerper = [b for b in knoten.body
                   if not (isinstance(b, ast.Expr) and isinstance(getattr(b, "value", None), ast.Constant)
                           and isinstance(b.value.value, str))]          # Docstring ignorieren
        schluessel = ast.dump(ast.Module(body=koerper, type_ignores=[]))
        if schluessel in ruempfe:
            hinweise.append(f"DOPPELT   {knoten.name} hat denselben Rumpf wie {ruempfe[schluessel]}")
        else:
            ruempfe[schluessel] = knoten.name
    return hinweise


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
        for hinweis in methoden_pruefen(code):
            probleme += 1
            print(f"  {hinweis}")
        print(f"  Selbst ausfuehren: python3 -m unittest -v {skript.relative_to(ROOT)}")
    else:
        print(f"\n  Kein Testskript tests/test_{kurztitel}.py -- Tests sind nur behauptet, nicht wiederholbar.")
    print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
    return 0 if not probleme else 1

# ---------------------------------------------------------------- gegenprobe

LAEUFER = r"""
import json, sys, unittest
modul = sys.argv[1]
suite = unittest.defaultTestLoader.loadTestsFromName(modul)
def name(t): return t.id().split(".")[-1].split(" ")[0]
stand = {}
def alle(s):
    for t in s:
        if isinstance(t, unittest.TestSuite): alle(t)
        elif t is not None: stand[name(t)] = "ok"
alle(suite)                       # vor run(): unittest entfernt gelaufene Tests aus der Suite
erg = unittest.TestResult()
suite.run(erg)
for t, _ in erg.failures: stand[name(t)] = "FAIL"
for t, _ in erg.errors:
    stand[name(t) if hasattr(t, "id") else str(t)] = "ERROR"
if not stand and erg.errors: stand["<Laden>"] = "ERROR"
for t, _ in erg.skipped: stand[name(t)] = "skipped"
print("@@KETTE@@" + json.dumps(stand))
"""


def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
    """Laesst das Testskript in einem eigenen Prozess laufen; Ergebnis je Testmethode."""
    modul = ".".join(skript.relative_to(ROOT).with_suffix("").parts)
    # Eigener, frischer Bytecode-Cache je Lauf: sonst kann Python eine alte .pyc weiterverwenden,
    # wenn die zurueckgesetzte Datei gleich gross ist und in derselben Sekunde geschrieben wurde.
    with tempfile.TemporaryDirectory(prefix="kette_pyc_") as cache:
        try:
            r = subprocess.run([sys.executable, "-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul],
                               cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
    for zeile in reversed(r.stdout.splitlines()):
        if zeile.startswith("@@KETTE@@"):
            return json.loads(zeile[len("@@KETTE@@"):])
    return {"<Testskript laedt nicht>": "ERROR"}


def _zuruecksetzen_und_testen(skript: Path, d: str, commit: str, timeout: int) -> dict[str, str] | None:
    """Eine Datei voruebergehend auf <commit> zuruecksetzen, Tests laufen lassen, wiederherstellen."""
    pfad = ROOT / d
    sicherung = Path(tempfile.mkdtemp(prefix="gegenprobe_"))
    kopie, weg = sicherung / "kopie", pfad.with_name(pfad.name + ".gegenprobe_weg")
    summe = hashlib.sha256(pfad.read_bytes()).hexdigest() if pfad.exists() else None
    try:
        if pfad.exists():
            shutil.copy2(pfad, kopie)
        alt = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{d}"], capture_output=True)
        if alt.returncode == 0:
            pfad.write_bytes(alt.stdout)
        elif pfad.exists():                       # Datei ist neu -> im alten Stand gab es sie nicht
            pfad.rename(weg)                      # umbenennen statt loeschen
        return tests_laufen(skript, timeout)
    finally:
        if weg.exists():
            weg.rename(pfad)
        elif kopie.exists():
            shutil.copy2(kopie, pfad)
        ok = summe is None or (pfad.exists() and hashlib.sha256(pfad.read_bytes()).hexdigest() == summe)
        if ok:
            shutil.rmtree(sicherung, ignore_errors=True)
        else:
            print(f"!!! {d} nicht sauber wiederhergestellt. Sicherung: {kopie}")


def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
    """Setzt jede seit <commit> geaenderte Code-Datei einzeln voruebergehend auf den alten Stand
    zurueck und laesst das Testskript laufen. Ein Test, der dabei nie rot wird, prueft keine der
    Aenderungen. Danach wird jeweils der aktuelle Stand wiederhergestellt (Pruefsumme)."""
    skript = ROOT / "tests" / f"test_{kurztitel}.py"
    if not skript.is_file():
        print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
    try:
        diff = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", commit],
                              capture_output=True, text=True, check=True).stdout.split()
        neu = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
                             capture_output=True, text=True, check=True).stdout.split()
    except subprocess.CalledProcessError as e:
        print(f"git-Fehler: {e.stderr.strip()}"); return 2
    dateien = sorted({d for d in diff + neu
                      if d.endswith((".py", ".sh", ".command")) and (ROOT / d).exists()
                      and not d.startswith(("tests/", "docs/", "role-split/kette/", "experiments/"))})
    if not dateien:
        print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2

    vorher = tests_laufen(skript, timeout)
    if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
        print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
        return 2
    print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
    rot_durch: dict[str, list[str]] = {t: [] for t in vorher}
    laden_scheitert: list[str] = []
    for d in dateien:
        nachher = _zuruecksetzen_und_testen(skript, d, commit, timeout)
        if nachher is None:
            print(f"  {d}: Zeitueberschreitung"); continue
        if set(nachher) - set(vorher):            # Laden gescheitert
            print(f"  {d}: ohne die neue Fassung laedt das Testskript gar nicht -- alle Tests rot, aber ohne Einzelaussage")
            laden_scheitert.append(Path(d).name)
            continue
        rote = [t for t, v in nachher.items() if v in ("FAIL", "ERROR")]
        for t in rote:
            rot_durch[t].append(d)
        print(f"  {d}: {len(rote)} Test(s) rot")
    print()
    gruen = [t for t, ds in rot_durch.items() if not ds]
    for t in sorted(rot_durch):
        if rot_durch[t]:
            print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
        elif laden_scheitert:
            print(f"  LADEN {t}  (rot nur, weil das Skript ohne {', '.join(laden_scheitert)} nicht laedt -- schwacher Beleg)")
        else:
            print(f"  GRUEN {t}  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)")
    print(f"\n{len(vorher) - len(gruen)} von {len(vorher)} Tests werden durch eine einzelne alte Datei rot"
          + (f", {len(gruen)} nur ueber das Laden" if laden_scheitert else "") + ". Aktueller Stand ist wiederhergestellt.")
    if gruen:
        print("GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) "
              "oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, "
              "dann wird die Gegenprobe je Test aussagekraeftig.")
    return 0 if not gruen else 1

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
    g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
    g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
    g.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args(argv)
    if args.cmd == "gegenprobe":
        return gegenprobe(args.kurztitel, args.commit, args.timeout)
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
