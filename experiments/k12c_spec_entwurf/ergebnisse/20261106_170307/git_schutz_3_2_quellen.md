# Quellen Schritt 2 (12 ok, 0 schlecht)


### `role-split/kette/kette.py` def _bloecke (Zeilen 692–706) – Parsen der Spec-Struktur für Schreibbereich und Anforderungen

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

### `role-split/kette/kette.py` def _diff (Zeilen 774–797) – Erzeugen des Diffs für das Review-Paket

```python
774| def _diff(commit: str, nur: set[str] | None = None, kurztitel: str | None = None
775|           ) -> tuple[dict[str, tuple[str, int]], list[str], list[str]]:
776|     """Inhalte der zur Kette gehoerigen Dateien gegen <commit>.
777|     Rueckgabe: (eintraege {datei: (abschnitt, vorrang)}, fremd_zeilen, kette_dateien)."""
778|     kette, fremd = _aenderungen(commit, kurztitel, nur)
779|     neu = set(_git("ls-files", "--others", "--exclude-standard").split())
780|     eintraege: dict[str, tuple[str, int]] = {}
781|     for d in kette:
782|         nicht_genannt = nur is None or d not in nur
783|         aktuell = (ROOT / d).read_text(encoding="utf-8", errors="replace").splitlines()
784|         nummeriert = [f"{i:4d}  {z}" for i, z in enumerate(aktuell, 1)]
785|         if d in neu:
786|             inhalt = _kappen(d, nummeriert, "neu", PAKET_DATEI_ZEILEN, nicht_genannt)
787|         else:
788|             diff = _git("diff", "-U3", commit, "--", d).splitlines()
789|             if len(diff) > len(aktuell):
790|                 inhalt = _kappen(d, nummeriert, "umbau", PAKET_DATEI_ZEILEN, nicht_genannt)
791|             else:
792|                 inhalt = _kappen(d, diff, "diff", PAKET_DIFF_ZEILEN, nicht_genannt)
793|         eintraege[d] = (inhalt, _vorrang(d, nur))
794|     fremd_zeilen = [f"- `{d}` – " + (", ".join(f"`{h}` ({b})" for h, b in dc) or "ohne Commit-Angabe")
795|                     + " – nicht Teil dieser Kette, nicht bewerten, nur zur Kenntnis"
796|                     for d, dc in fremd]
797|     return eintraege, fremd_zeilen, kette
```

### `role-split/kette/kette.py` def _ist_vorgabe (Zeilen 1646–1649) – Prüfen, ob eine Datei Teil der Vorgabe ist

```python
1646| def _ist_vorgabe(pfad: str) -> bool:
1647|     """Spec, Anforderung, Quellen, Vorlagen der Kette – darf die Umsetzung nie aendern."""
1648|     name = Path(pfad).name
1649|     return name.endswith(".md") and name.startswith(VORGABE_PRAEFIXE)
```

### `role-split/kette/kette.py` def _aenderungen (Zeilen 657–689) – Ermitteln der geänderten Dateien im aktuellen Stand

