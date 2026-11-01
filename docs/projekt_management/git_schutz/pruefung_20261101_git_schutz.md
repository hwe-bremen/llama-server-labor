# Pruefung git_schutz

- Zeit: 2026-11-01 20:16
- Ruecksetzpunkt: 7f95f7d
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261101_git_schutz.md  (8 Tests)
Handover: handover_20261101_git_schutz.md

  ok        T1    Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert“
  ok        T2    git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt
  ok        T3    hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht
  ok        T4    info/ und Unterordner – auch im Nacharbeit-Lauf
  ok        T5    Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund
  ok        T6    config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen
  ok        T7    Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start
  ok        T8    Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend

  Testskript tests/test_git_schutz.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_git_schutz.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t1_unveraendertes_git_verzeichnis_lauf_ok (tests.test_git_schutz.GitSchutzTests.test_t1_unveraendertes_git_verzeichnis_lauf_ok)
T1: Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert“ ... ok
test_t2_git_config_user_name_test_fall_vom_27_10 (tests.test_git_schutz.GitSchutzTests.test_t2_git_config_user_name_test_fall_vom_27_10)
T2: git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt ... ok
test_t3_hooks_neu_ausfuehrbar_symlink_geloescht (tests.test_git_schutz.GitSchutzTests.test_t3_hooks_neu_ausfuehrbar_symlink_geloescht)
T3: hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht ... ok
test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit (tests.test_git_schutz.GitSchutzTests.test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit)
T4: info/ und Unterordner – auch im Nacharbeit-Lauf ... ok
test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund (tests.test_git_schutz.GitSchutzTests.test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund)
T5: Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund ... ok
test_t6_config_unlesbar_kein_absturz (tests.test_git_schutz.GitSchutzTests.test_t6_config_unlesbar_kein_absturz)
T6: config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen ... ok
test_t7_git_verzeichnis_worktree_und_fehlt (tests.test_git_schutz.GitSchutzTests.test_t7_git_verzeichnis_worktree_und_fehlt)
T7: Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start ... ok
test_t8_standardwerte_im_echten_pfad (tests.test_git_schutz.GitSchutzTests.test_t8_standardwerte_im_echten_pfad)
T8: Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend ... ok

----------------------------------------------------------------------
Ran 8 tests in 1.499s

OK
```

## gegenprobe gegen 7f95f7d  (Exit 0)

```
Gegenprobe gegen 7f95f7d: 8 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 8 Test(s) rot

  rot   test_t1_unveraendertes_git_verzeichnis_lauf_ok  <- kette.py
  rot   test_t2_git_config_user_name_test_fall_vom_27_10  <- kette.py
  rot   test_t3_hooks_neu_ausfuehrbar_symlink_geloescht  <- kette.py
  rot   test_t4_info_exclude_und_unterordner_auch_in_der_nacharbeit  <- kette.py
  rot   test_t5_aenderungen_ausserhalb_der_geschuetzten_teile_kein_befund  <- kette.py
  rot   test_t6_config_unlesbar_kein_absturz  <- kette.py
  rot   test_t7_git_verzeichnis_worktree_und_fehlt  <- kette.py
  rot   test_t8_standardwerte_im_echten_pfad  <- kette.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
