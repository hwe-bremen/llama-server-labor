# Quellen Schritt 2 (11 ok, 1 schlecht)

- UNKLAR - `role-split/kette/kette.py` GIT_SCHUTZ – wofür (Konstante für geschützte Pfade)

### `role-split/kette/kette.py` def ablage (Zeilen 97–100) – wofür (Pfad zur Spec-Datei finden)

```python
 97| def ablage(kurztitel: str) -> Path:
 98|     """Ablage-Verzeichnis: docs/projekt_management/<kurztitel>/ wenn vorhanden, sonst docs/projekt_management/."""
 99|     ordner = PM / kurztitel
100|     return ordner if ordner.is_dir() else PM
```

### `role-split/kette/kette.py` def abschnitt (Zeilen 130–133) – wofür (Abschnitte aus Spec-Text extrahieren)

```python
130| def abschnitt(text: str, titel: str) -> str:
131|     """Inhalt unter '## <titel...>' bis zur naechsten '## '-Ueberschrift ('' wenn fehlt)."""
132|     m = re.search(rf"^##\s+{re.escape(titel)}[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
133|     return m.group(1) if m else ""
```

### `role-split/kette/kette.py` def pruefen (Zeilen 615–642) – wofür (Bestehende Prüflogik als Referenz für Struktur)

```python
615| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
616|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
617|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
618|     commit = commit or spec_commit(kurztitel)
619|     if not commit:
620|         print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
621|               f"(git log --oneline -10)."); return 2
622|     teile_dict = _pruefen_teile(kurztitel, commit, timeout)
623|     codes = {k: v[0] for k, v in teile_dict.items()}
624|     teile = []
625|     for titel_key in ("abgleich", "unittest", "gegenprobe"):
626|         code, out = teile_dict[titel_key]
627|         # Titel wiederherstellen: gegenprobe braucht {commit}
628|         titel = f"gegenprobe gegen {commit}" if titel_key == "gegenprobe" else titel_key
629|         teile.append(f"## {titel}  (Exit {code})\n\n```\n{out.rstrip()}\n```\n")
630|     kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
631|                       for k, v in codes.items())
632|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
633|     kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
634|             f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
635|     ziel = ablage(kurztitel) / f"pruefung_{datum}_{kurztitel}.md"
636|     ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
637|     print("\n".join(teile))
638|     print(f"\n==> {kurz}")
639|     print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
640|     return max(codes.values())
641| 
642| # ---------------------------------------------------------------- Review-Paket
```

### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1630–1639) – wofür (Verständnis, was git_schutz schützt)

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

### `role-split/kette/kette.py` def gegenprobe (Zeilen 432–489) – wofür (Referenz für Exit-Codes und Mechanik)

```python
432| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
433|     """Setzt jede seit <commit> geaenderte Code-Datei einzeln voruebergehend auf den alten Stand
434|     zurueck und laesst das Testskript laufen. Ein Test, der dabei nie rot wird, prueft keine der
435|     Aenderungen. Danach wird jeweils der aktuelle Stand wiederhergestellt (Pruefsumme)."""
436|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
437|     if not skript.is_file():
438|         print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
439|     try:
440|         kette, _fremd = _aenderungen(commit, kurztitel)
441|     except subprocess.CalledProcessError as e:
442|         print(f"git-Fehler: {e.stderr.strip()}"); return 2
443|     # A5: dieselbe Auswahl wie paket – nur zur Kette gehoerige Code-Dateien, auch role-split/kette/
444|     dateien = sorted(d for d in kette
445|                      if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))
446|     if not dateien:
447|         print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2
448| 
449|     vorher = tests_laufen(skript, timeout)
450|     if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
451|         print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
452|         return 2
453|     print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
454|     bestand = _bestand_ids(kurztitel)
455|     rot_durch: dict[str, list[str]] = {t: [] for t in vorher}
456|     laden_scheitert: list[str] = []
457|     for d in dateien:
458|         nachher = _zuruecksetzen_und_testen(skript, d, commit, timeout)
459|         if nachher is None:
460|             print(f"  {d}: Zeitueberschreitung"); continue
461|         if set(nachher) - set(vorher):            # Laden gescheitert
462|             print(f"  {d}: ohne die neue Fassung laedt das Testskript gar nicht -- alle Tests rot, aber ohne Einzelaussage")
463|             laden_scheitert.append(Path(d).name)
464|             continue
465|         rote = [t for t, v in nachher.items() if v in ("FAIL", "ERROR")]
466|         for t in rote:
467|             rot_durch[t].append(d)
468|         print(f"  {d}: {len(rote)} Test(s) rot")
469|     print()
470|     bestand_re = re.compile(rf"test_({'|'.join(bestand)})(_|$)", re.I)
471|     gruen = [t for t, ds in rot_durch.items() if not ds and not bestand_re.match(t)]
472|     for t in sorted(rot_durch):
473|         if rot_durch[t]:
474|             print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
475|         elif bestand_re.match(t) and not rot_durch[t]:
476|             print(f"  BESTAND {t}  (prueft laut Spec bewusst Bestehendes)")
477|         elif laden_scheitert:
478|             print(f"  LADEN {t}  (rot nur, weil das Skript ohne {', '.join(laden_scheitert)} nicht laedt -- schwacher Beleg)")
479|         else:
480|             print(f"  GRUEN {t}  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)")
481|     print(f"\n{len(vorher) - len(gruen)} von {len(vorher)} Tests werden durch eine einzelne alte Datei rot"
482|           + (f", {len(gruen)} nur ueber das Laden" if laden_scheitert else "") + ". Aktueller Stand ist wiederhergestellt.")
483|     if gruen:
484|         print("GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) "
485|               "oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, "
486|               "dann wird die Gegenprobe je Test aussagekraeftig.")
487|     return 0 if not gruen else 1
488| 
489| # ---------------------------------------------------------------- tests-pruefen (K11a)
```

