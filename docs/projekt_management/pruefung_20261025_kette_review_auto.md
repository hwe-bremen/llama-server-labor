# Pruefung kette_review_auto

- Zeit: 2026-10-25 18:48
- Ruecksetzpunkt: a74e250
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: FEHLER

## abgleich  (Exit 1)

```
Spec:     spec_20261025_kette_review_auto.md  (14 Tests)
Handover: handover_20261025_kette_review_auto.md

  ANDERS    T1    Spec: Endergebnis bei zwei gültigen Läufen
                  Handover: Endergebnis zwei gültige Läufe** – bestanden   (Uebereinstimmung 50% -- ausgetauscht?)
  ok        T2    Router nicht erreichbar
  ok        T3    Ungültiger Kurztitel
  ANDERS    T4    Spec: Nur rote Unit-Tests brechen ab
                  Handover: Rote Unit-Tests Abbruch** – bestanden   (Uebereinstimmung 50% -- ausgetauscht?)
  ok        T5    Paket-Voraussetzung fehlt
  ok        T6    Leere Modellantwort
  ok        T7    Automatisches Umbenennen
  ok        T8    Fehlende Befund-Tabelle
  ANDERS    T9    Spec: Abbruch bei Lauf 2 (Lauf 1 bleibt erhalten)
                  Handover: Abbruch bei Lauf 2** – bestanden   (Uebereinstimmung 50% -- ausgetauscht?)
  ok        T10   Zusammenfassung und Gesamt-Datei
  ANDERS    T11   Spec: Nur 127.0.0.1
                  Handover: Nur Loopback** – bestanden   (Uebereinstimmung 25% -- ausgetauscht?)
  ANDERS    T12   Spec: Abgeschnittene Antwort und HTTP-Fehler
                  Handover: Abgeschnittene Antwort** – bestanden   (Uebereinstimmung 50% -- ausgetauscht?)
  ok        T13   Herzschlag während des Laufs
  NICHT GET T14   Echter Lauf am K7-Stand (Hawe, manuell)  (unter 'Nicht getestet' -- Grund pruefen)

  Testskript tests/test_kette_review_auto.py: keine Methode test_<id> fuer T14
  Selbst ausfuehren: python3 -m unittest -v tests/test_kette_review_auto.py

7 Abweichung(en).
```

## unittest  (Exit 0)

```
test_k1_lauf1_fehlschlaegt_ein_request (tests.test_kette_review_auto.ReviewAutoTests.test_k1_lauf1_fehlschlaegt_ein_request) ... ok
test_k2_timeout_zeitueberschreitung (tests.test_kette_review_auto.ReviewAutoTests.test_k2_timeout_zeitueberschreitung) ... ok
test_t10_zusammenfassung_gesamt_datei (tests.test_kette_review_auto.ReviewAutoTests.test_t10_zusammenfassung_gesamt_datei) ... ok
test_t11_nur_loopback (tests.test_kette_review_auto.ReviewAutoTests.test_t11_nur_loopback) ... ok
test_t12_abgeschnittene_antwort (tests.test_kette_review_auto.ReviewAutoTests.test_t12_abgeschnittene_antwort) ... ok
test_t13_herzschlag_waehrend_lauf (tests.test_kette_review_auto.ReviewAutoTests.test_t13_herzschlag_waehrend_lauf) ... ok
test_t1_endergebnis_zwei_gueltige_laeufe (tests.test_kette_review_auto.ReviewAutoTests.test_t1_endergebnis_zwei_gueltige_laeufe) ... ok
test_t2_router_nicht_erreichbar (tests.test_kette_review_auto.ReviewAutoTests.test_t2_router_nicht_erreichbar) ... ok
test_t3_ungueltiger_kurztitel (tests.test_kette_review_auto.ReviewAutoTests.test_t3_ungueltiger_kurztitel) ... ok
test_t4_rote_unit_tests_abbruch (tests.test_kette_review_auto.ReviewAutoTests.test_t4_rote_unit_tests_abbruch) ... ok
test_t5_paket_voraussetzung_fehlt (tests.test_kette_review_auto.ReviewAutoTests.test_t5_paket_voraussetzung_fehlt) ... ok
test_t6_leere_modellantwort (tests.test_kette_review_auto.ReviewAutoTests.test_t6_leere_modellantwort) ... ok
test_t7_automatisches_umbenennen (tests.test_kette_review_auto.ReviewAutoTests.test_t7_automatisches_umbenennen) ... ok
test_t8_fehlende_befund_tabelle (tests.test_kette_review_auto.ReviewAutoTests.test_t8_fehlende_befund_tabelle) ... ok
test_t9_abbruch_bei_lauf_2 (tests.test_kette_review_auto.ReviewAutoTests.test_t9_abbruch_bei_lauf_2) ... ok

----------------------------------------------------------------------
Ran 15 tests in 1.177s

OK
```

## gegenprobe gegen a74e250  (Exit 2)

```
Keine geaenderten Code-Dateien seit a74e250.
```
