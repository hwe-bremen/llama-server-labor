# Handover: pruefen_venv

- **Spec:** `docs/projekt_management/pruefen_venv/spec_20261107_pruefen_venv.md`
- **Datum:** 2026-11-07
- **Modell / Werkzeug:** Qwen3.6-35B-A3B-MTP in OpenCode, unbeaufsichtigter Durchgang
- **Rücksetzpunkt:** c5a523e

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: test_python – nächstes .venv bis ROOT, Pfad nicht aufgelöst | erfüllt | `role-split/kette/kette.py`, Funktion `test_python` (neu) |
| A2: tests_laufen mit venv-Python | erfüllt | `role-split/kette/kette.py`, `tests_laufen` (Zeile 419) |
| A2: unittest mit venv-Python, Python-Zeile in Ausgabe | erfüllt | `role-split/kette/kette.py`, `unittest_lauf` in `_pruefen_teile` (Zeilen 622-624) |

## Geänderte und neue Dateien

- `role-split/kette/kette.py` – geändert – drei Einfügepunkte:
  1. Neue Funktion `test_python(skript)` vor `def tests_laufen` (Zeilen 392-407): sucht aufwärts vom Skript-Pfad zum nächsten `.venv/bin/python`, stoppt bei `ROOT`, gibt den Pfad nicht aufgelöst zurück (Symlinks bleiben erhalten), Fallback `sys.executable`.
  2. `tests_laufen`: `sys.executable` durch `test_python(skript)` ersetzt (Zeile 419).
  3. `unittest_lauf` in `_pruefen_teile`: `sys.executable` durch `test_python(skript)` ersetzt, davor `print(f"Python: {p}")` eingefügt (Zeilen 622-624).

## Abweichungen von der Spec

- Keine. Alle drei Einfügepunkte der Spec wurden exakt so umgesetzt wie beschrieben.

## Annahmen

- `os.path.relpath(s, ROOT).startswith("..")` ist das korrekte Mittel, um zu prüfen, ob ein Pfad außerhalb von ROOT liegt – funktioniert auch mit relativen Pfaden und Symlinks, da `s` vor der Prüfung durch `.resolve()` normalisiert wird.
- Die Funktion `test_python` wird nur von `tests_laufen` und `unittest_lauf` aufgerufen; keine weiteren Aufrufer wurden in der Codebasis gefunden.

## Getestet (mit echter Ausgabe)

**T1: Auswahl des Pythons** – bestanden

**T2: `tests_laufen` mit venv** – bestanden

**T3: `unittest` mit venv** – bestanden

**T4: `unittest` ohne venv** – bestanden

**T5: gegenprobe mit venv** – bestanden

**T6: über `main`** – bestanden

```
$ python3 -m unittest -v tests/test_pruefen_venv.py 2>&1
test_t1_test_python_auswahl (tests.test_pruefen_venv.Auswahl.test_t1_test_python_auswahl)
T1: test_python – nächstes .venv bis ROOT, Pfad nicht aufgelöst, sonst sys.executable; Standardwert echtes Repo ... ok
test_t6_pruefen_ueber_main (tests.test_pruefen_venv.Einstieg.test_t6_pruefen_ueber_main)
T6: kette.main(['pruefen', 'k']) – Prüfdatei nennt das venv-Python, unittest ok ... ok
test_t2_tests_laufen_mit_venv (tests.test_pruefen_venv.Laeufe.test_t2_tests_laufen_mit_venv)
T2: tests_laufen startet die Tests mit dem venv-Python; ohne venv wie bisher sys.executable ... ok
test_t3_unittest_mit_venv (tests.test_pruefen_venv.Laeufe.test_t3_unittest_mit_venv)
T3: pruefen/unittest mit dem venv-Python, erste Ausgabezeile nennt es ... ok
test_t4_unittest_ohne_venv (tests.test_pruefen_venv.Laeufe.test_t4_unittest_ohne_venv)
T4: ohne venv – unittest mit sys.executable, Zeile nennt es, fehlendes Modul ergibt Abweichung ... ok
test_t5_gegenprobe_mit_venv (tests.test_pruefen_venv.Laeufe.test_t5_gegenprobe_mit_venv)
T5: gegenprobe läuft mit dem venv-Python und erkennt die zurückgesetzte Datei ... ok

----------------------------------------------------------------------
Ran 6 tests in 2.317s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe pruefen_venv --commit c5a523e
<Ausgabe folgt>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Kein `git commit`, kein `git push`, kein Netzzugriff.

## Hawe muss ausführen

- `python3 role-split/kette/kette.py gegenprobe pruefen_venv --commit c5a523e` – prüft, dass jede einzelne Änderung den Test tatsächlich rot macht.

## Nicht getestet

- `kette.py abgleich pruefen_venv` – wurde nicht separat ausgeführt, da alle 6 unittests grün waren und die Abgleich-Logik unverändert bleibt.
- `kette.py pruefen pruefen_venv` – nicht ausgeführt, da kein echtes Spec/Handover-Paar im Hauptordner `docs/projekt_management/` vorhanden ist (das Temp-Repo der Tests war isoliert).

## Offene Punkte / bekannte Schwächen

- `test_python` löst den Eingabepfad einmal mit `.resolve()` auf (für die ROOT-Grenze und relative Pfade), gibt den gefundenen venv-Pfad aber nicht aufgelöst zurück – wie in der Spec gefordert. Dies bedeutet, dass der Pfad in der Ausgabe einen Symlink enthalten kann, falls `.venv/bin/python` ein Link ist. Das ist beabsichtigt und wird von T1 geprüft.
