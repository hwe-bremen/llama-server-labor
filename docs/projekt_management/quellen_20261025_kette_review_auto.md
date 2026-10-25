# Quellen: kette_review_auto

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen kette_review_auto` (2026-10-25 12:21, Stand `c04e261`), nach dem Abschnitt „Quellen“ in `spec_20261025_kette_review_auto.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` (Zeilen 449–493) – Aufruf für Schritt 1 (Tests) per `def pruefen`; Rückgabe `max(codes.values())` über abgleich, unittest und gegenprobe – also auch 1, wenn nur abgleich oder gegenprobe abweichen (in K7 bei jedem Durchgang so). Für A2 wird das Teilergebnis `unittest` gebraucht (siehe A2).

```python
449| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
450|     import contextlib
451|     import io
452|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
453|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
454|     commit = commit or spec_commit(kurztitel)
455|     if not commit:
456|         print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
457|               f"(git log --oneline -10)."); return 2
458|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
459|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
460|     teile, codes = [], {}
461| 
462|     def schritt(titel: str, fn) -> None:
463|         puffer = io.StringIO()
464|         with contextlib.redirect_stdout(puffer):
465|             try:
466|                 codes[titel] = fn()
467|             except Exception as e:                       # Werkzeugfehler sichtbar machen, nicht verschlucken
468|                 print(f"!!! Werkzeugfehler: {type(e).__name__}: {e}")
469|                 codes[titel] = 2
470|         teile.append(f"## {titel}  (Exit {codes[titel]})\n\n```\n{puffer.getvalue().rstrip()}\n```\n")
471| 
472|     def unittest_lauf() -> int:
473|         if not skript.is_file():
474|             print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
475|         r = subprocess.run([sys.executable, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
476|                            cwd=ROOT, capture_output=True, text=True, timeout=timeout)
477|         print((r.stdout + r.stderr).rstrip())
478|         return 0 if r.returncode == 0 else 1
479| 
480|     schritt("abgleich", lambda: abgleich(kurztitel))
481|     schritt("unittest", unittest_lauf)
482|     schritt(f"gegenprobe gegen {commit}", lambda: gegenprobe(kurztitel, commit, timeout))
483| 
484|     kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
485|                       for k, v in codes.items())
486|     kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
487|             f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
488|     ziel = PM / f"pruefung_{datum}_{kurztitel}.md"
489|     ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
490|     print("\n".join(teile))
491|     print(f"\n==> {kurz}")
492|     print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
493|     return max(codes.values())
```

### `role-split/kette/kette.py` (Zeilen 640–694) – Aufruf für Schritt 2 per `def paket`; Rückgabe 0 = Paket geschrieben; schreibt `review_paket_<datum>_<kurztitel>.md`.

```python
640| def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, still: bool = False) -> int:
641|     """Schreibt review_paket_<datum>_<kurztitel>.md. Rueckgabe 0 = geschrieben, 2 = Voraussetzung fehlt."""
642|     say = (lambda *a: None) if still else print
643|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
644|         say(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
645|     spec_p = datei_suchen("spec", kurztitel, datum)
646|     if not spec_p:
647|         say(f"Keine Spec spec_*_{kurztitel}.md – kein Review-Paket."); return 2
648|     datum = datum or _datum_aus(spec_p)
649|     commit = commit or spec_commit(kurztitel)
650|     if not commit:
651|         say(f"Kein Commit 'Spec {kurztitel}' – Ruecksetzpunkt mit --commit angeben."); return 2
652|     anf_p = datei_suchen("anforderung", kurztitel, None)
653|     ho_p = datei_suchen("handover", kurztitel, None)
654|     pr_p = datei_suchen("pruefung", kurztitel, None)
655|     spec = spec_p.read_text(encoding="utf-8")
656|     nur = _handover_dateien(ho_p.read_text(encoding="utf-8")) if ho_p else None
657|     try:
658|         diff, dateien = _diff(commit, nur)
659|     except subprocess.CalledProcessError as e:
660|         say(f"git-Fehler: {(e.stderr.strip().splitlines() or ['?'])[0]}"); return 2
661|     teile = [
662|         f"# Review-Paket: {kurztitel}\n",
663|         f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
664|         f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in dateien) or 'keine'}.\n"
665|         "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
666|         "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
667|         "## 1. Anforderung (verbindlich, woertlich)\n\n"
668|         + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
669|         f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
670|         f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
671|         f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
672|         f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
673|         f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
674|         f"## 3. Code-Aenderungen gegen `{commit}`\n\n{diff}",
675|         f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(ROOT / 'tests' / f'test_{kurztitel}.py')}"
676|         + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if (tc := _testcode(
677|             ROOT / "tests" / f"test_{kurztitel}.py",
678|             _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())) else ""),
679|         "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
680|         + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
681|             or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
682|         f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
683|     ]
684|     text = "\n\n".join(teile).rstrip() + "\n"
685|     ziel = PM / f"review_paket_{datum}_{kurztitel}.md"
686|     ziel.write_text(text, encoding="utf-8")
687|     groesse = len(text)
688|     say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)")
689|     if groesse > PAKET_WARNUNG_ZEICHEN:
690|         say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen – fuer 64K Kontext eng. "
691|             "Review dann eher in Teilen (z. B. erst Anforderungen A1–A3).")
692|     if not pr_p:
693|         say("Hinweis: keine pruefung_*-Datei – erst `kette.py pruefen <kurztitel>` laufen lassen.")
694|     return 0
```

### `role-split/kette/kette.py` (Zeilen 698–704) – Wiederverwendung für die auswertbare-Tabelle-Prüfung (A5) per `def _befunde` und `def _ist_hoch`.

```python
698| def _befunde(text: str) -> list[dict]:
699|     return tabelle(abschnitt(text, "Befunde"))
700| 
701| 
702| def _ist_hoch(zeile: dict) -> bool:
703|     schwere = (spalte(zeile, "schwere") or "").lower()
704|     return "hoch" in schwere or any(ja(spalte(zeile, n)) for n in ("datenverl", "unbemerkt", "harte"))
```

### `role-split/kette/kette.py` (Zeilen 84–115) – Parsing der Verdikt-Antwort (Befund-Tabelle erkennen) per `def abschnitt`, `def tabelle`, `def spalte`, `def ja`.

```python
 84| def abschnitt(text: str, titel: str) -> str:
 85|     """Inhalt unter '## <titel...>' bis zur naechsten '## '-Ueberschrift ('' wenn fehlt)."""
 86|     m = re.search(rf"^##\s+{re.escape(titel)}[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
 87|     return m.group(1) if m else ""
 88| 
 89| 
 90| def tabelle(block: str) -> list[dict]:
 91|     """Erste Markdown-Tabelle im Block als Liste von Dicts (Spaltennamen kleingeschrieben)."""
 92|     zeilen = [z.strip() for z in block.splitlines() if z.strip().startswith("|")]
 93|     if len(zeilen) < 2:
 94|         return []
 95|     zellen = lambda z: [c.strip() for c in z.strip("|").split("|")]
 96|     kopf = [k.lower() for k in zellen(zeilen[0])]
 97|     daten = []
 98|     for z in zeilen[1:]:
 99|         if re.fullmatch(r"[\s|:\-]+", z):
100|             continue
101|         werte = zellen(z)
102|         daten.append({k: (werte[i] if i < len(werte) else "") for i, k in enumerate(kopf)})
103|     return daten
104| 
105| 
106| def spalte(zeile: dict, *namen: str) -> str | None:
107|     """Wert der ersten Spalte, deren Name einen der Begriffe enthaelt."""
108|     for k, v in zeile.items():
109|         if any(n in k for n in namen):
110|             return v
111|     return None
112| 
113| 
114| def ja(wert: str | None) -> bool:
115|     return bool(wert) and wert.strip().strip("*").lower().startswith("ja")
```

### `role-split/kette/kette.py` (Zeilen 707–753) – Aufruf für Schritt 6 per `def zusammenfuehren`; schreibt `gesamt_<datum>_<kurztitel>.md`.

```python
707| def zusammenfuehren(pfade: list[Path]) -> int:
708|     if len(pfade) < 2:
709|         print("Mindestens zwei Verdikte angeben."); return 2
710|     zeilen, ergebnisse, fehlt = [], [], []
711|     for p in pfade:
712|         if not p.is_file():
713|             fehlt.append(str(p)); continue
714|         text = p.read_text(encoding="utf-8")
715|         m = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis") or text)
716|         ergebnisse.append((p.name, m.group(1) if m else "?"))
717|         befunde = _befunde(text)
718|         if not befunde:
719|             zeilen.append((p.name, "?", "(keine Befundtabelle erkannt – Verdikt von Hand lesen)", "", False))
720|         for b in befunde:
721|             schwere = spalte(b, "schwere") or "?"
722|             text_b = spalte(b, "befund", "begründung", "begruendung") or " | ".join(v for v in b.values() if v)
723|             ort = spalte(b, "datei", "zeile", "anfor") or ""
724|             zeilen.append((p.name, schwere, text_b, ort, _ist_hoch(b)))
725|     if fehlt:
726|         print("Fehlt: " + ", ".join(fehlt)); return 2
727|     hoch = [z for z in zeilen if z[4]]
728|     if hoch or any(e == "NACHBESSERN" for _, e in ergebnisse):
729|         urteil_ = "NACHBESSERN"
730|     elif any(e == "FAIL" for _, e in ergebnisse):
731|         urteil_ = "FAIL"
732|     elif all(e == "PASS" for _, e in ergebnisse):
733|         urteil_ = "PASS"
734|     else:
735|         urteil_ = "UNKLAR"
736|     if any(e == "FAIL" for _, e in ergebnisse):
737|         urteil_ = "FAIL"
738|     m = re.match(r"verdict_(\d{8})_(.+?)_[^_]+(?:_[^_]+)*\.md$", pfade[0].name)
739|     datum = m.group(1) if m else dt.date.today().strftime("%Y%m%d")
740|     kt = re.match(r"verdict_\d{8}_([a-z0-9_]+?)_(?:qwen|gemma|mellum|apertus|claude|hawe)", pfade[0].name)
741|     kurz = kt.group(1) if kt else "review"
742|     teile = [f"# Gesamtbefund: {kurz}\n",
743|              f"Mechanisch zusammengeführt mit `kette.py zusammenfuehren` ({dt.datetime.now():%Y-%m-%d %H:%M}). Kein Befund wurde weggelassen oder umformuliert.\n",
744|              "## Ergebnis\n", f"**{urteil_}** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.\n",
745|              "| Lauf | Ergebnis des Laufs |", "|---|---|"] + [f"| `{n}` | {e} |" for n, e in ergebnisse] + [
746|              "", "## Befunde (alle Läufe)\n", "| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |", "|---|---|---|---|---|"]
747|     for n, s_, t, o, h in zeilen:
748|         teile.append(f"| `{n}` | {s_} | {'ja' if h else 'nein'} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
749|     ziel = PM / f"gesamt_{datum}_{kurz}.md"
750|     ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
751|     print(f"{len(zeilen)} Befunde aus {len(ergebnisse)} Läufen, davon {len(hoch)} hoch -> {urteil_}")
752|     print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
753|     return 0 if urteil_ == "PASS" else 1
```

### `role-split/kette/kette.py` (Zeilen 1002–1054) – Muster für Prompt-Aufbau (Platzhalter, `<!--`-Zeilen streichen) per `def prompt`.

```python
1002| def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None, lauf: int | None = None) -> int:
1003|     vorlage = PROMPTS / f"{schritt}.md"
1004|     if not vorlage.is_file():
1005|         print(f"Keine Vorlage: {vorlage}"); return 2
1006|     anf = datei_suchen("anforderung", kurztitel, datum)
1007|     if not datum:
1008|         # Datum der vorhandenen Spec (Kette 4: "heute" passte nicht mehr am Folgetag)
1009|         datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or _datum_aus(anf) \
1010|             or dt.date.today().strftime("%Y%m%d")
1011|         anf = anf or datei_suchen("anforderung", kurztitel, datum)
1012|     if not commit and schritt != "spec":
1013|         commit = spec_commit(kurztitel)          # Ruecksetzpunkt = Commit "Spec <kurztitel>" (22.10.)
1014|         if commit:
1015|             print(f"Ruecksetzpunkt = Commit 'Spec {kurztitel}' ({commit}).", file=sys.stderr)
1016|     if not commit:
1017|         try:
1018|             commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
1019|                                     capture_output=True, text=True, check=True).stdout.strip()
1020|         except Exception:
1021|             commit = "<HASH>"
1022|         if schritt != "spec":
1023|             print(f"Hinweis: Ruecksetzpunkt = HEAD von {ROOT} ({commit}). Stimmt das (Worktree?)? "
1024|                   "Sonst --commit angeben.", file=sys.stderr)
1025|     paket_pfad = f"docs/projekt_management/review_paket_{datum}_{kurztitel}.md"
1026|     if schritt in ("review", "review2", "tief"):
1027|         if paket(kurztitel, commit if commit != "<HASH>" else None, None, still=False) != 0:
1028|             print("Hinweis: Review-Paket nicht gebaut (siehe oben) – Prompt verweist trotzdem darauf.",
1029|                   file=sys.stderr)
1030|     anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
1031|         f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
1032|     if not anf:
1033|         print(f"Hinweis: {anf_pfad} fehlt. Anlegen mit: kette.py anforderung {kurztitel} --aufgabe \"…\"",
1034|               file=sys.stderr)
1035|     text = (vorlage.read_text(encoding="utf-8")
1036|             .replace("{kurztitel}", kurztitel)
1037|             .replace("{datum}", datum)
1038|             .replace("{commit}", commit)
1039|             .replace("{anforderung}", anf_pfad)
1040|             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md")
1041|             .replace("{paket}", paket_pfad))
1042|     if anf:
1043|         text = re.sub(r"<AUFGABE[^>]*>", lambda _m: aufgabe_lesen(anf), text)
1044|     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
1045|     if lauf:
1046|         # Eigener Dateiname je Review-Lauf: sonst findet Lauf 2 das Verdikt von Lauf 1 (geschuetzt),
1047|         # liest es und haengt an (Probe K4, 22.10.) -> Laeufe nicht mehr unabhaengig.
1048|         text = text.replace("_<modellkürzel>.md", f"_<modellkürzel>_lauf{lauf}.md")
1049|         text += "Verdikte anderer Läufe liest du nicht.\n"
1050|     print(text)
1051|     if shutil.which("pbcopy"):
1052|         subprocess.run(["pbcopy"], input=text, text=True)
1053|         print("(in die Zwischenablage kopiert)", file=sys.stderr)
1054|     return 0
```

### `role-split/kette/kette.py` (Zeilen 1058–1103) – Muster für Subbefehl-Registrierung im `argparse` per `def main`.

```python
1058| def main(argv=None) -> int:
1059|     ap = argparse.ArgumentParser(description="Werkzeug fuer die Kette Spec -> Umsetzung -> Review")
1060|     sub = ap.add_subparsers(dest="cmd", required=True)
1061|     p = sub.add_parser("prompt"); p.add_argument("schritt", choices=SCHRITTE); p.add_argument("kurztitel")
1062|     p.add_argument("--datum"); p.add_argument("--commit")
1063|     p.add_argument("--lauf", type=int, help="Review-Lauf-Nummer (eigener Verdikt-Dateiname je Lauf)")
1064|     q = sub.add_parser("quellen"); q.add_argument("kurztitel"); q.add_argument("--datum")
1065|     n = sub.add_parser("anforderung"); n.add_argument("kurztitel")
1066|     n.add_argument("--aufgabe"); n.add_argument("--antwort"); n.add_argument("--frage"); n.add_argument("--datum")
1067|     a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
1068|     u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
1069|     g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
1070|     g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
1071|     g.add_argument("--timeout", type=int, default=300)
1072|     zf = sub.add_parser("zusammenfuehren", help="Befunde mehrerer Review-Laeufe mechanisch zusammenfuehren")
1073|     zf.add_argument("verdikte", nargs="+")
1074|     pk = sub.add_parser("paket", help="Review-Paket bauen (eine Datei fuers Review)")
1075|     pk.add_argument("kurztitel"); pk.add_argument("--commit"); pk.add_argument("--datum")
1076|     pr = sub.add_parser("pruefen", help="abgleich + unittest + gegenprobe, Ausgabe in Datei")
1077|     pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
1078|     args = ap.parse_args(argv)
1079|     if args.cmd == "zusammenfuehren":
1080|         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
1081|                                 for v in args.verdikte])
1082|     if args.cmd == "paket":
1083|         return paket(args.kurztitel, args.commit, args.datum)
1084|     if args.cmd == "pruefen":
1085|         return pruefen(args.kurztitel, args.commit, args.timeout)
1086|     if args.cmd == "gegenprobe":
1087|         return gegenprobe(args.kurztitel, args.commit, args.timeout)
1088|     if args.cmd == "quellen":
1089|         return quellen(args.kurztitel, args.datum)
1090|     if args.cmd == "anforderung":
1091|         return anforderung(args.kurztitel, args.aufgabe, args.antwort, args.frage, args.datum)
1092|     if args.cmd == "prompt":
1093|         return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
1094|     if args.cmd == "abgleich":
1095|         return abgleich(args.kurztitel, args.datum)
1096|     pfad = Path(args.verdikt)
1097|     if not pfad.is_absolute() and not pfad.exists():
1098|         pfad = PM / pfad.name
1099|     return urteil(pfad, args.anhaengen)
1100| 
1101| 
1102| if __name__ == "__main__":
1103|     sys.exit(main())
```

### `role-split/kette/kette.py` (Zeilen 253–260) – Rücksetzpunkt bestimmen (Commit „Spec <kurztitel>") per `def datei_suchen`.

```python
253| def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
254|     if datum:
255|         p = PM / f"{typ}_{datum}_{kurztitel}.md"
256|         return p if p.is_file() else None
257|     # Nur exakt <typ>_<JJJJMMTT>_<kurztitel>.md – sonst greift z. B. handover_..._nachbesserung2_<kt>.md (K6, 23.10.)
258|     muster = re.compile(rf"^{re.escape(typ)}_\d{{8}}_{re.escape(kurztitel)}\.md$")
259|     treffer = sorted(p for p in PM.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
260|     return treffer[-1] if treffer else None
```

### `role-split/kette/kette.py` (Zeilen 438–446) – Rücksetzpunkt bestimmen per `def spec_commit`; für die Paket-/Prüfungsschritte.

```python
438| def spec_commit(kurztitel: str) -> str | None:
439|     """Aeltester Commit, dessen Betreffzeile genau "Spec <kurztitel>" ist (= Ruecksetzpunkt)."""
440|     r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h%x09%s"],
441|                        capture_output=True, text=True)
442|     if r.returncode != 0:
443|         return None
444|     treffer = [z.split("\t", 1)[0] for z in r.stdout.splitlines()
445|                if "\t" in z and z.split("\t", 1)[1].strip() == f"Spec {kurztitel}"]
446|     return treffer[-1] if treffer else None
```

### `role-split/kette/prompts/review.md` (Zeilen 1–22) – ganze Datei (Zeilen 1–27) – Basis für die API-Fassung von Lauf 1; enthält die Sätze mit Datei-Zugriff („Lies NUR {paket}", „write_file", „append_file"), die in der API-Fassung gestrichen/ersetzt werden.

```markdown
 1| <!-- Schritt D, start_eval, NEUER Chat, Qwen3.6, Reasoning aus. kette.py baut vorher das Review-Paket. Danach: urteil. -->
 2| @review Prüf die Umsetzung zu „{kurztitel}".
 3| Lies NUR {paket}. Darin stehen Anforderung (verbindlich), Spec-Auszug, Code-Diff gegen {commit}, Testliste, Abweichungen aus dem Handover und die maschinelle Prüfung. Ganze Dateien liest du nicht; höchstens drei gezielte Nachlesungen (search_files oder ein Zeilenbereich), wenn eine Frage anders nicht zu klären ist. Ältere Verdikte liest du nicht.
 4| Nur falls das Paket fehlt: Anforderung {anforderung}, Spec docs/projekt_management/spec_{datum}_{kurztitel}.md, Handover docs/projekt_management/handover_{datum}_{kurztitel}.md, Diff gegen {commit} – dann gezielt, nicht vollständig lesen.
 5| 
 6| 1. Spec gegen Anforderung: Widerspricht eine Designentscheidung oder ein „akzeptiertes Restrisiko" der Anforderung? Das ist ein Befund (Harte Vorgabe: ja), auch wenn der Code die Spec korrekt umsetzt.
 7| 2. Für JEDE Anforderung beantwortest du diese sechs Pflichtfragen mit Fundstelle (Datei:Zeile):
 8|    a) Erzwungen oder nur verlangt? Steht das Verlangte nur in einem Prompt an ein LLM, in einem Kommentar oder in der Spec – oder erzwingt der Code es auch dann, wenn das LLM, der Feed oder die Eingabe sich nicht daran hält?
 9|    b) Leerer und abweichender Fall: Was passiert konkret, wenn die Eingabe leer ist (keine Einträge, leere Datei, leere Antwort) oder anders aussieht als erwartet (andere Überschrift, andere Schreibweise, fehlendes Feld)? Spiel es mit einem konkreten Beispiel durch.
