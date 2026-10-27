# Pruefung umsetzung_auto

- Zeit: 2026-10-27 15:46
- Ruecksetzpunkt: 3700da7
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261027_umsetzung_auto.md  (21 Tests)
Handover: handover_20261027_umsetzung_auto.md

  ok        T1    Vorab-Prüfung – Kurztitel ungültig
  ok        T2    Vorab-Prüfung – kein Spec-Commit
  ok        T3    Vorab-Prüfung – Spec ohne `## Schreibbereich
  ok        T4    Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)
  ok        T5    Vorab-Prüfung – `opencode` fehlt
  ok        T6    Vorab-Prüfung – Modell kein `llamacpp/
  ok        T7    Erfolgreicher Lauf, `reason: stop`, alle Prüfungen grün
  ok        T8    Lauf ohne `reason: stop
  ok        T9    Timeout
  ok        T10   Selbst-Commit
  ok        T11   Datei außerhalb Schreibbereich
  ok        T12   Handover fehlt
  ok        T13   Nacharbeit – Auftrag aus Datei
  ok        T14   Nacharbeit – zwei ohne Fortschritt
  ok        T15   Lebendsignal – Werkzeugzeile
  ok        T16   pruefen` rot
  ok        T17   Vorab-Prüfung – Nacharbeit mit fremden Änderungen
  ok        T18   Schreibbereich – Ordner-Eintrag
  ok        T19   Schreibbereich – Verbotene Dateien
  ok        T20   main() – gleicher Exit wie Funktionsaufruf
  ok        T21   Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)

  Testskript tests/test_umsetzung_auto.py: alle 21 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_umsetzung_auto.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t20_attrappe_sperrt_echtes_repo (tests.test_umsetzung_auto.EinstiegTests.test_t20_attrappe_sperrt_echtes_repo)
