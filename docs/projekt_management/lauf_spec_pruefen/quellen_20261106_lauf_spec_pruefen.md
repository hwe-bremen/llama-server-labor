# Quellen: lauf_spec_pruefen

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen lauf_spec_pruefen` (2026-11-06 08:35, Stand `2b63547`), nach dem Abschnitt „Quellen“ in `spec_20261106_lauf_spec_pruefen.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/automatik.py` (Zeilen 1–15) – Kopf, Import-Muster, Konstanten `GROESSE_*` und `UMSETZER_VORSCHLAG`

```python
 1| """Automatik: groesse, stand, status, lauf – K11b.
 2| 
 3| Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
 4| """
 5| import re
 6| import subprocess
 7| import sys
 8| from pathlib import Path
 9| 
10| import kette
11| 
12| GROESSE_DATEIEN = 2
13| GROESSE_ANFORDERUNGEN = 6
14| GROESSE_TESTS = 8
15| UMSETZER_VORSCHLAG = "35B"
```

### `role-split/kette/automatik.py` def groesse (Zeilen 18–35) – bleibt unverändert

```python
18| def groesse(spec_text: str) -> dict:
19|     """Groessenpruefung der Spec.
20| 
21|     dateien: Eintraege aus kette._schreibbereich (keiner -> 0).
22|     anforderungen: Anzahl der Ueberschriften ### <Buchstabe(n)><Zahl>:
23|                    **nur** im Abschnitt ``## Anforderungen``.
24|     tests: Anzahl kette.tests_finden.
25|     """
26|     dateien = len(kette._schreibbereich(spec_text)) if kette._schreibbereich(spec_text) is not None else 0
27|     anforderungen = len(
28|         re.findall(
29|             r"^###\s+[A-Za-z]+\d+:\s",
30|             kette.abschnitt(spec_text, "Anforderungen"),
31|             re.M,
32|         )
33|     )
34|     tests = len(kette.tests_finden(spec_text))
35|     return {"dateien": dateien, "anforderungen": anforderungen, "tests": tests}
```

### `role-split/kette/automatik.py` def lauf (Zeilen 137–190) – Einbaustelle, Größenblock wird ersetzt

```python
137| def lauf(kurztitel: str) -> int:
138|     """Kette: Groesse -> umsetzung-auto -> review-auto -> status -> HALT."""
139|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
140|         print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
141|         return 2
142| 
143|     commit = kette.spec_commit(kurztitel)
144|     if not commit:
145|         print(f'Kein Commit "Spec {kurztitel}" gefunden – erst die Spec committen.')
146|         return 2
147| 
148|     spec_p = kette.datei_suchen("spec", kurztitel, None)
149|     if not spec_p:
150|         print(f"Keine Spec spec_<datum>_{kurztitel}.md gefunden.")
151|         return 2
152| 
153|     spec_text = spec_p.read_text(encoding="utf-8")
154|     if not kette._vorgabe_tests(spec_text):
155|         print(
156|             "Spec hat keinen Abschnitt '## Vorgabe-Tests'. "
157|             "Vorgabe-Tests vorab schreiben (R48), sonst kein Start."
158|         )
159|         return 2
160| 
161|     g = groesse(spec_text)
162|     print(
163|         f"Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
164|         f"{g['tests']} Tests (Schwellen 2/6/8, vorläufig)"
165|     )
166| 
167|     if (
168|         g["dateien"] > GROESSE_DATEIEN
169|         or g["anforderungen"] > GROESSE_ANFORDERUNGEN
170|         or g["tests"] > GROESSE_TESTS
171|     ):
172|         print(
173|             "HALT – zu groß für den lokalen Umsetzer: Spec teilen oder "
174|             "Claude übernimmt (R43)."
175|         )
176|         return 3
177| 
178|     print(f"Umsetzer: {UMSETZER_VORSCHLAG}")
179|     exit_umsetzung = kette.umsetzung_auto(kurztitel)
180|     exit_code = exit_umsetzung
181| 
182|     if exit_umsetzung == 0:
183|         exit_review = kette.review_auto(kurztitel)
184|         exit_code = exit_review
185| 
186|     print()
187|     status(kurztitel)
188|     print("HALT – Entscheidung Hawe.")
189| 
190|     return exit_code
```

### `role-split/kette/spec_pruefen.py` (Zeilen 1–11) – `spec_pruefen` importiert `automatik` (Grund für den Import im Zweig)

```python
 1| """Mechanische Spec-Pruefung: Pflichtabschnitte, Platzhalter, Offene Fragen,
 2| Groesse, Aenderungsstellen, Stelle/Prueft-Zuordnung, Schreibbereich, Quellen.
 3| 
 4| Importiert kette (nicht umgekehrt), damit kette.py klein bleibt (R43).
 5| """
 6| import re
 7| import sys
 8| from pathlib import Path
 9| 
