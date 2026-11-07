# Quellen: pruefen_venv

Maschinell und woertlich aus dem Repo geholt mit `kette.py quellen pruefen_venv` (2026-11-07 14:01, Stand `c5a523e`), nach dem Abschnitt „Quellen“ in `spec_20261107_pruefen_venv.md`.
Nicht von Hand aendern – bei Bedarf die Spec anpassen und neu erzeugen. Konstanten, Formate und Schnittstellen werden nur von hier oder aus dem Code genommen, nie aus dem Gedaechtnis.

### `role-split/kette/kette.py` (Zeilen 370–391) – `LAEUFER` (wird unverändert an das gewählte Python übergeben)

```python
370| LAEUFER = r"""
371| import json, sys, unittest
372| modul = sys.argv[1]
373| suite = unittest.defaultTestLoader.loadTestsFromName(modul)
374| def name(t): return t.id().split(".")[-1].split(" ")[0]
375| stand = {}
376| def alle(s):
377|     for t in s:
378|         if isinstance(t, unittest.TestSuite): alle(t)
379|         elif t is not None: stand[name(t)] = "ok"
380| alle(suite)                       # vor run(): unittest entfernt gelaufene Tests aus der Suite
381| erg = unittest.TestResult()
382| suite.run(erg)
383| for t, _ in erg.failures: stand[name(t)] = "FAIL"
384| for t, _ in erg.errors:
385|     stand[name(t) if hasattr(t, "id") else str(t)] = "ERROR"
386| if not stand and erg.errors: stand["<Laden>"] = "ERROR"
387| for t, _ in erg.skipped: stand[name(t)] = "skipped"
388| print("@@KETTE@@" + json.dumps(stand))
389| """
390| 
391| 
```

### `role-split/kette/kette.py` def tests_laufen (Zeilen 392–406) – Einbaustelle 1 (Startzeile), Einfügestelle der neuen Funktion davor

```python
392| def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
393|     """Laesst das Testskript in einem eigenen Prozess laufen; Ergebnis je Testmethode."""
394|     modul = ".".join(skript.relative_to(ROOT).with_suffix("").parts)
395|     # Eigener, frischer Bytecode-Cache je Lauf: sonst kann Python eine alte .pyc weiterverwenden,
396|     # wenn die zurueckgesetzte Datei gleich gross ist und in derselben Sekunde geschrieben wurde.
397|     with tempfile.TemporaryDirectory(prefix="kette_pyc_") as cache:
398|         try:
399|             r = subprocess.run([sys.executable, "-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul],
400|                                cwd=ROOT, capture_output=True, text=True, timeout=timeout)
401|         except subprocess.TimeoutExpired:
402|             return None
403|     for zeile in reversed(r.stdout.splitlines()):
404|         if zeile.startswith("@@KETTE@@"):
405|             return json.loads(zeile[len("@@KETTE@@"):])
406|     return {"<Testskript laedt nicht>": "ERROR"}
```

### `role-split/kette/kette.py` def _pruefen_teile (Zeilen 580–616) – Einbaustelle 2 (`unittest_lauf`)

```python
580| def _pruefen_teile(kurztitel: str, commit: str | None = None, timeout: int = 300) -> dict:
581|     """Teilergebnisse von abgleich, unittest, gegenprobe. Rueckgabe: dict mit den drei Schlüsseln."""
582|     import contextlib
583|     import io
584|     if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
585|         return {"abgleich": (2, "Kurztitel ungueltig"), "unittest": (2, ""), "gegenprobe": (2, "")}
586|     commit = commit or spec_commit(kurztitel)
587|     if not commit:
588|         return {"abgleich": (2, f"Kein Commit 'Spec {kurztitel}'"),
589|                 "unittest": (2, ""), "gegenprobe": (2, "")}
590|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
591| 
592|     def schritt(titel: str, fn):
593|         puffer = io.StringIO()
594|         with contextlib.redirect_stdout(puffer):
595|             try:
596|                 code = fn()
597|             except Exception as e:
598|                 print(f"!!! Werkzeugfehler: {type(e).__name__}: {e}")
599|                 code = 2
600|         return code, puffer.getvalue()
601| 
602|     def unittest_lauf():
603|         if not skript.is_file():
604|             print(f"Kein Testskript {skript.relative_to(ROOT)}")
605|             return 2
606|         r = subprocess.run([sys.executable, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
607|                            cwd=ROOT, capture_output=True, text=True, timeout=timeout)
608|         print((r.stdout + r.stderr).rstrip())
609|         return 0 if r.returncode == 0 else 1
610| 
611|     abgl_code, abgl_out = schritt("abgleich", lambda: abgleich(kurztitel))
612|     unit_code, unit_out = schritt("unittest", unittest_lauf)
613|     gegen_code, gegen_out = schritt(f"gegenprobe gegen {commit}",
614|                                     lambda: gegenprobe(kurztitel, commit, timeout))
615|     return {"abgleich": (abgl_code, abgl_out), "unittest": (unit_code, unit_out),
616|             "gegenprobe": (gegen_code, gegen_out)}
```

