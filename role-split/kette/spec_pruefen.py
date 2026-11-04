"""Mechanische Spec-Pruefung: Pflichtabschnitte, Platzhalter, Offene Fragen,
Groesse, Aenderungsstellen, Stelle/Prueft-Zuordnung, Schreibbereich, Quellen.

Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
"""
import re
import sys
from pathlib import Path

import kette
import automatik

PFLICHT = (
    "Ziel", "Nicht-Ziele", "Schreibbereich", "Vorgabe-Tests", "Außenwirkung und Sperre",
    "Einstiegspunkte", "Quellen", "Anforderungen", "Fehlerpfade", "Testplan",
    "Offene Fragen", "Abweichende Meinung",
)
PLATZHALTER = (
    "# Spec: <kurztitel>",
    "<JJJJ-MM-TT>",
    "<Modellname aus dem System-Prompt>",
    "<nur Dateien, die du gelesen hast>",
    "<1–3 Sätze>",
    "<…>",
    "<Titel>",
    "<prüfbar formuliert>",
    "<Datei, Funktion>",
    "<beobachtbares Ergebnis>",
    "<Mail, Netzwerk",
    "<z. B. Variable",
    "<Testserver, temporäres Verzeichnis",
    "<prüfbare Bedingung:",
    "<ein Satz: woran würde",
    "<welche Datei bzw. welche Codezeile",
    "<… oder „Keine\">",
    "`pfad/datei.py`",
    "`pfad/ordner/`",
)

R59 = {"dateien": 1, "anforderungen": 4, "tests": 8, "stellen": 9}


def aenderungsstellen(spec_text: str) -> int | None:
    """Erste Zeile mit - **Änderungsstellen:** n -> n, sonst None."""
    m = re.search(r"^\s*[-*]\s*\*\*Änderungsstellen:\*\*\s*(\d+)", spec_text, re.M)
    return int(m.group(1)) if m else None


def _groesse(text: str) -> dict:
    """Groesse wie automatik.groesse plus 'stellen'."""
    g = automatik.groesse(text)
    g["stellen"] = aenderungsstellen(text)
    return g


def _abschnitte(text: str, befunde: list[str]) -> None:
    """A2.1: Pflichtabschnitte pruefen."""
    for titel in PFLICHT:
        muster = rf"^##\s+{re.escape(titel)}"
        if not re.search(muster, text, re.M | re.I):
            befunde.append(f'Abschnitt „## {titel}“ fehlt')
        elif not kette.abschnitt(text, titel).strip():
            befunde.append(f'Abschnitt „## {titel}“ ist leer')


def _zuordnung(text: str, befunde: list[str], hinweise: list[str]) -> None:
    """A3: Groesse, Aenderungsstellen, Zuordnung Anforderung <-> Test."""
    g = _groesse(text)

    # A3.1-3: aenderungsstellen und R59-Hinweise
    if g["stellen"] is None:
        befunde.append('Zeile „- **Änderungsstellen:** n“ fehlt')

    for key, label, r59_val in [
        ("dateien", "Dateien", R59["dateien"]),
        ("anforderungen", "Anforderungen", R59["anforderungen"]),
        ("tests", "Tests", R59["tests"]),
        ("stellen", "Änderungsstellen", R59["stellen"]),
    ]:
        val = g[key]
        if val is not None and val > r59_val:
            hinweise.append(f"Größe über R59 (vorläufig): {label} {val} > {r59_val}")

    # A3.4: Stelle je Anforderung
    anforderungen_text = kette.abschnitt(text, "Anforderungen")
    anfrage_ids = re.findall(r"^###\s+([A-Za-z]+\d+):\s", anforderungen_text, re.M)
    for aid in anfrage_ids:
        # Rumpf der Anforderung: von dieser Ueberschrift bis zur naechsten
        rumpf_muster = rf"^###\s+{re.escape(aid)}:\s(.*?)(?=^###\s+[A-Za-z]+\d+:\s|\Z)"
        rumpf = re.search(rumpf_muster, anforderungen_text, re.M | re.S)
        rumpf_text = rumpf.group(1) if rumpf else ""
        if not re.search(r"^\s*[-*]\s*\*\*Stelle:\*\*[ \t]*\S", rumpf_text, re.M):
            befunde.append(f"{aid} ohne „Stelle:“")

    # A3.5-6: Prüft je Test und Abdeckung
    testplan_text = kette.abschnitt(text, "Testplan")
    tests = kette.tests_finden(testplan_text)

    # Parse test plan into blocks: each block is the content between two ### T... headings
    test_blocks: dict[str, str] = {}
    test_ids_in_order = list(tests.keys())
    for i, tid in enumerate(test_ids_in_order):
        # Find the heading for this test
        heading_m = re.search(rf"^###\s+{re.escape(tid)}[^\n]*\n", testplan_text, re.M)
        if not heading_m:
            continue
        start = heading_m.end()
        # End is the next test heading or end of text
        if i + 1 < len(test_ids_in_order):
            next_tid = test_ids_in_order[i + 1]
            end_m = re.search(rf"^###\s+{re.escape(next_tid)}", testplan_text[start:], re.M)
            end = start + end_m.start() if end_m else len(testplan_text)
        else:
            end = len(testplan_text)
        test_blocks[tid] = testplan_text[start:end]

    geprüfte_anforderungen: set[str] = set()
    for tid in test_ids_in_order:
        block = test_blocks.get(tid, "")
        muster = rf"^\s*[-*]\s*\*\*Prüft:\*\*(.*)$"
        m = re.search(muster, block, re.M)
        if not m:
            befunde.append(f"{tid} ohne „Prüft:“")
            continue

        rest = m.group(1)
        # Klammerzusätze entfernen
        rest = re.sub(r"\([^)]*\)", " ", rest)
        # Backtick-Code durch Leerzeichen ersetzen
        rest = re.sub(r"`[^`]*`", " ", rest)
        rest = rest.strip()

        # Anforderungs-IDs extrahieren
        ids = re.findall(r"\b([A-Za-z]+\d+)(?:\.\d+)*", rest)
        # Normalisieren: Unterpunkte A3.2 -> A3, Bereich A4.2-A4.4 -> A4
        norm_ids = set()
        for i in ids:
            # Wenn es eine Anforderungs-ID ist (Buchstabe + Zahl), normalisieren
            nm = re.match(r"([A-Za-z]+)(\d+)(?:\.\d+)*", i)
            if nm:
                norm_ids.add(nm.group(1) + nm.group(2))

        # Nur die als Anforderung vorkommen
        bekannte_ids = set(anfrage_ids)
        gefundene = norm_ids & bekannte_ids
        if not gefundene:
            befunde.append(f"{tid} prüft keine Anforderung der Spec")
        else:
            geprüfte_anforderungen.update(gefundene)

    # A3.6: Anforderungen die von keinem Test geprüft sind
    for aid in anfrage_ids:
        if aid not in geprüfte_anforderungen:
            befunde.append(f"{aid} von keinem Test geprüft")


