# Spec-Paket: paket_vollstaendig (gebaut 25.10. von Claude, Stand Commit 5bba1f3)

Alles, was die Spec braucht. **Lies nur diese Datei und die Anforderung.** Weitere Stellen nur, wenn wirklich etwas fehlt: search_files + read_file mit start_line/end_line, höchstens drei Nachlesungen. Zeilennummern sind echte Zeilen der jeweiligen Datei.

## 1. kette.py – Übersicht (Funktionen und Paket-Konstanten)
```
  79| ROOT = HERE.parent.parent
  80| PM = ROOT / "docs" / "projekt_management"
  86| def abschnitt(text: str, titel: str) -> str:
  92| def tabelle(block: str) -> list[dict]:
 108| def spalte(zeile: dict, *namen: str) -> str | None:
 116| def ja(wert: str | None) -> bool:
 121| def urteil(pfad: Path, anhaengen: bool = False) -> int:
 197| def tests_finden(text: str) -> dict[str, str]:
 211| def woerter(titel: str) -> set[str]:
 216| def passt(spec_titel: str, ho_titel: str) -> float:
 226| def methoden_pruefen(code: str) -> list[str]:
 255| def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
 265| def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
 320| def name(t): return t.id().split(".")[-1].split(" ")[0]
 322| def alle(s):
 338| def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
 355| def _zuruecksetzen_und_testen(skript: Path, d: str, commit: str, timeout: int) -> dict[str, str] | None:
 382| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
 440| def spec_commit(kurztitel: str) -> str | None:
 451| def _pruefen_teile(kurztitel: str, commit: str | None = None, timeout: int = 300) -> dict:
 490| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
 519| PAKET_DIFF_ZEILEN = 700        # je Datei; Rest liest das Review gezielt nach
 520| PAKET_DATEI_ZEILEN = 900       # bei Umbau: ganze aktuelle Datei statt Diff, hoechstens so viele Zeilen
 521| PAKET_WARNUNG_ZEICHEN = 80000  # ~23k Token: darueber wird es fuer 64K Kontext eng
 523| PAKET_NIE = ("docs/", "tests/", "role-split/", "mcp-server/", "experiments/")
 526| def _bloecke(text: str, muster: str) -> str:
 543| def _testplan_kurz(spec: str) -> str:
 553| def _testliste(skript: Path) -> str:
 568| def _auffaellige_tests(pruefung: str) -> set[str]:
 578| def _testcode(skript: Path, auffaellig: set[str], grenze: int = 60) -> str:
 601| def _diff(commit: str, nur: set[str] | None = None) -> tuple[str, list[str]]:
 629| def _kappen(datei: str, zeilen: list[str], art: str, grenze: int) -> str:
 641| def _handover_dateien(text: str) -> set[str] | None:
 648| def _pruefung_kurz(pfad: Path | None) -> str:
 662| def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, still: bool = False) -> int:
 720| def _befunde(text: str) -> list[dict]:
 724| def _ist_hoch(zeile: dict) -> bool:
 729| def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
 801| def _datum_aus(pfad: Path | None) -> str | None:
 806| def aufgabe_lesen(pfad: Path) -> str:
 813| def anforderung(kurztitel: str, aufgabe: str | None, antwort: str | None, frage: str | None,
 855| def quelle_lesen(z: str) -> dict | None:
 893| def _block_name(zeilen: list[str], name: str) -> tuple[tuple[int, int] | None, str]:
 910| def _textstelle(zeilen: list[str], text: str, umfeld: int = 12) -> tuple[int, int] | None:
 917| def _passt(code_zeilen: list[str], zweck: str | None) -> list[str]:
 936| def _block(zeilen: list[str], art: str, name: str) -> tuple[int, int] | None:
 959| def quellen(kurztitel: str, datum: str | None = None) -> int:
1046| def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None, lauf: int | None = None) -> int:
1108| def _rel(pfad):
1119| def _herzschlag_stopp_event(lauf_nummer: int):
1135| def _api_ruf(prompt_text: str, lauf_nummer: int) -> tuple[str | None, dict]:
1186| def _freier_verdiktpfad(datum: str, kurztitel: str, lauf: int) -> Path:
1203| def _ist_auswertbar(verdikt_text: str) -> bool:
1218| def review_auto(kurztitel: str) -> int:
1355| def main(argv=None) -> int:
```

