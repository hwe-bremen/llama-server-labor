# Quellen Schritt 2 (6 ok, 6 schlecht)

- UNKLAR - `role-split/kette/kette.py` BESTAND – Konstante für Bestandstests
- UNKLAR - `role-split/kette/kette.py` GIT_SCHUTZ – Liste geschützter Dateien
- ZU LANG tests/test_kette_review_auto.py (517 Zeilen)
- ZU LANG tests/test_umsetzung_auto.py (476 Zeilen)
- ZU LANG tests/test_scout_bericht_ueberschreiben.py (614 Zeilen)
- ZU LANG tests/test_mail_planung.py (964 Zeilen)

### `role-split/kette/kette.py` def pruefen (Zeilen 615–642) – Haupteinstieg für den Befehl

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

### `role-split/kette/kette.py` def _schreibbereich (Zeilen 1630–1639) – Prüfung des Schreibbereichs

```python
1630| def _schreibbereich(spec_text: str) -> list[str] | None:
1631|     """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
1632|     if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
1633|         return None
1634|     eintraege = []
1635|     for z in abschnitt(spec_text, "Schreibbereich").splitlines():
1636|         m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
1637|         if m:
1638|             eintraege.append(m.group(1)[2:] if m.group(1).startswith("./") else m.group(1))
1639|     return eintraege
```

### `role-split/kette/kette.py` def _pruefung_kurz (Zeilen 821–832) – Formatierung des Prüfergebnisses

```python
821| def _pruefung_kurz(pfad: Path | None) -> str:
822|     if not pfad:
823|         return "(keine Pruefung gefunden – vorher `kette.py pruefen <kurztitel>` laufen lassen)"
824|     text = pfad.read_text(encoding="utf-8")
825|     kurz = re.search(r"^- Kurz:.*$", text, re.M)
826|     teile = [kurz.group(0) if kurz else ""]
827|     for titel in ("abgleich", "gegenprobe"):
828|         teile.append(f"#### {titel}\n{abschnitt(text, titel).strip()}")
829|     ut = abschnitt(text, "unittest")
830|     zus = [z for z in ut.splitlines() if re.match(r"^(Ran |OK|FAILED|FAIL:|ERROR:)", z)]
831|     teile.append("#### unittest (Zusammenfassung)\n" + ("\n".join(zus) or "(keine Zusammenfassung)"))
832|     return "\n\n".join(t for t in teile if t)
```

### `docs/projekt_management/_vorlage_spec.md` (Zeilen 1–100) – Vorlage für Pflichtabschnitte und Platzhalter