10| import kette
11| import automatik
```

### `role-split/kette/spec_pruefen.py` def spec_pruefen (Zeilen 229–260) – Ausgabe und Exit 0/1/2

```python
229| def spec_pruefen(kurztitel: str) -> int:
230|     """Spec prüfen und Befunde/Hinweise ausgeben. Exit 0/1/2."""
231|     # A1: Kurztitel validieren
232|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
233|         print(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).", file=sys.stderr)
234|         return 2
235| 
236|     # A1: Spec finden
237|     spec_p = kette.datei_suchen("spec", kurztitel, None)
238|     if spec_p is None:
239|         print(f"Keine spec_*_{kurztitel}.md")
240|         return 2
241| 
242|     # A1: Pruefen
243|     befunde, hinweise, g = pruefe(spec_p.read_text(encoding="utf-8"))
244| 
245|     # Ausgabe
246|     stellen_str = str(g["stellen"]) if g["stellen"] is not None else "?"
247|     print(f"Spec-Prüfung {kurztitel}: {spec_p.name}")
248|     print(f"  Größe: {g['dateien']} Datei(en), {g['anforderungen']} Anforderungen, "
249|           f"{g['tests']} Tests, {stellen_str} Änderungsstellen (R59 1/4/8/9, vorläufig)")
250|     for b in befunde:
251|         print(f"  BEFUND   {b}")
252|     for h in hinweise:
253|         print(f"  HINWEIS  {h}")
254| 
255|     if befunde:
256|         print(f"{len(befunde)} Befund(e), {len(hinweise)} Hinweis(e).")
257|         return 1
258|     else:
259|         print(f"Keine Befunde ({len(hinweise)} Hinweis(e)).")
260|         return 0
```

### `role-split/kette/kette.py` (Zeilen 2252–2260) – Verteiler: Muster „Import im Zweig“

```python
2252|     if args.cmd == "lauf":
2253|         import automatik
2254|         return automatik.lauf(args.kurztitel)
2255|     if args.cmd == "status":
2256|         import automatik
2257|         return automatik.status(args.kurztitel)
2258|     if args.cmd == "spec-pruefen":
2259|         import spec_pruefen
2260|         return spec_pruefen.spec_pruefen(args.kurztitel)
```

### `tests/test_lauf_spec_pruefen.py` (Zeilen 1–233) – Vorgabe-Tests (Meldungstexte wörtlich übernehmen)

```python
  1| #!/usr/bin/env python3
  2| """Vorgabe-Tests fuer K12a2 lauf_spec_pruefen (spec_20261106_lauf_spec_pruefen.md, T1–T6).
  3| 
  4| VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.
  5| 
  6| Keine Aussenwirkung: T1–T5 arbeiten in tempfile.TemporaryDirectory() mit eigenem Temp-Git-Repo und umgebogenem
  7| kette.ROOT/kette.PM. T6 liest den echten Bestand nur (git status vorher = nachher). umsetzung_auto und review_auto
  8| werden im Modul kette durch Attrappen ersetzt (kein opencode, kein Modell, kein Netz). automatik und spec_pruefen
  9| werden in jeder Methode importiert.
 10| """
 11| import io
 12| import subprocess
 13| import sys
 14| import tempfile
 15| import unittest
 16| from contextlib import redirect_stderr, redirect_stdout
 17| from pathlib import Path
 18| from unittest import mock
 19| 
 20| ECHT = Path(__file__).resolve().parent.parent
 21| KETTE_DIR = ECHT / "role-split" / "kette"
 22| sys.path.insert(0, str(KETTE_DIR))
 23| import kette  # noqa: E402
 24| 
 25| DATUM = "20261106"
 26| 
 27| 
 28| def spec(tests: int = 2, anforderungen: int = 2, bereich: int = 1, vorgabe: bool = True,
 29|          stellen: str | None = "3", offene: str = "- Keine") -> str:
 30|     """Vollstaendige Spec, die spec-pruefen ohne Befund besteht (bei den Standardwerten)."""
 31|     t = "# Spec: k\n\n- **Datum:** 2026-11-06\n- **Modell:** Test\n- **Betroffene Dateien:** `src/d0.py`\n"
 32|     if stellen is not None:
 33|         t += f"- **Änderungsstellen:** {stellen}\n"
 34|     t += "\n## Ziel\n\nx\n\n## Nicht-Ziele\n\n- y\n\n## Schreibbereich\n\n"
 35|     t += "".join(f"- `src/d{i}.py`\n" for i in range(bereich))
 36|     if vorgabe:
 37|         t += "\n## Vorgabe-Tests\n\n- `tests/test_k.py`\n"
 38|     t += ("\n## Außenwirkung und Sperre\n\n- nichts\n\n## Einstiegspunkte\n\n| Datei | Wie | Test |\n|---|---|---|\n"
 39|           "| `src/d0.py` | Modul | T1 |\n\n## Quellen\n\n- `src/d0.py` def f – Muster\n\n## Anforderungen\n\n")
 40|     t += "".join(f"### A{i + 1}: a\n- **Anforderung:** x\n- **Stelle:** `src/d0.py`, f\n- **Akzeptanz:** T1\n\n"
 41|                  for i in range(anforderungen))
 42|     t += "## Fehlerpfade\n\n| Anforderung | Fall |\n|---|---|\n| A1 | n. a. |\n\n## Testplan\n\n"
 43|     t += "".join(f"### T{i + 1}: t\n- **Prüft:** A{i % anforderungen + 1}\n- **Erwartung:** y\n\n"
 44|                  for i in range(tests))
 45|     t += f"## Offene Fragen\n\n{offene}\n\n## Abweichende Meinung\n\n- Keine\n"
 46|     return t
 47| 
 48| 
 49| def attrappen(test: unittest.TestCase) -> list:
 50|     """umsetzung_auto/review_auto in kette ersetzen; Rueckgabe: Liste der Aufrufe."""
 51|     aufrufe: list = []
 52|     test.code_umsetzung = 0
 53|     test.code_review = 0
 54| 
 55|     def umsetzung(kurztitel, nacharbeit=None):
 56|         aufrufe.append(("umsetzung", kurztitel))
 57|         return test.code_umsetzung
 58| 
 59|     def review(kurztitel):
 60|         aufrufe.append(("review", kurztitel))
 61|         return test.code_review
 62|     for name, f in (("umsetzung_auto", umsetzung), ("review_auto", review)):
 63|         p = mock.patch.object(kette, name, f)
 64|         p.start()
 65|         test.addCleanup(p.stop)
 66|     return aufrufe
 67| 
 68| 
 69| def rufen(fn, *a):
 70|     aus = io.StringIO()
 71|     with redirect_stdout(aus), redirect_stderr(aus):
 72|         code = fn(*a)
 73|     return code, aus.getvalue()
 74| 
 75| 
 76| class Temp(unittest.TestCase):
 77|     def setUp(self):
 78|         d = tempfile.TemporaryDirectory()
 79|         self.addCleanup(d.cleanup)
 80|         self.root = Path(d.name).resolve()
 81|         self.pm = self.root / "docs" / "projekt_management"
 82|         self.pm.mkdir(parents=True)
 83|         for name, wert in (("ROOT", self.root), ("PM", self.pm)):
 84|             alt = getattr(kette, name)
 85|             setattr(kette, name, wert)
 86|             self.addCleanup(setattr, kette, name, alt)
 87|         self.git("init", "-q")
 88|         self.aufrufe = attrappen(self)
 89| 
 90|     def git(self, *a):
 91|         return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
 92|                               check=True, capture_output=True, text=True).stdout
 93| 
 94|     def spec_committen(self, text: str, nachricht: str = "Spec k"):
 95|         (self.pm / f"spec_{DATUM}_k.md").write_text(text, encoding="utf-8")
 96|         self.git("add", ".")
 97|         self.git("commit", "-qm", nachricht)
 98| 
 99| 
