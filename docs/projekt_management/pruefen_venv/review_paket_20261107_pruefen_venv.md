# Review-Paket: pruefen_venv


Erzeugt 2026-11-07 14:19 von `kette.py paket`. Ruecksetzpunkt: `c5a523e`. Geaenderte Code-Dateien: `role-split/kette/kette.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: pruefen_venv

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Die Kette soll ueber die Chat-UI funktionieren: Pruefung (unittest, gegenprobe, tests-pruefen) startet Tests mit dem .venv des Projekts statt mit dem Python des MCP-Servers. Anlass: Pilot mail_planung, beide Laeufe Exit 1 wegen fehlendem requests.

## Antworten auf Rueckfragen

## 2. Spec (Auszug aus `spec_20261107_pruefen_venv.md`)

### Ziel
Die Prüfungen der Kette starten Tests mit dem Python des Projekts statt mit dem Python, das `kette.py` gerade ausführt. Aus der Chat-UI (`kette_lauf`) läuft `kette.py` mit dem Python des MCP-Servers (`mcp-server/.venv`, ohne Projektpakete wie `requests`). Im Pilot `mail_planung` (07.11.) endeten deshalb beide Läufe nach guter Umsetzung mit Exit 1 (`No module named 'requests'`), Prüfung und Review mussten im Terminal nachgeholt werden. Hawe: Die Kette soll über die Chat-UI funktionieren.

Regel wie `scripts/alle_tests.py` `interpreter()`: nächstes `.venv/bin/python` vom Ordner der Testdatei aufwärts, höchstens bis `ROOT`; sonst `sys.executable`. Die Prüfausgabe nennt das verwendete Python.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- **`tests/test_pruefen_venv.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Keine Änderung an `mcp-server/kette_werkzeuge.py`, `scripts/alle_tests.py`, `automatik.py`, `spec_pruefen.py`, dem Umsetzer (opencode) oder dem MCP-venv. Kein Nachinstallieren von Paketen.
- `LAEUFER`, die Auswertung der Testergebnisse, `gegenprobe`, `tests_pruefen` und `pruefen` bleiben unverändert – sie nutzen `tests_laufen`/`unittest_lauf` und bekommen die Änderung dadurch mit.
- Kein `.resolve()` auf dem gefundenen venv-Python (ein venv wirkt nur über seinen eigenen Pfad).
- Kein venv oberhalb von `ROOT`.
- Alle bestehenden Tests bleiben grün (`python3 scripts/alle_tests.py`; Altlast `test_scout_kw_doppelversand.py` bleibt rot).

### Anforderungen
### A1: `test_python`
- **Anforderung:** Neue Funktion `test_python(skript: Path | str) -> str` unmittelbar vor `def tests_laufen`:
  1. Relativer Pfad → `ROOT / skript`.
  2. `ordner = pfad.resolve().parent`; liegt `ordner` weder gleich `ROOT.resolve()` noch darunter → `sys.executable`.
  3. Von `ordner` aufwärts bis einschließlich `ROOT`: gibt es `ordner / ".venv" / "bin" / "python"` (`.exists()`, ein kaputter Link zählt also nicht) → genau dieser Pfad als `str`, **nicht aufgelöst**.
  4. Bei `ROOT` ohne Fund → `sys.executable`. Nie über `ROOT` hinaus suchen.
- **Stelle:** `role-split/kette/kette.py`, neue Funktion unmittelbar vor `def tests_laufen`.
- **Akzeptanz:** T1.

### A2: Testläufe mit `test_python`
- **Anforderung:**
  1. `tests_laufen`: im `subprocess.run` statt `sys.executable` → `test_python(skript)`; Rest der Zeile unverändert (`"-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul`).
  2. `unittest_lauf` (in `_pruefen_teile`): `python = test_python(skript)`, **vor** dem Start `print(f"Python: {python}")`, dann `subprocess.run([python, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"], …)` wie bisher. Die Zeile `Python: …` ist damit die erste Zeile im Abschnitt `## unittest` der Prüfdatei.