10|    c) Markiert, aber nie gezeigt? Wird etwas als erledigt, verarbeitet oder gesendet markiert, das der Nutzer nie zu sehen bekommt? Das ist IMMER ein Befund „hoch" (Unbemerkt: ja) – auch wenn es beabsichtigt oder im Handover begründet wirkt.
11|    d) Läuft die Absicherung selbst ins Leere? Gibt es einen Pfad, in dem eine Prüf- oder Nachtrags-Logik nichts tut, obwohl ihre Bedingung erfüllt ist (z. B. Bedingung prüft lose, Ersetzung sucht exakt)?
12|    e) Widersprüchliche Anweisungen: Enthält ein Prompt an ein LLM, eine Konfiguration oder ein Kommentar Anweisungen, die einander oder der Anforderung widersprechen (z. B. zwei Regeln, die nicht gleichzeitig erfüllbar sind)? Dann folgt das LLM zufällig einer davon – Befund.
13|    f) Anforderung Satz für Satz: Nimm jeden Satz der Anforderung (auch die Antworten auf Rückfragen) und prüfe am Code, ob er nach einem normalen Lauf, einem Wiederholungslauf und einem Fehlerlauf (Abbruch, Netzfehler) noch stimmt.
14|    Jede Antwort mit „nur verlangt", „verloren", „verschluckt", „unbemerkt", „läuft ins Leere", „widerspricht" oder „stimmt nicht mehr" ist ein Befund – in der Befundtabelle, nicht nur in der Anforderungstabelle. Was die Spec unter „Nicht-Ziele" ausschließt, ist kein Befund.
15| 3. Tests: Für jeden GRUEN- oder ANDERS-Test steht sein Code im Paket. Sag je Test, ob er bewusst Bestehendes prüft (in Ordnung) oder die neue Logik, die sein Titel nennt, gar nicht ausführt (Befund). Fehlt für eine Pflichtfrage mit Befund ein Test, ist auch das ein Befund.
16| 
17| Verdikt KNAPP (Richtwert 40 Zeilen; wird es länger, ist das in Ordnung – eine gespeicherte Datei nie löschen, kürzen oder unter neuem Namen neu schreiben), Form nach _vorlage_verdict.md (Abschnitte Ergebnis, Anforderungen einzeln, Befunde mit den Spalten Datenverlust / Unbemerkt / Harte Vorgabe, Nicht geprüft). Keine Wiederholung des Pakets.
18| Speichern in Abschnitten, damit bei vollem Kontext nichts verloren geht:
19| - erst write_file: Kopf + „## Ergebnis" + „## Befunde" (Tabelle),
20| - dann append_file: „## Anforderungen einzeln",
21| - dann append_file: „## Nicht geprüft".
22| Datei: docs/projekt_management/verdict_{datum}_{kurztitel}_<modellkürzel>.md
```

### `role-split/kette/prompts/review2.md` (Zeilen 1–13) – ganze Datei (Zeilen 1–13) – Basis für die API-Fassung von Lauf 2 (Betrieb).

```markdown
 1| <!-- Schritt D, Lauf 2 (anderer Blickwinkel), start_eval, NEUER Chat. Liest Lauf 1 nicht. Danach: kette.py zusammenfuehren. -->
 2| @review Zweites Review zu „{kurztitel}" – Blickwinkel BETRIEB. Ein erstes Review hat Code und Spec schon gegen die Anforderung geprüft; du suchst gezielt, was dabei typischerweise übersehen wird.
 3| Lies NUR {paket}. Höchstens drei gezielte Nachlesungen (search_files oder Zeilenbereich). Verdikte liest du nicht.
 4| Nur falls das Paket fehlt: Anforderung {anforderung}, Spec docs/projekt_management/spec_{datum}_{kurztitel}.md, Diff gegen {commit} – gezielt, nicht vollständig.
 5| 
 6| 1. Echte Abhängigkeiten statt Attrappen: Wo ersetzen die Tests eine echte Abhängigkeit (LLM/Modell, Netz, Server, Postfach, Dateisystem, Schlüsselbund, Uhrzeit)? Was liefert die echte Abhängigkeit anders als die Attrappe (Format und Zusatztext, Fehler, Zeitüberschreitung, Langsamkeit, Sonderzeichen)? Spiel für jede solche Stelle durch, was der Code dann tut. Läuft das Werkzeug mit der echten Abhängigkeit überhaupt durch?
 7| 2. Wiederkehrende Fehler: Gibt es eine Eingabe, die bei JEDEM Lauf erneut scheitert (einen kaputten oder ungewöhnlichen Datensatz)? Bleibt sie dann für immer hängen, ohne dass der Nutzer sie zu sehen bekommt? Wird ein vorübergehender Fehler (Netz) anders behandelt als ein dauerhafter (unbrauchbarer Inhalt)?
 8| 3. Anforderung Satz für Satz: Nimm jeden Satz der Anforderung (auch die Antworten auf Rückfragen). Widersprechen sich zwei Sätze in einem Fall? Stimmt jeder Satz nach einem normalen Lauf, einem Wiederholungslauf und einem Fehlerlauf noch?
 9| 4. Erster echter Einsatz: Was muss der Nutzer beim ersten Start mit echten Daten vorher einrichten, und was passiert, wenn es fehlt (Ordner, Konfigurationsdatei, Schlüsselbund-Eintrag, Port, TLS)? Ist die Fehlermeldung dann verständlich?