### `role-split/kette/kette.py` def gegenprobe (Zeilen 436–493) – nutzt `tests_laufen` (keine Änderung)

```python
436| def gegenprobe(kurztitel: str, commit: str, timeout: int = 300) -> int:
437|     """Setzt jede seit <commit> geaenderte Code-Datei einzeln voruebergehend auf den alten Stand
438|     zurueck und laesst das Testskript laufen. Ein Test, der dabei nie rot wird, prueft keine der
439|     Aenderungen. Danach wird jeweils der aktuelle Stand wiederhergestellt (Pruefsumme)."""
440|     skript = ROOT / "tests" / f"test_{kurztitel}.py"
441|     if not skript.is_file():
442|         print(f"Kein Testskript {skript.relative_to(ROOT)}"); return 2
443|     try:
444|         kette, _fremd = _aenderungen(commit, kurztitel)
445|     except subprocess.CalledProcessError as e:
446|         print(f"git-Fehler: {e.stderr.strip()}"); return 2
447|     # A5: dieselbe Auswahl wie paket – nur zur Kette gehoerige Code-Dateien, auch role-split/kette/
448|     dateien = sorted(d for d in kette
449|                      if d.endswith((".py", ".sh", ".command")) and not d.startswith("tests/"))
450|     if not dateien:
451|         print(f"Keine geaenderten Code-Dateien seit {commit}."); return 2
452| 
453|     vorher = tests_laufen(skript, timeout)
454|     if not vorher or any(v not in ("ok", "skipped") for v in vorher.values()):
455|         print(f"Abbruch: Das Testskript laeuft auf dem aktuellen Stand nicht gruen ({vorher}). Erst reparieren.")
456|         return 2
457|     print(f"Gegenprobe gegen {commit}: {len(vorher)} Tests, je Datei einzeln zurueckgesetzt\n")
458|     bestand = _bestand_ids(kurztitel)
459|     rot_durch: dict[str, list[str]] = {t: [] for t in vorher}
460|     laden_scheitert: list[str] = []
461|     for d in dateien:
462|         nachher = _zuruecksetzen_und_testen(skript, d, commit, timeout)
463|         if nachher is None:
464|             print(f"  {d}: Zeitueberschreitung"); continue
465|         if set(nachher) - set(vorher):            # Laden gescheitert
466|             print(f"  {d}: ohne die neue Fassung laedt das Testskript gar nicht -- alle Tests rot, aber ohne Einzelaussage")
467|             laden_scheitert.append(Path(d).name)
468|             continue
469|         rote = [t for t, v in nachher.items() if v in ("FAIL", "ERROR")]
470|         for t in rote:
471|             rot_durch[t].append(d)
472|         print(f"  {d}: {len(rote)} Test(s) rot")
473|     print()
474|     bestand_re = re.compile(rf"test_({'|'.join(bestand)})(_|$)", re.I)
475|     gruen = [t for t, ds in rot_durch.items() if not ds and not bestand_re.match(t)]
476|     for t in sorted(rot_durch):
477|         if rot_durch[t]:
478|             print(f"  rot   {t}  <- {', '.join(Path(x).name for x in rot_durch[t])}")
479|         elif bestand_re.match(t) and not rot_durch[t]:
480|             print(f"  BESTAND {t}  (prueft laut Spec bewusst Bestehendes)")
481|         elif laden_scheitert:
482|             print(f"  LADEN {t}  (rot nur, weil das Skript ohne {', '.join(laden_scheitert)} nicht laedt -- schwacher Beleg)")
483|         else:
484|             print(f"  GRUEN {t}  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)")
485|     print(f"\n{len(vorher) - len(gruen)} von {len(vorher)} Tests werden durch eine einzelne alte Datei rot"
486|           + (f", {len(gruen)} nur ueber das Laden" if laden_scheitert else "") + ". Aktueller Stand ist wiederhergestellt.")
487|     if gruen:
488|         print("GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) "
489|               "oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, "
490|               "dann wird die Gegenprobe je Test aussagekraeftig.")
491|     return 0 if not gruen else 1
492| 
493| # ---------------------------------------------------------------- tests-pruefen (K11a)
```