## 2. kette.py – tests_laufen, _zuruecksetzen_und_testen, gegenprobe, spec_commit (Zeilen 338–450)
```python
 338| def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
 339|     """Laesst das Testskript in einem eigenen Prozess laufen; Ergebnis je Testmethode."""
 340|     modul = ".".join(skript.relative_to(ROOT).with_suffix("").parts)
 341|     # Eigener, frischer Bytecode-Cache je Lauf: sonst kann Python eine alte .pyc weiterverwenden,
 342|     # wenn die zurueckgesetzte Datei gleich gross ist und in derselben Sekunde geschrieben wurde.
 343|     with tempfile.TemporaryDirectory(prefix="kette_pyc_") as cache:
 344|         try:
 345|             r = subprocess.run([sys.executable, "-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul],
 346|                                cwd=ROOT, capture_output=True, text=True, timeout=timeout)
 347|         except subprocess.TimeoutExpired:
 348|             return None
 349|     for zeile in reversed(r.stdout.splitlines()):
 350|         if zeile.startswith("@@KETTE@@"):
 351|             return json.loads(zeile[len("@@KETTE@@"):])
 352|     return {"<Testskript laedt nicht>": "ERROR"}
 353| 
 354| 
 355| def _zuruecksetzen_und_testen(skript: Path, d: str, commit: str, timeout: int) -> dict[str, str] | None:
 356|     """Eine Datei voruebergehend auf <commit> zuruecksetzen, Tests laufen lassen, wiederherstellen."""
 357|     pfad = ROOT / d
 358|     sicherung = Path(tempfile.mkdtemp(prefix="gegenprobe_"))
 359|     kopie, weg = sicherung / "kopie", pfad.with_name(pfad.name + ".gegenprobe_weg")
 360|     summe = hashlib.sha256(pfad.read_bytes()).hexdigest() if pfad.exists() else None
 361|     try:
 362|         if pfad.exists():
 363|             shutil.copy2(pfad, kopie)
 364|         alt = subprocess.run(["git", "-C", str(ROOT), "show", f"{commit}:{d}"], capture_output=True)
 365|         if alt.returncode == 0:
 366|             pfad.write_bytes(alt.stdout)
 367|         elif pfad.exists():                       # Datei ist neu -> im alten Stand gab es sie nicht
 368|             pfad.rename(weg)                      # umbenennen statt loeschen
 369|         return tests_laufen(skript, timeout)
 370|     finally:
 371|         if weg.exists():
 372|             weg.rename(pfad)
 373|         elif kopie.exists():
 374|             shutil.copy2(kopie, pfad)
 375|         ok = summe is None or (pfad.exists() and hashlib.sha256(pfad.read_bytes()).hexdigest() == summe)
 376|         if ok:
 377|             shutil.rmtree(sicherung, ignore_errors=True)
 378|         else:
 379|             print(f"!!! {d} nicht sauber wiederhergestellt. Sicherung: {kopie}")
 380| 
 381| 
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
 439| 
 440| def spec_commit(kurztitel: str) -> str | None:
 441|     """Aeltester Commit, dessen Betreffzeile genau "Spec <kurztitel>" ist (= Ruecksetzpunkt)."""
 442|     r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h%x09%s"],
 443|                        capture_output=True, text=True)
 444|     if r.returncode != 0:
 445|         return None
 446|     treffer = [z.split("\t", 1)[0] for z in r.stdout.splitlines()
 447|                if "\t" in z and z.split("\t", 1)[1].strip() == f"Spec {kurztitel}"]
 448|     return treffer[-1] if treffer else None
 449| 
 450| 
```