def _bereich_quellen(text: str, befunde: list[str], hinweise: list[str]) -> None:
    """A4: Schreibbereich und Quellen."""
    # A4.1: Schreibbereich
    eintraege = kette._schreibbereich(text)
    if eintraege is not None and not eintraege:
        befunde.append("Schreibbereich ohne Eintrag")
    for e in eintraege or []:  # Patch Claude: Quellen unabhaengig vom Schreibbereich pruefen (A4)
        if e.startswith(kette.PAKET_NIE):
            befunde.append(f"Schreibbereich unter {e.split('/')[0]}/: {e} (R47)")
        if kette._ist_vorgabe(e):
            befunde.append(f"Schreibbereich enthält Vorgabe-Datei: {e}")

    # A4.2: Quellen
    quellen_text = kette.abschnitt(text, "Quellen")
    if not re.search(r"^##\s+Quellen", text, re.M | re.I):
        return  # Abschnitt fehlt -> nicht pruefen
    if not quellen_text.strip():
        befunde.append("Quellen ohne Fundstelle der Form - `pfad` …")
        return

    # Jede Zeile des Quellen-Abschnitts prüfen
    fundstelle_vorhanden = False
    for z in quellen_text.splitlines():
        z_stripped = z.strip()
        if not z_stripped:
            continue
        q = kette.quelle_lesen(z_stripped)
        if q:
            fundstelle_vorhanden = True
        elif re.match(r"^\s*[-*]\s*`[^`]+/[^`]*`", z_stripped):
            # Sieht nach Fundstelle aus, aber quelle_lesen hat None geliefert
            befunde.append(f"Quelle nicht lesbar: {z_stripped[:120]}")

    if not fundstelle_vorhanden:
        befunde.append("Quellen ohne Fundstelle der Form - `pfad` …")


def pruefe(spec_text: str) -> tuple[list[str], list[str], dict]:
    """Spec mechanisch pruefen. Gibt (befunde, hinweise, groesse) zurueck."""
    # HTML-Kommentare entfernen
    text = re.sub(r"<!--.*?-->", "", spec_text, flags=re.S)

    befunde: list[str] = []
    hinweise: list[str] = []

    # A2.1: Pflichtabschnitte
    _abschnitte(text, befunde)

    # A2.2: Platzhalter
    for p in PLATZHALTER:
        if p in text:
            befunde.append(f"Platzhalter aus der Vorlage: {p}")

    # A2.3: Offene Fragen
    offene = kette.abschnitt(text, "Offene Fragen").strip()
    if offene:
        zeilen = [z.strip() for z in offene.splitlines() if z.strip()]
        if len(zeilen) == 1 and re.match(r"^(?:[-*]\s*)?Keine\b", zeilen[0], re.I):
            pass  # geklärt
        else:
            befunde.append("Offene Fragen nicht geklärt – erst beantworten, dann „Keine“")

    # A3: Groesse und Zuordnung
    _zuordnung(text, befunde, hinweise)

    # A4: Schreibbereich und Quellen
    _bereich_quellen(text, befunde, hinweise)

    g = _groesse(text)
    return befunde, hinweise, g


def spec_pruefen(kurztitel: str) -> int:
    """Spec prüfen und Befunde/Hinweise ausgeben. Exit 0/1/2."""
    # A1: Kurztitel validieren
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
        return 2

    # A1: Spec finden
    spec_p = kette.datei_suchen("spec", kurztitel, None)
    if spec_p is None:
        print(f"Keine spec_*_{kurztitel}.md")
        return 2

    # A1: Pruefen
    befunde, hinweise, g = pruefe(spec_p.read_text(encoding="utf-8"))

    # Ausgabe
    stellen_str = str(g["stellen"]) if g["stellen"] is not None else "?"
    print(f"Spec-Prüfung {kurztitel}: {spec_p.name}")
    print(f"  Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
          f"{g['tests']} Tests, {stellen_str} Änderungsstellen (R59 1/4/8/9, vorläufig)")
    for b in befunde:
        print(f"  BEFUND   {b}")
    for h in hinweise:
        print(f"  HINWEIS  {h}")

    if befunde:
        print(f"{len(befunde)} Befund(e), {len(hinweise)} Hinweis(e).")
        return 1
    else:
        print(f"Keine Befunde ({len(hinweise)} Hinweis(e)).")
        return 0
