# Pruefung vorgabe_nachtrag

- Zeit: 2026-10-28 10:01
- Ruecksetzpunkt: 404fefb
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261028_vorgabe_nachtrag.md  (4 Tests)
Handover: handover_20261028_vorgabe_nachtrag.md

  ok        T1    tests-pruefen – Bestand-Test grün ist in Ordnung; Spec ohne Test-ID ist Exit 2
  ok        T2    tests-pruefen – Bestand-Test rot ist eine Abweichung; --timeout wird weitergereicht
  ok        T3    gegenprobe – grüner Bestand-Test laut Spec ist keine Abweichung
  ok        T4    umsetzung-auto – Nacharbeit startet nicht, solange die Vorgabe-Tests offene Änderungen haben

  Testskript tests/test_vorgabe_nachtrag.py: alle 4 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_vorgabe_nachtrag.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t3_gegenprobe_bestand_gruen_zaehlt_nicht (tests.test_vorgabe_nachtrag.GegenprobeBestand.test_t3_gegenprobe_bestand_gruen_zaehlt_nicht)
T3: gegenprobe – gruener Bestand-Test laut Spec ist keine Abweichung ... ok
test_t4_nacharbeit_mit_offener_testdatei (tests.test_vorgabe_nachtrag.NacharbeitVorgabe.test_t4_nacharbeit_mit_offener_testdatei)
T4: umsetzung-auto – Nacharbeit startet nicht, solange die Vorgabe-Tests offene Aenderungen haben ... ok
test_t1_bestand_gruen_ok_und_spec_ohne_ids (tests.test_vorgabe_nachtrag.TestsPruefenBestand.test_t1_bestand_gruen_ok_und_spec_ohne_ids)
T1: tests-pruefen – Bestand-Test gruen ist in Ordnung; Spec ohne Test-ID ist Exit 2 ... ok
test_t2_bestand_rot_und_timeout_weitergereicht (tests.test_vorgabe_nachtrag.TestsPruefenBestand.test_t2_bestand_rot_und_timeout_weitergereicht)
T2: tests-pruefen – Bestand-Test rot ist eine Abweichung; --timeout wird weitergereicht ... ok

----------------------------------------------------------------------
Ran 4 tests in 1.120s

OK
```

## gegenprobe gegen 404fefb  (Exit 0)

```
Gegenprobe gegen 404fefb: 4 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 4 Test(s) rot

  rot   test_t1_bestand_gruen_ok_und_spec_ohne_ids  <- kette.py
  rot   test_t2_bestand_rot_und_timeout_weitergereicht  <- kette.py
  rot   test_t3_gegenprobe_bestand_gruen_zaehlt_nicht  <- kette.py
  rot   test_t4_nacharbeit_mit_offener_testdatei  <- kette.py

4 von 4 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
