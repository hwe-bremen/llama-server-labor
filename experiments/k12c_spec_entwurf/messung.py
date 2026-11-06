#!/usr/bin/env python3
"""K12c-Messung: Spec-Entwurf des lokalen Modells im Zwei-Schritt mit Quellen.

Lab-Experiment (beruehrt AskValentinAI nicht), nur Standardbibliothek. Ausserhalb der Kette.
Ruft das Modell ueber kette._api_ruf auf (nur 127.0.0.1, KETTE_LLM_MODEL, thinking aus).

Je Kette und Wiederholung:
  1. Modell: Anforderung + Antworten + Projektkontext vom Stand vor der Spec -> Rueckfragen, Annahmen, Quellen.
  2. Skript: Quellen woertlich vom selben Stand holen (git show), nicht aufloesbare zaehlen.
  3. Modell: Spec-Entwurf nach der Vorlage (+ LERNREGELN vom selben Stand).
  4. Skript: spec_pruefen.pruefe am Entwurf; Quellen-Abschnitt des Entwurfs erneut aufloesen.

Liest nur: Anforderungsdateien, eingaben/, prompt_schritt1.md, prompt_schritt3.md, Claudes Specs (nur fuer die
Leckpruefung, nie im Prompt) und Dateien vom Repo-Stand vor der Spec per git show/ls-tree.
Schreibt nur: experiments/k12c_spec_entwurf/ergebnisse/<zeitstempel>/.

Aufruf (im Repo-Root):
    python3 experiments/k12c_spec_entwurf/messung.py --trocken
    python3 experiments/k12c_spec_entwurf/messung.py
    python3 experiments/k12c_spec_entwurf/messung.py --ketten lauf_spec_pruefen --wiederholungen 1
Exit: 0 alle Laeufe mit Entwurf, 1 mindestens ein Schritt ohne Antwort, 2 Aufruf-/Eingabefehler oder Leck.
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
import spec_pruefen  # noqa: E402

PROMPT1 = HIER / "prompt_schritt1.md"
PROMPT3 = HIER / "prompt_schritt3.md"
ERGEBNISSE = HIER / "ergebnisse"
# Kette -> (Stand vor der Spec = Vorgaenger des Commits "Spec <kt>", Datum der Spec)
KETTEN = {"git_schutz": ("7f95f7d^", "20261101"),
          "spec_pruefen": ("031d296^", "20261104"),
          "lauf_spec_pruefen": ("2b63547^", "20261106")}
PLATZ1 = ("{projekt}", "{kurztitel}", "{aufgabe}", "{antworten}")
PLATZ3 = PLATZ1 + ("{lernregeln}", "{schritt1}", "{quellen}", "{datum_iso}")
MAX_TOKENS = int(os.environ.get("K12C_MAX_TOKENS", "16000"))
ZEICHEN_JE_TOKEN = 3.2
CODE_ENDUNGEN = (".py", ".command", ".sh")
CODE_AUSGESCHLOSSEN = ("role-split/eval/", "role-split/results/", "experiments/")
LECK_MIN = 50
OFFEN = "Offene Fragen nicht geklärt"


def _git(*args: str) -> str:
    """Nur lesende git-Befehle im Repo; Fehler -> RuntimeError."""
    if args[0] not in ("show", "ls-tree", "rev-parse"):
        raise ValueError(f"git {args[0]} nicht erlaubt")
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


class Stand:
    """Lesender Blick auf einen Commit (Dateiliste, Dateiinhalte)."""

    def __init__(self, ref: str):
        self.ref = ref
        self.commit = _git("rev-parse", "--short", ref).strip()
        self.dateien = set(_git("ls-tree", "-r", "--name-only", ref).splitlines())
        self._cache: dict[str, str] = {}

    def lesen(self, pfad: str) -> str | None:
        if pfad not in self.dateien:
            return None
        if pfad not in self._cache:
            self._cache[pfad] = _git("show", f"{self.ref}:{pfad}")
        return self._cache[pfad]


def eingabe(kt: str) -> tuple[str, str]:
    """(aufgabe, antworten) – Aufgabe aus der echten Anforderungsdatei, Antworten aus eingaben/."""
    anf = kette.datei_suchen("anforderung", kt, None)
    if anf is None:
        raise FileNotFoundError(f"Keine anforderung_*_{kt}.md")
    antworten = (HIER / "eingaben" / f"{kt}_antworten.md").read_text(encoding="utf-8").strip() or "(keine)"
    return kette.aufgabe_lesen(anf), antworten


def projektkontext(st: Stand) -> str:
    """Docstring von kette.py, Spec-Vorlage, Code-Dateiliste, Funktions-/Konstantenliste role-split/kette/."""
    quelle = st.lesen("role-split/kette/kette.py") or ""
    m = re.match(r'.*?"""(.*?)"""', quelle, re.S)
    if not m:
        raise RuntimeError(f"Docstring von kette.py im Stand {st.commit} nicht gefunden")
    vorlage = (st.lesen("docs/projekt_management/_vorlage_spec.md") or "").strip()
    dateien = sorted(d for d in st.dateien if d.endswith(CODE_ENDUNGEN) and not d.startswith(CODE_AUSGESCHLOSSEN))
    namen = []
    for d in sorted(x for x in st.dateien if re.fullmatch(r"role-split/kette/(?!test_)[\w]+\.py", x)):
        for z in (st.lesen(d) or "").splitlines():
            dm = re.match(r"^(def|class)\s+(\w+)\s*(\([^)]*\))?", z)
            km = re.match(r"^([A-Z][A-Z0-9_]+)\s*=", z)
            if dm:
                namen.append(f"{d}: {dm.group(1)} {dm.group(2)}{(dm.group(3) or '')[:80]}")
            elif km:
                namen.append(f"{d}: {km.group(1)}")
    return (f"## Projektkontext (Stand vor dieser Aufgabe, Commit {st.commit})\n\n"
            "### Befehle von role-split/kette/kette.py (Docstring)\n\n~~~~\n" + m.group(1).strip() + "\n~~~~\n\n"
            "### Vorlage für Specs (docs/projekt_management/_vorlage_spec.md)\n\n~~~~\n" + vorlage + "\n~~~~\n\n"
            "### Code-Dateien im Repo (ohne role-split/eval, role-split/results, experiments)\n\n"
            + "\n".join(dateien) + "\n\n### Funktionen, Klassen und Konstanten in role-split/kette/ (ohne Tests)\n\n"
            + "\n".join(namen))


def lernregeln(st: Stand) -> str:
    text = st.lesen("docs/learnings/LERNREGELN.md")
    return "## Lernregeln der Kette (Stand vor der Aufgabe)\n\n" + text.strip() if text else ""


def fuellen(vorlage: str, werte: dict[str, str], platz: tuple[str, ...]) -> str:
    for p in platz:
        if p not in vorlage:
            raise ValueError(f"Platzhalter {p} fehlt in der Prompt-Vorlage")
    for p in platz:
        vorlage = vorlage.replace(p, werte.get(p, ""))
    return vorlage


def quellen_aufloesen(st: Stand, block: str, vorgabe: str = "") -> tuple[str, int, int, list[str]]:
    """Quellen-Zeilen gegen den Stand aufloesen wie kette.quellen. -> (markdown, ok, nicht_ok, meldungen).

    vorgabe: Pfad der kuenftigen Vorgabe-Testdatei – gibt es am Stand noch nicht, zaehlt nicht als schlecht.
    """
    teile, meld, ok, schlecht = [], [], 0, 0
    for z in block.splitlines():
        q = kette.quelle_lesen(z)
        if not q:
            if re.match(r"^\s*[-*]\s*`[^`]+/[^`]*`", z):
                schlecht += 1; meld.append(f"UNKLAR {z.strip()[:120]}")
            continue
        pfad = q["pfad"]
        if vorgabe and pfad == vorgabe:
            meld.append(f"übersprungen {pfad} (Vorgabe-Tests, entsteht erst)"); continue
        text = st.lesen(pfad)
        if text is None:
            schlecht += 1; meld.append(f"FEHLT {pfad}"); continue
        zeilen = text.splitlines()
        art, name, stelle, von, bis, zweck = q["art"], q["name"], q["text"], q["von"], q["bis"], q["zweck"]
        titel, fehler = f"`{pfad}`", None
        if art:
            bereich = kette._block(zeilen, art, name) if "." not in name else kette._block_name(zeilen, name)[0]
            fehler = None if bereich else f"FEHLT {pfad} {art} {name}"
            titel += f" {art} {name}"
        elif name:
            bereich = kette._block_name(zeilen, name)[0] if pfad.endswith(".py") else None
            bereich = bereich or kette._textstelle(zeilen, name)
            fehler = None if bereich else f"FEHLT {pfad} {name}"
            titel += f" {name}"
        elif stelle:
            bereich = kette._textstelle(zeilen, stelle, 25)
            fehler = None if bereich else f"FEHLT {pfad} „{stelle}“"
        elif von:
            a, b = max(1, int(von)), min(len(zeilen), int(bis or von))
            bereich = (a, b)
            if kette._passt(zeilen[a - 1:b], zweck):
                fehler = f"PRÜFEN {pfad} Zeilen {a}–{b} (Namen aus dem Zweck fehlen)"
        else:
            bereich = (1, len(zeilen))
        if fehler is None and bereich and bereich[1] - bereich[0] + 1 > kette.QUELLE_MAX:
            fehler = f"ZU LANG {pfad} ({bereich[1] - bereich[0] + 1} Zeilen)"
        if fehler:
            schlecht += 1; meld.append(fehler); continue
        a, b = bereich
        breite = len(str(b))
        code = "\n".join(f"{n:>{breite}}| {zeilen[n - 1]}" for n in range(a, b + 1))
        ok += 1
        teile.append(f"### {titel} (Zeilen {a}–{b})" + (f" – {zweck.strip()}" if zweck else "")
                     + f"\n\n```{kette.SPRACHE.get(Path(pfad).suffix, '')}\n{code}\n```\n")
    return "\n".join(teile) or "(keine Quelle auflösbar)", ok, schlecht, meld


def leck_zeilen(kt: str, st: Stand, erlaubt: str) -> list[str]:
    """Kennzeichnende Zeilen aus Claudes Spec (>= LECK_MIN Zeichen), die nicht in Vorlage/Eingaben stehen."""
    spec = kette.datei_suchen("spec", kt, None)
    if spec is None:
        raise FileNotFoundError(f"Keine spec_*_{kt}.md fuer die Leckpruefung")
    if any(d.startswith(f"docs/projekt_management/{kt}/spec_") or re.search(rf"/spec_\d{{8}}_{kt}\.md$", d)
           for d in st.dateien):
        raise RuntimeError(f"Stand {st.commit} enthaelt schon die Spec von {kt}")
    return [z.strip() for z in spec.read_text(encoding="utf-8").splitlines()
            if len(z.strip()) >= LECK_MIN and z.strip() not in erlaubt]


def leck(prompt: str, kennz: list[str]) -> list[str]:
    return [z for z in kennz if z in prompt]


def schritt1_lesen(text: str) -> tuple[int, str, list[str]]:
    """(Anzahl Fragen, Quellen-Block, Formbefunde)."""
    t = text.strip()
    befunde = []
    n = len(re.findall(r"^F\d+:", t, re.M))
    if n == 0 and not t.startswith("Keine Rückfragen."):
        befunde.append("weder F1 noch „Keine Rückfragen.“")
    if n > 4:
        befunde.append(f"{n} Fragen > 4")
    if not re.search(r"^Annahmen:\s*$", t, re.M):
        befunde.append("„Annahmen:“ fehlt")
    m = re.search(r"^Quellen:\s*$", t, re.M)
    if not m:
        befunde.append("„Quellen:“ fehlt")
    return n, (t[m.end():] if m else ""), befunde


def entwurf_saeubern(text: str) -> str:
    t = text.strip()
    m = re.match(r"^```[a-z]*\n(.*)\n```$", t, re.S)
    return (m.group(1) if m else t).strip() + "\n"


def bewerten(st: Stand, entwurf: str, kt: str) -> dict:
    befunde, hinweise, g = spec_pruefen.pruefe(entwurf)
    harte = [b for b in befunde if not b.startswith(OFFEN)]
    _, ok, schlecht, meld = quellen_aufloesen(st, kette.abschnitt(entwurf, "Quellen"), f"tests/test_{kt}.py")
    return {"befunde": befunde, "harte": harte, "hinweise": hinweise, "groesse": g,
            "quellen_ok": ok, "quellen_schlecht": schlecht, "quellen_meld": meld,
            "offen": len(befunde) != len(harte),
            "mechanisch_ok": not harte and schlecht == 0 and ok > 0}


def ruf(prompt: str, nr: int) -> tuple[str | None, dict, float]:
    stopp, faden = kette._herzschlag_stopp_event(nr)
    t0 = time.monotonic()
    try:
        text, info = kette._api_ruf(prompt, nr)
    finally:
        stopp.set(); faden.join(timeout=2)
    return text, info, time.monotonic() - t0


KOPF_TAB = ["| Kette | Nr. | S1 s | S1 Fragen | S1 Form | Quellen ok/schlecht | S3 s | S3 Tok. | Befunde (hart) | "
            "Offene Fragen | Hinweise | Entwurf-Quellen ok/schlecht | Größe D/A/T/St | mechanisch |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="K12c-Messung: Spec-Entwurf des lokalen Modells")
    ap.add_argument("--ketten", default=",".join(KETTEN))
    ap.add_argument("--wiederholungen", type=int, default=3)
    ap.add_argument("--trocken", action="store_true", help="Prompts bauen, Claudes Quellen probehalber aufloesen, "
                    "kein Modellaufruf, nichts schreiben")
    a = ap.parse_args(argv)
    ketten = [k.strip() for k in a.ketten.split(",") if k.strip()]
    if not ketten or any(k not in KETTEN for k in ketten):
        print(f"--ketten: nur {', '.join(KETTEN)}", file=sys.stderr); return 2
    if a.wiederholungen < 1:
        print("--wiederholungen muss >= 1 sein", file=sys.stderr); return 2

    v1, v3 = PROMPT1.read_text(encoding="utf-8"), PROMPT3.read_text(encoding="utf-8")
    auftraege = []
    try:
        for kt in ketten:
            ref, datum = KETTEN[kt]
            st = Stand(ref)
            aufgabe, antworten = eingabe(kt)
            projekt = projektkontext(st)
            werte = {"{projekt}": projekt, "{kurztitel}": kt, "{aufgabe}": aufgabe, "{antworten}": antworten,
                     "{lernregeln}": lernregeln(st), "{datum_iso}": f"{datum[:4]}-{datum[4:6]}-{datum[6:]}"}
            p1 = fuellen(v1, werte, PLATZ1)
            kennz = leck_zeilen(kt, st, projekt + aufgabe)   # Antworten schreibt Claude: werden mitgeprüft
            gef = leck(p1, kennz) + leck(fuellen(v3, werte, PLATZ3), kennz)
            if gef:
                raise RuntimeError(f"Leck {kt}: {gef[0][:100]}")
            auftraege.append((kt, st, werte, p1, kennz))
    except (OSError, RuntimeError, ValueError) as e:
        print(f"Eingabe nicht baubar: {e}", file=sys.stderr); return 2

    if a.trocken:
        for kt, st, werte, p1, kennz in auftraege:
            claude = kette.datei_suchen("spec", kt, None).read_text(encoding="utf-8")
            qtext, ok, schlecht, meld = quellen_aufloesen(st, kette.abschnitt(claude, "Quellen"))
            p3 = fuellen(v3, {**werte, "{schritt1}": "(Schritt 1)", "{quellen}": qtext}, PLATZ3)
            print(f"{kt:<18} Stand {st.commit}  S1 ~{len(p1) / ZEICHEN_JE_TOKEN:>6.0f} Tok.  "
                  f"S3 (mit Claudes Quellen) ~{len(p3) / ZEICHEN_JE_TOKEN:>6.0f} Tok.  "
                  f"Claudes Quellen am Stand: {ok} ok, {schlecht} schlecht  Leck-Zeilen geprüft: {len(kennz)}")
            for m in meld:
                print(f"    {m}")
            k = bewerten(st, claude, kt)
            print(f"    Kontrolle Maßstab an Claudes Spec: harte Befunde {k['harte'] or 0}, Quellen "
                  f"{k['quellen_ok']}/{k['quellen_schlecht']}, mechanisch {'ok' if k['mechanisch_ok'] else 'nein'}")
        print(f"Trocken: {len(auftraege) * a.wiederholungen * 2} Modellaufrufe geplant, nichts geschrieben.")
        return 0

    kette.KETTE_LLM_MAX_TOKENS = MAX_TOKENS
    stempel = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    ordner = ERGEBNISSE / stempel
    ordner.mkdir(parents=True, exist_ok=False)
    kopf = [f"# K12c-Messung {stempel}", "",
            f"- Modell: `{kette.KETTE_LLM_MODEL}` über `{kette.KETTE_LLM_URL}` (kette._api_ruf, thinking aus)",
            f"- Temperatur: {os.environ.get('KETTE_LLM_TEMPERATURE') or 'Server-Standard'}; max_tokens {MAX_TOKENS}; "
            f"Timeout {kette.KETTE_LLM_TIMEOUT} s",
            "- Stände: " + ", ".join(f"{kt} {KETTEN[kt][0]}" for kt in ketten),
            f"- „Befunde (hart)“ = spec_pruefen-Befunde ohne „{OFFEN}“. mechanisch = 0 harte Befunde und alle "
            "Entwurf-Quellen auflösbar. Inhaltliche Bewertung: schluessel.md (Claude)."]
    zeilen: list[str] = []
    uebersicht = ordner / "uebersicht.md"

    def schreiben():
        uebersicht.write_text("\n".join(kopf + [""] + KOPF_TAB + zeilen) + "\n", encoding="utf-8")
    schreiben()

    print("Aufwärmen (lädt das Modell, Zeit zählt nicht) …", flush=True)
    w, _ = kette._api_ruf("Antworte nur mit: OK", 0)
    if w is None:
        print("Aufwärmen fehlgeschlagen – Router läuft? Abbruch.", file=sys.stderr); return 1

    gescheitert, nr = 0, 0
    gesamt = len(auftraege) * a.wiederholungen
    for wdh in range(1, a.wiederholungen + 1):
        for kt, st, werte, p1, kennz in auftraege:
            nr += 1
            basis = ordner / f"{kt}_{wdh}"
            print(f"[{nr}/{gesamt}] {kt} #{wdh} Schritt 1", flush=True)
            t1, i1, d1 = ruf(p1, nr * 10 + 1)
            if t1 is None:
                gescheitert += 1
                zeilen.append(f"| {kt} | {wdh} | {d1:.0f} | – | GESCHEITERT | – | – | – | – | – | – | – | – | – |")
                schreiben(); continue
            n1, qblock, form1 = schritt1_lesen(t1)
            Path(f"{basis}_1_rueckfragen.md").write_text(
                f"<!-- {d1:.1f} s, prompt {i1.get('prompt_tokens')}, antwort {i1.get('completion_tokens')}, "
                f"Form: {'; '.join(form1) or 'ok'} -->\n\n{t1.strip()}\n", encoding="utf-8")
            qtext, qok, qschlecht, qmeld = quellen_aufloesen(st, qblock)
            Path(f"{basis}_2_quellen.md").write_text(
                f"# Quellen Schritt 2 ({qok} ok, {qschlecht} schlecht)\n\n" + "".join(f"- {m}\n" for m in qmeld)
                + "\n" + qtext, encoding="utf-8")
            p3 = fuellen(v3, {**werte, "{schritt1}": t1.strip(), "{quellen}": qtext}, PLATZ3)
            if leck(p3, kennz):
                print("  LECK in Schritt 3 – übersprungen", flush=True)
                zeilen.append(f"| {kt} | {wdh} | {d1:.0f} | {n1} | LECK | {qok}/{qschlecht} | – | – | – | – | – | – | – | – |")
                schreiben(); continue
            print(f"  {d1:.0f} s, {n1} Fragen, Quellen {qok}/{qschlecht}; Schritt 3 "
                  f"(~{len(p3) / ZEICHEN_JE_TOKEN:.0f} Tok.)", flush=True)
            t3, i3, d3 = ruf(p3, nr * 10 + 3)
            if t3 is None:
                gescheitert += 1
                zeilen.append(f"| {kt} | {wdh} | {d1:.0f} | {n1} | {'; '.join(form1) or 'ok'} | {qok}/{qschlecht} | "
                              f"{d3:.0f} | – | GESCHEITERT | – | – | – | – | – |")
                schreiben(); continue
            entwurf = entwurf_saeubern(t3)
            b = bewerten(st, entwurf, kt)
            g = b["groesse"]
            Path(f"{basis}_3_entwurf.md").write_text(entwurf, encoding="utf-8")
            Path(f"{basis}_4_pruefung.md").write_text(
                f"# Prüfung {kt} #{wdh}\n\n- Schritt 3: {d3:.1f} s, prompt {i3.get('prompt_tokens')}, "
                f"antwort {i3.get('completion_tokens')}\n- mechanisch ok: {b['mechanisch_ok']}\n\n## Befunde\n\n"
                + ("".join(f"- {x}\n" for x in b["befunde"]) or "- keine\n") + "\n## Hinweise\n\n"
                + ("".join(f"- {x}\n" for x in b["hinweise"]) or "- keine\n") + "\n## Quellen im Entwurf\n\n"
                + f"- {b['quellen_ok']} ok, {b['quellen_schlecht']} schlecht\n"
                + "".join(f"- {m}\n" for m in b["quellen_meld"]), encoding="utf-8")
            zeilen.append(f"| {kt} | {wdh} | {d1:.0f} | {n1} | {'; '.join(form1) or 'ok'} | {qok}/{qschlecht} | "
                          f"{d3:.0f} | {i3.get('completion_tokens')} | {len(b['harte'])} | "
                          f"{'ja' if b['offen'] else 'nein'} | {len(b['hinweise'])} | "
                          f"{b['quellen_ok']}/{b['quellen_schlecht']} | {g['dateien']}/{g['anforderungen']}/"
                          f"{g['tests']}/{g['stellen'] if g['stellen'] is not None else '?'} | "
                          f"{'ok' if b['mechanisch_ok'] else 'nein'} |")
            schreiben()
            print(f"  {d3:.0f} s, {i3.get('completion_tokens')} Tok., harte Befunde {len(b['harte'])}, "
                  f"Entwurf-Quellen {b['quellen_ok']}/{b['quellen_schlecht']}, mechanisch "
                  f"{'ok' if b['mechanisch_ok'] else 'nein'}", flush=True)

    print(f"\nFertig: {ordner.relative_to(ROOT)} – {gesamt - gescheitert} Entwürfe, {gescheitert} gescheitert.")
    return 1 if gescheitert else 0


if __name__ == "__main__":
    sys.exit(main())
