# Quellen: vorgabe_nachtrag

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen vorgabe_nachtrag` (2026-10-28 09:48, Stand `5711d85`), nach dem Abschnitt „Quellen“ in `spec_20261028_vorgabe_nachtrag.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` def tests_finden (Zeilen 208–219) – {Test-ID: Titel} (B1, B2)

```python
208| def tests_finden(text: str) -> dict[str, str]:
209|     """Test-IDs (T1, NT3 ...) mit Titel aus Ueberschriften, Fettzeilen oder Tabellenzeilen."""
210|     gefunden: dict[str, str] = {}
211|     muster = re.compile(rf"^\s*(?:#{{2,5}}\s*|\*\*|\|\s*)({TEST_ID})\b[.:)]?\s*(.*)$")
212|     for z in text.splitlines():
213|         m = muster.match(z)
214|         if not m:
215|             continue
216|         titel = m.group(2)
217|         titel = titel.split("|")[0] if z.lstrip().startswith("|") else titel
218|         gefunden.setdefault(m.group(1), titel.strip(" *:`"))
219|     return gefunden
```

### `role-split/kette/kette.py` def datei_suchen (Zeilen 266–273) – Spec zum Kurztitel finden (B1)

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

### `role-split/kette/kette.py` def _vorgabe_tests (Zeilen 451–453) – Stelle für die neue Konstante und den Helfer (B1)

```python
451| def _vorgabe_tests(spec_text: str) -> bool:
452|     """Wahr, wenn die Spec den Abschnitt '## Vorgabe-Tests' hat (Tests vorab, Umsetzer schreibt nur Code)."""
453|     return re.search(r"^##\s+Vorgabe-Tests\s*$", spec_text, re.M) is not None
```

### `role-split/kette/kette.py` def tests_pruefen (Zeilen 456–499) – Schleife über die Test-IDs (B1)

```python
456| def tests_pruefen(kurztitel: str, timeout: int = 300) -> int:
457|     """Prueft vorab geschriebene Tests: je Test-ID der Spec eine Methode, Skript laedt, jeder Test rot vorab."""
458|     spec = datei_suchen("spec", kurztitel, None)
459|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
460|     if not skript.is_file():
461|         print(f"Keine Vorgabe-Tests tests/test_{kurztitel}.py"); return 2
462|     if not spec:
463|         print(f"Keine spec_*_{kurztitel}.md"); return 2
464|     spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
465|     if not spec_tests:
466|         print(f"Keine Test-IDs (T1, NT1 ...) in {spec.name}"); return 2
467|     code = skript.read_text(encoding="utf-8")
468|     probleme = 0
469|     for hinweis in methoden_pruefen(code):
470|         probleme += 1
471|         print(f"  {hinweis}")
472|     stand = tests_laufen(skript, timeout)
473|     if stand is None:
474|         print(f"  ZEIT      Testskript nach {timeout} s abgebrochen")
475|         return 1
476|     try:
477|         methoden = {k.name for k in ast.walk(ast.parse(code))
478|                     if isinstance(k, (ast.FunctionDef, ast.AsyncFunctionDef)) and k.name.startswith("test")}
479|     except SyntaxError:
480|         methoden = set()
481|     if not set(stand) & methoden:          # nur Lade-Eintraege, keine echte Testmethode gelaufen
482|         print("  LAEDT NICHT Testskript laedt nicht -- neue Funktionen erst in der Methode importieren")
483|         return 1
484|     for tid in spec_tests:
485|         namen = [n for n in stand if re.match(rf"test_{tid.lower()}(_|$)", n)]
486|         if not namen:
487|             probleme += 1
488|             print(f"  FEHLT     {tid}")
489|             continue
490|         nicht_rot = [n for n in namen if stand[n] not in ("FAIL", "ERROR")]
491|         if nicht_rot:
492|             probleme += 1
493|             print(f"  NICHT ROT {tid}  {', '.join(nicht_rot)} (ohne Umsetzung nicht rot -- prueft nichts Neues)")
494|         else:
495|             print(f"  rot       {tid}")
496|     print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
497|     return 0 if not probleme else 1
498| 
499| # ---------------------------------------------------------------- pruefen (alles in einem)
```

### `role-split/kette/kette.py` def gegenprobe (Zeilen 396–449) – Liste `gruen` und Ausgabeschleife (B2)

```python
396| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
397|     """Setzt jede seit <commit> geaenderte Code-Datei einzeln voruebergehend auf den alten Stand
398|     zurueck und laesst das Testskript laufen. Ein Test, der dabei nie rot wird, prueft keine der
399|     Aenderungen. Danach wird jeweils der aktuelle Stand wiederhergestellt (Pruefsumme)."""
400|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
401|     if not skript.is_file():
402|         print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
403|     try:
404|         kette, _fremd = _aenderungen(commit, kurztitel)
405|     except subprocess.CalledProcessError as e:
406|         print(f"git-Fehler: {e.stderr.strip()}"); return 2
407|     # A5: dieselbe Auswahl wie paket – nur zur Kette gehoerige Code-Dateien, auch role-split/kette/
408|     dateien = sorted(d for d in kette
409|                      if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))
410|     if not dateien:
411|         print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2
412| 
413|     vorher = tests_laufen(skript, timeout)
414|     if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
415|         print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
416|         return 2
417|     print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
418|     rot_durch: dict[str, list[str]] = {t: [] for t in vorher}
419|     laden_scheitert: list[str] = []
420|     for d in dateien:
421|         nachher = _zuruecksetzen_und_testen(skript, d, commit, timeout)
422|         if nachher is None:
423|             print(f"  {d}: Zeitueberschreitung"); continue
424|         if set(nachher) - set(vorher):            # Laden gescheitert
425|             print(f"  {d}: ohne die neue Fassung laedt das Testskript gar nicht -- alle Tests rot, aber ohne Einzelaussage")
426|             laden_scheitert.append(Path(d).name)
427|             continue
428|         rote = [t for t, v in nachher.items() if v in ("FAIL", "ERROR")]
429|         for t in rote:
430|             rot_durch[t].append(d)
431|         print(f"  {d}: {len(rote)} Test(s) rot")
432|     print()
433|     gruen = [t for t, ds in rot_durch.items() if not ds]
434|     for t in sorted(rot_durch):
435|         if rot_durch[t]:
436|             print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
437|         elif laden_scheitert:
438|             print(f"  LADEN {t}  (rot nur, weil das Skript ohne {', '.join(laden_scheitert)} nicht laedt -- schwacher Beleg)")
439|         else:
440|             print(f"  GRUEN {t}  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)")
441|     print(f"\n{len(vorher) - len(gruen)} von {len(vorher)} Tests werden durch eine einzelne alte Datei rot"
442|           + (f", {len(gruen)} nur ueber das Laden" if laden_scheitert else "") + ". Aktueller Stand ist wiederhergestellt.")
443|     if gruen:
444|         print("GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) "
445|               "oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, "
446|               "dann wird die Gegenprobe je Test aussagekraeftig.")
447|     return 0 if not gruen else 1
448| 
449| # ---------------------------------------------------------------- tests-pruefen (K11a)
```

### `role-split/kette/kette.py` def umsetzung_auto (Zeilen 1840–2022) – Block „K11a: Vorgabe-Tests“, Liste `offen` (A2.4), Prüfung (b) (B3, B4)

```python
1840| def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
1841|     """K10: Umsetzung bzw. Nacharbeit ueber `opencode run` ohne TUI, danach mechanisch pruefen.
1842|     Exit 0 = abgeschlossen + keine Verletzung + pruefen 0; 1 = Lauf/Pruefung nicht in Ordnung; 2 = Voraussetzung."""
1843|     def nein(meldung: str, code: int = 2) -> int:
1844|         print(meldung, file=sys.stderr)
1845|         return code
1846| 
1847|     # A2.1 Kurztitel
1848|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
1849|         return nein(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).")
1850|     # A2.2 Spec-Commit
1851|     commit = spec_commit(kurztitel)
1852|     if not commit:
1853|         return nein(f"Kein Commit 'Spec {kurztitel}' gefunden – erst die Spec committen.")
1854|     # A2.3 Spec mit Schreibbereich
1855|     spec_p = datei_suchen("spec", kurztitel, None)
1856|     if not spec_p:
1857|         return nein(f"Keine Spec spec_<datum>_{kurztitel}.md in {_rel(PM)}.")
1858|     bereich = _schreibbereich(spec_p.read_text(encoding="utf-8"))
1859|     if bereich is None:
1860|         return nein(f"Spec {spec_p.name} hat keinen Abschnitt '## Schreibbereich'. Spec um '## Schreibbereich' "
1861|                     "ergaenzen (Dateien/Ordner, die die Umsetzung aendern darf), sonst kein umsetzung-auto-Lauf.")
1862|     if not bereich:
1863|         return nein(f"'## Schreibbereich' in {spec_p.name} ist leer – mindestens einen Pfad eintragen.")
1864|     for e in bereich:
1865|         if _ist_vorgabe(e):
1866|             print(f"Hinweis: Schreibbereich nennt {e} – Vorgaben (spec_/anforderung_/quellen_/_vorlage_) "
1867|                   "sind nie erlaubt; eine Änderung daran endet in (b) mit Exit 1.", file=sys.stderr)
1868|     datum = _datum_aus(spec_p) or dt.date.today().strftime("%Y%m%d")
1869|     testdatei = f"tests/test_{kurztitel}.py"
1870|     handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
1871|     protokoll_p = PM / f"umsetzung_{datum}_{kurztitel}.md"
1872|     nach_p = None
1873|     if nacharbeit:
1874|         nach_p = Path(nacharbeit)
1875|         if not nach_p.is_absolute():
1876|             nach_p = (ROOT / nach_p) if (ROOT / nach_p).is_file() else nach_p.resolve()
1877|         if not nach_p.is_file():
1878|             return nein(f"Nacharbeitsdatei {nacharbeit} nicht gefunden.")
1879|     # A2.4 Arbeitsstand
1880|     offen = _offene_dateien()
1881|     if offen is None:
1882|         return nein("git status fehlgeschlagen – ist ROOT ein Git-Repo?")
1883|     if not nach_p:
1884|         if offen:
1885|             return nein("Arbeitsstand nicht sauber – ohne --nacharbeit muss alles committet sein:\n"
1886|                         + "\n".join(f"  {d}" for d in offen))
1887|     else:
1888|         try:
1889|             nach_rel = nach_p.resolve().relative_to(ROOT.resolve()).as_posix()
1890|         except ValueError:
1891|             nach_rel = None
1892|         fremd = [d for d in offen
1893|                  if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d == testdatei or d == handover_rel
1894|                                              or _ist_kettendatei(d, kurztitel) or d == nach_rel)]
1895|         if fremd:
1896|             return nein("Nacharbeit: unzulaessige offene Aenderungen (Vorgaben oder ausserhalb von Schreibbereich/"
1897|                         "Testdatei/Kettendateien):\n" + "\n".join(f"  {d}" for d in fremd))
1898|     # K11a: Vorgabe-Tests
1899|     vorgabe = _vorgabe_tests(spec_p.read_text(encoding="utf-8"))
1900|     if vorgabe:
1901|         if not (ROOT / testdatei).is_file():
1902|             return nein(f"Spec nennt '## Vorgabe-Tests', aber {testdatei} fehlt.")
1903|         if not nach_p and tests_pruefen(kurztitel) != 0:
1904|             return nein(f"Vorgabe-Tests nicht in Ordnung (kette.py tests-pruefen {kurztitel}) – kein Lauf.")
1905|     # A2.5 opencode
1906|     programm = _opencode_programm()
1907|     if not programm:
1908|         ziel = os.environ.get("KETTE_OPENCODE") or "opencode im PATH"
1909|         return nein(f"opencode nicht gefunden ({ziel}).")
1910|     # A2.6 Modell
1911|     modell = os.environ.get("KETTE_UMSETZUNG_MODEL", UMSETZUNG_MODELL_STANDARD)
1912|     if not modell.startswith("llamacpp/"):
1913|         return nein(f"Modell '{modell}' beginnt nicht mit 'llamacpp/' (nur direkt am Router, ohne Gedaechtnis).")
1914|     # A8 Halt-Regel und Nummer
1915|     zeilen = _protokoll(protokoll_p)
1916|     handover_p = ROOT / handover_rel
1917|     handover_alt = handover_p.read_text(encoding="utf-8") if handover_p.is_file() else ""
1918|     nb = len(re.findall(r"^## Nachbesserung\b", handover_alt, re.M)) + 1
1919|     if nach_p and _halt_noetig(zeilen):
1920|         return nein("Zwei Nachbesserungen in Folge ohne Fortschritt – keine weitere. Übergabe an Hawe.", 1)
1921|     art = f"nb{nb}" if nach_p else "erst"
1922|     # A3 Prompt
1923|     prompt_text = _umsetzung_prompt(kurztitel, datum, commit, nach_p, nb)
1924|     if prompt_text is None:
1925|         return nein(f"Prompt-Vorlage {_rel(PROMPTS / 'umsetzung_nacht.md')} fehlt.")
1926|     try:
1927|         timeout = int(os.environ.get("KETTE_UMSETZUNG_TIMEOUT", UMSETZUNG_TIMEOUT_STANDARD))
1928|         bash_ms = int(os.environ.get("OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS", UMSETZUNG_BASH_MS_STANDARD))
1929|     except ValueError:
1930|         return nein("KETTE_UMSETZUNG_TIMEOUT / OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS muessen ganze Zahlen sein.")
1931| 
1932|     # A7 Schnappschuss VOR dem Start
1933|     head_vor = _git("rev-parse", "HEAD").strip()
1934|     stand_vor = _stand()
1935|     if stand_vor is None:
1936|         return nein("git status fehlgeschlagen.")
1937|     befehl = programm + ["run", "--format", "json", "--agent", UMSETZUNG_AGENT, "--model", modell,
1938|                          "--dir", str(ROOT), "--title", f"kette {kurztitel} {art}", prompt_text]
1939|     env = dict(os.environ, OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=str(bash_ms))
1940|     rohdaten = ROOT / "role-split" / "results" / f"umsetzung_auto_{datum}_{kurztitel}_{dt.datetime.now():%H%M%S}.jsonl"
1941|     print(f"umsetzung-auto {kurztitel} ({art}): Modell {modell}, Agent {UMSETZUNG_AGENT}, "
1942|           f"Zeitlimit {timeout} s, Rücksetzpunkt {commit}", flush=True)
1943|     info = _lauf(befehl, env, timeout, rohdaten)
1944| 
1945|     # A7 Schnappschuss SOFORT nach dem Lauf, bevor kette.py selbst etwas schreibt
1946|     stand_nach = _stand() or {}
1947|     head_nach = _git("rev-parse", "HEAD").strip()
1948|     aenderungen = _in_diesem_lauf(stand_vor, stand_nach)
1949|     abgeschlossen = not info["timeout"] and info["reason"] == "stop"
1950|     befunde = []
1951| 
1952|     if info.get("haengt"):
1953|         befunde.append("opencode reagiert 30 s nach SIGKILL nicht – Prozess pruefen (ps).")
1954|     if info.get("startfehler"):
1955|         befunde.append(f"opencode liess sich nicht starten: {info['startfehler']}")
1956|     elif info["timeout"]:
1957|         befunde.append(f"Timeout nach {timeout} s – opencode samt Unterprozessen beendet.")
1958|     elif info["ereignisse"] == 0:
1959|         befunde.append("Keine gültigen JSON-Ereignisse von opencode.")
1960|     elif info["reason"] != "stop":
1961|         befunde.append(f"Lauf nicht abgeschlossen (reason: {info['reason']}).")
1962|     # (a) immer
1963|     if head_vor != head_nach:
1964|         befunde.append(f"Selbst-Commit: HEAD {head_vor[:7]} -> {head_nach[:7]} (nichts zurückgesetzt).")
1965|     # (b) immer
1966|     if vorgabe and testdatei in aenderungen:
1967|         befunde.append(f"Vorgabe-Tests in diesem Lauf geändert: {testdatei} ({aenderungen[testdatei]}) – "
1968|                        "nichts zurückgesetzt.")
1969|     verstoesse = [(d, a) for d, a in aenderungen.items()
1970|                   if not (vorgabe and d == testdatei)
1971|                   and (_ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d in (testdatei, handover_rel)))]
1972|     if verstoesse:
1973|         befunde.append("Schreibbereich verletzt (nichts zurückgesetzt):\n"
1974|                        + "\n".join(f"  {d} ({a})" for d, a in verstoesse))
1975|     # (c) und (d) nur bei abgeschlossenem Lauf
1976|     rot, pruefen_code = "–", "–"
1977|     if abgeschlossen:
1978|         if handover_rel not in aenderungen or not (ROOT / handover_rel).is_file():
1979|             befunde.append(f"Handover {handover_rel} in diesem Lauf nicht geschrieben.")
1980|         elif nach_p and not re.search(rf"^## Nachbesserung {nb}\b",
1981|                                       (ROOT / handover_rel).read_text(encoding="utf-8"), re.M):
1982|             befunde.append(f"Handover {handover_rel} hat keinen Abschnitt '## Nachbesserung {nb}'.")
1983|         code = pruefen(kurztitel)
1984|         pruefen_code = str(code)
1985|         rot = _rot_aus_pruefung(kurztitel)
1986|         if code != 0:
1987|             befunde.append(f"pruefen: Exit {code}.")
1988|     else:
1989|         print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")
1990| 
1991|     exit_code = 1 if befunde else 0
1992|     reason = "timeout" if info["timeout"] else (info["reason"] or "–")
1993|     zeile = (f"- **{dt.datetime.now():%Y-%m-%d %H:%M}** – Modell: {modell}, Dauer: {info['dauer']} s, "
1994|              f"Tools: {info['werkzeuge']}, Fehler: {len(info['fehler'])}, Abgelehnt: {len(info['abgelehnt'])}, "
1995|              f"Tokens: {info['tokens']}, reason: {reason}, rot: {rot}, pruefen: {pruefen_code}, art: {art}, "
1996|              f"Exit: {exit_code}\n")
1997|     if not protokoll_p.exists():
1998|         protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
1999|                                encoding="utf-8")
2000|     tt = info["tokens_teile"]
2001|     zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}, spitze {info['tokens_spitze']}\n"
2002|     for e in info["fehler"]:
2003|         zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
2004|     with open(protokoll_p, "a", encoding="utf-8") as f:
2005|         f.write(zeile)
2006| 
2007|     print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
2008|     print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
2009|           f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']} (Spitze {info['tokens_spitze']}), reason {reason}")
2010|     for e in info["fehler"]:
2011|         print(f"  {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}")
2012|     if info["text"]:
2013|         print(f"Schlusstext: {info['text'][:300]}")
2014|     print(f"In diesem Lauf geändert: {', '.join(aenderungen) or 'nichts'}")
2015|     for b in befunde:
2016|         print(f"!!! {b}")
2017|     print(f"Rohdaten: {_rel(rohdaten)}\nProtokoll: {_rel(protokoll_p)}")
2018|     print(f"==> {'OK' if exit_code == 0 else 'NICHT IN ORDNUNG'} (Exit {exit_code})")
2019|     return exit_code
2020| 
2021| 
2022| # ---------------------------------------------------------------- main
```

### `tests/test_umsetzung_auto.py` class Basis (Zeilen 51–125) – Testaufbau T4

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