```python
657| def _aenderungen(commit: str, kurztitel: str | None, nur: set[str] | None = None
658|                  ) -> tuple[list[str], list[tuple[str, list[tuple[str, str]]]]]:
659|     """A1: Alle seit <commit> geaenderten/neuen Dateien (ausser PAKET_NIE), getrennt nach
660|     zur Kette gehoerig / fremd. Gemeinsame Auswahl fuer paket und gegenprobe (A5).
661| 
662|     Quellen: Commits <commit>..HEAD, nicht committete Aenderungen (auch vorgemerkt),
663|     unversionierte Dateien. Zur Kette gehoert eine Datei, wenn sie (a) in einem Commit mit dem
664|     Kurztitel in der Nachricht geaendert wurde, (b) nicht committete oder unversionierte
665|     Aenderungen hat oder (c) in der Uebergabe genannt wird. Sonst fremd.
666|     Rueckgabe: (kette, fremd) mit fremd = [(datei, [(kurzhash, betreff), ...]), ...]."""
667|     committet = set(_git("diff", "--name-only", commit, "HEAD").split())
668|     offen = set(_git("diff", "--name-only", "HEAD").split())          # unstaged + staged
669|     neu = set(_git("ls-files", "--others", "--exclude-standard").split())
670|     alle = sorted(d for d in committet | offen | neu
671|                   if not d.startswith(PAKET_NIE) and (ROOT / d).is_file())
672|     log = [z.split("\t", 1) for z in _git("log", "--format=%H%x09%s", f"{commit}..HEAD").splitlines()
673|            if "\t" in z]
674|     # Kurztitel als ganzes Wort (nicht "g" in "gross"): links/rechts kein a-z, 0-9, _
675|     muster = re.compile(rf"(?<![a-z0-9_]){re.escape(kurztitel)}(?![a-z0-9_])") if kurztitel else None
676|     eigene = {h for h, betreff in log if muster and muster.search(betreff)}
677|     kette: list[str] = []
678|     fremd: list[tuple[str, list[tuple[str, str]]]] = []
679|     for d in alle:
680|         if d in offen or d in neu or (nur and d in nur):
681|             kette.append(d)
682|             continue
683|         dc = [z.split("\t", 1) for z in
684|               _git("log", "--format=%H%x09%s", f"{commit}..HEAD", "--", d).splitlines() if "\t" in z]
685|         if any(h in eigene for h, _ in dc):
686|             kette.append(d)
687|         else:
688|             fremd.append((d, [(h[:7], b) for h, b in dc]))
689|     return kette, fremd
```

### `role-split/kette/kette.py` def gegenprobe (Zeilen 432–489) – Logik zum Zurücksetzen und Testen

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

### `role-split/kette/kette.py` def pruefen (Zeilen 615–642) – Hauptlogik für Prüfung und Gegenprobe

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

### `role-split/kette/kette.py` def paket (Zeilen 835–938) – Zusammenstellen des Review-Pakets