10| Was die Spec unter „Nicht-Ziele" ausschließt, ist kein Befund. Wiederhole keine reinen Stilfragen.
11| 
12| Verdikt KNAPP (Richtwert 40 Zeilen; nie löschen, kürzen oder neu schreiben), Form nach _vorlage_verdict.md (Ergebnis, Befunde mit den Spalten Datenverlust / Unbemerkt / Harte Vorgabe, Nicht geprüft). Speichern: erst write_file (Kopf, Ergebnis, Befunde), dann append_file für weitere Abschnitte.
13| Datei: docs/projekt_management/verdict_{datum}_{kurztitel}_<modellkürzel>_betrieb.md
```

### `agents/mail_planung/mail_planung.py` (Zeilen 540–554) – bewährtes Muster für den API-Aufruf: `requests.post` auf `{URL}/v1/chat/completions`, JSON mit `model`, `messages`, `temperature`, `chat_template_kwargs: {"enable_thinking": False}`, `timeout`.

```python
540|     user_prompt = f"Analysiere folgende E-Mail:\n\n{body}"
541| 
542|     response = requests.post(
543|         f"{MAIL_LLM_URL}/v1/chat/completions",
544|         json={
545|             "model": MAIL_LLM_MODEL,
546|             "messages": [
547|                 {"role": "system", "content": system_prompt},
548|                 {"role": "user", "content": user_prompt},
549|             ],
550|             "temperature": 0.1,
551|             "chat_template_kwargs": {"enable_thinking": False},
552|         },
553|         timeout=LLM_TIMEOUT,
554|     )
```

### `docs/projekt_management/_vorlage_verdict.md` (Zeilen 1–45) – ganze Datei (Zeilen 1–45) – erwartete Form des Verdikts (Abschnitte Ergebnis, Anforderungen einzeln, Befunde mit Spalten Datenverlust/Unbemerkt/Harte Vorgabe), woran die auswertbare-Tabelle-Prüfung gemessen wird.

```markdown
 1| # Verdikt: <kurztitel>
 2| 
 3| - **Spec:** `spec_<JJJJMMTT>_<kurztitel>.md`
 4| - **Handover:** `handover_<JJJJMMTT>_<kurztitel>.md`
 5| - **Datum:** <JJJJ-MM-TT>
 6| - **Modell:** <Modellname aus dem System-Prompt>
 7| - **Geprüfte Dateien:** <Liste der tatsächlich gelesenen Code-Dateien>
 8| 
 9| Dateiname: `verdict_<JJJJMMTT>_<kurztitel>_<modellkürzel>.md`