100| class Halt(Temp):
101| 
102|     def test_t1_befunde_halten_vor_der_umsetzung(self):
103|         """T1: lauf – Befunde aus spec-pruefen halten mit Exit 3 vor der Umsetzung"""
104|         import automatik
105|         self.spec_committen(spec(offene="- Soll X oder Y?"))
106|         code, out = rufen(automatik.lauf, "k")
107|         self.assertEqual(code, 3, out)
108|         self.assertEqual(self.aufrufe, [])
109|         self.assertIn(f"Spec-Prüfung k: spec_{DATUM}_k.md", out)
110|         self.assertIn("  BEFUND   Offene Fragen nicht geklärt", out)
111|         self.assertIn("HALT – Spec-Prüfung mit Befunden", out)
112|         self.assertNotIn("Umsetzer:", out)
113|         self.assertNotIn("HALT – Entscheidung Hawe.", out)
114|         self.spec_committen(spec(stellen=None), nachricht="alte Spec ohne Zeile")
115|         code, out = rufen(automatik.lauf, "k")
116|         self.assertEqual(code, 3, out)
117|         self.assertIn("  BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt", out)
118|         self.assertEqual(self.aufrufe, [])
119| 
120|     def test_t2_groesse_nur_hinweis(self):
121|         """T2: lauf – Größe über den alten Schwellen und über R59 hält nicht mehr an"""
122|         import automatik
123|         self.spec_committen(spec(tests=9, anforderungen=7, bereich=3, stellen="12"))
124|         code, out = rufen(automatik.lauf, "k")
125|         self.assertEqual(code, 0, out)
126|         self.assertEqual(self.aufrufe, [("umsetzung", "k"), ("review", "k")])
127|         for h in ("Dateien 3 > 1", "Anforderungen 7 > 4", "Tests 9 > 8", "Änderungsstellen 12 > 9"):
128|             self.assertIn(f"  HINWEIS  Größe über R59 (vorläufig): {h}", out)
129|         self.assertIn("Keine Befunde (4 Hinweis(e)).", out)
130|         self.assertNotIn("teilen", out)
131|         self.assertIn("HALT – Entscheidung Hawe.", out)
132| 
133| 
134| class Ablauf(Temp):
135| 
136|     def test_t3_ausgabe_wie_einzelbefehl(self):
137|         """T3: lauf – gültige Spec: Ausgabe wie spec-pruefen, danach Umsetzung und Review"""
138|         import automatik
139|         import spec_pruefen
140|         self.spec_committen(spec())
141|         _, einzeln = rufen(spec_pruefen.spec_pruefen, "k")
142|         code, out = rufen(automatik.lauf, "k")
143|         self.assertEqual(code, 0, out)
144|         self.assertEqual(self.aufrufe, [("umsetzung", "k"), ("review", "k")])
145|         self.assertTrue(out.startswith(einzeln), out)
146|         self.assertIn("  Größe: 1 Datei(en), 2 Anforderungen, 2 Tests, 3 Änderungsstellen (R59 1/4/8/9, vorläufig)\n"
147|                       "Keine Befunde (0 Hinweis(e)).\nUmsetzer: 35B\n", out)
148|         self.assertNotIn("Schwellen 2/6/8", out)
149|         self.code_umsetzung = 1
150|         code, out = rufen(automatik.lauf, "k")
151|         self.assertEqual(code, 1, out)
152|         self.assertEqual(self.aufrufe[-1], ("umsetzung", "k"))
153| 
154|     def test_t4_vorbedingungen_und_exit_2(self):
155|         """T4: lauf – Vorbedingungen vor der Spec-Prüfung, Exit 2 der Spec-Prüfung durchgereicht"""
156|         import automatik
157|         import spec_pruefen
158|         self.spec_committen(spec(vorgabe=False))
159|         code, out = rufen(automatik.lauf, "k")
160|         self.assertEqual(code, 2, out)
161|         self.assertIn("Vorgabe-Tests", out)
162|         self.assertNotIn("Spec-Prüfung", out)
163|         self.spec_committen(spec(), nachricht="mit Vorgabe")
164|         gesehen = []
165|         with mock.patch.object(spec_pruefen, "spec_pruefen", lambda kt: gesehen.append(kt) or 2):
166|             code, out = rufen(automatik.lauf, "k")
167|         self.assertEqual(gesehen, ["k"])
168|         self.assertEqual(code, 2, out)
169|         self.assertEqual(self.aufrufe, [])
170|         self.assertNotIn("HALT – Entscheidung Hawe.", out)
171|         with mock.patch.object(spec_pruefen, "spec_pruefen", lambda kt: 1):
172|             code, out = rufen(automatik.lauf, "k")
173|         self.assertEqual(code, 3, out)
174|         self.assertEqual(self.aufrufe, [])
175| 
176| 
177| class Einstieg(Temp):
178| 
179|     def test_t5_standardwerte_und_echter_aufruf(self):
180|         """T5: Standardwerte – alte Schwellen weg, groesse bleibt, lauf und spec-pruefen über kette.main in frischem Prozess"""
181|         import automatik
182|         import spec_pruefen
183|         for name in ("GROESSE_DATEIEN", "GROESSE_ANFORDERUNGEN", "GROESSE_TESTS"):
184|             self.assertFalse(hasattr(automatik, name), name)
185|         self.assertEqual(automatik.groesse(spec(tests=3)), {"dateien": 1, "anforderungen": 2, "tests": 3})
186|         self.assertEqual(automatik.UMSETZER_VORSCHLAG, "35B")
187|         self.assertEqual(spec_pruefen.R59, {"dateien": 1, "anforderungen": 4, "tests": 8, "stellen": 9})
188|         self.spec_committen(spec(offene="- Frage offen"))
189|         skript = (
190|             "import sys\n"
191|             f"sys.path.insert(0, {str(KETTE_DIR)!r})\n"
192|             "from pathlib import Path\n"
193|             "import kette\n"
194|             "kette.ROOT = Path(sys.argv[1]); kette.PM = kette.ROOT / 'docs' / 'projekt_management'\n"
195|             "kette.umsetzung_auto = lambda *a, **k: sys.exit(99)\n"
196|             "kette.review_auto = lambda *a, **k: sys.exit(98)\n"
197|             "sys.exit(kette.main(['lauf', 'k']))\n"
198|         )
199|         r = subprocess.run([sys.executable, "-c", skript, str(self.root)], capture_output=True, text=True,
200|                            cwd=str(self.root), timeout=60)
201|         self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
202|         self.assertIn("HALT – Spec-Prüfung mit Befunden", r.stdout)
203|         self.assertNotIn("Traceback", r.stderr)
204|         r = subprocess.run([sys.executable, "-c", skript.replace("['lauf', 'k']", "['spec-pruefen', 'k']"),
205|                             str(self.root)], capture_output=True, text=True, cwd=str(self.root), timeout=60)
206|         self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
207|         self.assertNotIn("Traceback", r.stderr)
208| 
209| 
210| class Bestand(unittest.TestCase):
211| 
212|     def test_t6_trockenlauf_echter_bestand(self):
213|         """T6: Trockenlauf am echten Bestand – alte Spec hält, saubere Spec läuft, nichts geschrieben"""
214|         import automatik
215|         aufrufe = attrappen(self)
216|         vorher = subprocess.run(["git", "-C", str(kette.ROOT), "status", "--porcelain"],
217|                                 capture_output=True, text=True).stdout
218|         code, out = rufen(automatik.lauf, "git_schutz")
219|         self.assertEqual(code, 3, out)
220|         befunde = [z for z in out.splitlines() if z.startswith("  BEFUND")]
221|         self.assertEqual(befunde, ["  BEFUND   Zeile „- **Änderungsstellen:** n“ fehlt"], out)
222|         self.assertEqual(aufrufe, [])
223|         code, out = rufen(automatik.lauf, "spec_pruefen")
224|         self.assertEqual(code, 0, out)
225|         self.assertIn("Keine Befunde", out)
226|         self.assertEqual(aufrufe, [("umsetzung", "spec_pruefen"), ("review", "spec_pruefen")])
227|         nachher = subprocess.run(["git", "-C", str(kette.ROOT), "status", "--porcelain"],
228|                                  capture_output=True, text=True).stdout
229|         self.assertEqual(vorher, nachher)
230| 
231| 
232| if __name__ == "__main__":
233|     unittest.main()
```