```markdown
  1| # Spec: <kurztitel>
  2| 
  3| - **Datum:** <JJJJ-MM-TT>
  4| - **Modell:** <Modellname aus dem System-Prompt>
  5| - **Betroffene Dateien:** <nur Dateien, die du gelesen hast>
  6| 
  7| ## Ziel
  8| 
  9| <1–3 Sätze>
 10| 
 11| ## Nicht-Ziele
 12| 
 13| - <…>
 14| 
 15| ## Schreibbereich
 16| 
 17| <!-- Dateien/Ordner, die die Umsetzung ändern darf, z. B. role-split/kette/ oder einzelne Pfade. Ordner mit „/" am Ende. -->
 18| Pflicht für `kette.py umsetzung-auto` (ohne diesen Abschnitt: Exit 2). Eine Zeile je Eintrag, Pfad in Backticks, relativ
 19| zum Repo. `tests/test_<kurztitel>.py` und der Handover sind immer erlaubt; Spec, Anforderung, Quellen und Vorlagen nie.
 20| 
 21| - `pfad/datei.py`
 22| - `pfad/ordner/`
 23| 
 24| ## Vorgabe-Tests
 25| 
 26| <!-- Optional (ab K11a). Nur wenn die Tests VOR der Umsetzung geschrieben werden (R48); sonst Abschnitt löschen. -->
 27| Mit diesem Abschnitt ist `tests/test_<kurztitel>.py` Vorgabe: Sie wird mit der Spec committet, vor dem Erstlauf von
 28| `kette.py tests-pruefen <kurztitel>` geprüft (je Test-ID eine Methode, Skript lädt, jeder Test rot vorab) und darf von der
 29| Umsetzung nicht geändert werden. Tests für bestehendes Verhalten tragen `(Bestand)` im Titel und müssen vorab grün sein (R49).
 30| 
 31| - `tests/test_<kurztitel>.py`
 32| 
 33| ## Außenwirkung und Sperre
 34| 
 35| - **Was kann die Aufgabe außerhalb des Repos auslösen?** <Mail, Netzwerk, echte Daten/DB, Schlüsselbund, launchd … oder „nichts">
 36| - **Technische Sperre für Tests:** <z. B. Variable, die echten Versand erst erlaubt; temporäres Datenverzeichnis. Eine Regel im Prompt reicht nicht.>
 37| 
 38| ## Einstiegspunkte
 39| 
 40| Welche geänderten Dateien werden **wie** gestartet (Pipeline, launchd, von Hand, als Modul importiert)?
 41| Für jeden Einstiegspunkt gibt es einen Test, der ihn so startet wie im Betrieb (ohne Außenwirkung, z. B.
 42| `runpy.run_path(…, run_name="kein_main")` für Imports, Ersatzskripte für Pipelines).
 43| Anlass 18.10.: Ein relativer Import ließ den Scout bei jedem Lauf abstürzen; alle Funktionstests waren grün.
 44| 
 45| | Datei | Wie gestartet | Test |
 46| |---|---|---|
 47| | `pfad/skript.py` | `python3 pfad/skript.py` aus `run_x.sh` | T… |
 48| 
 49| ## Quellen
 50| 
 51| Jede Konstante, jedes Dateiformat, jede Schnittstelle oder Option, die die Umsetzung braucht, als Fundstelle im Repo –
 52| **nichts aus dem Gedächtnis**. Eine Zeile je Quelle, Pfad in Backticks, dann `Zeilen a–b` oder `def Name` / `class Name`
 53| (ohne Angabe: ganze Datei, max. 400 Zeilen), dann Zweck. `kette.py quellen <kurztitel>` holt die Auszüge danach
 54| maschinell und wörtlich nach `quellen_<JJJJMMTT>_<kurztitel>.md`. Was nicht im Repo steht (externe Doku, Format
 55| eines Fremdprogramms), kommt unter „Offene Fragen" – Hawe legt die Quelle dann als Datei ins Repo.
 56| 
 57| - `pfad/datei.py` def funktion – wofür gebraucht
 58| - `pfad/datei.py` Zeilen 10–40 – wofür gebraucht
 59| 
 60| ## Anforderungen
 61| 
 62| ### A1: <Titel>
 63| - **Anforderung:** <prüfbar formuliert>
 64| - **Stelle:** <Datei, Funktion>
 65| - **Akzeptanz:** <beobachtbares Ergebnis>
 66| 
 67| ## Fehlerpfade
 68| 
 69| Für **jede** Anforderung jede Frage durchspielen. Zeilen ohne Befund trotzdem eintragen („unverändert", „n. a.").
 70| 
 71| | Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
 72| |---|---|---|---|---|
 73| | A1 | Gegenstelle antwortet nicht oder schweigt (Netz, Server, Router) | | | T… |
 74| | A1 | Eingabe leer oder ungültig (Variable, Datei, Argument) | | | |
 75| | A1 | Ziel existiert schon (Datei, Eintrag) — wird etwas überschrieben? | | | |
 76| | A1 | Schalter kombiniert (z. B. Trockenlauf + anderer Modus) | | | |
 77| | A1 | Lauf ohne Testschalter / gegen echte Daten | | | |
 78| | A1 | Absturz mitten im Lauf | | | |
 79| 
 80| ## Testplan
 81| 
 82| Alle Tests werden als `tests/test_<kurztitel>.py` (unittest) umgesetzt, je Test eine Methode `test_<id>_…`. Kein Test hat Außenwirkung.
 83| Nach der Umsetzung prüft `kette.py gegenprobe`, welche Tests mit dem alten Code rot werden. Neue Funktionen im Test daher **in der Methode** importieren, nicht am Dateianfang, sonst lädt das ganze Testskript mit altem Code nicht und die Gegenprobe sagt je Test nichts.
 84| 
 85| ### T1: <Titel>
 86| - **Prüft:** A1, Fehlerpfad „…"
 87| - **Aufbau:** <Testserver, temporäres Verzeichnis, Umgebungsvariablen>
 88| - **Erwartung:** <prüfbare Bedingung: Exit-Code, Datei existiert, Dauer ≥ x s …>
 89| - **Warum misst der Test das Richtige?** <ein Satz: woran würde der Test scheitern, wenn die Anforderung NICHT erfüllt ist?>
 90| - **Gegenprobe:** <welche Datei bzw. welche Codezeile muss im alten Zustand sein, damit dieser Test rot wird? „keine" = Test prüft Bestehendes, dann begründen>
 91| 
 92| <!-- Test für bestehendes Verhalten mit Vorgabe-Tests: „### T2: <Titel> (Bestand)“ – muss vorab grün sein. -->
 93| 
 94| ## Offene Fragen
 95| 
 96| - <… oder „Keine">
 97| 
 98| ## Abweichende Meinung
 99| 
100| - <… oder „Keine">
```

