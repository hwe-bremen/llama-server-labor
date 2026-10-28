# Quellen: lauf_status

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen lauf_status` (2026-10-28 12:01, Stand `1cd414b`), nach dem Abschnitt „Quellen“ in `spec_20261028_lauf_status.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1587–1596) – Einträge des Schreibbereichs (C1)

```python
1587| def _schreibbereich(spec_text: str) -> list[str] | None:
1588|     """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
1589|     if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
1590|         return None
1591|     eintraege = []
1592|     for z in abschnitt(spec_text, "Schreibbereich").splitlines():
1593|         m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
1594|         if m:
1595|             eintraege.append(m.group(1)[2:] if m.group(1).startswith("./") else m.group(1))
1596|     return eintraege
```

### `role-split/kette/kette.py` def abschnitt (Zeilen 97–100) – Inhalt unter einer `##`-Überschrift (C1)

```python
 97| def abschnitt(text: str, titel: str) -> str:
 98|     """Inhalt unter '## <titel...>' bis zur naechsten '## '-Ueberschrift ('' wenn fehlt)."""
 99|     m = re.search(rf"^##\s+{re.escape(titel)}[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
100|     return m.group(1) if m else ""
```

### `role-split/kette/kette.py` def tests_finden (Zeilen 208–219) – Test-IDs der Spec (C1)

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

### `role-split/kette/kette.py` def datei_suchen (Zeilen 266–273) – Kettendateien zum Kurztitel (C2, C3)

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

### `role-split/kette/kette.py` def spec_commit (Zeilen 529–537) – Commit „Spec <kt>“ (C2, C3)

```python
529| def spec_commit(kurztitel: str) -> str | None:
530|     """Aeltester Commit, dessen Betreffzeile genau "Spec <kurztitel>" ist (= Ruecksetzpunkt)."""
531|     r = subprocess.run(["git", "-C", str(ROOT), "log", "--format=%h%x09%s"],
532|                        capture_output=True, text=True)
533|     if r.returncode != 0:
534|         return None
535|     treffer = [z.split("\t", 1)[0] for z in r.stdout.splitlines()
536|                if "\t" in z and z.split("\t", 1)[1].strip() == f"Spec {kurztitel}"]
537|     return treffer[-1] if treffer else None
```

### `role-split/kette/kette.py` def _vorgabe_tests (Zeilen 470–472) – Abschnitt `## Vorgabe-Tests` (C2, C3)

```python
470| def _vorgabe_tests(spec_text: str) -> bool:
471|     """Wahr, wenn die Spec den Abschnitt '## Vorgabe-Tests' hat (Tests vorab, Umsetzer schreibt nur Code)."""
472|     return re.search(r"^##\s+Vorgabe-Tests\s*$", spec_text, re.M) is not None
```

### `role-split/kette/kette.py` def _datum_aus (Zeilen 1002–1004) – Datum aus dem Spec-Dateinamen (C3)

```python
1002| def _datum_aus(pfad: Path | None) -> str | None:
1003|     m = re.search(r"_(\d{8})_", pfad.name) if pfad else None
1004|     return m.group(1) if m else None
```

### `role-split/kette/kette.py` def umsetzung_auto (Zeilen 1868–2051) – Exit 0/1/2 (C2)

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

### `role-split/kette/kette.py` def review_auto (Zeilen 1435–1575) – Exit 0/1/2, schreibt `gesamt_<datum>_<kt>.md` (C2, C3)

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

### `role-split/kette/kette.py` def main (Zeilen 2053–2106) – Subparser (C5)