T20 Absicherung (kein main()-Aufruf): Attrappe sperrt das echte Repo und Ziele außerhalb von Temp ... ok
test_t20_main_gleicher_exit_wie_funktionsaufruf (tests.test_umsetzung_auto.EinstiegTests.test_t20_main_gleicher_exit_wie_funktionsaufruf)
T20: main() – gleicher Exit wie Funktionsaufruf ... ok
test_t10_selbst_commit (tests.test_umsetzung_auto.LaufTests.test_t10_selbst_commit)
T10: Selbst-Commit ... ok
test_t11_datei_ausserhalb_schreibbereich (tests.test_umsetzung_auto.LaufTests.test_t11_datei_ausserhalb_schreibbereich)
T11: Datei außerhalb Schreibbereich ... ok
test_t12_handover_fehlt (tests.test_umsetzung_auto.LaufTests.test_t12_handover_fehlt)
T12: Handover fehlt ... ok
test_t15_fehlgeschlagener_befehl_mit_wortlaut (tests.test_umsetzung_auto.LaufTests.test_t15_fehlgeschlagener_befehl_mit_wortlaut)
T15: Lebendsignal – Werkzeugzeile (fehlgeschlagener, nicht abgelehnter Befehl mit Wortlaut) ... ok
test_t15_herzschlag (tests.test_umsetzung_auto.LaufTests.test_t15_herzschlag)
T15: Lebendsignal – Werkzeugzeile (Herzschlag während einer langen Pause) ... ok
test_t15_lebendsignal_werkzeugzeile (tests.test_umsetzung_auto.LaufTests.test_t15_lebendsignal_werkzeugzeile)
T15: Lebendsignal – Werkzeugzeile ... ok
test_t16_pruefen_rot (tests.test_umsetzung_auto.LaufTests.test_t16_pruefen_rot)
T16: pruefen rot ... ok
test_t18_schreibbereich_ordner_eintrag (tests.test_umsetzung_auto.LaufTests.test_t18_schreibbereich_ordner_eintrag)
T18: Schreibbereich – Ordner-Eintrag ... ok
test_t19_schreibbereich_verbotene_dateien (tests.test_umsetzung_auto.LaufTests.test_t19_schreibbereich_verbotene_dateien)
T19: Schreibbereich – Verbotene Dateien ... ok
test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen (tests.test_umsetzung_auto.LaufTests.test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen)
T7: Erfolgreicher Lauf, reason: stop, alle Prüfungen grün ... ok
test_t7_exitcode_von_opencode_wird_ignoriert (tests.test_umsetzung_auto.LaufTests.test_t7_exitcode_von_opencode_wird_ignoriert)
T7: Erfolgreicher Lauf, reason: stop (opencode-Exit ≠ 0 zählt nicht, nur das JSON) ... ok
test_t8_kein_gueltiges_json (tests.test_umsetzung_auto.LaufTests.test_t8_kein_gueltiges_json)
T8: Lauf ohne reason: stop (Strom ohne gültiges JSON) ... ok
test_t8_lauf_ohne_reason_stop (tests.test_umsetzung_auto.LaufTests.test_t8_lauf_ohne_reason_stop)
T8: Lauf ohne reason: stop ... ok
test_t9_timeout (tests.test_umsetzung_auto.LaufTests.test_t9_timeout)
T9: Timeout ... ok
test_t9_timeout_beendet_unterprozesse (tests.test_umsetzung_auto.LaufTests.test_t9_timeout_beendet_unterprozesse)
T9: Timeout (auch Kindprozesse von opencode werden beendet) ... ok
test_t13_nacharbeit_auftrag_aus_datei (tests.test_umsetzung_auto.NacharbeitTests.test_t13_nacharbeit_auftrag_aus_datei)
T13: Nacharbeit – Auftrag aus Datei ... ok
test_t13_nummer_aus_handover (tests.test_umsetzung_auto.NacharbeitTests.test_t13_nummer_aus_handover)
T13: Nacharbeit – Auftrag aus Datei (Nummer n = bestehende Abschnitte im Handover + 1) ... ok
test_t13_ohne_neuen_abschnitt_nicht_in_ordnung (tests.test_umsetzung_auto.NacharbeitTests.test_t13_ohne_neuen_abschnitt_nicht_in_ordnung)
T13: Nacharbeit – Auftrag aus Datei (Handover ohne neuen Abschnitt → Exit 1) ... ok
test_t14_gegenfall_fortschritt_hebt_halt_auf (tests.test_umsetzung_auto.NacharbeitTests.test_t14_gegenfall_fortschritt_hebt_halt_auf)
T14: Nacharbeit – zwei ohne Fortschritt (Gegenfall: einer mit Fortschritt) ... ok
test_t14_nacharbeit_zwei_ohne_fortschritt (tests.test_umsetzung_auto.NacharbeitTests.test_t14_nacharbeit_zwei_ohne_fortschritt)
T14: Nacharbeit – zwei ohne Fortschritt ... ok
test_t14_unterzeilen_zaehlen_nicht (tests.test_umsetzung_auto.NacharbeitTests.test_t14_unterzeilen_zaehlen_nicht)
T14: Nacharbeit – zwei ohne Fortschritt (Unterzeilen mit fremdem Text zählen nicht als Lauf) ... ok
test_t17_handover_anderes_datum_ist_fremd (tests.test_umsetzung_auto.NacharbeitTests.test_t17_handover_anderes_datum_ist_fremd)
T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen (Handover mit anderem Datum) ... ok
test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen (tests.test_umsetzung_auto.NacharbeitTests.test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen)
T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen ... ok
test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei (tests.test_umsetzung_auto.NacharbeitTests.test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei)
T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2) ... ok
test_t1_vorab_pruefung_kurztitel_ungueltig (tests.test_umsetzung_auto.VorabTests.test_t1_vorab_pruefung_kurztitel_ungueltig)
T1: Vorab-Prüfung – Kurztitel ungültig ... ok
test_t2_vorab_pruefung_kein_spec_commit (tests.test_umsetzung_auto.VorabTests.test_t2_vorab_pruefung_kein_spec_commit)
T2: Vorab-Prüfung – kein Spec-Commit ... ok
test_t3_vorab_pruefung_leerer_schreibbereich (tests.test_umsetzung_auto.VorabTests.test_t3_vorab_pruefung_leerer_schreibbereich)
T3: Vorab-Prüfung – Spec ohne ## Schreibbereich (Abweichung 2: leerer Abschnitt gilt wie fehlend) ... ok
test_t3_vorab_pruefung_spec_ohne_schreibbereich (tests.test_umsetzung_auto.VorabTests.test_t3_vorab_pruefung_spec_ohne_schreibbereich)
T3: Vorab-Prüfung – Spec ohne ## Schreibbereich ... ok
test_t4_vorab_pruefung_unrunder_arbeitsstand (tests.test_umsetzung_auto.VorabTests.test_t4_vorab_pruefung_unrunder_arbeitsstand)
T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf) ... ok
test_t5_vorab_pruefung_opencode_fehlt (tests.test_umsetzung_auto.VorabTests.test_t5_vorab_pruefung_opencode_fehlt)
T5: Vorab-Prüfung – opencode fehlt ... ok
test_t6_vorab_pruefung_modell_kein_llamacpp (tests.test_umsetzung_auto.VorabTests.test_t6_vorab_pruefung_modell_kein_llamacpp)
T6: Vorab-Prüfung – Modell kein llamacpp/ ... ok