### `tests/test_vorgabe_tests.py` (Zeilen 1–174) – Beispiel für Validierung von Tests

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

### `tests/test_mcp_kette.py` (Zeilen 1–340) – Beispiel für Schnittstellenprüfung

```python
  1| #!/usr/bin/env python3
  2| """Vorgabe-Tests fuer mcp_kette (spec_20261028_mcp_kette.md, T1–T8).
  3| 
  4| VORGABE: Diese Datei ist vor der Umsetzung geschrieben. Die Umsetzung aendert sie nicht.
  5| 
  6| Keine Aussenwirkung: Jeder Test arbeitet in tempfile.TemporaryDirectory() mit umgebogenem
  7| kette_werkzeuge.ROOT / KETTE_PY / LAUF_DIR. Statt kette.py laeuft ein Ersatzskript, das nur
  8| schlaeft und druckt; git nur in einem Wegwerf-Repo im Temp-Verzeichnis.
  9| kette_werkzeuge wird in jeder Methode importiert (rot vorab).
 10| """
 11| import ast
 12| import json
 13| import os
 14| import signal
 15| import subprocess
 16| import sys
 17| import tempfile
 18| import time
 19| import unittest
 20| from pathlib import Path
 21| from unittest import mock
 22| 
 23| ECHT = Path(__file__).resolve().parent.parent
 24| sys.path.insert(0, str(ECHT / "mcp-server"))
 25| 
 26| ERSATZ = '''import os, sys, time
 27| cmd, kt = sys.argv[1], sys.argv[2]
 28| if cmd == "lauf":
 29|     print(f"Groesse: lauf {kt}")
 30|     time.sleep(float(os.environ.get("ERSATZ_DAUER", "1")))
 31|     print("HALT – Entscheidung Hawe.")
 32|     sys.exit(int(os.environ.get("ERSATZ_EXIT", "3")))
 33| if cmd == "status":
 34|     print(f"Status {kt}")
 35|     print("Naechster Schritt: Ersatz")
 36|     sys.exit(0)
 37| sys.exit(9)
 38| '''
 39| 
 40| SPEC = """# Spec: k
 41| 
 42| ## Schreibbereich
 43| 
 44| - `pkg/`
 45| - `einzeln.py`
 46| 
 47| ## Vorgabe-Tests
 48| 
 49| - `tests/test_k.py`
 50| """
 51| 
 52| 
 53| def kw():
 54|     import kette_werkzeuge
 55|     return kette_werkzeuge
 56| 
 57| 
 58| class Temp(unittest.TestCase):
 59|     def setUp(self):
 60|         d = tempfile.TemporaryDirectory()
 61|         self.addCleanup(d.cleanup)
 62|         self.root = Path(d.name).resolve()
 63|         self.laeufe = self.root / "laeufe"
 64|         self.ersatz = self.root / "ersatz_kette.py"
 65|         self.ersatz.write_text(ERSATZ, encoding="utf-8")
 66|         self.env = mock.patch.dict(os.environ, {"ERSATZ_DAUER": "1", "ERSATZ_EXIT": "3"})
 67|         self.env.start()
 68|         self.addCleanup(self.env.stop)
 69| 
 70|     def modul(self):
 71|         m = kw()
 72|         for name, wert in (("ROOT", self.root), ("KETTE_PY", self.ersatz), ("LAUF_DIR", self.laeufe)):
 73|             alt = getattr(m, name)
 74|             setattr(m, name, wert)
 75|             self.addCleanup(setattr, m, name, alt)
 76|         self.addCleanup(self.aufraeumen, m)
 77|         return m
 78| 
 79|     def aufraeumen(self, m):
 80|         for p in list(getattr(m, "_PROZESSE", [])):
 81|             try:
 82|                 p.wait(timeout=30)
 83|             except Exception:
 84|                 p.kill()
 85|         m._PROZESSE.clear()
 86| 
 87|     def warten_fertig(self, kt, sek=30):
 88|         ende = time.time() + sek
 89|         while time.time() < ende:
 90|             if (self.laeufe / f"{kt}.json").is_file() and not (self.laeufe / "lauf.lock").exists():
 91|                 return json.loads((self.laeufe / f"{kt}.json").read_text(encoding="utf-8"))
 92|             time.sleep(0.1)
 93|         self.fail(f"Lauf {kt} nach {sek} s nicht fertig")
 94| 
 95|     def git(self, *a):
 96|         return subprocess.run(["git", "-C", str(self.root), *a], capture_output=True, text=True, check=True).stdout
 97| 
 98| 
 99| class Gemeinsam(Temp):
100| 
101|     def test_t1_ungueltiger_kurztitel(self):
102|         """T1: Ungültiger Kurztitel – jedes Werkzeug meldet FEHLER und tut nichts"""
103|         m = self.modul()
104|         for kt in ("../x", "K", "", "a b", "k;rm"):
105|             for fn in (m.kette_status, m.kette_lauf, m.kette_ergebnis, m.kette_commit):
106|                 out = fn(kt)
107|                 self.assertIsInstance(out, str)
108|                 self.assertTrue(out.startswith("FEHLER"), f"{fn.__name__}({kt!r}): {out}")
109|                 self.assertIn("ungültig", out, f"{fn.__name__}({kt!r}): Kurztitel nicht geprüft")
110|         self.assertFalse(self.laeufe.exists(), "Lauf-Ordner darf nicht angelegt werden")
111|         self.assertEqual(m._PROZESSE, [])
112| 
113| 
114| class Lauf(Temp):
115| 
116|     def test_t2_lauf_kehrt_sofort_zurueck_und_laeuft_durch(self):
117|         """T2: kette_lauf kehrt sofort zurück; Läufer schreibt Protokoll und Ergebnis und gibt die Sperre frei"""
118|         m = self.modul()
119|         os.environ["ERSATZ_DAUER"] = "2"
120|         t0 = time.monotonic()
121|         out = m.kette_lauf("k")
122|         dauer = time.monotonic() - t0
123|         self.assertLess(dauer, 1.5, f"blockiert {dauer:.1f} s")
124|         self.assertTrue(out.startswith("Lauf gestartet: k"), out)
125|         self.assertIn('kette_status(kurztitel="k")', out)
126|         self.assertTrue((self.laeufe / "lauf.lock").is_file(), "Sperre fehlt während des Laufs")
127|         sperre = json.loads((self.laeufe / "lauf.lock").read_text(encoding="utf-8"))
128|         self.assertEqual(sperre["kurztitel"], "k")
129|         e = self.warten_fertig("k")
130|         self.assertEqual(e["exit"], 3)
131|         self.assertEqual(e["kurztitel"], "k")
132|         self.assertGreaterEqual(e["ende"] - e["start"], 1.5)
133|         log = (self.laeufe / "k.log").read_text(encoding="utf-8")
134|         self.assertIn("Groesse: lauf k", log)
135|         self.assertIn("HALT", log)
136|         self.assertIsNone(m.laufender())
137| 
138|     def test_t3_nur_ein_lauf_und_schreibsperre(self):
139|         """T3: Während eines Laufs: zweiter Start und Commit abgelehnt; danach wieder frei"""
140|         m = self.modul()
141|         os.environ["ERSATZ_DAUER"] = "3"
142|         self.assertTrue(m.kette_lauf("k").startswith("Lauf gestartet"))
143|         out = m.kette_lauf("k2")
144|         self.assertTrue(out.startswith("ABGELEHNT"), out)
145|         self.assertIn("k", out)
146|         self.assertTrue(m.kette_lauf("k").startswith("ABGELEHNT"))
147|         self.assertTrue(m.kette_commit("k").startswith("ABGELEHNT"))
148|         self.assertEqual(len(m._PROZESSE), 1, "es darf nur ein Läufer gestartet sein")
149|         self.assertFalse((self.laeufe / "k2.log").exists())
150|         self.warten_fertig("k")
151|         os.environ["ERSATZ_DAUER"] = "0"
152|         self.assertTrue(m.kette_lauf("k2").startswith("Lauf gestartet: k2"))
153|         self.assertEqual(self.warten_fertig("k2")["exit"], 3)
154| 
155|     def test_t4_verwaiste_sperre(self):
156|         """T4: Verwaiste Sperre (toter Prozess, alte Sperre ohne pid) wird entfernt; frische ohne pid gilt als belegt"""
157|         m = self.modul()
158|         self.laeufe.mkdir()
159|         tot = subprocess.Popen([sys.executable, "-c", "pass"])
160|         tot.wait()
161|         sperre = self.laeufe / "lauf.lock"
162|         sperre.write_text(json.dumps({"kurztitel": "alt", "start": time.time(), "pid": tot.pid}), encoding="utf-8")
163|         self.assertIsNone(m.laufender())
164|         self.assertFalse(sperre.exists(), "verwaiste Sperre (toter Prozess) nicht entfernt")
165|         sperre.write_text(json.dumps({"kurztitel": "alt", "start": time.time() - 3600, "pid": None}),
166|                           encoding="utf-8")
167|         self.assertIsNone(m.laufender())
168|         self.assertFalse(sperre.exists(), "alte Sperre ohne pid nicht entfernt")
169|         sperre.write_text(json.dumps({"kurztitel": "alt", "start": time.time(), "pid": None}), encoding="utf-8")
170|         self.assertTrue(m.kette_lauf("k").startswith("ABGELEHNT"))
171|         sperre.write_text("kaputt", encoding="utf-8")
172|         os.environ["ERSATZ_DAUER"] = "0"
173|         self.assertTrue(m.kette_lauf("k").startswith("Lauf gestartet"), "kaputte Sperre muss als verwaist gelten")
174|         self.warten_fertig("k")
175|         os.environ["ERSATZ_DAUER"] = "30"
176|         self.assertTrue(m.kette_lauf("k").startswith("Lauf gestartet"))
177|         laeufer = m._PROZESSE[-1]
178|         os.killpg(laeufer.pid, signal.SIGKILL)
179|         time.sleep(0.5)
180|         self.assertTrue(sperre.exists(), "Sperre bleibt nach hartem Abbruch liegen")
181|         self.assertIsNone(m.laufender(), "abgeschossener Läufer (Zombie) gilt noch als lebend")
182|         self.assertFalse(sperre.exists())
183| 
184| 
185| class Anzeige(Temp):
186| 
187|     def test_t5_status(self):
188|         """T5: kette_status – keiner / läuft / letzter Exit, jeweils mit der Ausgabe von kette.py status"""
189|         m = self.modul()
190|         out = m.kette_status("k")
191|         self.assertTrue(out.startswith("Lauf: keiner"), out)
192|         self.assertIn("Status k", out)
193|         self.assertIn("Exit 0", out)
194|         os.environ["ERSATZ_DAUER"] = "2"
195|         m.kette_lauf("k")
196|         out = m.kette_status("k")
197|         self.assertTrue(out.startswith("Lauf: läuft (k"), out)
198|         self.assertIn("Status k", out)
199|         self.warten_fertig("k")
200|         out = m.kette_status("k")
201|         self.assertTrue(out.startswith("Lauf: letzter Lauf Exit 3"), out)
202| 
203|     def test_t6_ergebnis(self):
204|         """T6: kette_ergebnis – ohne Protokoll, nach dem Lauf, nur das Ende langer Protokolle"""
205|         m = self.modul()
206|         self.assertTrue(m.kette_ergebnis("k").startswith("Kein Protokoll für k"))
207|         os.environ["ERSATZ_DAUER"] = "0"
208|         m.kette_lauf("k")
209|         self.warten_fertig("k")
210|         out = m.kette_ergebnis("k")
211|         self.assertTrue(out.startswith("Lauf k: Exit 3"), out)
212|         self.assertIn("HALT", out)
213|         (self.laeufe / "lang.log").write_text("\n".join(f"zeile {i}" for i in range(200)) + "\n",
214|                                               encoding="utf-8")
215|         (self.laeufe / "lang.json").write_text(json.dumps({"kurztitel": "lang", "exit": 0, "start": 1, "ende": 2}),
216|                                                encoding="utf-8")
217|         out = m.kette_ergebnis("lang")
218|         self.assertIn("zeile 199", out)
219|         self.assertIn("zeile 120", out)
220|         self.assertNotIn("zeile 119\n", out)
221|         self.assertIn("Letzte 80 von 200 Zeilen", out)
222| 
223| 
224| class Commit(Temp):
225| 
226|     def repo(self):
227|         self.git("init", "-q")
228|         self.git("config", "user.name", "Test")
229|         self.git("config", "user.email", "test@example.invalid")
230|         pm = self.root / "docs" / "projekt_management" / "k"
231|         pm.mkdir(parents=True)
232|         (pm / "spec_20261028_k.md").write_text(SPEC, encoding="utf-8")
233|         (self.root / "pkg").mkdir()
234|         (self.root / "pkg" / "a.py").write_text("A = 1\n", encoding="utf-8")
235|         (self.root / "alt.py").write_text("x\n", encoding="utf-8")
236|         self.git("add", "-A")
237|         self.git("commit", "-q", "-m", "Start")
238|         return self.git("rev-parse", "HEAD").strip()
239| 
240|     def test_t7_commit_zwei_schritte_nur_erlaubte_dateien(self):
241|         """T7: kette_commit – Vorschau ohne Commit, falscher Code abgelehnt, richtiger Code committet nur Erlaubtes"""
242|         m = self.modul()
243|         self.laeufe.mkdir()
244|         start = self.repo()
245|         (self.root / "pkg" / "a.py").write_text("A = 2\n", encoding="utf-8")
246|         (self.root / "pkg" / "neu.py").write_text("B = 1\n", encoding="utf-8")
247|         (self.root / "tests").mkdir()
248|         (self.root / "tests" / "test_k.py").write_text("# t\n", encoding="utf-8")
249|         (self.root / "docs" / "projekt_management" / "k" / "handover_20261028_k.md").write_text("h\n", encoding="utf-8")
250|         (self.root / "fremd.txt").write_text("f\n", encoding="utf-8")
251|         (self.root / "alt.py").unlink()
252|         (self.root / "vorgemerkt.txt").write_text("v\n", encoding="utf-8")
253|         self.git("add", "vorgemerkt.txt")
254| 
255|         out = m.kette_commit("k")
256|         self.assertTrue(out.startswith("Vorschau Commit k"), out)
257|         self.assertEqual(self.git("rev-parse", "HEAD").strip(), start, "Vorschau darf nicht committen")
258|         self.assertIn("Im Commit (4)", out)
259|         for p in ("pkg/a.py", "pkg/neu.py", "tests/test_k.py", "docs/projekt_management/k/handover_20261028_k.md"):
260|             self.assertIn(p, out)
261|         self.assertIn("Nicht im Commit (3)", out)
262|         code = out.split("Bestätigungscode: ")[1].split()[0]
263|         self.assertRegex(code, r"^[0-9a-f]{6}$")
264| 
265|         out = m.kette_commit("k", "000000" if code != "000000" else "111111")
266|         self.assertTrue(out.startswith("ABGELEHNT"), out)
267|         self.assertEqual(self.git("rev-parse", "HEAD").strip(), start)
268| 
269|         out = m.kette_commit("k", code)
270|         self.assertTrue(out.startswith("Committet:"), out)
271|         self.assertNotEqual(self.git("rev-parse", "HEAD").strip(), start)
272|         namen = set(self.git("show", "--name-only", "--format=", "HEAD").split())
273|         self.assertEqual(namen, {"pkg/a.py", "pkg/neu.py", "tests/test_k.py",
274|                                  "docs/projekt_management/k/handover_20261028_k.md"})
275|         self.assertTrue(self.git("log", "-1", "--format=%s").startswith("Kette k:"))
276|         rest = self.git("status", "--porcelain")
277|         self.assertIn("fremd.txt", rest)
278|         self.assertIn("alt.py", rest)
279|         self.assertIn("vorgemerkt.txt", rest, "vorher Vorgemerktes darf nicht mitgenommen werden")
280|         self.assertEqual(self.git("diff", "--cached", "--name-only").split(), ["vorgemerkt.txt"],
281|                          "fremde Dateien dürfen nicht vorgemerkt werden")
282| 
283|         self.assertTrue(m.kette_commit("k").startswith("Nichts zu committen für k"))
284|         self.assertTrue(m.kette_commit("ohne_spec").startswith("FEHLER"))
285| 
286| 
287| class Einstieg(unittest.TestCase):
288| 
289|     def test_t8_registrierung_und_server(self):
290|         """T8: registrieren meldet genau vier Werkzeuge an; lab_mcp_server schaltet sie nur mit MCP_ALLOW_KETTE=1 frei"""
291|         m = kw()
292| 
293|         class Attrappe:
294|             def __init__(self):
295|                 self.namen = []
296| 
297|             def tool(self, *a, **k):
298|                 def deco(fn):
299|                     self.namen.append(fn.__name__)
300|                     self.assertdoc(fn)
301|                     return fn
302|                 return deco
303| 
304|             def assertdoc(self, fn):
305|                 if not (fn.__doc__ or "").strip():
306|                     raise AssertionError(f"{fn.__name__} ohne Beschreibung")
307| 
308|         a = Attrappe()
309|         namen = m.registrieren(a)
310|         erwartet = ["kette_status", "kette_lauf", "kette_ergebnis", "kette_commit"]
311|         self.assertEqual(sorted(a.namen), sorted(erwartet))
312|         self.assertEqual(sorted(namen), sorted(erwartet))
313|         self.assertIn("nicht erneut", m.kette_lauf.__doc__.lower())
314|         self.assertIn("zustimmung", m.kette_commit.__doc__.lower())
315| 
316|         quelle = (ECHT / "mcp-server" / "lab_mcp_server.py").read_text(encoding="utf-8")
317|         baum = ast.parse(quelle)
318|         texte = {n.value for n in ast.walk(baum) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
319|         self.assertIn("MCP_ALLOW_KETTE", texte)
320|         aufrufe = [n for n in ast.walk(baum) if isinstance(n, ast.Call)
321|                    and isinstance(n.func, ast.Attribute) and n.func.attr == "registrieren"]
322|         self.assertEqual(len(aufrufe), 1, "registrieren(mcp) genau einmal aufrufen")
323|         ifs = [n for n in ast.walk(baum) if isinstance(n, ast.If)
324|                and any(c is aufrufe[0] for c in ast.walk(n))]
325|         self.assertTrue(ifs, "registrieren muss hinter einer Bedingung stehen")
326|         self.assertTrue(any("ALLOW_KETTE" in ast.unparse(n.test) for n in ifs),
327|                         "Bedingung muss ALLOW_KETTE prüfen")
328|         zuw = [n for n in ast.walk(baum) if isinstance(n, ast.Assign)
329|                and any(isinstance(z, ast.Name) and z.id == "ALLOW_KETTE" for z in n.targets)]
330|         self.assertEqual(len(zuw), 1, "ALLOW_KETTE genau einmal zuweisen")
331|         self.assertIn("MCP_ALLOW_KETTE", ast.unparse(zuw[0].value))
332|         self.assertIn("READONLY", ast.unparse(zuw[0].value), "mit MCP_READONLY=1 muss es aus sein")
333| 
334|         r = subprocess.run([sys.executable, str(ECHT / "mcp-server" / "kette_werkzeuge.py")],
335|                            capture_output=True, text=True, timeout=30)
336|         self.assertEqual(r.returncode, 2, "ohne --laeufer: Exit 2")
337| 
338| 
339| if __name__ == "__main__":
340|     unittest.main()
```
