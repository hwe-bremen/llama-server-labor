# Quellen: spec_pruefen

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen spec_pruefen` (2026-11-04 20:57, Stand `031d296`), nach dem Abschnitt „Quellen“ in `spec_20261104_spec_pruefen.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/automatik.py` (Zeilen 1–16) – Kopf und Import-Muster (Modul importiert `kette`, nicht umgekehrt)

```python
 1| """Automatik: groesse, stand, status, lauf – K11b.
 2| 
 3| Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
 4| """
 5| import re
 6| import subprocess
 7| import sys
 8| from pathlib import Path
 9| 
10| import kette
11| 
12| GROESSE_DATEIEN = 2
13| GROESSE_ANFORDERUNGEN = 6
14| GROESSE_TESTS = 8
15| UMSETZER_VORSCHLAG = "35B"
16| 
```

### `role-split/kette/automatik.py` def groesse (Zeilen 18–35) – Dateien/Anforderungen/Tests, wird unverändert wiederverwendet

```python
18| def groesse(spec_text: str) -> dict:
19|     """Groessenpruefung der Spec.
20| 
21|     dateien: Eintraege aus kette._schreibbereich (keiner -> 0).
22|     anforderungen: Anzahl der Ueberschriften ### <Buchstabe(n)><Zahl>:
23|                    **nur** im Abschnitt ``## Anforderungen``.
24|     tests: Anzahl kette.tests_finden.
25|     """
26|     dateien = len(kette._schreibbereich(spec_text)) if kette._schreibbereich(spec_text) is not None else 0
27|     anforderungen = len(
28|         re.findall(
29|             r"^###\s+[A-Za-z]+\d+:\s",
30|             kette.abschnitt(spec_text, "Anforderungen"),
31|             re.M,
32|         )
33|     )
34|     tests = len(kette.tests_finden(spec_text))
35|     return {"dateien": dateien, "anforderungen": anforderungen, "tests": tests}
```

### `role-split/kette/kette.py` def abschnitt (Zeilen 130–133) – Inhalt eines Abschnitts (Präfix-Treffer, ohne Groß/klein)

```python
130| def abschnitt(text: str, titel: str) -> str:
131|     """Inhalt unter '## <titel...>' bis zur naechsten '## '-Ueberschrift ('' wenn fehlt)."""
132|     m = re.search(rf"^##\s+{re.escape(titel)}[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
133|     return m.group(1) if m else ""
```

### `role-split/kette/kette.py` (Zeilen 235–252) – `TEST_ID` und `tests_finden`

```python
235| TEST_ID = r"[A-Z]{0,3}T\d+"
236| STOP = {"mit", "ohne", "und", "im", "in", "der", "die", "das", "den", "dem", "des", "ein", "eine",
237|         "einem", "bei", "von", "zu", "auf", "fuer", "für", "als", "nach", "vor", "aus", "oder", "test"}
238| TAG = re.compile(r"^[a-z]\d+$")   # Anforderungs-Kuerzel wie n6, a3, e1
239| 
240| 
241| def tests_finden(text: str) -> dict[str, str]:
242|     """Test-IDs (T1, NT3 ...) mit Titel aus Ueberschriften, Fettzeilen oder Tabellenzeilen."""
243|     gefunden: dict[str, str] = {}
244|     muster = re.compile(rf"^\s*(?:#{{2,5}}\s*|\*\*|\|\s*)({TEST_ID})\b[.:)]?\s*(.*)$")
245|     for z in text.splitlines():
246|         m = muster.match(z)
247|         if not m:
248|             continue
249|         titel = m.group(2)
250|         titel = titel.split("|")[0] if z.lstrip().startswith("|") else titel
251|         gefunden.setdefault(m.group(1), titel.strip(" *:`"))
252|     return gefunden
```

### `role-split/kette/kette.py` def datei_suchen (Zeilen 299–309) – Spec finden (Ablage-Ordner, sonst flach)

```python
299| def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
300|     if datum:
301|         # Nur Ablage-Ordner der Kette (Nachbesserung 1 E2: kein Fallback mehr auf flach)
302|         abl = ablage(kurztitel)
303|         p = abl / f"{typ}_{datum}_{kurztitel}.md"
304|         return p if p.is_file() else None
305|     # Nur exakt <typ>_<JJJJMMTT>_<kurztitel>.md – sonst greift z. B. handover_..._nachbesserung2_<kt>.md (K6, 23.10.)
306|     muster = re.compile(rf"^{re.escape(typ)}_\d{{8}}_{re.escape(kurztitel)}\.md$")
307|     abl = ablage(kurztitel)
308|     treffer = sorted(p for p in abl.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
309|     return treffer[-1] if treffer else None
```

### `role-split/kette/kette.py` def quelle_lesen (Zeilen 1093–1128) – eine Quellen-Zeile lesen (`None` = nicht lesbar)

```python
1093| def quelle_lesen(z: str) -> dict | None:
1094|     """Eine Zeile aus „## Quellen" -> {pfad, von, bis, art, name, text, zweck}; None, wenn keine Fundstelle."""
1095|     m = re.match(r"^\s*[-*]\s*`([^`]+)`(.*)$", z)
1096|     if not m or not re.search(r"[/.]", m.group(1)):
1097|         return None
1098|     pfad, rest = m.group(1).strip(), m.group(2)
1099|     q = {"pfad": pfad, "von": None, "bis": None, "art": None, "name": None, "text": None, "zweck": None}
1100|     rest = rest.strip()
1101|     # 1) Zeilen a–b (auch in Klammern)
1102|     zm = re.match(r"^\(?\s*" + _ZEILEN + r"\s*\)?", rest)
1103|     if zm:
1104|         q["von"], q["bis"] = int(zm.group(1)), int(zm.group(2) or zm.group(1))
1105|         rest = rest[zm.end():].strip()
1106|     else:
1107|         # 2) `def X` / `class X` / `X.Y` / `X` / def X (ohne Backticks) / Abschnitt „…"
1108|         nm = (re.match(r"^`?(def|class)\s+([A-Za-z_][\w.]*)(?:\([^)`]*\))?`?", rest)
1109|               or re.match(r"^`([^`]+)`", rest)
1110|               or re.match(r"^Abschnitt\s+[„\"']([^“\"']+)[“\"']", rest))
1111|         if nm:
1112|             if nm.lastindex == 2:
1113|                 q["art"], q["name"] = nm.group(1), nm.group(2)
1114|             else:
1115|                 wort = nm.group(1).strip()
1116|                 if re.fullmatch(r"[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)?(?:\(\))?", wort):
1117|                     q["name"] = wort.rstrip("()")
1118|                 else:
1119|                     q["text"] = wort
1120|             rest = rest[nm.end():].strip()
1121|             km = re.match(r"^\(\s*" + _ZEILEN + r"\s*\)", rest)   # Klammerzusatz ignorieren, def gewinnt
1122|             if km:
1123|                 rest = rest[km.end():].strip()
1124|     tm = re.match(r"^" + _TRENNER + r"(.*)$", rest)
1125|     if rest and not tm:
1126|         return None          # unbekannte Angabe hinter dem Pfad -> UNKLAR melden statt ganze Datei holen
1127|     q["zweck"] = (tm.group(1) if tm else "").strip() or None
1128|     return q
```

### `role-split/kette/kette.py` (Zeilen 1203–1208) – Schleife in quellen: Muster für „sieht nach Fundstelle aus, Form unklar“

```python
1203|     for z in block.splitlines():
1204|         q = quelle_lesen(z)
1205|         if q:
1206|             eintraege.append(q)
1207|         elif re.match(r"^\s*[-*]\s*`[^`]+/[^`]*`", z):  # sieht nach Fundstelle aus, Form aber unklar
1208|             unerkannt.append(z.strip())
```

### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1630–1639) – Einträge des Schreibbereichs (`None` = Abschnitt fehlt)

```python
1630| def _schreibbereich(spec_text: str) -> list[str] | None:
1631|     """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
1632|     if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
1633|         return None
1634|     eintraege = []
1635|     for z in abschnitt(spec_text, "Schreibbereich").splitlines():
1636|         m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
1637|         if m:
1638|             eintraege.append(m.group(1)[2:] if m.group(1).startswith("./") else m.group(1))
1639|     return eintraege
```

### `role-split/kette/kette.py` def _ist_vorgabe (Zeilen 1647–1650) – Vorgabe-Dateien

```python
1647| def _ist_vorgabe(pfad: str) -> bool:
1648|     """Spec, Anforderung, Quellen, Vorlagen der Kette – darf die Umsetzung nie aendern."""
1649|     name = Path(pfad).name
1650|     return name.endswith(".md") and name.startswith(VORGABE_PRAEFIXE)
```

### `role-split/kette/kette.py` (Zeilen 647–648) – `PAKET_NIE`

```python
647| # Nur docs/ und experiments/ gehoeren nie ins Paket. .md-Dateien in role-split/, tests/ etc. werden aufgenommen.
648| PAKET_NIE = ("docs/", "experiments/",)
```

### `role-split/kette/kette.py` (Zeilen 64–69) – Docstring: Einfügestelle für den neuen Befehl

```python
64|   python3 role-split/kette/kette.py tests-pruefen <kurztitel> [--timeout S]
65|         Prueft vorab geschriebene Tests (Spec mit '## Vorgabe-Tests'): je Test-ID eine Methode, Skript laedt,
66|         jeder Test rot ohne Umsetzung. umsetzung-auto startet den Erstlauf nur bei Exit 0 (K11a).
67| 
68| Exit-Codes: 0 = in Ordnung / PASS, 1 = Abweichung / NACHBESSERN, 2 = Datei/Format-Fehler.
69| Mode B: Lab, beruehrt AskValentinAI nicht.
```

### `role-split/kette/kette.py` def main (Zeilen 2188–2258) – Einbaustelle Parser und Verteiler

```python
2188| def main(argv=None) -> int:
2189|     ap = argparse.ArgumentParser(description="Werkzeug fuer die Kette Spec -> Umsetzung -> Review")
2190|     sub = ap.add_subparsers(dest="cmd", required=True)
2191|     p = sub.add_parser("prompt"); p.add_argument("schritt", choices=SCHRITTE); p.add_argument("kurztitel")
2192|     p.add_argument("--datum"); p.add_argument("--commit")
2193|     p.add_argument("--lauf", type=int, help="Review-Lauf-Nummer (eigener Verdikt-Dateiname je Lauf)")
2194|     q = sub.add_parser("quellen"); q.add_argument("kurztitel"); q.add_argument("--datum")
2195|     n = sub.add_parser("anforderung"); n.add_argument("kurztitel")
2196|     n.add_argument("--aufgabe"); n.add_argument("--antwort"); n.add_argument("--frage"); n.add_argument("--datum")
2197|     a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
2198|     u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
2199|     g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
2200|     g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
2201|     g.add_argument("--timeout", type=int, default=300)
2202|     zf = sub.add_parser("zusammenfuehren", help="Befunde mehrerer Review-Laeufe mechanisch zusammenfuehren")
2203|     zf.add_argument("verdikte", nargs="+")
2204|     pk = sub.add_parser("paket", help="Review-Paket bauen (eine Datei fuers Review)")
2205|     pk.add_argument("kurztitel"); pk.add_argument("--commit"); pk.add_argument("--datum")
2206|     pr = sub.add_parser("pruefen", help="abgleich + unittest + gegenprobe, Ausgabe in Datei")
2207|     pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
2208|     ra = sub.add_parser("review-auto", help="Review-Paket, zwei API-Laeufe, Verdikte, Zusammenfassung")
2209|     ra.add_argument("kurztitel")
2210|     ua = sub.add_parser("umsetzung-auto", help="Umsetzung/Nacharbeit ueber opencode run ohne TUI, danach pruefen")
2211|     ua.add_argument("kurztitel"); ua.add_argument("--nacharbeit", help="Datei mit dem Nachbesserungs-Auftrag")
2212|     tp = sub.add_parser("tests-pruefen", help="Vorgabe-Tests pruefen: Abdeckung, laedt, rot vorab")
2213|     tp.add_argument("kurztitel"); tp.add_argument("--timeout", type=int, default=300)
2214|     lf = sub.add_parser("lauf", help="Kette: Groesse -> umsetzung-auto -> review-auto -> status")
2215|     lf.add_argument("kurztitel")
2216|     st = sub.add_parser("status", help="Stand der Kette anzeigen, ohne etwas auszufuehren")
2217|     st.add_argument("kurztitel")
2218|     e = sub.add_parser("einsortieren", help="Flache PM-Dateien in Ordner verschieben")
2219|     eg = e.add_mutually_exclusive_group(required=True)
2220|     eg.add_argument("kurztitel", nargs="?")
2221|     eg.add_argument("--alle", action="store_true")
2222|     args = ap.parse_args(argv)
2223|     if args.cmd == "zusammenfuehren":
2224|         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
2225|                                 for v in args.verdikte])
2226|     if args.cmd == "paket":
2227|         return paket(args.kurztitel, args.commit, args.datum)
2228|     if args.cmd == "pruefen":
2229|         return pruefen(args.kurztitel, args.commit, args.timeout)
2230|     if args.cmd == "review-auto":
2231|         return review_auto(args.kurztitel)
2232|     if args.cmd == "umsetzung-auto":
2233|         return umsetzung_auto(args.kurztitel, args.nacharbeit)
2234|     if args.cmd == "tests-pruefen":
2235|         return tests_pruefen(args.kurztitel, args.timeout)
2236|     if args.cmd == "gegenprobe":
2237|         return gegenprobe(args.kurztitel, args.commit, args.timeout)
2238|     if args.cmd == "quellen":
2239|         return quellen(args.kurztitel, args.datum)
2240|     if args.cmd == "anforderung":
2241|         return anforderung(args.kurztitel, args.aufgabe, args.antwort, args.frage, args.datum)
2242|     if args.cmd == "prompt":
2243|         return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
2244|     if args.cmd == "abgleich":
2245|         return abgleich(args.kurztitel, args.datum)
2246|     if args.cmd == "lauf":
2247|         import automatik
2248|         return automatik.lauf(args.kurztitel)
2249|     if args.cmd == "status":
2250|         import automatik
2251|         return automatik.status(args.kurztitel)
2252|     if args.cmd == "einsortieren":
2253|         import einsortieren
2254|         return einsortieren.einsortieren(None if args.alle else args.kurztitel)
2255|     pfad = Path(args.verdikt)
2256|     if not pfad.is_absolute() and not pfad.exists():
2257|         pfad = PM / pfad.name
2258|     return urteil(pfad, args.anhaengen)
```

### `tests/test_spec_pruefen.py` (Zeilen 22–47) – `PFLICHT_ERWARTET` und `PLATZHALTER_ERWARTET`: Werte für `PFLICHT` und `PLATZHALTER`, **Zeichen für Zeichen** übernehmen (Gedankenstrich, Auslassungszeichen, Umlaute, „ und ")

```python
22| PFLICHT_ERWARTET = (
23|     "Ziel", "Nicht-Ziele", "Schreibbereich", "Vorgabe-Tests", "Außenwirkung und Sperre",
24|     "Einstiegspunkte", "Quellen", "Anforderungen", "Fehlerpfade", "Testplan",
25|     "Offene Fragen", "Abweichende Meinung",
26| )
27| PLATZHALTER_ERWARTET = (
28|     "# Spec: <kurztitel>",
29|     "<JJJJ-MM-TT>",
30|     "<Modellname aus dem System-Prompt>",
31|     "<nur Dateien, die du gelesen hast>",
32|     "<1–3 Sätze>",
33|     "<…>",
34|     "<Titel>",
35|     "<prüfbar formuliert>",
36|     "<Datei, Funktion>",
37|     "<beobachtbares Ergebnis>",
38|     "<Mail, Netzwerk",
39|     "<z. B. Variable",
40|     "<Testserver, temporäres Verzeichnis",
41|     "<prüfbare Bedingung:",
42|     "<ein Satz: woran würde",
43|     "<welche Datei bzw. welche Codezeile",
44|     "<… oder „Keine\">",
45|     "`pfad/datei.py`",
46|     "`pfad/ordner/`",
47| )
```

### `docs/projekt_management/_vorlage_spec.md` (Zeilen 1–101) – Vorlage, aus der die Platzhalter stammen

```markdown
  1| # Spec: <kurztitel>
  2| 
  3| - **Datum:** <JJJJ-MM-TT>
  4| - **Modell:** <Modellname aus dem System-Prompt>
  5| - **Betroffene Dateien:** <nur Dateien, die du gelesen hast>
  6| - **Änderungsstellen:** <Zahl der Stellen im Code, die die Umsetzung ändert; ab etwa 10 teilen (R55, R59)>
  7| 
  8| ## Ziel
  9| 
 10| <1–3 Sätze>
 11| 
 12| ## Nicht-Ziele
 13| 
 14| - <…>
 15| 
 16| ## Schreibbereich
 17| 
 18| <!-- Dateien/Ordner, die die Umsetzung ändern darf, z. B. role-split/kette/ oder einzelne Pfade. Ordner mit „/" am Ende. -->
 19| Pflicht für `kette.py umsetzung-auto` (ohne diesen Abschnitt: Exit 2). Eine Zeile je Eintrag, Pfad in Backticks, relativ
 20| zum Repo. `tests/test_<kurztitel>.py` und der Handover sind immer erlaubt; Spec, Anforderung, Quellen und Vorlagen nie.
 21| 
 22| - `pfad/datei.py`
 23| - `pfad/ordner/`
 24| 
 25| ## Vorgabe-Tests
 26| 
 27| <!-- Optional (ab K11a). Nur wenn die Tests VOR der Umsetzung geschrieben werden (R48); sonst Abschnitt löschen. -->
 28| Mit diesem Abschnitt ist `tests/test_<kurztitel>.py` Vorgabe: Sie wird mit der Spec committet, vor dem Erstlauf von
 29| `kette.py tests-pruefen <kurztitel>` geprüft (je Test-ID eine Methode, Skript lädt, jeder Test rot vorab) und darf von der
 30| Umsetzung nicht geändert werden. Tests für bestehendes Verhalten tragen `(Bestand)` im Titel und müssen vorab grün sein (R49).
 31| 
 32| - `tests/test_<kurztitel>.py`
 33| 
 34| ## Außenwirkung und Sperre
 35| 
 36| - **Was kann die Aufgabe außerhalb des Repos auslösen?** <Mail, Netzwerk, echte Daten/DB, Schlüsselbund, launchd … oder „nichts">
 37| - **Technische Sperre für Tests:** <z. B. Variable, die echten Versand erst erlaubt; temporäres Datenverzeichnis. Eine Regel im Prompt reicht nicht.>
 38| 
 39| ## Einstiegspunkte
 40| 
 41| Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
 42| Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
 43| `runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).
 44| Anlass 18.10.: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen; alle Funktionstests waren grün.
 45| 
 46| | Datei | Wie gestartet | Test |
 47| |---|---|---|
 48| | `pfad/skript.py` | `python3 pfad/skript.py` aus `run_x.sh` | T… |
 49| 
 50| ## Quellen
 51| 
 52| Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo –
 53| **nichts aus dem Gedächtnis**. Eine Zeile je Quelle, Pfad in Backticks, dann `Zeilen a–b` oder `def Name` / `class Name`
 54| (ohne Angabe: ganze Datei, max. 400 Zeilen), dann Zweck. `kette.py quellen <kurztitel>` holt die Auszüge danach
 55| maschinell und wörtlich nach `quellen_<JJJJMMTT>_<kurztitel>.md`. Was nicht im Repo steht (externe Doku, Format
 56| eines Fremdprogramms), kommt unter „Offene Fragen" – Hawe legt die Quelle dann als Datei ins Repo.
 57| 
 58| - `pfad/datei.py` def funktion – wofür gebraucht
 59| - `pfad/datei.py` Zeilen 10–40 – wofür gebraucht
 60| 
 61| ## Anforderungen
 62| 
 63| ### A1: <Titel>
 64| - **Anforderung:** <prüfbar formuliert>
 65| - **Stelle:** <Datei, Funktion>
 66| - **Akzeptanz:** <beobachtbares Ergebnis>
 67| 
 68| ## Fehlerpfade
 69| 
 70| Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").
 71| 
 72| | Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
 73| |---|---|---|---|---|
 74| | A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | | | T… |
 75| | A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | | | |
 76| | A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | | | |
 77| | A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | | | |
 78| | A1 | Lauf ohne Testschalter / gegen echte Daten | | | |
 79| | A1 | Absturz mitten im Lauf | | | |
 80| 
 81| ## Testplan
 82| 
 83| Alle Tests werden als `tests/test_<kurztitel>.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
 84| Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.
 85| 
 86| ### T1: <Titel>
 87| - **Prüft:** A1, Fehlerpfad „…"
 88| - **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
 89| - **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
 90| - **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>
 91| - **Gegenprobe:** <welche Datei bzw. welche Codezeile muss im alten Zustand sein, damit dieser Test rot wird? „keine" = Test prüft Bestehendes, dann begründen>
 92| 
 93| <!-- Test für bestehendes Verhalten mit Vorgabe-Tests: „### T2: <Titel> (Bestand)“ – muss vorab grün sein. -->
 94| 
 95| ## Offene Fragen
 96| 
 97| - <… oder „Keine">
 98| 
 99| ## Abweichende Meinung
100| 
101| - <… oder „Keine">
```