### `role-split/kette/kette.py` def main (Zeilen 2188–2258) – wofür (Neuen Subcommand `spec-pruefen` einbinden)

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

### `role-split/kette/kette.py` def _bloecke (Zeilen 692–706) – wofür (Helfer zum Parsen von Markdown-Blöcken)

```python
692| def _bloecke(text: str, muster: str) -> str:
693|     """Alle Abschnitte (## oder ###), deren Ueberschrift auf muster passt, samt Inhalt
694|     bis zur naechsten Ueberschrift gleicher oder hoeherer Ebene."""
695|     zeilen, raus, ebene = text.splitlines(), [], 0
696|     for z in zeilen:
697|         m = re.match(r"^(#{2,3})\s+(.*)", z)
698|         if m:
699|             neu = len(m.group(1))
700|             if ebene and neu <= ebene:
701|                 ebene = 0
702|             if not ebene and re.search(muster, m.group(2), re.I):
703|                 ebene = neu
704|         if ebene:
705|             raus.append(z)
706|     return "\n".join(raus).strip()
```

### `role-split/kette/kette.py` def _protokoll (Zeilen 1783–1794) – wofür (Falls Ausgabe in Datei geschrieben wird)

```python
1783| def _protokoll(pfad: Path) -> list[dict]:
1784|     """Protokollzeilen (A6) in Dateireihenfolge: [{'rot', 'pruefen', 'art'}, ...]."""
1785|     if not pfad.is_file():
1786|         return []
1787|     zeilen = []
1788|     for z in pfad.read_text(encoding="utf-8").splitlines():
1789|         if not z.startswith("- **"):            # nur Laufzeilen; Unterzeilen enthalten fremden Befehlstext
1790|             continue
1791|         m = PROTOKOLL_RE.search(z)
1792|         if m:
1793|             zeilen.append({k: m.group(k).strip() for k in ("rot", "pruefen", "art")})
1794|     return zeilen
```

### `role-split/kette/kette.py` def _datum_aus (Zeilen 1038–1040) – wofür (Datum für Ausgabedatei ermitteln)

```python
1038| def _datum_aus(pfad: Path | None) -> str | None:
1039|     m = re.search(r"_(\d{8})_", pfad.name) if pfad else None
1040|     return m.group(1) if m else None
```

### `docs/projekt_management/_vorlage_spec.md` (Zeilen 1–100) – wofür (Exakte Vorlage für Pflichtabschnitte und Platzhalter)