### `scripts/alle_tests.py` def interpreter (Zeilen 69–81) – Muster für die Suchregel

```python
69| def interpreter(rel):
70|     """Nächstes .venv/bin/python vom Ordner der Datei aufwaerts, sonst sys.executable."""
71|     start = (ROOT / rel).resolve().parent
72|     for ordner in [start] + list(start.parents):
73|         if ordner == ROOT:
74|             venv_py = ordner / ".venv" / "bin" / "python"
75|             if venv_py.exists():
76|                 return str(venv_py)
77|             break
78|         venv_py = ordner / ".venv" / "bin" / "python"
79|         if venv_py.exists():
80|             return str(venv_py)
81|     return sys.executable
```

### `mcp-server/kette_werkzeuge.py` def _laeufer (Zeilen 168–192) – warum `sys.executable` aus der Chat-UI das MCP-venv ist

```python
168| def _laeufer(kurztitel: str, kette_py: str, lauf_dir: str, root: str) -> int:
169|     """Eigener Prozess: fuehrt kette.py lauf aus, schreibt Protokoll und Ergebnis, gibt die Sperre frei."""
170|     d = Path(lauf_dir)
171|     start = time.time()
172|     code = -1
173|     log = d / f"{kurztitel}.log"
174|     try:
175|         with log.open("w", encoding="utf-8") as fh:
176|             fh.write(f"# kette.py lauf {kurztitel} – Start {datetime.now().isoformat(timespec='seconds')}\n")
177|             fh.flush()
178|             r = subprocess.run([sys.executable, kette_py, "lauf", kurztitel], cwd=root,
179|                                stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT)
180|             code = r.returncode
181|     except Exception as e:  # Laeufer darf die Sperre nie haengen lassen
182|         with log.open("a", encoding="utf-8") as fh:
183|             fh.write(f"\nFEHLER im Läufer: {type(e).__name__}: {e}\n")
184|     finally:
185|         (d / f"{kurztitel}.json").write_text(
186|             json.dumps({"kurztitel": kurztitel, "exit": code, "start": start, "ende": time.time()}),
187|             encoding="utf-8")
188|         (d / "lauf.lock").unlink(missing_ok=True)
189|     return 0
190| 
191| 
192| # ---------------------------------------------------------------- K3 Status
```

### `tests/test_pruefen_venv.py` (Zeilen 1–179) – Vorgabe-Tests (Meldetexte wörtlich übernehmen)

