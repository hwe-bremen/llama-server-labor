# Quellen Schritt 2 (8 ok, 4 schlecht)

- ZU LANG tests/test_umsetzung_auto.py (476 Zeilen)
- ZU LANG tests/test_kette_review_auto.py (517 Zeilen)
- ZU LANG tests/test_scout_bericht_ueberschreiben.py (614 Zeilen)
- ZU LANG tests/test_mail_planung.py (964 Zeilen)

### `role-split/kette/kette.py` def umsetzung_auto (Zeilen 1922–2106) – wie der Umsetzer aufgerufen wird und was als Exit 1 gilt

```python
1922| def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
1923|     """K10: Umsetzung bzw. Nacharbeit ueber `opencode run` ohne TUI, danach mechanisch pruefen.
1924|     Exit 0 = abgeschlossen + keine Verletzung + pruefen 0; 1 = Lauf/Pruefung nicht in Ordnung; 2 = Voraussetzung."""
1925|     def nein(meldung: str, code: int = 2) -> int:
1926|         print(meldung, file=sys.stderr)
1927|         return code
1928| 
1929|     # A2.1 Kurztitel
1930|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
1931|         return nein(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).")
1932|     # A2.2 Spec-Commit
1933|     commit = spec_commit(kurztitel)
1934|     if not commit:
1935|         return nein(f"Kein Commit 'Spec {kurztitel}' gefunden – erst die Spec committen.")
1936|     # A2.3 Spec mit Schreibbereich
1937|     spec_p = datei_suchen("spec", kurztitel, None)
1938|     if not spec_p:
1939|         return nein(f"Keine Spec spec_<datum>_{kurztitel}.md in {_rel(PM)}.")
1940|     bereich = _schreibbereich(spec_p.read_text(encoding="utf-8"))
1941|     if bereich is None:
1942|         return nein(f"Spec {spec_p.name} hat keinen Abschnitt '## Schreibbereich'. Spec um '## Schreibbereich' "
1943|                     "ergaenzen (Dateien/Ordner, die die Umsetzung aendern darf), sonst kein umsetzung-auto-Lauf.")
1944|     if not bereich:
1945|         return nein(f"'## Schreibbereich' in {spec_p.name} ist leer – mindestens einen Pfad eintragen.")
1946|     for e in bereich:
1947|         if _ist_vorgabe(e):
1948|             print(f"Hinweis: Schreibbereich nennt {e} – Vorgaben (spec_/anforderung_/quellen_/_vorlage_) "
1949|                   "sind nie erlaubt; eine Änderung daran endet in (b) mit Exit 1.", file=sys.stderr)
1950|     datum = _datum_aus(spec_p) or dt.date.today().strftime("%Y%m%d")
1951|     testdatei = f"tests/test_{kurztitel}.py"
1952|     handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
1953|     handover_rel = _ablage_text(handover_rel, kurztitel)
1954|     protokoll_p = ablage(kurztitel) / f"umsetzung_{datum}_{kurztitel}.md"
1955|     nach_p = None
1956|     if nacharbeit:
1957|         nach_p = Path(nacharbeit)
1958|         if not nach_p.is_absolute():
1959|             nach_p = (ROOT / nach_p) if (ROOT / nach_p).is_file() else nach_p.resolve()
1960|         if not nach_p.is_file():
1961|             return nein(f"Nacharbeitsdatei {nacharbeit} nicht gefunden.")
1962|     # A2.4 Arbeitsstand
1963|     offen = _offene_dateien()
1964|     if offen is None:
1965|         return nein("git status fehlgeschlagen – ist ROOT ein Git-Repo?")
1966|     if not nach_p:
1967|         if offen:
1968|             return nein("Arbeitsstand nicht sauber – ohne --nacharbeit muss alles committet sein:\n"
1969|                         + "\n".join(f"  {d}" for d in offen))
1970|     else:
1971|         try:
1972|             nach_rel = nach_p.resolve().relative_to(ROOT.resolve()).as_posix()
1973|         except ValueError:
1974|             nach_rel = None
1975|         fremd = [d for d in offen
1976|                  if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d == testdatei or d == handover_rel
1977|                                              or _ist_kettendatei(d, kurztitel) or d == nach_rel)]
1978|         if fremd:
1979|             return nein("Nacharbeit: unzulaessige offene Aenderungen (Vorgaben oder ausserhalb von Schreibbereich/"
1980|                         "Testdatei/Kettendateien):\n" + "\n".join(f"  {d}" for d in fremd))
1981|     # K11a: Vorgabe-Tests
1982|     vorgabe = _vorgabe_tests(spec_p.read_text(encoding="utf-8"))
1983|     if vorgabe:
1984|         if not (ROOT / testdatei).is_file():
1985|             return nein(f"Spec nennt '## Vorgabe-Tests', aber {testdatei} fehlt.")
1986|         if nach_p and testdatei in offen:
1987|             return nein(f"Nacharbeit: Vorgabe-Tests {testdatei} haben offene Aenderungen. Auf die Vorgabe zuruecksetzen (git restore {testdatei}) oder eine bewusste Korrektur committen – kein Lauf.")
1988|         if not nach_p and tests_pruefen(kurztitel) != 0:
1989|             return nein(f"Vorgabe-Tests nicht in Ordnung (kette.py tests-pruefen {kurztitel}) – kein Lauf.")
1990|     # A2.5 opencode
1991|     programm = _opencode_programm()
1992|     if not programm:
1993|         ziel = os.environ.get("KETTE_OPENCODE") or "opencode im PATH"
1994|         return nein(f"opencode nicht gefunden ({ziel}).")
1995|     # A2.6 Modell
1996|     modell = os.environ.get("KETTE_UMSETZUNG_MODEL", UMSETZUNG_MODELL_STANDARD)
1997|     if not modell.startswith("llamacpp/"):
1998|         return nein(f"Modell '{modell}' beginnt nicht mit 'llamacpp/' (nur direkt am Router, ohne Gedaechtnis).")
1999|     # A8 Halt-Regel und Nummer
2000|     zeilen = _protokoll(protokoll_p)
2001|     handover_p = ROOT / handover_rel
2002|     handover_alt = handover_p.read_text(encoding="utf-8") if handover_p.is_file() else ""
2003|     nb = len(re.findall(r"^## Nachbesserung\b", handover_alt, re.M)) + 1
2004|     if nach_p and _halt_noetig(zeilen):
2005|         return nein("Zwei Nachbesserungen in Folge ohne Fortschritt – keine weitere. Übergabe an Hawe.", 1)
2006|     art = f"nb{nb}" if nach_p else "erst"
2007|     # A3 Prompt
2008|     prompt_text = _umsetzung_prompt(kurztitel, datum, commit, nach_p, nb)
2009|     if prompt_text is None:
2010|         return nein(f"Prompt-Vorlage {_rel(PROMPTS / 'umsetzung_nacht.md')} fehlt.")
2011|     try:
2012|         timeout = int(os.environ.get("KETTE_UMSETZUNG_TIMEOUT", UMSETZUNG_TIMEOUT_STANDARD))
2013|         bash_ms = int(os.environ.get("OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS", UMSETZUNG_BASH_MS_STANDARD))
2014|     except ValueError:
2015|         return nein("KETTE_UMSETZUNG_TIMEOUT / OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS muessen ganze Zahlen sein.")
2016| 
2017|     # A7 Schnappschuss VOR dem Start
2018|     head_vor = _git("rev-parse", "HEAD").strip()
2019|     stand_vor = _stand()
2020|     if stand_vor is None:
2021|         return nein("git status fehlgeschlagen.")
2022|     befehl = programm + ["run", "--format", "json", "--agent", UMSETZUNG_AGENT, "--model", modell,
2023|                          "--dir", str(ROOT), "--title", f"kette {kurztitel} {art}", prompt_text]
2024|     env = dict(os.environ, OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=str(bash_ms))
2025|     rohdaten = ROOT / "role-split" / "results" / f"umsetzung_auto_{datum}_{kurztitel}_{dt.datetime.now():%H%M%S}.jsonl"
2026|     print(f"umsetzung-auto {kurztitel} ({art}): Modell {modell}, Agent {UMSETZUNG_AGENT}, "
2027|           f"Zeitlimit {timeout} s, Rücksetzpunkt {commit}", flush=True)
2028|     info = _lauf(befehl, env, timeout, rohdaten)
2029| 
2030|     # A7 Schnappschuss SOFORT nach dem Lauf, bevor kette.py selbst etwas schreibt
2031|     stand_nach = _stand() or {}
2032|     head_nach = _git("rev-parse", "HEAD").strip()
2033|     aenderungen = _in_diesem_lauf(stand_vor, stand_nach)
2034|     abgeschlossen = not info["timeout"] and info["reason"] == "stop"
2035|     befunde = []
2036| 
2037|     if info.get("haengt"):
2038|         befunde.append("opencode reagiert 30 s nach SIGKILL nicht – Prozess pruefen (ps).")
2039|     if info.get("startfehler"):
2040|         befunde.append(f"opencode liess sich nicht starten: {info['startfehler']}")
2041|     elif info["timeout"]:
2042|         befunde.append(f"Timeout nach {timeout} s – opencode samt Unterprozessen beendet.")
2043|     elif info["ereignisse"] == 0:
2044|         befunde.append("Keine gültigen JSON-Ereignisse von opencode.")
2045|     elif info["reason"] != "stop":
2046|         befunde.append(f"Lauf nicht abgeschlossen (reason: {info['reason']}).")
2047|     # (a) immer
2048|     if head_vor != head_nach:
2049|         befunde.append(f"Selbst-Commit: HEAD {head_vor[:7]} -> {head_nach[:7]} (nichts zurückgesetzt).")
2050|     # (b) immer
2051|     if vorgabe and testdatei in aenderungen:
2052|         befunde.append(f"Vorgabe-Tests in diesem Lauf geändert: {testdatei} ({aenderungen[testdatei]}) – "
2053|                        "nichts zurückgesetzt.")
2054|     verstoesse = [(d, a) for d, a in aenderungen.items()
2055|                   if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d in (testdatei, handover_rel))]
2056|     if verstoesse:
2057|         befunde.append("Schreibbereich verletzt (nichts zurückgesetzt):\n"
2058|                        + "\n".join(f"  {d} ({a})" for d, a in verstoesse))
2059|     # (c) und (d) nur bei abgeschlossenem Lauf
2060|     rot, pruefen_code = "–", "–"
2061|     if abgeschlossen:
2062|         if handover_rel not in aenderungen or not (ROOT / handover_rel).is_file():
2063|             befunde.append(f"Handover {handover_rel} in diesem Lauf nicht geschrieben.")
2064|         elif nach_p and not re.search(rf"^## Nachbesserung {nb}\b",
2065|                                       (ROOT / handover_rel).read_text(encoding="utf-8"), re.M):
2066|             befunde.append(f"Handover {handover_rel} hat keinen Abschnitt '## Nachbesserung {nb}'.")
2067|         code = pruefen(kurztitel)
2068|         pruefen_code = str(code)
2069|         rot = _rot_aus_pruefung(kurztitel)
2070|         if code != 0:
2071|             befunde.append(f"pruefen: Exit {code}.")
2072|     else:
2073|         print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")
2074| 
2075|     exit_code = 1 if befunde else 0
2076|     reason = "timeout" if info["timeout"] else (info["reason"] or "–")
2077|     zeile = (f"- **{dt.datetime.now():%Y-%m-%d %H:%M}** – Modell: {modell}, Dauer: {info['dauer']} s, "
2078|              f"Tools: {info['werkzeuge']}, Fehler: {len(info['fehler'])}, Abgelehnt: {len(info['abgelehnt'])}, "
2079|              f"Tokens: {info['tokens']}, reason: {reason}, rot: {rot}, pruefen: {pruefen_code}, art: {art}, "
2080|              f"Exit: {exit_code}\n")
2081|     if not protokoll_p.exists():
2082|         protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
2083|                                encoding="utf-8")
2084|     tt = info["tokens_teile"]
2085|     zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}, spitze {info['tokens_spitze']}\n"
2086|     for e in info["fehler"]:
2087|         zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
2088|     with open(protokoll_p, "a", encoding="utf-8") as f:
2089|         f.write(zeile)
2090| 
2091|     print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
2092|     print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
2093|           f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']} (Spitze {info['tokens_spitze']}), reason {reason}")
2094|     for e in info["fehler"]:
2095|         print(f"  {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}")
2096|     if info["text"]:
2097|         print(f"Schlusstext: {info['text'][:300]}")
2098|     print(f"In diesem Lauf geändert: {', '.join(aenderungen) or 'nichts'}")
2099|     for b in befunde:
2100|         print(f"!!! {b}")
2101|     print(f"Rohdaten: {_rel(rohdaten)}\nProtokoll: {_rel(protokoll_p)}")
2102|     print(f"==> {'OK' if exit_code == 0 else 'NICHT IN ORDNUNG'} (Exit {exit_code})")
2103|     return exit_code
2104| 
2105| 
2106| # ---------------------------------------------------------------- main
```

