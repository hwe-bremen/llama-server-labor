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

  python3 role-split/kette/kette.py umsetzung-auto <kurztitel> [--nacharbeit <datei.md>]
        Umsetzung bzw. Nacharbeit ohne TUI: opencode run --format json, Agent umsetzung_nacht,
        Modell KETTE_UMSETZUNG_MODEL (nur llamacpp/), Zeitlimit KETTE_UMSETZUNG_TIMEOUT (7200 s).
        Danach mechanisch: Selbst-Commit, Schreibbereich der Spec, Handover, pruefen. Protokollzeile in
        docs/projekt_management/umsetzung_<datum>_<kurztitel>.md, Rohdaten in role-split/results/.

  python3 role-split/kette/kette.py tests-pruefen <kurztitel> [--timeout S]
        Prueft vorab geschriebene Tests (Spec mit '## Vorgabe-Tests'): je Test-ID eine Methode, Skript laedt,
        jeder Test rot ohne Umsetzung. umsetzung-auto startet den Erstlauf nur bei Exit 0 (K11a).

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
import signal
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PM = ROOT / "docs" / "projekt_management"
PROMPTS = HERE / "prompts"
SCHRITTE = ("spec", "umsetzung", "review", "review2", "tief")

# ---------------------------------------------------------------- Ablage-Ordner (K13a)

def ablage(kurztitel: str) -> Path:
    """Ablage-Verzeichnis: docs/projekt_management/<kurztitel>/ wenn vorhanden, sonst docs/projekt_management/."""
    ordner = PM / kurztitel
    return ordner if ordner.is_dir() else PM


def _ablage_rel(kurztitel: str) -> str:
    """Relativer Pfad zur Ablage, wie er in Dateinamen/Prompts steht."""
    if (PM / kurztitel).is_dir():
        return f"docs/projekt_management/{kurztitel}"
    return "docs/projekt_management"


def _ablage_text(text: str, kurztitel: str) -> str:
    """Ersetzt docs/projekt_management/ in Pfaden durch den Ablage-Ordner der Kette.
    
    Ersetzt jedes docs/projekt_management/ das nicht auf _vorlage_ folgt,
    unabhaengig vom Dateisuffix. Doppelordner werden vermieden, indem
    der Aufrufer den Text vor Platzhalter-Ersetzung umbiegt.
    """
    if not (PM / kurztitel).is_dir():
        return text
    abl = f"docs/projekt_management/{kurztitel}/"
    # Ersetze docs/projekt_management/<nicht-slash, nicht-whitespace> nur wenn es kein _vorlage_ ist
    # Der Dateiname wird beibehalten (Capture-Group)
    return re.sub(
        r"docs/projekt_management/(?!_vorlage_)([^/\s]+)",
        lambda m: f"{abl}{m.group(1)}",
        text
    )

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
        # Nur Ablage-Ordner der Kette (Nachbesserung 1 E2: kein Fallback mehr auf flach)
        abl = ablage(kurztitel)
        p = abl / f"{typ}_{datum}_{kurztitel}.md"
        return p if p.is_file() else None
    # Nur exakt <typ>_<JJJJMMTT>_<kurztitel>.md – sonst greift z. B. handover_..._nachbesserung2_<kt>.md (K6, 23.10.)
    muster = re.compile(rf"^{re.escape(typ)}_\d{{8}}_{re.escape(kurztitel)}\.md$")
    abl = ablage(kurztitel)
    treffer = sorted(p for p in abl.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
    return treffer[-1] if treffer else None


def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
    spec, ho = datei_suchen("spec", kurztitel, datum), datei_suchen("handover", kurztitel, datum)
    if not spec or not ho:
        print(f"Spec oder Handover fehlt: spec={spec}, handover={ho}"); return 2
    spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
    ho_text = ho.read_text(encoding="utf-8")
    getestet = tests_finden(abschnitt(ho_text, "Getestet"))
    # A2: Bereichsangaben (T1–T2, T1-T2) unter "Nicht getestet" entfernen
    nicht_text = abschnitt(ho_text, "Nicht getestet")
    nicht_text = re.sub(rf"\b({TEST_ID})\s*[–—-]\s*({TEST_ID})\b", "", nicht_text)
    nicht = set(re.findall(rf"\b({TEST_ID})\b", nicht_text))
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
        kette, _fremd = _aenderungen(commit, kurztitel)
    except subprocess.CalledProcessError as e:
        print(f"git-Fehler: {e.stderr.strip()}"); return 2
    # A5: dieselbe Auswahl wie paket – nur zur Kette gehoerige Code-Dateien, auch role-split/kette/
    dateien = sorted(d for d in kette
                     if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))
    if not dateien:
        print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2

    vorher = tests_laufen(skript, timeout)
    if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
        print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
        return 2
    print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
    bestand = _bestand_ids(kurztitel)
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
    bestand_re = re.compile(rf"test_({'|'.join(bestand)})(_|$)", re.I)
    gruen = [t for t, ds in rot_durch.items() if not ds and not bestand_re.match(t)]
    for t in sorted(rot_durch):
        if rot_durch[t]:
            print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
        elif bestand_re.match(t) and not rot_durch[t]:
            print(f"  BESTAND {t}  (prueft laut Spec bewusst Bestehendes)")
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

# ---------------------------------------------------------------- tests-pruefen (K11a)

BESTAND = "(Bestand)"


def _bestand_ids(kurztitel: str) -> set[str]:
    """Test-IDs der Spec, deren Titel BESTAND enthält."""
    spec = datei_suchen("spec", kurztitel, None)
    if not spec:
        return set()
    ids, titel_map = [], tests_finden(spec.read_text(encoding="utf-8"))
    for tid, titel in titel_map.items():
        if BESTAND in titel:
            ids.append(tid)
    return set(ids)


def _vorgabe_tests(spec_text: str) -> bool:
    """Wahr, wenn die Spec den Abschnitt '## Vorgabe-Tests' hat (Tests vorab, Umsetzer schreibt nur Code)."""
    return re.search(r"^##\s+Vorgabe-Tests\s*$", spec_text, re.M) is not None


def tests_pruefen(kurztitel: str, timeout: int = 300) -> int:
    """Prueft vorab geschriebene Tests: je Test-ID der Spec eine Methode, Skript laedt, jeder Test rot vorab."""
    spec = datei_suchen("spec", kurztitel, None)
    skript = ROOT / "tests" / f"test_{kurztitel}.py"
    if not skript.is_file():
        print(f"Keine Vorgabe-Tests tests/test_{kurztitel}.py"); return 2
    if not spec:
        print(f"Keine spec_*_{kurztitel}.md"); return 2
    spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
    if not spec_tests:
        print(f"Keine Test-IDs (T1, NT1 ...) in {spec.name}"); return 2
    code = skript.read_text(encoding="utf-8")
    probleme = 0
    for hinweis in methoden_pruefen(code):
        probleme += 1
        print(f"  {hinweis}")
    stand = tests_laufen(skript, timeout)
    if stand is None:
        print(f"  ZEIT      Testskript nach {timeout} s abgebrochen")
        return 1
    try:
        methoden = {k.name for k in ast.walk(ast.parse(code))
                    if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)) and k.name.startswith("test")}
    except SyntaxError:
        methoden = set()
    if not set(stand) & methoden:          # nur Lade-Eintraege, keine echte Testmethode gelaufen
        print("  LAEDT NICHT Testskript laedt nicht -- neue Funktionen erst in der Methode importieren")
        return 1
    bestand = _bestand_ids(kurztitel)
    for tid in spec_tests:
        namen = [n for n in stand if re.match(rf"test_{tid.lower()}(_|$)", n)]
        if not namen:
            probleme += 1
            print(f"  FEHLT     {tid}")
            continue
        if tid in bestand:
            if not namen or all(stand[n] == "ok" for n in namen):
                print(f"  gruen     {tid}")
            else:
                probleme += 1
                nicht_ok = [n for n in namen if stand[n] != "ok"]
                print(f"  NICHT GRUEN {tid}  {', '.join(nicht_ok)} (Bestand-Test muss vorab grün sein)")
            continue
        nicht_rot = [n for n in namen if stand[n] not in ("FAIL", "ERROR")]
        if nicht_rot:
            probleme += 1
            print(f"  NICHT ROT {tid}  {', '.join(nicht_rot)} (ohne Umsetzung nicht rot -- prueft nichts Neues)")
        else:
            print(f"  rot       {tid}")
    print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
    return 0 if not probleme else 1

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


