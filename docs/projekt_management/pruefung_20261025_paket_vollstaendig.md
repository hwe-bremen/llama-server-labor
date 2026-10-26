# Pruefung paket_vollstaendig

- Zeit: 2026-10-26 12:38
- Ruecksetzpunkt: 84e3bb7
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: Abweichung

## abgleich  (Exit 1)

```
Spec:     spec_20261025_paket_vollstaendig.md  (10 Tests)
Handover: handover_20261026_paket_vollstaendig.md

  ANDERS    T1    Spec: Fehlerpfade von paket (Git-Fehler, kein Spec-Commit, keine Spec, ungültiger Kurztitel)
                  Handover: Paket enthält .md-Dateien in role-split/ (keine blanket .md-Ausschließung)** – bestanden   (Uebereinstimmung 20% -- ausgetauscht?)
  ANDERS    T2    Spec: Paket enthält Dateien unter tests/ und role-split/, auch unversionierte
                  Handover: docs/ und experiments/ sind aus dem Paket ausgeschlossen** – bestanden   (Uebereinstimmung 11% -- ausgetauscht?)
  ANDERS    T3    Spec: Handover-Datei ohne Markierung, fremde Datei mit Markierung
                  Handover: Paket wird nach Gesamtgröße gekürzt (≤ 80000 Zeichen)** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  ok        T4    Vorrang-Kürzung – Vorrang 3 wird weggelassen
  ANDERS    T5    Spec: KETTE_PAKET_MAX überschritten → Exit 1
                  Handover: Shared Helper _is_chain_file() existiert und wird von paket verwendet** – bestanden   (Uebereinstimmung 17% -- ausgetauscht?)
  ok        T6    Gegenprobe berücksichtigt role-split/kette/
  ANDERS    T7    Spec: Bestehende Tests in test_kette.py bleiben grün
                  Handover: Nur docs/ geändert => Exit 0, keine Paket-Datei mit Code** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  ANDERS    T8    Spec: Fremde Commits nur als Liste
                  Handover: Omitted-Liste markiert Dateien mit 'nicht in der Übergabe genannt'** – bestanden   (Uebereinstimmung 25% -- ausgetauscht?)
  ANDERS    T9    Spec: Paket ohne Code trotz Änderungen → Exit 1
                  Handover: gegenprobe nimmt role-split/kette/ Dateien auf (nicht ausgeschlossen)** – bestanden   (Uebereinstimmung 0% -- ausgetauscht?)
  FEHLT     T10   Abnahme – echter Lauf am K7-Stand (Hawe, manuell)

  Testskript tests/test_paket_vollstaendig.py: keine Methode test_<id> fuer T10
  Selbst ausfuehren: python3 -m unittest -v tests/test_paket_vollstaendig.py

9 Abweichung(en).
```

## unittest  (Exit 0)

```
test_t1_md_dateien_in_role_split_im_paket (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t1_md_dateien_in_role_split_im_paket)
T1: Paket enthaelt .md-Dateien in role-split/ (keine blanket .md-Ausschliessung). ... ok
test_t2_docs_experiments_ausschluss (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t2_docs_experiments_ausschluss)
T2: docs/ und experiments/ sind aus dem Paket ausgeschlossen. ... ok
test_t3_kuerzung_nach_gesamtgroesse (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t3_kuerzung_nach_gesamtgroesse)
T3: Paket wird nach Gesamtgroesse gekuerzt (<= 80000 Zeichen). ... ok
test_t4_vorrang_reihenfolge_kuerzung (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t4_vorrang_reihenfolge_kuerzung)
T4: Bei Kuerzung wird Vorrang 3 zuerst entfernt, dann 2, V1 bleibt. ... ok
test_t5_shared_helper_kette_vs_fremd (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t5_shared_helper_kette_vs_fremd)
T5: Shared Helper _is_chain_file() existiert und wird von paket verwendet. ... ok
test_t6_datei_mit_historie_und_aenderung (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t6_datei_mit_historie_und_aenderung)
T6: role-split-Datei mit Commit-Historie + Aenderung gehoert zur Kette. ... ok
test_t7_nur_docs_geaendert_exit0 (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t7_nur_docs_geaendert_exit0)
T7: Nur docs/ geaendert => Exit 0, keine Paket-Datei mit Code. ... ok
test_t8_omitted_liste_nicht_genannt (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t8_omitted_liste_nicht_genannt)
T8: Omitted-Liste markiert Dateien mit 'nicht in der Uebergabe genannt'. ... ok
test_t9_gegenprobe_role_split_einschliesst (tests.test_paket_vollstaendig.TestPaketVollstaendig.test_t9_gegenprobe_role_split_einschliesst)
T9: gegenprobe nimmt role-split/kette/ Dateien auf (nicht ausgeschlossen). ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.772s

OK
```

## gegenprobe gegen 84e3bb7  (Exit 1)

```
Gegenprobe gegen 84e3bb7: 9 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 8 Test(s) rot
  role-split/kette/test_kette.py: 0 Test(s) rot

  rot   test_t1_md_dateien_in_role_split_im_paket  <- kette.py
  rot   test_t2_docs_experiments_ausschluss  <- kette.py
  rot   test_t3_kuerzung_nach_gesamtgroesse  <- kette.py
  rot   test_t4_vorrang_reihenfolge_kuerzung  <- kette.py
  rot   test_t5_shared_helper_kette_vs_fremd  <- kette.py
  rot   test_t6_datei_mit_historie_und_aenderung  <- kette.py
  GRUEN test_t7_nur_docs_geaendert_exit0  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t8_omitted_liste_nicht_genannt  <- kette.py
  rot   test_t9_gegenprobe_role_split_einschliesst  <- kette.py

8 von 9 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, dann wird die Gegenprobe je Test aussagekraeftig.
```