```markdown
  1| # Spec: <kurztitel>
  2| 
  3| - **Datum:** <JJJJ-MM-TT>
  4| - **Modell:** <Modellname aus dem System-Prompt>
  5| - **Betroffene Dateien:** <nur Dateien, die du gelesen hast>
  6| 
  7| ## Ziel
  8| 
  9| <1–3 Sätze>
 10| 
 11| ## Nicht-Ziele
 12| 
 13| - <…>
 14| 
 15| ## Schreibbereich
 16| 
 17| <!-- Dateien/Ordner, die die Umsetzung ändern darf, z. B. role-split/kette/ oder einzelne Pfade. Ordner mit „/" am Ende. -->
 18| Pflicht für `kette.py umsetzung-auto` (ohne diesen Abschnitt: Exit 2). Eine Zeile je Eintrag, Pfad in Backticks, relativ
 19| zum Repo. `tests/test_<kurztitel>.py` und der Handover sind immer erlaubt; Spec, Anforderung, Quellen und Vorlagen nie.
 20| 
 21| - `pfad/datei.py`
 22| - `pfad/ordner/`
 23| 
 24| ## Vorgabe-Tests
 25| 
 26| <!-- Optional (ab K11a). Nur wenn die Tests VOR der Umsetzung geschrieben werden (R48); sonst Abschnitt löschen. -->
 27| Mit diesem Abschnitt ist `tests/test_<kurztitel>.py` Vorgabe: Sie wird mit der Spec committet, vor dem Erstlauf von
 28| `kette.py tests-pruefen <kurztitel>` geprüft (je Test-ID eine Methode, Skript lädt, jeder Test rot vorab) und darf von der
 29| Umsetzung nicht geändert werden. Tests für bestehendes Verhalten tragen `(Bestand)` im Titel und müssen vorab grün sein (R49).
 30| 
 31| - `tests/test_<kurztitel>.py`
 32| 
 33| ## Außenwirkung und Sperre
 34| 
 35| - **Was kann die Aufgabe außerhalb des Repos auslösen?** <Mail, Netzwerk, echte Daten/DB, Schlüsselbund, launchd … oder „nichts">
 36| - **Technische Sperre für Tests:** <z. B. Variable, die echten Versand erst erlaubt; temporäres Datenverzeichnis. Eine Regel im Prompt reicht nicht.>
 37| 
 38| ## Einstiegspunkte
 39| 
 40| Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
 41| Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
 42| `runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).
 43| Anlass 18.10.: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen; alle Funktionstests waren grün.
 44| 
 45| | Datei | Wie gestartet | Test |
 46| |---|---|---|
 47| | `pfad/skript.py` | `python3 pfad/skript.py` aus `run_x.sh` | T… |
 48| 
 49| ## Quellen
 50| 
 51| Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo –
 52| **nichts aus dem Gedächtnis**. Eine Zeile je Quelle, Pfad in Backticks, dann `Zeilen a–b` oder `def Name` / `class Name`
 53| (ohne Angabe: ganze Datei, max. 400 Zeilen), dann Zweck. `kette.py quellen <kurztitel>` holt die Auszüge danach
 54| maschinell und wörtlich nach `quellen_<JJJJMMTT>_<kurztitel>.md`. Was nicht im Repo steht (externe Doku, Format
 55| eines Fremdprogramms), kommt unter „Offene Fragen" – Hawe legt die Quelle dann als Datei ins Repo.
 56| 
 57| - `pfad/datei.py` def funktion – wofür gebraucht
 58| - `pfad/datei.py` Zeilen 10–40 – wofür gebraucht
 59| 
 60| ## Anforderungen
 61| 
 62| ### A1: <Titel>
 63| - **Anforderung:** <prüfbar formuliert>
 64| - **Stelle:** <Datei, Funktion>
 65| - **Akzeptanz:** <beobachtbares Ergebnis>
 66| 
 67| ## Fehlerpfade
 68| 
 69| Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").
 70| 
 71| | Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
 72| |---|---|---|---|---|
 73| | A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | | | T… |
 74| | A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | | | |
 75| | A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | | | |
 76| | A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | | | |
 77| | A1 | Lauf ohne Testschalter / gegen echte Daten | | | |
 78| | A1 | Absturz mitten im Lauf | | | |
 79| 
 80| ## Testplan
 81| 
 82| Alle Tests werden als `tests/test_<kurztitel>.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
 83| Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.
 84| 
 85| ### T1: <Titel>
 86| - **Prüft:** A1, Fehlerpfad „…"
 87| - **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
 88| - **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
 89| - **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>
 90| - **Gegenprobe:** <welche Datei bzw. welche Codezeile muss im alten Zustand sein, damit dieser Test rot wird? „keine" = Test prüft Bestehendes, dann begründen>
 91| 
 92| <!-- Test für bestehendes Verhalten mit Vorgabe-Tests: „### T2: <Titel> (Bestand)“ – muss vorab grün sein. -->
 93| 
 94| ## Offene Fragen
 95| 
 96| - <… oder „Keine">
 97| 
 98| ## Abweichende Meinung
 99| 
100| - <… oder „Keine">
```

### `role-split/kette/automatik.py` def groesse (Zeilen 18–35) – wofür (Referenz für Größenberechnung, falls wiederverwendbar)

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