def _pruefen_teile(kurztitel: str, commit: str | None = None, timeout: int = 300) -> dict:
    """Teilergebnisse von abgleich, unittest, gegenprobe. Rueckgabe: dict mit den drei Schlüsseln."""
    import contextlib
    import io
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        return {"abgleich": (2, "Kurztitel ungueltig"), "unittest": (2, ""), "gegenprobe": (2, "")}
    commit = commit or spec_commit(kurztitel)
    if not commit:
        return {"abgleich": (2, f"Kein Commit 'Spec {kurztitel}'"),
                "unittest": (2, ""), "gegenprobe": (2, "")}
    skript = ROOT / "tests" / f"test_{kurztitel}.py"

    def schritt(titel: str, fn):
        puffer = io.StringIO()
        with contextlib.redirect_stdout(puffer):
            try:
                code = fn()
            except Exception as e:
                print(f"!!! Werkzeugfehler: {type(e).__name__}: {e}")
                code = 2
        return code, puffer.getvalue()

    def unittest_lauf():
        if not skript.is_file():
            print(f"Kein Testskript {skript.relative_to(ROOT)}")
            return 2
        r = subprocess.run([sys.executable, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
                           cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        print((r.stdout + r.stderr).rstrip())
        return 0 if r.returncode == 0 else 1

    abgl_code, abgl_out = schritt("abgleich", lambda: abgleich(kurztitel))
    unit_code, unit_out = schritt("unittest", unittest_lauf)
    gegen_code, gegen_out = schritt(f"gegenprobe gegen {commit}",
                                    lambda: gegenprobe(kurztitel, commit, timeout))
    return {"abgleich": (abgl_code, abgl_out), "unittest": (unit_code, unit_out),
            "gegenprobe": (gegen_code, gegen_out)}


def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
    commit = commit or spec_commit(kurztitel)
    if not commit:
        print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
              f"(git log --oneline -10)."); return 2
    teile_dict = _pruefen_teile(kurztitel, commit, timeout)
    codes = {k: v[0] for k, v in teile_dict.items()}
    teile = []
    for titel_key in ("abgleich", "unittest", "gegenprobe"):
        code, out = teile_dict[titel_key]
        # Titel wiederherstellen: gegenprobe braucht {commit}
        titel = f"gegenprobe gegen {commit}" if titel_key == "gegenprobe" else titel_key
        teile.append(f"## {titel}  (Exit {code})\n\n```\n{out.rstrip()}\n```\n")
    kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
                      for k, v in codes.items())
    datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
    kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
            f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
    ziel = ablage(kurztitel) / f"pruefung_{datum}_{kurztitel}.md"
    ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
    print("\n".join(teile))
    print(f"\n==> {kurz}")
    print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
    return max(codes.values())

# ---------------------------------------------------------------- Review-Paket

PAKET_DIFF_ZEILEN = 700        # je Datei; Rest liest das Review gezielt nach
PAKET_DATEI_ZEILEN = 900       # bei Umbau: ganze aktuelle Datei statt Diff, hoechstens so viele Zeilen
PAKET_WARNUNG_ZEICHEN = 80000  # ~23k Token: darueber wird es fuer 64K Kontext eng
# Nur docs/ und experiments/ gehoeren nie ins Paket. .md-Dateien in role-split/, tests/ etc. werden aufgenommen.
PAKET_NIE = ("docs/", "experiments/",)
# Harte Obergrenze: darueber bricht paket mit Exit 1 ab (nach Vorrang-Kuerzung).
KETTE_PAKET_MAX = int(os.environ.get("KETTE_PAKET_MAX", "150000"))


def _git(*a: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout


def _aenderungen(commit: str, kurztitel: str | None, nur: set[str] | None = None
                 ) -> tuple[list[str], list[tuple[str, list[tuple[str, str]]]]]:
    """A1: Alle seit <commit> geaenderten/neuen Dateien (ausser PAKET_NIE), getrennt nach
    zur Kette gehoerig / fremd. Gemeinsame Auswahl fuer paket und gegenprobe (A5).

    Quellen: Commits <commit>..HEAD, nicht committete Aenderungen (auch vorgemerkt),
    unversionierte Dateien. Zur Kette gehoert eine Datei, wenn sie (a) in einem Commit mit dem
    Kurztitel in der Nachricht geaendert wurde, (b) nicht committete oder unversionierte
    Aenderungen hat oder (c) in der Uebergabe genannt wird. Sonst fremd.
    Rueckgabe: (kette, fremd) mit fremd = [(datei, [(kurzhash, betreff), ...]), ...]."""
    committet = set(_git("diff", "--name-only", commit, "HEAD").split())
    offen = set(_git("diff", "--name-only", "HEAD").split())          # unstaged + staged
    neu = set(_git("ls-files", "--others", "--exclude-standard").split())
    alle = sorted(d for d in committet | offen | neu
                  if not d.startswith(PAKET_NIE) and (ROOT / d).is_file())
    log = [z.split("\t", 1) for z in _git("log", "--format=%H%x09%s", f"{commit}..HEAD").splitlines()
           if "\t" in z]
    # Kurztitel als ganzes Wort (nicht "g" in "gross"): links/rechts kein a-z, 0-9, _
    muster = re.compile(rf"(?<![a-z0-9_]){re.escape(kurztitel)}(?![a-z0-9_])") if kurztitel else None
    eigene = {h for h, betreff in log if muster and muster.search(betreff)}
    kette: list[str] = []
    fremd: list[tuple[str, list[tuple[str, str]]]] = []
    for d in alle:
        if d in offen or d in neu or (nur and d in nur):
            kette.append(d)
            continue
        dc = [z.split("\t", 1) for z in
              _git("log", "--format=%H%x09%s", f"{commit}..HEAD", "--", d).splitlines() if "\t" in z]
        if any(h in eigene for h, _ in dc):
            kette.append(d)
        else:
            fremd.append((d, [(h[:7], b) for h, b in dc]))
    return kette, fremd


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


def _vorrang(d: str, nur: set[str] | None) -> int:
    """A3: 1 = Uebergabe oder ausserhalb tests/ (nie kuerzen), 2 = Testcode, 3 = Testdaten."""
    if (nur and d in nur) or not d.startswith("tests/"):
        return 1
    return 2 if d.endswith((".py", ".sh", ".command")) else 3


def _diff(commit: str, nur: set[str] | None = None, kurztitel: str | None = None
          ) -> tuple[dict[str, tuple[str, int]], list[str], list[str]]:
    """Inhalte der zur Kette gehoerigen Dateien gegen <commit>.
    Rueckgabe: (eintraege {datei: (abschnitt, vorrang)}, fremd_zeilen, kette_dateien)."""
    kette, fremd = _aenderungen(commit, kurztitel, nur)
    neu = set(_git("ls-files", "--others", "--exclude-standard").split())
    eintraege: dict[str, tuple[str, int]] = {}
    for d in kette:
        nicht_genannt = nur is None or d not in nur
        aktuell = (ROOT / d).read_text(encoding="utf-8", errors="replace").splitlines()
        nummeriert = [f"{i:4d}  {z}" for i, z in enumerate(aktuell, 1)]
        if d in neu:
            inhalt = _kappen(d, nummeriert, "neu", PAKET_DATEI_ZEILEN, nicht_genannt)
        else:
            diff = _git("diff", "-U3", commit, "--", d).splitlines()
            if len(diff) > len(aktuell):
                inhalt = _kappen(d, nummeriert, "umbau", PAKET_DATEI_ZEILEN, nicht_genannt)
            else:
                inhalt = _kappen(d, diff, "diff", PAKET_DIFF_ZEILEN, nicht_genannt)
        eintraege[d] = (inhalt, _vorrang(d, nur))
    fremd_zeilen = [f"- `{d}` – " + (", ".join(f"`{h}` ({b})" for h, b in dc) or "ohne Commit-Angabe")
                    + " – nicht Teil dieser Kette, nicht bewerten, nur zur Kenntnis"
                    for d, dc in fremd]
    return eintraege, fremd_zeilen, kette


def _kappen(datei: str, zeilen: list[str], art: str, grenze: int, nicht_genannt: bool = False) -> str:
    was = {"neu": "neue Datei, mit Zeilennummern", "umbau": "stark umgebaut – aktuelle Datei mit Zeilennummern",
           "diff": "Diff"}[art]
    kopf = f"### {datei} ({was}, {len(zeilen)} Zeilen)"
    if nicht_genannt:
        kopf += "\n> **nicht in der Uebergabe genannt** – moeglicherweise ausserhalb des Auftrags"
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
        eintraege, fremd_zeilen, kette = _diff(commit, nur, kurztitel)
    except subprocess.CalledProcessError as e:
        say(f"git-Fehler: {(e.stderr.strip().splitlines() or ['?'])[0]}"); return 2

    def bauen(drin: dict[str, tuple[str, int]], weg: list[str]) -> str:
        code = "\n\n".join(drin[d][0] for d in sorted(drin)) or "(keine Code-Aenderungen gegen den Ruecksetzpunkt)"
        weg_zeilen = []
        for d in sorted(weg):
            grund = {2: "Testcode", 3: "Testdaten"}.get(_vorrang(d, nur), "?")
            zusatz = " (nicht in der Uebergabe genannt)" if nur is None or d not in nur else ""
            weg_zeilen.append(f"- `{d}` – {grund}, Paket zu gross{zusatz}")
        teile = [
            f"# Review-Paket: {kurztitel}\n",
            f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
            f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in sorted(drin)) or 'keine'}.\n"
            "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
            "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
            "## 1. Anforderung (verbindlich, woertlich)\n\n"
            + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
            f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
            f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
            f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
            f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
            f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
            f"## 3. Code-Aenderungen gegen `{commit}`\n\n{code}",
        ]
        if fremd_zeilen:
            teile.append("## 3a. Fremde Aenderungen (nur Liste)\n\nDiese Dateien wurden nur in Commits ohne den "
                         f"Kurztitel `{kurztitel}` geaendert. Sie gehoeren nicht zur Aufgabe – nicht bewerten.\n\n"
                         + "\n".join(fremd_zeilen))
        if weg_zeilen:
            teile.append("## 3b. Weggelassen (Paket zu gross)\n\nTeil der Kette, aber wegen der Paketgroesse "
                         "ohne Inhalt. Bei Bedarf gezielt nachlesen.\n\n" + "\n".join(weg_zeilen))
        skript = ROOT / "tests" / f"test_{kurztitel}.py"
        tc = _testcode(skript, _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())
        teile += [
            f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(skript)}"
            + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if tc else ""),
            "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
            + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
                or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
            f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
        ]
        return "\n\n".join(teile).rstrip() + "\n"

    # A7: Aenderungen ausserhalb docs/, aber nichts davon gehoert zur Kette -> lauter Fehler
    if not eintraege and fremd_zeilen:
        say(f"Paket ohne Code trotz Aenderungen seit {commit}: {len(fremd_zeilen)} Datei(en), davon "
            f"{len(fremd_zeilen)} fremd. Commits ohne Kurztitel '{kurztitel}' in der Nachricht? "
            "Dann Ruecksetzpunkt/Kurztitel pruefen. Exit 1, kein Paket.")
        return 1

    # A3: nach Gesamtgroesse kuerzen – erst Vorrang 3, dann 2; Vorrang 1 nie
    drin, weg = dict(eintraege), []
    text = bauen(drin, weg)
    for stufe in (3, 2):
        if len(text) <= PAKET_WARNUNG_ZEICHEN:
            break
        for d in sorted(x for x, (_, v) in drin.items() if v == stufe):
            weg.append(d); del drin[d]
            text = bauen(drin, weg)
            if len(text) <= PAKET_WARNUNG_ZEICHEN:
                break

    # A7 (Fall b): Kette-Dateien vorhanden, aber nach der Kuerzung keine mit Inhalt
    if eintraege and not drin:
        say("Paket ohne Code trotz Aenderungen: alle Dateien der Kette mussten weggelassen werden. Exit 1, kein Paket.")
        return 1

    groesse = len(text)
    # A4: harte Obergrenze vor dem Schreiben
    if groesse > KETTE_PAKET_MAX:
        say(f"Paket passt nicht in den Kontext des Review-Modells, Review in Teilen noetig "
            f"({groesse} Zeichen > KETTE_PAKET_MAX {KETTE_PAKET_MAX}). Exit 1, kein Paket.")
        return 1
    ziel = ablage(kurztitel) / f"review_paket_{datum}_{kurztitel}.md"
    ziel.write_text(text, encoding="utf-8")
    say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)"
        + (f", {len(weg)} Datei(en) weggelassen" if weg else "") + (f", {len(fremd_zeilen)} fremd" if fremd_zeilen else ""))
    if groesse > PAKET_WARNUNG_ZEICHEN:
        say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen (nur noch Vorrang 1) – fuer 64K Kontext eng.")
    if not pr_p:
        say("Hinweis: keine pruefung_*-Datei – erst `kette.py pruefen <kurztitel>` laufen lassen.")
    return 0

