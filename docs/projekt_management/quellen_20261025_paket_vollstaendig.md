# Quellen: paket_vollstaendig

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen paket_vollstaendig` (2026-10-25 18:44, Stand `5bba1f3`), nach dem Abschnitt „Quellen“ in `spec_20261025_paket_vollstaendig.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` def paket (Zeilen 662–718) – die Hauptfunktion, die geändert wird: Paket bauen, Datei schreiben, Return-Code.

```python
662| def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, still: bool = False) -> int:
663|     """Schreibt review_paket_<datum>_<kurztitel>.md. Rueckgabe 0 = geschrieben, 2 = Voraussetzung fehlt."""
664|     say = (lambda *a: None) if still else print
665|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
666|         say(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
667|     spec_p = datei_suchen("spec", kurztitel, datum)
668|     if not spec_p:
669|         say(f"Keine Spec spec_*_{kurztitel}.md – kein Review-Paket."); return 2
670|     datum = datum or _datum_aus(spec_p)
671|     commit = commit or spec_commit(kurztitel)
672|     if not commit:
673|         say(f"Kein Commit 'Spec {kurztitel}' – Ruecksetzpunkt mit --commit angeben."); return 2
674|     anf_p = datei_suchen("anforderung", kurztitel, None)
675|     ho_p = datei_suchen("handover", kurztitel, None)
676|     pr_p = datei_suchen("pruefung", kurztitel, None)
677|     spec = spec_p.read_text(encoding="utf-8")
678|     nur = _handover_dateien(ho_p.read_text(encoding="utf-8")) if ho_p else None
679|     try:
680|         diff, dateien = _diff(commit, nur)
681|     except subprocess.CalledProcessError as e:
682|         say(f"git-Fehler: {(e.stderr.strip().splitlines() or ['?'])[0]}"); return 2
683|     teile = [
684|         f"# Review-Paket: {kurztitel}\n",
685|         f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
686|         f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in dateien) or 'keine'}.\n"
687|         "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
688|         "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
689|         "## 1. Anforderung (verbindlich, woertlich)\n\n"
690|         + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
691|         f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
692|         f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
693|         f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
694|         f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
695|         f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
696|         f"## 3. Code-Aenderungen gegen `{commit}`\n\n{diff}",
697|         f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(ROOT / 'tests' / f'test_{kurztitel}.py')}"
698|         + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if (tc := _testcode(
699|             ROOT / "tests" / f"test_{kurztitel}.py",
700|             _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())) else ""),
701|         "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
702|         + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
703|             or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
704|         f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
705|     ]
706|     text = "\n\n".join(teile).rstrip() + "\n"
707|     ziel = PM / f"review_paket_{datum}_{kurztitel}.md"
708|     ziel.write_text(text, encoding="utf-8")
709|     groesse = len(text)
710|     say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)")
711|     if groesse > PAKET_WARNUNG_ZEICHEN:
712|         say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen – fuer 64K Kontext eng. "
713|             "Review dann eher in Teilen (z. B. erst Anforderungen A1–A3).")
714|     if not pr_p:
715|         say("Hinweis: keine pruefung_*-Datei – erst `kette.py pruefen <kurztitel>` laufen lassen.")
716|     return 0
717| 
718| # ---------------------------------------------------------------- zusammenfuehren
```

### `role-split/kette/kette.py` def _diff (Zeilen 601–626) – liefert geänderte/neue Dateien gegen den Rücksetzpunkt und deren Diff-Inhalt. Wird um die Vorrang-Klassifikation und die Kürzungsliste erweitert.

```python
601| def _diff(commit: str, nur: set[str] | None = None) -> tuple[str, list[str]]:
602|     """Code-Aenderungen gegen commit. Nie Werkzeug-/Doku-/Testordner (PAKET_NIE).
603|     nur: wenn gesetzt (aus dem Handover), nur diese Dateien.
604|     Kleine Aenderung -> Diff; Umbau (Diff laenger als die Datei) oder neue Datei -> aktuelle Datei mit
605|     Zeilennummern (kuerzer und lesbarer)."""
606|     def git(*a):
607|         return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
608|     geaendert = git("diff", "--name-only", commit).split()
609|     neu = git("ls-files", "--others", "--exclude-standard").split()
610|     def code(d):
611|         return (not d.startswith(PAKET_NIE) and not d.endswith(".md") and (ROOT / d).is_file()
612|                 and (nur is None or d in nur))
613|     teile, dateien = [], []
614|     for d in sorted({x for x in geaendert + neu if code(x)}):
615|         aktuell = (ROOT / d).read_text(encoding="utf-8", errors="replace").splitlines()
616|         nummeriert = [f"{i:4d}  {z}" for i, z in enumerate(aktuell, 1)]
617|         if d in neu and d not in geaendert:
618|             teile.append(_kappen(d, nummeriert, "neu", PAKET_DATEI_ZEILEN))
619|         else:
620|             diff = git("diff", "-U3", commit, "--", d).splitlines()
621|             if len(diff) > len(aktuell):
622|                 teile.append(_kappen(d, nummeriert, "umbau", PAKET_DATEI_ZEILEN))
623|             else:
624|                 teile.append(_kappen(d, diff, "diff", PAKET_DIFF_ZEILEN))
625|         dateien.append(d)
626|     return "\n\n".join(teile) or "(keine Code-Aenderungen gegen den Ruecksetzpunkt)", dateien
```

### `role-split/kette/kette.py` def _kappen (Zeilen 629–638) – kapppt eine einzelne Datei auf die Zeilengrenze. Bleibt, aber wird bei der Vorrang-Kürzung nicht mehr aufgerufen, wenn die Datei komplett weggelassen wird.

```python
629| def _kappen(datei: str, zeilen: list[str], art: str, grenze: int) -> str:
630|     was = {"neu": "neue Datei, mit Zeilennummern", "umbau": "stark umgebaut – aktuelle Datei mit Zeilennummern",
631|            "diff": "Diff"}[art]
632|     kopf = f"### {datei} ({was}, {len(zeilen)} Zeilen)"
633|     rest = ""
634|     if len(zeilen) > grenze:
635|         rest = (f"\n[... {len(zeilen) - grenze} weitere Zeilen gekuerzt – bei Bedarf gezielt "
636|                 f"mit read_file/search_files in {datei} nachlesen]")
637|         zeilen = zeilen[:grenze]
638|     return f"{kopf}\n\n```{'diff' if art == 'diff' else ''}\n" + "\n".join(zeilen) + f"\n```{rest}"
```

### `role-split/kette/kette.py` def _handover_dateien (Zeilen 641–645) – liefert die Pfade aus dem Handover-Abschnitt. Wird für die Vorrang-1-Erkennung weiterverwendet.

```python
641| def _handover_dateien(text: str) -> set[str] | None:
642|     """Pfade in Backticks aus dem Handover (Abschnitte 'Geaenderte … Dateien'). None, wenn keine."""
643|     bloecke = _bloecke(text, r"ge[aä]nderte|neue dateien")
644|     pfade = {m for m in re.findall(r"`([\w./-]+\.\w+)`", bloecke) if "/" in m or "." in m}
645|     return pfade or None
```

### `role-split/kette/kette.py` def _bloecke (Zeilen 526–540) – extrahiert Abschnitte aus Markdown. Wird von `_handover_dateien` verwendet, nicht direkt geändert.

```python
526| def _bloecke(text: str, muster: str) -> str:
527|     """Alle Abschnitte (## oder ###), deren Ueberschrift auf muster passt, samt Inhalt
528|     bis zur naechsten Ueberschrift gleicher oder hoeherer Ebene."""
529|     zeilen, raus, ebene = text.splitlines(), [], 0
530|     for z in zeilen:
531|         m = re.match(r"^(#{2,3})\s+(.*)", z)
532|         if m:
533|             neu = len(m.group(1))
534|             if ebene and neu <= ebene:
535|                 ebene = 0
536|             if not ebene and re.search(muster, m.group(2), re.I):
537|                 ebene = neu
538|         if ebene:
539|             raus.append(z)
540|     return "\n".join(raus).strip()
```

### `role-split/kette/kette.py` (Zeilen 519–523) – Konstanten `PAKET_DIFF_ZEILEN`, `PAKET_DATEI_ZEILEN`, `PAKET_WARNUNG_ZEICHEN`, `PAKET_NIE`; werden angepasst: `PAKET_NIE` verliert `tests/` und `role-split/`, neue Konstante `KETTE_PAKET_MAX` wird eingeführt.

```python
519| PAKET_DIFF_ZEILEN = 700        # je Datei; Rest liest das Review gezielt nach
520| PAKET_DATEI_ZEILEN = 900       # bei Umbau: ganze aktuelle Datei statt Diff, hoechstens so viele Zeilen
521| PAKET_WARNUNG_ZEICHEN = 80000  # ~23k Token: darueber wird es fuer 64K Kontext eng
522| # Werkzeug-/Infrastruktur-Ordner gehoeren nie zur Aufgabe (sonst landen spaetere Werkzeug-Commits im Diff).
523| PAKET_NIE = ("docs/", "tests/", "role-split/", "mcp-server/", "experiments/")
```

### `role-split/kette/kette.py` def gegenprobe (Zeilen 382–438) – setzt geänderte Dateien einzeln zurück. Wird um `role-split/kette/` erweitert (Punkt 5 der Anforderung).

```python
382| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
383|     """Setzt jede seit <commit> geaenderte Code-Datei einzeln voruebergehend auf den alten Stand
384|     zurueck und laesst das Testskript laufen. Ein Test, der dabei nie rot wird, prueft keine der
385|     Aenderungen. Danach wird jeweils der aktuelle Stand wiederhergestellt (Pruefsumme)."""
386|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
387|     if not skript.is_file():
388|         print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
389|     try:
390|         diff = subprocess.run(["git", "-C", str(ROOT), "diff", "--name-only", commit],
391|                               capture_output=True, text=True, check=True).stdout.split()
392|         neu = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
393|                              capture_output=True, text=True, check=True).stdout.split()
394|     except subprocess.CalledProcessError as e:
395|         print(f"git-Fehler: {e.stderr.strip()}"); return 2
396|     dateien = sorted({d for d in diff + neu
397|                       if d.endswith((".py", ".sh", ".command")) and (ROOT / d).exists()
398|                       and not d.startswith(("tests/", "docs/", "role-split/kette/", "experiments/"))})
399|     if not dateien:
400|         print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2
401| 
402|     vorher = tests_laufen(skript, timeout)
403|     if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
404|         print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
405|         return 2
406|     print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
407|     rot_durch: dict[str, list[str]] = {t: [] for t in vorher}
408|     laden_scheitert: list[str] = []
409|     for d in dateien:
410|         nachher = _zuruecksetzen_und_testen(skript, d, commit, timeout)
411|         if nachher is None:
412|             print(f"  {d}: Zeitueberschreitung"); continue
413|         if set(nachher) - set(vorher):            # Laden gescheitert
414|             print(f"  {d}: ohne die neue Fassung laedt das Testskript gar nicht -- alle Tests rot, aber ohne Einzelaussage")
415|             laden_scheitert.append(Path(d).name)
416|             continue
417|         rote = [t for t, v in nachher.items() if v in ("FAIL", "ERROR")]
418|         for t in rote:
419|             rot_durch[t].append(d)
420|         print(f"  {d}: {len(rote)} Test(s) rot")
421|     print()
422|     gruen = [t for t, ds in rot_durch.items() if not ds]
423|     for t in sorted(rot_durch):
424|         if rot_durch[t]:
425|             print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
426|         elif laden_scheitert:
427|             print(f"  LADEN {t}  (rot nur, weil das Skript ohne {', '.join(laden_scheitert)} nicht laedt -- schwacher Beleg)")
428|         else:
429|             print(f"  GRUEN {t}  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)")
430|     print(f"\n{len(vorher) - len(gruen)} von {len(vorher)} Tests werden durch eine einzelne alte Datei rot"
431|           + (f", {len(gruen)} nur ueber das Laden" if laden_scheitert else "") + ". Aktueller Stand ist wiederhergestellt.")
432|     if gruen:
433|         print("GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) "
434|               "oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, "
435|               "dann wird die Gegenprobe je Test aussagekraeftig.")
436|     return 0 if not gruen else 1
437| 
438| # ---------------------------------------------------------------- pruefen (alles in einem)
```

### `role-split/kette/kette.py` (Zeilen 451–515) – `_pruefen_teile` und `pruefen` kombinieren Teil-Return-Codes per `max()`. Wichtig für den Exit-1-Fall: `pruefen` meldet `max(codes.values())`, und `review-auto` bricht bei `!= 0` ab (Zeile 1232–1233).

```python
451| def _pruefen_teile(kurztitel: str, commit: str | None = None, timeout: int = 300) -> dict:
452|     """Teilergebnisse von abgleich, unittest, gegenprobe. Rueckgabe: dict mit den drei Schlüsseln."""
453|     import contextlib
454|     import io
455|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
456|         return {"abgleich": (2, "Kurztitel ungueltig"), "unittest": (2, ""), "gegenprobe": (2, "")}
457|     commit = commit or spec_commit(kurztitel)
458|     if not commit:
459|         return {"abgleich": (2, f"Kein Commit 'Spec {kurztitel}'"),
460|                 "unittest": (2, ""), "gegenprobe": (2, "")}
461|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
462| 
463|     def schritt(titel: str, fn):
464|         puffer = io.StringIO()
465|         with contextlib.redirect_stdout(puffer):
466|             try:
467|                 code = fn()
468|             except Exception as e:
469|                 print(f"!!! Werkzeugfehler: {type(e).__name__}: {e}")
470|                 code = 2
471|         return code, puffer.getvalue()
472| 
473|     def unittest_lauf():
474|         if not skript.is_file():
475|             print(f"Kein Testskript {skript.relative_to(ROOT)}")
476|             return 2
477|         r = subprocess.run([sys.executable, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
478|                            cwd=ROOT, capture_output=True, text=True, timeout=timeout)
479|         print((r.stdout + r.stderr).rstrip())
480|         return 0 if r.returncode == 0 else 1
481| 
482|     abgl_code, abgl_out = schritt("abgleich", lambda: abgleich(kurztitel))
483|     unit_code, unit_out = schritt("unittest", unittest_lauf)
484|     gegen_code, gegen_out = schritt(f"gegenprobe gegen {commit}",
485|                                     lambda: gegenprobe(kurztitel, commit, timeout))
486|     return {"abgleich": (abgl_code, abgl_out), "unittest": (unit_code, unit_out),
487|             "gegenprobe": (gegen_code, gegen_out)}
488| 
489| 
490| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
491|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
492|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
493|     commit = commit or spec_commit(kurztitel)
494|     if not commit:
495|         print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
496|               f"(git log --oneline -10)."); return 2
497|     teile_dict = _pruefen_teile(kurztitel, commit, timeout)
498|     codes = {k: v[0] for k, v in teile_dict.items()}
499|     teile = []
500|     for titel_key in ("abgleich", "unittest", "gegenprobe"):
501|         code, out = teile_dict[titel_key]
502|         # Titel wiederherstellen: gegenprobe braucht {commit}
503|         titel = f"gegenprobe gegen {commit}" if titel_key == "gegenprobe" else titel_key
504|         teile.append(f"## {titel}  (Exit {code})\n\n```\n{out.rstrip()}\n```\n")
505|     kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
506|                       for k, v in codes.items())
507|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
508|     kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
509|             f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
510|     ziel = PM / f"pruefung_{datum}_{kurztitel}.md"
511|     ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
512|     print("\n".join(teile))
513|     print(f"\n==> {kurz}")
514|     print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
515|     return max(codes.values())
```

### `role-split/kette/kette.py` def spec_commit (Zeilen 440–448) – liefert den Rücksetzpunkt-Commit. Nicht geändert.

```python
440| def spec_commit(kurztitel: str) -> str | None:
441|     """Aeltester Commit, dessen Betreffzeile genau "Spec <kurztitel>" ist (= Ruecksetzpunkt)."""
442|     r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h%x09%s"],
443|                        capture_output=True, text=True)
444|     if r.returncode != 0:
445|         return None
446|     treffer = [z.split("\t", 1)[0] for z in r.stdout.splitlines()
447|                if "\t" in z and z.split("\t", 1)[1].strip() == f"Spec {kurztitel}"]
448|     return treffer[-1] if treffer else None
```

### `role-split/kette/kette.py` (Zeilen 553–598) – `_testliste` und `_testcode` liefern Testmethoden-Liste und Testcode. Nicht geändert, aber Teil des Pakets (Abschnitt 4).

```python
553| def _testliste(skript: Path) -> str:
554|     if not skript.is_file():
555|         return "(kein Testskript gefunden)"
556|     try:
557|         baum = ast.parse(skript.read_text(encoding="utf-8"))
558|     except SyntaxError as e:
559|         return f"(Testskript nicht lesbar: {e})"
560|     raus = []
561|     for knoten in ast.walk(baum):
562|         if isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)) and knoten.name.startswith("test"):
563|             doc = (ast.get_docstring(knoten) or "").strip().splitlines()
564|             raus.append(f"- `{knoten.name}` (Zeile {knoten.lineno})" + (f": {doc[0]}" if doc else ""))
565|     return "\n".join(raus) or "(keine Testmethoden)"
566| 
567| 
568| def _auffaellige_tests(pruefung: str) -> set[str]:
569|     """Test-IDs/Methoden, die die Pruefung als GRUEN, LADEN oder ANDERS markiert (kleingeschrieben)."""
570|     treffer = set()
571|     for m in re.finditer(r"^\s*(?:GRUEN|LADEN)\s+(test_\w+)", pruefung, re.M):
572|         treffer.add(m.group(1).lower())
573|     for m in re.finditer(r"^\s*ANDERS\s+(T\w+)", pruefung, re.M):
574|         treffer.add(m.group(1).lower())
575|     return treffer
576| 
577| 
578| def _testcode(skript: Path, auffaellig: set[str], grenze: int = 60) -> str:
579|     """Quelltext der auffaelligen Testmethoden (je hoechstens grenze Zeilen), damit das Review
580|     beurteilen kann, was sie wirklich pruefen (Probe 22.10.: ohne Testcode 0/4 Testbefunde)."""
581|     if not skript.is_file() or not auffaellig:
582|         return ""
583|     text = skript.read_text(encoding="utf-8")
584|     try:
585|         baum = ast.parse(text)
586|     except SyntaxError:
587|         return ""
588|     zeilen, teile = text.splitlines(), []
589|     for k in ast.walk(baum):
590|         if not isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)) or not k.name.startswith("test"):
591|             continue
592|         name = k.name.lower()
593|         kennung = re.match(r"test_(t\w*?\d+[a-z]?)(?:_|$)", name)
594|         if name in auffaellig or (kennung and kennung.group(1) in auffaellig):
595|             ende = min(k.end_lineno or k.lineno, k.lineno + grenze - 1)
596|             code = "\n".join(f"{i:4d}  {zeilen[i - 1]}" for i in range(k.lineno, ende + 1))
597|             teile.append(f"#### {k.name}\n\n```\n{code}\n```")
598|     return "\n\n".join(teile)
```

### `role-split/kette/kette.py` def _pruefung_kurz (Zeilen 648–659) – liefert Kurzfassung der Prüfung. Nicht geändert, Teil des Pakets (Abschnitt 6).

```python
648| def _pruefung_kurz(pfad: Path | None) -> str:
649|     if not pfad:
650|         return "(keine Pruefung gefunden – vorher `kette.py pruefen <kurztitel>` laufen lassen)"
651|     text = pfad.read_text(encoding="utf-8")
652|     kurz = re.search(r"^- Kurz:.*$", text, re.M)
653|     teile = [kurz.group(0) if kurz else ""]
654|     for titel in ("abgleich", "gegenprobe"):
655|         teile.append(f"#### {titel}\n{abschnitt(text, titel).strip()}")
656|     ut = abschnitt(text, "unittest")
657|     zus = [z for z in ut.splitlines() if re.match(r"^(Ran |OK|FAILED|FAIL:|ERROR:)", z)]
658|     teile.append("#### unittest (Zusammenfassung)\n" + ("\n".join(zus) or "(keine Zusammenfassung)"))
659|     return "\n\n".join(t for t in teile if t)
```

### `role-split/kette/kette.py` (Zeilen 1218–1354) – `review_auto` ruft `paket(kurztitel)` auf (Paket-Aufruf Zeile 1230–1241). Nicht geändert, aber der Einstiegspunkt für den echten Lauf.

```python
1218| def review_auto(kurztitel: str) -> int:
1219|     """Review-Paket bauen, zwei API-Laeufe, Verdikte speichern, zusammenfuehren."""
1220|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
1221|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
1222| 
1223|     # A2: Pruefung, Abbruch bei roten Unit-Tests
1224|     teile_dict = _pruefen_teile(kurztitel)
1225|     unit_code = teile_dict["unittest"][0]
1226|     if unit_code != 0:
1227|         if unit_code == 2:
1228|             print(f"Pruefung-Fehler (Exit 2) – Review nicht moeglich."); return 2
1229|         print("Unit-Tests rot – direkt nachbessern, kein Review nötig"); return 1
1230| 
1231|     # A3: Review-Paket bauen
1232|     if paket(kurztitel) != 0:
1233|         print("Review-Paket nicht gebaut – Voraussetzung fehlt (Exit 2)."); return 2
1234|     paket_pfad = PM / f"review_paket_{_datum_aus(datei_suchen('spec', kurztitel, None)) or dt.date.today().strftime('%Y%m%d')}_{kurztitel}.md"
1235|     paket_text = paket_pfad.read_text(encoding="utf-8") if paket_pfad.exists() else ""
1236| 
1237|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
1238| 
1239|     # A1: Prompt-Dateien laden, {paket_text} ersetzen
1240|     prompt1 = (PROMPTS / "review_api.md").read_text(encoding="utf-8").replace("{paket_text}", paket_text).replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", "").replace("{datum_heute}", dt.datetime.now().strftime("%Y-%m-%d")).replace("{modell}", KETTE_LLM_MODEL)
1241|     prompt2 = (PROMPTS / "review2_api.md").read_text(encoding="utf-8").replace("{paket_text}", paket_text).replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", "").replace("{datum_heute}", dt.datetime.now().strftime("%Y-%m-%d")).replace("{modell}", KETTE_LLM_MODEL)
1242| 
1243|     verdikt1 = verdikt2 = None
1244|     info1 = info2 = {}
1245|     pfad1 = pfad2 = None
1246| 
1247|     # Lauf 1
1248|     print(f"Lauf 1 von 2 (Anforderung) gestartet")
1249|     stop1, thread1 = _herzschlag_stopp_event(1)
1250|     start1 = dt.datetime.now()
1251|     try:
1252|         verdikt1, info1 = _api_ruf(prompt1, 1)
1253|     except Exception:
1254|         print("Lauf 1 gescheitert – Exit 1, kein Lauf 2."); stop1.set(); thread1.join(timeout=2); return 1
1255|     stop1.set()
1256|     thread1.join(timeout=2)
1257|     elapsed1 = int((dt.datetime.now() - start1).total_seconds())
1258|     if not verdikt1:
1259|         print("Lauf 1: keine Antwort vom Server – Exit 1, kein Lauf 2."); return 1
1260|     print(f"Lauf 1 fertig ({elapsed1}s, {info1.get('prompt_tokens', '?')} prompt, "
1261|           f"{info1.get('completion_tokens', '?')} completion tokens)")
1262|     try:
1263|         pfad1 = _freier_verdiktpfad(datum, kurztitel, 1)
1264|         with open(pfad1, "x", encoding="utf-8") as f:
1265|             f.write(verdikt1)
1266|         print(f"Verdikt 1 gespeichert: {_rel(pfad1)}")
1267|     except FileExistsError:
1268|         zaehler = 2
1269|         while True:
1270|             pfad1 = PM / f"verdict_{datum}_{kurztitel}_qwen36-35b_{zaehler}.md"
1271|             if not pfad1.exists():
1272|                 with open(pfad1, "x", encoding="utf-8") as f:
1273|                     f.write(verdikt1)
1274|                 print(f"Verdikt 1 gespeichert: {_rel(pfad1)} (Zaehler {zaehler})")
1275|                 break
1276|             zaehler += 1
1277| 
1278|     # Lauf 2
1279|     print(f"Lauf 2 von 2 (Betrieb) gestartet")
1280|     stop2, thread2 = _herzschlag_stopp_event(2)
1281|     start2 = dt.datetime.now()
1282|     try:
1283|         verdikt2, info2 = _api_ruf(prompt2, 2)
1284|     except Exception:
1285|         print("Lauf 2 gescheitert – Exit 1."); stop2.set(); thread2.join(timeout=2); return 1
1286|     stop2.set()
1287|     thread2.join(timeout=2)
1288|     elapsed2 = int((dt.datetime.now() - start2).total_seconds())
1289|     if not verdikt2:
1290|         print("Lauf 2: keine Antwort vom Server – Exit 1."); return 1
1291|     print(f"Lauf 2 fertig ({elapsed2}s, {info2.get('prompt_tokens', '?')} prompt, "
1292|           f"{info2.get('completion_tokens', '?')} completion tokens)")
1293|     try:
1294|         pfad2 = _freier_verdiktpfad(datum, kurztitel, 2)
1295|         with open(pfad2, "x", encoding="utf-8") as f:
1296|             f.write(verdikt2)
1297|         print(f"Verdikt 2 gespeichert: {_rel(pfad2)}")
1298|     except FileExistsError:
1299|         zaehler = 2
1300|         while True:
1301|             pfad2 = PM / f"verdict_{datum}_{kurztitel}_qwen36-35b_betrieb_{zaehler}.md"
1302|             if not pfad2.exists():
1303|                 with open(pfad2, "x", encoding="utf-8") as f:
1304|                     f.write(verdikt2)
1305|                 print(f"Verdikt 2 gespeichert: {_rel(pfad2)} (Zaehler {zaehler})")
1306|                 break
1307|             zaehler += 1
1308| 
1309|     # A6: Auswertbare Befund-Tabelle
1310|     auswertbar1 = verdikt1 and _ist_auswertbar(verdikt1)
1311|     auswertbar2 = verdikt2 and _ist_auswertbar(verdikt2)
1312| 
1313|     unvollstaendig = not auswertbar1 or not auswertbar2
1314|     fehlende_datei = []
1315|     if not auswertbar1 and pfad1:
1316|         fehlende_datei.append(pfad1.name)
1317|     if not auswertbar2 and pfad2:
1318|         fehlende_datei.append(pfad2.name)
1319| 
1320|     # A7: Zusammenführen (intern, auch mit 1 oder 0 gültigen Pfaenden)
1321|     gueltige_pfade = [p for p, aw in [(pfad1, auswertbar1), (pfad2, auswertbar2)]
1322|                       if p and aw]
1323|     gesamt_exit = zusammenfuehren(gueltige_pfade, _internal=True)
1324| 
1325|     # UNVOLLSTÄNDIG: bei fehlender Tabelle immer 1, Gesamtbefund anpassen
1326|     if unvollstaendig:
1327|         gesamt_pfad = PM / f"gesamt_{datum}_{kurztitel}.md"
1328|         if gesamt_pfad.exists():
1329|             text = gesamt_pfad.read_text(encoding="utf-8")
1330|             text = text.replace("**PASS**", "**UNVOLLSTÄNDIG**")
1331|             warnhinweis = (f"Ein Lauf ohne auswertbare Befund-Tabelle: {', '.join(fehlende_datei)} "
1332|                            f"– Gesamtbefund beruht nur auf {len(gueltige_pfade)} Lauf/Läufen")
1333|             text = text.replace(f"# Gesamtbefund: {kurztitel}\n",
1334|                                 f"# Gesamtbefund: {kurztitel}\n\n> {warnhinweis}\n")
1335|             gesamt_pfad.write_text(text, encoding="utf-8")
1336|         gesamt_exit = 1
1337|         print(f"==> UNVOLLSTÄNDIG: Befund-Tabelle fehlt in {', '.join(fehlende_datei)}")
1338| 
1339|     # Zusammenfassung
1340|     gesamt_pfad = PM / f"gesamt_{datum}_{kurztitel}.md"
1341|     print(f"\n=== Zusammenfassung ===")
1342|     if unvollstaendig:
1343|         print("Ergebnis: UNVOLLSTÄNDIG")
1344|     else:
1345|         print(f"Ergebnis: {'PASS' if gesamt_exit == 0 else 'NACHBESSERN'}")
1346|     print(f"Verdikt 1: {_rel(pfad1) if pfad1 else 'keine'}")
1347|     print(f"Verdikt 2: {_rel(pfad2) if pfad2 else 'keine'}")
1348|     print(f"Gesamt: {_rel(gesamt_pfad) if gesamt_pfad.exists() else 'keine'}")
1349| 
1350|     return gesamt_exit
1351| 
1352| 
1353| # ---------------------------------------------------------------- main
1354| 
```

### `role-split/kette/test_kette.py` class PruefenTests (Zeilen 174–306) – enthält die bestehenden Paket-Tests (`test_paket_inhalt` Zeile 240, `test_paket_nur_dateien_aus_handover_und_nie_werkzeug` Zeile 255, `test_paket_kleine_aenderung_als_diff` Zeile 268, `test_paket_kappt_lange_dateien` Zeile 282, `test_paket_ohne_spec_schreibt_nichts` Zeile 292). Die Tests, die das alte Verhalten festschreiben, werden angepasst.

```python
174| class PruefenTests(unittest.TestCase):
175|     def setUp(self):
176|         import subprocess
177|         d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
178|         self.root = root = Path(d.name)
179|         def git(*a):
180|             subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
181|                            check=True, capture_output=True)
182|         self.git = git
183|         git("init", "-q")
184|         (root / "docs/projekt_management").mkdir(parents=True)
185|         (root / "mod.py").write_text("def f():\n    return 1\n")
186|         git("add", "."); git("commit", "-qm", "Spec g")
187|         self.erster = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
188|                                      capture_output=True, text=True).stdout.strip()
189|         (root / "mod.py").write_text("def f():\n    return 2\n")
190|         git("add", "."); git("commit", "-qm", "Spec g")          # spaeterer gleichnamiger Commit
191|         (root / "tests").mkdir()
192|         (root / "tests" / "test_g.py").write_text(
193|             "import sys, unittest\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent))\n"
194|             "class T(unittest.TestCase):\n"
195|             "    def test_t1_neu(self):\n        import mod\n        self.assertEqual(mod.f(), 2)\n")
196|         for name, wert in (("ROOT", root), ("PM", root / "docs/projekt_management")):
197|             alt = getattr(kette, name); setattr(kette, name, wert)
198|             self.addCleanup(setattr, kette, name, alt)
199| 
200|     def test_aeltester_spec_commit_und_datei(self):
201|         self.assertEqual(kette.spec_commit("g"), self.erster)
202|         code, out = lauf(kette.pruefen, "g")
203|         dateien = list((self.root / "docs/projekt_management").glob("pruefung_*_g.md"))
204|         self.assertEqual(len(dateien), 1, out)
205|         text = dateien[0].read_text(encoding="utf-8")
206|         for teil in ("## abgleich", "## unittest", f"## gegenprobe gegen {self.erster}", "Ran 1 test", "rot   test_t1_neu"):
207|             self.assertIn(teil, text)
208|         self.assertEqual(code, 2)                                  # abgleich: keine Spec -> 2, sichtbar
209|         self.assertIn("abgleich: FEHLER", out)
210| 
211|     def test_ohne_spec_commit_abbruch(self):
212|         self.assertIsNone(kette.spec_commit("anders"))
213|         code, out = lauf(kette.pruefen, "anders")
214|         self.assertEqual(code, 2); self.assertIn("Kein Commit 'Spec anders'", out)
215|         self.assertEqual(list((self.root / "docs/projekt_management").glob("pruefung_*")), [])
216| 
217|     def test_prompt_review_nimmt_spec_commit_statt_head(self):
218|         (kette.PM / "spec_20261022_g.md").write_text("# Spec\n", encoding="utf-8")
219|         code, out = lauf(kette.prompt, "review", "g", None, None)
220|         self.assertEqual(code, 0)
221|         self.assertIn(self.erster, out)
222| 
223|     def _paket_vorbereiten(self):
224|         pm = kette.PM
225|         (pm / "spec_20261022_g.md").write_text(
226|             "# Spec\n\n## Ziel\nZIELTEXT\n\n## Nicht-Ziele\nNZTEXT\n\n## Quellen\nQUELLTEXT\n\n## Anforderungen\n### A1: Eins\nANFTEXT\n\n"
227|             "## Fehlerpfade\nFEHLERTABELLE\n\n## Testplan\n### T1: Erster\n- **Prüft:** A1\n- **Aufbau:** AUFBAUTEXT\n"
228|             "- **Erwartung:** ERWARTET1\n\n## Offene Fragen\nOQTEXT\n", encoding="utf-8")
229|         (pm / "anforderung_20261022_g.md").write_text("HAWE WILL X\n", encoding="utf-8")
230|         (pm / "handover_20261022_g.md").write_text(
231|             "# HO\n## Umgesetzt\nUMGESETZT\n## Getestet (mit echter Ausgabe)\nLANGE AUSGABE\n"
232|             "## Abweichungen von der Spec\nABWEICHUNG1\n### Detail\nDETAIL1\n## Nachbesserung 2\nNB2\n"
233|             "### Abweichungen bei Nachbesserung 2\nABWEICHUNG2\n", encoding="utf-8")
234|         (pm / "pruefung_20261022_g.md").write_text(
235|             "# Pruefung g\n\n- Kurz: abgleich: ok | unittest: ok\n\n## abgleich  (Exit 0)\nABGL\n"
236|             "## unittest  (Exit 0)\ntest_x ... ok\nRan 1 test in 0.1s\nOK\n## gegenprobe gegen x  (Exit 1)\nGEGEN\n  GRUEN test_t1_neu  (wird mit keiner alten Datei rot)\n",
237|             encoding="utf-8")
238|         (self.root / "neu_modul.py").write_text("Y = 1\n")
239| 
240|     def test_paket_inhalt(self):
241|         self._paket_vorbereiten()
242|         code, out = lauf(kette.paket, "g")
243|         self.assertEqual(code, 0, out)
244|         text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
245|         for soll in ("HAWE WILL X", "ZIELTEXT", "ANFTEXT", "### T1: Erster", "ERWARTET1", "OQTEXT",
246|                      "### mod.py (stark umgebaut", "   2      return 2", "### neu_modul.py (neue Datei", "   1  Y = 1",
247|                      "`test_t1_neu` (Zeile", "ABWEICHUNG1", "DETAIL1", "ABWEICHUNG2",
248|                      "- Kurz: abgleich: ok", "ABGL", "GEGEN", "Ran 1 test", self.erster,
249|                      "NZTEXT", "#### test_t1_neu", "self.assertEqual(mod.f(), 2)"):
250|             self.assertIn(soll, text, soll)
251|         for nicht in ("QUELLTEXT", "FEHLERTABELLE", "AUFBAUTEXT", "LANGE AUSGABE", "UMGESETZT", "test_x ... ok"):
252|             self.assertNotIn(nicht, text, nicht)
253|         self.assertIn("Zeichen, ca.", out)
254| 
255|     def test_paket_nur_dateien_aus_handover_und_nie_werkzeug(self):
256|         self._paket_vorbereiten()
257|         (self.root / "role-split").mkdir()
258|         (self.root / "role-split" / "werkzeug.py").write_text("W = 1\n")
259|         ho = kette.PM / "handover_20261022_g.md"
260|         ho.write_text(ho.read_text(encoding="utf-8") + "\n## Geänderte und neue Dateien\n- `neu_modul.py` – neu\n",
261|                       encoding="utf-8")
262|         lauf(kette.paket, "g")
263|         text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
264|         self.assertIn("### neu_modul.py", text)
265|         self.assertNotIn("### mod.py", text)
266|         self.assertNotIn("werkzeug.py", text.split("## 3.")[1].split("## 4.")[0])
267| 
268|     def test_paket_kleine_aenderung_als_diff(self):
269|         self._paket_vorbereiten()
270|         groß = "".join(f"def f{i}():\n    return {i}\n" for i in range(40))
271|         (self.root / "gross.py").write_text(groß)
272|         self.git("add", "gross.py"); self.git("commit", "-qm", "gross")
273|         import subprocess
274|         alt_commit = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--short", "HEAD"],
275|                                     capture_output=True, text=True).stdout.strip()
276|         (self.root / "gross.py").write_text(groß.replace("return 7\n", "return 70\n"))
277|         lauf(kette.paket, "g", alt_commit)
278|         text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
279|         self.assertIn("### gross.py (Diff", text)
280|         self.assertIn("+    return 70", text)
281| 
282|     def test_paket_kappt_lange_dateien(self):
283|         self._paket_vorbereiten()
284|         (self.root / "neu_modul.py").write_text("".join(f"Z{i} = {i}\n" for i in range(50)))
285|         alt = kette.PAKET_DATEI_ZEILEN; kette.PAKET_DATEI_ZEILEN = 10
286|         self.addCleanup(setattr, kette, "PAKET_DATEI_ZEILEN", alt)
287|         lauf(kette.paket, "g")
288|         text = (kette.PM / "review_paket_20261022_g.md").read_text(encoding="utf-8")
289|         self.assertIn("40 weitere Zeilen gekuerzt", text)
290|         self.assertNotIn("Z45 = 45", text)
291| 
292|     def test_paket_ohne_spec_schreibt_nichts(self):
293|         code, out = lauf(kette.paket, "g")
294|         self.assertEqual(code, 2); self.assertIn("Keine Spec", out)
295|         self.assertEqual(list(kette.PM.glob("review_paket_*")), [])
296| 
297|     def test_prompt_review_baut_paket_und_nennt_es(self):
298|         self._paket_vorbereiten()
299|         code, out = lauf(kette.prompt, "review", "g", None, None)
300|         self.assertEqual(code, 0)
301|         self.assertTrue((kette.PM / "review_paket_20261022_g.md").exists())
302|         self.assertIn("review_paket_20261022_g.md", out)
303| 
304|     def test_kurztitel_mit_pfad_abgelehnt(self):
305|         code, out = lauf(kette.pruefen, "../x")
306|         self.assertEqual(code, 2); self.assertIn("ungueltig", out)
```

### `role-split/kette/test_kette.py` class GegenprobeTests (Zeilen 144–171) – enthält `test_rot_und_gruen`. Wird um einen Test für `role-split/kette/` erweitert.

```python
144| class GegenprobeTests(unittest.TestCase):
145|     def test_rot_und_gruen(self):
146|         import subprocess
147|         d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
148|         root = Path(d.name)
149|         def git(*a):
150|             subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
151|                            check=True, capture_output=True)
152|         git("init", "-q")
153|         (root / "mod.py").write_text("def f():\n    return 1\n")
154|         git("add", "."); git("commit", "-qm", "alt")
155|         alt = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
156|         (root / "mod.py").write_text("def f():\n    return 2\n")
157|         (root / "neu.py").write_text("X = 1\n")
158|         (root / "tests").mkdir()
159|         (root / "tests" / "test_g.py").write_text(
160|             "import sys, unittest\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).parent.parent))\n"
161|             "class T(unittest.TestCase):\n"
162|             "    def test_t1_neu(self):\n        import mod\n        self.assertEqual(mod.f(), 2)\n"
163|             "    def test_t2_bestand(self):\n        self.assertEqual(1, 1)\n")
164|         alt_root = kette.ROOT; kette.ROOT = root
165|         self.addCleanup(lambda: setattr(kette, "ROOT", alt_root))
166|         code, out = lauf(kette.gegenprobe, "g", alt, 60)
167|         self.assertEqual(code, 1, out)
168|         self.assertIn("rot   test_t1_neu  <- mod.py", out)
169|         self.assertIn("GRUEN test_t2_bestand", out)
170|         self.assertEqual((root / "mod.py").read_text(), "def f():\n    return 2\n")
171|         self.assertTrue((root / "neu.py").exists())
```

### `role-split/kette/prompts/review_api.md` (Zeilen 7–7) – `{paket_text}`-Platzhalter. Nicht geändert, aber der Konsument des Pakets.

```markdown
7| {paket_text}
```

### `role-split/kette/prompts/review2_api.md` (Zeilen 7–7) – `{paket_text}`-Platzhalter. Nicht geändert.

```markdown
7| {paket_text}
```