### `role-split/kette/kette.py` def _im_schreibbereich (Zeilen 1641–1643) – wie der Schreibbereich geprüft wird (hier muss die neue Prüfung integriert werden)

```python
1641| def _im_schreibbereich(pfad: str, eintraege: list[str]) -> bool:
1642|     """Exakter Dateipfad oder Ordner-Eintrag mit '/' am Ende als Praefix."""
1643|     return any(pfad == e or (e.endswith("/") and pfad.startswith(e)) for e in eintraege)
```

### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1629–1638) – wo der Schreibbereich definiert wird

```python
1629| def _schreibbereich(spec_text: str) -> list[str] | None:
1630|     """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
1631|     if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
1632|         return None
1633|     eintraege = []
1634|     for z in abschnitt(spec_text, "Schreibbereich").splitlines():
1635|         m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
1636|         if m:
1637|             eintraege.append(m.group(1)[2:] if m.group(1).startswith("./") else m.group(1))
1638|     return eintraege
```

### `role-split/kette/kette.py` def _git (Zeilen 653–654) – wie Git-Befehle ausgeführt werden (für die Prüfung)

```python
653| def _git(*a: str) -> str:
654|     return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
```

### `role-split/kette/kette.py` def pruefen (Zeilen 615–642) – wie die Prüfung durchgeführt wird

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

