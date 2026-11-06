# Quellen Schritt 2 (2 ok, 2 schlecht)

- UNKLAR - `role-split/kette/spec_pruefen.py` PFLICHT – welche Abschnitte zwingend sind
- FEHLT role-split/kette/kette.py def spec_pruefen

### `role-split/kette/spec_pruefen.py` def pruefe (Zeilen 194–226) – wie Befunde gesammelt werden

```python
194| def pruefe(spec_text: str) -> tuple[list[str], list[str], dict]:
195|     """Spec mechanisch pruefen. Gibt (befunde, hinweise, groesse) zurueck."""
196|     # HTML-Kommentare entfernen
197|     text = re.sub(r"<!--.*?-->", "", spec_text, flags=re.S)
198| 
199|     befunde: list[str] = []
200|     hinweise: list[str] = []
201| 
202|     # A2.1: Pflichtabschnitte
203|     _abschnitte(text, befunde)
204| 
205|     # A2.2: Platzhalter
206|     for p in PLATZHALTER:
207|         if p in text:
208|             befunde.append(f"Platzhalter aus der Vorlage: {p}")
209| 
210|     # A2.3: Offene Fragen
211|     offene = kette.abschnitt(text, "Offene Fragen").strip()
212|     if offene:
213|         zeilen = [z.strip() for z in offene.splitlines() if z.strip()]
214|         if len(zeilen) == 1 and re.match(r"^(?:[-*]\s*)?Keine\b", zeilen[0], re.I):
215|             pass  # geklärt
216|         else:
217|             befunde.append("Offene Fragen nicht geklärt – erst beantworten, dann „Keine“")
218| 
219|     # A3: Groesse und Zuordnung
220|     _zuordnung(text, befunde, hinweise)
221| 
222|     # A4: Schreibbereich und Quellen
223|     _bereich_quellen(text, befunde, hinweise)
224| 
225|     g = _groesse(text)
226|     return befunde, hinweise, g
```

### `role-split/kette/kette.py` def abgleich (Zeilen 316–368) – Vergleichslogik (als Referenz für Konsistenz)

```python
316| def abgleich(kurztitel: str, datum: str | None = None, schwelle: float = 0.6) -> int:
317|     spec, ho = datei_suchen("spec", kurztitel, datum), datei_suchen("handover", kurztitel, datum)
318|     if not spec or not ho:
319|         print(f"Spec oder Handover fehlt: spec={spec}, handover={ho}"); return 2
320|     spec_tests = tests_finden(spec.read_text(encoding="utf-8"))
321|     ho_text = ho.read_text(encoding="utf-8")
322|     getestet = tests_finden(abschnitt(ho_text, "Getestet"))
323|     # A2: Bereichsangaben (T1–T2, T1-T2) unter "Nicht getestet" entfernen
324|     nicht_text = abschnitt(ho_text, "Nicht getestet")
325|     nicht_text = re.sub(rf"\b({TEST_ID})\s*[–—-]\s*({TEST_ID})\b", "", nicht_text)
326|     nicht = set(re.findall(rf"\b({TEST_ID})\b", nicht_text))
327|     print(f"Spec:     {spec.name}  ({len(spec_tests)} Tests)\nHandover: {ho.name}\n")
328|     if not spec_tests:
329|         print("Keine Test-IDs (T1, NT1 ...) in der Spec gefunden."); return 2
330| 
331|     probleme = 0
332|     for tid, titel in spec_tests.items():
333|         if tid in getestet:
334|             q = passt(titel, getestet[tid])
335|             if q >= schwelle:
336|                 print(f"  ok        {tid:5} {titel}")
337|             else:
338|                 probleme += 1
339|                 print(f"  ANDERS    {tid:5} Spec: {titel}\n"
340|                       f"                  Handover: {getestet[tid]}   (Uebereinstimmung {q:.0%} -- ausgetauscht?)")
341|         elif tid in nicht:
342|             probleme += 1
343|             print(f"  NICHT GET {tid:5} {titel}  (unter 'Nicht getestet' -- Grund pruefen)")
344|         else:
345|             probleme += 1
346|             print(f"  FEHLT     {tid:5} {titel}")
347|     for tid in getestet.keys() - spec_tests.keys():
348|         print(f"  EXTRA     {tid:5} {getestet[tid]}  (nicht in der Spec)")
349| 
350|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
351|     if skript.is_file():
352|         code = skript.read_text(encoding="utf-8")
353|         ohne = [t for t in spec_tests if not re.search(rf"def\s+test_{t.lower()}(_|\b)", code)]
354|         if ohne:
355|             probleme += 1
356|             print(f"\n  Testskript {skript.relative_to(ROOT)}: keine Methode test_<id> fuer {', '.join(ohne)}")
357|         else:
358|             print(f"\n  Testskript {skript.relative_to(ROOT)}: alle {len(spec_tests)} Tests als Methode vorhanden")
359|         for hinweis in methoden_pruefen(code):
360|             probleme += 1
361|             print(f"  {hinweis}")
362|         print(f"  Selbst ausfuehren: python3 -m unittest -v {skript.relative_to(ROOT)}")
363|     else:
364|         print(f"\n  Kein Testskript tests/test_{kurztitel}.py -- Tests sind nur behauptet, nicht wiederholbar.")
365|     print(f"\n{'Keine Abweichung.' if not probleme else f'{probleme} Abweichung(en).'}")
366|     return 0 if not probleme else 1
367| 
368| # ---------------------------------------------------------------- gegenprobe
```