10| 
11| ## Ergebnis
12| 
13| **PASS | NACHBESSERN | FAIL** – ein bis zwei Sätze Begründung.
14| 
15| ## Anforderungen einzeln
16| 
17| | Nr. | Anforderung (kurz) | Befund | Fundstelle |
18| |---|---|---|---|
19| | 1 | … | erfüllt / teilweise / nicht | `datei.py:42` |
20| 
21| ## Handover gegen Code
22| 
23| - <Aussagen im Handover, die der Code nicht stützt. „Keine Abweichung gefunden", wenn so.>
24| - <Behauptete Tests ohne Ausgabe gelten als nicht belegt.>
25| 
26| ## Befunde
27| 
28| Für **jeden** Befund drei Fragen mit ja/nein beantworten. Ein „ja" macht den Befund „hoch", unabhängig davon,
29| ob die Schwäche schon vorher bestand. `kette.py urteil` prüft das nach.
30| - **Datenverlust:** Kann Daten verlieren, überschreiben oder echte Daten verändern?
31| - **Unbemerkt:** Kann ein Fehler unbemerkt bleiben (Hänger, Schweigen, falscher Exit-Code, Test misst nichts)?
32| - **Harte Vorgabe:** Verstößt es gegen eine harte Vorgabe der Spec oder des Auftrags (z. B. kein echter Versand)?
33| 
34| | # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
35| |---|---|---|---|---|---|---|---|
36| | 1 | ja / nein | ja / nein | ja / nein | hoch / mittel / niedrig | | | |
37| 
38| ## Nicht geprüft
39| 
40| - **Kann Hawe selbst prüfen:** <Test, Lauf, Blick in Datei>
41| - **Braucht externe Quelle:** <Doku, Recherche, frische Instanz>
42| 
43| ## Abweichende Meinung
44| 
45| - <Wo die Review-Instanz anders entschieden hätte, auch bei PASS. „Keine", wenn keine.>
```

### `role-split/kette/test_kette.py` (Zeilen 1–40) – Muster für die Teststruktur (unittest, `tempfile.TemporaryDirectory`, `redirect_stdout`, `sys.path.insert`).

```python
 1| #!/usr/bin/env python3
 2| """Selbsttest fuer kette.py (stdlib, ohne Modell):  python3 role-split/kette/test_kette.py"""
 3| import io
 4| import sys
 5| import tempfile
 6| import unittest
 7| from contextlib import redirect_stdout
 8| from pathlib import Path
 9| 