## 3. kette.py – Paket-Konstanten, Hilfsfunktionen und paket (Zeilen 519–719)
```python
 519| PAKET_DIFF_ZEILEN = 700        # je Datei; Rest liest das Review gezielt nach
 520| PAKET_DATEI_ZEILEN = 900       # bei Umbau: ganze aktuelle Datei statt Diff, hoechstens so viele Zeilen
 521| PAKET_WARNUNG_ZEICHEN = 80000  # ~23k Token: darueber wird es fuer 64K Kontext eng
 522| # Werkzeug-/Infrastruktur-Ordner gehoeren nie zur Aufgabe (sonst landen spaetere Werkzeug-Commits im Diff).
 523| PAKET_NIE = ("docs/", "tests/", "role-split/", "mcp-server/", "experiments/")
 524| 
 525| 
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
 541| 
 542| 
 543| def _testplan_kurz(spec: str) -> str:
 544|     """Aus dem Testplan nur die Test-Ueberschriften und die Erwartungs-Zeilen."""
 545|     block = abschnitt(spec, "Testplan")
 546|     raus = []
 547|     for z in block.splitlines():
 548|         if z.startswith("### ") or re.match(r"^\s*-\s*\*\*Erwartung", z):
 549|             raus.append(z)
 550|     return "\n".join(raus).strip()
 551| 
 552| 
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
 599| 
 600| 
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
 627| 
 628| 
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
 639| 
 640| 
 641| def _handover_dateien(text: str) -> set[str] | None:
 642|     """Pfade in Backticks aus dem Handover (Abschnitte 'Geaenderte … Dateien'). None, wenn keine."""
 643|     bloecke = _bloecke(text, r"ge[aä]nderte|neue dateien")
 644|     pfade = {m for m in re.findall(r"`([\w./-]+\.\w+)`", bloecke) if "/" in m or "." in m}
 645|     return pfade or None
 646| 
 647| 
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
 660| 
 661| 
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
 719| 
```

## 4. kette.py – Aufruf von paket in review_auto (Zeilen 1230–1243)
```python
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
```

## 5. test_kette.py – Gegenprobe-Tests (ab Zeile 144, 90 Zeilen)
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
 172| 
 173| 
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
```

## 6. test_kette.py – Paket-Tests (Zeilen 237–311)
```python
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
 307| 
 308| 
 309| class TestcodeTests(unittest.TestCase):
 310|     def test_auffaellige_ids(self):
 311|         txt = "  GRUEN test_t12_x  (..)\n  LADEN test_t3_y (..)\n  ANDERS    T8    Spec: …\n  rot   test_t1_z <- a.py\n"
```

## 7. RUNBOOK – Phase C (wie pruefen/gegenprobe heute beschrieben sind)
## Phase C – Maschinelle Prüfung (ein Befehl)

```bash
python3 role-split/kette/kette.py pruefen <kurztitel>
```

Das macht nacheinander **abgleich** (Spec-Tests vs. Handover/Testskript), **unittest** und **gegenprobe**
(jede geänderte Datei einzeln auf den alten Stand zurück – wird ein Test dann rot, misst er die Änderung).
Die ganze Ausgabe steht danach in `pruefung_<datum>_<kurztitel>.md`.

**Lesen – nur die letzte Zeile:**

| Kurzzeile | Bedeutung | Weiter mit |
|---|---|---|
| `unittest: Abweichung` | Tests rot | direkt **F → Nachbessern** (kein Review nötig) |
| `gegenprobe: Abweichung` | mind. ein Test `GRUEN` (bleibt mit altem Code grün) | normal: im Review/Gegenprüfung ansehen lassen; Bestandstests sind ok |
| `abgleich: Abweichung` | Test fehlt, umbenannt (`ANDERS`) oder ohne Methode | im Review/Gegenprüfung ansehen lassen |
| `… FEHLER` | Werkzeug konnte nicht laufen (Datei fehlt, kein Spec-Commit) | Meldung lesen; Rücksetzpunkt fehlt → `pruefen <kurztitel> --commit <hash>` |

Achtung: `gegenprobe` verändert Dateien für Sekunden – nicht laufen lassen, während OpenCode arbeitet.

---

## 8. Gemessene Fakten (Claude, 24./25.10.)
- **Warum es den Handover-Filter gibt (22.10.):** Das Paket war 128 141 Zeichen groß, weil Werkzeug-Commits zwischen Spec-Commit und Umsetzung (Änderungen an `kette.py` durch Claude) und ein Umbau-Diff mitkamen. Nach Filter „nur Dateien aus dem Handover-Abschnitt ‚Geänderte und neue Dateien‘" plus `PAKET_NIE`: 58 661 Zeichen.
- **K7 (`mail_server_test`), Paket vom 25.10.:** „Geänderte Code-Dateien: keine". Neueste Übergabe (NB3, 24.10.) nannte `agents/mail_planung/mail_planung.py` nicht; fast der ganze K7-Code liegt unter `tests/` (in `PAKET_NIE`). Folge im echten `review-auto`-Lauf: beide Läufe meldeten A4/A5 fälschlich „nicht umgesetzt".
- **K8 (`kette_review_auto`):** Code in `role-split/kette/kette.py` (in `PAKET_NIE`), `gegenprobe` meldete „Keine geaenderten Code-Dateien" (filtert `role-split/kette/`). Claude ergänzte das Paket von Hand (`experiments/k8_paket_ergaenzen.py`).
- **Größen der echten Änderungen (ohne docs/):**
```
K7: git diff --stat 37b1da1 0ddd9bc
 agents/mail_planung/mail_planung.py                |  48 ++-
 tests/mail_server_test/einliefern.py               | 103 +++++
 tests/mail_server_test/erwartungen.json            | 134 ++++++
 .../mail_server_test/mails/01_einfach_eintrag.eml  |  16 +
 tests/mail_server_test/mails/02_nur_html.eml       |  17 +
 .../mail_server_test/mails/03_anhang_ignoriert.eml |  36 ++
 tests/mail_server_test/mails/04_leer.eml           |  15 +
 tests/mail_server_test/mails/05_umlaut_betreff.eml |  15 +
 tests/mail_server_test/mails/06_weiterleitung.eml  |  29 ++
 .../mails/07_doppelte_message_id.eml               |  16 +
 tests/mail_server_test/mails/08_sehr_lang.eml      | 114 ++++++
 .../mails/09_termin_ohne_datum.eml                 |  14 +
 .../mail_server_test/mails/10_ungueltiges_json.eml |  19 +
 tests/mail_server_test/mails/11_injection.eml      |  21 +
 tests/mail_server_test/mails/12_leerer_betreff.eml |  12 +
 .../mail_server_test/mails/13_multipart_mixed.eml  |  34 ++
 tests/mail_server_test/mails/14_synthetic_id.eml   |  12 +
 .../mails/15_kurze_bestatigung.eml                 |  12 +
 .../mail_server_test/mails/16_duplikat_neue_id.eml |  16 +
 tests/mail_server_test/pruefen.py                  | 232 +++++++++++
 tests/mail_server_test/start_test_mailserver.sh    | 150 +++++++
 tests/test_mail_server_test.py                     | 450 +++++++++++++++++++++
 22 files changed, 1503 insertions(+), 12 deletions(-)

