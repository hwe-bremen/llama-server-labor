#!/usr/bin/env python3
"""K12b-Messung: Rueckfragen des lokalen Modells zu erledigten Ketten.

Lab-Experiment (beruehrt AskValentinAI nicht), nur Standardbibliothek. Ausserhalb der Kette.
Ruft das Modell ueber kette._api_ruf auf - derselbe Weg wie die spaetere Kette K12b
(nur 127.0.0.1, KETTE_LLM_MODEL, KETTE_LLM_TIMEOUT, KETTE_LLM_MAX_TOKENS, thinking aus).

Liest nur: Anforderungsdateien der Ketten, eingaben/, prompt_rueckfragen.md, LERNREGELN.md.
Schreibt nur: experiments/k12b_rueckfragen/ergebnisse/<zeitstempel>/.

Aufruf (im Repo-Root):
    python3 experiments/k12b_rueckfragen/messung.py --trocken
    python3 experiments/k12b_rueckfragen/messung.py
    python3 experiments/k12b_rueckfragen/messung.py --ketten alle_tests --varianten B --wiederholungen 1

Varianten: A = fester Kontext + Anforderung; B = zusaetzlich docs/learnings/LERNREGELN.md.
Exit: 0 alle Laeufe mit Antwort, 1 mindestens ein Lauf ohne Antwort, 2 Aufruffehler.
"""
import argparse
import datetime as dt
import os
import re
import sys
import time
from pathlib import Path

HIER = Path(__file__).resolve().parent
ROOT = HIER.parents[1]
sys.path.insert(0, str(ROOT / "role-split" / "kette"))
import kette  # noqa: E402

PROMPT = HIER / "prompt_rueckfragen.md"
LERNREGELN = ROOT / "docs" / "learnings" / "LERNREGELN.md"
ERGEBNISSE = HIER / "ergebnisse"
# Kette -> Rohfassung unter eingaben/ (None = echte Anforderungsdatei lesen)
KETTEN = {"git_schutz": None, "alle_tests": None, "spec_pruefen": "spec_pruefen_roh.md"}
VARIANTEN = ("A", "B")
PLATZHALTER = ("{lernregeln}", "{aufgabe}", "{antworten}")
MAX_FRAGEN = 6
ZEICHEN_JE_TOKEN = 3.2  # grobe Schaetzung, siehe experiments/kontext_128k/m1_tempo.py


def eingabe(kt: str) -> tuple[str, str, str]:
    """(aufgabe, antworten, quelle) fuer eine Kette."""
    roh = KETTEN[kt]
    if roh:
        p = HIER / "eingaben" / roh
        return p.read_text(encoding="utf-8").strip(), "(keine)", str(p.relative_to(ROOT))
    anf = kette.datei_suchen("anforderung", kt, None)
    if anf is None:
        raise FileNotFoundError(f"Keine anforderung_*_{kt}.md")
    text = anf.read_text(encoding="utf-8")
    antworten = kette.abschnitt(text, "Antworten auf Rueckfragen").strip() or "(keine)"
    return kette.aufgabe_lesen(anf), antworten, str(anf.relative_to(ROOT))


def prompt_bauen(vorlage: str, variante: str, aufgabe: str, antworten: str) -> str:
    for p in PLATZHALTER:
        if p not in vorlage:
            raise ValueError(f"Platzhalter {p} fehlt in {PROMPT.name}")
    lr = ""
    if variante == "B":
        lr = "## Lernregeln der Kette\n\n" + LERNREGELN.read_text(encoding="utf-8").strip()
    return (vorlage.replace("{lernregeln}", lr)
            .replace("{aufgabe}", aufgabe)
            .replace("{antworten}", antworten))


def form_pruefen(text: str) -> tuple[int, list[str]]:
    """Mechanische Formpruefung. Rueckgabe (Anzahl Fragen, Befunde)."""
    t = text.strip()
    if t.startswith("Keine Rückfragen."):
        rest = t[len("Keine Rückfragen."):].strip()
        return 0, ([] if rest else ["„Keine Rückfragen.“ ohne Begründung"])
    befunde = []
    koepfe = list(re.finditer(r"^F(\d+):[ \t]*(\S.*)?$", t, re.M))
    if not koepfe:
        return 0, ["keine Frage F1: gefunden und nicht „Keine Rückfragen.“"]
    if t[:koepfe[0].start()].strip():
        befunde.append("Text vor F1")
    nummern = [int(m.group(1)) for m in koepfe]
    if nummern != list(range(1, len(nummern) + 1)):
        befunde.append(f"Nummern nicht fortlaufend: {nummern}")
    if len(koepfe) > MAX_FRAGEN:
        befunde.append(f"{len(koepfe)} Fragen > {MAX_FRAGEN}")
    annahmen = re.search(r"^Annahmen:[ \t]*$", t, re.M)
    if not annahmen:
        befunde.append("Abschnitt „Annahmen:“ fehlt")
    ende_letzte = annahmen.start() if annahmen else len(t)
    for i, m in enumerate(koepfe):
        ende = koepfe[i + 1].start() if i + 1 < len(koepfe) else ende_letzte
        block = t[m.start():ende]
        if not m.group(2):
            befunde.append(f"F{m.group(1)} ohne Fragetext")
        if not re.search(r"^[ \t]+Optionen:[ \t]*\S", block, re.M):
            befunde.append(f"F{m.group(1)} ohne „Optionen:“")
        if not re.search(r"^[ \t]+Warum:[ \t]*\S", block, re.M):
            befunde.append(f"F{m.group(1)} ohne „Warum:“")
    return len(koepfe), befunde


