# Quellen: vorgabe_tests

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen vorgabe_tests` (2026-10-27 22:10, Stand `fb0dabd`), nach dem Abschnitt „Quellen“ in `spec_20261027_vorgabe_tests.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` def tests_finden (Zeilen 204–215) – {Test-ID: Titel} aus der Spec (A2)

```python
204| def tests_finden(text: str) -> dict[str, str]:
205|     """Test-IDs (T1, NT3 ...) mit Titel aus Ueberschriften, Fettzeilen oder Tabellenzeilen."""
206|     gefunden: dict[str, str] = {}
207|     muster = re.compile(rf"^\s*(?:#{{2,5}}\s*|\*\*|\|\s*)({TEST_ID})\b[.:)]?\s*(.*)$")
208|     for z in text.splitlines():
209|         m = muster.match(z)
210|         if not m:
211|             continue
212|         titel = m.group(2)
213|         titel = titel.split("|")[0] if z.lstrip().startswith("|") else titel
214|         gefunden.setdefault(m.group(1), titel.strip(" *:`"))
215|     return gefunden
```

### `role-split/kette/kette.py` def methoden_pruefen (Zeilen 233–259) – Hinweise OHNE PRUEF / DOPPELT / SYNTAX (A2)

```python
233| def methoden_pruefen(code: str) -> list[str]:
234|     """Findet Testmethoden ohne Pruefung und Testmethoden mit identischem Rumpf.
235|     (17./18.10.: T9 bestand aus zwei identischen Methoden; ein Test ohne assert misst nichts.)"""
236|     try:
237|         baum = ast.parse(code)
238|     except SyntaxError as e:
239|         return [f"SYNTAX    Testskript laesst sich nicht parsen: {e}"]
240|     hinweise, ruempfe = [], {}
241|     for knoten in ast.walk(baum):
242|         if not isinstance(knoten, ast.FunctionDef) or not knoten.name.startswith("test"):
243|             continue
244|         prueft = any(
245|             (isinstance(n, ast.Assert)) or
246|             (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and PRUEF_AUFRUFE.match(n.func.attr)) or
247|             (isinstance(n, ast.Raise))
248|             for n in ast.walk(knoten))
249|         if not prueft:
250|             hinweise.append(f"OHNE PRUEF {knoten.name}: kein assert/fail -- der Test kann nicht rot werden")
251|         koerper = [b for b in knoten.body
252|                    if not (isinstance(b, ast.Expr) and isinstance(getattr(b, "value", None), ast.Constant)
253|                            and isinstance(b.value.value, str))]          # Docstring ignorieren
254|         schluessel = ast.dump(ast.Module(body=koerper, type_ignores=[]))
255|         if schluessel in ruempfe:
256|             hinweise.append(f"DOPPELT   {knoten.name} hat denselben Rumpf wie {ruempfe[schluessel]}")
257|         else:
258|             ruempfe[schluessel] = knoten.name
259|     return hinweise
```

### `role-split/kette/kette.py` def tests_laufen (Zeilen 348–362) – Testskript im eigenen Prozess, Ergebnis je Methode (A2)

```python
348| def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
349|     """Laesst das Testskript in einem eigenen Prozess laufen; Ergebnis je Testmethode."""
350|     modul = ".".join(skript.relative_to(ROOT).with_suffix("").parts)
351|     # Eigener, frischer Bytecode-Cache je Lauf: sonst kann Python eine alte .pyc weiterverwenden,
352|     # wenn die zurueckgesetzte Datei gleich gross ist und in derselben Sekunde geschrieben wurde.
353|     with tempfile.TemporaryDirectory(prefix="kette_pyc_") as cache:
354|         try:
355|             r = subprocess.run([sys.executable, "-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul],
356|                                cwd=ROOT, capture_output=True, text=True, timeout=timeout)
357|         except subprocess.TimeoutExpired:
358|             return None
359|     for zeile in reversed(r.stdout.splitlines()):
360|         if zeile.startswith("@@KETTE@@"):
361|             return json.loads(zeile[len("@@KETTE@@"):])
362|     return {"<Testskript laedt nicht>": "ERROR"}
```

### `role-split/kette/kette.py` def gegenprobe (Zeilen 392–445) – Muster für Ausgabezeilen und Abschlusszeile (A2)

```python
392| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
393|     """Setzt jede seit <commit> geaenderte Code-Datei einzeln voruebergehend auf den alten Stand
394|     zurueck und laesst das Testskript laufen. Ein Test, der dabei nie rot wird, prueft keine der
395|     Aenderungen. Danach wird jeweils der aktuelle Stand wiederhergestellt (Pruefsumme)."""
396|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
397|     if not skript.is_file():
398|         print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
399|     try:
400|         kette, _fremd = _aenderungen(commit, kurztitel)
401|     except subprocess.CalledProcessError as e:
402|         print(f"git-Fehler: {e.stderr.strip()}"); return 2
403|     # A5: dieselbe Auswahl wie paket – nur zur Kette gehoerige Code-Dateien, auch role-split/kette/
404|     dateien = sorted(d for d in kette
405|                      if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))
406|     if not dateien:
407|         print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2
408| 
409|     vorher = tests_laufen(skript, timeout)
410|     if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
411|         print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
412|         return 2
413|     print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
414|     rot_durch: dict[str, list[str]] = {t: [] for t in vorher}
415|     laden_scheitert: list[str] = []
416|     for d in dateien:
417|         nachher = _zuruecksetzen_und_testen(skript, d, commit, timeout)
418|         if nachher is None:
419|             print(f"  {d}: Zeitueberschreitung"); continue
420|         if set(nachher) - set(vorher):            # Laden gescheitert
421|             print(f"  {d}: ohne die neue Fassung laedt das Testskript gar nicht -- alle Tests rot, aber ohne Einzelaussage")
422|             laden_scheitert.append(Path(d).name)
423|             continue
424|         rote = [t for t, v in nachher.items() if v in ("FAIL", "ERROR")]
425|         for t in rote:
426|             rot_durch[t].append(d)
427|         print(f"  {d}: {len(rote)} Test(s) rot")
428|     print()
429|     gruen = [t for t, ds in rot_durch.items() if not ds]
430|     for t in sorted(rot_durch):
431|         if rot_durch[t]:
432|             print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
433|         elif laden_scheitert:
434|             print(f"  LADEN {t}  (rot nur, weil das Skript ohne {', '.join(laden_scheitert)} nicht laedt -- schwacher Beleg)")
435|         else:
436|             print(f"  GRUEN {t}  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)")
437|     print(f"\n{len(vorher) - len(gruen)} von {len(vorher)} Tests werden durch eine einzelne alte Datei rot"
438|           + (f", {len(gruen)} nur ueber das Laden" if laden_scheitert else "") + ". Aktueller Stand ist wiederhergestellt.")
439|     if gruen:
440|         print("GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) "
441|               "oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, "
442|               "dann wird die Gegenprobe je Test aussagekraeftig.")
443|     return 0 if not gruen else 1
444| 
445| # ---------------------------------------------------------------- pruefen (alles in einem)
```

### `role-split/kette/kette.py` def abgleich (Zeilen 272–324) – Abschlusszeile „Keine Abweichung.“ / „n Abweichung(en).“ (A2)

```python
272| def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
273|     spec, ho = datei_suchen("spec", kurztitel, datum), datei_suchen("handover", kurztitel, datum)
274|     if not spec or not ho:
275|         print(f"Spec oder Handover fehlt: spec={spec}, handover={ho}"); return 2
276|     spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
277|     ho_text = ho.read_text(encoding="utf-8")
278|     getestet = tests_finden(abschnitt(ho_text, "Getestet"))
279|     # A2: Bereichsangaben (T1–T2, T1-T2) unter "Nicht getestet" entfernen
280|     nicht_text = abschnitt(ho_text, "Nicht getestet")
281|     nicht_text = re.sub(rf"\b({TEST_ID})\s*[–—-]\s*({TEST_ID})\b", "", nicht_text)
282|     nicht = set(re.findall(rf"\b({TEST_ID})\b", nicht_text))
283|     print(f"Spec:     {spec.name}  ({len(spec_tests)} Tests)\nHandover: {ho.name}\n")
284|     if not spec_tests:
285|         print("Keine Test-IDs (T1, NT1 ...) in der Spec gefunden."); return 2
286| 
287|     probleme = 0
288|     for tid, titel in spec_tests.items():
289|         if tid in getestet:
290|             q = passt(titel, getestet[tid])
291|             if q >= schwelle:
292|                 print(f"  ok        {tid:5} {titel}")
293|             else:
294|                 probleme += 1
295|                 print(f"  ANDERS    {tid:5} Spec: {titel}\n"
296|                       f"                  Handover: {getestet[tid]}   (Uebereinstimmung {q:.0%} -- ausgetauscht?)")
297|         elif tid in nicht:
298|             probleme += 1
299|             print(f"  NICHT GET {tid:5} {titel}  (unter 'Nicht getestet' -- Grund pruefen)")
300|         else:
301|             probleme += 1
302|             print(f"  FEHLT     {tid:5} {titel}")
303|     for tid in getestet.keys() - spec_tests.keys():
304|         print(f"  EXTRA     {tid:5} {getestet[tid]}  (nicht in der Spec)")
305| 
306|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
307|     if skript.is_file():
308|         code = skript.read_text(encoding="utf-8")
309|         ohne = [t for t in spec_tests if not re.search(rf"def\s+test_{t.lower()}(_|\b)", code)]
310|         if ohne:
311|             probleme += 1
312|             print(f"\n  Testskript {skript.relative_to(ROOT)}: keine Methode test_<id> fuer {', '.join(ohne)}")
313|         else:
314|             print(f"\n  Testskript {skript.relative_to(ROOT)}: alle {len(spec_tests)} Tests als Methode vorhanden")
315|         for hinweis in methoden_pruefen(code):
316|             probleme += 1
317|             print(f"  {hinweis}")
318|         print(f"  Selbst ausfuehren: python3 -m unittest -v {skript.relative_to(ROOT)}")
319|     else:
320|         print(f"\n  Kein Testskript tests/test_{kurztitel}.py -- Tests sind nur behauptet, nicht wiederholbar.")
321|     print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
322|     return 0 if not probleme else 1
323| 
324| # ---------------------------------------------------------------- gegenprobe
```

### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1505–1514) – Muster, wie ein Spec-Abschnitt erkannt wird (A1)

```python
1505| def _schreibbereich(spec_text: str) -> list[str] | None:
1506|     """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
1507|     if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
1508|         return None
1509|     eintraege = []
1510|     for z in abschnitt(spec_text, "Schreibbereich").splitlines():
1511|         m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
1512|         if m:
1513|             eintraege.append(m.group(1)[2:] if m.group(1).startswith("./") else m.group(1))
1514|     return eintraege
```

### `role-split/kette/kette.py` def _umsetzung_prompt (Zeilen 1657–1685) – Prompt-Aufbau, Pflichtzeilen, Nachbesserungs-Teil (A4)

```python
1657| def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path | None, nb: int) -> str | None:
1658|     vorlage = PROMPTS / "umsetzung_nacht.md"
1659|     if not vorlage.is_file():
1660|         return None
1661|     anf = datei_suchen("anforderung", kurztitel, None)
1662|     anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
1663|         f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
1664|     text = (vorlage.read_text(encoding="utf-8")
1665|             .replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", commit)
1666|             .replace("{anforderung}", anf_pfad)
1667|             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md"))
1668|     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
1669|     # A1: Pflichtzeilen im Handover – nach Grundtext, vor Nachbesserung
1670|     spec_p = datei_suchen("spec", kurztitel, None)
1671|     if spec_p:
1672|         spec_tests = tests_finden(spec_p.read_text(encoding="utf-8"))
1673|         if spec_tests:
1674|             zeilen = ["", "## Pflichtzeilen im Handover",
1675|                       'Unter „## Getestet" steht für jede Test-ID genau eine dieser Zeilen (Titel unverändert, Status wählen):']
1676|             for tid, titel in spec_tests.items():
1677|                 zeilen.append(f"**{tid}: {titel}** – bestanden | fehlgeschlagen")
1678|             zeilen.append('Unter „## Nicht getestet" nur Test-IDs, die wirklich nicht getestet sind – keine Sammelangaben wie „T1–T5".')
1679|             text += "\n".join(zeilen) + "\n"
1680|     if nacharbeit:
1681|         text += (f"\n## Nachbesserung {nb}\n\nDas ist Nachbesserung {nb}. Der Auftrag steht unten (aus "
1682|                  f"`{_rel(nacharbeit)}`). Ergänze den Handover docs/projekt_management/handover_{datum}_"
1683|                  f"{kurztitel}.md um den Abschnitt „## Nachbesserung {nb}\" – nichts Bestehendes löschen.\n\n"
1684|                  + nacharbeit.read_text(encoding="utf-8").strip() + "\n")
1685|     return text
```

### `role-split/kette/kette.py` def umsetzung_auto (Zeilen 1781–1952) – Vorab-Prüfungen, Prüfung (b) Schreibbereich (A3)

```python
1781| def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
1782|     """K10: Umsetzung bzw. Nacharbeit ueber `opencode run` ohne TUI, danach mechanisch pruefen.
1783|     Exit 0 = abgeschlossen + keine Verletzung + pruefen 0; 1 = Lauf/Pruefung nicht in Ordnung; 2 = Voraussetzung."""
1784|     def nein(meldung: str, code: int = 2) -> int:
1785|         print(meldung, file=sys.stderr)
1786|         return code
1787| 
1788|     # A2.1 Kurztitel
1789|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
1790|         return nein(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).")
1791|     # A2.2 Spec-Commit
1792|     commit = spec_commit(kurztitel)
1793|     if not commit:
1794|         return nein(f"Kein Commit 'Spec {kurztitel}' gefunden – erst die Spec committen.")
1795|     # A2.3 Spec mit Schreibbereich
1796|     spec_p = datei_suchen("spec", kurztitel, None)
1797|     if not spec_p:
1798|         return nein(f"Keine Spec spec_<datum>_{kurztitel}.md in {_rel(PM)}.")
1799|     bereich = _schreibbereich(spec_p.read_text(encoding="utf-8"))
1800|     if bereich is None:
1801|         return nein(f"Spec {spec_p.name} hat keinen Abschnitt '## Schreibbereich'. Spec um '## Schreibbereich' "
1802|                     "ergaenzen (Dateien/Ordner, die die Umsetzung aendern darf), sonst kein umsetzung-auto-Lauf.")
1803|     if not bereich:
1804|         return nein(f"'## Schreibbereich' in {spec_p.name} ist leer – mindestens einen Pfad eintragen.")
1805|     for e in bereich:
1806|         if _ist_vorgabe(e):
1807|             print(f"Hinweis: Schreibbereich nennt {e} – Vorgaben (spec_/anforderung_/quellen_/_vorlage_) "
1808|                   "sind nie erlaubt; eine Änderung daran endet in (b) mit Exit 1.", file=sys.stderr)
1809|     datum = _datum_aus(spec_p) or dt.date.today().strftime("%Y%m%d")
1810|     testdatei = f"tests/test_{kurztitel}.py"
1811|     handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
1812|     protokoll_p = PM / f"umsetzung_{datum}_{kurztitel}.md"
1813|     nach_p = None
1814|     if nacharbeit:
1815|         nach_p = Path(nacharbeit)
1816|         if not nach_p.is_absolute():
1817|             nach_p = (ROOT / nach_p) if (ROOT / nach_p).is_file() else nach_p.resolve()
1818|         if not nach_p.is_file():
1819|             return nein(f"Nacharbeitsdatei {nacharbeit} nicht gefunden.")
1820|     # A2.4 Arbeitsstand
1821|     offen = _offene_dateien()
1822|     if offen is None:
1823|         return nein("git status fehlgeschlagen – ist ROOT ein Git-Repo?")
1824|     if not nach_p:
1825|         if offen:
1826|             return nein("Arbeitsstand nicht sauber – ohne --nacharbeit muss alles committet sein:\n"
1827|                         + "\n".join(f"  {d}" for d in offen))
1828|     else:
1829|         try:
1830|             nach_rel = nach_p.resolve().relative_to(ROOT.resolve()).as_posix()
1831|         except ValueError:
1832|             nach_rel = None
1833|         fremd = [d for d in offen
1834|                  if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d == testdatei or d == handover_rel
1835|                                              or _ist_kettendatei(d, kurztitel) or d == nach_rel)]
1836|         if fremd:
1837|             return nein("Nacharbeit: unzulaessige offene Aenderungen (Vorgaben oder ausserhalb von Schreibbereich/"
1838|                         "Testdatei/Kettendateien):\n" + "\n".join(f"  {d}" for d in fremd))
1839|     # A2.5 opencode
1840|     programm = _opencode_programm()
1841|     if not programm:
1842|         ziel = os.environ.get("KETTE_OPENCODE") or "opencode im PATH"
1843|         return nein(f"opencode nicht gefunden ({ziel}).")
1844|     # A2.6 Modell
1845|     modell = os.environ.get("KETTE_UMSETZUNG_MODEL", UMSETZUNG_MODELL_STANDARD)
1846|     if not modell.startswith("llamacpp/"):
1847|         return nein(f"Modell '{modell}' beginnt nicht mit 'llamacpp/' (nur direkt am Router, ohne Gedaechtnis).")
1848|     # A8 Halt-Regel und Nummer
1849|     zeilen = _protokoll(protokoll_p)
1850|     handover_p = ROOT / handover_rel
1851|     handover_alt = handover_p.read_text(encoding="utf-8") if handover_p.is_file() else ""
1852|     nb = len(re.findall(r"^## Nachbesserung\b", handover_alt, re.M)) + 1
1853|     if nach_p and _halt_noetig(zeilen):
1854|         return nein("Zwei Nachbesserungen in Folge ohne Fortschritt – keine weitere. Übergabe an Hawe.", 1)
1855|     art = f"nb{nb}" if nach_p else "erst"
1856|     # A3 Prompt
1857|     prompt_text = _umsetzung_prompt(kurztitel, datum, commit, nach_p, nb)
1858|     if prompt_text is None:
1859|         return nein(f"Prompt-Vorlage {_rel(PROMPTS / 'umsetzung_nacht.md')} fehlt.")
1860|     try:
1861|         timeout = int(os.environ.get("KETTE_UMSETZUNG_TIMEOUT", UMSETZUNG_TIMEOUT_STANDARD))
1862|         bash_ms = int(os.environ.get("OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS", UMSETZUNG_BASH_MS_STANDARD))
1863|     except ValueError:
1864|         return nein("KETTE_UMSETZUNG_TIMEOUT / OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS muessen ganze Zahlen sein.")
1865| 
1866|     # A7 Schnappschuss VOR dem Start
1867|     head_vor = _git("rev-parse", "HEAD").strip()
1868|     stand_vor = _stand()
1869|     if stand_vor is None:
1870|         return nein("git status fehlgeschlagen.")
1871|     befehl = programm + ["run", "--format", "json", "--agent", UMSETZUNG_AGENT, "--model", modell,
1872|                          "--dir", str(ROOT), "--title", f"kette {kurztitel} {art}", prompt_text]
1873|     env = dict(os.environ, OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=str(bash_ms))
1874|     rohdaten = ROOT / "role-split" / "results" / f"umsetzung_auto_{datum}_{kurztitel}_{dt.datetime.now():%H%M%S}.jsonl"
1875|     print(f"umsetzung-auto {kurztitel} ({art}): Modell {modell}, Agent {UMSETZUNG_AGENT}, "
1876|           f"Zeitlimit {timeout} s, Rücksetzpunkt {commit}", flush=True)
1877|     info = _lauf(befehl, env, timeout, rohdaten)
1878| 
1879|     # A7 Schnappschuss SOFORT nach dem Lauf, bevor kette.py selbst etwas schreibt
1880|     stand_nach = _stand() or {}
1881|     head_nach = _git("rev-parse", "HEAD").strip()
1882|     aenderungen = _in_diesem_lauf(stand_vor, stand_nach)
1883|     abgeschlossen = not info["timeout"] and info["reason"] == "stop"
1884|     befunde = []
1885| 
1886|     if info.get("haengt"):
1887|         befunde.append("opencode reagiert 30 s nach SIGKILL nicht – Prozess pruefen (ps).")
1888|     if info.get("startfehler"):
1889|         befunde.append(f"opencode liess sich nicht starten: {info['startfehler']}")
1890|     elif info["timeout"]:
1891|         befunde.append(f"Timeout nach {timeout} s – opencode samt Unterprozessen beendet.")
1892|     elif info["ereignisse"] == 0:
1893|         befunde.append("Keine gültigen JSON-Ereignisse von opencode.")
1894|     elif info["reason"] != "stop":
1895|         befunde.append(f"Lauf nicht abgeschlossen (reason: {info['reason']}).")
1896|     # (a) immer
1897|     if head_vor != head_nach:
1898|         befunde.append(f"Selbst-Commit: HEAD {head_vor[:7]} -> {head_nach[:7]} (nichts zurückgesetzt).")
1899|     # (b) immer
1900|     verstoesse = [(d, a) for d, a in aenderungen.items()
1901|                   if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d in (testdatei, handover_rel))]
1902|     if verstoesse:
1903|         befunde.append("Schreibbereich verletzt (nichts zurückgesetzt):\n"
1904|                        + "\n".join(f"  {d} ({a})" for d, a in verstoesse))
1905|     # (c) und (d) nur bei abgeschlossenem Lauf
1906|     rot, pruefen_code = "–", "–"
1907|     if abgeschlossen:
1908|         if handover_rel not in aenderungen or not (ROOT / handover_rel).is_file():
1909|             befunde.append(f"Handover {handover_rel} in diesem Lauf nicht geschrieben.")
1910|         elif nach_p and not re.search(rf"^## Nachbesserung {nb}\b",
1911|                                       (ROOT / handover_rel).read_text(encoding="utf-8"), re.M):
1912|             befunde.append(f"Handover {handover_rel} hat keinen Abschnitt '## Nachbesserung {nb}'.")
1913|         code = pruefen(kurztitel)
1914|         pruefen_code = str(code)
1915|         rot = _rot_aus_pruefung(kurztitel)
1916|         if code != 0:
1917|             befunde.append(f"pruefen: Exit {code}.")
1918|     else:
1919|         print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")
1920| 
1921|     exit_code = 1 if befunde else 0
1922|     reason = "timeout" if info["timeout"] else (info["reason"] or "–")
1923|     zeile = (f"- **{dt.datetime.now():%Y-%m-%d %H:%M}** – Modell: {modell}, Dauer: {info['dauer']} s, "
1924|              f"Tools: {info['werkzeuge']}, Fehler: {len(info['fehler'])}, Abgelehnt: {len(info['abgelehnt'])}, "
1925|              f"Tokens: {info['tokens']}, reason: {reason}, rot: {rot}, pruefen: {pruefen_code}, art: {art}, "
1926|              f"Exit: {exit_code}\n")
1927|     if not protokoll_p.exists():
1928|         protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
1929|                                encoding="utf-8")
1930|     tt = info["tokens_teile"]
1931|     zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}, spitze {info['tokens_spitze']}\n"
1932|     for e in info["fehler"]:
1933|         zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
1934|     with open(protokoll_p, "a", encoding="utf-8") as f:
1935|         f.write(zeile)
1936| 
1937|     print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
1938|     print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
1939|           f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']} (Spitze {info['tokens_spitze']}), reason {reason}")
1940|     for e in info["fehler"]:
1941|         print(f"  {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}")
1942|     if info["text"]:
1943|         print(f"Schlusstext: {info['text'][:300]}")
1944|     print(f"In diesem Lauf geändert: {', '.join(aenderungen) or 'nichts'}")
1945|     for b in befunde:
1946|         print(f"!!! {b}")
1947|     print(f"Rohdaten: {_rel(rohdaten)}\nProtokoll: {_rel(protokoll_p)}")
1948|     print(f"==> {'OK' if exit_code == 0 else 'NICHT IN ORDNUNG'} (Exit {exit_code})")
1949|     return exit_code
1950| 
1951| 
1952| # ---------------------------------------------------------------- main
```

### `role-split/kette/kette.py` def main (Zeilen 1954–2003) – Subparser (A5)

```python
1954| def main(argv=None) -> int:
1955|     ap = argparse.ArgumentParser(description="Werkzeug fuer die Kette Spec -> Umsetzung -> Review")
1956|     sub = ap.add_subparsers(dest="cmd", required=True)
1957|     p = sub.add_parser("prompt"); p.add_argument("schritt", choices=SCHRITTE); p.add_argument("kurztitel")
1958|     p.add_argument("--datum"); p.add_argument("--commit")
1959|     p.add_argument("--lauf", type=int, help="Review-Lauf-Nummer (eigener Verdikt-Dateiname je Lauf)")
1960|     q = sub.add_parser("quellen"); q.add_argument("kurztitel"); q.add_argument("--datum")
1961|     n = sub.add_parser("anforderung"); n.add_argument("kurztitel")
1962|     n.add_argument("--aufgabe"); n.add_argument("--antwort"); n.add_argument("--frage"); n.add_argument("--datum")
1963|     a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
1964|     u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
1965|     g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
1966|     g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
1967|     g.add_argument("--timeout", type=int, default=300)
1968|     zf = sub.add_parser("zusammenfuehren", help="Befunde mehrerer Review-Laeufe mechanisch zusammenfuehren")
1969|     zf.add_argument("verdikte", nargs="+")
1970|     pk = sub.add_parser("paket", help="Review-Paket bauen (eine Datei fuers Review)")
1971|     pk.add_argument("kurztitel"); pk.add_argument("--commit"); pk.add_argument("--datum")
1972|     pr = sub.add_parser("pruefen", help="abgleich + unittest + gegenprobe, Ausgabe in Datei")
1973|     pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
1974|     ra = sub.add_parser("review-auto", help="Review-Paket, zwei API-Laeufe, Verdikte, Zusammenfassung")
1975|     ra.add_argument("kurztitel")
1976|     ua = sub.add_parser("umsetzung-auto", help="Umsetzung/Nacharbeit ueber opencode run ohne TUI, danach pruefen")
1977|     ua.add_argument("kurztitel"); ua.add_argument("--nacharbeit", help="Datei mit dem Nachbesserungs-Auftrag")
1978|     args = ap.parse_args(argv)
1979|     if args.cmd == "zusammenfuehren":
1980|         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
1981|                                 for v in args.verdikte])
1982|     if args.cmd == "paket":
1983|         return paket(args.kurztitel, args.commit, args.datum)
1984|     if args.cmd == "pruefen":
1985|         return pruefen(args.kurztitel, args.commit, args.timeout)
1986|     if args.cmd == "review-auto":
1987|         return review_auto(args.kurztitel)
1988|     if args.cmd == "umsetzung-auto":
1989|         return umsetzung_auto(args.kurztitel, args.nacharbeit)
1990|     if args.cmd == "gegenprobe":
1991|         return gegenprobe(args.kurztitel, args.commit, args.timeout)
1992|     if args.cmd == "quellen":
1993|         return quellen(args.kurztitel, args.datum)
1994|     if args.cmd == "anforderung":
1995|         return anforderung(args.kurztitel, args.aufgabe, args.antwort, args.frage, args.datum)
1996|     if args.cmd == "prompt":
1997|         return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
1998|     if args.cmd == "abgleich":
1999|         return abgleich(args.kurztitel, args.datum)
2000|     pfad = Path(args.verdikt)
2001|     if not pfad.is_absolute() and not pfad.exists():
2002|         pfad = PM / pfad.name
2003|     return urteil(pfad, args.anhaengen)
```

### `tests/test_umsetzung_auto.py` class Basis (Zeilen 51–125) – Testaufbau T6–T8

```python
 51| class Basis(unittest.TestCase):
 52|     pruefen_code = 0
 53|     pruefen_ausgabe = "Ran 1 test in 0.001s\n\nOK"
 54| 
 55|     def setUp(self):
 56|         self.echt_vorher = _echter_stand()
 57|         d = tempfile.TemporaryDirectory()
 58|         self.addCleanup(d.cleanup)
 59|         self.root = root = Path(d.name).resolve()
 60|         self.pm = root / "docs" / "projekt_management"
 61|         self.pm.mkdir(parents=True)
 62|         (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC, encoding="utf-8")
 63|         (self.pm / f"anforderung_{DATUM}_g.md").write_text("# Anforderung g\n\n## Aufgabe\n\n> X\n", encoding="utf-8")
 64|         (self.pm / f"quellen_{DATUM}_g.md").write_text("# Quellen g\n", encoding="utf-8")
 65|         (root / "src").mkdir()
 66|         (root / "src" / "modul.py").write_text("X = 1\n", encoding="utf-8")
 67|         (root / "role-split" / "kette").mkdir(parents=True)
 68|         (root / "role-split" / "kette" / "kette.py").write_text("# Platzhalter\n", encoding="utf-8")
 69|         (root / ".gitignore").write_text("role-split/results/\n", encoding="utf-8")
 70|         self.git("init", "-q")
 71|         self.git("add", ".")
 72|         self.git("commit", "-qm", "Spec g")
 73|         for name, wert in (("ROOT", root), ("PM", self.pm)):
 74|             alt = getattr(kette, name)
 75|             setattr(kette, name, wert)
 76|             self.addCleanup(setattr, kette, name, alt)
 77|         self.aufrufe_pruefen = 0
 78| 
 79|         def pruefen_attrappe(kurztitel, commit=None, timeout=300):
 80|             self.aufrufe_pruefen += 1
 81|             (self.pm / f"pruefung_{DATUM}_{kurztitel}.md").write_text(
 82|                 f"# Pruefung {kurztitel}\n\n## unittest  (Exit {self.pruefen_code})\n\n```\n"
 83|                 f"{self.pruefen_ausgabe}\n```\n", encoding="utf-8")
 84|             return self.pruefen_code
 85|         alt_pruefen = kette.pruefen
 86|         kette.pruefen = pruefen_attrappe
 87|         self.addCleanup(setattr, kette, "pruefen", alt_pruefen)
 88|         self.argsdatei = root.parent / f"{root.name}_args.json"
 89|         self.addCleanup(lambda: self.argsdatei.unlink(missing_ok=True))
 90|         umgebung = {k: v for k, v in os.environ.items() if not k.startswith("FAKE_")}
 91|         umgebung.update({"KETTE_OPENCODE": str(FAKE), "KETTE_UMSETZUNG_TIMEOUT": "60",
 92|                          "FAKE_ARGS": str(self.argsdatei)})
 93|         umgebung.pop("KETTE_UMSETZUNG_MODEL", None)
 94|         p = mock.patch.dict(os.environ, umgebung, clear=True)
 95|         p.start()
 96|         self.addCleanup(p.stop)
 97|         self.addCleanup(self._echt_unveraendert)
 98| 
 99|     def _echt_unveraendert(self):
100|         self.assertEqual(_echter_stand(), self.echt_vorher, "Test hat das echte Repo veraendert!")
101| 
102|     def git(self, *a) -> str:
103|         return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
104|                               check=True, capture_output=True, text=True).stdout
105| 
106|     def lauf(self, kurztitel="g", nacharbeit=None, **fake):
107|         from kette import umsetzung_auto
108|         os.environ.update({k: str(v) for k, v in fake.items()})
109|         aus, fehler = io.StringIO(), io.StringIO()
110|         with redirect_stdout(aus), redirect_stderr(fehler):
111|             code = umsetzung_auto(kurztitel, nacharbeit)
112|         return code, aus.getvalue() + fehler.getvalue()
113| 
114|     def protokoll(self) -> str:
115|         p = self.pm / f"umsetzung_{DATUM}_g.md"
116|         return p.read_text(encoding="utf-8") if p.exists() else ""
117| 
118|     def gestartet(self) -> bool:
119|         return self.argsdatei.exists()
120| 
121|     def nacharbeit_vorbereiten(self, auftrag="Bitte A3 korrigieren: Feld X fehlt."):
122|         (self.root / HANDOVER).write_text("# Handover g\n\nErstumsetzung.\n", encoding="utf-8")
123|         datei = self.pm / f"nacharbeit_{DATUM}_g_1.md"
124|         datei.write_text(auftrag + "\n", encoding="utf-8")
125|         return datei
```
