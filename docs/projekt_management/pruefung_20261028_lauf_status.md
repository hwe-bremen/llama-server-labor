# Pruefung lauf_status

- Zeit: 2026-10-28 12:20
- Ruecksetzpunkt: c9469ed
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261028_lauf_status.md  (8 Tests)
Handover: handover_20261028_lauf_status.md

  ok        T1    lauf – ohne Commit „Spec <kt>“ kein Start
  ok        T2    lauf – ohne Abschnitt Vorgabe-Tests kein Start
  ok        T3    lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es
  ok        T4    lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung
  ok        T5    lauf – Umsetzung nicht in Ordnung, kein Review
  ok        T6    lauf – Review nicht PASS ergibt Exit 1
  ok        T7    status – Stand und nächster Schritt aus den Dateien
  ok        T8    main – lauf und status über kette.py

  Testskript tests/test_lauf_status.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_lauf_status.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t8_main_lauf_und_status (tests.test_lauf_status.Einstieg.test_t8_main_lauf_und_status)
T8: main – lauf und status über kette.py ... ok
test_t4_lauf_ok_bis_halt (tests.test_lauf_status.LaufAblauf.test_t4_lauf_ok_bis_halt)
T4: lauf – Umsetzung und Review grün, Halt an Hawes Entscheidung ... ok
test_t5_lauf_umsetzung_rot (tests.test_lauf_status.LaufAblauf.test_t5_lauf_umsetzung_rot)
T5: lauf – Umsetzung nicht in Ordnung, kein Review ... ok
test_t6_lauf_review_nicht_pass (tests.test_lauf_status.LaufAblauf.test_t6_lauf_review_nicht_pass)
T6: lauf – Review nicht PASS ergibt Exit 1 ... ok
test_t1_lauf_ohne_spec_commit (tests.test_lauf_status.LaufVorab.test_t1_lauf_ohne_spec_commit)
T1: lauf – ohne Commit „Spec <kt>“ kein Start ... ok
test_t2_lauf_ohne_vorgabe_tests (tests.test_lauf_status.LaufVorab.test_t2_lauf_ohne_vorgabe_tests)
T2: lauf – ohne Abschnitt Vorgabe-Tests kein Start ... ok
test_t3_lauf_zu_gross (tests.test_lauf_status.LaufVorab.test_t3_lauf_zu_gross)
T3: lauf – Größenprüfung hält bei Überschreitung, an der Schwelle läuft es ... ok
test_t7_status_naechster_schritt (tests.test_lauf_status.Status.test_t7_status_naechster_schritt)
T7: status – Stand und nächster Schritt aus den Dateien ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.501s

OK
```

## gegenprobe gegen c9469ed  (Exit 0)

```
Gegenprobe gegen c9469ed: 8 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/automatik.py: 8 Test(s) rot
  role-split/kette/kette.py: 1 Test(s) rot

  rot   test_t1_lauf_ohne_spec_commit  <- automatik.py
  rot   test_t2_lauf_ohne_vorgabe_tests  <- automatik.py
  rot   test_t3_lauf_zu_gross  <- automatik.py
  rot   test_t4_lauf_ok_bis_halt  <- automatik.py
  rot   test_t5_lauf_umsetzung_rot  <- automatik.py
  rot   test_t6_lauf_review_nicht_pass  <- automatik.py
  rot   test_t7_status_naechster_schritt  <- automatik.py
  rot   test_t8_main_lauf_und_status  <- automatik.py, kette.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
