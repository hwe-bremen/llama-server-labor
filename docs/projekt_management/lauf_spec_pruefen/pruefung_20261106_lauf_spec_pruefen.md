# Pruefung lauf_spec_pruefen

- Zeit: 2026-11-06 16:35
- Ruecksetzpunkt: 2b63547
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261106_lauf_spec_pruefen.md  (6 Tests)
Handover: handover_20261106_lauf_spec_pruefen.md

  ok        T1    Befunde halten vor der Umsetzung
  ok        T2    Größe nur noch Hinweis
  ok        T3    Ausgabe wie der Einzelbefehl
  ok        T4    Vorbedingungen und Exit 2
  ok        T5    Standardwerte und echter Aufruf
  ok        T6    Trockenlauf am echten Bestand

  Testskript tests/test_lauf_spec_pruefen.py: alle 6 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_lauf_spec_pruefen.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t3_ausgabe_wie_einzelbefehl (tests.test_lauf_spec_pruefen.Ablauf.test_t3_ausgabe_wie_einzelbefehl)
T3: lauf – gültige Spec: Ausgabe wie spec-pruefen, danach Umsetzung und Review ... ok
test_t4_vorbedingungen_und_exit_2 (tests.test_lauf_spec_pruefen.Ablauf.test_t4_vorbedingungen_und_exit_2)
T4: lauf – Vorbedingungen vor der Spec-Prüfung, Exit 2 der Spec-Prüfung durchgereicht ... ok
test_t6_trockenlauf_echter_bestand (tests.test_lauf_spec_pruefen.Bestand.test_t6_trockenlauf_echter_bestand)
T6: Trockenlauf am echten Bestand – alte Spec hält, saubere Spec läuft, nichts geschrieben ... ok
test_t5_standardwerte_und_echter_aufruf (tests.test_lauf_spec_pruefen.Einstieg.test_t5_standardwerte_und_echter_aufruf)
T5: Standardwerte – alte Schwellen weg, groesse bleibt, lauf und spec-pruefen über kette.main in frischem Prozess ... ok
test_t1_befunde_halten_vor_der_umsetzung (tests.test_lauf_spec_pruefen.Halt.test_t1_befunde_halten_vor_der_umsetzung)
T1: lauf – Befunde aus spec-pruefen halten mit Exit 3 vor der Umsetzung ... ok
test_t2_groesse_nur_hinweis (tests.test_lauf_spec_pruefen.Halt.test_t2_groesse_nur_hinweis)
T2: lauf – Größe über den alten Schwellen und über R59 hält nicht mehr an ... ok

----------------------------------------------------------------------
Ran 6 tests in 0.432s

OK
```

## gegenprobe gegen 2b63547  (Exit 0)

```
Gegenprobe gegen 2b63547: 6 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/automatik.py: 6 Test(s) rot

  rot   test_t1_befunde_halten_vor_der_umsetzung  <- automatik.py
  rot   test_t2_groesse_nur_hinweis  <- automatik.py
  rot   test_t3_ausgabe_wie_einzelbefehl  <- automatik.py
  rot   test_t4_vorbedingungen_und_exit_2  <- automatik.py
  rot   test_t5_standardwerte_und_echter_aufruf  <- automatik.py
  rot   test_t6_trockenlauf_echter_bestand  <- automatik.py

6 von 6 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
