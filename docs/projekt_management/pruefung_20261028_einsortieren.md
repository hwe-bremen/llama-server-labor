# Pruefung einsortieren

- Zeit: 2026-10-28 16:07
- Ruecksetzpunkt: be29af5
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261028_einsortieren.md  (7 Tests)
Handover: handover_20261028_einsortieren.md

  ok        T1    anforderung – neue Kette bekommt ihren Ordner
  ok        T2    zuordnen – Datei zur Kette, längster Kurztitel gewinnt
  ok        T3    einsortieren <kt> – nur die Dateien dieser Kette, Vorlagen und fremde bleiben
  ok        T4    einsortieren --alle über kette.py – alle Ketten mit Spec oder Anforderung
  ok        T5    einsortieren – vorhandene Datei im Ordner wird nicht überschrieben
  ok        T6    einsortieren – ungültiger Kurztitel, Aufruf ohne Kurztitel und ohne --alle
  ok        T7    einsortieren <kt> – Kette, deren Spec schon im Ordner liegt

  Testskript tests/test_einsortieren.py: alle 7 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_einsortieren.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t1_neue_kette_bekommt_ordner (tests.test_einsortieren.Anlegen.test_t1_neue_kette_bekommt_ordner)
T1: anforderung – neue Kette bekommt ihren Ordner ... ok
test_t3_einsortieren_einer_kette (tests.test_einsortieren.Einsortieren.test_t3_einsortieren_einer_kette)
T3: einsortieren <kt> – nur die Dateien dieser Kette, Vorlagen und fremde bleiben ... ok
test_t4_alle_ueber_main (tests.test_einsortieren.Einsortieren.test_t4_alle_ueber_main)
T4: einsortieren --alle über kette.py – alle Ketten mit Spec oder Anforderung ... ok
test_t5_ziel_belegt (tests.test_einsortieren.Einsortieren.test_t5_ziel_belegt)
T5: einsortieren – vorhandene Datei im Ordner wird nicht überschrieben ... ok
test_t6_falsche_aufrufe (tests.test_einsortieren.Einsortieren.test_t6_falsche_aufrufe)
T6: einsortieren – ungültiger Kurztitel, Aufruf ohne Kurztitel und ohne --alle ... ok
test_t7_kette_ohne_flache_spec (tests.test_einsortieren.Einsortieren.test_t7_kette_ohne_flache_spec)
T7: einsortieren <kt> – Kette, deren Spec schon im Ordner liegt ... ok
test_t2_zuordnen_nach_name (tests.test_einsortieren.Zuordnen.test_t2_zuordnen_nach_name)
T2: zuordnen – Datei zur Kette, längster Kurztitel gewinnt ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.010s

OK
```

## gegenprobe gegen be29af5  (Exit 0)

```
Gegenprobe gegen be29af5: 7 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/einsortieren.py: 7 Test(s) rot
  role-split/kette/kette.py: 2 Test(s) rot

  rot   test_t1_neue_kette_bekommt_ordner  <- einsortieren.py, kette.py
  rot   test_t2_zuordnen_nach_name  <- einsortieren.py
  rot   test_t3_einsortieren_einer_kette  <- einsortieren.py
  rot   test_t4_alle_ueber_main  <- einsortieren.py, kette.py
  rot   test_t5_ziel_belegt  <- einsortieren.py
  rot   test_t6_falsche_aufrufe  <- einsortieren.py
  rot   test_t7_kette_ohne_flache_spec  <- einsortieren.py

7 von 7 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
