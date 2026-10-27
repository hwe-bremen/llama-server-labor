# Quellen: k10b_nachtraege

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen k10b_nachtraege` (2026-10-27 17:18, Stand `39a9696`), nach dem Abschnitt „Quellen“ in `spec_20261027_k10b_nachtraege.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` def tests_finden (Zeilen 204–215) – liefert {Test-ID: Titel} aus einer Spec (für A1)

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

### `role-split/kette/kette.py` def abgleich (Zeilen 272–321) – Stelle „Nicht getestet“ (für A2)

```python
272| def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
273|     spec, ho = datei_suchen("spec", kurztitel, datum), datei_suchen("handover", kurztitel, datum)
274|     if not spec or not ho:
275|         print(f"Spec oder Handover fehlt: spec={spec}, handover={ho}"); return 2
276|     spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
277|     ho_text = ho.read_text(encoding="utf-8")
278|     getestet = tests_finden(abschnitt(ho_text, "Getestet"))
279|     nicht = set(re.findall(rf"\b({TEST_ID})\b", abschnitt(ho_text, "Nicht getestet")))
280|     print(f"Spec:     {spec.name}  ({len(spec_tests)} Tests)\nHandover: {ho.name}\n")
281|     if not spec_tests:
282|         print("Keine Test-IDs (T1, NT1 ...) in der Spec gefunden."); return 2
283| 
284|     probleme = 0
285|     for tid, titel in spec_tests.items():
286|         if tid in getestet:
287|             q = passt(titel, getestet[tid])
288|             if q >= schwelle:
289|                 print(f"  ok        {tid:5} {titel}")
290|             else:
291|                 probleme += 1
292|                 print(f"  ANDERS    {tid:5} Spec: {titel}\n"
293|                       f"                  Handover: {getestet[tid]}   (Uebereinstimmung {q:.0%} -- ausgetauscht?)")
294|         elif tid in nicht:
295|             probleme += 1
296|             print(f"  NICHT GET {tid:5} {titel}  (unter 'Nicht getestet' -- Grund pruefen)")
297|         else:
298|             probleme += 1
299|             print(f"  FEHLT     {tid:5} {titel}")
300|     for tid in getestet.keys() - spec_tests.keys():
301|         print(f"  EXTRA     {tid:5} {getestet[tid]}  (nicht in der Spec)")
302| 
303|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
304|     if skript.is_file():
305|         code = skript.read_text(encoding="utf-8")
306|         ohne = [t for t in spec_tests if not re.search(rf"def\s+test_{t.lower()}(_|\b)", code)]
307|         if ohne:
308|             probleme += 1
309|             print(f"\n  Testskript {skript.relative_to(ROOT)}: keine Methode test_<id> fuer {', '.join(ohne)}")
310|         else:
311|             print(f"\n  Testskript {skript.relative_to(ROOT)}: alle {len(spec_tests)} Tests als Methode vorhanden")
312|         for hinweis in methoden_pruefen(code):
313|             probleme += 1
314|             print(f"  {hinweis}")
315|         print(f"  Selbst ausfuehren: python3 -m unittest -v {skript.relative_to(ROOT)}")
316|     else:
317|         print(f"\n  Kein Testskript tests/test_{kurztitel}.py -- Tests sind nur behauptet, nicht wiederholbar.")
318|     print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
319|     return 0 if not probleme else 1
320| 
321| # ---------------------------------------------------------------- gegenprobe
```

### `role-split/kette/kette.py` def _umsetzung_prompt (Zeilen 1637–1654) – Prompt-Aufbau (für A1)

```python
1637| def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path | None, nb: int) -> str | None:
1638|     vorlage = PROMPTS / "umsetzung_nacht.md"
1639|     if not vorlage.is_file():
1640|         return None
1641|     anf = datei_suchen("anforderung", kurztitel, None)
1642|     anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
1643|         f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
1644|     text = (vorlage.read_text(encoding="utf-8")
1645|             .replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", commit)
1646|             .replace("{anforderung}", anf_pfad)
1647|             .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md"))
1648|     text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
1649|     if nacharbeit:
1650|         text += (f"\n## Nachbesserung {nb}\n\nDas ist Nachbesserung {nb}. Der Auftrag steht unten (aus "
1651|                  f"`{_rel(nacharbeit)}`). Ergänze den Handover docs/projekt_management/handover_{datum}_"
1652|                  f"{kurztitel}.md um den Abschnitt „## Nachbesserung {nb}\" – nichts Bestehendes löschen.\n\n"
1653|                  + nacharbeit.read_text(encoding="utf-8").strip() + "\n")
1654|     return text
```

### `role-split/kette/kette.py` def _lauf (Zeilen 1657–1744) – Auswertung von `step_finish` und `info` (für A3)

```python
1657| def _lauf(befehl: list[str], env: dict, timeout: int, rohdaten: Path) -> dict:
1658|     """Startet opencode in eigener Prozessgruppe, liest den JSON-Strom zeilenweise (sofort in die
1659|     Rohdaten), gibt je Werkzeugaufruf eine Zeile aus und beendet die Gruppe nach `timeout` s (A5, A6, A9)."""
1660|     info = {"werkzeuge": 0, "fehler": [], "abgelehnt": [], "tokens": 0, "reason": None, "text": "",
1661|             "ereignisse": 0, "kaputt": 0, "timeout": False,
1662|             "tokens_teile": {"input": 0, "output": 0, "reasoning": 0}}
1663|     rohdaten.parent.mkdir(parents=True, exist_ok=True)
1664|     stderr_datei = rohdaten.with_suffix(".err")
1665|     start = dt.datetime.now()
1666|     with open(rohdaten, "w", encoding="utf-8") as roh, open(stderr_datei, "w", encoding="utf-8") as fehlerkanal:
1667|         try:
1668|             proc = subprocess.Popen(befehl, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=fehlerkanal,
1669|                                     text=True, encoding="utf-8", errors="replace", start_new_session=True)
1670|         except OSError as e:
1671|             info["startfehler"] = f"{type(e).__name__}: {e}"
1672|             info["dauer"] = 0
1673|             return info
1674| 
1675|         def lesen():
1676|             for zeile in proc.stdout:
1677|                 roh.write(zeile); roh.flush()
1678|                 zeile = zeile.strip()
1679|                 if not zeile:
1680|                     continue
1681|                 try:
1682|                     e = json.loads(zeile)
1683|                 except json.JSONDecodeError:
1684|                     info["kaputt"] += 1
1685|                     continue
1686|                 info["ereignisse"] += 1
1687|                 teil = e.get("part") or {}
1688|                 typ = e.get("type")
1689|                 if typ == "tool_use":
1690|                     zustand = teil.get("state") or {}
1691|                     status = zustand.get("status")
1692|                     if status not in ("completed", "error"):
1693|                         continue
1694|                     info["werkzeuge"] += 1
1695|                     eingabe = zustand.get("input")
1696|                     wortlaut = (eingabe.get("command") or eingabe.get("filePath") or json.dumps(eingabe,
1697|                                 ensure_ascii=False)) if isinstance(eingabe, dict) else str(eingabe or "")
1698|                     kurz = wortlaut.replace("\n", " ")[:60]
1699|                     print(f"[{dt.datetime.now():%H:%M:%S}] {teil.get('tool', '?')}: {kurz}"
1700|                           + ("…" if len(wortlaut) > 60 else "") + ("  [FEHLER]" if status == "error" else ""),
1701|                           flush=True)
1702|                     if status == "error":
1703|                         fehlertext = str(zustand.get("error") or "")
1704|                         eintrag = f"{teil.get('tool', '?')}: {wortlaut[:200]} – {fehlertext[:200]}".replace("\n", " ")
1705|                         info["fehler"].append(eintrag)
1706|                         if any(t in fehlertext for t in ABGELEHNT_TEXTE):
1707|                             info["abgelehnt"].append(eintrag)
1708|                 elif typ == "step_finish":
1709|                     info["reason"] = teil.get("reason")
1710|                     tok = teil.get("tokens") or {}
1711|                     info["tokens"] += int(tok.get("total") or 0)
1712|                     for k in info["tokens_teile"]:
1713|                         info["tokens_teile"][k] += int(tok.get(k) or 0)
1714|                 elif typ == "text":
1715|                     info["text"] = teil.get("text") or info["text"]
1716| 
1717|         leser = threading.Thread(target=lesen, daemon=True)
1718|         leser.start()
1719|         stopp = threading.Event()
1720| 
1721|         def puls():
1722|             while not stopp.wait(KETTE_HERZSCHLAG_S):
1723|                 minuten = int((dt.datetime.now() - start).total_seconds()) // 60
1724|                 print(f"[{dt.datetime.now():%H:%M:%S}] Lebenszeichen, Lauf läuft seit {minuten} min", flush=True)
1725| 
1726|         herz = threading.Thread(target=puls, daemon=True)
1727|         herz.start()
1728|         try:
1729|             proc.wait(timeout=timeout)
1730|         except subprocess.TimeoutExpired:
1731|             info["timeout"] = True
1732|             try:
1733|                 os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
1734|             except (ProcessLookupError, PermissionError, OSError):
1735|                 proc.kill()
1736|             try:
1737|                 proc.wait(timeout=30)
1738|             except subprocess.TimeoutExpired:
1739|                 info["haengt"] = True
1740|         finally:
1741|             stopp.set()
1742|         leser.join(timeout=10)
1743|     info["dauer"] = int((dt.datetime.now() - start).total_seconds())
1744|     return info
```

### `role-split/kette/kette.py` (Zeilen 1888–1906) – Protokollzeile, Unterzeilen, Zusammenfassung auf stdout (für A3)

```python
1888|     reason = "timeout" if info["timeout"] else (info["reason"] or "–")
1889|     zeile = (f"- **{dt.datetime.now():%Y-%m-%d %H:%M}** – Modell: {modell}, Dauer: {info['dauer']} s, "
1890|              f"Tools: {info['werkzeuge']}, Fehler: {len(info['fehler'])}, Abgelehnt: {len(info['abgelehnt'])}, "
1891|              f"Tokens: {info['tokens']}, reason: {reason}, rot: {rot}, pruefen: {pruefen_code}, art: {art}, "
1892|              f"Exit: {exit_code}\n")
1893|     if not protokoll_p.exists():
1894|         protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
1895|                                encoding="utf-8")
1896|     tt = info["tokens_teile"]
1897|     zeile += f"  - Tokens: input {tt['input']}, output {tt['output']}, reasoning {tt['reasoning']}\n"
1898|     for e in info["fehler"]:
1899|         zeile += f"  - {'abgelehnt' if e in info['abgelehnt'] else 'fehlgeschlagen'}: {e}\n"
1900|     with open(protokoll_p, "a", encoding="utf-8") as f:
1901|         f.write(zeile)
1902| 
1903|     print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
1904|     print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
1905|           f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']}, reason {reason}")
1906|     for e in info["fehler"]:
```

### `role-split/kette/kette.py` def _ist_hoch (Zeilen 823–825) – Regel „hoch“ (für A4)

```python
823| def _ist_hoch(zeile: dict) -> bool:
824|     schwere = (spalte(zeile, "schwere") or "").lower()
825|     return "hoch" in schwere or any(ja(spalte(zeile, n)) for n in ("datenverl", "unbemerkt", "harte"))
```

### `role-split/kette/kette.py` def zusammenfuehren (Zeilen 828–898) – Gesamtbefund (für A4)

```python
828| def zusammenfuehren(pfade: list[Path], _internal: bool = False) -> int:
829|     if len(pfade) < 2:
830|         if _internal:
831|             print("Nur ein Verdikt – Gesamtbefund wird mit Warnung geschrieben.")
832|             # Gesamtbefund mit UNVOLLSTÄNDIG schreiben
833|             p = pfade[0]
834|             m = re.match(r"verdict_(\d{8})_(.+?)_[^_]+(?:_[^_]+)*\.md$", p.name)
835|             datum = m.group(1) if m else dt.date.today().strftime("%Y%m%d")
836|             kt = re.match(r"verdict_\d{8}_([a-z0-9_]+?)_(?:qwen|gemma|mellum|apertus|claude|hawe)", p.name)
837|             kurz = kt.group(1) if kt else "review"
838|             text = p.read_text(encoding="utf-8")
839|             m2 = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis") or text)
840|             ergebnis = m2.group(1) if m2 else "?"
841|             teile = [f"# Gesamtbefund: {kurz}\n",
842|                      f"Mechanisch zusammengeführt mit `kette.py zusammenfuehren` ({dt.datetime.now():%Y-%m-%d %H:%M}). Kein Befund wurde weggelassen oder umformuliert.\n",
843|                       "## Ergebnis\n", f"**UNVOLLSTÄNDIG** – Nur ein Lauf mit auswertbarer Befund-Tabelle.\n",
844|                      "| Lauf | Ergebnis des Laufs |", "|---|---|",
845|                       f"| `{p.name}` | {ergebnis.replace('PASS', 'UNVOLLSTÄNDIG')} |",
846|                      "",
847|                      "> Ein weiterer Lauf fehlt. Der Gesamtbefund beruht auf nur einem Lauf mit auswertbarer Tabelle.\n"]
848|             ziel = PM / f"gesamt_{datum}_{kurz}.md"
849|             ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
850|             print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
851|             return 1
852|         print("Mindestens zwei Verdikte angeben."); return 2
853|     zeilen, ergebnisse, fehlt = [], [], []
854|     for p in pfade:
855|         if not p.is_file():
856|             fehlt.append(str(p)); continue
857|         text = p.read_text(encoding="utf-8")
858|         m = re.search(r"\b(PASS|NACHBESSERN|FAIL)\b", abschnitt(text, "Ergebnis") or text)
859|         ergebnisse.append((p.name, m.group(1) if m else "?"))
860|         befunde = _befunde(text)
861|         if not befunde:
862|             zeilen.append((p.name, "?", "(keine Befundtabelle erkannt – Verdikt von Hand lesen)", "", False))
863|         for b in befunde:
864|             schwere = spalte(b, "schwere") or "?"
865|             text_b = spalte(b, "befund", "begründung", "begruendung") or " | ".join(v for v in b.values() if v)
866|             ort = spalte(b, "datei", "zeile", "anfor") or ""
867|             zeilen.append((p.name, schwere, text_b, ort, _ist_hoch(b)))
868|     if fehlt:
869|         print("Fehlt: " + ", ".join(fehlt)); return 2
870|     hoch = [z for z in zeilen if z[4]]
871|     if hoch or any(e == "NACHBESSERN" for _, e in ergebnisse):
872|         urteil_ = "NACHBESSERN"
873|     elif any(e == "FAIL" for _, e in ergebnisse):
874|         urteil_ = "FAIL"
875|     elif all(e == "PASS" for _, e in ergebnisse):
876|         urteil_ = "PASS"
877|     else:
878|         urteil_ = "UNKLAR"
879|     if any(e == "FAIL" for _, e in ergebnisse):
880|         urteil_ = "FAIL"
881|     m = re.match(r"verdict_(\d{8})_(.+?)_[^_]+(?:_[^_]+)*\.md$", pfade[0].name)
882|     datum = m.group(1) if m else dt.date.today().strftime("%Y%m%d")
883|     kt = re.match(r"verdict_\d{8}_([a-z0-9_]+?)_(?:qwen|gemma|mellum|apertus|claude|hawe)", pfade[0].name)
884|     kurz = kt.group(1) if kt else "review"
885|     teile = [f"# Gesamtbefund: {kurz}\n",
886|              f"Mechanisch zusammengeführt mit `kette.py zusammenfuehren` ({dt.datetime.now():%Y-%m-%d %H:%M}). Kein Befund wurde weggelassen oder umformuliert.\n",
887|              "## Ergebnis\n", f"**{urteil_}** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.\n",
888|              "| Lauf | Ergebnis des Laufs |", "|---|---|"] + [f"| `{n}` | {e} |" for n, e in ergebnisse] + [
889|              "", "## Befunde (alle Läufe)\n", "| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |", "|---|---|---|---|---|"]
890|     for n, s_, t, o, h in zeilen:
891|         teile.append(f"| `{n}` | {s_} | {'ja' if h else 'nein'} | {o.replace('|', '/')} | {t.replace('|', '/')} |")
892|     ziel = PM / f"gesamt_{datum}_{kurz}.md"
893|     ziel.write_text("\n".join(teile) + "\n", encoding="utf-8")
894|     print(f"{len(zeilen)} Befunde aus {len(ergebnisse)} Läufen, davon {len(hoch)} hoch -> {urteil_}")
895|     print(f"Geschrieben: {ziel.relative_to(ROOT) if ziel.is_relative_to(ROOT) else ziel}")
896|     return 0 if urteil_ == "PASS" else 1
897| 
898| # ---------------------------------------------------------------- anforderung
```

### `tests/test_umsetzung_auto.py` class Basis (Zeilen 51–125) – Testaufbau mit Attrappe für einen ganzen `umsetzung_auto`-Lauf (für T3)

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

### `docs/projekt_management/verdict_20261027_umsetzung_auto_qwen36-35b_betrieb.md` (Zeilen 35–40) – Format der Befund-Tabelle (für T4)

```markdown
35| ## Befunde
36| 
37| | # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
38| |---|---|---|---|---|---|---|---|
39| | 1 | nein | nein | nein | niedrig | `kette.py:1640` | Timeout-Behandlung: `proc.wait()` nach Kill kann blockieren, wenn Kind-Prozess sich nicht sofort beendet. In der Praxis ist dies akzeptabel, da der Hauptprozess (opencode) tot ist. |
40| 
```