### `role-split/kette/kette.py` def gegenprobe (Zeilen 432–489) – wie die Gegenprobe funktioniert (muss auch die neue Prüfung abdecken)

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

### `tests/test_vorgabe_tests.py` (Zeilen 1–174) – Struktur der Vorgabe-Tests

```python
  1| #!/usr/bin/env python3
  2| """Vorgabe-Tests fuer K11a vorgabe_tests (spec_20261027_vorgabe_tests.md, T1–T8).
  3| 
  4| VORGABE: Diese Datei hat Claude vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.
  5| 
  6| Keine Aussenwirkung: T1–T5 arbeiten in tempfile.TemporaryDirectory() mit umgebogenem kette.ROOT/kette.PM;
  7| T6–T8 nutzen die Testklasse Basis aus tests/test_umsetzung_auto.py (eigenes Temp-Git-Repo, Attrappe
  8| opencode_fake.py mit Temp-Sperre, Pruefung am Ende, dass das echte Repo unveraendert ist).
  9| Neue Funktionen werden in den Methoden importiert, damit die Gegenprobe je Test aussagekraeftig ist.
 10| """
 11| import io
 12| import json
 13| import sys
 14| import tempfile
 15| import unittest
 16| from contextlib import redirect_stderr, redirect_stdout
 17| from pathlib import Path
 18| 
 19| ECHT = Path(__file__).resolve().parent.parent
 20| sys.path.insert(0, str(ECHT))
 21| sys.path.insert(0, str(ECHT / "role-split" / "kette"))
 22| import kette  # noqa: E402
 23| from tests.test_umsetzung_auto import Basis, DATUM, HANDOVER  # noqa: E402
 24| 
 25| SPEC_K = ("# Spec: k\n\n## Ziel\nx\n\n## Vorgabe-Tests\n\n- `tests/test_k.py`\n\n"
 26|           "## Testplan\n\n### T1: Erster\n- **Erwartung:** a\n\n### T2: Zweiter\n- **Erwartung:** b\n")
 27| # Beide Tests rot ohne Umsetzung: neue Funktion wird in der Methode importiert.
 28| ROT = ("import unittest\n\nclass K(unittest.TestCase):\n"
 29|        "    def test_t1_erster(self):\n        from neu import f\n        self.assertEqual(f(), 1)\n\n"
 30|        "    def test_t2_zweiter(self):\n        from neu import g\n        self.assertEqual(g(), 2)\n")
 31| 
 32| 
 33| class Temp(unittest.TestCase):
 34|     def setUp(self):
 35|         d = tempfile.TemporaryDirectory()
 36|         self.addCleanup(d.cleanup)
 37|         self.root = Path(d.name).resolve()
 38|         self.pm = self.root / "docs" / "projekt_management"
 39|         self.pm.mkdir(parents=True)
 40|         (self.root / "tests").mkdir()
 41|         for name, wert in (("ROOT", self.root), ("PM", self.pm)):
 42|             alt = getattr(kette, name)
 43|             setattr(kette, name, wert)
 44|             self.addCleanup(setattr, kette, name, alt)
 45|         (self.pm / "spec_20261028_k.md").write_text(SPEC_K, encoding="utf-8")
 46| 
 47|     def schreibe_testdatei(self, text: str):
 48|         (self.root / "tests" / "test_k.py").write_text(text, encoding="utf-8")
 49| 
 50|     def rufen(self, fn, *a):
 51|         aus = io.StringIO()
 52|         with redirect_stdout(aus), redirect_stderr(aus):
 53|             code = fn(*a)
 54|         return code, aus.getvalue()
 55| 
 56| 
 57| class TestsPruefen(Temp):
 58| 
 59|     def test_t1_tests_pruefen_rot_vorab_ok(self):
 60|         """T1: tests-pruefen – alle Vorgabe-Tests vorhanden und rot vorab"""
 61|         from kette import tests_pruefen
 62|         self.schreibe_testdatei(ROT)
 63|         code, out = self.rufen(tests_pruefen, "k")
 64|         self.assertEqual(code, 0, out)
 65|         self.assertIn("rot       T1", out)
 66|         self.assertIn("rot       T2", out)
 67|         self.assertIn("Keine Abweichung.", out)
 68|         code2, out2 = self.rufen(kette.main, ["tests-pruefen", "k"])
 69|         self.assertEqual(code2, 0, out2)
 70| 
 71|     def test_t2_tests_pruefen_test_fehlt(self):
 72|         """T2: tests-pruefen – Test-ID ohne Methode"""
 73|         from kette import tests_pruefen
 74|         self.schreibe_testdatei(ROT.split("    def test_t2_zweiter")[0])
 75|         code, out = self.rufen(tests_pruefen, "k")
 76|         self.assertEqual(code, 1, out)
 77|         self.assertIn("FEHLT     T2", out)
 78|         self.assertIn("rot       T1", out)
 79| 
 80|     def test_t3_tests_pruefen_gruen_ohne_umsetzung(self):
 81|         """T3: tests-pruefen – Test ohne Umsetzung schon gruen"""
 82|         from kette import tests_pruefen
 83|         self.schreibe_testdatei(ROT.replace("from neu import f\n        self.assertEqual(f(), 1)",
 84|                                          "self.assertEqual(1, 1)"))
 85|         code, out = self.rufen(tests_pruefen, "k")
 86|         self.assertEqual(code, 1, out)
 87|         self.assertIn("NICHT ROT T1", out)
 88|         self.assertIn("rot       T2", out)
 89| 
 90|     def test_t4_tests_pruefen_laedt_nicht(self):
 91|         """T4: tests-pruefen – Testskript laedt nicht"""
 92|         from kette import tests_pruefen
 93|         self.schreibe_testdatei("from neu import f\n" + ROT)
 94|         code, out = self.rufen(tests_pruefen, "k")
 95|         self.assertEqual(code, 1, out)
 96|         self.assertIn("LAEDT NICHT", out)
 97|         self.assertNotIn("rot       T1", out)
 98| 
 99|     def test_t5_tests_pruefen_voraussetzung_fehlt(self):
100|         """T5: tests-pruefen – Testdatei oder Spec fehlt"""
101|         from kette import tests_pruefen
102|         code, out = self.rufen(tests_pruefen, "k")
103|         self.assertEqual(code, 2, out)
104|         self.assertIn("tests/test_k.py", out)
105|         self.schreibe_testdatei(ROT)
106|         (self.pm / "spec_20261028_k.md").unlink()
107|         code, out = self.rufen(tests_pruefen, "k")
108|         self.assertEqual(code, 2, out)
109| 
110| 
111| SPEC_VORGABE = (
112|     "# Spec: g\n\n## Ziel\nTest.\n\n## Schreibbereich\n\n"
113|     "- `src/`\n- `role-split/kette/`\n- `docs/projekt_management/`\n- `tests/`\n\n"
114|     "## Vorgabe-Tests\n\n- `tests/test_g.py`\n\n"
115|     "## Testplan\n\n### T1: Erster\n- **Erwartung:** x\n"
116| )
117| ROT_G = ("import unittest\n\nclass G(unittest.TestCase):\n"
118|          "    def test_t1_erster(self):\n        from src.neu import f\n        self.assertEqual(f(), 1)\n")
119| GRUEN_G = ROT_G.replace("from src.neu import f\n        self.assertEqual(f(), 1)", "self.assertTrue(True)")
120| 
121| 
122| class UmsetzungMitVorgabe(Basis):
123| 
124|     def vorgabe(self, testcode: str, spec: str = SPEC_VORGABE, nachricht: str = "Tests g"):
125|         (self.pm / f"spec_{DATUM}_g.md").write_text(spec, encoding="utf-8")
126|         (self.root / "tests").mkdir(exist_ok=True)
127|         (self.root / "tests" / "test_g.py").write_text(testcode, encoding="utf-8")
128|         self.git("add", ".")
129|         self.git("commit", "-qm", nachricht)
130| 
131|     def prompt_text(self) -> str:
132|         return json.loads(self.argsdatei.read_text(encoding="utf-8"))[-1]
133| 
134|     def test_t6_erstlauf_nur_mit_rot_vorab(self):
135|         """T6: umsetzung-auto – Erstlauf startet nur mit bestandener Testpruefung"""
136|         self.vorgabe(GRUEN_G)
137|         code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
138|         self.assertEqual(code, 2, out)
139|         self.assertFalse(self.gestartet(), out)
140|         self.assertIn("NICHT ROT T1", out)
141|         self.vorgabe(ROT_G)
142|         code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
143|         self.assertEqual(code, 0, out)
144|         self.assertTrue(self.gestartet(), out)
145|         self.assertIn("## Vorgabe-Tests", self.prompt_text())
146|         self.assertIn("Du änderst diese Datei nicht", self.prompt_text())
147| 
148|     def test_t7_vorgabe_tests_geaendert(self):
149|         """T7: umsetzung-auto – Aenderung an Vorgabe-Tests ist ein Verstoss"""
150|         # Gegenfall zuerst: ohne Abschnitt Vorgabe-Tests darf der Umsetzer die Testdatei schreiben.
151|         code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_EDIT="tests/test_g.py")
152|         self.assertEqual(code, 0, out)
153|         self.assertNotIn("Vorgabe-Tests", out)
154|         self.assertNotIn("## Vorgabe-Tests", self.prompt_text())
155|         self.argsdatei.unlink()
156|         self.vorgabe(ROT_G, nachricht="zwischen")
157|         code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_EDIT="tests/test_g.py")
158|         self.assertEqual(code, 1, out)
159|         self.assertIn("Vorgabe-Tests in diesem Lauf geändert: tests/test_g.py", out)
160|         self.assertNotIn("Schreibbereich verletzt", out)
161| 
162|     def test_t8_nacharbeit_ohne_rot_vorab(self):
163|         """T8: umsetzung-auto – Nacharbeit prueft nicht auf rot vorab, Prompt nennt Vorgabe"""
164|         self.vorgabe(GRUEN_G)
165|         datei = self.nacharbeit_vorbereiten()
166|         code, out = self.lauf(nacharbeit=str(datei), FAKE_HANDOVER=HANDOVER, FAKE_NACHBESSERUNG=1)
167|         self.assertTrue(self.gestartet(), out)
168|         self.assertEqual(code, 0, out)
169|         self.assertNotIn("NICHT ROT", out)
170|         self.assertIn("## Vorgabe-Tests", self.prompt_text())
171| 
172| 
173| if __name__ == "__main__":
174|     unittest.main()
```