```python
835| def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, still: bool = False) -> int:
836|     """Schreibt review_paket_<datum>_<kurztitel>.md. Rueckgabe 0 = geschrieben, 2 = Voraussetzung fehlt."""
837|     say = (lambda *a: None) if still else print
838|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
839|         say(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
840|     spec_p = datei_suchen("spec", kurztitel, datum)
841|     if not spec_p:
842|         say(f"Keine Spec spec_*_{kurztitel}.md – kein Review-Paket."); return 2
843|     datum = datum or _datum_aus(spec_p)
844|     commit = commit or spec_commit(kurztitel)
845|     if not commit:
846|         say(f"Kein Commit 'Spec {kurztitel}' – Ruecksetzpunkt mit --commit angeben."); return 2
847|     anf_p = datei_suchen("anforderung", kurztitel, None)
848|     ho_p = datei_suchen("handover", kurztitel, None)
849|     pr_p = datei_suchen("pruefung", kurztitel, None)
850|     spec = spec_p.read_text(encoding="utf-8")
851|     nur = _handover_dateien(ho_p.read_text(encoding="utf-8")) if ho_p else None
852|     try:
853|         eintraege, fremd_zeilen, kette = _diff(commit, nur, kurztitel)
854|     except subprocess.CalledProcessError as e:
855|         say(f"git-Fehler: {(e.stderr.strip().splitlines() or ['?'])[0]}"); return 2
856| 
857|     def bauen(drin: dict[str, tuple[str, int]], weg: list[str]) -> str:
858|         code = "\n\n".join(drin[d][0] for d in sorted(drin)) or "(keine Code-Aenderungen gegen den Ruecksetzpunkt)"
859|         weg_zeilen = []
860|         for d in sorted(weg):
861|             grund = {2: "Testcode", 3: "Testdaten"}.get(_vorrang(d, nur), "?")
862|             zusatz = " (nicht in der Uebergabe genannt)" if nur is None or d not in nur else ""
863|             weg_zeilen.append(f"- `{d}` – {grund}, Paket zu gross{zusatz}")
864|         teile = [
865|             f"# Review-Paket: {kurztitel}\n",
866|             f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
867|             f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in sorted(drin)) or 'keine'}.\n"
868|             "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
869|             "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
870|             "## 1. Anforderung (verbindlich, woertlich)\n\n"
871|             + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
872|             f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
873|             f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
874|             f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
875|             f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
876|             f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
877|             f"## 3. Code-Aenderungen gegen `{commit}`\n\n{code}",
878|         ]
879|         if fremd_zeilen:
880|             teile.append("## 3a. Fremde Aenderungen (nur Liste)\n\nDiese Dateien wurden nur in Commits ohne den "
881|                          f"Kurztitel `{kurztitel}` geaendert. Sie gehoeren nicht zur Aufgabe – nicht bewerten.\n\n"
882|                          + "\n".join(fremd_zeilen))
883|         if weg_zeilen:
884|             teile.append("## 3b. Weggelassen (Paket zu gross)\n\nTeil der Kette, aber wegen der Paketgroesse "
885|                          "ohne Inhalt. Bei Bedarf gezielt nachlesen.\n\n" + "\n".join(weg_zeilen))
886|         skript = ROOT / "tests" / f"test_{kurztitel}.py"
887|         tc = _testcode(skript, _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())
888|         teile += [
889|             f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(skript)}"
890|             + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if tc else ""),
891|             "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
892|             + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
893|                 or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
894|             f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
895|         ]
896|         return "\n\n".join(teile).rstrip() + "\n"
897| 
898|     # A7: Aenderungen ausserhalb docs/, aber nichts davon gehoert zur Kette -> lauter Fehler
899|     if not eintraege and fremd_zeilen:
900|         say(f"Paket ohne Code trotz Aenderungen seit {commit}: {len(fremd_zeilen)} Datei(en), davon "
901|             f"{len(fremd_zeilen)} fremd. Commits ohne Kurztitel '{kurztitel}' in der Nachricht? "
902|             "Dann Ruecksetzpunkt/Kurztitel pruefen. Exit 1, kein Paket.")
903|         return 1
904| 
905|     # A3: nach Gesamtgroesse kuerzen – erst Vorrang 3, dann 2; Vorrang 1 nie
906|     drin, weg = dict(eintraege), []
907|     text = bauen(drin, weg)
908|     for stufe in (3, 2):
909|         if len(text) <= PAKET_WARNUNG_ZEICHEN:
910|             break
911|         for d in sorted(x for x, (_, v) in drin.items() if v == stufe):
912|             weg.append(d); del drin[d]
913|             text = bauen(drin, weg)
914|             if len(text) <= PAKET_WARNUNG_ZEICHEN:
915|                 break
916| 
917|     # A7 (Fall b): Kette-Dateien vorhanden, aber nach der Kuerzung keine mit Inhalt
918|     if eintraege and not drin:
919|         say("Paket ohne Code trotz Aenderungen: alle Dateien der Kette mussten weggelassen werden. Exit 1, kein Paket.")
920|         return 1
921| 
922|     groesse = len(text)
923|     # A4: harte Obergrenze vor dem Schreiben
924|     if groesse > KETTE_PAKET_MAX:
925|         say(f"Paket passt nicht in den Kontext des Review-Modells, Review in Teilen noetig "
926|             f"({groesse} Zeichen > KETTE_PAKET_MAX {KETTE_PAKET_MAX}). Exit 1, kein Paket.")
927|         return 1
928|     ziel = ablage(kurztitel) / f"review_paket_{datum}_{kurztitel}.md"
929|     ziel.write_text(text, encoding="utf-8")
930|     say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)"
931|         + (f", {len(weg)} Datei(en) weggelassen" if weg else "") + (f", {len(fremd_zeilen)} fremd" if fremd_zeilen else ""))
932|     if groesse > PAKET_WARNUNG_ZEICHEN:
933|         say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen (nur noch Vorrang 1) – fuer 64K Kontext eng.")
934|     if not pr_p:
935|         say("Hinweis: keine pruefung_*-Datei – erst `kette.py pruefen <kurztitel>` laufen lassen.")
936|     return 0
937| 
938| # ---------------------------------------------------------------- zusammenfuehren
```