# ---------------------------------------------------------------- zusammenfuehren

def _befunde(text: str) -> list[dict]:
    return tabelle(abschnitt(text, "Befunde"))


def _ist_hoch(zeile: dict) -> bool:
    schwere = (spalte(zeile, "schwere") or "").lower()
    return "hoch" in schwere or any(ja(spalte(zeile, n)) for n in ("datenverl", "unbemerkt", "harte"))


# A4: Modell hat Befund selbst zurückgezogen
def _zurueckgezogen(text: str) -> bool:
    """Wahr, wenn der Befundtext (ohne *, rechts gestrippt) auf 'Korrekt.' oder 'Befund entfällt.' endet."""
    bereinigt = text.replace("*", "").rstrip()
    return bereinigt.endswith("Korrekt.") or bereinigt.endswith("Befund entfällt.")


def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
    if len(pfade) < 2:
        if _internal:
            print("Nur ein Verdikt – Gesamtbefund wird mit Warnung geschrieben.")
            # Gesamtbefund mit UNVOLLSTÄNDIG schreiben
            p = pfade[0]
            m = re.match(r"verdict_(\d{8})_(.+?)_[^_]+(?:_[^_]+)*\.md$", p.name)
            datum = m.group(1) if m else dt.date.today().strftime("%Y%m%d")
            kt = re.match(r"verdict_\d{8}_([a-z0-9_]+?)_(?:qwen|gemma|mellum|apertus|claude|hawe)", p.name)
            kurz = kt.group(1) if kt else "review"
            text = p.read_text(encoding="utf-8")
            m2 = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis") or text)
            ergebnis = m2.group(1) if m2 else "?"
            teile = [f"# Gesamtbefund: {kurz}\n",
                     f"Mechanisch zusammengeführt mit `kette.py zusammenfuehren` ({dt.datetime.now():%Y-%m-%d %H:%M}). Kein Befund wurde weggelassen oder umformuliert.\n",
                      "## Ergebnis\n", f"**UNVOLLSTÄNDIG** – Nur ein Lauf mit auswertbarer Befund-Tabelle.\n",
                     "| Lauf | Ergebnis des Laufs |", "|---|---|",
                      f"| `{p.name}` | {ergebnis.replace('PASS', 'UNVOLLSTÄNDIG')} |",
                     "",
                     "> Ein weiterer Lauf fehlt. Der Gesamtbefund beruht auf nur einem Lauf mit auswertbarer Tabelle.\n"]
            ziel = ablage(kurz) / f"gesamt_{datum}_{kurz}.md"
            ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
            print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
            return 1
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
            zeilen.append((p.name, "?", "(keine Befundtabelle erkannt – Verdikt von Hand lesen)", "", False, False))
        for b in befunde:
            schwere = spalte(b, "schwere") or "?"
            text_b = spalte(b, "befund", "begründung", "begruendung") or " | ".join(v for v in b.values() if v)
            ort = spalte(b, "datei", "zeile", "anfor") or ""
            h = _ist_hoch(b)
            z = _zurueckgezogen(text_b)
            zeilen.append((p.name, schwere, text_b, ort, h, z))
    if fehlt:
        print("Fehlt: " + ", ".join(fehlt)); return 2
    hoch = [z for z in zeilen if z[4] and not z[5]]
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
    for n, s_, t, o, h, z in zeilen:
        if h and z:
            hoch_zeig = "nein (zurückgezogen)"
        elif h:
            hoch_zeig = "ja"
        else:
            hoch_zeig = "nein"
        teile.append(f"| `{n}` | {s_} | {hoch_zeig} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
    ziel = ablage(kurz) / f"gesamt_{datum}_{kurz}.md"
    ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
    zurueckgezogen = len([z for z in zeilen if z[5]])
    zeile_zur = f", {zurueckgezogen} zurückgezogen" if zurueckgezogen else ""
    print(f"{len(zeilen)} Befunde aus {len(ergebnisse)} Läufen, davon {len(hoch)} hoch{zeile_zur} -> {urteil_}")
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
        abl = ablage(kurztitel)
        abl.mkdir(parents=True, exist_ok=True)
        ziel = abl / f"anforderung_{d}_{kurztitel}.md"
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
    ziel_datei = ablage(kurztitel) / f"quellen_{d}_{kurztitel}.md"
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
    paket_pfad = f"{_ablage_rel(kurztitel)}/review_paket_{datum}_{kurztitel}.md"
    if schritt in ("review", "review2", "tief"):
        if paket(kurztitel, commit if commit != "<HASH>" else None, None, still=False) != 0:
            print("Hinweis: Review-Paket nicht gebaut (siehe oben) – Prompt verweist trotzdem darauf.",
                  file=sys.stderr)
    anf_pfad = f"{_ablage_rel(kurztitel)}/{anf.name}" if anf else \
        f"{_ablage_rel(kurztitel)}/anforderung_{datum}_{kurztitel}.md"
    if not anf:
        print(f"Hinweis: {anf_pfad} fehlt. Anlegen mit: kette.py anforderung {kurztitel} --aufgabe \"…\"",
              file=sys.stderr)
    text = (vorlage.read_text(encoding="utf-8"))
    # K13a: Pfade in der Ablage der Kette nennen — vor Platzhalter-Ersetzung (Nachbesserung 1 E4)
    text = _ablage_text(text, kurztitel)
    text = (text.replace("{kurztitel}", kurztitel)
              .replace("{datum}", datum)
              .replace("{commit}", commit)
              .replace("{anforderung}", anf_pfad)
              .replace("{quellen}", f"{_ablage_rel(kurztitel)}/quellen_{datum}_{kurztitel}.md")
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

# ---------------------------------------------------------------- review-auto

KETTE_LLM_URL = os.environ.get("KETTE_LLM_URL", "http://127.0.0.1:8080")
KETTE_LLM_MODEL = os.environ.get("KETTE_LLM_MODEL", "unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL")
KETTE_LLM_TIMEOUT = int(os.environ.get("KETTE_LLM_TIMEOUT", "1800"))
KETTE_LLM_MAX_TOKENS = int(os.environ.get("KETTE_LLM_MAX_TOKENS", "8000"))
# Leer = Sampling-Werte des Servers (config/models.ini, fuer Qwen 0.6/0.95/20). Frueher fest 0.1:
# niedrige Temperatur ohne Denkphase fuehrte beim 35B zu Wiederholungsschleifen bis max_tokens.
KETTE_LLM_TEMPERATURE = os.environ.get("KETTE_LLM_TEMPERATURE", "")
KETTE_ABGESCHNITTEN = Path(os.environ.get("KETTE_ABGESCHNITTEN", "/tmp"))
KETTE_HERZSCHLAG_S = int(os.environ.get("KETTE_HERZSCHLAG_S", "60"))


def _rel(pfad):
    """Pfad relativ zu ROOT, falls möglich, sonst absolut."""
    try:
        return pfad.relative_to(ROOT)
    except ValueError:
        return pfad


# ------------------------------------------------------------------ review-auto (A2–A8)


def _herzschlag_stopp_event(lauf_nummer: int):
    """Starter fuer den Herzschlag-Thread. Gibt (event, thread) zurueck."""
    stop = threading.Event()

    def pulse():
        start = dt.datetime.now()
        while not stop.is_set():
            elapsed = int((dt.datetime.now() - start).total_seconds())
            print(f"Lauf {lauf_nummer}: {elapsed // 60} min …", flush=True)
            stop.wait(KETTE_HERZSCHLAG_S)

    t = threading.Thread(target=pulse, daemon=True)
    t.start()
    return stop, t


def _api_ruf(prompt_text: str, lauf_nummer: int) -> tuple[str | None, dict]:
    """POST auf <KETTE_LLM_URL>/v1/chat/completions. Rueckgabe: (text, info_dict)."""
    import urllib.error
    import urllib.parse
    import urllib.request

    url = KETTE_LLM_URL
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""
    if hostname not in ("127.0.0.1", "localhost"):
        print(f"Nur 127.0.0.1 erlaubt, Host '{hostname}' abgelehnt."); return None, {}

    nutzlast = {
        "model": KETTE_LLM_MODEL,
        "messages": [{"role": "user", "content": prompt_text}],
        "max_tokens": KETTE_LLM_MAX_TOKENS,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if KETTE_LLM_TEMPERATURE:
        nutzlast["temperature"] = float(KETTE_LLM_TEMPERATURE)
    body = json.dumps(nutzlast).encode("utf-8")
    req = urllib.request.Request(url + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=KETTE_LLM_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_err = e.read().decode("utf-8", errors="replace")[:200]
        print(f"Router meldet HTTP {e.code}: {body_err}"); return None, {}
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, socket.timeout):
            print(f"Zeitüberschreitung nach {KETTE_LLM_TIMEOUT} s"); return None, {}
        print(f"Router nicht erreichbar: {reason}"); return None, {}
    except socket.timeout:
        print(f"Zeitüberschreitung nach {KETTE_LLM_TIMEOUT} s"); return None, {}
    except TimeoutError:
        print(f"Zeitüberschreitung nach {KETTE_LLM_TIMEOUT} s"); return None, {}

    choices = data.get("choices") or []
    if not choices:
        print("leere Modellantwort"); return None, {}
    content = (choices[0].get("message") or {}).get("content")
    if not content:
        print("leere Modellantwort"); return None, {}
    finish = (choices[0].get("finish_reason") or "")
    if finish == "length":
        n = (data.get("usage") or {}).get("completion_tokens")
        ziel = KETTE_ABGESCHNITTEN / f"kette_abgeschnitten_lauf{lauf_nummer}.md"
        try:
            ziel.write_text(content, encoding="utf-8")
        except OSError:
            ziel = None
        print(f"Antwort abgeschnitten (finish_reason=length) nach {n} Token "
              f"(KETTE_LLM_MAX_TOKENS={KETTE_LLM_MAX_TOKENS}). Text: {ziel} – "
              f"auf Wiederholungsschleife pruefen, bevor das Limit erhoeht wird."); return None, {}

    usage = (data.get("usage") or {})
    return content, {"prompt_tokens": usage.get("prompt_tokens"),
                     "completion_tokens": usage.get("completion_tokens")}


def _freier_verdiktpfad(datum: str, kurztitel: str, lauf: int) -> Path:
    """Exklusiver Verdikt-Pfad mit automatischem Zähler (_2, _3 …)."""
    modellkuerzel = "qwen36-35b"
    basis = f"verdict_{datum}_{kurztitel}_{modellkuerzel}"
    if lauf == 2:
        basis += "_betrieb"
    zaehler = 1
    abl = ablage(kurztitel)
    while True:
        if zaehler > 1:
            pfad = abl / f"{basis}_{zaehler}.md"
        else:
            pfad = abl / f"{basis}.md"
        if not pfad.exists():
            return pfad
        zaehler += 1


def _ist_auswertbar(verdikt_text: str) -> bool:
    """Prueft, ob das Verdikt eine auswertbare Befund-Tabelle hat."""
    bef_block = abschnitt(verdikt_text, "Befunde")
    if not bef_block:
        return False
    rows = tabelle(bef_block)
    if not rows:
        return False
    required = {"datenverl", "unbemerkt", "harte", "schwere"}
    kopf = set(rows[0].keys())
    return all(any(r in k for k in kopf) for r in required)


# ---------------------------------------------------------------- review-auto

def review_auto(kurztitel: str) -> int:
    """Review-Paket bauen, zwei API-Laeufe, Verdikte speichern, zusammenfuehren."""
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2

    # A2: Pruefung, Abbruch bei roten Unit-Tests
    teile_dict = _pruefen_teile(kurztitel)
    unit_code = teile_dict["unittest"][0]
    if unit_code != 0:
        if unit_code == 2:
            print(f"Pruefung-Fehler (Exit 2) – Review nicht moeglich."); return 2
        print("Unit-Tests rot – direkt nachbessern, kein Review nötig"); return 1

    # A3: Review-Paket bauen
    if paket(kurztitel) != 0:
        print("Review-Paket nicht gebaut – Voraussetzung fehlt (Exit 2)."); return 2
    paket_pfad = ablage(kurztitel) / f"review_paket_{_datum_aus(datei_suchen('spec', kurztitel, None)) or dt.date.today().strftime('%Y%m%d')}_{kurztitel}.md"
    paket_text = paket_pfad.read_text(encoding="utf-8") if paket_pfad.exists() else ""

    datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")

    # A1: Prompt-Dateien laden, {paket_text} ersetzen
    prompt1 = (PROMPTS / "review_api.md").read_text(encoding="utf-8").replace("{paket_text}", paket_text).replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", "").replace("{datum_heute}", dt.datetime.now().strftime("%Y-%m-%d")).replace("{modell}", KETTE_LLM_MODEL)
    prompt2 = (PROMPTS / "review2_api.md").read_text(encoding="utf-8").replace("{paket_text}", paket_text).replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", "").replace("{datum_heute}", dt.datetime.now().strftime("%Y-%m-%d")).replace("{modell}", KETTE_LLM_MODEL)

    verdikt1 = verdikt2 = None
    info1 = info2 = {}
    pfad1 = pfad2 = None

    # Lauf 1
    print(f"Lauf 1 von 2 (Anforderung) gestartet")
    stop1, thread1 = _herzschlag_stopp_event(1)
    start1 = dt.datetime.now()
    try:
        verdikt1, info1 = _api_ruf(prompt1, 1)
    except Exception:
        print("Lauf 1 gescheitert – Exit 1, kein Lauf 2."); stop1.set(); thread1.join(timeout=2); return 1
    stop1.set()
    thread1.join(timeout=2)
    elapsed1 = int((dt.datetime.now() - start1).total_seconds())
    if not verdikt1:
        print("Lauf 1: keine Antwort vom Server – Exit 1, kein Lauf 2."); return 1
    print(f"Lauf 1 fertig ({elapsed1}s, {info1.get('prompt_tokens', '?')} prompt, "
          f"{info1.get('completion_tokens', '?')} completion tokens)")
    try:
        pfad1 = _freier_verdiktpfad(datum, kurztitel, 1)
        with open(pfad1, "x", encoding="utf-8") as f:
            f.write(verdikt1)
        print(f"Verdikt 1 gespeichert: {_rel(pfad1)}")
    except FileExistsError:
        zaehler = 2
        abl = ablage(kurztitel)
        while True:
            pfad1 = abl / f"verdict_{datum}_{kurztitel}_qwen36-35b_{zaehler}.md"
            if not pfad1.exists():
                with open(pfad1, "x", encoding="utf-8") as f:
                    f.write(verdikt1)
                print(f"Verdikt 1 gespeichert: {_rel(pfad1)} (Zaehler {zaehler})")
                break
            zaehler += 1

    # Lauf 2
    print(f"Lauf 2 von 2 (Betrieb) gestartet")
    stop2, thread2 = _herzschlag_stopp_event(2)
    start2 = dt.datetime.now()
    try:
        verdikt2, info2 = _api_ruf(prompt2, 2)
    except Exception:
        print("Lauf 2 gescheitert – Exit 1."); stop2.set(); thread2.join(timeout=2); return 1
    stop2.set()
    thread2.join(timeout=2)
    elapsed2 = int((dt.datetime.now() - start2).total_seconds())
    if not verdikt2:
        print("Lauf 2: keine Antwort vom Server – Exit 1."); return 1
    print(f"Lauf 2 fertig ({elapsed2}s, {info2.get('prompt_tokens', '?')} prompt, "
          f"{info2.get('completion_tokens', '?')} completion tokens)")
    try:
        pfad2 = _freier_verdiktpfad(datum, kurztitel, 2)
        with open(pfad2, "x", encoding="utf-8") as f:
            f.write(verdikt2)
        print(f"Verdikt 2 gespeichert: {_rel(pfad2)}")
    except FileExistsError:
        zaehler = 2
        abl = ablage(kurztitel)
        while True:
            pfad2 = abl / f"verdict_{datum}_{kurztitel}_qwen36-35b_betrieb_{zaehler}.md"
            if not pfad2.exists():
                with open(pfad2, "x", encoding="utf-8") as f:
                    f.write(verdikt2)
                print(f"Verdikt 2 gespeichert: {_rel(pfad2)} (Zaehler {zaehler})")
                break
            zaehler += 1

    # A6: Auswertbare Befund-Tabelle
    auswertbar1 = verdikt1 and _ist_auswertbar(verdikt1)
    auswertbar2 = verdikt2 and _ist_auswertbar(verdikt2)

    unvollstaendig = not auswertbar1 or not auswertbar2
    fehlende_datei = []
    if not auswertbar1 and pfad1:
        fehlende_datei.append(pfad1.name)
    if not auswertbar2 and pfad2:
        fehlende_datei.append(pfad2.name)

    # A7: Zusammenführen (intern, auch mit 1 oder 0 gültigen Pfaenden)
    gueltige_pfade = [p for p, aw in [(pfad1, auswertbar1), (pfad2, auswertbar2)]
                      if p and aw]
    gesamt_exit = zusammenfuehren(gueltige_pfade, _internal=True)

    # UNVOLLSTÄNDIG: bei fehlender Tabelle immer 1, Gesamtbefund anpassen
    if unvollstaendig:
        gesamt_pfad = ablage(kurztitel) / f"gesamt_{datum}_{kurztitel}.md"
        if gesamt_pfad.exists():
            text = gesamt_pfad.read_text(encoding="utf-8")
            text = text.replace("**PASS**", "**UNVOLLSTÄNDIG**")
            warnhinweis = (f"Ein Lauf ohne auswertbare Befund-Tabelle: {', '.join(fehlende_datei)} "
                           f"– Gesamtbefund beruht nur auf {len(gueltige_pfade)} Lauf/Läufen")
            text = text.replace(f"# Gesamtbefund: {kurztitel}\n",
                                f"# Gesamtbefund: {kurztitel}\n\n> {warnhinweis}\n")
            gesamt_pfad.write_text(text, encoding="utf-8")
        gesamt_exit = 1
        print(f"==> UNVOLLSTÄNDIG: Befund-Tabelle fehlt in {', '.join(fehlende_datei)}")

    # Zusammenfassung
    gesamt_pfad = ablage(kurztitel) / f"gesamt_{datum}_{kurztitel}.md"
    print(f"\n=== Zusammenfassung ===")
    if unvollstaendig:
        print("Ergebnis: UNVOLLSTÄNDIG")
    else:
        print(f"Ergebnis: {'PASS' if gesamt_exit == 0 else 'NACHBESSERN'}")
    print(f"Verdikt 1: {_rel(pfad1) if pfad1 else 'keine'}")
    print(f"Verdikt 2: {_rel(pfad2) if pfad2 else 'keine'}")
    print(f"Gesamt: {_rel(gesamt_pfad) if gesamt_pfad.exists() else 'keine'}")

    return gesamt_exit


# ---------------------------------------------------------------- umsetzung-auto (K10)
#
# Startet die Umsetzung ohne TUI ueber `opencode run --format json` (Agent umsetzung_nacht) und
# prueft danach mechanisch. Gemessen an opencode 1.19.3 (Spec-Paket §1): Exit-Code ist immer 0,
# Erfolg steht nur im JSON; `ask` wird ohne TUI sofort abgelehnt; OPENCODE_PERMISSION kann
# Agent-Regeln nicht ueberstimmen -> Sperren stehen in der Agent-Datei, Schreibgrenze prueft kette.py.

UMSETZUNG_AGENT = "umsetzung_nacht"
UMSETZUNG_MODELL_STANDARD = "llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL"
UMSETZUNG_TIMEOUT_STANDARD = 7200          # s, ganzer Lauf (A5)
UMSETZUNG_BASH_MS_STANDARD = 300000        # ms, Einzelbefehl, wertet OpenCode selbst aus (Probe P3)
# Kettendateien, die bei Nacharbeit offen sein duerfen (A2.4); Spec/Anforderung/Quellen nie.
KETTEN_PRAEFIXE = ("pruefung", "umsetzung", "review_paket", "verdict", "gesamt", "nacharbeit")
VORGABE_PRAEFIXE = ("spec_", "anforderung_", "quellen_", "_vorlage_")
ABGELEHNT_TEXTE = ("rejected permission", "rule which prevents")


def _schreibbereich(spec_text: str) -> list[str] | None:
    """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
    if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
        return None
    eintraege = []
    for z in abschnitt(spec_text, "Schreibbereich").splitlines():
        m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
        if m:
            eintraege.append(m.group(1)[2:] if m.group(1).startswith("./") else m.group(1))
    return eintraege


def _im_schreibbereich(pfad: str, eintraege: list[str]) -> bool:
    """Exakter Dateipfad oder Ordner-Eintrag mit '/' am Ende als Praefix."""
    return any(pfad == e or (e.endswith("/") and pfad.startswith(e)) for e in eintraege)


def _ist_vorgabe(pfad: str) -> bool:
    """Spec, Anforderung, Quellen, Vorlagen der Kette – darf die Umsetzung nie aendern."""
    name = Path(pfad).name
    return name.endswith(".md") and name.startswith(VORGABE_PRAEFIXE)


def _ist_kettendatei(pfad: str, kurztitel: str) -> bool:
    """Von der Kette erzeugte Datei dieses Kurztitels in docs/projekt_management/ (ohne Vorgaben).
    
    Erkennen auch im Ablage-Ordner docs/projekt_management/<kurztitel>/ (K13a).
    """
    p = Path(pfad)
    muster = rf"^(?:{'|'.join(KETTEN_PRAEFIXE)})_\d{{8}}_{re.escape(kurztitel)}(?:_[\w.-]+)?\.md$"
    # Erst im Ablage-Ordner der Kette prüfen
    ordner = f"docs/projekt_management/{kurztitel}"
    if p.parent.as_posix() == ordner:
        return re.match(muster, p.name) is not None
    # Dann flach in docs/projekt_management/
    if p.parent.as_posix() == "docs/projekt_management":
        return re.match(muster, p.name) is not None
    return False


def _offene_dateien() -> list[str] | None:
    """Pfade aus `git status --porcelain -z --untracked-files=all` (geaendert, vorgemerkt, neu, geloescht).
    -z: keine Anfuehrungszeichen, Umbenennungen liefern Ziel und Quelle. None bei git-Fehler."""
    r = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "-z", "--untracked-files=all"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    teile, pfade, i = r.stdout.split("\0"), [], 0
    while i < len(teile):
        eintrag = teile[i]
        i += 1
        if len(eintrag) < 4:
            continue
        status, pfad = eintrag[:2], eintrag[3:]
        pfade.append(pfad)
        if "R" in status or "C" in status:       # Umbenennung/Kopie: naechstes Feld ist die Quelle
            if i < len(teile) and teile[i]:
                pfade.append(teile[i])
            i += 1
    return sorted(set(pfade))


def _stand() -> dict[str, str] | None:
    """Pruefsummen aller offenen Dateien: {pfad: sha256 | '<geloescht>' | '<unlesbar>'} (A7)."""
    pfade = _offene_dateien()
    if pfade is None:
        return None
    stand = {}
    for d in pfade:
        p = ROOT / d
        if not p.exists():
            stand[d] = "<geloescht>"
        elif p.is_file():
            try:
                stand[d] = hashlib.sha256(p.read_bytes()).hexdigest()
            except OSError:
                stand[d] = "<unlesbar>"
        else:
            stand[d] = "<kein-file>"
    return stand


def _in_diesem_lauf(vor: dict[str, str], nach: dict[str, str]) -> dict[str, str]:
    """{pfad: 'neu'|'weg'|'geaendert'} fuer alles, was sich zwischen den Schnappschuessen unterscheidet.
    Eine vorher saubere Datei, die der Lauf aendert, taucht nur in `nach` auf -> 'neu' (= jetzt offen)."""
    raus = {}
    for d in sorted(set(vor) | set(nach)):
        if d not in vor:
            raus[d] = "neu"
        elif d not in nach:
            raus[d] = "weg"
        elif vor[d] != nach[d]:
            raus[d] = "geaendert"
    return raus


PROTOKOLL_RE = re.compile(r"rot: (?P<rot>[^,]+), pruefen: (?P<pruefen>[^,]+), art: (?P<art>erst|nb\d+)")


def _protokoll(pfad: Path) -> list[dict]:
    """Protokollzeilen (A6) in Dateireihenfolge: [{'rot', 'pruefen', 'art'}, ...]."""
    if not pfad.is_file():
        return []
    zeilen = []
    for z in pfad.read_text(encoding="utf-8").splitlines():
        if not z.startswith("- **"):            # nur Laufzeilen; Unterzeilen enthalten fremden Befehlstext
            continue
        m = PROTOKOLL_RE.search(z)
        if m:
            zeilen.append({k: m.group(k).strip() for k in ("rot", "pruefen", "art")})
    return zeilen


def _zahl(wert: str) -> int | None:
    return int(wert) if re.fullmatch(r"\d+", str(wert).strip()) else None


def _fortschritt(alt: dict, neu: dict) -> bool:
    """A8: rot bekannt und gesunken ODER pruefen bekannt und kleiner – und keiner der beiden schlechter.
    Unbekannte Werte ('–') zaehlen nie als Fortschritt."""
    ar, nr, ap, np_ = _zahl(alt["rot"]), _zahl(neu["rot"]), _zahl(alt["pruefen"]), _zahl(neu["pruefen"])
    if None in (ar, nr, ap, np_):
        return False
    return (nr < ar or np_ < ap) and nr <= ar and np_ <= ap


def _halt_noetig(zeilen: list[dict]) -> bool:
    """Die letzten zwei nb-Laeufe zeigten beide keinen Fortschritt gegenueber ihrem jeweiligen Vorlauf."""
    nb = [i for i, z in enumerate(zeilen) if z["art"].startswith("nb") and i > 0]
    if len(nb) < 2:
        return False
    return all(not _fortschritt(zeilen[i - 1], zeilen[i]) for i in nb[-2:])


def _rot_aus_pruefung(kurztitel: str) -> str:
    """failures+errors aus der unittest-Ausgabe der pruefung-Datei; 'OK' -> 0; sonst '–' (A6)."""
    pfad = datei_suchen("pruefung", kurztitel, None)
    if not pfad:
        return "–"
    ut = abschnitt(pfad.read_text(encoding="utf-8"), "unittest")
    m = re.search(r"^FAILED \(([^)]*)\)", ut, re.M)
    if m:
        werte = dict(re.findall(r"(\w+)=(\d+)", m.group(1)))
        return str(int(werte.get("failures", 0)) + int(werte.get("errors", 0)))
    if re.search(r"^OK\b", ut, re.M):
        return "0"
    return "–"


def _opencode_programm() -> list[str] | None:
    """KETTE_OPENCODE (Pfad; .py wird mit sys.executable gestartet) oder `opencode` im PATH."""
    eigen = os.environ.get("KETTE_OPENCODE", "").strip()
    if eigen:
        if not Path(eigen).is_file():
            return None
        return [sys.executable, eigen] if eigen.endswith(".py") else [eigen]
    gefunden = shutil.which("opencode")
    return [gefunden] if gefunden else None


def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path | None, nb: int) -> str | None:
    vorlage = PROMPTS / "umsetzung_nacht.md"
    if not vorlage.is_file():
        return None
    anf = datei_suchen("anforderung", kurztitel, None)
    anf_pfad = f"{_ablage_rel(kurztitel)}/{anf.name}" if anf else \
        f"{_ablage_rel(kurztitel)}/anforderung_{datum}_{kurztitel}.md"
    text = (vorlage.read_text(encoding="utf-8"))
    # K13a: Pfade in der Ablage der Kette nennen — vor Platzhalter-Ersetzung (Nachbesserung 1 E4)
    text = _ablage_text(text, kurztitel)
    text = (text.replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", commit)
              .replace("{anforderung}", anf_pfad)
              .replace("{quellen}", f"{_ablage_rel(kurztitel)}/quellen_{datum}_{kurztitel}.md"))
    text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
    # A1: Pflichtzeilen im Handover – nach Grundtext, vor Nachbesserung
    spec_p = datei_suchen("spec", kurztitel, None)
    if spec_p:
        spec_tests = tests_finden(spec_p.read_text(encoding="utf-8"))
        if spec_tests:
            zeilen = ["", "## Pflichtzeilen im Handover",
                      'Unter „## Getestet" steht für jede Test-ID genau eine dieser Zeilen (Titel unverändert, Status wählen):']
            for tid, titel in spec_tests.items():
                zeilen.append(f"**{tid}: {titel}** – bestanden | fehlgeschlagen")
            zeilen.append('Unter „## Nicht getestet" nur Test-IDs, die wirklich nicht getestet sind – keine Sammelangaben wie „T1–T5".')
            text += "\n".join(zeilen) + "\n"
    if spec_p and _vorgabe_tests(spec_p.read_text(encoding="utf-8")):
        text += ("\n## Vorgabe-Tests\n\nAbweichend von den Testregeln oben: Die Tests stehen schon in "
                 f"tests/test_{kurztitel}.py. Du änderst diese Datei nicht – keine Zeile. Schreib nur den Code, "
                 f"bis python3 -m unittest -v tests/test_{kurztitel}.py grün ist. Passt ein Test nicht zur Spec, "
                 "nenne ihn im Handover unter „Abweichungen“.\n")
    if nacharbeit:
        nacharbeit_text = nacharbeit.read_text(encoding="utf-8").strip()
        handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
        handover_rel = _ablage_text(handover_rel, kurztitel)
        text += (f"\n## Nachbesserung {nb}\n\nDas ist Nachbesserung {nb}. Der Auftrag steht unten (aus "
                 f"`{_rel(nacharbeit)}`). Ergänze den Handover {handover_rel} um den Abschnitt „## Nachbesserung {nb}\" – nichts Bestehendes löschen.\n\n"
                 + nacharbeit_text + "\n")
    return text


def _lauf(befehl: list[str], env: dict, timeout: int, rohdaten: Path) -> dict:
    """Startet opencode in eigener Prozessgruppe, liest den JSON-Strom zeilenweise (sofort in die
    Rohdaten), gibt je Werkzeugaufruf eine Zeile aus und beendet die Gruppe nach `timeout` s (A5, A6, A9)."""
    info = {"werkzeuge": 0, "fehler": [], "abgelehnt": [], "tokens": 0, "tokens_spitze": 0, "reason": None, "text": "",
            "ereignisse": 0, "kaputt": 0, "timeout": False,
            "tokens_teile": {"input": 0, "output": 0, "reasoning": 0}}
    rohdaten.parent.mkdir(parents=True, exist_ok=True)
    stderr_datei = rohdaten.with_suffix(".err")
    start = dt.datetime.now()
    with open(rohdaten, "w", encoding="utf-8") as roh, open(stderr_datei, "w", encoding="utf-8") as fehlerkanal:
        try:
            proc = subprocess.Popen(befehl, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=fehlerkanal,
                                    text=True, encoding="utf-8", errors="replace", start_new_session=True)
        except OSError as e:
            info["startfehler"] = f"{type(e).__name__}: {e}"
            info["dauer"] = 0
            return info

        def lesen():
            for zeile in proc.stdout:
                roh.write(zeile); roh.flush()
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    e = json.loads(zeile)
                except json.JSONDecodeError:
                    info["kaputt"] += 1
                    continue
                info["ereignisse"] += 1
                teil = e.get("part") or {}
                typ = e.get("type")
                if typ == "tool_use":
                    zustand = teil.get("state") or {}
                    status = zustand.get("status")
                    if status not in ("completed", "error"):
                        continue
                    info["werkzeuge"] += 1
                    eingabe = zustand.get("input")
                    wortlaut = (eingabe.get("command") or eingabe.get("filePath") or json.dumps(eingabe,
                                ensure_ascii=False)) if isinstance(eingabe, dict) else str(eingabe or "")
                    kurz = wortlaut.replace("\n", " ")[:60]
                    print(f"[{dt.datetime.now():%H:%M:%S}] {teil.get('tool', '?')}: {kurz}"
                          + ("…" if len(wortlaut) > 60 else "") + ("  [FEHLER]" if status == "error" else ""),
                          flush=True)
                    if status == "error":
                        fehlertext = str(zustand.get("error") or "")
                        eintrag = f"{teil.get('tool', '?')}: {wortlaut[:200]} – {fehlertext[:200]}".replace("\n", " ")
                        info["fehler"].append(eintrag)
                        if any(t in fehlertext for t in ABGELEHNT_TEXTE):
                            info["abgelehnt"].append(eintrag)
                elif typ == "step_finish":
                    info["reason"] = teil.get("reason")
                    tok = teil.get("tokens") or {}
                    total = int(tok.get("total") or 0)
                    info["tokens"] += total
                    if total > info["tokens_spitze"]:
                        info["tokens_spitze"] = total
                    for k in info["tokens_teile"]:
                        info["tokens_teile"][k] += int(tok.get(k) or 0)
                elif typ == "text":
                    info["text"] = teil.get("text") or info["text"]

        leser = threading.Thread(target=lesen, daemon=True)
        leser.start()
        stopp = threading.Event()

        def puls():
            while not stopp.wait(KETTE_HERZSCHLAG_S):
                minuten = int((dt.datetime.now() - start).total_seconds()) // 60
                print(f"[{dt.datetime.now():%H:%M:%S}] Lebenszeichen, Lauf läuft seit {minuten} min", flush=True)

        herz = threading.Thread(target=puls, daemon=True)
        herz.start()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            info["timeout"] = True
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                info["haengt"] = True
        finally:
            stopp.set()
        leser.join(timeout=10)
    info["dauer"] = int((dt.datetime.now() - start).total_seconds())
    return info


def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
    """K10: Umsetzung bzw. Nacharbeit ueber `opencode run` ohne TUI, danach mechanisch pruefen.
    Exit 0 = abgeschlossen + keine Verletzung + pruefen 0; 1 = Lauf/Pruefung nicht in Ordnung; 2 = Voraussetzung."""
    def nein(meldung: str, code: int = 2) -> int:
        print(meldung, file=sys.stderr)
        return code

    # A2.1 Kurztitel
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        return nein(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).")
    # A2.2 Spec-Commit
    commit = spec_commit(kurztitel)
    if not commit:
        return nein(f"Kein Commit 'Spec {kurztitel}' gefunden – erst die Spec committen.")
    # A2.3 Spec mit Schreibbereich
    spec_p = datei_suchen("spec", kurztitel, None)
    if not spec_p:
        return nein(f"Keine Spec spec_<datum>_{kurztitel}.md in {_rel(PM)}.")
    bereich = _schreibbereich(spec_p.read_text(encoding="utf-8"))
    if bereich is None:
        return nein(f"Spec {spec_p.name} hat keinen Abschnitt '## Schreibbereich'. Spec um '## Schreibbereich' "
                    "ergaenzen (Dateien/Ordner, die die Umsetzung aendern darf), sonst kein umsetzung-auto-Lauf.")
    if not bereich:
        return nein(f"'## Schreibbereich' in {spec_p.name} ist leer – mindestens einen Pfad eintragen.")
    for e in bereich:
        if _ist_vorgabe(e):
            print(f"Hinweis: Schreibbereich nennt {e} – Vorgaben (spec_/anforderung_/quellen_/_vorlage_) "
                  "sind nie erlaubt; eine Änderung daran endet in (b) mit Exit 1.", file=sys.stderr)
    datum = _datum_aus(spec_p) or dt.date.today().strftime("%Y%m%d")
    testdatei = f"tests/test_{kurztitel}.py"
    handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
    handover_rel = _ablage_text(handover_rel, kurztitel)
    protokoll_p = ablage(kurztitel) / f"umsetzung_{datum}_{kurztitel}.md"
    nach_p = None
    if nacharbeit:
        nach_p = Path(nacharbeit)
        if not nach_p.is_absolute():
            nach_p = (ROOT / nach_p) if (ROOT / nach_p).is_file() else nach_p.resolve()
        if not nach_p.is_file():
            return nein(f"Nacharbeitsdatei {nacharbeit} nicht gefunden.")
    # A2.4 Arbeitsstand
    offen = _offene_dateien()
    if offen is None:
        return nein("git status fehlgeschlagen – ist ROOT ein Git-Repo?")
    if not nach_p:
        if offen:
            return nein("Arbeitsstand nicht sauber – ohne --nacharbeit muss alles committet sein:\n"
                        + "\n".join(f"  {d}" for d in offen))
    else:
        try:
            nach_rel = nach_p.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            nach_rel = None
        fremd = [d for d in offen
                 if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d == testdatei or d == handover_rel
                                             or _ist_kettendatei(d, kurztitel) or d == nach_rel)]
        if fremd:
            return nein("Nacharbeit: unzulaessige offene Aenderungen (Vorgaben oder ausserhalb von Schreibbereich/"
                        "Testdatei/Kettendateien):\n" + "\n".join(f"  {d}" for d in fremd))
    # K11a: Vorgabe-Tests
    vorgabe = _vorgabe_tests(spec_p.read_text(encoding="utf-8"))
    if vorgabe:
        if not (ROOT / testdatei).is_file():
            return nein(f"Spec nennt '## Vorgabe-Tests', aber {testdatei} fehlt.")
        if nach_p and testdatei in offen:
            return nein(f"Nacharbeit: Vorgabe-Tests {testdatei} haben offene Aenderungen. Auf die Vorgabe zuruecksetzen (git restore {testdatei}) oder eine bewusste Korrektur committen – kein Lauf.")
        if not nach_p and tests_pruefen(kurztitel) != 0:
            return nein(f"Vorgabe-Tests nicht in Ordnung (kette.py tests-pruefen {kurztitel}) – kein Lauf.")
    # A2.5 opencode
    programm = _opencode_programm()
    if not programm:
        ziel = os.environ.get("KETTE_OPENCODE") or "opencode im PATH"
        return nein(f"opencode nicht gefunden ({ziel}).")
    # A2.6 Modell
    modell = os.environ.get("KETTE_UMSETZUNG_MODEL", UMSETZUNG_MODELL_STANDARD)
    if not modell.startswith("llamacpp/"):
        return nein(f"Modell '{modell}' beginnt nicht mit 'llamacpp/' (nur direkt am Router, ohne Gedaechtnis).")
    # A8 Halt-Regel und Nummer
    zeilen = _protokoll(protokoll_p)
    handover_p = ROOT / handover_rel
    handover_alt = handover_p.read_text(encoding="utf-8") if handover_p.is_file() else ""
    nb = len(re.findall(r"^## Nachbesserung\b", handover_alt, re.M)) + 1
    if nach_p and _halt_noetig(zeilen):
        return nein("Zwei Nachbesserungen in Folge ohne Fortschritt – keine weitere. Übergabe an Hawe.", 1)
    art = f"nb{nb}" if nach_p else "erst"
    # A3 Prompt
    prompt_text = _umsetzung_prompt(kurztitel, datum, commit, nach_p, nb)
    if prompt_text is None:
        return nein(f"Prompt-Vorlage {_rel(PROMPTS / 'umsetzung_nacht.md')} fehlt.")
    try:
        timeout = int(os.environ.get("KETTE_UMSETZUNG_TIMEOUT", UMSETZUNG_TIMEOUT_STANDARD))
        bash_ms = int(os.environ.get("OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS", UMSETZUNG_BASH_MS_STANDARD))
    except ValueError:
        return nein("KETTE_UMSETZUNG_TIMEOUT / OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS muessen ganze Zahlen sein.")

    # A7 Schnappschuss VOR dem Start
    head_vor = _git("rev-parse", "HEAD").strip()
    stand_vor = _stand()
    if stand_vor is None:
        return nein("git status fehlgeschlagen.")
    befehl = programm + ["run", "--format", "json", "--agent", UMSETZUNG_AGENT, "--model", modell,
                         "--dir", str(ROOT), "--title", f"kette {kurztitel} {art}", prompt_text]
    env = dict(os.environ, OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=str(bash_ms))
    rohdaten = ROOT / "role-split" / "results" / f"umsetzung_auto_{datum}_{kurztitel}_{dt.datetime.now():%H%M%S}.jsonl"
    print(f"umsetzung-auto {kurztitel} ({art}): Modell {modell}, Agent {UMSETZUNG_AGENT}, "
          f"Zeitlimit {timeout} s, Rücksetzpunkt {commit}", flush=True)
    info = _lauf(befehl, env, timeout, rohdaten)

    # A7 Schnappschuss SOFORT nach dem Lauf, bevor kette.py selbst etwas schreibt
    stand_nach = _stand() or {}
    head_nach = _git("rev-parse", "HEAD").strip()
    aenderungen = _in_diesem_lauf(stand_vor, stand_nach)
    abgeschlossen = not info["timeout"] and info["reason"] == "stop"
    befunde = []

    if info.get("haengt"):
        befunde.append("opencode reagiert 30 s nach SIGKILL nicht – Prozess pruefen (ps).")
    if info.get("startfehler"):
        befunde.append(f"opencode liess sich nicht starten: {info['startfehler']}")
    elif info["timeout"]:
        befunde.append(f"Timeout nach {timeout} s – opencode samt Unterprozessen beendet.")
    elif info["ereignisse"] == 0:
        befunde.append("Keine gültigen JSON-Ereignisse von opencode.")
    elif info["reason"] != "stop":
        befunde.append(f"Lauf nicht abgeschlossen (reason: {info['reason']}).")
    # (a) immer
    if head_vor != head_nach:
        befunde.append(f"Selbst-Commit: HEAD {head_vor[:7]} -> {head_nach[:7]} (nichts zurückgesetzt).")
    # (b) immer
    if vorgabe and testdatei in aenderungen:
        befunde.append(f"Vorgabe-Tests in diesem Lauf geändert: {testdatei} ({aenderungen[testdatei]}) – "
                       "nichts zurückgesetzt.")
    verstoesse = [(d, a) for d, a in aenderungen.items()
                  if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d in (testdatei, handover_rel))]
    if verstoesse:
        befunde.append("Schreibbereich verletzt (nichts zurückgesetzt):\n"
                       + "\n".join(f"  {d} ({a})" for d, a in verstoesse))
    # (c) und (d) nur bei abgeschlossenem Lauf
    rot, pruefen_code = "–", "–"
    if abgeschlossen:
        if handover_rel not in aenderungen or not (ROOT / handover_rel).is_file():
            befunde.append(f"Handover {handover_rel} in diesem Lauf nicht geschrieben.")
        elif nach_p and not re.search(rf"^## Nachbesserung {nb}\b",
                                      (ROOT / handover_rel).read_text(encoding="utf-8"), re.M):
            befunde.append(f"Handover {handover_rel} hat keinen Abschnitt '## Nachbesserung {nb}'.")
        code = pruefen(kurztitel)
        pruefen_code = str(code)
        rot = _rot_aus_pruefung(kurztitel)
        if code != 0:
            befunde.append(f"pruefen: Exit {code}.")
    else:
        print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")

    exit_code = 1 if befunde else 0
    reason = "timeout" if info["timeout"] else (info["reason"] or "–")
    zeile = (f"- **{dt.datetime.now():%Y-%m-%d %H:%M}** – Modell: {modell}, Dauer: {info['dauer']} s, "
             f"Tools: {info['werkzeuge']}, Fehler: {len(info['fehler'])}, Abgelehnt: {len(info['abgelehnt'])}, "
             f"Tokens: {info['tokens']}, reason: {reason}, rot: {rot}, pruefen: {pruefen_code}, art: {art}, "
             f"Exit: {exit_code}\n")
    if not protokoll_p.exists():
        protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
                               encoding="utf-8")
    tt = info["tokens_teile"]
    zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}, spitze {info['tokens_spitze']}\n"
    for e in info["fehler"]:
        zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
    with open(protokoll_p, "a", encoding="utf-8") as f:
        f.write(zeile)

    print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
    print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
          f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']} (Spitze {info['tokens_spitze']}), reason {reason}")
    for e in info["fehler"]:
        print(f"  {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}")
    if info["text"]:
        print(f"Schlusstext: {info['text'][:300]}")
    print(f"In diesem Lauf geändert: {', '.join(aenderungen) or 'nichts'}")
    for b in befunde:
        print(f"!!! {b}")
    print(f"Rohdaten: {_rel(rohdaten)}\nProtokoll: {_rel(protokoll_p)}")
    print(f"==> {'OK' if exit_code == 0 else 'NICHT IN ORDNUNG'} (Exit {exit_code})")
    return exit_code


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
    ra = sub.add_parser("review-auto", help="Review-Paket, zwei API-Laeufe, Verdikte, Zusammenfassung")
    ra.add_argument("kurztitel")
    ua = sub.add_parser("umsetzung-auto", help="Umsetzung/Nacharbeit ueber opencode run ohne TUI, danach pruefen")
    ua.add_argument("kurztitel"); ua.add_argument("--nacharbeit", help="Datei mit dem Nachbesserungs-Auftrag")
    tp = sub.add_parser("tests-pruefen", help="Vorgabe-Tests pruefen: Abdeckung, laedt, rot vorab")
    tp.add_argument("kurztitel"); tp.add_argument("--timeout", type=int, default=300)
    lf = sub.add_parser("lauf", help="Kette: Groesse -> umsetzung-auto -> review-auto -> status")
    lf.add_argument("kurztitel")
    st = sub.add_parser("status", help="Stand der Kette anzeigen, ohne etwas auszufuehren")
    st.add_argument("kurztitel")
    args = ap.parse_args(argv)
    if args.cmd == "zusammenfuehren":
        return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
                                for v in args.verdikte])
    if args.cmd == "paket":
        return paket(args.kurztitel, args.commit, args.datum)
    if args.cmd == "pruefen":
        return pruefen(args.kurztitel, args.commit, args.timeout)
    if args.cmd == "review-auto":
        return review_auto(args.kurztitel)
    if args.cmd == "umsetzung-auto":
        return umsetzung_auto(args.kurztitel, args.nacharbeit)
    if args.cmd == "tests-pruefen":
        return tests_pruefen(args.kurztitel, args.timeout)
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
    if args.cmd == "lauf":
        import automatik
        return automatik.lauf(args.kurztitel)
    if args.cmd == "status":
        import automatik
        return automatik.status(args.kurztitel)
    pfad = Path(args.verdikt)
    if not pfad.is_absolute() and not pfad.exists():
        pfad = PM / pfad.name
    return urteil(pfad, args.anhaengen)


if __name__ == "__main__":
    sys.exit(main())
