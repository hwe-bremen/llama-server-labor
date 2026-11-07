# Pruefung mail_filter

- Zeit: 2026-11-07 13:24
- Ruecksetzpunkt: d69e46b
- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

## abgleich  (Exit 0)

```
Spec:     spec_20261107_mail_filter.md  (8 Tests)
Handover: handover_20261107_mail_filter.md

  ok        T1    Newsletter-Erkennung
  ok        T2    Ausnahme für Projekt-Absender
  ok        T3    Newsletter übersprungen
  ok        T4    Ausnahme und Reihenfolge
  ok        T5    Absender lesbar
  ok        T6    Termine ohne Beschreibung
  ok        T7    Prompt
  ok        T8    Ende zu Ende über `main

  Testskript tests/test_mail_filter.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_mail_filter.py

Keine Abweichung.
```

## unittest  (Exit 0)

```
test_t3_newsletter_uebersprungen (tests.test_mail_filter.Abruf.test_t3_newsletter_uebersprungen)
T3: Newsletter nicht geladen, nicht gezählt, eine Zeile mit dekodiertem Absender; Zusammenfassung unverändert ... ok
test_t4_ausnahme_projekt_absender (tests.test_mail_filter.Abruf.test_t4_ausnahme_projekt_absender)
T4: Newsletter von Projekt-Absender wird geholt; Stichwort allein schützt nicht; bekannte vor Newsletter ... ok
test_t5_absender_dekodiert (tests.test_mail_filter.Abruf.test_t5_absender_dekodiert)
T5: Absender im Mail-Dict lesbar (RFC 2047), einfache Adresse unverändert, Projekt-Zuordnung greift ... ok
test_t8_main_mit_newsletter (tests.test_mail_filter.EndeZuEnde.test_t8_main_mit_newsletter)
T8: main – Newsletter nie in Planung/DB, auch im zweiten Lauf nicht geladen; Absender lesbar; kein nacktes Datum ... ok
test_t1_ist_newsletter (tests.test_mail_filter.Erkennung.test_t1_ist_newsletter)
T1: Newsletter an List-Unsubscribe oder Precedence bulk/list/junk – nicht an List-Id allein ... ok
test_t2_projekt_absender (tests.test_mail_filter.Erkennung.test_t2_projekt_absender)
T2: Ausnahme nur für Absender/Domain aus mail_projects.json; Stichwort zählt nicht; Fehler -> False ... ok
test_t6_termin_ohne_beschreibung_verworfen (tests.test_mail_filter.Termine.test_t6_termin_ohne_beschreibung_verworfen)
T6: nacktes Datum ist kein Termin; mit Beschreibung bleibt; nur nackte -> kein Abschnitt Termine ... ok
test_t7_prompt_termine (tests.test_mail_filter.Termine.test_t7_prompt_termine)
T7: Prompt verlangt 'YYYY-MM-DD: Beschreibung' und schließt das Versanddatum aus ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.069s

OK
```

## gegenprobe gegen d69e46b  (Exit 0)

```
Gegenprobe gegen d69e46b: 8 Tests, je Datei einzeln zurueckgesetzt

  agents/mail_planung/mail_planung.py: 8 Test(s) rot

  rot   test_t1_ist_newsletter  <- mail_planung.py
  rot   test_t2_projekt_absender  <- mail_planung.py
  rot   test_t3_newsletter_uebersprungen  <- mail_planung.py
  rot   test_t4_ausnahme_projekt_absender  <- mail_planung.py
  rot   test_t5_absender_dekodiert  <- mail_planung.py
  rot   test_t6_termin_ohne_beschreibung_verworfen  <- mail_planung.py
  rot   test_t7_prompt_termine  <- mail_planung.py
  rot   test_t8_main_mit_newsletter  <- mail_planung.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
