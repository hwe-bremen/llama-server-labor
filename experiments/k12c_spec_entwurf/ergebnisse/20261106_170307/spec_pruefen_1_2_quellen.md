# Quellen Schritt 2 (12 ok, 0 schlecht)


### `role-split/kette/kette.py` def abgleich (Zeilen 312–364) – Mechanismus zum Vergleichen von Spec und Handover, relevant für die Logik von Exit-Codes und Befunden

```python
312| def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
313|     spec, ho = datei_suchen("spec", kurztitel, datum), datei_suchen("handover", kurztitel, datum)
314|     if not spec or not ho:
315|         print(f"Spec oder Handover fehlt: spec={spec}, handover={ho}"); return 2
316|     spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
317|     ho_text = ho.read_text(encoding="utf-8")
318|     getestet = tests_finden(abschnitt(ho_text, "Getestet"))
319|     # A2: Bereichsangaben (T1–T2, T1-T2) unter "Nicht getestet" entfernen
320|     nicht_text = abschnitt(ho_text, "Nicht getestet")
321|     nicht_text = re.sub(rf"\b({TEST_ID})\s*[–—-]\s*({TEST_ID})\b", "", nicht_text)
322|     nicht = set(re.findall(rf"\b({TEST_ID})\b", nicht_text))
323|     print(f"Spec:     {spec.name}  ({len(spec_tests)} Tests)\nHandover: {ho.name}\n")
324|     if not spec_tests:
325|         print("Keine Test-IDs (T1, NT1 ...) in der Spec gefunden."); return 2
326| 
327|     probleme = 0
328|     for tid, titel in spec_tests.items():
329|         if tid in getestet:
330|             q = passt(titel, getestet[tid])
331|             if q >= schwelle:
332|                 print(f"  ok        {tid:5} {titel}")
333|             else:
334|                 probleme += 1
335|                 print(f"  ANDERS    {tid:5} Spec: {titel}\n"
336|                       f"                  Handover: {getestet[tid]}   (Uebereinstimmung {q:.0%} -- ausgetauscht?)")
337|         elif tid in nicht:
338|             probleme += 1
339|             print(f"  NICHT GET {tid:5} {titel}  (unter 'Nicht getestet' -- Grund pruefen)")
340|         else:
341|             probleme += 1
342|             print(f"  FEHLT     {tid:5} {titel}")
343|     for tid in getestet.keys() - spec_tests.keys():
344|         print(f"  EXTRA     {tid:5} {getestet[tid]}  (nicht in der Spec)")
345| 
346|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
347|     if skript.is_file():
348|         code = skript.read_text(encoding="utf-8")
349|         ohne = [t for t in spec_tests if not re.search(rf"def\s+test_{t.lower()}(_|\b)", code)]
350|         if ohne:
351|             probleme += 1
352|             print(f"\n  Testskript {skript.relative_to(ROOT)}: keine Methode test_<id> fuer {', '.join(ohne)}")
353|         else:
354|             print(f"\n  Testskript {skript.relative_to(ROOT)}: alle {len(spec_tests)} Tests als Methode vorhanden")
355|         for hinweis in methoden_pruefen(code):
356|             probleme += 1
357|             print(f"  {hinweis}")
358|         print(f"  Selbst ausfuehren: python3 -m unittest -v {skript.relative_to(ROOT)}")
359|     else:
360|         print(f"\n  Kein Testskript tests/test_{kurztitel}.py -- Tests sind nur behauptet, nicht wiederholbar.")
361|     print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
362|     return 0 if not probleme else 1
363| 
364| # ---------------------------------------------------------------- gegenprobe
```

### `role-split/kette/kette.py` def pruefen (Zeilen 615–642) – Hauptfunktion für mechanische Prüfungen, zeigt Struktur der Befundtabellen

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

### `role-split/kette/kette.py` def _ist_hoch (Zeilen 944–949) – Logik, wie ein Befund als „hoch" (Exit 1) gewertet wird

```python
944| def _ist_hoch(zeile: dict) -> bool:
945|     schwere = (spalte(zeile, "schwere") or "").lower()
946|     return "hoch" in schwere or any(ja(spalte(zeile, n)) for n in ("datenverl", "unbemerkt", "harte"))
947| 
948| 
949| # A4: Modell hat Befund selbst zurückgezogen
```

