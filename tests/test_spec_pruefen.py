#!/usr/bin/env python3
"""Vorgabe-Tests fuer spec_pruefen (spec_20261104_spec_pruefen.md, T1–T8). Nicht aendern.

Keine Aussenwirkung: Die Pruefung liest nur. T1–T7 pruefen Spec-Texte direkt bzw. biegen kette.PM auf ein
tempfile.TemporaryDirectory() um. T8 ruft das echte Werkzeug am echten Repo nur lesend auf (R58) und prueft,
dass der Arbeitsstand dabei unveraendert bleibt. spec_pruefen wird in den Methoden importiert.
"""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ECHT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ECHT / "role-split" / "kette"))
import kette  # noqa: E402

PFLICHT_ERWARTET = (
    "Ziel", "Nicht-Ziele", "Schreibbereich", "Vorgabe-Tests", "Außenwirkung und Sperre",
    "Einstiegspunkte", "Quellen", "Anforderungen", "Fehlerpfade", "Testplan",
    "Offene Fragen", "Abweichende Meinung",
)
PLATZHALTER_ERWARTET = (
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

GUT = """# Spec: probe

- **Datum:** 2026-11-04
- **Modell:** Claude
- **Betroffene Dateien:** `role-split/kette/probe.py`
- **Änderungsstellen:** 3

## Ziel

Probe für die Spec-Prüfung. Meldung `.git/<rel> (<neu|weg|geaendert>)`, Aufruf `kette.py lauf <kt>`.

## Nicht-Ziele

- Nichts anderes.

## Schreibbereich

<!-- Kommentar aus der Vorlage mit <Titel> und `pfad/datei.py` zählt nicht -->
- `role-split/kette/probe.py`

## Vorgabe-Tests

- `tests/test_probe.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Nichts.
- **Technische Sperre für Tests:** Temp-Ordner.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/probe.py` | als Modul | T1 |

## Quellen

- `role-split/kette/kette.py` def abschnitt – Abschnitt lesen
- `role-split/kette/kette.py` Zeilen 1–5 – Kopf

## Anforderungen

### A1: Erste
- **Anforderung:** etwas.
- **Stelle:** `probe.py`, neue Funktion `eins`.
- **Akzeptanz:** T1.

### A2: Zweite
- **Anforderung:** mehr.
- **Stelle:** `probe.py`, direkt hinter `eins`.
- **Akzeptanz:** T2.

## Fehlerpfade

| Anforderung | Fall | Vorher | Erwartet | Test |
|---|---|---|---|---|
| A1 | leer | – | Exit 2 | T1 |

## Testplan

### T1: Erster
- **Prüft:** A1 (R58-Vorschlag: Standardwerte), `--timeout`
- **Erwartung:** Exit 0.

### T2: Zweiter
- **Prüft:** A2.3–A2.4
- **Erwartung:** Exit 1.

## Offene Fragen

- Keine

## Abweichende Meinung

- Keine
"""


def _sp():
    import spec_pruefen
    return spec_pruefen


def _ohne_abschnitt(text: str, titel: str) -> str:
    """Entfernt '## titel' samt Inhalt bis zur naechsten '## '-Ueberschrift."""
    zeilen, aus, weg = text.split("\n"), [], False
    for z in zeilen:
        if z.startswith("## "):
            weg = z[3:].strip() == titel
        if not weg:
            aus.append(z)
    return "\n".join(aus)


def _ersetze_abschnitt(text: str, titel: str, inhalt: str) -> str:
    zeilen, aus, weg = text.split("\n"), [], False
    for z in zeilen:
        if z.startswith("## "):
            weg = z[3:].strip() == titel
            if weg:
                aus.extend([z, "", inhalt, ""])
                continue
        if not weg:
            aus.append(z)
    return "\n".join(aus)


class TempPM:
    """kette.PM auf einen Temp-Ordner umbiegen; Spec flach oder im Ablage-Ordner ablegen."""

    def __init__(self, kt=None, text=None, ordner=True):
        self.kt, self.text, self.ordner = kt, text, ordner

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        pm = Path(self.tmp.name) / "docs" / "projekt_management"
        pm.mkdir(parents=True)
        if self.kt:
            ziel = pm / self.kt if self.ordner else pm
            ziel.mkdir(exist_ok=True)
            (ziel / f"spec_20261104_{self.kt}.md").write_text(self.text, encoding="utf-8")
        self.patch = mock.patch.object(kette, "PM", pm)
        self.patch.start()
        self.pm = pm
        return self

    def __exit__(self, *a):
        self.patch.stop()
        self.tmp.cleanup()

    def dateien(self):
        return sorted(str(p.relative_to(self.pm)) for p in self.pm.rglob("*"))


def _lauf(fn, *args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = fn(*args)
    return code, out.getvalue(), err.getvalue()


class TestSpecPruefen(unittest.TestCase):

    def test_t1_gueltige_spec_keine_befunde(self):
        sp = _sp()
        befunde, hinweise, g = sp.pruefe(GUT)
        self.assertEqual(befunde, [])
        self.assertEqual(hinweise, [])
        self.assertEqual(g, {"dateien": 1, "anforderungen": 2, "tests": 2, "stellen": 3})
        with TempPM("probe", GUT) as t:
            vorher = t.dateien()
            code, out, _ = _lauf(sp.spec_pruefen, "probe")
            self.assertEqual(t.dateien(), vorher, "spec_pruefen darf nichts schreiben")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.splitlines(), [
            "Spec-Prüfung probe: spec_20261104_probe.md",
            "  Größe: 1 Datei(en), 2 Anforderungen, 2 Tests, 3 Änderungsstellen (R59 1/4/8/9, vorläufig)",
            "Keine Befunde (0 Hinweis(e)).",
        ])

    def test_t2_pflichtabschnitte_fehlen_oder_leer(self):
        sp = _sp()
        for titel in PFLICHT_ERWARTET:
            befunde, _, _ = sp.pruefe(_ohne_abschnitt(GUT, titel))
            self.assertIn(f"Abschnitt „## {titel}“ fehlt", befunde, titel)
            self.assertNotIn(f"Abschnitt „## {titel}“ ist leer", befunde, titel)
        leer = _ersetze_abschnitt(GUT, "Fehlerpfade", "<!-- nur ein Kommentar -->\n\n")
        befunde, _, _ = sp.pruefe(leer)
        self.assertIn("Abschnitt „## Fehlerpfade“ ist leer", befunde)
        self.assertNotIn("Abschnitt „## Fehlerpfade“ fehlt", befunde)
        leer2 = _ersetze_abschnitt(GUT, "Nicht-Ziele", "   ")
        befunde, _, _ = sp.pruefe(leer2)
        self.assertEqual(befunde, ["Abschnitt „## Nicht-Ziele“ ist leer"])
        befunde, _, _ = sp.pruefe(_ersetze_abschnitt(GUT, "Offene Fragen", ""))
        self.assertEqual(befunde, ["Abschnitt „## Offene Fragen“ ist leer"])

    def test_t3_platzhalter_und_offene_fragen(self):
        sp = _sp()
        for p in PLATZHALTER_ERWARTET:
            text = GUT.replace("Probe für die Spec-Prüfung.", f"Probe {p} für die Spec-Prüfung.")
            befunde, _, _ = sp.pruefe(text)
            self.assertIn(f"Platzhalter aus der Vorlage: {p}", befunde, p)
        for ok in ("- Keine", "Keine.", "* keine", "- Keine (alles geklärt am 04.11.)"):
            befunde, _, _ = sp.pruefe(_ersetze_abschnitt(GUT, "Offene Fragen", ok))
            self.assertEqual(befunde, [], ok)
        frage = "Offene Fragen nicht geklärt – erst beantworten, dann „Keine“"
        for offen in ("- Soll der Lauf abbrechen?", "- Keine\n- Aber: Grenze 10 oder 12?"):
            befunde, _, _ = sp.pruefe(_ersetze_abschnitt(GUT, "Offene Fragen", offen))
            self.assertEqual(befunde, [frage], offen)

    def test_t4_aenderungsstellen_und_groesse_nur_hinweis(self):
        sp = _sp()
        ohne = GUT.replace("- **Änderungsstellen:** 3\n", "")
        befunde, _, g = sp.pruefe(ohne)
        self.assertEqual(befunde, ["Zeile „- **Änderungsstellen:** n“ fehlt"])
        self.assertIsNone(g["stellen"])
        self.assertIsNone(sp.aenderungsstellen(ohne))
        self.assertIsNone(sp.aenderungsstellen("- **Änderungsstellen:** viele\n"))
        self.assertEqual(sp.aenderungsstellen("- **Änderungsstellen:** 12 (verteilt)\n"), 12)
        gross = GUT.replace("- **Änderungsstellen:** 3", "- **Änderungsstellen:** 12 (verteilt)")
        gross = gross.replace("- `role-split/kette/probe.py`\n\n## Vorgabe",
                              "- `role-split/kette/probe.py`\n- `role-split/kette/zwei.py`\n\n## Vorgabe")
        extra = "".join(f"### A{i}: Mehr\n- **Stelle:** hier.\n\n" for i in (3, 4, 5))
        gross = gross.replace("## Fehlerpfade", extra + "## Fehlerpfade")
        gross = gross.replace("- **Prüft:** A2.3–A2.4", "- **Prüft:** A2.3–A2.4, A3, A4, A5")
        befunde, hinweise, g = sp.pruefe(gross)
        self.assertEqual(befunde, [])
        self.assertEqual(g, {"dateien": 2, "anforderungen": 5, "tests": 2, "stellen": 12})
        self.assertEqual(hinweise, [
            "Größe über R59 (vorläufig): Dateien 2 > 1",
            "Größe über R59 (vorläufig): Anforderungen 5 > 4",
            "Größe über R59 (vorläufig): Änderungsstellen 12 > 9",
        ])
        grenze = GUT.replace("- **Änderungsstellen:** 3", "- **Änderungsstellen:** 9")
        self.assertEqual(sp.pruefe(grenze)[1], [])
        with TempPM("gross", gross):
            code, out, _ = _lauf(sp.spec_pruefen, "gross")
        self.assertEqual(code, 0, out)
        self.assertIn("  HINWEIS  Größe über R59 (vorläufig): Änderungsstellen 12 > 9", out.splitlines())
        self.assertEqual(out.splitlines()[-1], "Keine Befunde (3 Hinweis(e)).")
        beides = gross.replace("- **Änderungsstellen:** 12 (verteilt)\n", "")
        with TempPM("beides", beides):
            code, out, _ = _lauf(sp.spec_pruefen, "beides")
        self.assertEqual(code, 1, out)
        self.assertEqual(out.splitlines(), [
            "Spec-Prüfung beides: spec_20261104_beides.md",
            "  Größe: 2 Datei(en), 5 Anforderungen, 2 Tests, ? Änderungsstellen (R59 1/4/8/9, vorläufig)",
            "  BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt",
            "  HINWEIS  Größe über R59 (vorläufig): Dateien 2 > 1",
            "  HINWEIS  Größe über R59 (vorläufig): Anforderungen 5 > 4",
            "1 Befund(e), 2 Hinweis(e).",
        ])

    def test_t5_stelle_und_prueft_zuordnung(self):
        sp = _sp()
        ohne_stelle = GUT.replace("- **Stelle:** `probe.py`, direkt hinter `eins`.\n", "")
        self.assertEqual(sp.pruefe(ohne_stelle)[0], ["A2 ohne „Stelle:“"])
        leere_stelle = GUT.replace("- **Stelle:** `probe.py`, direkt hinter `eins`.", "- **Stelle:**")
        self.assertEqual(sp.pruefe(leere_stelle)[0], ["A2 ohne „Stelle:“"])
        ohne_prueft = GUT.replace("- **Prüft:** A2.3–A2.4\n", "")
        self.assertEqual(sp.pruefe(ohne_prueft)[0], ["T2 ohne „Prüft:“", "A2 von keinem Test geprüft"])
        nur_zusatz = GUT.replace("- **Prüft:** A1 (R58-Vorschlag: Standardwerte), `--timeout`",
                                 "- **Prüft:** Fehlerpfad (A1), `A1`, R58")
        self.assertEqual(sp.pruefe(nur_zusatz)[0],
                         ["T1 prüft keine Anforderung der Spec", "A1 von keinem Test geprüft"])
        bereich = GUT.replace("- **Prüft:** A2.3–A2.4", "- **Prüft:** A1.2–A2.4 (Bestand: A9)")
        self.assertEqual(sp.pruefe(bereich)[0], [])

    def test_t6_schreibbereich_und_quellen(self):
        sp = _sp()

        def mit_bereich(*zeilen):
            return _ersetze_abschnitt(GUT, "Schreibbereich", "\n".join(zeilen))

        self.assertEqual(sp.pruefe(mit_bereich("- `docs/x.py`"))[0],
                         ["Schreibbereich unter docs/: docs/x.py (R47)"])
        self.assertEqual(sp.pruefe(mit_bereich("- `experiments/neu/`"))[0],
                         ["Schreibbereich unter experiments/: experiments/neu/ (R47)"])
        self.assertEqual(sp.pruefe(mit_bereich("- `role-split/kette/spec_alt.md`"))[0],
                         ["Schreibbereich enthält Vorgabe-Datei: role-split/kette/spec_alt.md"])
        self.assertEqual(sp.pruefe(mit_bereich("Nur Text, kein Eintrag."))[0],
                         ["Schreibbereich ohne Eintrag"])
        unklar = GUT.replace("- `role-split/kette/kette.py` Zeilen 1–5 – Kopf",
                             "- `role-split/kette/kette.py` irgendwas ohne Trenner")
        self.assertEqual(sp.pruefe(unklar)[0],
                         ["Quelle nicht lesbar: - `role-split/kette/kette.py` irgendwas ohne Trenner"])
        prosa = _ersetze_abschnitt(GUT, "Quellen", "Alles steht im Code.")
        self.assertEqual(sp.pruefe(prosa)[0], ["Quellen ohne Fundstelle der Form - `pfad` …"])

    def test_t7_aufruf_ueber_kette_main_und_fehlerpfade(self):
        sp = _sp()
        code, out, err = _lauf(kette.main, ["spec-pruefen", "Falsch-Titel"])
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("ungültig", err)
        with TempPM() as t:
            code, out, _ = _lauf(kette.main, ["spec-pruefen", "fehlt"])
            self.assertEqual(t.dateien(), [])
        self.assertEqual((code, out.strip()), (2, "Keine spec_*_fehlt.md"))
        schlecht = GUT.replace("- **Änderungsstellen:** 3\n", "")
        for ordner in (True, False):
            with TempPM("flach", schlecht, ordner=ordner):
                code, out, _ = _lauf(kette.main, ["spec-pruefen", "flach"])
            self.assertEqual(code, 1, out)
            self.assertEqual(out.splitlines(), [
                "Spec-Prüfung flach: spec_20261104_flach.md",
                "  Größe: 1 Datei(en), 2 Anforderungen, 2 Tests, ? Änderungsstellen (R59 1/4/8/9, vorläufig)",
                "  BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt",
                "1 Befund(e), 0 Hinweis(e).",
            ])

    def test_t8_standardwerte_und_trockenlauf_am_echten_bestand(self):
        sp = _sp()
        self.assertEqual(sp.R59, {"dateien": 1, "anforderungen": 4, "tests": 8, "stellen": 9})
        self.assertEqual(sp.PFLICHT, PFLICHT_ERWARTET)
        self.assertEqual(sp.PLATZHALTER, PLATZHALTER_ERWARTET)
        self.assertEqual(kette.PM, ECHT / "docs" / "projekt_management")
        vorlage = (ECHT / "docs" / "projekt_management" / "_vorlage_spec.md").read_text(encoding="utf-8")
        for p in PLATZHALTER_ERWARTET:
            self.assertIn(p, vorlage, p)
        self.assertRegex(vorlage, r"(?m)^- \*\*Änderungsstellen:\*\* <")
        status_vor = subprocess.run(["git", "-C", str(ECHT), "status", "--porcelain"],
                                    capture_output=True, text=True).stdout

        def echt(kt):
            r = subprocess.run([sys.executable, str(ECHT / "role-split" / "kette" / "kette.py"),
                                "spec-pruefen", kt], cwd=str(ECHT / "docs"),
                               capture_output=True, text=True, timeout=60)
            zeilen = r.stdout.splitlines()
            return (r.returncode, [z.strip() for z in zeilen if z.startswith("  BEFUND")],
                    [z.strip() for z in zeilen if z.startswith("  HINWEIS")], r.stdout + r.stderr)

        code, befunde, hinweise, alles = echt("git_schutz")
        self.assertEqual((code, befunde, hinweise),
                         (1, ["BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt"], []), alles)
        code, befunde, hinweise, alles = echt("alle_tests")
        self.assertEqual((code, befunde, hinweise),
                         (1, ["BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt"],
                          ["HINWEIS  Größe über R59 (vorläufig): Anforderungen 5 > 4"]), alles)
        code, befunde, _, alles = echt("spec_pruefen")
        self.assertEqual((code, befunde), (0, []), alles)
        status_nach = subprocess.run(["git", "-C", str(ECHT), "status", "--porcelain"],
                                     capture_output=True, text=True).stdout
        self.assertEqual(status_nach, status_vor)


if __name__ == "__main__":
    unittest.main()