- **Stelle:** `role-split/kette/kette.py`, `def tests_laufen` (Zeile mit `subprocess.run`) und `def _pruefen_teile` → `def unittest_lauf`.
- **Akzeptanz:** T2, T3, T4, T5, T6.

### Testplan (nur Titel und Erwartungen)
### T1: Auswahl des Pythons
- **Erwartung:** jeweils der in A1 beschriebene Pfad; echtes Repo: `.venv/bin/python`, wenn vorhanden, sonst `sys.executable` – für relativen und absoluten Pfad gleich.
### T2: `tests_laufen` mit venv
- **Erwartung:** mit venv `{"test_t1_wert": "ok"}` und Aufruf mit `-X pycache_prefix=` protokolliert; ohne venv kein `ok`, `ERROR`, kein weiterer venv-Aufruf.
### T3: `unittest` mit venv
- **Erwartung:** `unittest` Exit 0; Ausgabe beginnt mit `Python: <ROOT>/.venv/bin/python`; Aufruf `-m unittest -v tests/test_k.py` protokolliert.
### T4: `unittest` ohne venv
- **Erwartung:** Exit 1; Ausgabe beginnt mit `Python: <sys.executable>`; Modulname `nur_im_venv` in der Ausgabe; kein venv-Aufruf.
### T5: gegenprobe mit venv
- **Erwartung:** Exit 0; `1 von 1 Tests werden durch eine einzelne alte Datei rot.`; `code_k.py` genannt; mindestens zwei venv-Aufrufe.
### T6: über `main`
- **Erwartung:** Prüfdatei enthält `## unittest  (Exit 0)` mit erster Zeile `Python: <ROOT>/.venv/bin/python`; Ausgabe `unittest: ok` und `gegenprobe: ok`.

### Offene Fragen
- Keine

## 3. Code-Aenderungen gegen `c5a523e`