### `role-split/kette/kette.py` def _befunde (Zeilen 940–941) – Parsen von Befundtabellen, relevant für die Struktur der Ausgabe

```python
940| def _befunde(text: str) -> list[dict]:
941|     return tabelle(abschnitt(text, "Befunde"))
```

### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1630–1639) – Parsen des „Schreibbereich"-Abschnitts, zeigt, wie Platzhalter extrahiert werden

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

### `role-split/kette/kette.py` def _testplan_kurz (Zeilen 709–716) – Parsen des Testplans, zeigt, wie Tests und ihre Unterpunkte identifiziert werden

```python
709| def _testplan_kurz(spec: str) -> str:
710|     """Aus dem Testplan nur die Test-Ueberschriften und die Erwartungs-Zeilen."""
711|     block = abschnitt(spec, "Testplan")
712|     raus = []
713|     for z in block.splitlines():
714|         if z.startswith("### ") or re.match(r"^\s*-\s*\*\*Erwartung", z):
715|             raus.append(z)
716|     return "\n".join(raus).strip()
```

### `role-split/kette/kette.py` def _block (Zeilen 1174–1194) – Hilfsfunktion zum Extrahieren von Markdown-Blöcken, zentral für das Finden von Abschnitten

```python
1174| def _block(zeilen: list[str], art: str, name: str) -> tuple[int, int] | None:
1175|     """Zeilenbereich (1-basiert, inkl.) einer def/class samt Dekoratoren bis zur naechsten gleich tiefen Zeile."""
1176|     kopf = re.compile(rf"^(\s*)(?:async\s+)?{art}\s+{re.escape(name)}\b")
1177|     for i, z in enumerate(zeilen):
1178|         m = kopf.match(z)
1179|         if not m:
1180|             continue
1181|         tiefe = len(m.group(1))
1182|         start = i
1183|         while start > 0 and zeilen[start - 1].strip().startswith("@"):
1184|             start -= 1
1185|         ende = i
1186|         for j in range(i + 1, len(zeilen)):
1187|             zj = zeilen[j]
1188|             if zj.strip() and len(zj) - len(zj.lstrip()) <= tiefe and not zj.lstrip().startswith(("#", ")")):
1189|                 break
1190|             ende = j
1191|         while ende > i and not zeilen[ende].strip():
1192|             ende -= 1
1193|         return start + 1, ende + 1
1194|     return None
```

### `role-split/kette/kette.py` def main (Zeilen 2188–2258) – Einstiegspunkt, zeigt, wie Befehle registriert und aufgerufen werden

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

### `role-split/kette/kette.py` def gegenprobe (Zeilen 432–489) – Referenz für die Nutzung von Exit-Codes und mechanischer Prüfung

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

### `role-split/kette/kette.py` def tests_pruefen (Zeilen 511–563) – Referenz für die Prüfung von Tests, zeigt Struktur der Test-IDs

```python
511| def tests_pruefen(kurztitel: str, timeout: int = 300) -> int:
512|     """Prueft vorab geschriebene Tests: je Test-ID der Spec eine Methode, Skript laedt, jeder Test rot vorab."""
513|     spec = datei_suchen("spec", kurztitel, None)
514|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
515|     if not skript.is_file():
516|         print(f"Keine Vorgabe-Tests tests/test_{kurztitel}.py"); return 2
517|     if not spec:
518|         print(f"Keine spec_*_{kurztitel}.md"); return 2
519|     spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
520|     if not spec_tests:
521|         print(f"Keine Test-IDs (T1, NT1 ...) in {spec.name}"); return 2
522|     code = skript.read_text(encoding="utf-8")
523|     probleme = 0
524|     for hinweis in methoden_pruefen(code):
525|         probleme += 1
526|         print(f"  {hinweis}")
527|     stand = tests_laufen(skript, timeout)
528|     if stand is None:
529|         print(f"  ZEIT      Testskript nach {timeout} s abgebrochen")
530|         return 1
531|     try:
532|         methoden = {k.name for k in ast.walk(ast.parse(code))
533|                     if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)) and k.name.startswith("test")}
534|     except SyntaxError:
535|         methoden = set()
536|     if not set(stand) & methoden:          # nur Lade-Eintraege, keine echte Testmethode gelaufen
537|         print("  LAEDT NICHT Testskript laedt nicht -- neue Funktionen erst in der Methode importieren")
538|         return 1
539|     bestand = _bestand_ids(kurztitel)
540|     for tid in spec_tests:
541|         namen = [n for n in stand if re.match(rf"test_{tid.lower()}(_|$)", n)]
542|         if not namen:
543|             probleme += 1
544|             print(f"  FEHLT     {tid}")
545|             continue
546|         if tid in bestand:
547|             if not namen or all(stand[n] == "ok" for n in namen):
548|                 print(f"  gruen     {tid}")
549|             else:
550|                 probleme += 1
551|                 nicht_ok = [n for n in namen if stand[n] != "ok"]
552|                 print(f"  NICHT GRUEN {tid}  {', '.join(nicht_ok)} (Bestand-Test muss vorab grün sein)")
553|             continue
554|         nicht_rot = [n for n in namen if stand[n] not in ("FAIL", "ERROR")]
555|         if nicht_rot:
556|             probleme += 1
557|             print(f"  NICHT ROT {tid}  {', '.join(nicht_rot)} (ohne Umsetzung nicht rot -- prueft nichts Neues)")
558|         else:
559|             print(f"  rot       {tid}")
560|     print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
561|     return 0 if not probleme else 1
562| 
563| # ---------------------------------------------------------------- pruefen (alles in einem)
```

