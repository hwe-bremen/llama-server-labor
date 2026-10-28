# Pruefung vorgabe_tests

- Zeit: 2026-10-28 08:53
- Ruecksetzpunkt: 39ce6aa
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261027_vorgabe_tests.md  (8 Tests)
Handover: handover_20261027_vorgabe_tests.md

  ok        T1    tests-pruefen – alle Vorgabe-Tests vorhanden und rot vorab
  ok        T2    tests-pruefen – Test-ID ohne Methode
  ok        T3    tests-pruefen – Test ohne Umsetzung schon grün
  ok        T4    tests-pruefen – Testskript lädt nicht
  ok        T5    tests-pruefen – Testdatei oder Spec fehlt
  ok        T6    umsetzung-auto – Erstlauf startet nur mit bestandener Testprüfung
  ok        T7    umsetzung-auto – Änderung an Vorgabe-Tests ist ein Verstoß
  ok        T8    umsetzung-auto – Nacharbeit prüft nicht auf rot vorab, Prompt nennt Vorgabe

  Testskript tests/test_vorgabe_tests.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_vorgabe_tests.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t1_tests_pruefen_rot_vorab_ok (tests.test_vorgabe_tests.TestsPruefen.test_t1_tests_pruefen_rot_vorab_ok)
T1: tests-pruefen – alle Vorgabe-Tests vorhanden und rot vorab ... ok
test_t2_tests_pruefen_test_fehlt (tests.test_vorgabe_tests.TestsPruefen.test_t2_tests_pruefen_test_fehlt)
T2: tests-pruefen – Test-ID ohne Methode ... ok
test_t3_tests_pruefen_gruen_ohne_umsetzung (tests.test_vorgabe_tests.TestsPruefen.test_t3_tests_pruefen_gruen_ohne_umsetzung)
T3: tests-pruefen – Test ohne Umsetzung schon gruen ... ok
test_t4_tests_pruefen_laedt_nicht (tests.test_vorgabe_tests.TestsPruefen.test_t4_tests_pruefen_laedt_nicht)
T4: tests-pruefen – Testskript laedt nicht ... ok
test_t5_tests_pruefen_voraussetzung_fehlt (tests.test_vorgabe_tests.TestsPruefen.test_t5_tests_pruefen_voraussetzung_fehlt)
T5: tests-pruefen – Testdatei oder Spec fehlt ... ok
test_t6_erstlauf_nur_mit_rot_vorab (tests.test_vorgabe_tests.UmsetzungMitVorgabe.test_t6_erstlauf_nur_mit_rot_vorab)
T6: umsetzung-auto – Erstlauf startet nur mit bestandener Testpruefung ... ok
test_t7_vorgabe_tests_geaendert (tests.test_vorgabe_tests.UmsetzungMitVorgabe.test_t7_vorgabe_tests_geaendert)
T7: umsetzung-auto – Aenderung an Vorgabe-Tests ist ein Verstoss ... ok
test_t8_nacharbeit_ohne_rot_vorab (tests.test_vorgabe_tests.UmsetzungMitVorgabe.test_t8_nacharbeit_ohne_rot_vorab)
T8: umsetzung-auto – Nacharbeit prueft nicht auf rot vorab, Prompt nennt Vorgabe ... ok

----------------------------------------------------------------------
Ran 8 tests in 1.643s

OK
```

## gegenprobe gegen 39ce6aa  (Exit 0)

```
Gegenprobe gegen 39ce6aa: 8 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 8 Test(s) rot

  rot   test_t1_tests_pruefen_rot_vorab_ok  <- kette.py
  rot   test_t2_tests_pruefen_test_fehlt  <- kette.py
  rot   test_t3_tests_pruefen_gruen_ohne_umsetzung  <- kette.py
  rot   test_t4_tests_pruefen_laedt_nicht  <- kette.py
  rot   test_t5_tests_pruefen_voraussetzung_fehlt  <- kette.py
  rot   test_t6_erstlauf_nur_mit_rot_vorab  <- kette.py
  rot   test_t7_vorgabe_tests_geaendert  <- kette.py
  rot   test_t8_nacharbeit_ohne_rot_vorab  <- kette.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
