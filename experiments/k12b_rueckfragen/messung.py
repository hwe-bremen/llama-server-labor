#!/usr/bin/env python3
"""K12b-Messung: Rueckfragen des lokalen Modells zu erledigten Ketten.

Lab-Experiment (beruehrt AskValentinAI nicht), nur Standardbibliothek. Ausserhalb der Kette.
Ruft das Modell ueber kette._api_ruf auf - derselbe Weg wie die spaetere Kette K12b
(nur 127.0.0.1, KETTE_LLM_MODEL, KETTE_LLM_TIMEOUT, KETTE_LLM_MAX_TOKENS, thinking aus).

Liest nur: Anforderungsdateien der Ketten, eingaben/, prompt_rueckfragen.md, LERNREGELN.md und
(Varianten C/D) Dateien aus dem Repo-Stand vor der jeweiligen Spec per `git show`/`git ls-tree`.
Schreibt nur: experiments/k12b_rueckfragen/ergebnisse/<zeitstempel>/.

Aufruf (im Repo-Root):
    python3 experiments/k12b_rueckfragen/messung.py --trocken
    python3 experiments/k12b_rueckfragen/messung.py --varianten C,D
    python3 experiments/k12b_rueckfragen/messung.py --ketten alle_tests --varianten C --wiederholungen 1

Varianten:
    A = fester Kontext + Anforderung
    B = A + docs/learnings/LERNREGELN.md (heutiger Stand)
    C = A + Projektkontext vom Stand vor der Spec (kette.py-Befehle, Spec-Vorlage, Liste der Code-Dateien)
    D = C + LERNREGELN.md vom selben Stand
Exit: 0 alle Laeufe mit Antwort, 1 mindestens ein Lauf ohne Antwort, 2 Aufruffehler.
"""
import argparse
import datetime as dt
import os
import re
import subprocess
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
# Kette -> (Rohfassung unter eingaben/ oder None = echte Anforderungsdatei, Repo-Stand vor der Spec)
# Stand = Vorgaenger des Commits "Spec <kurztitel>" (git_schutz 7f95f7d, alle_tests 1faadfe, spec_pruefen 031d296).
KETTEN = {"git_schutz": (None, "7f95f7d^"),
          "alle_tests": (None, "1faadfe^"),
          "spec_pruefen": ("spec_pruefen_roh.md", "031d296^")}
VARIANTEN = ("A", "B", "C", "D")
PLATZHALTER = ("{projekt}", "{lernregeln}", "{aufgabe}", "{antworten}")
MAX_FRAGEN = 6
ZEICHEN_JE_TOKEN = 3.2  # grobe Schaetzung, siehe experiments/kontext_128k/m1_tempo.py
CODE_ENDUNGEN = (".py", ".command", ".sh")
CODE_AUSGESCHLOSSEN = ("role-split/eval/", "role-split/results/", "experiments/")


def eingabe(kt: str) -> tuple[str, str, str]:
    """(aufgabe, antworten, quelle) fuer eine Kette."""
    roh = KETTEN[kt][0]
    if roh:
        p = HIER / "eingaben" / roh
        return p.read_text(encoding="utf-8").strip(), "(keine)", str(p.relative_to(ROOT))
    anf = kette.datei_suchen("anforderung", kt, None)
    if anf is None:
        raise FileNotFoundError(f"Keine anforderung_*_{kt}.md")
    text = anf.read_text(encoding="utf-8")
    antworten = kette.abschnitt(text, "Antworten auf Rueckfragen").strip() or "(keine)"
    return kette.aufgabe_lesen(anf), antworten, str(anf.relative_to(ROOT))


def _git(*args: str) -> str:
    """Nur lesende git-Befehle (show, ls-tree, rev-parse) im Repo; Fehler -> RuntimeError."""
    if args[0] not in ("show", "ls-tree", "rev-parse"):
        raise ValueError(f"git {args[0]} nicht erlaubt")
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def projektkontext(stand: str) -> str:
    """Projektkontext vom Repo-Stand <stand>: kette.py-Befehle, Spec-Vorlage, Liste der Code-Dateien."""
    commit = _git("rev-parse", "--short", stand).strip()
    quelle = _git("show", f"{stand}:role-split/kette/kette.py")
    m = re.match(r'.*?"""(.*?)"""', quelle, re.S)
    if not m:
        raise RuntimeError(f"Docstring von kette.py im Stand {commit} nicht gefunden")
    vorlage = _git("show", f"{stand}:docs/projekt_management/_vorlage_spec.md").strip()
    dateien = [d for d in _git("ls-tree", "-r", "--name-only", stand).splitlines()
               if d.endswith(CODE_ENDUNGEN) and not d.startswith(CODE_AUSGESCHLOSSEN)]
    return (f"## Projektkontext (Stand vor dieser Aufgabe, Commit {commit})\n\n"
            "### Befehle von role-split/kette/kette.py (Docstring)\n\n~~~~\n" + m.group(1).strip() + "\n~~~~\n\n"
            "### Vorlage für Specs (docs/projekt_management/_vorlage_spec.md)\n\n~~~~\n" + vorlage + "\n~~~~\n\n"
            "### Code-Dateien im Repo (ohne role-split/eval, role-split/results, experiments)\n\n"
            + "\n".join(dateien))


def lernregeln(variante: str, stand: str) -> str:
    if variante == "B":
        text = LERNREGELN.read_text(encoding="utf-8")
    elif variante == "D":
        text = _git("show", f"{stand}:docs/learnings/LERNREGELN.md")
    else:
        return ""
    return "## Lernregeln der Kette\n\n" + text.strip()


def prompt_bauen(vorlage: str, aufgabe: str, antworten: str, projekt: str = "", lr: str = "") -> str:
    for p in PLATZHALTER:
        if p not in vorlage:
            raise ValueError(f"Platzhalter {p} fehlt in {PROMPT.name}")
    return (vorlage.replace("{projekt}", projekt)
            .replace("{lernregeln}", lr)
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
    tabelle = ["| Kette | Var. | Nr. | Dauer s | Prompt-Tok. | Antwort-Tok. | Fragen | Form |",
               "|---|---|---|---|---|---|---|---|"]
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
        print(f"--varianten: nur {', '.join(VARIANTEN)}", file=sys.stderr); return 2
    if a.wiederholungen < 1:
        print("--wiederholungen muss >= 1 sein", file=sys.stderr); return 2

    vorlage = PROMPT.read_text(encoding="utf-8")
    auftraege = []
    try:
        for kt in ketten:
            aufgabe, antworten, quelle = eingabe(kt)
            stand = KETTEN[kt][1]
            projekt = projektkontext(stand) if any(v in ("C", "D") for v in varianten) else ""
            for v in varianten:
                p = prompt_bauen(vorlage, aufgabe, antworten,
                                 projekt if v in ("C", "D") else "", lernregeln(v, stand))
                auftraege.append((kt, v, p, quelle))
    except (OSError, RuntimeError, ValueError) as e:
        print(f"Eingabe nicht baubar: {e}", file=sys.stderr); return 2

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
            f"- Varianten: {', '.join(varianten)} (A = Kontext + Anforderung, B = + LERNREGELN heute, "
            "C = + Projektkontext vor der Spec, D = C + LERNREGELN vor der Spec)",
            "- Stände: " + ", ".join(f"{kt} {KETTEN[kt][1]}" for kt in ketten),
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
                zeilen.append(f"| {kt} | {v} | {wdh} | {dauer:.0f} | – | – | – | GESCHEITERT (siehe Konsole) |")
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
                          f"{info.get('completion_tokens')} | {n} | {form} |")
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
