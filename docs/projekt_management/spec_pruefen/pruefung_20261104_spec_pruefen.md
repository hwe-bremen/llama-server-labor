# Pruefung spec_pruefen

- Zeit: 2026-11-04 21:56
- Ruecksetzpunkt: 031d296
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261104_spec_pruefen.md  (8 Tests)
Handover: handover_20261104_spec_pruefen.md

  ok        T1    Gültige Spec – keine Befunde, genaue Ausgabe, nichts geschrieben
  ok        T2    Pflichtabschnitte fehlen oder sind leer
  ok        T3    Platzhalter der Vorlage und offene Fragen
  ok        T4    Änderungsstellen Pflicht, Größe über R59 nur Hinweis
  ok        T5    Stelle und Prüft-Zuordnung
  ok        T6    Schreibbereich und Quellen
  ok        T7    Aufruf über `kette.main` und Fehlerpfade
  ok        T8    Standardwerte und Trockenlauf am echten Bestand

  Testskript tests/test_spec_pruefen.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_spec_pruefen.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t1_gueltige_spec_keine_befunde (tests.test_spec_pruefen.TestSpecPruefen.test_t1_gueltige_spec_keine_befunde) ... ok
test_t2_pflichtabschnitte_fehlen_oder_leer (tests.test_spec_pruefen.TestSpecPruefen.test_t2_pflichtabschnitte_fehlen_oder_leer) ... ok
test_t3_platzhalter_und_offene_fragen (tests.test_spec_pruefen.TestSpecPruefen.test_t3_platzhalter_und_offene_fragen) ... ok
test_t4_aenderungsstellen_und_groesse_nur_hinweis (tests.test_spec_pruefen.TestSpecPruefen.test_t4_aenderungsstellen_und_groesse_nur_hinweis) ... ok
test_t5_stelle_und_prueft_zuordnung (tests.test_spec_pruefen.TestSpecPruefen.test_t5_stelle_und_prueft_zuordnung) ... ok
test_t6_schreibbereich_und_quellen (tests.test_spec_pruefen.TestSpecPruefen.test_t6_schreibbereich_und_quellen) ... ok
test_t7_aufruf_ueber_kette_main_und_fehlerpfade (tests.test_spec_pruefen.TestSpecPruefen.test_t7_aufruf_ueber_kette_main_und_fehlerpfade) ... ok
test_t8_standardwerte_und_trockenlauf_am_echten_bestand (tests.test_spec_pruefen.TestSpecPruefen.test_t8_standardwerte_und_trockenlauf_am_echten_bestand) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.205s

OK
```

## gegenprobe gegen 031d296  (Exit 0)

```
Gegenprobe gegen 031d296: 8 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 2 Test(s) rot
  role-split/kette/spec_pruefen.py: 8 Test(s) rot

  rot   test_t1_gueltige_spec_keine_befunde  <- spec_pruefen.py
  rot   test_t2_pflichtabschnitte_fehlen_oder_leer  <- spec_pruefen.py
  rot   test_t3_platzhalter_und_offene_fragen  <- spec_pruefen.py
  rot   test_t4_aenderungsstellen_und_groesse_nur_hinweis  <- spec_pruefen.py
  rot   test_t5_stelle_und_prueft_zuordnung  <- spec_pruefen.py
  rot   test_t6_schreibbereich_und_quellen  <- spec_pruefen.py
  rot   test_t7_aufruf_ueber_kette_main_und_fehlerpfade  <- kette.py, spec_pruefen.py
  rot   test_t8_standardwerte_und_trockenlauf_am_echten_bestand  <- kette.py, spec_pruefen.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
