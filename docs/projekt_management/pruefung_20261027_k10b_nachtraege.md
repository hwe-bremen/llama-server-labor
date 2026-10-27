# Pruefung k10b_nachtraege

- Zeit: 2026-10-27 20:59
- Ruecksetzpunkt: 29060aa
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261027_k10b_nachtraege.md  (4 Tests)
Handover: handover_20261027_k10b_nachtraege.md

  ok        T1    Prompt nennt je Test-ID eine Pflichtzeile
  ok        T2    abgleich – Bereich unter „Nicht getestet“ ist keine Einzelnennung
  ok        T3    Tokens – Spitze je Schritt im Protokoll und auf stdout
  ok        T4    zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht

  Testskript tests/test_k10b_nachtraege.py: alle 4 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_k10b_nachtraege.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t2_bereich_zaehlt_nicht (tests.test_k10b_nachtraege.AbgleichTests.test_t2_bereich_zaehlt_nicht)
T2: abgleich – Bereich „T1–T2“ unter Nicht getestet ist keine Einzelnennung ... ok
test_t1_pflichtzeilen_im_prompt (tests.test_k10b_nachtraege.PromptTests.test_t1_pflichtzeilen_im_prompt)
T1: Prompt nennt je Test-ID eine Pflichtzeile ... ok
test_t3_tokens_spitze (tests.test_k10b_nachtraege.TokenTests.test_t3_tokens_spitze)
T3: Tokens – Spitze je Schritt im Protokoll und auf stdout ... ok
test_t4_zurueckgezogen_nicht_hoch (tests.test_k10b_nachtraege.ZusammenfuehrenTests.test_t4_zurueckgezogen_nicht_hoch)
T4: zusammenfuehren – zurückgezogene „hoch“-Zeilen zählen nicht ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.174s

OK
```

## gegenprobe gegen 29060aa  (Exit 0)

```
Gegenprobe gegen 29060aa: 4 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 4 Test(s) rot

  rot   test_t1_pflichtzeilen_im_prompt  <- kette.py
  rot   test_t2_bereich_zaehlt_nicht  <- kette.py
  rot   test_t3_tokens_spitze  <- kette.py
  rot   test_t4_zurueckgezogen_nicht_hoch  <- kette.py

4 von 4 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