```python
  1| #!/usr/bin/env python3
  2| """Vorgabe-Tests fuer pruefen_venv (spec_20261107_pruefen_venv.md, T1–T6).
  3| 
  4| VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.
  5| 
  6| Keine Aussenwirkung: Jeder Test (ausser dem Standardwert-Teil von T1) arbeitet in tempfile.TemporaryDirectory()
  7| mit eigenem Git-Repo und umgebogenem kette.ROOT/kette.PM. Das „venv“ im Temp-Repo ist ein Shell-Skript, das seine
  8| Aufrufe in eine Datei ausserhalb des Repos schreibt und das laufende Python mit zusaetzlichem PYTHONPATH startet –
  9| so gibt es ein Modul (nur_im_venv), das nur mit dem venv-Python importierbar ist (wie requests im Pilot).
 10| Kein Netz, kein Modell, kein opencode.
 11| """
 12| import io
 13| import os
 14| import shutil
 15| import stat
 16| import subprocess
 17| import sys
 18| import tempfile
 19| import unittest
 20| from contextlib import redirect_stderr, redirect_stdout
 21| from pathlib import Path
 22| 
 23| ECHT = Path(__file__).resolve().parent.parent
 24| sys.path.insert(0, str(ECHT / "role-split" / "kette"))
 25| import kette  # noqa: E402
 26| 
 27| SPEC_K = "# Spec: k\n\n## Testplan\n\n### T1: t\n- **Prüft:** A1\n"
 28| TEST_K = """import unittest
 29| import nur_im_venv
 30| import code_k
 31| 
 32| 
 33| class T(unittest.TestCase):
 34|     def test_t1_wert(self):
 35|         self.assertEqual(code_k.f(), nur_im_venv.WERT)
 36| """
 37| 
 38| 
 39| class Temp(unittest.TestCase):
 40|     def setUp(self):
 41|         d = tempfile.TemporaryDirectory()
 42|         self.addCleanup(d.cleanup)
 43|         aussen = tempfile.TemporaryDirectory()
 44|         self.addCleanup(aussen.cleanup)
 45|         self.aussen = Path(aussen.name).resolve()
 46|         self.root = Path(d.name).resolve() / "repo"
 47|         self.pm = self.root / "docs" / "projekt_management"
 48|         self.pm.mkdir(parents=True)
 49|         (self.root / "tests").mkdir()
 50|         for name, wert in (("ROOT", self.root), ("PM", self.pm)):
 51|             alt = getattr(kette, name)
 52|             setattr(kette, name, wert)
 53|             self.addCleanup(setattr, kette, name, alt)
 54|         self.aufrufe = self.aussen / "venv_aufrufe.txt"
 55|         (self.root / "nur_venv").mkdir()
 56|         (self.root / "nur_venv" / "nur_im_venv.py").write_text("WERT = 1\n", encoding="utf-8")
 57|         self.venv = self.venv_anlegen(self.root)
 58|         (self.root / ".gitignore").write_text(".venv/\nnur_venv/\n__pycache__/\n", encoding="utf-8")
 59|         (self.root / "code_k.py").write_text("def f():\n    return 0\n", encoding="utf-8")
 60|         (self.root / "tests" / "test_k.py").write_text(TEST_K, encoding="utf-8")
 61|         (self.pm / "spec_20261107_k.md").write_text(SPEC_K, encoding="utf-8")
 62|         self.git("init", "-q")
 63|         self.git("add", ".")
 64|         self.git("commit", "-qm", "Spec k")
 65|         (self.root / "code_k.py").write_text("def f():\n    return 1\n", encoding="utf-8")
 66| 
 67|     def venv_anlegen(self, ordner: Path) -> Path:
 68|         py = ordner / ".venv" / "bin" / "python"
 69|         py.parent.mkdir(parents=True, exist_ok=True)
 70|         py.write_text("#!/bin/sh\n"
 71|                       f'echo "$@" >> "{self.aufrufe}"\n'
 72|                       f'PYTHONPATH="{self.root / "nur_venv"}${{PYTHONPATH:+:$PYTHONPATH}}" exec "{sys.executable}" "$@"\n',
 73|                       encoding="utf-8")
 74|         py.chmod(py.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
 75|         return py
 76| 
 77|     def venv_weg(self):
 78|         shutil.move(str(self.root / ".venv"), str(self.aussen / "venv_weg"))
 79| 
 80|     def git(self, *a):
 81|         return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
 82|                               check=True, capture_output=True, text=True).stdout
 83| 
 84|     def gelesen(self) -> str:
 85|         return self.aufrufe.read_text(encoding="utf-8") if self.aufrufe.exists() else ""
 86| 
 87|     def rufen(self, fn, *a):
 88|         aus = io.StringIO()
 89|         with redirect_stdout(aus), redirect_stderr(aus):
 90|             code = fn(*a)
 91|         return code, aus.getvalue()
 92| 
 93| 
 94| class Auswahl(Temp):
 95| 
 96|     def test_t1_test_python_auswahl(self):
 97|         """T1: test_python – nächstes .venv bis ROOT, Pfad nicht aufgelöst, sonst sys.executable; Standardwert echtes Repo"""
 98|         tp = kette.test_python
 99|         self.assertEqual(tp(self.root / "tests" / "test_k.py"), str(self.venv))
100|         self.assertEqual(tp("tests/test_k.py"), str(self.venv))
101|         unter = self.root / "tests" / "sub"
102|         unter.mkdir()
103|         eigen = self.venv_anlegen(unter)
104|         self.assertEqual(tp(unter / "test_x.py"), str(eigen))
105|         self.assertEqual(tp("tests/test_k.py"), str(self.venv))
106|         self.assertEqual(tp(self.aussen / "test_fremd.py"), sys.executable)
107|         self.venv_anlegen(self.root.parent)
108|         self.venv_weg()
109|         self.assertEqual(tp("tests/test_k.py"), sys.executable, "venv oberhalb von ROOT darf nicht zählen")
110|         link = self.root / ".venv" / "bin" / "python"
111|         link.parent.mkdir(parents=True)
112|         link.symlink_to(sys.executable)
113|         self.assertEqual(tp("tests/test_k.py"), str(link), "venv-Python nicht auflösen")
114|         link.unlink()
115|         link.symlink_to(self.aussen / "gibt_es_nicht")
116|         self.assertEqual(tp("tests/test_k.py"), sys.executable, "kaputter Link zählt nicht")
117|         setattr(kette, "ROOT", ECHT)
118|         echt = ECHT / ".venv" / "bin" / "python"
119|         erwartet = str(echt) if echt.exists() else sys.executable
120|         self.assertEqual(tp("tests/test_pruefen_venv.py"), erwartet)
121|         self.assertEqual(tp(ECHT / "tests" / "test_pruefen_venv.py"), erwartet)
122| 
123| 
124| class Laeufe(Temp):
125| 
126|     def test_t2_tests_laufen_mit_venv(self):
127|         """T2: tests_laufen startet die Tests mit dem venv-Python; ohne venv wie bisher sys.executable"""
128|         erg = kette.tests_laufen(self.root / "tests" / "test_k.py", 60)
129|         self.assertEqual(erg, {"test_t1_wert": "ok"})
130|         self.assertIn("-X pycache_prefix=", self.gelesen())
131|         self.venv_weg()
132|         erg = kette.tests_laufen(self.root / "tests" / "test_k.py", 60)
133|         self.assertNotIn("ok", erg.values(), erg)
134|         self.assertIn("ERROR", erg.values(), erg)
135|         self.assertEqual(self.gelesen().count("pycache_prefix="), 1)
136| 
137|     def test_t3_unittest_mit_venv(self):
138|         """T3: pruefen/unittest mit dem venv-Python, erste Ausgabezeile nennt es"""
139|         teile = kette._pruefen_teile("k")
140|         code, out = teile["unittest"]
141|         self.assertEqual(code, 0, out)
142|         self.assertTrue(out.startswith(f"Python: {self.venv}\n"), out[:200])
143|         self.assertIn("OK", out)
144|         self.assertIn("-m unittest -v tests/test_k.py", self.gelesen())
145| 
146|     def test_t4_unittest_ohne_venv(self):
147|         """T4: ohne venv – unittest mit sys.executable, Zeile nennt es, fehlendes Modul ergibt Abweichung"""
148|         self.venv_weg()
149|         code, out = kette._pruefen_teile("k")["unittest"]
150|         self.assertEqual(code, 1, out)
151|         self.assertTrue(out.startswith(f"Python: {sys.executable}\n"), out[:200])
152|         self.assertIn("nur_im_venv", out)
153|         self.assertEqual(self.gelesen(), "")
154| 
155|     def test_t5_gegenprobe_mit_venv(self):
156|         """T5: gegenprobe läuft mit dem venv-Python und erkennt die zurückgesetzte Datei"""
157|         code, out = kette._pruefen_teile("k")["gegenprobe"]
158|         self.assertEqual(code, 0, out)
159|         self.assertIn("1 von 1 Tests werden durch eine einzelne alte Datei rot.", out)
160|         self.assertIn("code_k.py", out)
161|         self.assertGreaterEqual(self.gelesen().count("pycache_prefix="), 2)
162| 
163| 
164| class Einstieg(Temp):
165| 
166|     def test_t6_pruefen_ueber_main(self):
167|         """T6: kette.main(['pruefen', 'k']) – Prüfdatei nennt das venv-Python, unittest ok"""
168|         code, out = self.rufen(kette.main, ["pruefen", "k"])
169|         datei = self.pm / "pruefung_20261107_k.md"
170|         if not datei.exists():
171|             datei = next(self.root.glob("docs/projekt_management/**/pruefung_*_k.md"))
172|         text = datei.read_text(encoding="utf-8")
173|         self.assertIn(f"## unittest  (Exit 0)\n\n```\nPython: {self.venv}\n", text)
174|         self.assertIn("unittest: ok", out)
175|         self.assertIn("gegenprobe: ok", out)
176| 
177| 
178| if __name__ == "__main__":
179|     unittest.main()
```
