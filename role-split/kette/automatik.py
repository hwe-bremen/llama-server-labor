"""Automatik: groesse, stand, status, lauf – K11b.

Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
"""
import re
import subprocess
import sys
from pathlib import Path

import kette

GROESSE_DATEIEN = 2
GROESSE_ANFORDERUNGEN = 6
GROESSE_TESTS = 8
UMSETZER_VORSCHLAG = "35B"


def groesse(spec_text: str) -> dict:
    """Groessenpruefung der Spec.

    dateien: Eintraege aus kette._schreibbereich (keiner -> 0).
    anforderungen: Anzahl der Ueberschriften ### <Buchstabe(n)><Zahl>:
                   **nur** im Abschnitt ``## Anforderungen``.
    tests: Anzahl kette.tests_finden.
    """
    dateien = len(kette._schreibbereich(spec_text)) if kette._schreibbereich(spec_text) is not None else 0
    anforderungen = len(
        re.findall(
            r"^###\s+[A-Za-z]+\d+:\s",
            kette.abschnitt(spec_text, "Anforderungen"),
            re.M,
        )
    )
    tests = len(kette.tests_finden(spec_text))
    return {"dateien": dateien, "anforderungen": anforderungen, "tests": tests}


def stand(kurztitel: str) -> dict:
    """Stand der Kette aus den vorhandenen Dateien."""
    spec_p = kette.datei_suchen("spec", kurztitel, None)
    spec_commit = kette.spec_commit(kurztitel)
    spec_text = spec_p.read_text(encoding="utf-8") if spec_p else ""
    vorgabe = kette._vorgabe_tests(spec_text)

    # Laeufe aus Protokoll
    protokoll_p = kette.datei_suchen("umsetzung", kurztitel, None)
    laeufe = []
    if protokoll_p:
        text = protokoll_p.read_text(encoding="utf-8")
        muster = re.compile(r"art:\s*(erst|nb\d+),\s*Exit:\s*(\d+)")
        for z in text.splitlines():
            if not z.lstrip().startswith("- **"):
                continue
            m = muster.search(z)
            if m:
                laeufe.append((m.group(1), int(m.group(2))))

    # Review aus Gesamtbefund
    review = None
    gesamt_p = kette.datei_suchen("gesamt", kurztitel, None)
    if gesamt_p:
        text = gesamt_p.read_text(encoding="utf-8")
        for z in text.splitlines():
            if "**" in z:
                for wert in ("PASS", "NACHBESSERN", "UNVOLLSTÄNDIG"):
                    if f"**{wert}**" in z:
                        review = wert
                        break
                if review:
                    break

    # Offene Dateien
    offen_list = []
    r = subprocess.run(
        ["git", "-C", str(kette.ROOT), "status", "--porcelain"],
        capture_output=True, text=True,
    )
    if r.returncode == 0:
        offen_list = [line.strip() for line in r.stdout.splitlines() if line.strip()]

    return {
        "spec": str(spec_p) if spec_p else None,
        "spec_commit": spec_commit,
        "vorgabe": vorgabe,
        "laeufe": laeufe,
        "review": review,
        "offen": offen_list,
    }


def status(kurztitel: str) -> int:
    """Status ausgeben und naechsten Schritt bestimmen."""
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _).", file=sys.stderr)
        return 2

    s = stand(kurztitel)

    # Naechster Schritt, erste zutreffende Regel
    if not s["spec"]:
        next_text = "Spec fehlt."
    elif not s["spec_commit"]:
        next_text = f'Spec committen: git commit -m "Spec {kurztitel}"'
    elif not s["laeufe"]:
        next_text = f"kette.py lauf {kurztitel}"
    elif s["laeufe"][-1][1] != 0:
        next_text = (
            "Nacharbeit notwendig – Umsetzer aufgerufen und nicht in Ordnung, "
            "dann Übernahme durch Claude."
        )
    elif not s["review"]:
        next_text = f"kette.py review-auto {kurztitel}"
    elif s["review"] != "PASS":
        next_text = f"Review {s['review']} – gegenprüfen."
    elif s["offen"]:
        next_text = "Alle Testdateien laufen lassen (R50), dann committen."
    else:
        next_text = "Abgeschlossen – nichts offen."

    # Ausgabe
    print(f"Status {kurztitel}")
    print(f"  Spec:          {Path(s['spec']).name if s['spec'] else 'fehlt'}")
    print(f"  Spec-Commit:   {s['spec_commit'] or 'fehlt'}")
    print(f"  Vorgabe-Tests: {'ja' if s['vorgabe'] else 'nein'}")
    if s["laeufe"]:
        lauf_text = ", ".join(f"{a} Exit {e}" for a, e in s["laeufe"])
    else:
        lauf_text = "keiner"
    print(f"  Umsetzung:     {lauf_text}")
    print(f"  Review:        {s['review'] or 'keins'}")
    print(f"  Offen:         {len(s['offen'])} Datei(en)")
    print(f"Nächster Schritt: {next_text}")

    return 0 if s["spec"] else 2


def lauf(kurztitel: str) -> int:
    """Kette: Groesse -> umsetzung-auto -> review-auto -> status -> HALT."""
    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
        print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
        return 2

    commit = kette.spec_commit(kurztitel)
    if not commit:
        print(f'Kein Commit "Spec {kurztitel}" gefunden – erst die Spec committen.')
        return 2

    spec_p = kette.datei_suchen("spec", kurztitel, None)
    if not spec_p:
        print(f"Keine Spec spec_<datum>_{kurztitel}.md gefunden.")
        return 2

    spec_text = spec_p.read_text(encoding="utf-8")
    if not kette._vorgabe_tests(spec_text):
        print(
            "Spec hat keinen Abschnitt '## Vorgabe-Tests'. "
            "Vorgabe-Tests vorab schreiben (R48), sonst kein Start."
        )
        return 2

    g = groesse(spec_text)
    print(
        f"Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
        f"{g['tests']} Tests (Schwellen 2/6/8, vorläufig)"
    )

    if (
        g["dateien"] > GROESSE_DATEIEN
        or g["anforderungen"] > GROESSE_ANFORDERUNGEN
        or g["tests"] > GROESSE_TESTS
    ):
        print(
            "HALT – zu groß für den lokalen Umsetzer: Spec teilen oder "
            "Claude übernimmt (R43)."
        )
        return 3

    print(f"Umsetzer: {UMSETZER_VORSCHLAG}")
    exit_umsetzung = kette.umsetzung_auto(kurztitel)
    exit_code = exit_umsetzung

    if exit_umsetzung == 0:
        exit_review = kette.review_auto(kurztitel)
        exit_code = exit_review

    print()
    status(kurztitel)
    print("HALT – Entscheidung Hawe.")

    return exit_code