### `tests/test_paket_vollstaendig.py` (Zeilen 1–228) – Struktur des Review-Pakets

```python
  1| #!/usr/bin/env python3
  2| """Tests fuer Spec paket_vollstaendig (K9), Testplan T1–T9 plus Zusatztests K1–K2.
  3| 
  4| Jeder Test baut ein Wegwerf-Git-Repo und prueft Verhalten (Paketinhalt, Exit-Code, Gegenprobe),
  5| nicht den Quelltext. Laeuft ab Python 3.10. Geschrieben von Claude (Uebernahme NB2, 26.10.).
  6| """
  7| import io
  8| import subprocess
  9| import sys
 10| import tempfile
 11| import unittest
 12| from contextlib import redirect_stdout
 13| from pathlib import Path
 14| 
 15| PROJ = Path(__file__).resolve().parent.parent
 16| sys.path.insert(0, str(PROJ / "role-split" / "kette"))
 17| import kette  # noqa: E402
 18| 
 19| 
 20| def lauf(fn, *a, **kw):
 21|     buf = io.StringIO()
 22|     with redirect_stdout(buf):
 23|         code = fn(*a, **kw)
 24|     return code, buf.getvalue()
 25| 
 26| 
 27| class Basis(unittest.TestCase):
 28|     """Repo mit Spec-Datei und Commit 'Spec g' als Ruecksetzpunkt."""
 29| 
 30|     def setUp(self):
 31|         d = tempfile.TemporaryDirectory()
 32|         self.addCleanup(d.cleanup)
 33|         self.root = Path(d.name)
 34|         self.git("init", "-q")
 35|         self.pm = self.root / "docs" / "projekt_management"
 36|         self.pm.mkdir(parents=True)
 37|         (self.pm / "spec_20261026_g.md").write_text(
 38|             "# Spec\n\n## Ziel\nZ\n\n## Nicht-Ziele\nN\n\n## Anforderungen\n### A1: Eins\nX\n\n"
 39|             "## Testplan\n### T1: Erster\n- **Erwartung:** E\n\n## Offene Fragen\nO\n", encoding="utf-8")
 40|         self.schreibe("mod.py", "def f():\n    return 1\n")
 41|         self.git("add", "-A")
 42|         self.git("commit", "-qm", "Spec g")
 43|         self.spec_commit = self.git("rev-parse", "--short", "HEAD").strip()
 44|         for name, wert in (("ROOT", self.root), ("PM", self.pm)):
 45|             alt = getattr(kette, name)
 46|             setattr(kette, name, wert)
 47|             self.addCleanup(setattr, kette, name, alt)
 48| 
 49|     def git(self, *a):
 50|         return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
 51|                               check=True, capture_output=True, text=True).stdout
 52| 
 53|     def schreibe(self, rel, inhalt):
 54|         p = self.root / rel
 55|         p.parent.mkdir(parents=True, exist_ok=True)
 56|         p.write_text(inhalt, encoding="utf-8")
 57| 
 58|     def commit(self, nachricht, **dateien):
 59|         for rel, inhalt in dateien.items():
 60|             self.schreibe(rel.replace("__", "/"), inhalt)
 61|         self.git("add", "-A")
 62|         self.git("commit", "-qm", nachricht)
 63| 
 64|     def handover(self, *dateien):
 65|         zeilen = "".join(f"- `{d}` – x\n" for d in dateien)
 66|         (self.pm / "handover_20261026_g.md").write_text(
 67|             f"# HO\n## Geänderte und neue Dateien\n{zeilen}\n## Abweichungen\nkeine\n", encoding="utf-8")
 68| 
 69|     def paket(self, **kw):
 70|         code, out = lauf(kette.paket, "g", **kw)
 71|         ziel = self.pm / "review_paket_20261026_g.md"
 72|         text = ziel.read_text(encoding="utf-8") if ziel.exists() else None
 73|         return code, out, text
 74| 
 75|     @staticmethod
 76|     def code_teil(text):
 77|         rest = text.split("## 3. Code-Aenderungen")[1]
 78|         for ende in ("## 3a.", "## 3b.", "## 4."):
 79|             if ende in rest:
 80|                 rest = rest.split(ende)[0]
 81|         return rest
 82| 
 83|     @staticmethod
 84|     def markiert(code_teil):
 85|         return {b.split(" ")[0] for b in code_teil.split("### ")[1:] if "nicht in der Uebergabe genannt" in b}
 86| 
 87| 
 88| class TestPaketVollstaendig(Basis):
 89| 
 90|     def test_t1_fehlerpfade_von_paket(self):
 91|         """T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)"""
 92|         code, out = lauf(kette.paket, "G-1")
 93|         self.assertEqual(code, 2); self.assertIn("ungueltig", out)
 94|         code, out = lauf(kette.paket, "nichtda")
 95|         self.assertEqual(code, 2); self.assertIn("Keine Spec", out)
 96|         (self.pm / "spec_20261026_ohne.md").write_text("# Spec\n", encoding="utf-8")
 97|         code, out = lauf(kette.paket, "ohne")
 98|         self.assertEqual(code, 2); self.assertIn("Kein Commit 'Spec ohne'", out)
 99|         code, out = lauf(kette.paket, "g", commit="deadbeefdeadbeef")
100|         self.assertEqual(code, 2); self.assertIn("git-Fehler", out)
101|         self.assertEqual(list(self.pm.glob("review_paket_*")), [])
102| 
103|     def test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte(self):
104|         """T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte"""
105|         self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
106|         self.schreibe("tests/test_g.py", "import unittest\n")                       # unversioniert
107|         self.schreibe("tests/daten/x.json", '{"a": 1}\n')                            # unversioniert
108|         self.schreibe("role-split/kette/hilfs.py", "H = 1\n")
109|         self.git("add", "role-split/kette/hilfs.py")                                 # nur vorgemerkt
110|         self.schreibe("role-split/rollen/r.md", "# Rolle R\n")                       # .md unter role-split
111|         self.handover("mod.py")
112|         code, out, text = self.paket()
113|         self.assertEqual(code, 0, out)
114|         teil = self.code_teil(text)
115|         for d in ("mod.py", "tests/test_g.py", "tests/daten/x.json", "role-split/kette/hilfs.py",
116|                   "role-split/rollen/r.md"):
117|             self.assertIn(f"### {d} ", teil, d)
118|         self.assertEqual(self.markiert(teil), {"tests/test_g.py", "tests/daten/x.json",
119|                                                "role-split/kette/hilfs.py", "role-split/rollen/r.md"})
120| 
121|     def test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung(self):
122|         """T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung"""
123|         self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
124|         self.schreibe("tests/test_g.py", "import unittest\n")
125|         self.schreibe("role-split/kette/hilfs.py", "H = 1\n")
126|         self.handover("mod.py", "tests/test_g.py")
127|         code, out, text = self.paket()
128|         self.assertEqual(code, 0, out)
129|         self.assertEqual(self.markiert(self.code_teil(text)), {"role-split/kette/hilfs.py"})
130| 
131|     def test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen(self):
132|         """T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen"""
133|         self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
134|         self.schreibe("tests/test_g.py", "import unittest\n")
135|         zeile = "Testzeile mit Inhalt fuer eine grosse Datei\n"
136|         self.schreibe("tests/daten/gross.eml", zeile * 2500)          # ~110 000 Zeichen, Vorrang 3
137|         alt = kette.PAKET_DATEI_ZEILEN
138|         kette.PAKET_DATEI_ZEILEN = 5000
139|         self.addCleanup(setattr, kette, "PAKET_DATEI_ZEILEN", alt)
140|         self.handover("mod.py")
141|         code, out, text = self.paket()
142|         self.assertEqual(code, 0, out)
143|         teil = self.code_teil(text)
144|         self.assertIn("### mod.py ", teil)
145|         self.assertIn("### tests/test_g.py ", teil)                    # Vorrang 2 bleibt, reicht schon
146|         self.assertNotIn("gross.eml", teil)
147|         weg = text.split("## 3b.")[1].split("## 4.")[0]
148|         self.assertIn("`tests/daten/gross.eml` – Testdaten", weg)
149|         self.assertLessEqual(len(text), kette.PAKET_WARNUNG_ZEICHEN)
150| 
151|     def test_t5_kette_paket_max_ueberschritten_exit_1(self):
152|         """T5: KETTE_PAKET_MAX überschritten → Exit 1"""
153|         self.commit("g: mod", **{"mod.py": "".join(f"def f{i}():\n    return {i}\n" for i in range(300))})
154|         self.handover("mod.py")
155|         alt = kette.KETTE_PAKET_MAX
156|         kette.KETTE_PAKET_MAX = 3000
157|         self.addCleanup(setattr, kette, "KETTE_PAKET_MAX", alt)
158|         code, out, text = self.paket()
159|         self.assertEqual(code, 1, out)
160|         self.assertIn("passt nicht in den Kontext", out)
161|         self.assertIsNone(text)
162| 
163|     def test_t6_gegenprobe_beruecksichtigt_role_split_kette(self):
164|         """T6: Gegenprobe berücksichtigt role-split/kette/"""
165|         self.commit("Werkzeug: fremd", **{"fremd.py": "F = 5\n"})
166|         self.commit("g: hilfs", **{"role-split__kette__hilfs.py": "H = 7\n"})
167|         self.schreibe("tests/test_g.py",
168|                       "import sys, unittest\nfrom pathlib import Path\n"
169|                       "R = Path(__file__).resolve().parent.parent\n"
170|                       "sys.path.insert(0, str(R / 'role-split' / 'kette')); sys.path.insert(0, str(R))\n"
171|                       "class T(unittest.TestCase):\n"
172|                       "    def test_t1_hilfs(self):\n        import hilfs\n        self.assertEqual(hilfs.H, 7)\n"
173|                       "    def test_t2_fremd(self):\n        import fremd\n        self.assertEqual(fremd.F, 5)\n")
174|         code, out = lauf(kette.gegenprobe, "g", self.spec_commit)
175|         self.assertIn("rot   test_t1_hilfs  <- hilfs.py", out)
176|         self.assertIn("GRUEN test_t2_fremd", out)                     # fremde Datei nicht zurueckgesetzt
177|         self.assertNotIn("fremd.py:", out)
178|         self.assertEqual((self.root / "role-split/kette/hilfs.py").read_text(), "H = 7\n")
179| 
180|     def test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen(self):
181|         """T7: Bestehende Tests in test_kette.py bleiben grün"""
182|         r = subprocess.run([sys.executable, str(PROJ / "role-split" / "kette" / "test_kette.py")],
183|                            capture_output=True, text=True, timeout=300)
184|         self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-2000:])
185| 
186|     def test_t8_fremde_commits_nur_als_liste(self):
187|         """T8: Fremde Commits nur als Liste"""
188|         self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
189|         self.commit("Werkzeug: x", **{"werkzeug.py": "GEHEIMER_INHALT = 1\n", "anderes.py": "A = 1\n"})
190|         self.handover("mod.py", "anderes.py")
191|         code, out, text = self.paket()
192|         self.assertEqual(code, 0, out)
193|         teil = self.code_teil(text)
194|         self.assertIn("### mod.py ", teil)
195|         self.assertIn("### anderes.py ", teil)                          # fremd, aber in der Uebergabe
196|         self.assertNotIn("GEHEIMER_INHALT", text)
197|         fremd = text.split("## 3a.")[1].split("## 4.")[0]
198|         self.assertIn("`werkzeug.py`", fremd)
199|         self.assertIn("Werkzeug: x", fremd)
200|         self.assertNotIn("anderes.py", fremd)
201| 
202|     def test_t9_paket_ohne_code_trotz_aenderungen_exit_1(self):
203|         """T9: Paket ohne Code trotz Änderungen → Exit 1"""
204|         self.commit("Werkzeug: x", **{"mod.py": "def f():\n    return 9\n"})
205|         code, out, text = self.paket()
206|         self.assertEqual(code, 1, out)
207|         self.assertIn("Paket ohne Code trotz Aenderungen", out)
208|         self.assertIsNone(text)
209| 
210|     def test_k1_nur_docs_geaendert_exit_0(self):
211|         """K1: Nur docs/ geaendert -> Exit 0, 'keine Code-Dateien'"""
212|         self.commit("g: doku", **{"docs__notiz.md": "x\n"})
213|         code, out, text = self.paket()
214|         self.assertEqual(code, 0, out)
215|         self.assertIn("Geaenderte Code-Dateien: keine", text)
216| 
217|     def test_k2_kurztitel_als_ganzes_wort(self):
218|         """K2: Kurztitel 'g' trifft nicht 'gross' -> Datei aus 'gross init' ist fremd"""
219|         self.commit("gross init", **{"gross.py": "G = 1\n"})
220|         self.commit("g: mod", **{"mod.py": "def f():\n    return 2\n"})
221|         code, out, text = self.paket()
222|         self.assertEqual(code, 0, out)
223|         self.assertIn("`gross.py`", text.split("## 3a.")[1].split("## 4.")[0])
224|         self.assertNotIn("### gross.py", self.code_teil(text))
225| 
226| 
227| if __name__ == "__main__":
228|     unittest.main()
```
