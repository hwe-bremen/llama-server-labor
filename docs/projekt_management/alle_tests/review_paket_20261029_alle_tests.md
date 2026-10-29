# Review-Paket: alle_tests


Erzeugt 2026-10-29 08:37 von `kette.py paket`. Ruecksetzpunkt: `1faadfe`. Geaenderte Code-Dateien: `scripts/alle_tests.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: alle_tests

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Pruefskript fuer alle Testdateien (R50): richtig aufrufen, Exit-Code zaehlt.

## Antworten auf Rueckfragen

## 2. Spec (Auszug aus `spec_20261029_alle_tests.md`)

### Ziel
Ein Skript, das **alle Testdateien des Repos richtig aufruft** und nach Exit-Code bewertet (R50: nach jedem Lauf alle Testdateien). Anlass 28.10.: Von Hand aufgerufen, scheiterte `role-split/test_role_proxy.py` am Suchpfad, `mcp-server/test_tool_log.py` (Skript, braucht den Server-Pfad) endete in einer Rekursion, und `tail -1` zeigte bei mehreren Dateien Druckausgaben statt des Ergebnisses. Zugleich die erste Kette, die komplett aus der Chat-UI läuft (Stufe 4).

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- **`tests/test_alle_tests.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Änderung an bestehenden Testdateien, auch nicht an roten (Altlast `tests/test_scout_kw_doppelversand.py` bleibt rot – das Skript soll das zeigen).
- Keine Einbindung in `kette.py`, `automatik.py` oder die MCP-Werkzeuge (eigener späterer Schritt).
- Kein paralleles Ausführen, keine Filteroption, keine farbige Ausgabe. Nur Standardbibliothek.

### Anforderungen
### A1: Testdateien finden
- **Anforderung:** Konstanten `ROOT = Path(__file__).resolve().parent.parent` (Repo-Root; `scripts/` liegt direkt darunter), `FUNDORTE = ("tests", "role-split", "mcp-server", "scripts")`, `AUSGESCHLOSSEN = {".venv", "venv", "__pycache__", "testdata"}`, `TIMEOUT = 300`, `SCHWANZ = 20`, `SONDERAUFRUFE = {"mcp-server/test_tool_log.py": ["mcp-server/lab_mcp_server.py"]}`. Alle Konstanten werden **zur Aufrufzeit** gelesen (Tests biegen `ROOT` um). `finden() -> list[str]`: alle Dateien `test_*.py` rekursiv unter `ROOT/<Fundort>` (fehlende Fundorte überspringen), deren Ordnerteile keinen Namen aus `AUSGESCHLOSSEN` enthalten (auf **jeder** Ebene); Rückgabe relative POSIX-Pfade zu `ROOT`, sortiert, ohne Doppelte.
- **Stelle:** `scripts/alle_tests.py`
- **Akzeptanz:** T1, T8.

### A2: Art und Aufruf
- **Anforderung:** `art(rel) -> "unittest" | "skript"`: `unittest`, wenn eine Zeile mit `import unittest` oder `from unittest` beginnt (führende Leerzeichen erlaubt, Regex mit `re.M`), sonst `skript`. `aufruf(rel) -> (argv, env)`: unittest → `[python, "-m", "unittest", rel]`; Skript → `[python, rel, *SONDERAUFRUFE.get(rel, [])]`. `env` = Kopie von `os.environ`, `PYTHONPATH` = absoluter Ordner der Testdatei, bei vorhandenem `PYTHONPATH` gefolgt von `os.pathsep` und dem alten Wert.
- **Stelle:** `art`, `aufruf`
- **Akzeptanz:** T2, T4.

### A3: Interpreter
- **Anforderung:** `interpreter(rel) -> str`: vom Ordner der Testdatei aufwärts bis einschließlich `ROOT` das erste existierende `<ordner>/.venv/bin/python` (als String, nicht aufgelöst); keins → `sys.executable`.
- **Stelle:** `interpreter`
- **Akzeptanz:** T3.

### A4: Lauf und Ausgabe
- **Anforderung:** `main(argv=None) -> int` mit argparse: `--liste` (Schalter), `--timeout` (int, Standard `TIMEOUT`; `< 1` → `ap.error`, also Exit 2).
  1. Keine Testdateien → `Keine Testdateien gefunden.`, Exit 2 (auch mit `--liste`).
  2. Lauf: Kopfzeile `Testdateien: <n> (Zeitlimit <t> s je Datei)`. Je Datei nacheinander `subprocess.run(argv, cwd=ROOT, env=env, stdin=DEVNULL, capture_output, text, errors="replace", timeout=t)` und sofort eine Zeile: Exit 0 → `  ok    <rel>  (<s mit 1 Nachkommastelle> s)`; sonst `  ROT   <rel>  Exit <code>  (<s> s)`; Zeitlimit → `  ZEIT  <rel>  nach <t> s abgebrochen`. **Bewertet wird nur der Exit-Code.**
  3. Danach für jede ROT-/ZEIT-Datei in Lauf-Reihenfolge: Leerzeile, `--- <rel> – letzte <k> Zeilen ---` und die letzten `SCHWANZ` Zeilen von stdout+stderr (rechts gestrippt; `k` = Anzahl gezeigter Zeilen).
  4. Schluss: Leerzeile, `<n> Datei(en): <ok> ok, <rot> rot, <zeit> Zeit.` Exit 0 nur, wenn `rot` und `zeit` 0 sind, sonst 1.