----------------------------------------------------------------------
Ran 33 tests in 9.218s

OK
```

## gegenprobe gegen 3700da7  (Exit 0)

```
Gegenprobe gegen 3700da7: 33 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 32 Test(s) rot
  role-split/kette/testdata/opencode_fake.py: 23 Test(s) rot

  rot   test_t10_selbst_commit  <- kette.py, opencode_fake.py
  rot   test_t11_datei_ausserhalb_schreibbereich  <- kette.py, opencode_fake.py
  rot   test_t12_handover_fehlt  <- kette.py, opencode_fake.py
  rot   test_t13_nacharbeit_auftrag_aus_datei  <- kette.py, opencode_fake.py
  rot   test_t13_nummer_aus_handover  <- kette.py, opencode_fake.py
  rot   test_t13_ohne_neuen_abschnitt_nicht_in_ordnung  <- kette.py, opencode_fake.py
  rot   test_t14_gegenfall_fortschritt_hebt_halt_auf  <- kette.py
  rot   test_t14_nacharbeit_zwei_ohne_fortschritt  <- kette.py, opencode_fake.py
  rot   test_t14_unterzeilen_zaehlen_nicht  <- kette.py
  rot   test_t15_fehlgeschlagener_befehl_mit_wortlaut  <- kette.py, opencode_fake.py
  rot   test_t15_herzschlag  <- kette.py, opencode_fake.py
  rot   test_t15_lebendsignal_werkzeugzeile  <- kette.py, opencode_fake.py
  rot   test_t16_pruefen_rot  <- kette.py, opencode_fake.py
  rot   test_t17_handover_anderes_datum_ist_fremd  <- kette.py
  rot   test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen  <- kette.py
  rot   test_t18_schreibbereich_ordner_eintrag  <- kette.py, opencode_fake.py
  rot   test_t19_schreibbereich_verbotene_dateien  <- kette.py, opencode_fake.py
  rot   test_t1_vorab_pruefung_kurztitel_ungueltig  <- kette.py
  rot   test_t20_attrappe_sperrt_echtes_repo  <- opencode_fake.py
  rot   test_t20_main_gleicher_exit_wie_funktionsaufruf  <- kette.py, opencode_fake.py
  rot   test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei  <- kette.py, opencode_fake.py
  rot   test_t2_vorab_pruefung_kein_spec_commit  <- kette.py
  rot   test_t3_vorab_pruefung_leerer_schreibbereich  <- kette.py
  rot   test_t3_vorab_pruefung_spec_ohne_schreibbereich  <- kette.py
  rot   test_t4_vorab_pruefung_unrunder_arbeitsstand  <- kette.py
  rot   test_t5_vorab_pruefung_opencode_fehlt  <- kette.py
  rot   test_t6_vorab_pruefung_modell_kein_llamacpp  <- kette.py, opencode_fake.py
  rot   test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen  <- kette.py, opencode_fake.py
  rot   test_t7_exitcode_von_opencode_wird_ignoriert  <- kette.py, opencode_fake.py
  rot   test_t8_kein_gueltiges_json  <- kette.py, opencode_fake.py
  rot   test_t8_lauf_ohne_reason_stop  <- kette.py, opencode_fake.py
  rot   test_t9_timeout  <- kette.py, opencode_fake.py
  rot   test_t9_timeout_beendet_unterprozesse  <- kette.py, opencode_fake.py

33 von 33 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