10| sys.path.insert(0, str(Path(__file__).resolve().parent))
11| import kette  # noqa: E402
12| 
13| KOPF = "# Verdikt: x\n\n## Ergebnis\n\n**{u}** – Text.\n\n## Anforderungen einzeln\n\n" \
14|        "| Nr. | Anforderung | Befund | Fundstelle |\n|---|---|---|---|\n{anf}\n\n## Befunde\n\n" \
15|        "| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg |\n" \
16|        "|---|---|---|---|---|---|---|---|\n{bef}\n"
17| 
18| 
19| def lauf(fn, *a):
20|     buf = io.StringIO()
21|     with redirect_stdout(buf):
22|         code = fn(*a)
23|     return code, buf.getvalue()
24| 
25| 
26| class UrteilTests(unittest.TestCase):
27|     def verdikt(self, u, anf, bef):
28|         d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
29|         p = Path(d.name) / "verdict_x.md"
30|         p.write_text(KOPF.format(u=u, anf=anf, bef=bef), encoding="utf-8")
31|         return p
32| 
33|     def test_haenger_als_niedrig_wird_hoch(self):
34|         # Tiefenpruefung 17.10. im neuen Format: Timeout fehlt, 'niedrig', aber Fehler bleibt unbemerkt
35|         p = self.verdikt("PASS", "| A1 | Fehler-Mail | erfüllt | x.py:1 |",
36|                          "| 3 | nein | ja | nein | niedrig | x.py:192 | kein SMTP-Timeout | timeout= setzen |")
37|         code, out = lauf(kette.urteil, p)
38|         self.assertEqual(code, 1)
39|         self.assertIn("Es gilt:             NACHBESSERN", out)
40|         self.assertIn("WIDERSPRUCH", out)
```