### `role-split/kette/kette.py` def _rot_aus_pruefung (Zeilen 1818–1830) – Logik für das Erkennen von Fehlern in der Prüfung

```python
1818| def _rot_aus_pruefung(kurztitel: str) -> str:
1819|     """failures+errors aus der unittest-Ausgabe der pruefung-Datei; 'OK' -> 0; sonst '–' (A6)."""
1820|     pfad = datei_suchen("pruefung", kurztitel, None)
1821|     if not pfad:
1822|         return "–"
1823|     ut = abschnitt(pfad.read_text(encoding="utf-8"), "unittest")
1824|     m = re.search(r"^FAILED \(([^)]*)\)", ut, re.M)
1825|     if m:
1826|         werte = dict(re.findall(r"(\w+)=(\d+)", m.group(1)))
1827|         return str(int(werte.get("failures", 0)) + int(werte.get("errors", 0)))
1828|     if re.search(r"^OK\b", ut, re.M):
1829|         return "0"
1830|     return "–"
```

### `role-split/kette/kette.py` def _git_schutz (Zeilen 1741–1777) – Referenz für die Integration von git_schutz, um Fehlalarme zu vermeiden

```python
1741| def _git_schutz(gitdir: Path) -> dict[str, str]:
1742|     """Schnappschuss der geschuetzten Teile: {rel: hash|x|link:...|<unlesbar>}."""
1743|     raus = {}
1744|     for name in GIT_SCHUTZ:
1745|         p = gitdir / name
1746|         if p.is_symlink():
1747|             raus[name] = "link:" + os.readlink(p)
1748|         elif p.is_file():
1749|             try:
1750|                 h = hashlib.sha256(p.read_bytes()).hexdigest()
1751|                 if p.stat().st_mode & 0o111:
1752|                     h += ":x"
1753|                 raus[name] = h
1754|             except OSError:
1755|                 raus[name] = "<unlesbar>"
1756|         elif p.is_dir():
1757|             for dirpath, dirnames, filenames in os.walk(p, followlinks=False):
1758|                 dp = Path(dirpath)
1759|                 for fn in filenames:
1760|                     fp = dp / fn
1761|                     rel = fp.relative_to(gitdir).as_posix()
1762|                     if fp.is_symlink():
1763|                         raus[rel] = "link:" + os.readlink(fp)
1764|                     else:
1765|                         try:
1766|                             h = hashlib.sha256(fp.read_bytes()).hexdigest()
1767|                             if fp.stat().st_mode & 0o111:
1768|                                 h += ":x"
1769|                             raus[rel] = h
1770|                         except OSError:
1771|                             raus[rel] = "<unlesbar>"
1772|                 for dn in dirnames:
1773|                     dpp = dp / dn
1774|                     if dpp.is_symlink():
1775|                         rel = dpp.relative_to(gitdir).as_posix()
1776|                         raus[rel] = "link:" + os.readlink(dpp)
1777|     return raus
```
