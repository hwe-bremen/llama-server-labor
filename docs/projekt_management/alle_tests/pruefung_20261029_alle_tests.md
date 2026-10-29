# Pruefung alle_tests

- Zeit: 2026-10-29 08:37
- Ruecksetzpunkt: 1faadfe
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261029_alle_tests.md  (8 Tests)
Handover: handover_20261029_alle_tests.md

  ok        T1    finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert
  ok        T2    art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad
  ok        T3    interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable
  ok        T4    Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0
  ok        T5    Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende
  ok        T6    Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter
  ok        T7    --liste führt nichts aus; keine Testdateien → Exit 2
  ok        T8    Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile

  Testskript tests/test_alle_tests.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_alle_tests.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t2_art_aufruf_und_suchpfad (tests.test_alle_tests.Aufruf.test_t2_art_aufruf_und_suchpfad)
T2: art und aufruf – unittest vs. Skript, Sonderargumente, cwd-unabhängiger Suchpfad ... ok
test_t3_interpreter_naechstes_venv (tests.test_alle_tests.Aufruf.test_t3_interpreter_naechstes_venv)
T3: interpreter – nächstes .venv vom Ordner aufwärts, sonst sys.executable ... ok
test_t8_echtes_repo_standardwerte (tests.test_alle_tests.Einstieg.test_t8_echtes_repo_standardwerte)
T8: Standardwerte im echten Pfad – ROOT ist der Repo-Root, --liste über die Befehlszeile ... ok
test_t1_finden_fundorte_und_ausschluesse (tests.test_alle_tests.Finden.test_t1_finden_fundorte_und_ausschluesse)
T1: finden – nur test_*.py in den Fundorten, ohne .venv/__pycache__/testdata, sortiert ... ok
test_t4_gruen_mit_nachbarmodul_und_bindestrich (tests.test_alle_tests.Laufen.test_t4_gruen_mit_nachbarmodul_und_bindestrich)
T4: Lauf grün – Nachbarmodul im Ordner mit Bindestrich, Skript mit Sonderargument, Exit 0 ... ok
test_t5_rot_nach_exit_code_mit_ausgabe (tests.test_alle_tests.Laufen.test_t5_rot_nach_exit_code_mit_ausgabe)
T5: Lauf rot – Exit-Code zählt (nicht die letzte Zeile), Ausgabe der roten Dateien am Ende ... ok
test_t6_zeitlimit (tests.test_alle_tests.Laufen.test_t6_zeitlimit)
T6: Zeitlimit – hängende Datei wird nach --timeout abgebrochen, der Rest läuft weiter ... ok
test_t7_liste_und_leer (tests.test_alle_tests.Laufen.test_t7_liste_und_leer)
T7: --liste führt nichts aus; keine Testdateien → Exit 2 ... ok

----------------------------------------------------------------------
Ran 8 tests in 2.416s

OK
```

## gegenprobe gegen 1faadfe  (Exit 0)

```
Gegenprobe gegen 1faadfe: 8 Tests, je Datei einzeln zurueckgesetzt

  scripts/alle_tests.py: 8 Test(s) rot

  rot   test_t1_finden_fundorte_und_ausschluesse  <- alle_tests.py
  rot   test_t2_art_aufruf_und_suchpfad  <- alle_tests.py
  rot   test_t3_interpreter_naechstes_venv  <- alle_tests.py
  rot   test_t4_gruen_mit_nachbarmodul_und_bindestrich  <- alle_tests.py
  rot   test_t5_rot_nach_exit_code_mit_ausgabe  <- alle_tests.py
  rot   test_t6_zeitlimit  <- alle_tests.py
  rot   test_t7_liste_und_leer  <- alle_tests.py
  rot   test_t8_echtes_repo_standardwerte  <- alle_tests.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