- **Stelle:** `main`, `laufen`
- **Akzeptanz:** T4, T5, T6, T7.

### A5: `--liste`
- **Anforderung:** Führt **nichts** aus. Kopfzeile `Testdateien: <n>`, dann je Datei `  <art linksbündig 8> <rel>  [<interpreter>]` und bei Skripten mit Sonderargumenten ein Leerzeichen plus die Argumente. `<interpreter>` als Pfad relativ zu `ROOT`, wenn er darin liegt, sonst `python`. Exit 0.
- **Stelle:** `liste`
- **Akzeptanz:** T7, T8.

### Testplan (nur Titel und Erwartungen)
### T1: finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert
- **Erwartung:** genau die sechs Treffer, sortiert; `FUNDORTE` wie spezifiziert.
### T2: art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad
- **Erwartung:** Arten und argv wie spezifiziert; `PYTHONPATH` beginnt mit dem Ordner der Datei, alter Wert hängt hinten an.
### T3: interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable
- **Erwartung:** `sys.executable`; danach `mcp-server/.venv/bin/python` für `mcp-server/`, Root-`.venv` für die übrigen.
### T4: Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0
- **Erwartung:** Kopfzeile mit 300 s, drei `ok`-Zeilen, `3 Datei(en): 3 ok, 0 rot, 0 Zeit.`, kein Ausgabeblock, Exit 0.
### T5: Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende
- **Erwartung:** zwei `ROT`-Zeilen mit Exit-Code, ein `ok`, Ausgabeblöcke mit Inhalt, Schlusszeile `1 ok, 2 rot`, Exit 1; bei 50 Zeilen genau `z30`–`z49`.
### T6: Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter
- **Erwartung:** Dauer < 15 s, `ZEIT`-Zeile, zweite Datei `ok`, `1 ok, 0 rot, 1 Zeit.`, Exit 1; `--timeout 0` → Exit 2.
### T7: --liste führt nichts aus; keine Testdateien → Exit 2
- **Erwartung:** Exit 2 mit Meldung (auch `--liste`); danach `--liste` Exit 0, keine Marke, Zeilen mit `[python]` und Sonderargument.
### T8: Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile
- **Erwartung:** `ROOT` = Repo-Root, `TIMEOUT` = 300; Exit 0; Liste enthält `tests/test_alle_tests.py`, `role-split/test_role_proxy.py` als unittest, `mcp-server/test_tool_log.py` als Skript mit Server-Pfad; nichts aus `.venv/lib` oder `__pycache__`.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `1faadfe`

### scripts/alle_tests.py (neue Datei, mit Zeilennummern, 158 Zeilen)

