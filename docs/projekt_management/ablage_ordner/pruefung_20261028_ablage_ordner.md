# Pruefung ablage_ordner

- Zeit: 2026-10-28 15:16
- Ruecksetzpunkt: 593feb0
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261028_ablage_ordner.md  (7 Tests)
Handover: handover_20261028_ablage_ordner.md

  ok        T1    ablage – Ordner der Kette, wenn vorhanden, sonst flach
  ok        T2    datei_suchen – sucht in der Ablage der Kette
  ok        T3    anforderung, Verdikt-Pfad und Gesamtbefund landen in der Ablage
  ok        T4    umsetzung-auto – Prompt, Handover und Protokoll in der Ablage, Vorlagen bleiben
  ok        T5    _ist_kettendatei – Kettendateien im Ordner der Kette zählen
  ok        T6    role_proxy – Spec-Auftrag nennt Pfade in der Ablage
  ok        T7    pruefen, quellen, paket und prompt – Ausgaben und Pfade in der Ablage

  Testskript tests/test_ablage_ordner.py: alle 7 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_ablage_ordner.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t1_ablage_ordner_oder_flach (tests.test_ablage_ordner.Ablage.test_t1_ablage_ordner_oder_flach)
T1: ablage – Ordner der Kette, wenn vorhanden, sonst flach ... ok
test_t2_datei_suchen_in_der_ablage (tests.test_ablage_ordner.Ablage.test_t2_datei_suchen_in_der_ablage)
T2: datei_suchen – sucht in der Ablage der Kette ... ok
test_t3_schreibende_befehle_in_der_ablage (tests.test_ablage_ordner.Ablage.test_t3_schreibende_befehle_in_der_ablage)
T3: anforderung, Verdikt-Pfad und Gesamtbefund landen in der Ablage ... ok
test_t5_kettendatei_im_ordner (tests.test_ablage_ordner.Kettendatei.test_t5_kettendatei_im_ordner)
T5: _ist_kettendatei – Kettendateien im Ordner der Kette zählen ... ok
test_t6_role_proxy_spec_auftrag_im_ordner (tests.test_ablage_ordner.RollenProxy.test_t6_role_proxy_spec_auftrag_im_ordner)
T6: role_proxy – Spec-Auftrag nennt Pfade in der Ablage ... ok
test_t4_umsetzung_auto_mit_ordner (tests.test_ablage_ordner.UmsetzungImOrdner.test_t4_umsetzung_auto_mit_ordner)
T4: umsetzung-auto – Prompt, Handover und Protokoll in der Ablage, Vorlagen bleiben ... ok
test_t7_pruefen_quellen_paket_prompt_in_der_ablage (tests.test_ablage_ordner.WeitereBefehle.test_t7_pruefen_quellen_paket_prompt_in_der_ablage)
T7: pruefen, quellen, paket und prompt – Ausgaben und Pfade in der Ablage ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.354s

OK
```

## gegenprobe gegen 593feb0  (Exit 0)

```
Gegenprobe gegen 593feb0: 7 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 7 Test(s) rot
  role-split/role_proxy.py: 1 Test(s) rot

  rot   test_t1_ablage_ordner_oder_flach  <- kette.py
  rot   test_t2_datei_suchen_in_der_ablage  <- kette.py
  rot   test_t3_schreibende_befehle_in_der_ablage  <- kette.py
  rot   test_t4_umsetzung_auto_mit_ordner  <- kette.py
  rot   test_t5_kettendatei_im_ordner  <- kette.py
  rot   test_t6_role_proxy_spec_auftrag_im_ordner  <- kette.py, role_proxy.py
  rot   test_t7_pruefen_quellen_paket_prompt_in_der_ablage  <- kette.py

7 von 7 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
