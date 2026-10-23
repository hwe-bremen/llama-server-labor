#!/usr/bin/env python3
"""
kette.py — Werkzeug fuer die Kette Spec -> Umsetzung -> Review (-> Tiefenpruefung).

Befehle, nur Standardbibliothek, liest/schreibt nur im Projekt:

  python3 role-split/kette/kette.py anforderung <kurztitel> --aufgabe "TEXT"
  python3 role-split/kette/kette.py anforderung <kurztitel> --antwort "TEXT" [--frage "TEXT"]
        Legt Hawes Aufgabe woertlich als docs/projekt_management/anforderung_<datum>_<kurztitel>.md ab
        bzw. haengt eine Antwort auf eine Rueckfrage an. Diese Datei ist die verbindliche Vorgabe,
        gegen die Spec, Umsetzung und Review gemessen werden (seit 20.10., Befund Kette 4).

  python3 role-split/kette/kette.py quellen <kurztitel> [--datum JJJJMMTT]
        Liest den Abschnitt "## Quellen" der Spec (je Zeile: `pfad` [Zeilen a-b | def/class Name] - Zweck)
        und schreibt die Auszuege WOERTLICH mit Zeilennummern nach quellen_<datum>_<kurztitel>.md.
        Nur Dateien im Repo. Die Umsetzung nimmt Konstanten/Formate/Schnittstellen nur von dort (21.10.,
        Befund Wissensbreite: mit Quelle 32/32, aus dem Gedaechtnis 0-23/32).

  python3 role-split/kette/kette.py prompt <schritt> <kurztitel> [--datum JJJJMMTT] [--commit HASH]
        schritt: spec | umsetzung | review | tief
        Gibt den fertigen Startprompt aus (und kopiert ihn per pbcopy, falls vorhanden).
        Ohne --datum: Datum der vorhandenen Spec (bzw. Anforderung), sonst heute.
        Ohne --commit: aktueller HEAD, mit Warnung (im Worktree/Hauptrepo pruefen!).

  python3 role-split/kette/kette.py abgleich <kurztitel> [--datum JJJJMMTT]
        Vergleicht die Test-IDs der Spec mit dem Handover (fehlt, ausgetauscht,
        nicht getestet) und prueft, ob tests/test_<kurztitel>.py je Test eine Methode hat.

  python3 role-split/kette/kette.py gegenprobe <kurztitel> --commit <ruecksetzpunkt>
        Setzt die geaenderten Code-Dateien voruebergehend auf den Stand von <commit>
        zurueck, laesst das Testskript laufen und stellt danach alles wieder her.
        Jeder Test, der dabei gruen bleibt, prueft die Aenderung nicht.

  python3 role-split/kette/kette.py pruefen <kurztitel> [--commit HASH]
        Alles in einem: abgleich + unittest -v + gegenprobe. Ruecksetzpunkt ohne --commit
        automatisch = aeltester Commit mit Nachricht "Spec <kurztitel>" (kein $K/$R noetig).
        Schreibt die komplette Ausgabe nach docs/projekt_management/pruefung_<datum>_<kurztitel>.md
        (Gegenpruefer liest sie dort, kein Kopieren) und zeigt am Ende eine Kurzzeile.

  python3 role-split/kette/kette.py paket <kurztitel> [--commit HASH]
        Baut docs/projekt_management/review_paket_<datum>_<kurztitel>.md: Anforderung wörtlich,
        aus der Spec nur Ziel/Anforderungen/Testplan-Erwartungen/Offene Fragen, Diff gegen den
        Ruecksetzpunkt, Testliste, Abweichungen aus dem Handover, Kurzfassung der Pruefung.
        Das Review liest nur diese eine Datei (22.10.: Reviews liefen bei 64K Kontext voll).
        `prompt review` baut das Paket automatisch.

  python3 role-split/kette/kette.py zusammenfuehren <verdikt1.md> <verdikt2.md> [...]
        Fuehrt die Befundtabellen mehrerer Review-Laeufe MECHANISCH zusammen (kein LLM, nichts geht
        verloren): eine Tabelle mit Spalte „Lauf", Urteil nach der Regel „ein hoher Befund in einem Lauf
        = NACHBESSERN". Schreibt docs/projekt_management/gesamt_<datum>_<kurztitel>.md.

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
SCHRITTE = ("spec", "umsetzung", "review", "review2", "tief")

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
    # Nur exakt <typ>_<JJJJMMTT>_<kurztitel>.md – sonst greift z. B. handover_..._nachbesserung2_<kt>.md (K6, 23.10.)
    muster = re.compile(rf"^{re.escape(typ)}_\d{{8}}_{re.escape(kurztitel)}\.md$")
    treffer = sorted(p for p in PM.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
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

# ---------------------------------------------------------------- pruefen (alles in einem)

def spec_commit(kurztitel: str) -> str | None:
    """Aeltester Commit, dessen Betreffzeile genau "Spec <kurztitel>" ist (= Ruecksetzpunkt)."""
    r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h%x09%s"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    treffer = [z.split("\t", 1)[0] for z in r.stdout.splitlines()
               if "\t" in z and z.split("\t", 1)[1].strip() == f"Spec {kurztitel}"]
    return treffer[-1] if treffer else None


def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
    import contextlib
    import io
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
    commit = commit or spec_commit(kurztitel)
    if not commit:
        print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
              f"(git log --oneline -10)."); return 2
    datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
    skript = ROOT / "tests" / f"test_{kurztitel}.py"
    teile, codes = [], {}

    def schritt(titel: str, fn) -> None:
        puffer = io.StringIO()
        with contextlib.redirect_stdout(puffer):
            try:
                codes[titel] = fn()
            except Exception as e:                       # Werkzeugfehler sichtbar machen, nicht verschlucken
                print(f"!!! Werkzeugfehler: {type(e).__name__}: {e}")
                codes[titel] = 2
        teile.append(f"## {titel}  (Exit {codes[titel]})\n\n```\n{puffer.getvalue().rstrip()}\n```\n")

    def unittest_lauf() -> int:
        if not skript.is_file():
            print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
        r = subprocess.run([sys.executable, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
                           cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        print((r.stdout + r.stderr).rstrip())
        return 0 if r.returncode == 0 else 1

    schritt("abgleich", lambda: abgleich(kurztitel))
    schritt("unittest", unittest_lauf)
    schritt(f"gegenprobe gegen {commit}", lambda: gegenprobe(kurztitel, commit, timeout))

    kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
                      for k, v in codes.items())
    kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
            f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
    ziel = PM / f"pruefung_{datum}_{kurztitel}.md"
    ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
    print("\n".join(teile))
    print(f"\n==> {kurz}")
    print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
    return max(codes.values())

# ---------------------------------------------------------------- Review-Paket

PAKET_DIFF_ZEILEN = 700        # je Datei; Rest liest das Review gezielt nach
PAKET_DATEI_ZEILEN = 900       # bei Umbau: ganze aktuelle Datei statt Diff, hoechstens so viele Zeilen
PAKET_WARNUNG_ZEICHEN = 80000  # ~23k Token: darueber wird es fuer 64K Kontext eng
# Werkzeug-/Infrastruktur-Ordner gehoeren nie zur Aufgabe (sonst landen spaetere Werkzeug-Commits im Diff).
PAKET_NIE = ("docs/", "tests/", "role-split/", "mcp-server/", "experiments/")


def _bloecke(text: str, muster: str) -> str:
    """Alle Abschnitte (## oder ###), deren Ueberschrift auf muster passt, samt Inhalt
    bis zur naechsten Ueberschrift gleicher oder hoeherer Ebene."""
    zeilen, raus, ebene = text.splitlines(), [], 0
    for z in zeilen:
        m = re.match(r"^(#{2,3})\s+(.*)", z)
        if m:
            neu = len(m.group(1))
            if ebene and neu <= ebene:
                ebene = 0
            if not ebene and re.search(muster, m.group(2), re.I):
                ebene = neu
        if ebene:
            raus.append(z)
    return "\n".join(raus).strip()


def _testplan_kurz(spec: str) -> str:
    """Aus dem Testplan nur die Test-Ueberschriften und die Erwartungs-Zeilen."""
    block = abschnitt(spec, "Testplan")
    raus = []
    for z in block.splitlines():
        if z.startswith("### ") or re.match(r"^\s*-\s*\*\*Erwartung", z):
            raus.append(z)
    return "\n".join(raus).strip()


def _testliste(skript: Path) -> str:
    if not skript.is_file():
        return "(kein Testskript gefunden)"
    try:
        baum = ast.parse(skript.read_text(encoding="utf-8"))
    except SyntaxError as e:
        return f"(Testskript nicht lesbar: {e})"
    raus = []
    for knoten in ast.walk(baum):
        if isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)) and knoten.name.startswith("test"):
            doc = (ast.get_docstring(knoten) or "").strip().splitlines()
            raus.append(f"- `{knoten.name}` (Zeile {knoten.lineno})" + (f": {doc[0]}" if doc else ""))
    return "\n".join(raus) or "(keine Testmethoden)"


def _auffaellige_tests(pruefung: str) -> set[str]:
    """Test-IDs/Methoden, die die Pruefung als GRUEN, LADEN oder ANDERS markiert (kleingeschrieben)."""
    treffer = set()
    for m in re.finditer(r"^\s*(?:GRUEN|LADEN)\s+(test_\w+)", pruefung, re.M):
        treffer.add(m.group(1).lower())
    for m in re.finditer(r"^\s*ANDERS\s+(T\w+)", pruefung, re.M):
        treffer.add(m.group(1).lower())
    return treffer


def _testcode(skript: Path, auffaellig: set[str], grenze: int = 60) -> str:
    """Quelltext der auffaelligen Testmethoden (je hoechstens grenze Zeilen), damit das Review
    beurteilen kann, was sie wirklich pruefen (Probe 22.10.: ohne Testcode 0/4 Testbefunde)."""
    if not skript.is_file() or not auffaellig:
        return ""
    text = skript.read_text(encoding="utf-8")
    try:
        baum = ast.parse(text)
    except SyntaxError:
        return ""
    zeilen, teile = text.splitlines(), []
    for k in ast.walk(baum):
        if not isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)) or not k.name.startswith("test"):
            continue
        name = k.name.lower()
        kennung = re.match(r"test_(t\w*?\d+[a-z]?)(?:_|$)", name)
        if name in auffaellig or (kennung and kennung.group(1) in auffaellig):
            ende = min(k.end_lineno or k.lineno, k.lineno + grenze - 1)
            code = "\n".join(f"{i:4d}  {zeilen[i - 1]}" for i in range(k.lineno, ende + 1))
            teile.append(f"#### {k.name}\n\n```\n{code}\n```")
    return "\n\n".join(teile)


def _diff(commit: str, nur: set[str] | None = None) -> tuple[str, list[str]]:
    """Code-Aenderungen gegen commit. Nie Werkzeug-/Doku-/Testordner (PAKET_NIE).
    nur: wenn gesetzt (aus dem Handover), nur diese Dateien.
    Kleine Aenderung -> Diff; Umbau (Diff laenger als die Datei) oder neue Datei -> aktuelle Datei mit
    Zeilennummern (kuerzer und lesbarer)."""
    def git(*a):
        return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
    geaendert = git("diff", "--name-only", commit).split()
    neu = git("ls-files", "--others", "--exclude-standard").split()
    def code(d):
        return (not d.startswith(PAKET_NIE) and not d.endswith(".md") and (ROOT / d).is_file()
                and (nur is None or d in nur))
    teile, dateien = [], []
    for d in sorted({x for x in geaendert + neu if code(x)}):
        aktuell = (ROOT / d).read_text(encoding="utf-8", errors="replace").splitlines()
        nummeriert = [f"{i:4d}  {z}" for i, z in enumerate(aktuell, 1)]
        if d in neu and d not in geaendert:
            teile.append(_kappen(d, nummeriert, "neu", PAKET_DATEI_ZEILEN))
        else:
            diff = git("diff", "-U3", commit, "--", d).splitlines()
            if len(diff) > len(aktuell):
                teile.append(_kappen(d, nummeriert, "umbau", PAKET_DATEI_ZEILEN))
            else:
                teile.append(_kappen(d, diff, "diff", PAKET_DIFF_ZEILEN))
        dateien.append(d)
    return "\n\n".join(teile) or "(keine Code-Aenderungen gegen den Ruecksetzpunkt)", dateien


def _kappen(datei: str, zeilen: list[str], art: str, grenze: int) -> str:
    was = {"neu": "neue Datei, mit Zeilennummern", "umbau": "stark umgebaut – aktuelle Datei mit Zeilennummern",
           "diff": "Diff"}[art]
    kopf = f"### {datei} ({was}, {len(zeilen)} Zeilen)"
    rest = ""
    if len(zeilen) > grenze:
        rest = (f"\n[... {len(zeilen) - grenze} weitere Zeilen gekuerzt – bei Bedarf gezielt "
                f"mit read_file/search_files in {datei} nachlesen]")
        zeilen = zeilen[:grenze]
    return f"{kopf}\n\n```{'diff' if art == 'diff' else ''}\n" + "\n".join(zeilen) + f"\n```{rest}"


def _handover_dateien(text: str) -> set[str] | None:
    """Pfade in Backticks aus dem Handover (Abschnitte 'Geaenderte … Dateien'). None, wenn keine."""
    bloecke = _bloecke(text, r"ge[aä]nderte|neue dateien")
    pfade = {m for m in re.findall(r"`([\w./-]+\.\w+)`", bloecke) if "/" in m or "." in m}
    return pfade or None


def _pruefung_kurz(pfad: Path | None) -> str:
    if not pfad:
        return "(keine Pruefung gefunden – vorher `kette.py pruefen <kurztitel>` laufen lassen)"
    text = pfad.read_text(encoding="utf-8")
    kurz = re.search(r"^- Kurz:.*$", text, re.M)
    teile = [kurz.group(0) if kurz else ""]
    for titel in ("abgleich", "gegenprobe"):
        teile.append(f"#### {titel}\n{abschnitt(text, titel).strip()}")
    ut = abschnitt(text, "unittest")
    zus = [z for z in ut.splitlines() if re.match(r"^(Ran |OK|FAILED|FAIL:|ERROR:)", z)]
    teile.append("#### unittest (Zusammenfassung)\n" + ("\n".join(zus) or "(keine Zusammenfassung)"))
    return "\n\n".join(t for t in teile if t)


def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, still: bool = False) -> int:
    """Schreibt review_paket_<datum>_<kurztitel>.md. Rueckgabe 0 = geschrieben, 2 = Voraussetzung fehlt."""
    say = (lambda *a: None) if still else print
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        say(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
    spec_p = datei_suchen("spec", kurztitel, datum)
    if not spec_p:
        say(f"Keine Spec spec_*_{kurztitel}.md – kein Review-Paket."); return 2
    datum = datum or _datum_aus(spec_p)
    commit = commit or spec_commit(kurztitel)
    if not commit:
        say(f"Kein Commit 'Spec {kurztitel}' – Ruecksetzpunkt mit --commit angeben."); return 2
    anf_p = datei_suchen("anforderung", kurztitel, None)
    ho_p = datei_suchen("handover", kurztitel, None)
    pr_p = datei_suchen("pruefung", kurztitel, None)
    spec = spec_p.read_text(encoding="utf-8")
    nur = _handover_dateien(ho_p.read_text(encoding="utf-8")) if ho_p else None
    try:
        diff, dateien = _diff(commit, nur)
    except subprocess.CalledProcessError as e:
        say(f"git-Fehler: {(e.stderr.strip().splitlines() or ['?'])[0]}"); return 2
    teile = [
        f"# Review-Paket: {kurztitel}\n",
        f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
        f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in dateien) or 'keine'}.\n"
        "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
        "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
        "## 1. Anforderung (verbindlich, woertlich)\n\n"
        + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
        f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
        f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
        f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
        f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
        f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
        f"## 3. Code-Aenderungen gegen `{commit}`\n\n{diff}",
        f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(ROOT / 'tests' / f'test_{kurztitel}.py')}"
        + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if (tc := _testcode(
            ROOT / "tests" / f"test_{kurztitel}.py",
            _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())) else ""),
        "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
        + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
            or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
        f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
    ]
    text = "\n\n".join(teile).rstrip() + "\n"
    ziel = PM / f"review_paket_{datum}_{kurztitel}.md"
    ziel.write_text(text, encoding="utf-8")
    groesse = len(text)
    say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)")
    if groesse > PAKET_WARNUNG_ZEICHEN:
        say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen – fuer 64K Kontext eng. "
            "Review dann eher in Teilen (z. B. erst Anforderungen A1–A3).")
    if not pr_p:
        say("Hinweis: keine pruefung_*-Datei – erst `kette.py pruefen <kurztitel>` laufen lassen.")
    return 0

# ---------------------------------------------------------------- zusammenfuehren

def _befunde(text: str) -> list[dict]:
    return tabelle(abschnitt(text, "Befunde"))


def _ist_hoch(zeile: dict) -> bool:
    schwere = (spalte(zeile, "schwere") or "").lower()
    return "hoch" in schwere or any(ja(spalte(zeile, n)) for n in ("datenverl", "unbemerkt", "harte"))


def zusammenfuehren(pfade: list[Path]) -> int:
    if len(pfade) < 2:
        print("Mindestens zwei Verdikte angeben."); return 2
    zeilen, ergebnisse, fehlt = [], [], []
    for p in pfade:
        if not p.is_file():
            fehlt.append(str(p)); continue
        text = p.read_text(encoding="utf-8")
        m = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis") or text)
        ergebnisse.append((p.name, m.group(1) if m else "?"))
        befunde = _befunde(text)
        if not befunde:
            zeilen.append((p.name, "?", "(keine Befundtabelle erkannt – Verdikt von Hand lesen)", "", False))
        for b in befunde:
            schwere = spalte(b, "schwere") or "?"
            text_b = spalte(b, "befund", "begründung", "begruendung") or " | ".join(v for v in b.values() if v)
            ort = spalte(b, "datei", "zeile", "anfor") or ""
            zeilen.append((p.name, schwere, text_b, ort, _ist_hoch(b)))
    if fehlt:
        print("Fehlt: " + ", ".join(fehlt)); return 2
    hoch = [z for z in zeilen if z[4]]
    if hoch or any(e == "NACHBESSERN" for _, e in ergebnisse):
        urteil_ = "NACHBESSERN"
    elif any(e == "FAIL" for _, e in ergebnisse):
        urteil_ = "FAIL"
    elif all(e == "PASS" for _, e in ergebnisse):
        urteil_ = "PASS"
    else:
        urteil_ = "UNKLAR"
    if any(e == "FAIL" for _, e in ergebnisse):
        urteil_ = "FAIL"
    m = re.match(r"verdict_(\d{8})_(.+?)_[^_]+(?:_[^_]+)*\.md$", pfade[0].name)
    datum = m.group(1) if m else dt.date.today().strftime("%Y%m%d")
    kt = re.match(r"verdict_\d{8}_([a-z0-9_]+?)_(?:qwen|gemma|mellum|apertus|claude|hawe)", pfade[0].name)
    kurz = kt.group(1) if kt else "review"
    teile = [f"# Gesamtbefund: {kurz}\n",
             f"Mechanisch zusammengeführt mit `kette.py zusammenfuehren` ({dt.datetime.now():%Y-%m-%d %H:%M}). Kein Befund wurde weggelassen oder umformuliert.\n",
             "## Ergebnis\n", f"**{urteil_}** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.\n",
             "| Lauf | Ergebnis des Laufs |", "|---|---|"] + [f"| `{n}` | {e} |" for n, e in ergebnisse] + [
             "", "## Befunde (alle Läufe)\n", "| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |", "|---|---|---|---|---|"]
    for n, s_, t, o, h in zeilen:
        teile.append(f"| `{n}` | {s_} | {'ja' if h else 'nein'} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
    ziel = PM / f"gesamt_{datum}_{kurz}.md"
    ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
    print(f"{len(zeilen)} Befunde aus {len(ergebnisse)} Läufen, davon {len(hoch)} hoch -> {urteil_}")
    print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
    return 0 if urteil_ == "PASS" else 1

# ---------------------------------------------------------------- anforderung

def _datum_aus(pfad: Path | None) -> str | None:
    m = re.search(r"_(\d{8})_", pfad.name) if pfad else None
    return m.group(1) if m else None


def aufgabe_lesen(pfad: Path) -> str:
    """Text unter '## Aufgabe' (ohne Zitatzeichen)."""
    block = abschnitt(pfad.read_text(encoding="utf-8"), "Aufgabe")
    zeilen = [re.sub(r"^>\s?", "", z) for z in block.splitlines()]
    return "\n".join(zeilen).strip()


def anforderung(kurztitel: str, aufgabe: str | None, antwort: str | None, frage: str | None,
                datum: str | None) -> int:
    vorhanden = datei_suchen("anforderung", kurztitel, datum)
    zitat = lambda t: "\n".join("> " + z if z else ">" for z in t.strip().splitlines())
    if aufgabe:
        if vorhanden:
            print(f"Gibt es schon: {vorhanden} (nichts ueberschrieben; Antworten mit --antwort anhaengen)")
            return 2
        d = datum or dt.date.today().strftime("%Y%m%d")
        ziel = PM / f"anforderung_{d}_{kurztitel}.md"
        PM.mkdir(parents=True, exist_ok=True)
        ziel.write_text(
            f"# Anforderung: {kurztitel}\n\n"
            "Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;\n"
            "die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.\n\n"
            f"## Aufgabe\n\n{zitat(aufgabe)}\n\n## Antworten auf Rueckfragen\n\n", encoding="utf-8")
        print(f"Angelegt: {ziel}")
        return 0
    if antwort:
        if not vorhanden:
            print(f"Keine anforderung_*_{kurztitel}.md – erst mit --aufgabe anlegen"); return 2
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        teil = f"**{stamp}**" + (f" — Frage: {frage.strip()}" if frage else "") + f"\n\n{zitat(antwort)}\n\n"
        with vorhanden.open("a", encoding="utf-8") as f:
            f.write(teil)
        print(f"Angehaengt an {vorhanden.name}")
        return 0
    print("--aufgabe oder --antwort angeben"); return 2


# ---------------------------------------------------------------- quellen

QUELLE_RE = re.compile(
    r"^\s*[-*]\s*`([^`]+)`\s*"
    r"(?:(?:Zeilen?|Z\.)\s*(\d+)\s*(?:[–—-]\s*(\d+))?|`?(def|class)\s+([A-Za-z_]\w*)(?:\([^)`]*\))?`?)?"
    r"\s*(?:[–—:-]\s*(.*))?$")
# Toleranter Leser (22.10., K6): Gedankenstrich —, Name in Backticks ohne def/class, Klasse.methode,
# Klammerzusatz „(Zeilen a–b)", Schluessel in Nicht-Python-Dateien (Textstelle mit Umgebung).
_TRENNER = r"\s*(?:[–—:]|-(?=\s))\s*"
_ZEILEN = r"(?:Zeilen?|Z\.)\s*(\d+)\s*(?:[–—-]\s*(\d+))?"


def quelle_lesen(z: str) -> dict | None:
    """Eine Zeile aus „## Quellen" -> {pfad, von, bis, art, name, text, zweck}; None, wenn keine Fundstelle."""
    m = re.match(r"^\s*[-*]\s*`([^`]+)`(.*)$", z)
    if not m or not re.search(r"[/.]", m.group(1)):
        return None
    pfad, rest = m.group(1).strip(), m.group(2)
    q = {"pfad": pfad, "von": None, "bis": None, "art": None, "name": None, "text": None, "zweck": None}
    rest = rest.strip()
    # 1) Zeilen a–b (auch in Klammern)
    zm = re.match(r"^\(?\s*" + _ZEILEN + r"\s*\)?", rest)
    if zm:
        q["von"], q["bis"] = int(zm.group(1)), int(zm.group(2) or zm.group(1))
        rest = rest[zm.end():].strip()
    else:
        # 2) `def X` / `class X` / `X.Y` / `X` / def X (ohne Backticks) / Abschnitt „…"
        nm = (re.match(r"^`?(def|class)\s+([A-Za-z_][\w.]*)(?:\([^)`]*\))?`?", rest)
              or re.match(r"^`([^`]+)`", rest)
              or re.match(r"^Abschnitt\s+[„\"']([^“\"']+)[“\"']", rest))
        if nm:
            if nm.lastindex == 2:
                q["art"], q["name"] = nm.group(1), nm.group(2)
            else:
                wort = nm.group(1).strip()
                if re.fullmatch(r"[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)?(?:\(\))?", wort):
                    q["name"] = wort.rstrip("()")
                else:
                    q["text"] = wort
            rest = rest[nm.end():].strip()
            km = re.match(r"^\(\s*" + _ZEILEN + r"\s*\)", rest)   # Klammerzusatz ignorieren, def gewinnt
            if km:
                rest = rest[km.end():].strip()
    tm = re.match(r"^" + _TRENNER + r"(.*)$", rest)
    if rest and not tm:
        return None          # unbekannte Angabe hinter dem Pfad -> UNKLAR melden statt ganze Datei holen
    q["zweck"] = (tm.group(1) if tm else "").strip() or None
    return q


def _block_name(zeilen: list[str], name: str) -> tuple[tuple[int, int] | None, str]:
    """Name ohne def/class: Klasse.methode, sonst def, sonst class. Rueckgabe (Bereich, Beschreibung)."""
    if "." in name:
        kl, me = name.split(".", 1)
        aussen = _block(zeilen, "class", kl)
        if aussen:
            innen = _block(zeilen[aussen[0] - 1:aussen[1]], "def", me)
            if innen:
                return (aussen[0] + innen[0] - 1, aussen[0] + innen[1] - 1), f"def {name}"
        return None, f"def {name}"
    for art in ("def", "class"):
        b = _block(zeilen, art, name)
        if b:
            return b, f"{art} {name}"
    return None, name


def _textstelle(zeilen: list[str], text: str, umfeld: int = 12) -> tuple[int, int] | None:
    for i, z in enumerate(zeilen):
        if text in z:
            return max(1, i + 1 - 2), min(len(zeilen), i + 1 + umfeld)
    return None


def _passt(code_zeilen: list[str], zweck: str | None) -> list[str]:
    """Namen aus `…` im Zweck, die im geholten Bereich NICHT vorkommen (Hinweis auf Zeilen aus dem Gedaechtnis)."""
    if not zweck:
        return []
    namen = set()
    for teil in re.findall(r"`([^`]+)`", zweck):
        namen.update(w for w in re.findall(r"[A-Za-z_]\w{3,}", teil))
    if not namen:
        return []
    inhalt = "\n".join(code_zeilen)
    fehlen = sorted(n for n in namen if n not in inhalt)
    return fehlen if len(fehlen) == len(namen) else []


QUELLE_MAX = 400
SPRACHE = {".py": "python", ".sh": "bash", ".command": "bash", ".json": "json", ".md": "markdown",
           ".ini": "ini", ".toml": "toml", ".yaml": "yaml", ".yml": "yaml", ".plist": "xml"}


def _block(zeilen: list[str], art: str, name: str) -> tuple[int, int] | None:
    """Zeilenbereich (1-basiert, inkl.) einer def/class samt Dekoratoren bis zur naechsten gleich tiefen Zeile."""
    kopf = re.compile(rf"^(\s*)(?:async\s+)?{art}\s+{re.escape(name)}\b")
    for i, z in enumerate(zeilen):
        m = kopf.match(z)
        if not m:
            continue
        tiefe = len(m.group(1))
        start = i
        while start > 0 and zeilen[start - 1].strip().startswith("@"):
            start -= 1
        ende = i
        for j in range(i + 1, len(zeilen)):
            zj = zeilen[j]
            if zj.strip() and len(zj) - len(zj.lstrip()) <= tiefe and not zj.lstrip().startswith(("#", ")")):
                break
            ende = j
        while ende > i and not zeilen[ende].strip():
            ende -= 1
        return start + 1, ende + 1
    return None


def quellen(kurztitel: str, datum: str | None = None) -> int:
    spec = datei_suchen("spec", kurztitel, datum)
    if not spec:
        print(f"Keine spec_*_{kurztitel}.md"); return 2
    block = abschnitt(spec.read_text(encoding="utf-8"), "Quellen")
    eintraege, unerkannt = [], []
    for z in block.splitlines():
        q = quelle_lesen(z)
        if q:
            eintraege.append(q)
        elif re.match(r"^\s*[-*]\s*`[^`]+/[^`]*`", z):  # sieht nach Fundstelle aus, Form aber unklar
            unerkannt.append(z.strip())
    if not eintraege:
        print(f"{spec.name}: Abschnitt '## Quellen' fehlt oder hat keine Zeile der Form - `pfad` …"); return 2
    d = _datum_aus(spec)
    try:
        stand = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                               capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        stand = "?"
    teile = [f"# Quellen: {kurztitel}\n",
             f"Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen {kurztitel}` "
             f"({dt.datetime.now():%Y-%m-%d %H:%M}, Stand `{stand}`), nach dem Abschnitt „Quellen“ in `{spec.name}`.",
             "Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. "
             "Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.\n"]
    fehler = 0
    for q in eintraege:
        pfad, von, bis, art, name, text, zweck = (q[k] for k in ("pfad", "von", "bis", "art", "name", "text", "zweck"))
        ziel = (ROOT / pfad).resolve()
        titel = f"`{pfad}`"
        try:
            ziel.relative_to(ROOT.resolve())
        except ValueError:
            teile.append(f"### {titel}\n\n**VERWEIGERT:** liegt ausserhalb des Repos.\n"); fehler += 1; continue
        if not ziel.is_file():
            teile.append(f"### {titel}\n\n**FEHLT:** Datei nicht gefunden.\n"); fehler += 1; continue
        zeilen = ziel.read_text(encoding="utf-8", errors="replace").splitlines()
        hinweis = ""
        if art:
            bereich = _block(zeilen, art, name) if "." not in name else _block_name(zeilen, name)[0]
            if not bereich:
                teile.append(f"### {titel} {art} {name}\n\n**FEHLT:** `{art} {name}` nicht gefunden.\n"); fehler += 1; continue
            a, b = bereich; titel += f" {art} {name}"
        elif name:
            bereich, was = _block_name(zeilen, name) if ziel.suffix == ".py" else (None, name)
            if not bereich:
                bereich = _textstelle(zeilen, name); was = f"Textstelle „{name}“"
            if not bereich:
                teile.append(f"### {titel} {name}\n\n**FEHLT:** `{name}` nicht gefunden.\n"); fehler += 1; continue
            a, b = bereich; titel += f" {was}"
        elif text:
            bereich = _textstelle(zeilen, text, 25)
            if not bereich:
                teile.append(f"### {titel} „{text}“\n\n**FEHLT:** Textstelle nicht gefunden.\n"); fehler += 1; continue
            a, b = bereich; titel += f" Textstelle „{text}“"
        elif von:
            a = max(1, int(von)); b = min(len(zeilen), int(bis or von))
            fehlen = _passt(zeilen[a - 1:b], zweck)
            if fehlen:
                hinweis = (f"\n**PRÜFEN:** Keiner der im Zweck genannten Namen ({', '.join(fehlen)}) steht in diesen Zeilen – "
                           f"Zeilenangabe vermutlich aus dem Gedächtnis. Besser `def`/`class`/Name angeben.\n")
                fehler += 1
        else:
            a, b = 1, len(zeilen)
        if b - a + 1 > QUELLE_MAX:
            teile.append(f"### {titel}\n\n**ZU LANG:** {b - a + 1} Zeilen (max. {QUELLE_MAX}) – Zeilen oder def/class angeben.\n")
            fehler += 1; continue
        breite = len(str(b))
        code = "\n".join(f"{n:>{breite}}| {zeilen[n - 1]}" for n in range(a, b + 1))
        teile.append(f"### {titel} (Zeilen {a}–{b})" + (f" – {zweck.strip()}" if zweck else "") + hinweis +
                     f"\n\n```{SPRACHE.get(ziel.suffix, '')}\n{code}\n```\n")
    for z in unerkannt:
        teile.append(f"### Nicht erkannt\n\n**UNKLAR:** `{z[:200]}` – Form: `pfad` Zeilen a–b | def Name | class Name | `Name` | Abschnitt „…“\n")
        fehler += 1
    ziel_datei = PM / f"quellen_{d}_{kurztitel}.md"
    ziel_datei.write_text("\n".join(teile), encoding="utf-8")
    print(f"{len(eintraege)} Quellen -> {ziel_datei}" + (f"   {fehler} mit FEHLT/VERWEIGERT/ZU LANG/UNKLAR/PRÜFEN" if fehler else ""))
    for t in teile:
        if "**PRÜFEN:**" in t or "**FEHLT:**" in t:
            print("  " + t.splitlines()[0].lstrip("# ") + "  -> " + ("PRÜFEN" if "PRÜFEN" in t else "FEHLT"))
    for z in unerkannt:
        print(f"  UNKLAR (nicht geholt): {z[:120]}")
    return 1 if fehler else 0


# ---------------------------------------------------------------- prompt

def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None, lauf: int | None = None) -> int:
    vorlage = PROMPTS / f"{schritt}.md"
    if not vorlage.is_file():
        print(f"Keine Vorlage: {vorlage}"); return 2
    anf = datei_suchen("anforderung", kurztitel, datum)
    if not datum:
        # Datum der vorhandenen Spec (Kette 4: "heute" passte nicht mehr am Folgetag)
        datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or _datum_aus(anf) \
            or dt.date.today().strftime("%Y%m%d")
        anf = anf or datei_suchen("anforderung", kurztitel, datum)
    if not commit and schritt != "spec":
        commit = spec_commit(kurztitel)          # Ruecksetzpunkt = Commit "Spec <kurztitel>" (22.10.)
        if commit:
            print(f"Ruecksetzpunkt = Commit 'Spec {kurztitel}' ({commit}).", file=sys.stderr)
    if not commit:
        try:
            commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True, check=True).stdout.strip()
        except Exception:
            commit = "<HASH>"
        if schritt != "spec":
            print(f"Hinweis: Ruecksetzpunkt = HEAD von {ROOT} ({commit}). Stimmt das (Worktree?)? "
                  "Sonst --commit angeben.", file=sys.stderr)
    paket_pfad = f"docs/projekt_management/review_paket_{datum}_{kurztitel}.md"
    if schritt in ("review", "review2", "tief"):
        if paket(kurztitel, commit if commit != "<HASH>" else None, None, still=False) != 0:
            print("Hinweis: Review-Paket nicht gebaut (siehe oben) – Prompt verweist trotzdem darauf.",
                  file=sys.stderr)
    anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
        f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
    if not anf:
        print(f"Hinweis: {anf_pfad} fehlt. Anlegen mit: kette.py anforderung {kurztitel} --aufgabe \"…\"",
              file=sys.stderr)
    text = (vorlage.read_text(encoding="utf-8")
            .replace("{kurztitel}", kurztitel)
            .replace("{datum}", datum)
            .replace("{commit}", commit)
            .replace("{anforderung}", anf_pfad)
            .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md")
            .replace("{paket}", paket_pfad))
    if anf:
        text = re.sub(r"<AUFGABE[^>]*>", lambda _m: aufgabe_lesen(anf), text)
    text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
    if lauf:
        # Eigener Dateiname je Review-Lauf: sonst findet Lauf 2 das Verdikt von Lauf 1 (geschuetzt),
        # liest es und haengt an (Probe K4, 22.10.) -> Laeufe nicht mehr unabhaengig.
        text = text.replace("_<modellkürzel>.md", f"_<modellkürzel>_lauf{lauf}.md")
        text += "Verdikte anderer Läufe liest du nicht.\n"
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
    p.add_argument("--lauf", type=int, help="Review-Lauf-Nummer (eigener Verdikt-Dateiname je Lauf)")
    q = sub.add_parser("quellen"); q.add_argument("kurztitel"); q.add_argument("--datum")
    n = sub.add_parser("anforderung"); n.add_argument("kurztitel")
    n.add_argument("--aufgabe"); n.add_argument("--antwort"); n.add_argument("--frage"); n.add_argument("--datum")
    a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
    u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
    g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
    g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
    g.add_argument("--timeout", type=int, default=300)
    zf = sub.add_parser("zusammenfuehren", help="Befunde mehrerer Review-Laeufe mechanisch zusammenfuehren")
    zf.add_argument("verdikte", nargs="+")
    pk = sub.add_parser("paket", help="Review-Paket bauen (eine Datei fuers Review)")
    pk.add_argument("kurztitel"); pk.add_argument("--commit"); pk.add_argument("--datum")
    pr = sub.add_parser("pruefen", help="abgleich + unittest + gegenprobe, Ausgabe in Datei")
    pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
    args = ap.parse_args(argv)
    if args.cmd == "zusammenfuehren":
        return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
                                for v in args.verdikte])
    if args.cmd == "paket":
        return paket(args.kurztitel, args.commit, args.datum)
    if args.cmd == "pruefen":
        return pruefen(args.kurztitel, args.commit, args.timeout)
    if args.cmd == "gegenprobe":
        return gegenprobe(args.kurztitel, args.commit, args.timeout)
    if args.cmd == "quellen":
        return quellen(args.kurztitel, args.datum)
    if args.cmd == "anforderung":
        return anforderung(args.kurztitel, args.aufgabe, args.antwort, args.frage, args.datum)
    if args.cmd == "prompt":
        return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
    if args.cmd == "abgleich":
        return abgleich(args.kurztitel, args.datum)
    pfad = Path(args.verdikt)
    if not pfad.is_absolute() and not pfad.exists():
        pfad = PM / pfad.name
    return urteil(pfad, args.anhaengen)


if __name__ == "__main__":
    sys.exit(main())