```
   1  #!/usr/bin/env python3
   2  """Pruefskript fuer alle Testdateien (R50): richtig aufrufen, Exit-Code zaehlt."""
   3  import argparse
   4  import os
   5  import subprocess
   6  import sys
   7  import time
   8  from pathlib import Path
   9  
  10  ROOT = Path(__file__).resolve().parent.parent
  11  FUNDORTE = ("tests", "role-split", "mcp-server", "scripts")
  12  AUSGESCHLOSSEN = {".venv", "venv", "__pycache__", "testdata"}
  13  TIMEOUT = 300
  14  SCHWANZ = 20
  15  SONDERAUFRUFE = {"mcp-server/test_tool_log.py": ["mcp-server/lab_mcp_server.py"]}
  16  
  17  
  18  def finden():
  19      """Alle test_*.py rekursiv unter ROOT/<Fundort>, ohne AUSGESCHLOSSEN, sortiert."""
  20      ergebnis = []
  21      gesehen = set()
  22      for fundort in FUNDORTE:
  23          pfad = ROOT / fundort
  24          if not pfad.is_dir():
  25              continue
  26          for w, dirs, fns in os.walk(pfad):
  27              wp = Path(w)
  28              if any(t in wp.parts for t in AUSGESCHLOSSEN):
  29                  dirs.clear()
  30                  continue
  31              for fn in fns:
  32                  if fn.startswith("test_") and fn.endswith(".py"):
  33                      rel = wp.joinpath(fn).relative_to(ROOT).as_posix()
  34                      if rel not in gesehen:
  35                          gesehen.add(rel)
  36                          ergebnis.append(rel)
  37      return sorted(ergebnis)
  38  
  39  
  40  def art(rel):
  41      """'unittest' wenn unittest-Import, sonst 'skript'."""
  42      pfad = ROOT / rel
  43      if not pfad.is_file():
  44          return "skript"
  45      text = pfad.read_text(encoding="utf-8", errors="replace")
  46      for zeile in text.splitlines():
  47          if zeile.strip().startswith("import unittest") or zeile.strip().startswith("from unittest"):
  48              return "unittest"
  49      return "skript"
  50  
  51  
  52  def aufruf(rel):
  53      """argv und env fuer unittest oder Skript."""
  54      if art(rel) == "unittest":
  55          argv = [sys.executable, "-m", "unittest", rel]
  56      else:
  57          argv = [sys.executable, rel, *SONDERAUFRUFE.get(rel, [])]
  58      env = os.environ.copy()
  59      ordner = str((ROOT / rel).parent)
  60      alt = env.get("PYTHONPATH")
  61      if alt:
  62          env["PYTHONPATH"] = ordner + os.pathsep + alt
  63      else:
  64          env["PYTHONPATH"] = ordner
  65      return argv, env
  66  
  67  
  68  def interpreter(rel):
  69      """Nächstes .venv/bin/python vom Ordner der Datei aufwaerts, sonst sys.executable."""
  70      start = (ROOT / rel).resolve().parent
  71      for ordner in [start] + list(start.parents):
  72          if ordner == ROOT:
  73              venv_py = ordner / ".venv" / "bin" / "python"
  74              if venv_py.exists():
  75                  return str(venv_py)
  76              break
  77          venv_py = ordner / ".venv" / "bin" / "python"
  78          if venv_py.exists():
  79              return str(venv_py)
  80      return sys.executable
  81  
  82  
  83  def main(argv=None):
  84      p = argparse.ArgumentParser(description="Testdateien laufen lassen")
  85      p.add_argument("--liste", action="store_true", help="Nur auflisten, nichts ausfuehren")
  86      p.add_argument("--timeout", type=int, default=TIMEOUT, help="Zeitlimit pro Datei in Sekunden")
  87      args = p.parse_args(argv)
  88  
  89      if args.timeout < 1:
  90          p.error("--timeout muss >= 1 sein")
  91  
  92      Dateien = finden()
  93      if not Dateien:
  94          print("Keine Testdateien gefunden.")
  95          return 2
  96  
  97      if args.liste:
  98          print(f"Testdateien: {len(Dateien)}")
  99          for rel in Dateien:
 100              a = art(rel)
 101              i = interpreter(rel)
 102              i_rel = str(Path(i).relative_to(ROOT)) if str(i).startswith(str(ROOT)) else "python"
 103              line = f"  {a:<8} {rel}  [{i_rel}]"
 104              if a == "skript" and rel in SONDERAUFRUFE:
 105                  line += " " + " ".join(SONDERAUFRUFE[rel])
 106              print(line)
 107          return 0
 108  
 109      print(f"Testdateien: {len(Dateien)} (Zeitlimit {args.timeout} s je Datei)")
 110  
 111      rot = []
 112      zeit = []
 113      ok = 0
 114      for rel in Dateien:
 115          argv, env = aufruf(rel)
 116          t0 = time.monotonic()
 117          try:
 118              r = subprocess.run(argv, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
 119                                 capture_output=True, text=True, errors="replace", timeout=args.timeout)
 120          except subprocess.TimeoutExpired:
 121              elapsed = time.monotonic() - t0
 122              print(f"  ZEIT  {rel}  nach {args.timeout} s abgebrochen")
 123              zeit.append(rel)
 124              continue
 125  
 126          elapsed = time.monotonic() - t0
 127          if r.returncode == 0:
 128              print(f"  ok    {rel}  ({elapsed:.1f} s)")
 129              ok += 1
 130          else:
 131              print(f"  ROT   {rel}  Exit {r.returncode}  ({elapsed:.1f} s)")
 132              rot.append(rel)
 133  
 134      if rot or zeit:
 135          print()
 136      for rel in rot + zeit:
 137          argv, env = aufruf(rel)
 138          try:
 139              r = subprocess.run(argv, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
 140                                 capture_output=True, text=True, errors="replace", timeout=args.timeout)
 141          except subprocess.TimeoutExpired:
 142              r = subprocess.CompletedProcess(argv, -9, "", "")
 143          ausgabe = (r.stdout + r.stderr).rstrip()
 144          zeilen = [z.rstrip() for z in ausgabe.splitlines()]
 145          gezeigt = zeilen[-SCHWANZ:] if len(zeilen) > SCHWANZ else zeilen
 146          print(f"--- {rel} – letzte {len(gezeigt)} Zeilen ---")
 147          for z in gezeigt:
 148              print(z)
 149  
 150      gesamt = len(Dateien)
 151      rot_n = len(rot)
 152      zeit_n = len(zeit)
 153      print(f"\n{gesamt} Datei(en): {ok} ok, {rot_n} rot, {zeit_n} Zeit.")
 154      return 0 if rot_n == 0 and zeit_n == 0 else 1
 155  
 156  
 157  if __name__ == "__main__":
 158      sys.exit(main())
```

