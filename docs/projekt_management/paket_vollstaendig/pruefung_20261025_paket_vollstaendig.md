# Pruefung paket_vollstaendig

- Zeit: 2026-10-26 22:26
- Ruecksetzpunkt: 84e3bb7
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: Abweichung

## abgleich  (Exit 1)

```
Spec:     spec_20261025_paket_vollstaendig.md  (10 Tests)
Handover: handover_20261026_paket_vollstaendig.md

  ok        T1    Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)
  ok        T2    Paket enthält Dateien unter tests/ und role-split/, auch unversionierte
  ok        T3    Handover-Datei ohne Markierung, fremde Datei mit Markierung
  ok        T4    Vorrang-Kürzung – Vorrang 3 wird weggelassen
  ok        T5    KETTE_PAKET_MAX überschritten → Exit 1
  ok        T6    Gegenprobe berücksichtigt role-split/kette/
  ok        T7    Bestehende Tests in test_kette.py bleiben grün
  ok        T8    Fremde Commits nur als Liste
  ok        T9    Paket ohne Code trotz Änderungen → Exit 1
  NICHT GET T10   Abnahme – echter Lauf am K7-Stand (Hawe, manuell)  (unter 'Nicht getestet' -- Grund pruefen)

  Testskript tests/test_paket_vollstaendig.py: keine Methode test_<id> fuer T10
  Selbst ausfuehren: python3 -m unittest -v tests/test_paket_vollstaendig.py

2 Abweichung(en).
```

## unittest  (Exit 0)

```
test_k1_nur_docs_geaendert_exit_0 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_k1_nur_docs_geaendert_exit_0)
K1: Nur docs/ geaendert -> Exit 0, 'keine Code-Dateien' ... ok
test_k2_kurztitel_als_ganzes_wort (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_k2_kurztitel_als_ganzes_wort)
K2: Kurztitel 'g' trifft nicht 'gross' -> Datei aus 'gross init' ist fremd ... ok
test_t1_fehlerpfade_von_paket (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t1_fehlerpfade_von_paket)
T1: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel) ... ok
test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte)
T2: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte ... ok
test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung)
T3: Handover-Datei ohne Markierung, fremde Datei mit Markierung ... ok
test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen)
T4: Vorrang-Kürzung – Vorrang 3 wird weggelassen ... ok
test_t5_kette_paket_max_ueberschritten_exit_1 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t5_kette_paket_max_ueberschritten_exit_1)
T5: KETTE_PAKET_MAX überschritten → Exit 1 ... ok
test_t6_gegenprobe_beruecksichtigt_role_split_kette (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t6_gegenprobe_beruecksichtigt_role_split_kette)
T6: Gegenprobe berücksichtigt role-split/kette/ ... ok
test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen)
T7: Bestehende Tests in test_kette.py bleiben grün ... ok
test_t8_fremde_commits_nur_als_liste (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t8_fremde_commits_nur_als_liste)
T8: Fremde Commits nur als Liste ... ok
test_t9_paket_ohne_code_trotz_aenderungen_exit_1 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t9_paket_ohne_code_trotz_aenderungen_exit_1)
T9: Paket ohne Code trotz Änderungen → Exit 1 ... ok

----------------------------------------------------------------------
Ran 11 tests in 2.937s

OK
```

## gegenprobe gegen 84e3bb7  (Exit 1)

```
Gegenprobe gegen 84e3bb7: 11 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 9 Test(s) rot
  role-split/kette/test_kette.py: 1 Test(s) rot

  GRUEN test_k1_nur_docs_geaendert_exit_0  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_k2_kurztitel_als_ganzes_wort  <- kette.py
  GRUEN test_t1_fehlerpfade_von_paket  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t2_paket_enthaelt_dateien_unter_tests_und_role_split_auch_unversionierte  <- kette.py
  rot   test_t3_handover_datei_ohne_markierung_fremde_datei_mit_markierung  <- kette.py
  rot   test_t4_vorrang_kuerzung_vorrang_3_wird_weggelassen  <- kette.py
  rot   test_t5_kette_paket_max_ueberschritten_exit_1  <- kette.py
  rot   test_t6_gegenprobe_beruecksichtigt_role_split_kette  <- kette.py
  rot   test_t7_bestehende_tests_in_test_kette_py_bleiben_gruen  <- kette.py, test_kette.py
  rot   test_t8_fremde_commits_nur_als_liste  <- kette.py
  rot   test_t9_paket_ohne_code_trotz_aenderungen_exit_1  <- kette.py

9 von 11 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, dann wird die Gegenprobe je Test aussagekraeftig.
```