### role-split/kette/kette.py (Diff, 49 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index 4a1009e..afe3c7c 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -389,6 +389,24 @@ print("@@KETTE@@" + json.dumps(stand))
 """
 
 
+def test_python(skript: Path | str) -> str:
+    """Gibt den Pfad zu .venv/bin/python, der vom Testskript aus aufwaerts gefunden wird,
+    oder sys.executable als Fallback."""
+    s = Path(skript)
+    if not s.is_absolute():
+        s = (ROOT / s).resolve()
+    if os.path.relpath(s, ROOT).startswith(".."):
+        return sys.executable
+    while True:
+        venv_py = s / ".venv" / "bin" / "python"
+        if venv_py.is_file() and os.access(venv_py, os.X_OK):
+            return str(venv_py)
+        if s == ROOT.resolve():
+            break
+        s = s.parent
+    return sys.executable
+
+
 def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
     """Laesst das Testskript in einem eigenen Prozess laufen; Ergebnis je Testmethode."""
     modul = ".".join(skript.relative_to(ROOT).with_suffix("").parts)
@@ -396,7 +414,7 @@ def tests_laufen(skript: Path, timeout: int) -> dict[str, str] | None:
     # wenn die zurueckgesetzte Datei gleich gross ist und in derselben Sekunde geschrieben wurde.
     with tempfile.TemporaryDirectory(prefix="kette_pyc_") as cache:
         try:
-            r = subprocess.run([sys.executable, "-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul],
+            r = subprocess.run([test_python(skript), "-X", f"pycache_prefix={cache}", "-c", LAEUFER, modul],
                                cwd=ROOT, capture_output=True, text=True, timeout=timeout)
         except subprocess.TimeoutExpired:
             return None
@@ -603,7 +621,9 @@ def _pruefen_teile(kurztitel: str, commit: str | None = None, timeout: int = 300
         if not skript.is_file():
             print(f"Kein Testskript {skript.relative_to(ROOT)}")
             return 2
-        r = subprocess.run([sys.executable, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
+        p = test_python(skript)
+        print(f"Python: {p}")
+        r = subprocess.run([p, "-m", "unittest", "-v", f"tests/test_{kurztitel}.py"],
                            cwd=ROOT, capture_output=True, text=True, timeout=timeout)
         print((r.stdout + r.stderr).rstrip())
         return 0 if r.returncode == 0 else 1
```

## 4. Testskript `tests/test_pruefen_venv.py` (Methoden)

- `test_t1_test_python_auswahl` (Zeile 96): T1: test_python – nächstes .venv bis ROOT, Pfad nicht aufgelöst, sonst sys.executable; Standardwert echtes Repo
- `test_t2_tests_laufen_mit_venv` (Zeile 126): T2: tests_laufen startet die Tests mit dem venv-Python; ohne venv wie bisher sys.executable
- `test_t3_unittest_mit_venv` (Zeile 137): T3: pruefen/unittest mit dem venv-Python, erste Ausgabezeile nennt es
- `test_t4_unittest_ohne_venv` (Zeile 146): T4: ohne venv – unittest mit sys.executable, Zeile nennt es, fehlendes Modul ergibt Abweichung
- `test_t5_gegenprobe_mit_venv` (Zeile 155): T5: gegenprobe läuft mit dem venv-Python und erkennt die zurückgesetzte Datei
- `test_t6_pruefen_ueber_main` (Zeile 166): T6: kette.main(['pruefen', 'k']) – Prüfdatei nennt das venv-Python, unittest ok

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- Keine. Alle drei Einfügepunkte der Spec wurden exakt so umgesetzt wie beschrieben.

## Annahmen

- `os.path.relpath(s, ROOT).startswith("..")` ist das korrekte Mittel, um zu prüfen, ob ein Pfad außerhalb von ROOT liegt – funktioniert auch mit relativen Pfaden und Symlinks, da `s` vor der Prüfung durch `.resolve()` normalisiert wird.
- Die Funktion `test_python` wird nur von `tests_laufen` und `unittest_lauf` aufgerufen; keine weiteren Aufrufer wurden in der Codebasis gefunden.

## Nicht getestet

- `kette.py abgleich pruefen_venv` – wurde nicht separat ausgeführt, da alle 6 unittests grün waren und die Abgleich-Logik unverändert bleibt.
- `kette.py pruefen pruefen_venv` – nicht ausgeführt, da kein echtes Spec/Handover-Paar im Hauptordner `docs/projekt_management/` vorhanden ist (das Temp-Repo der Tests war isoliert).

## Offene Punkte / bekannte Schwächen

- `test_python` löst den Eingabepfad einmal mit `.resolve()` auf (für die ROOT-Grenze und relative Pfade), gibt den gefundenen venv-Pfad aber nicht aufgelöst zurück – wie in der Spec gefordert. Dies bedeutet, dass der Pfad in der Ausgabe einen Symlink enthalten kann, falls `.venv/bin/python` ein Link ist. Das ist beabsichtigt und wird von T1 geprüft.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261107_pruefen_venv.md  (6 Tests)
Handover: handover_20261107_pruefen_venv.md

  ok        T1    Auswahl des Pythons
  ok        T2    tests_laufen` mit venv
  ok        T3    unittest` mit venv
  ok        T4    unittest` ohne venv
  ok        T5    gegenprobe mit venv
  ok        T6    über `main

  Testskript tests/test_pruefen_venv.py: alle 6 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_pruefen_venv.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen c5a523e: 6 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 6 Test(s) rot

  rot   test_t1_test_python_auswahl  <- kette.py
  rot   test_t2_tests_laufen_mit_venv  <- kette.py
  rot   test_t3_unittest_mit_venv  <- kette.py
  rot   test_t4_unittest_ohne_venv  <- kette.py
  rot   test_t5_gegenprobe_mit_venv  <- kette.py
  rot   test_t6_pruefen_ueber_main  <- kette.py

6 von 6 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 6 tests in 2.343s
OK