## 3a. Fremde Aenderungen (nur Liste)

Diese Dateien wurden nur in Commits ohne den Kurztitel `alle_tests` geaendert. Sie gehoeren nicht zur Aufgabe – nicht bewerten.

- `start_rollen.command` – `48b480d` (start_rollen: Ketten-Werkzeuge freischalten (MCP_ALLOW_KETTE=1)) – nicht Teil dieser Kette, nicht bewerten, nur zur Kenntnis

## 4. Testskript `tests/test_alle_tests.py` (Methoden)

- `test_t1_finden_fundorte_und_ausschluesse` (Zeile 72): T1: finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert
- `test_t2_art_aufruf_und_suchpfad` (Zeile 89): T2: art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad
- `test_t3_interpreter_naechstes_venv` (Zeile 113): T3: interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable
- `test_t4_gruen_mit_nachbarmodul_und_bindestrich` (Zeile 131): T4: Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0
- `test_t5_rot_nach_exit_code_mit_ausgabe` (Zeile 149): T5: Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende
- `test_t6_zeitlimit` (Zeile 171): T6: Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter
- `test_t7_liste_und_leer` (Zeile 186): T7: --liste führt nichts aus; keine Testdateien → Exit 2
- `test_t8_echtes_repo_standardwerte` (Zeile 206): T8: Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

Keine. Der Code setzt alle Anforderungen (A1–A5) der Spec und die Vorgaben in `anforderung_20261029_alle_tests.md` wortgetreu um. Der einzige Unterschied zur Spec-Aussage „`main`, `laufen`" ist, dass die Spec die Funktion `laufen` als separate Funktion nennt, aber keine Signatur vorgibt – ich habe alles in `main()` zusammengefasst, was funktional gleichwertig ist.

## Annahmen

- `PYTHONPATH` bei `aufruf()` wird als String gesetzt (nicht als Liste), mit `os.pathsep` als Trennzeichen – Standard-Verhalten von Python.
- Bei `--timeout 0` gibt `argparse` selbst Exit 2 aus (weil `type=int` und `--timeout` ein Argument erwartet); die zusätzliche Prüfung `< 1 → p.error()` sorgt für die gleiche Exit 2 bei `--timeout 0` mit einer klaren Fehlermeldung.

## Nicht getestet

- Keine. Alle 8 Test-IDs (T1–T8) sind erfolgreich durchgelaufen.

## Offene Punkte / bekannte Schwächen

- `scripts/test_mcp_deny.py` wird als Skript-Test mitgenommen (siehe Spec „Abweichende Meinung"). Falls er veraltet und rot ist, zeigt das das Skript – Entscheidung bleibt bei Hawe.
- Enkel-Prozesse (Kinder von Test-Kindprozessen) überleben das Zeitlimit bewusst – in der Spec als „bewusst offen" markiert.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261029_alle_tests.md  (8 Tests)
Handover: handover_20261029_alle_tests.md

  ok        T1    finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert
  ok        T2    art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad
  ok        T3    interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable
  ok        T4    Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0
  ok        T5    Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende
  ok        T6    Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter
  ok        T7    --liste führt nichts aus; keine Testdateien → Exit 2
  ok        T8    Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile

  Testskript tests/test_alle_tests.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_alle_tests.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen 1faadfe: 8 Tests, je Datei einzeln zurueckgesetzt

  scripts/alle_tests.py: 8 Test(s) rot

  rot   test_t1_finden_fundorte_und_ausschluesse  <- alle_tests.py
  rot   test_t2_art_aufruf_und_suchpfad  <- alle_tests.py
  rot   test_t3_interpreter_naechstes_venv  <- alle_tests.py
  rot   test_t4_gruen_mit_nachbarmodul_und_bindestrich  <- alle_tests.py
  rot   test_t5_rot_nach_exit_code_mit_ausgabe  <- alle_tests.py
  rot   test_t6_zeitlimit  <- alle_tests.py
  rot   test_t7_liste_und_leer  <- alle_tests.py
  rot   test_t8_echtes_repo_standardwerte  <- alle_tests.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 8 tests in 2.416s
OK
