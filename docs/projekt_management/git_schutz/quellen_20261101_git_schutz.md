# Quellen: git_schutz

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen git_schutz` (2026-11-01 18:56, Stand `662a444`), nach dem Abschnitt „Quellen“ in `spec_20261101_git_schutz.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` (Zeilen 1619–1626) – Konstanten der Umsetzung; `GIT_SCHUTZ` kommt direkt hinter `ABGELEHNT_TEXTE`

```python
1619| UMSETZUNG_AGENT = "umsetzung_nacht"
1620| UMSETZUNG_MODELL_STANDARD = "llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL"
1621| UMSETZUNG_TIMEOUT_STANDARD = 7200          # s, ganzer Lauf (A5)
1622| UMSETZUNG_BASH_MS_STANDARD = 300000        # ms, Einzelbefehl, wertet OpenCode selbst aus (Probe P3)
1623| # Kettendateien, die bei Nacharbeit offen sein duerfen (A2.4); Spec/Anforderung/Quellen nie.
1624| KETTEN_PRAEFIXE = ("pruefung", "umsetzung", "review_paket", "verdict", "gesamt", "nacharbeit")
1625| VORGABE_PRAEFIXE = ("spec_", "anforderung_", "quellen_", "_vorlage_")
1626| ABGELEHNT_TEXTE = ("rejected permission", "rule which prevents")
```

### `role-split/kette/kette.py` def _git (Zeilen 653–654) – wirft bei git-Fehler (`check=True`), Ursache des Absturzes

```python
653| def _git(*a: str) -> str:
654|     return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout
```

### `role-split/kette/kette.py` def _stand (Zeilen 1691–1708) – Muster für Prüfsummen (sha256)

```python
1691| def _stand() -> dict[str, str] | None:
1692|     """Pruefsummen aller offenen Dateien: {pfad: sha256 | '<geloescht>' | '<unlesbar>'} (A7)."""
1693|     pfade = _offene_dateien()
1694|     if pfade is None:
1695|         return None
1696|     stand = {}
1697|     for d in pfade:
1698|         p = ROOT / d
1699|         if not p.exists():
1700|             stand[d] = "<geloescht>"
1701|         elif p.is_file():
1702|             try:
1703|                 stand[d] = hashlib.sha256(p.read_bytes()).hexdigest()
1704|             except OSError:
1705|                 stand[d] = "<unlesbar>"
1706|         else:
1707|             stand[d] = "<kein-file>"
1708|     return stand
```

### `role-split/kette/kette.py` def _in_diesem_lauf (Zeilen 1711–1722) – Vergleich zweier Schnappschüsse, wird wiederverwendet

```python
1711| def _in_diesem_lauf(vor: dict[str, str], nach: dict[str, str]) -> dict[str, str]:
1712|     """{pfad: 'neu'|'weg'|'geaendert'} fuer alles, was sich zwischen den Schnappschuessen unterscheidet.
1713|     Eine vorher saubere Datei, die der Lauf aendert, taucht nur in `nach` auf -> 'neu' (= jetzt offen)."""
1714|     raus = {}
1715|     for d in sorted(set(vor) | set(nach)):
1716|         if d not in vor:
1717|             raus[d] = "neu"
1718|         elif d not in nach:
1719|             raus[d] = "weg"
1720|         elif vor[d] != nach[d]:
1721|             raus[d] = "geaendert"
1722|     return raus
```

### `role-split/kette/kette.py` def umsetzung_auto (Zeilen 1922–2106) – Einbaustelle (A7-Schnappschüsse, Befunde (a)/(b), (c)/(d), Protokoll, Schlussausgabe)

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