K8: git diff --stat a74e250 04e2ced
 role-split/kette/RUNBOOK.md             |  13 +
 role-split/kette/kette.py               | 335 ++++++++++++++++++++--
 role-split/kette/prompts/review2_api.md |  60 ++++
 role-split/kette/prompts/review_api.md  |  66 +++++
 role-split/roles/idee.md                |  55 ++++
 tests/test_kette_review_auto.py         | 485 ++++++++++++++++++++++++++++++++
 6 files changed, 997 insertions(+), 17 deletions(-)
```
- **Fremde Commits im Bereich:** Zwischen Spec-Commit und Abschluss von K8 liegt ein Commit, der nicht zur Kette gehört (Rolle `@idee`, RUNBOOK):
```
04e2ced Kette kette_review_auto: review-auto (Stufe 1), NB1/NB2, echter Lauf
80916fd Rolle @idee (Phase 0: Idee klaeren) + RUNBOOK
```
  Ein reines `git diff <rücksetzpunkt>` nimmt solche Dateien mit. Das ist das Problem, das der Handover-Filter einmal lösen sollte.
- **Gegenprobe-Hintergrund:** Sie setzt je Datei den alten Stand ein und lässt die Tests laufen. `role-split/kette/` ist ausgenommen; Vermutung (Claude): weil das Zurücksetzen von `kette.py` das laufende Werkzeug selbst betrifft. Ein bereits gestarteter Python-Prozess hat seinen Code geladen; die Tests laufen in einem Unterprozess.
- Review-Modell: Kontext 65 536 Token; `PAKET_WARNUNG_ZEICHEN` = 80 000 (~23k Token). K7-Paket (ohne Code) 43 052 Zeichen; mit K7-Code geschätzt deutlich mehr (`.eml`-Testdaten ~550 Zeilen, `08_sehr_lang.eml` allein > 20 000 Zeichen Text).
- `review-auto` ruft `paket(kurztitel)` ohne Commit; Rücksetzpunkt = Commit „Spec <kurztitel>" (`spec_commit`).