### `role-split/kette/kette.py` def urteil (Zeilen 165–233) – Ableiten des Urteils aus dem Verdikt

```python
165| def urteil(pfad: Path, anhaengen: bool = False) -> int:
166|     if not pfad.is_file():
167|         print(f"Nicht gefunden: {pfad}"); return 2
168|     text = pfad.read_text(encoding="utf-8")
169|     m = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis"))
170|     modell = m.group(1) if m else None
171|     hinweise, korrekturen = [], []
172| 
173|     offen = []
174|     for z in tabelle(abschnitt(text, "Anforderungen")):
175|         status = (spalte(z, "befund", "status") or "").lower()
176|         if "teilweise" in status or re.search(r"\bnicht\b", status):
177|             offen.append(f"{spalte(z, 'nr') or '?'}: {status}")
178| 
179|     befunde = tabelle(abschnitt(text, "Befunde"))
180|     hoch = []
181|     kriterien_da = befunde and any(spalte(befunde[0], k) is not None
182|                                    for k in ("datenverlust", "unbemerkt", "harte"))
183|     if befunde and not kriterien_da:
184|         hinweise.append("Altes Format: Befunde ohne Spalten Datenverlust/Unbemerkt/Harte Vorgabe "
185|                         "-- Schwere wird nur uebernommen, nicht geprueft.")
186|     for z in befunde:
187|         nr = spalte(z, "#") or "?"
188|         schwere = (spalte(z, "schwere") or "").lower()
189|         if not schwere.strip(" -"):
190|             continue  # leere Vorlagenzeile
191|         gruende = [k for k, n in (("Datenverlust", "datenverlust"), ("Unbemerkt", "unbemerkt"),
192|                                   ("Harte Vorgabe", "harte")) if ja(spalte(z, n))]
193|         if gruende and "hoch" not in schwere:
194|             korrekturen.append(f"Befund {nr}: als '{schwere}' eingestuft, aber ja bei "
195|                                f"{', '.join(gruende)} -> hoch")
196|             hoch.append(nr)
197|         elif "hoch" in schwere:
198|             hoch.append(nr)
199| 
200|     regel = "NACHBESSERN" if (hoch or offen) else "PASS"
201|     # Die Regel verschaerft nur: ein strengeres Modellurteil bleibt stehen.
202|     rang = {"PASS": 0, "NACHBESSERN": 1, "FAIL": 2}
203|     mech = max(regel, modell or "PASS", key=rang.get)
204| 
205|     zeilen = [f"Modell-Urteil:       {modell or 'nicht gefunden'}",
206|               f"Regel-Urteil:        {regel}",
207|               f"Es gilt:             {mech}"]
208|     if hoch:
209|         zeilen.append(f"  Befunde hoch: {', '.join(hoch)}")
210|     if offen:
211|         zeilen.append(f"  Anforderungen offen: {'; '.join(offen)}")
212|     zeilen += [f"  Korrektur: {k}" for k in korrekturen]
213|     zeilen += [f"  Hinweis: {h}" for h in hinweise]
214|     if modell and rang[regel] > rang[modell]:
215|         zeilen.append(f"  WIDERSPRUCH: Modell sagt {modell}, die Regel verlangt {regel}.")
216|     elif modell and rang[regel] < rang[modell]:
217|         zeilen.append(f"  Modell strenger als die Regel -- Begruendung im Verdikt lesen.")
218|     print("\n".join(zeilen))
219| 
220|     if anhaengen:
221|         marke = "## Mechanisches Urteil (kette.py)"
222|         if marke in text:
223|             print("(Abschnitt existiert schon, nicht erneut angehaengt)")
224|         else:
225|             stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
226|             pfad.write_text(text.rstrip("\n") + f"\n\n{marke}\n\n_{stamp}_\n\n```\n"
227|                             + "\n".join(zeilen) + "\n```\n", encoding="utf-8")
228|             print(f"Angehaengt an {pfad.name}")
229|     if modell is None and not befunde:
230|         return 2
231|     return 0 if mech == "PASS" else 1
232| 
233| # ---------------------------------------------------------------- abgleich
```

### `role-split/kette/automatik.py` def stand (Zeilen 38–88) – Ermitteln des Projektstands

```python
38| def stand(kurztitel: str) -> dict:
39|     """Stand der Kette aus den vorhandenen Dateien."""
40|     spec_p = kette.datei_suchen("spec", kurztitel, None)
41|     spec_commit = kette.spec_commit(kurztitel)
42|     spec_text = spec_p.read_text(encoding="utf-8") if spec_p else ""
43|     vorgabe = kette._vorgabe_tests(spec_text)
44| 
45|     # Laeufe aus Protokoll
46|     protokoll_p = kette.datei_suchen("umsetzung", kurztitel, None)
47|     laeufe = []
48|     if protokoll_p:
49|         text = protokoll_p.read_text(encoding="utf-8")
50|         muster = re.compile(r"art:\s*(erst|nb\d+),\s*Exit:\s*(\d+)")
51|         for z in text.splitlines():
52|             if not z.lstrip().startswith("- **"):
53|                 continue
54|             m = muster.search(z)
55|             if m:
56|                 laeufe.append((m.group(1), int(m.group(2))))
57| 
58|     # Review aus Gesamtbefund
59|     review = None
60|     gesamt_p = kette.datei_suchen("gesamt", kurztitel, None)
61|     if gesamt_p:
62|         text = gesamt_p.read_text(encoding="utf-8")
63|         for z in text.splitlines():
64|             if "**" in z:
65|                 for wert in ("PASS", "NACHBESSERN", "UNVOLLSTÄNDIG"):
66|                     if f"**{wert}**" in z:
67|                         review = wert
68|                         break
69|                 if review:
70|                     break
71| 
72|     # Offene Dateien
73|     offen_list = []
74|     r = subprocess.run(
75|         ["git", "-C", str(kette.ROOT), "status", "--porcelain"],
76|         capture_output=True, text=True,
77|     )
78|     if r.returncode == 0:
79|         offen_list = [line.strip() for line in r.stdout.splitlines() if line.strip()]
80| 
81|     return {
82|         "spec": str(spec_p) if spec_p else None,
83|         "spec_commit": spec_commit,
84|         "vorgabe": vorgabe,
85|         "laeufe": laeufe,
86|         "review": review,
87|         "offen": offen_list,
88|     }
```

### `role-split/kette/einsortieren.py` def zuordnen (Zeilen 15–29) – Zuordnen von Dateien zu Ketten

```python
15| def zuordnen(name: str, kurztitel_liste: list[str]) -> str | None:
16|     """name nach Typ+Datum+Kurztitel auflösen; laengster Treffer gewinnt."""
17|     m = DATEI_RE.match(name)
18|     if not m:
19|         return None
20|     typ, _datum, rest = m.groups()
21|     if typ not in TYPEN:
22|         return None
23|     treffer = []
24|     for kt in kurztitel_liste:
25|         if rest == kt or rest.startswith(kt + "_"):
26|             treffer.append(kt)
27|     if not treffer:
28|         return None
29|     return max(treffer, key=len)
```

### `role-split/kette/kette.py` def _git (Zeilen 653–654) – Aufruf von Git-Befehlen

```python
653| def _git(*a: str) -> str:
654|     return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
```

### `role-split/kette/kette.py` def _rel (Zeilen 1353–1361) – Pfadkonvertierung

```python
1353| def _rel(pfad):
1354|     """Pfad relativ zu ROOT, falls möglich, sonst absolut."""
1355|     try:
1356|         return pfad.relative_to(ROOT)
1357|     except ValueError:
1358|         return pfad
1359| 
1360| 
1361| # ------------------------------------------------------------------ review-auto (A2–A8)
```