def uebersicht_schreiben(ziel: Path, kopf: list[str], zeilen: list[str]) -> None:
    tabelle = ["| Kette | Var. | Nr. | Dauer s | Prompt-Tok. | Antwort-Tok. | Fragen | Form | Hawe: hätte geändert? |",
               "|---|---|---|---|---|---|---|---|---|"]
    ziel.write_text("\n".join(kopf + [""] + tabelle + zeilen) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="K12b-Messung: Rueckfragen des lokalen Modells")
    ap.add_argument("--ketten", default=",".join(KETTEN))
    ap.add_argument("--varianten", default=",".join(VARIANTEN))
    ap.add_argument("--wiederholungen", type=int, default=3)
    ap.add_argument("--trocken", action="store_true", help="nur Prompts bauen, kein Modellaufruf, nichts schreiben")
    a = ap.parse_args(argv)
    ketten = [k.strip() for k in a.ketten.split(",") if k.strip()]
    varianten = [v.strip() for v in a.varianten.split(",") if v.strip()]
    if not ketten or any(k not in KETTEN for k in ketten):
        print(f"--ketten: nur {', '.join(KETTEN)}", file=sys.stderr); return 2
    if not varianten or any(v not in VARIANTEN for v in varianten):
        print("--varianten: nur A, B", file=sys.stderr); return 2
    if a.wiederholungen < 1:
        print("--wiederholungen muss >= 1 sein", file=sys.stderr); return 2

    vorlage = PROMPT.read_text(encoding="utf-8")
    auftraege = []
    for kt in ketten:
        aufgabe, antworten, quelle = eingabe(kt)
        for v in varianten:
            auftraege.append((kt, v, prompt_bauen(vorlage, v, aufgabe, antworten), quelle))

    if a.trocken:
        for kt, v, p, quelle in auftraege:
            rest = [x for x in PLATZHALTER if x in p]
            print(f"{kt:<13} {v}  {len(p):>6} Zeichen  ~{len(p) / ZEICHEN_JE_TOKEN:>6.0f} Token  "
                  f"Quelle {quelle}" + (f"  UNERSETZT {rest}" if rest else ""))
        print(f"Trocken: {len(auftraege) * a.wiederholungen} Aufrufe geplant, nichts geschrieben.")
        return 0

    stempel = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    ordner = ERGEBNISSE / stempel
    ordner.mkdir(parents=True, exist_ok=False)
    temp = os.environ.get("KETTE_LLM_TEMPERATURE") or "Server-Standard"
    kopf = [f"# K12b-Messung {stempel}", "",
            f"- Modell: `{kette.KETTE_LLM_MODEL}` über `{kette.KETTE_LLM_URL}` (kette._api_ruf, thinking aus)",
            f"- Temperatur: {temp}; max_tokens {kette.KETTE_LLM_MAX_TOKENS}; Timeout {kette.KETTE_LLM_TIMEOUT} s",
            "- Varianten: A = Kontext + Anforderung, B = zusätzlich LERNREGELN.md",
            "- Hinweis: llama-server cached gleiche Prompt-Anfänge – Wiederholungen 2/3 sind deshalb schneller.",
            "- Bewertung der Fragen: siehe schluessel.md (Kategorien K/N/B/U/S/L)."]
    zeilen = []
    uebersicht = ordner / "uebersicht.md"
    uebersicht_schreiben(uebersicht, kopf, zeilen)

    print(f"Aufwärmen (lädt das Modell, Zeit zählt nicht) …", flush=True)
    t0 = time.monotonic()
    w, _ = kette._api_ruf("Antworte nur mit: OK", 0)
    if w is None:
        print("Aufwärmen fehlgeschlagen – Router läuft? Abbruch.", file=sys.stderr); return 1
    print(f"Aufwärmen {time.monotonic() - t0:.0f} s", flush=True)

    gescheitert = 0
    nr_global = 0
    for wdh in range(1, a.wiederholungen + 1):
        for kt, v, p, _quelle in auftraege:
            nr_global += 1
            print(f"[{nr_global}/{len(auftraege) * a.wiederholungen}] {kt} {v} #{wdh}", flush=True)
            stopp, faden = kette._herzschlag_stopp_event(nr_global)
            t0 = time.monotonic()
            try:
                text, info = kette._api_ruf(p, nr_global)
            finally:
                stopp.set(); faden.join(timeout=2)
            dauer = time.monotonic() - t0
            if text is None:
                gescheitert += 1
                zeilen.append(f"| {kt} | {v} | {wdh} | {dauer:.0f} | – | – | – | GESCHEITERT (siehe Konsole) | |")
                uebersicht_schreiben(uebersicht, kopf, zeilen)
                continue
            n, befunde = form_pruefen(text)
            form = "ok" if not befunde else "; ".join(befunde)
            datei = ordner / f"{kt}_{v}_{wdh}.md"
            datei.write_text(
                f"<!-- {kt} Variante {v} Wiederholung {wdh}: {dauer:.1f} s, "
                f"prompt {info.get('prompt_tokens')}, antwort {info.get('completion_tokens')}, Form: {form} -->\n\n"
                + text.strip() + "\n", encoding="utf-8")
            zeilen.append(f"| {kt} | {v} | {wdh} | {dauer:.0f} | {info.get('prompt_tokens')} | "
                          f"{info.get('completion_tokens')} | {n} | {form} | |")
            uebersicht_schreiben(uebersicht, kopf, zeilen)
            print(f"  {dauer:.0f} s, {n} Fragen, Form: {form}", flush=True)

    print(f"\nFertig: {_rel(ordner)} – {nr_global - gescheitert} ok, {gescheitert} gescheitert.")
    return 1 if gescheitert else 0


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


if __name__ == "__main__":
    sys.exit(main())