```python
2053| def main(argv=None) -> int:
2054|     ap = argparse.ArgumentParser(description="Werkzeug fuer die Kette Spec -> Umsetzung -> Review")
2055|     sub = ap.add_subparsers(dest="cmd", required=True)
2056|     p = sub.add_parser("prompt"); p.add_argument("schritt", choices=SCHRITTE); p.add_argument("kurztitel")
2057|     p.add_argument("--datum"); p.add_argument("--commit")
2058|     p.add_argument("--lauf", type=int, help="Review-Lauf-Nummer (eigener Verdikt-Dateiname je Lauf)")
2059|     q = sub.add_parser("quellen"); q.add_argument("kurztitel"); q.add_argument("--datum")
2060|     n = sub.add_parser("anforderung"); n.add_argument("kurztitel")
2061|     n.add_argument("--aufgabe"); n.add_argument("--antwort"); n.add_argument("--frage"); n.add_argument("--datum")
2062|     a = sub.add_parser("abgleich"); a.add_argument("kurztitel"); a.add_argument("--datum")
2063|     u = sub.add_parser("urteil"); u.add_argument("verdikt"); u.add_argument("--anhaengen", action="store_true")
2064|     g = sub.add_parser("gegenprobe"); g.add_argument("kurztitel")
2065|     g.add_argument("--commit", required=True, help="Ruecksetzpunkt vor der Umsetzung")
2066|     g.add_argument("--timeout", type=int, default=300)
2067|     zf = sub.add_parser("zusammenfuehren", help="Befunde mehrerer Review-Laeufe mechanisch zusammenfuehren")
2068|     zf.add_argument("verdikte", nargs="+")
2069|     pk = sub.add_parser("paket", help="Review-Paket bauen (eine Datei fuers Review)")
2070|     pk.add_argument("kurztitel"); pk.add_argument("--commit"); pk.add_argument("--datum")
2071|     pr = sub.add_parser("pruefen", help="abgleich + unittest + gegenprobe, Ausgabe in Datei")
2072|     pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
2073|     ra = sub.add_parser("review-auto", help="Review-Paket, zwei API-Laeufe, Verdikte, Zusammenfassung")
2074|     ra.add_argument("kurztitel")
2075|     ua = sub.add_parser("umsetzung-auto", help="Umsetzung/Nacharbeit ueber opencode run ohne TUI, danach pruefen")
2076|     ua.add_argument("kurztitel"); ua.add_argument("--nacharbeit", help="Datei mit dem Nachbesserungs-Auftrag")
2077|     tp = sub.add_parser("tests-pruefen", help="Vorgabe-Tests pruefen: Abdeckung, laedt, rot vorab")
2078|     tp.add_argument("kurztitel"); tp.add_argument("--timeout", type=int, default=300)
2079|     args = ap.parse_args(argv)
2080|     if args.cmd == "zusammenfuehren":
2081|         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
2082|                                 for v in args.verdikte])
2083|     if args.cmd == "paket":
2084|         return paket(args.kurztitel, args.commit, args.datum)
2085|     if args.cmd == "pruefen":
2086|         return pruefen(args.kurztitel, args.commit, args.timeout)
2087|     if args.cmd == "review-auto":
2088|         return review_auto(args.kurztitel)
2089|     if args.cmd == "umsetzung-auto":
2090|         return umsetzung_auto(args.kurztitel, args.nacharbeit)
2091|     if args.cmd == "tests-pruefen":
2092|         return tests_pruefen(args.kurztitel, args.timeout)
2093|     if args.cmd == "gegenprobe":
2094|         return gegenprobe(args.kurztitel, args.commit, args.timeout)
2095|     if args.cmd == "quellen":
2096|         return quellen(args.kurztitel, args.datum)
2097|     if args.cmd == "anforderung":
2098|         return anforderung(args.kurztitel, args.aufgabe, args.antwort, args.frage, args.datum)
2099|     if args.cmd == "prompt":
2100|         return prompt(args.schritt, args.kurztitel, args.datum, args.commit, args.lauf)
2101|     if args.cmd == "abgleich":
2102|         return abgleich(args.kurztitel, args.datum)
2103|     pfad = Path(args.verdikt)
2104|     if not pfad.is_absolute() and not pfad.exists():
2105|         pfad = PM / pfad.name
2106|     return urteil(pfad, args.anhaengen)
```
