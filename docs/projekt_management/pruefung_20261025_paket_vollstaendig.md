# Pruefung paket_vollstaendig

- Zeit: 2026-10-26 06:49
- Ruecksetzpunkt: 84e3bb7
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: ok

## abgleich  (Exit 1)

```
Spec:     spec_20261025_paket_vollstaendig.md  (10 Tests)
Handover: handover_20261025_paket_vollstaendig.md

  ANDERS    T1    Spec: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)
                  Handover: docs/ und .md-Dateien nie im Paket (PAKET_NIE)** – bestanden   (Uebereinstimmung 10% -- ausgetauscht?)
  ANDERS    T2    Spec: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte
                  Handover: KETTE_PAKET_MAX als Konstante vorhanden und > 0** – bestanden   (Uebereinstimmung 11% -- ausgetauscht?)
  ANDERS    T3    Spec: Handover-Datei ohne Markierung, fremde Datei mit Markierung
                  Handover: Dateien in Commits mit Kurztitel gehoeren zur Kette** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  ANDERS    T4    Spec: Vorrang-Kürzung – Vorrang 3 wird weggelassen
                  Handover: Fremde Dateien erscheinen in separater Sektion** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  ANDERS    T5    Spec: KETTE_PAKET_MAX überschritten → Exit 1
                  Handover: Dateien nicht im Handover werden markiert** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  ANDERS    T6    Spec: Gegenprobe berücksichtigt role-split/kette/
                  Handover: Vorrang-Klassifikation funktioniert korrekt** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  ANDERS    T7    Spec: Bestehende Tests in test_kette.py bleiben grün
                  Handover: Paket > KETTE_PAKET_MAX -> Exit 1** – bestanden   (Uebereinstimmung 17% -- ausgetauscht?)
  ANDERS    T8    Spec: Fremde Commits nur als Liste
                  Handover: Gegenprobe nimmt role-split/kette/ auf** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  ok        T9    Paket ohne Code trotz Änderungen → Exit 1
  FEHLT     T10   Abnahme – echter Lauf am K7-Stand (Hawe, manuell)

  Testskript tests/test_paket_vollstaendig.py: keine Methode test_<id> fuer T10
  Selbst ausfuehren: python3 -m unittest -v tests/test_paket_vollstaendig.py

10 Abweichung(en).
```

## unittest  (Exit 0)

```
test_t1_docs_excluded (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t1_docs_excluded)
T1: docs/ und .md-Dateien nie im Paket (PAKET_NIE). ... ok
test_t2_kette_paket_max_exists (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t2_kette_paket_max_exists)
T2: KETTE_PAKET_MAX als Konstante vorhanden und > 0. ... ok
test_t3_ketten_dateien_im_paket (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t3_ketten_dateien_im_paket)
T3: Dateien in Commits mit Kurztitel gehoeren zur Kette. ... ok
test_t4_fremde_dateien_liste (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t4_fremde_dateien_liste)
T4: Fremde Dateien erscheinen in separater Sektion. ... ok
test_t5_nicht_genannt_markierung (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t5_nicht_genannt_markierung)
T5: Dateien nicht im Handover werden markiert. ... ok
test_t6_vorrang_klassifikation (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t6_vorrang_klassifikation)
T6: Vorrang-Klassifikation funktioniert korrekt. ... ok
test_t7_harte_obergrenze_exit1 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t7_harte_obergrenze_exit1)
T7: Paket > KETTE_PAKET_MAX -> Exit 1. ... ok
test_t8_gegenprobe_role_split (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t8_gegenprobe_role_split)
T8: Gegenprobe nimmt role-split/kette/ auf. ... ok
test_t9_paket_ohne_code_exit1 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t9_paket_ohne_code_exit1)
T9: Paket ohne Code trotz Aenderungen -> Exit 1. ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.010s

OK
```

## gegenprobe gegen 84e3bb7  (Exit 0)

```
Gegenprobe gegen 84e3bb7: 9 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 9 Test(s) rot
  role-split/kette/test_kette.py: 0 Test(s) rot

  rot   test_t1_docs_excluded  <- kette.py
  rot   test_t2_kette_paket_max_exists  <- kette.py
  rot   test_t3_ketten_dateien_im_paket  <- kette.py
  rot   test_t4_fremde_dateien_liste  <- kette.py
  rot   test_t5_nicht_genannt_markierung  <- kette.py
  rot   test_t6_vorrang_klassifikation  <- kette.py
  rot   test_t7_harte_obergrenze_exit1  <- kette.py
  rot   test_t8_gegenprobe_role_split  <- kette.py
  rot   test_t9_paket_ohne_code_exit1  <- kette.py

9 von 9 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
