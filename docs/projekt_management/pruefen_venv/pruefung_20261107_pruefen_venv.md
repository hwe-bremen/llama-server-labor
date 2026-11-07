# Pruefung pruefen_venv

- Zeit: 2026-11-07 14:19
- Ruecksetzpunkt: c5a523e
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

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

## unittest  (Exit 0)

```
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
Ran 6 tests in 2.343s

OK
```

## gegenprobe gegen c5a523e  (Exit 0)

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
