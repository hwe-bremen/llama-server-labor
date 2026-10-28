# Quellen: ablage_ordner

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen ablage_ordner` (2026-10-28 13:57, Stand `b128473`), nach dem Abschnitt „Quellen“ in `spec_20261028_ablage_ordner.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` def datei_suchen (Zeilen 266–273) – Suche nach `<typ>_<datum>_<kt>.md` (E2)

```python
266| def datei_suchen(typ: str, kurztitel: str, datum: str | None) -> Path | None:
267|     if datum:
268|         p = PM / f"{typ}_{datum}_{kurztitel}.md"
269|         return p if p.is_file() else None
270|     # Nur exakt <typ>_<JJJJMMTT>_<kurztitel>.md – sonst greift z. B. handover_..._nachbesserung2_<kt>.md (K6, 23.10.)
271|     muster = re.compile(rf"^{re.escape(typ)}_\d{{8}}_{re.escape(kurztitel)}\.md$")
272|     treffer = sorted(p for p in PM.glob(f"{typ}_*_{kurztitel}.md") if muster.match(p.name))
273|     return treffer[-1] if treffer else None
```

### `role-split/kette/kette.py` def pruefen (Zeilen 579–606) – Ziel `pruefung_…` (E3)

```python
579| def pruefen(kurztitel: str, commit: str | None = None, timeout: int = 300) -> int:
580|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
581|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
582|     commit = commit or spec_commit(kurztitel)
583|     if not commit:
584|         print(f"Kein Commit 'Spec {kurztitel}' gefunden. Ruecksetzpunkt mit --commit angeben "
585|               f"(git log --oneline -10)."); return 2
586|     teile_dict = _pruefen_teile(kurztitel, commit, timeout)
587|     codes = {k: v[0] for k, v in teile_dict.items()}
588|     teile = []
589|     for titel_key in ("abgleich", "unittest", "gegenprobe"):
590|         code, out = teile_dict[titel_key]
591|         # Titel wiederherstellen: gegenprobe braucht {commit}
592|         titel = f"gegenprobe gegen {commit}" if titel_key == "gegenprobe" else titel_key
593|         teile.append(f"## {titel}  (Exit {code})\n\n```\n{out.rstrip()}\n```\n")
594|     kurz = " | ".join(f"{k.split()[0]}: {'ok' if v == 0 else ('Abweichung' if v == 1 else 'FEHLER')}"
595|                       for k, v in codes.items())
596|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
597|     kopf = (f"# Pruefung {kurztitel}\n\n- Zeit: {dt.datetime.now():%Y-%m-%d %H:%M}\n"
598|             f"- Ruecksetzpunkt: {commit}\n- Kurz: {kurz}\n\n")
599|     ziel = PM / f"pruefung_{datum}_{kurztitel}.md"
600|     ziel.write_text(kopf + "\n".join(teile), encoding="utf-8")
601|     print("\n".join(teile))
602|     print(f"\n==> {kurz}")
603|     print(f"==> Ausgabe gespeichert: {ziel.relative_to(ROOT)}  (dem Gegenpruefer nur noch Bescheid sagen)")
604|     return max(codes.values())
605| 
606| # ---------------------------------------------------------------- Review-Paket
```

### `role-split/kette/kette.py` def paket (Zeilen 799–902) – Ziel `review_paket_…` (E3)

```python
799| def paket(kurztitel: str, commit: str | None = None, datum: str | None = None, still: bool = False) -> int:
800|     """Schreibt review_paket_<datum>_<kurztitel>.md. Rueckgabe 0 = geschrieben, 2 = Voraussetzung fehlt."""
801|     say = (lambda *a: None) if still else print
802|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
803|         say(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
804|     spec_p = datei_suchen("spec", kurztitel, datum)
805|     if not spec_p:
806|         say(f"Keine Spec spec_*_{kurztitel}.md – kein Review-Paket."); return 2
807|     datum = datum or _datum_aus(spec_p)
808|     commit = commit or spec_commit(kurztitel)
809|     if not commit:
810|         say(f"Kein Commit 'Spec {kurztitel}' – Ruecksetzpunkt mit --commit angeben."); return 2
811|     anf_p = datei_suchen("anforderung", kurztitel, None)
812|     ho_p = datei_suchen("handover", kurztitel, None)
813|     pr_p = datei_suchen("pruefung", kurztitel, None)
814|     spec = spec_p.read_text(encoding="utf-8")
815|     nur = _handover_dateien(ho_p.read_text(encoding="utf-8")) if ho_p else None
816|     try:
817|         eintraege, fremd_zeilen, kette = _diff(commit, nur, kurztitel)
818|     except subprocess.CalledProcessError as e:
819|         say(f"git-Fehler: {(e.stderr.strip().splitlines() or ['?'])[0]}"); return 2
820| 
821|     def bauen(drin: dict[str, tuple[str, int]], weg: list[str]) -> str:
822|         code = "\n\n".join(drin[d][0] for d in sorted(drin)) or "(keine Code-Aenderungen gegen den Ruecksetzpunkt)"
823|         weg_zeilen = []
824|         for d in sorted(weg):
825|             grund = {2: "Testcode", 3: "Testdaten"}.get(_vorrang(d, nur), "?")
826|             zusatz = " (nicht in der Uebergabe genannt)" if nur is None or d not in nur else ""
827|             weg_zeilen.append(f"- `{d}` – {grund}, Paket zu gross{zusatz}")
828|         teile = [
829|             f"# Review-Paket: {kurztitel}\n",
830|             f"Erzeugt {dt.datetime.now():%Y-%m-%d %H:%M} von `kette.py paket`. Ruecksetzpunkt: `{commit}`. "
831|             f"Geaenderte Code-Dateien: {', '.join(f'`{d}`' for d in sorted(drin)) or 'keine'}.\n"
832|             "Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – "
833|             "dann gezielt (search_files, Zeilenbereich), nicht komplett.\n",
834|             "## 1. Anforderung (verbindlich, woertlich)\n\n"
835|             + (anf_p.read_text(encoding="utf-8").strip() if anf_p else "(keine Anforderungsdatei – nur Spec als Massstab)"),
836|             f"## 2. Spec (Auszug aus `{spec_p.name}`)\n\n### Ziel\n{abschnitt(spec, 'Ziel').strip()}\n\n"
837|             f"### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)\n{abschnitt(spec, 'Nicht-Ziele').strip() or '(keine)'}\n\n"
838|             f"### Anforderungen\n{abschnitt(spec, 'Anforderungen').strip()}\n\n"
839|             f"### Testplan (nur Titel und Erwartungen)\n{_testplan_kurz(spec)}\n\n"
840|             f"### Offene Fragen\n{abschnitt(spec, 'Offene Fragen').strip() or '(keine)'}",
841|             f"## 3. Code-Aenderungen gegen `{commit}`\n\n{code}",
842|         ]
843|         if fremd_zeilen:
844|             teile.append("## 3a. Fremde Aenderungen (nur Liste)\n\nDiese Dateien wurden nur in Commits ohne den "
845|                          f"Kurztitel `{kurztitel}` geaendert. Sie gehoeren nicht zur Aufgabe – nicht bewerten.\n\n"
846|                          + "\n".join(fremd_zeilen))
847|         if weg_zeilen:
848|             teile.append("## 3b. Weggelassen (Paket zu gross)\n\nTeil der Kette, aber wegen der Paketgroesse "
849|                          "ohne Inhalt. Bei Bedarf gezielt nachlesen.\n\n" + "\n".join(weg_zeilen))
850|         skript = ROOT / "tests" / f"test_{kurztitel}.py"
851|         tc = _testcode(skript, _auffaellige_tests(pr_p.read_text(encoding="utf-8")) if pr_p else set())
852|         teile += [
853|             f"## 4. Testskript `tests/test_{kurztitel}.py` (Methoden)\n\n{_testliste(skript)}"
854|             + (f"\n\n### Code der auffaelligen Tests (GRUEN/ANDERS in der Pruefung)\n\n{tc}" if tc else ""),
855|             "## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte\n\n"
856|             + ((_bloecke(ho_p.read_text(encoding="utf-8"), r"abweich|annahm|offen|nicht getestet|schw[aä]chen")
857|                 or "(keine solchen Abschnitte)") if ho_p else "(kein Handover)"),
858|             f"## 6. Maschinelle Pruefung (Kurzfassung)\n\n{_pruefung_kurz(pr_p)}",
859|         ]
860|         return "\n\n".join(teile).rstrip() + "\n"
861| 
862|     # A7: Aenderungen ausserhalb docs/, aber nichts davon gehoert zur Kette -> lauter Fehler
863|     if not eintraege and fremd_zeilen:
864|         say(f"Paket ohne Code trotz Aenderungen seit {commit}: {len(fremd_zeilen)} Datei(en), davon "
865|             f"{len(fremd_zeilen)} fremd. Commits ohne Kurztitel '{kurztitel}' in der Nachricht? "
866|             "Dann Ruecksetzpunkt/Kurztitel pruefen. Exit 1, kein Paket.")
867|         return 1
868| 
869|     # A3: nach Gesamtgroesse kuerzen – erst Vorrang 3, dann 2; Vorrang 1 nie
870|     drin, weg = dict(eintraege), []
871|     text = bauen(drin, weg)
872|     for stufe in (3, 2):
873|         if len(text) <= PAKET_WARNUNG_ZEICHEN:
874|             break
875|         for d in sorted(x for x, (_, v) in drin.items() if v == stufe):
876|             weg.append(d); del drin[d]
877|             text = bauen(drin, weg)
878|             if len(text) <= PAKET_WARNUNG_ZEICHEN:
879|                 break
880| 
881|     # A7 (Fall b): Kette-Dateien vorhanden, aber nach der Kuerzung keine mit Inhalt
882|     if eintraege and not drin:
883|         say("Paket ohne Code trotz Aenderungen: alle Dateien der Kette mussten weggelassen werden. Exit 1, kein Paket.")
884|         return 1
885| 
886|     groesse = len(text)
887|     # A4: harte Obergrenze vor dem Schreiben
888|     if groesse > KETTE_PAKET_MAX:
889|         say(f"Paket passt nicht in den Kontext des Review-Modells, Review in Teilen noetig "
890|             f"({groesse} Zeichen > KETTE_PAKET_MAX {KETTE_PAKET_MAX}). Exit 1, kein Paket.")
891|         return 1
892|     ziel = PM / f"review_paket_{datum}_{kurztitel}.md"
893|     ziel.write_text(text, encoding="utf-8")
894|     say(f"Review-Paket: {ziel.relative_to(ROOT)}  ({groesse} Zeichen, ca. {groesse // 3500}k Token)"
895|         + (f", {len(weg)} Datei(en) weggelassen" if weg else "") + (f", {len(fremd_zeilen)} fremd" if fremd_zeilen else ""))
896|     if groesse > PAKET_WARNUNG_ZEICHEN:
897|         say(f"WARNUNG: Paket > {PAKET_WARNUNG_ZEICHEN} Zeichen (nur noch Vorrang 1) – fuer 64K Kontext eng.")
898|     if not pr_p:
899|         say("Hinweis: keine pruefung_*-Datei – erst `kette.py pruefen <kurztitel>` laufen lassen.")
900|     return 0
901| 
902| # ---------------------------------------------------------------- zusammenfuehren
```

### `role-split/kette/kette.py` def zusammenfuehren (Zeilen 920–1000) – Ziel `gesamt_…`, Tupel in `zeilen` (E3, E6)

```python
 920| def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
 921|     if len(pfade) < 2:
 922|         if _internal:
 923|             print("Nur ein Verdikt – Gesamtbefund wird mit Warnung geschrieben.")
 924|             # Gesamtbefund mit UNVOLLSTÄNDIG schreiben
 925|             p = pfade[0]
 926|             m = re.match(r"verdict_(\d{8})_(.+?)_[^_]+(?:_[^_]+)*\.md$", p.name)
 927|             datum = m.group(1) if m else dt.date.today().strftime("%Y%m%d")
 928|             kt = re.match(r"verdict_\d{8}_([a-z0-9_]+?)_(?:qwen|gemma|mellum|apertus|claude|hawe)", p.name)
 929|             kurz = kt.group(1) if kt else "review"
 930|             text = p.read_text(encoding="utf-8")
 931|             m2 = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis") or text)
 932|             ergebnis = m2.group(1) if m2 else "?"
 933|             teile = [f"# Gesamtbefund: {kurz}\n",
 934|                      f"Mechanisch zusammengeführt mit `kette.py zusammenfuehren` ({dt.datetime.now():%Y-%m-%d %H:%M}). Kein Befund wurde weggelassen oder umformuliert.\n",
 935|                       "## Ergebnis\n", f"**UNVOLLSTÄNDIG** – Nur ein Lauf mit auswertbarer Befund-Tabelle.\n",
 936|                      "| Lauf | Ergebnis des Laufs |", "|---|---|",
 937|                       f"| `{p.name}` | {ergebnis.replace('PASS', 'UNVOLLSTÄNDIG')} |",
 938|                      "",
 939|                      "> Ein weiterer Lauf fehlt. Der Gesamtbefund beruht auf nur einem Lauf mit auswertbarer Tabelle.\n"]
 940|             ziel = PM / f"gesamt_{datum}_{kurz}.md"
 941|             ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
 942|             print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
 943|             return 1
 944|         print("Mindestens zwei Verdikte angeben."); return 2
 945|     zeilen, ergebnisse, fehlt = [], [], []
 946|     for p in pfade:
 947|         if not p.is_file():
 948|             fehlt.append(str(p)); continue
 949|         text = p.read_text(encoding="utf-8")
 950|         m = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis") or text)
 951|         ergebnisse.append((p.name, m.group(1) if m else "?"))
 952|         befunde = _befunde(text)
 953|         if not befunde:
 954|             zeilen.append((p.name, "?", "(keine Befundtabelle erkannt – Verdikt von Hand lesen)", "", False))
 955|         for b in befunde:
 956|             schwere = spalte(b, "schwere") or "?"
 957|             text_b = spalte(b, "befund", "begründung", "begruendung") or " | ".join(v for v in b.values() if v)
 958|             ort = spalte(b, "datei", "zeile", "anfor") or ""
 959|             h = _ist_hoch(b)
 960|             z = _zurueckgezogen(text_b)
 961|             zeilen.append((p.name, schwere, text_b, ort, h, z))
 962|     if fehlt:
 963|         print("Fehlt: " + ", ".join(fehlt)); return 2
 964|     hoch = [z for z in zeilen if z[4] and not z[5]]
 965|     if hoch or any(e == "NACHBESSERN" for _, e in ergebnisse):
 966|         urteil_ = "NACHBESSERN"
 967|     elif any(e == "FAIL" for _, e in ergebnisse):
 968|         urteil_ = "FAIL"
 969|     elif all(e == "PASS" for _, e in ergebnisse):
 970|         urteil_ = "PASS"
 971|     else:
 972|         urteil_ = "UNKLAR"
 973|     if any(e == "FAIL" for _, e in ergebnisse):
 974|         urteil_ = "FAIL"
 975|     m = re.match(r"verdict_(\d{8})_(.+?)_[^_]+(?:_[^_]+)*\.md$", pfade[0].name)
 976|     datum = m.group(1) if m else dt.date.today().strftime("%Y%m%d")
 977|     kt = re.match(r"verdict_\d{8}_([a-z0-9_]+?)_(?:qwen|gemma|mellum|apertus|claude|hawe)", pfade[0].name)
 978|     kurz = kt.group(1) if kt else "review"
 979|     teile = [f"# Gesamtbefund: {kurz}\n",
 980|              f"Mechanisch zusammengeführt mit `kette.py zusammenfuehren` ({dt.datetime.now():%Y-%m-%d %H:%M}). Kein Befund wurde weggelassen oder umformuliert.\n",
 981|              "## Ergebnis\n", f"**{urteil_}** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.\n",
 982|              "| Lauf | Ergebnis des Laufs |", "|---|---|"] + [f"| `{n}` | {e} |" for n, e in ergebnisse] + [
 983|              "", "## Befunde (alle Läufe)\n", "| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |", "|---|---|---|---|---|"]
 984|     for n, s_, t, o, h, z in zeilen:
 985|         if h and z:
 986|             hoch_zeig = "nein (zurückgezogen)"
 987|         elif h:
 988|             hoch_zeig = "ja"
 989|         else:
 990|             hoch_zeig = "nein"
 991|         teile.append(f"| `{n}` | {s_} | {hoch_zeig} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
 992|     ziel = PM / f"gesamt_{datum}_{kurz}.md"
 993|     ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
 994|     zurueckgezogen = len([z for z in zeilen if z[5]])
 995|     zeile_zur = f", {zurueckgezogen} zurückgezogen" if zurueckgezogen else ""
 996|     print(f"{len(zeilen)} Befunde aus {len(ergebnisse)} Läufen, davon {len(hoch)} hoch{zeile_zur} -> {urteil_}")
 997|     print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
 998|     return 0 if urteil_ == "PASS" else 1
 999| 
1000| # ---------------------------------------------------------------- anforderung
```

### `role-split/kette/kette.py` def anforderung (Zeilen 1014–1044) – Ziel `anforderung_…` (E3)

```python
1014| def anforderung(kurztitel: str, aufgabe: str | None, antwort: str | None, frage: str | None,
1015|                 datum: str | None) -> int:
1016|     vorhanden = datei_suchen("anforderung", kurztitel, datum)
1017|     zitat = lambda t: "\n".join("> " + z if z else ">" for z in t.strip().splitlines())
1018|     if aufgabe:
1019|         if vorhanden:
1020|             print(f"Gibt es schon: {vorhanden} (nichts ueberschrieben; Antworten mit --antwort anhaengen)")
1021|             return 2
1022|         d = datum or dt.date.today().strftime("%Y%m%d")
1023|         ziel = PM / f"anforderung_{d}_{kurztitel}.md"
1024|         PM.mkdir(parents=True, exist_ok=True)
1025|         ziel.write_text(
1026|             f"# Anforderung: {kurztitel}\n\n"
1027|             "Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;\n"
1028|             "die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.\n\n"
1029|             f"## Aufgabe\n\n{zitat(aufgabe)}\n\n## Antworten auf Rueckfragen\n\n", encoding="utf-8")
1030|         print(f"Angelegt: {ziel}")
1031|         return 0
1032|     if antwort:
1033|         if not vorhanden:
1034|             print(f"Keine anforderung_*_{kurztitel}.md – erst mit --aufgabe anlegen"); return 2
1035|         stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
1036|         teil = f"**{stamp}**" + (f" — Frage: {frage.strip()}" if frage else "") + f"\n\n{zitat(antwort)}\n\n"
1037|         with vorhanden.open("a", encoding="utf-8") as f:
1038|             f.write(teil)
1039|         print(f"Angehaengt an {vorhanden.name}")
1040|         return 0
1041|     print("--aufgabe oder --antwort angeben"); return 2
1042| 
1043| 
1044| # ---------------------------------------------------------------- quellen
```

### `role-split/kette/kette.py` def quellen (Zeilen 1160–1245) – Ziel der Quellen-Datei (E3)

```python
1160| def quellen(kurztitel: str, datum: str | None = None) -> int:
1161|     spec = datei_suchen("spec", kurztitel, datum)
1162|     if not spec:
1163|         print(f"Keine spec_*_{kurztitel}.md"); return 2
1164|     block = abschnitt(spec.read_text(encoding="utf-8"), "Quellen")
1165|     eintraege, unerkannt = [], []
1166|     for z in block.splitlines():
1167|         q = quelle_lesen(z)
1168|         if q:
1169|             eintraege.append(q)
1170|         elif re.match(r"^\s*[-*]\s*`[^`]+/[^`]*`", z):  # sieht nach Fundstelle aus, Form aber unklar
1171|             unerkannt.append(z.strip())
1172|     if not eintraege:
1173|         print(f"{spec.name}: Abschnitt '## Quellen' fehlt oder hat keine Zeile der Form - `pfad` …"); return 2
1174|     d = _datum_aus(spec)
1175|     try:
1176|         stand = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
1177|                                capture_output=True, text=True, check=True).stdout.strip()
1178|     except Exception:
1179|         stand = "?"
1180|     teile = [f"# Quellen: {kurztitel}\n",
1181|              f"Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen {kurztitel}` "
1182|              f"({dt.datetime.now():%Y-%m-%d %H:%M}, Stand `{stand}`), nach dem Abschnitt „Quellen“ in `{spec.name}`.",
1183|              "Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. "
1184|              "Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.\n"]
1185|     fehler = 0
1186|     for q in eintraege:
1187|         pfad, von, bis, art, name, text, zweck = (q[k] for k in ("pfad", "von", "bis", "art", "name", "text", "zweck"))
1188|         ziel = (ROOT / pfad).resolve()
1189|         titel = f"`{pfad}`"
1190|         try:
1191|             ziel.relative_to(ROOT.resolve())
1192|         except ValueError:
1193|             teile.append(f"### {titel}\n\n**VERWEIGERT:** liegt ausserhalb des Repos.\n"); fehler += 1; continue
1194|         if not ziel.is_file():
1195|             teile.append(f"### {titel}\n\n**FEHLT:** Datei nicht gefunden.\n"); fehler += 1; continue
1196|         zeilen = ziel.read_text(encoding="utf-8", errors="replace").splitlines()
1197|         hinweis = ""
1198|         if art:
1199|             bereich = _block(zeilen, art, name) if "." not in name else _block_name(zeilen, name)[0]
1200|             if not bereich:
1201|                 teile.append(f"### {titel} {art} {name}\n\n**FEHLT:** `{art} {name}` nicht gefunden.\n"); fehler += 1; continue
1202|             a, b = bereich; titel += f" {art} {name}"
1203|         elif name:
1204|             bereich, was = _block_name(zeilen, name) if ziel.suffix == ".py" else (None, name)
1205|             if not bereich:
1206|                 bereich = _textstelle(zeilen, name); was = f"Textstelle „{name}“"
1207|             if not bereich:
1208|                 teile.append(f"### {titel} {name}\n\n**FEHLT:** `{name}` nicht gefunden.\n"); fehler += 1; continue
1209|             a, b = bereich; titel += f" {was}"
1210|         elif text:
1211|             bereich = _textstelle(zeilen, text, 25)
1212|             if not bereich:
1213|                 teile.append(f"### {titel} „{text}“\n\n**FEHLT:** Textstelle nicht gefunden.\n"); fehler += 1; continue
1214|             a, b = bereich; titel += f" Textstelle „{text}“"
1215|         elif von:
1216|             a = max(1, int(von)); b = min(len(zeilen), int(bis or von))
1217|             fehlen = _passt(zeilen[a - 1:b], zweck)
1218|             if fehlen:
1219|                 hinweis = (f"\n**PRÜFEN:** Keiner der im Zweck genannten Namen ({', '.join(fehlen)}) steht in diesen Zeilen – "
1220|                            f"Zeilenangabe vermutlich aus dem Gedächtnis. Besser `def`/`class`/Name angeben.\n")
1221|                 fehler += 1
1222|         else:
1223|             a, b = 1, len(zeilen)
1224|         if b - a + 1 > QUELLE_MAX:
1225|             teile.append(f"### {titel}\n\n**ZU LANG:** {b - a + 1} Zeilen (max. {QUELLE_MAX}) – Zeilen oder def/class angeben.\n")
1226|             fehler += 1; continue
1227|         breite = len(str(b))
1228|         code = "\n".join(f"{n:>{breite}}| {zeilen[n - 1]}" for n in range(a, b + 1))
1229|         teile.append(f"### {titel} (Zeilen {a}–{b})" + (f" – {zweck.strip()}" if zweck else "") + hinweis +
1230|                      f"\n\n```{SPRACHE.get(ziel.suffix, '')}\n{code}\n```\n")
1231|     for z in unerkannt:
1232|         teile.append(f"### Nicht erkannt\n\n**UNKLAR:** `{z[:200]}` – Form: `pfad` Zeilen a–b | def Name | class Name | `Name` | Abschnitt „…“\n")
1233|         fehler += 1
1234|     ziel_datei = PM / f"quellen_{d}_{kurztitel}.md"
1235|     ziel_datei.write_text("\n".join(teile), encoding="utf-8")
1236|     print(f"{len(eintraege)} Quellen -> {ziel_datei}" + (f"   {fehler} mit FEHLT/VERWEIGERT/ZU LANG/UNKLAR/PRÜFEN" if fehler else ""))
1237|     for t in teile:
1238|         if "**PRÜFEN:**" in t or "**FEHLT:**" in t:
1239|             print("  " + t.splitlines()[0].lstrip("# ") + "  -> " + ("PRÜFEN" if "PRÜFEN" in t else "FEHLT"))
1240|     for z in unerkannt:
1241|         print(f"  UNKLAR (nicht geholt): {z[:120]}")
1242|     return 1 if fehler else 0
1243| 
1244| 
1245| # ---------------------------------------------------------------- prompt
```

### `role-split/kette/kette.py` def prompt (Zeilen 1247–1301) – Pfade im Prompt (E4)

```python
1247| def prompt(schritt: str, kurztitel: str, datum: str | None, commit: str | None, lauf: int | None = None) -> int:
1248|     vorlage = PROMPTS / f"{schritt}.md"
1249|     if not vorlage.is_file():
1250|         print(f"Keine Vorlage: {vorlage}"); return 2
1251|     anf = datei_suchen("anforderung", kurztitel, datum)
1252|     if not datum:
1253|         # Datum der vorhandenen Spec (Kette 4: "heute" passte nicht mehr am Folgetag)
1254|         datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or _datum_aus(anf) \
1255|             or dt.date.today().strftime("%Y%m%d")
1256|         anf = anf or datei_suchen("anforderung", kurztitel, datum)
1257|     if not commit and schritt != "spec":
1258|         commit = spec_commit(kurztitel)          # Ruecksetzpunkt = Commit "Spec <kurztitel>" (22.10.)
1259|         if commit:
1260|             print(f"Ruecksetzpunkt = Commit 'Spec {kurztitel}' ({commit}).", file=sys.stderr)
1261|     if not commit:
1262|         try:
1263|             commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
1264|                                     capture_output=True, text=True, check=True).stdout.strip()
1265|         except Exception:
1266|             commit = "<HASH>"
1267|         if schritt != "spec":
1268|             print(f"Hinweis: Ruecksetzpunkt = HEAD von {ROOT} ({commit}). Stimmt das (Worktree?)? "
1269|                   "Sonst --commit angeben.", file=sys.stderr)
1270|     paket_pfad = f"docs/projekt_management/review_paket_{datum}_{kurztitel}.md"
1271|     if schritt in ("review", "review2", "tief"):
1272|         if paket(kurztitel, commit if commit != "<HASH>" else None, None, still=False) != 0:
1273|             print("Hinweis: Review-Paket nicht gebaut (siehe oben) – Prompt verweist trotzdem darauf.",
1274|                   file=sys.stderr)
1275|     anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
1276|         f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
1277|     if not anf:
1278|         print(f"Hinweis: {anf_pfad} fehlt. Anlegen mit: kette.py anforderung {kurztitel} --aufgabe \"…\"",
1279|               file=sys.stderr)
1280|     text = (vorlage.read_text(encoding="utf-8")
1281|             .replace("{kurztitel}", kurztitel)
1282|             .replace("{datum}", datum)
1283|             .replace("{commit}", commit)
1284|             .replace("{anforderung}", anf_pfad)
1285|             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md")
1286|             .replace("{paket}", paket_pfad))
1287|     if anf:
1288|         text = re.sub(r"<AUFGABE[^>]*>", lambda _m: aufgabe_lesen(anf), text)
1289|     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
1290|     if lauf:
1291|         # Eigener Dateiname je Review-Lauf: sonst findet Lauf 2 das Verdikt von Lauf 1 (geschuetzt),
1292|         # liest es und haengt an (Probe K4, 22.10.) -> Laeufe nicht mehr unabhaengig.
1293|         text = text.replace("_<modellkürzel>.md", f"_<modellkürzel>_lauf{lauf}.md")
1294|         text += "Verdikte anderer Läufe liest du nicht.\n"
1295|     print(text)
1296|     if shutil.which("pbcopy"):
1297|         subprocess.run(["pbcopy"], input=text, text=True)
1298|         print("(in die Zwischenablage kopiert)", file=sys.stderr)
1299|     return 0
1300| 
1301| # ---------------------------------------------------------------- review-auto
```

### `role-split/kette/kette.py` def _freier_verdiktpfad (Zeilen 1403–1417) – Verdikt-Pfad (E3)

```python
1403| def _freier_verdiktpfad(datum: str, kurztitel: str, lauf: int) -> Path:
1404|     """Exklusiver Verdikt-Pfad mit automatischem Zähler (_2, _3 …)."""
1405|     modellkuerzel = "qwen36-35b"
1406|     basis = f"verdict_{datum}_{kurztitel}_{modellkuerzel}"
1407|     if lauf == 2:
1408|         basis += "_betrieb"
1409|     zaehler = 1
1410|     while True:
1411|         if zaehler > 1:
1412|             pfad = PM / f"{basis}_{zaehler}.md"
1413|         else:
1414|             pfad = PM / f"{basis}.md"
1415|         if not pfad.exists():
1416|             return pfad
1417|         zaehler += 1
```

### `role-split/kette/kette.py` def review_auto (Zeilen 1435–1575) – Paket-, Verdikt- und Gesamt-Pfade (E3)

```python
1435| def review_auto(kurztitel: str) -> int:
1436|     """Review-Paket bauen, zwei API-Laeufe, Verdikte speichern, zusammenfuehren."""
1437|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
1438|         print(f"Kurztitel '{kurztitel}' ungueltig (nur a-z, 0-9, _)."); return 2
1439| 
1440|     # A2: Pruefung, Abbruch bei roten Unit-Tests
1441|     teile_dict = _pruefen_teile(kurztitel)
1442|     unit_code = teile_dict["unittest"][0]
1443|     if unit_code != 0:
1444|         if unit_code == 2:
1445|             print(f"Pruefung-Fehler (Exit 2) – Review nicht moeglich."); return 2
1446|         print("Unit-Tests rot – direkt nachbessern, kein Review nötig"); return 1
1447| 
1448|     # A3: Review-Paket bauen
1449|     if paket(kurztitel) != 0:
1450|         print("Review-Paket nicht gebaut – Voraussetzung fehlt (Exit 2)."); return 2
1451|     paket_pfad = PM / f"review_paket_{_datum_aus(datei_suchen('spec', kurztitel, None)) or dt.date.today().strftime('%Y%m%d')}_{kurztitel}.md"
1452|     paket_text = paket_pfad.read_text(encoding="utf-8") if paket_pfad.exists() else ""
1453| 
1454|     datum = _datum_aus(datei_suchen("spec", kurztitel, None)) or dt.date.today().strftime("%Y%m%d")
1455| 
1456|     # A1: Prompt-Dateien laden, {paket_text} ersetzen
1457|     prompt1 = (PROMPTS / "review_api.md").read_text(encoding="utf-8").replace("{paket_text}", paket_text).replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", "").replace("{datum_heute}", dt.datetime.now().strftime("%Y-%m-%d")).replace("{modell}", KETTE_LLM_MODEL)
1458|     prompt2 = (PROMPTS / "review2_api.md").read_text(encoding="utf-8").replace("{paket_text}", paket_text).replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", "").replace("{datum_heute}", dt.datetime.now().strftime("%Y-%m-%d")).replace("{modell}", KETTE_LLM_MODEL)
1459| 
1460|     verdikt1 = verdikt2 = None
1461|     info1 = info2 = {}
1462|     pfad1 = pfad2 = None
1463| 
1464|     # Lauf 1
1465|     print(f"Lauf 1 von 2 (Anforderung) gestartet")
1466|     stop1, thread1 = _herzschlag_stopp_event(1)
1467|     start1 = dt.datetime.now()
1468|     try:
1469|         verdikt1, info1 = _api_ruf(prompt1, 1)
1470|     except Exception:
1471|         print("Lauf 1 gescheitert – Exit 1, kein Lauf 2."); stop1.set(); thread1.join(timeout=2); return 1
1472|     stop1.set()
1473|     thread1.join(timeout=2)
1474|     elapsed1 = int((dt.datetime.now() - start1).total_seconds())
1475|     if not verdikt1:
1476|         print("Lauf 1: keine Antwort vom Server – Exit 1, kein Lauf 2."); return 1
1477|     print(f"Lauf 1 fertig ({elapsed1}s, {info1.get('prompt_tokens', '?')} prompt, "
1478|           f"{info1.get('completion_tokens', '?')} completion tokens)")
1479|     try:
1480|         pfad1 = _freier_verdiktpfad(datum, kurztitel, 1)
1481|         with open(pfad1, "x", encoding="utf-8") as f:
1482|             f.write(verdikt1)
1483|         print(f"Verdikt 1 gespeichert: {_rel(pfad1)}")
1484|     except FileExistsError:
1485|         zaehler = 2
1486|         while True:
1487|             pfad1 = PM / f"verdict_{datum}_{kurztitel}_qwen36-35b_{zaehler}.md"
1488|             if not pfad1.exists():
1489|                 with open(pfad1, "x", encoding="utf-8") as f:
1490|                     f.write(verdikt1)
1491|                 print(f"Verdikt 1 gespeichert: {_rel(pfad1)} (Zaehler {zaehler})")
1492|                 break
1493|             zaehler += 1
1494| 
1495|     # Lauf 2
1496|     print(f"Lauf 2 von 2 (Betrieb) gestartet")
1497|     stop2, thread2 = _herzschlag_stopp_event(2)
1498|     start2 = dt.datetime.now()
1499|     try:
1500|         verdikt2, info2 = _api_ruf(prompt2, 2)
1501|     except Exception:
1502|         print("Lauf 2 gescheitert – Exit 1."); stop2.set(); thread2.join(timeout=2); return 1
1503|     stop2.set()
1504|     thread2.join(timeout=2)
1505|     elapsed2 = int((dt.datetime.now() - start2).total_seconds())
1506|     if not verdikt2:
1507|         print("Lauf 2: keine Antwort vom Server – Exit 1."); return 1
1508|     print(f"Lauf 2 fertig ({elapsed2}s, {info2.get('prompt_tokens', '?')} prompt, "
1509|           f"{info2.get('completion_tokens', '?')} completion tokens)")
1510|     try:
1511|         pfad2 = _freier_verdiktpfad(datum, kurztitel, 2)
1512|         with open(pfad2, "x", encoding="utf-8") as f:
1513|             f.write(verdikt2)
1514|         print(f"Verdikt 2 gespeichert: {_rel(pfad2)}")
1515|     except FileExistsError:
1516|         zaehler = 2
1517|         while True:
1518|             pfad2 = PM / f"verdict_{datum}_{kurztitel}_qwen36-35b_betrieb_{zaehler}.md"
1519|             if not pfad2.exists():
1520|                 with open(pfad2, "x", encoding="utf-8") as f:
1521|                     f.write(verdikt2)
1522|                 print(f"Verdikt 2 gespeichert: {_rel(pfad2)} (Zaehler {zaehler})")
1523|                 break
1524|             zaehler += 1
1525| 
1526|     # A6: Auswertbare Befund-Tabelle
1527|     auswertbar1 = verdikt1 and _ist_auswertbar(verdikt1)
1528|     auswertbar2 = verdikt2 and _ist_auswertbar(verdikt2)
1529| 
1530|     unvollstaendig = not auswertbar1 or not auswertbar2
1531|     fehlende_datei = []
1532|     if not auswertbar1 and pfad1:
1533|         fehlende_datei.append(pfad1.name)
1534|     if not auswertbar2 and pfad2:
1535|         fehlende_datei.append(pfad2.name)
1536| 
1537|     # A7: Zusammenführen (intern, auch mit 1 oder 0 gültigen Pfaenden)
1538|     gueltige_pfade = [p for p, aw in [(pfad1, auswertbar1), (pfad2, auswertbar2)]
1539|                       if p and aw]
1540|     gesamt_exit = zusammenfuehren(gueltige_pfade, _internal=True)
1541| 
1542|     # UNVOLLSTÄNDIG: bei fehlender Tabelle immer 1, Gesamtbefund anpassen
1543|     if unvollstaendig:
1544|         gesamt_pfad = PM / f"gesamt_{datum}_{kurztitel}.md"
1545|         if gesamt_pfad.exists():
1546|             text = gesamt_pfad.read_text(encoding="utf-8")
1547|             text = text.replace("**PASS**", "**UNVOLLSTÄNDIG**")
1548|             warnhinweis = (f"Ein Lauf ohne auswertbare Befund-Tabelle: {', '.join(fehlende_datei)} "
1549|                            f"– Gesamtbefund beruht nur auf {len(gueltige_pfade)} Lauf/Läufen")
1550|             text = text.replace(f"# Gesamtbefund: {kurztitel}\n",
1551|                                 f"# Gesamtbefund: {kurztitel}\n\n> {warnhinweis}\n")
1552|             gesamt_pfad.write_text(text, encoding="utf-8")
1553|         gesamt_exit = 1
1554|         print(f"==> UNVOLLSTÄNDIG: Befund-Tabelle fehlt in {', '.join(fehlende_datei)}")
1555| 
1556|     # Zusammenfassung
1557|     gesamt_pfad = PM / f"gesamt_{datum}_{kurztitel}.md"
1558|     print(f"\n=== Zusammenfassung ===")
1559|     if unvollstaendig:
1560|         print("Ergebnis: UNVOLLSTÄNDIG")
1561|     else:
1562|         print(f"Ergebnis: {'PASS' if gesamt_exit == 0 else 'NACHBESSERN'}")
1563|     print(f"Verdikt 1: {_rel(pfad1) if pfad1 else 'keine'}")
1564|     print(f"Verdikt 2: {_rel(pfad2) if pfad2 else 'keine'}")
1565|     print(f"Gesamt: {_rel(gesamt_pfad) if gesamt_pfad.exists() else 'keine'}")
1566| 
1567|     return gesamt_exit
1568| 
1569| 
1570| # ---------------------------------------------------------------- umsetzung-auto (K10)
1571| #
1572| # Startet die Umsetzung ohne TUI ueber `opencode run --format json` (Agent umsetzung_nacht) und
1573| # prueft danach mechanisch. Gemessen an opencode 1.19.3 (Spec-Paket §1): Exit-Code ist immer 0,
1574| # Erfolg steht nur im JSON; `ask` wird ohne TUI sofort abgelehnt; OPENCODE_PERMISSION kann
1575| # Agent-Regeln nicht ueberstimmen -> Sperren stehen in der Agent-Datei, Schreibgrenze prueft kette.py.
```

### `role-split/kette/kette.py` def _ist_kettendatei (Zeilen 1610–1616) – Ordnerprüfung (E5)

```python
1610| def _ist_kettendatei(pfad: str, kurztitel: str) -> bool:
1611|     """Von der Kette erzeugte Datei dieses Kurztitels in docs/projekt_management/ (ohne Vorgaben)."""
1612|     p = Path(pfad)
1613|     if p.parent.as_posix() != "docs/projekt_management":
1614|         return False
1615|     muster = rf"^(?:{'|'.join(KETTEN_PRAEFIXE)})_\d{{8}}_{re.escape(kurztitel)}(?:_[\w.-]+)?\.md$"
1616|     return re.match(muster, p.name) is not None
```

### `role-split/kette/kette.py` def _umsetzung_prompt (Zeilen 1739–1772) – Pfade im Umsetzer-Prompt (E4)

```python
1739| def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path | None, nb: int) -> str | None:
1740|     vorlage = PROMPTS / "umsetzung_nacht.md"
1741|     if not vorlage.is_file():
1742|         return None
1743|     anf = datei_suchen("anforderung", kurztitel, None)
1744|     anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
1745|         f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
1746|     text = (vorlage.read_text(encoding="utf-8")
1747|             .replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", commit)
1748|             .replace("{anforderung}", anf_pfad)
1749|             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md"))
1750|     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
1751|     # A1: Pflichtzeilen im Handover – nach Grundtext, vor Nachbesserung
1752|     spec_p = datei_suchen("spec", kurztitel, None)
1753|     if spec_p:
1754|         spec_tests = tests_finden(spec_p.read_text(encoding="utf-8"))
1755|         if spec_tests:
1756|             zeilen = ["", "## Pflichtzeilen im Handover",
1757|                       'Unter „## Getestet" steht für jede Test-ID genau eine dieser Zeilen (Titel unverändert, Status wählen):']
1758|             for tid, titel in spec_tests.items():
1759|                 zeilen.append(f"**{tid}: {titel}** – bestanden | fehlgeschlagen")
1760|             zeilen.append('Unter „## Nicht getestet" nur Test-IDs, die wirklich nicht getestet sind – keine Sammelangaben wie „T1–T5".')
1761|             text += "\n".join(zeilen) + "\n"
1762|     if spec_p and _vorgabe_tests(spec_p.read_text(encoding="utf-8")):
1763|         text += ("\n## Vorgabe-Tests\n\nAbweichend von den Testregeln oben: Die Tests stehen schon in "
1764|                  f"tests/test_{kurztitel}.py. Du änderst diese Datei nicht – keine Zeile. Schreib nur den Code, "
1765|                  f"bis python3 -m unittest -v tests/test_{kurztitel}.py grün ist. Passt ein Test nicht zur Spec, "
1766|                  "nenne ihn im Handover unter „Abweichungen“.\n")
1767|     if nacharbeit:
1768|         text += (f"\n## Nachbesserung {nb}\n\nDas ist Nachbesserung {nb}. Der Auftrag steht unten (aus "
1769|                  f"`{_rel(nacharbeit)}`). Ergänze den Handover docs/projekt_management/handover_{datum}_"
1770|                  f"{kurztitel}.md um den Abschnitt „## Nachbesserung {nb}\" – nichts Bestehendes löschen.\n\n"
1771|                  + nacharbeit.read_text(encoding="utf-8").strip() + "\n")
1772|     return text
```

### `role-split/kette/kette.py` def umsetzung_auto (Zeilen 1868–2051) – `handover_rel`, `protokoll_p` (E3)

```python
1868| def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
1869|     """K10: Umsetzung bzw. Nacharbeit ueber `opencode run` ohne TUI, danach mechanisch pruefen.
1870|     Exit 0 = abgeschlossen + keine Verletzung + pruefen 0; 1 = Lauf/Pruefung nicht in Ordnung; 2 = Voraussetzung."""
1871|     def nein(meldung: str, code: int = 2) -> int:
1872|         print(meldung, file=sys.stderr)
1873|         return code
1874| 
1875|     # A2.1 Kurztitel
1876|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
1877|         return nein(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).")
1878|     # A2.2 Spec-Commit
1879|     commit = spec_commit(kurztitel)
1880|     if not commit:
1881|         return nein(f"Kein Commit 'Spec {kurztitel}' gefunden – erst die Spec committen.")
1882|     # A2.3 Spec mit Schreibbereich
1883|     spec_p = datei_suchen("spec", kurztitel, None)
1884|     if not spec_p:
1885|         return nein(f"Keine Spec spec_<datum>_{kurztitel}.md in {_rel(PM)}.")
1886|     bereich = _schreibbereich(spec_p.read_text(encoding="utf-8"))
1887|     if bereich is None:
1888|         return nein(f"Spec {spec_p.name} hat keinen Abschnitt '## Schreibbereich'. Spec um '## Schreibbereich' "
1889|                     "ergaenzen (Dateien/Ordner, die die Umsetzung aendern darf), sonst kein umsetzung-auto-Lauf.")
1890|     if not bereich:
1891|         return nein(f"'## Schreibbereich' in {spec_p.name} ist leer – mindestens einen Pfad eintragen.")
1892|     for e in bereich:
1893|         if _ist_vorgabe(e):
1894|             print(f"Hinweis: Schreibbereich nennt {e} – Vorgaben (spec_/anforderung_/quellen_/_vorlage_) "
1895|                   "sind nie erlaubt; eine Änderung daran endet in (b) mit Exit 1.", file=sys.stderr)
1896|     datum = _datum_aus(spec_p) or dt.date.today().strftime("%Y%m%d")
1897|     testdatei = f"tests/test_{kurztitel}.py"
1898|     handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
1899|     protokoll_p = PM / f"umsetzung_{datum}_{kurztitel}.md"
1900|     nach_p = None
1901|     if nacharbeit:
1902|         nach_p = Path(nacharbeit)
1903|         if not nach_p.is_absolute():
1904|             nach_p = (ROOT / nach_p) if (ROOT / nach_p).is_file() else nach_p.resolve()
1905|         if not nach_p.is_file():
1906|             return nein(f"Nacharbeitsdatei {nacharbeit} nicht gefunden.")
1907|     # A2.4 Arbeitsstand
1908|     offen = _offene_dateien()
1909|     if offen is None:
1910|         return nein("git status fehlgeschlagen – ist ROOT ein Git-Repo?")
1911|     if not nach_p:
1912|         if offen:
1913|             return nein("Arbeitsstand nicht sauber – ohne --nacharbeit muss alles committet sein:\n"
1914|                         + "\n".join(f"  {d}" for d in offen))
1915|     else:
1916|         try:
1917|             nach_rel = nach_p.resolve().relative_to(ROOT.resolve()).as_posix()
1918|         except ValueError:
1919|             nach_rel = None
1920|         fremd = [d for d in offen
1921|                  if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d == testdatei or d == handover_rel
1922|                                              or _ist_kettendatei(d, kurztitel) or d == nach_rel)]
1923|         if fremd:
1924|             return nein("Nacharbeit: unzulaessige offene Aenderungen (Vorgaben oder ausserhalb von Schreibbereich/"
1925|                         "Testdatei/Kettendateien):\n" + "\n".join(f"  {d}" for d in fremd))
1926|     # K11a: Vorgabe-Tests
1927|     vorgabe = _vorgabe_tests(spec_p.read_text(encoding="utf-8"))
1928|     if vorgabe:
1929|         if not (ROOT / testdatei).is_file():
1930|             return nein(f"Spec nennt '## Vorgabe-Tests', aber {testdatei} fehlt.")
1931|         if nach_p and testdatei in offen:
1932|             return nein(f"Nacharbeit: Vorgabe-Tests {testdatei} haben offene Aenderungen. Auf die Vorgabe zuruecksetzen (git restore {testdatei}) oder eine bewusste Korrektur committen – kein Lauf.")
1933|         if not nach_p and tests_pruefen(kurztitel) != 0:
1934|             return nein(f"Vorgabe-Tests nicht in Ordnung (kette.py tests-pruefen {kurztitel}) – kein Lauf.")
1935|     # A2.5 opencode
1936|     programm = _opencode_programm()
1937|     if not programm:
1938|         ziel = os.environ.get("KETTE_OPENCODE") or "opencode im PATH"
1939|         return nein(f"opencode nicht gefunden ({ziel}).")
1940|     # A2.6 Modell
1941|     modell = os.environ.get("KETTE_UMSETZUNG_MODEL", UMSETZUNG_MODELL_STANDARD)
1942|     if not modell.startswith("llamacpp/"):
1943|         return nein(f"Modell '{modell}' beginnt nicht mit 'llamacpp/' (nur direkt am Router, ohne Gedaechtnis).")
1944|     # A8 Halt-Regel und Nummer
1945|     zeilen = _protokoll(protokoll_p)
1946|     handover_p = ROOT / handover_rel
1947|     handover_alt = handover_p.read_text(encoding="utf-8") if handover_p.is_file() else ""
1948|     nb = len(re.findall(r"^## Nachbesserung\b", handover_alt, re.M)) + 1
1949|     if nach_p and _halt_noetig(zeilen):
1950|         return nein("Zwei Nachbesserungen in Folge ohne Fortschritt – keine weitere. Übergabe an Hawe.", 1)
1951|     art = f"nb{nb}" if nach_p else "erst"
1952|     # A3 Prompt
1953|     prompt_text = _umsetzung_prompt(kurztitel, datum, commit, nach_p, nb)
1954|     if prompt_text is None:
1955|         return nein(f"Prompt-Vorlage {_rel(PROMPTS / 'umsetzung_nacht.md')} fehlt.")
1956|     try:
1957|         timeout = int(os.environ.get("KETTE_UMSETZUNG_TIMEOUT", UMSETZUNG_TIMEOUT_STANDARD))
1958|         bash_ms = int(os.environ.get("OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS", UMSETZUNG_BASH_MS_STANDARD))
1959|     except ValueError:
1960|         return nein("KETTE_UMSETZUNG_TIMEOUT / OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS muessen ganze Zahlen sein.")
1961| 
1962|     # A7 Schnappschuss VOR dem Start
1963|     head_vor = _git("rev-parse", "HEAD").strip()
1964|     stand_vor = _stand()
1965|     if stand_vor is None:
1966|         return nein("git status fehlgeschlagen.")
1967|     befehl = programm + ["run", "--format", "json", "--agent", UMSETZUNG_AGENT, "--model", modell,
1968|                          "--dir", str(ROOT), "--title", f"kette {kurztitel} {art}", prompt_text]
1969|     env = dict(os.environ, OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=str(bash_ms))
1970|     rohdaten = ROOT / "role-split" / "results" / f"umsetzung_auto_{datum}_{kurztitel}_{dt.datetime.now():%H%M%S}.jsonl"
1971|     print(f"umsetzung-auto {kurztitel} ({art}): Modell {modell}, Agent {UMSETZUNG_AGENT}, "
1972|           f"Zeitlimit {timeout} s, Rücksetzpunkt {commit}", flush=True)
1973|     info = _lauf(befehl, env, timeout, rohdaten)
1974| 
1975|     # A7 Schnappschuss SOFORT nach dem Lauf, bevor kette.py selbst etwas schreibt
1976|     stand_nach = _stand() or {}
1977|     head_nach = _git("rev-parse", "HEAD").strip()
1978|     aenderungen = _in_diesem_lauf(stand_vor, stand_nach)
1979|     abgeschlossen = not info["timeout"] and info["reason"] == "stop"
1980|     befunde = []
1981| 
1982|     if info.get("haengt"):
1983|         befunde.append("opencode reagiert 30 s nach SIGKILL nicht – Prozess pruefen (ps).")
1984|     if info.get("startfehler"):
1985|         befunde.append(f"opencode liess sich nicht starten: {info['startfehler']}")
1986|     elif info["timeout"]:
1987|         befunde.append(f"Timeout nach {timeout} s – opencode samt Unterprozessen beendet.")
1988|     elif info["ereignisse"] == 0:
1989|         befunde.append("Keine gültigen JSON-Ereignisse von opencode.")
1990|     elif info["reason"] != "stop":
1991|         befunde.append(f"Lauf nicht abgeschlossen (reason: {info['reason']}).")
1992|     # (a) immer
1993|     if head_vor != head_nach:
1994|         befunde.append(f"Selbst-Commit: HEAD {head_vor[:7]} -> {head_nach[:7]} (nichts zurückgesetzt).")
1995|     # (b) immer
1996|     if vorgabe and testdatei in aenderungen:
1997|         befunde.append(f"Vorgabe-Tests in diesem Lauf geändert: {testdatei} ({aenderungen[testdatei]}) – "
1998|                        "nichts zurückgesetzt.")
1999|     verstoesse = [(d, a) for d, a in aenderungen.items()
2000|                   if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d in (testdatei, handover_rel))]
2001|     if verstoesse:
2002|         befunde.append("Schreibbereich verletzt (nichts zurückgesetzt):\n"
2003|                        + "\n".join(f"  {d} ({a})" for d, a in verstoesse))
2004|     # (c) und (d) nur bei abgeschlossenem Lauf
2005|     rot, pruefen_code = "–", "–"
2006|     if abgeschlossen:
2007|         if handover_rel not in aenderungen or not (ROOT / handover_rel).is_file():
2008|             befunde.append(f"Handover {handover_rel} in diesem Lauf nicht geschrieben.")
2009|         elif nach_p and not re.search(rf"^## Nachbesserung {nb}\b",
2010|                                       (ROOT / handover_rel).read_text(encoding="utf-8"), re.M):
2011|             befunde.append(f"Handover {handover_rel} hat keinen Abschnitt '## Nachbesserung {nb}'.")
2012|         code = pruefen(kurztitel)
2013|         pruefen_code = str(code)
2014|         rot = _rot_aus_pruefung(kurztitel)
2015|         if code != 0:
2016|             befunde.append(f"pruefen: Exit {code}.")
2017|     else:
2018|         print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")
2019| 
2020|     exit_code = 1 if befunde else 0
2021|     reason = "timeout" if info["timeout"] else (info["reason"] or "–")
2022|     zeile = (f"- **{dt.datetime.now():%Y-%m-%d %H:%M}** – Modell: {modell}, Dauer: {info['dauer']} s, "
2023|              f"Tools: {info['werkzeuge']}, Fehler: {len(info['fehler'])}, Abgelehnt: {len(info['abgelehnt'])}, "
2024|              f"Tokens: {info['tokens']}, reason: {reason}, rot: {rot}, pruefen: {pruefen_code}, art: {art}, "
2025|              f"Exit: {exit_code}\n")
2026|     if not protokoll_p.exists():
2027|         protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
2028|                                encoding="utf-8")
2029|     tt = info["tokens_teile"]
2030|     zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}, spitze {info['tokens_spitze']}\n"
2031|     for e in info["fehler"]:
2032|         zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
2033|     with open(protokoll_p, "a", encoding="utf-8") as f:
2034|         f.write(zeile)
2035| 
2036|     print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
2037|     print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
2038|           f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']} (Spitze {info['tokens_spitze']}), reason {reason}")
2039|     for e in info["fehler"]:
2040|         print(f"  {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}")
2041|     if info["text"]:
2042|         print(f"Schlusstext: {info['text'][:300]}")
2043|     print(f"In diesem Lauf geändert: {', '.join(aenderungen) or 'nichts'}")
2044|     for b in befunde:
2045|         print(f"!!! {b}")
2046|     print(f"Rohdaten: {_rel(rohdaten)}\nProtokoll: {_rel(protokoll_p)}")
2047|     print(f"==> {'OK' if exit_code == 0 else 'NICHT IN ORDNUNG'} (Exit {exit_code})")
2048|     return exit_code
2049| 
2050| 
2051| # ---------------------------------------------------------------- main
```

### `role-split/role_proxy.py` def capture_task (Zeilen 234–282) – Spec-Auftrag im System-Prompt (E4)

```python
234| def capture_task(msgs: list) -> str:
235|     """Schreibt Aufgabe und Antworten woertlich in die Anforderungsdatei.
236| 
237|     msgs: Nachrichten NACH dem Entfernen der Trigger. Gibt den Spec-Auftrag fuer den
238|     System-Prompt zurueck ('' wenn der Chat keine "Neue Aufgabe" enthaelt).
239|     """
240|     start = None
241|     for i, m in enumerate(msgs):
242|         if isinstance(m, dict) and m.get("role") == "user":
243|             hit = NEW_TASK_RE.match(_content_as_text(m.get("content")))
244|             if hit:
245|                 start, kurztitel, aufgabe = i, hit.group(1).lower(), hit.group(2).strip()
246|                 break
247|     if start is None:
248|         return ""
249|     import contextlib, io
250|     k = _kette()
251|     with contextlib.redirect_stdout(io.StringIO()):
252|         anf = k.datei_suchen("anforderung", kurztitel, None)
253|         if anf is None:
254|             k.anforderung(kurztitel, aufgabe, None, None, None)
255|             anf = k.datei_suchen("anforderung", kurztitel, None)
256|         if anf is None:
257|             return ""
258|         vorhanden = anf.read_text(encoding="utf-8")
259|         for i in range(start + 1, len(msgs)):
260|             m = msgs[i]
261|             if not (isinstance(m, dict) and m.get("role") == "user"):
262|                 continue
263|             text = _content_as_text(m.get("content")).strip()
264|             if not text or COMMAND_RE.match(text):
265|                 continue
266|             zitat = "\n".join("> " + z if z else ">" for z in text.splitlines())
267|             if zitat in vorhanden:
268|                 continue  # schon mitgeschrieben (UI schickt den Verlauf jedes Mal)
269|             k.anforderung(kurztitel, None, text, _last_question(msgs, i), None)
270|             vorhanden = anf.read_text(encoding="utf-8")
271|             print(f"[role-split] Antwort an {anf.name} angehaengt", file=sys.stderr)
272|     datum = re.search(r"_(\d{8})_", anf.name).group(1)
273|     vorlage = HERE / "kette" / "prompts" / "spec.md"
274|     if not vorlage.is_file():
275|         return ""
276|     t = vorlage.read_text(encoding="utf-8")
277|     t = "\n".join(z for z in t.splitlines() if not z.startswith("<!--")).strip()
278|     t = re.sub(r"^@review\s+", "", t)
279|     t = (t.replace("{kurztitel}", kurztitel).replace("{datum}", datum)
280|           .replace("{anforderung}", f"docs/projekt_management/{anf.name}"))
281|     t = re.sub(r"<AUFGABE[^>]*>", lambda _m: aufgabe, t)
282|     return ("## Auftrag dieses Chats (automatisch; Hawes Worte stehen woertlich in der Anforderungsdatei)\n\n" + t)
```
