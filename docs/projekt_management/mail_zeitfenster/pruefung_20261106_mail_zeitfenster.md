# Pruefung mail_zeitfenster

- Zeit: 2026-11-07 11:18
- Ruecksetzpunkt: 248942c
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: ok

## abgleich  (Exit 1)

```
Spec:     spec_20261106_mail_zeitfenster.md  (8 Tests)
Handover: handover_20261106_mail_zeitfenster.md

  FEHLT     T1    Einstellungen und IMAP-Datum
  FEHLT     T2    Suche mit SINCE und Bestand-Aufruf
  FEHLT     T3    Höchstzahl, älteste zuerst, Zusammenfassung
  FEHLT     T4    Bekannte und Mails ohne Message-ID
  FEHLT     T5    main` – Reihenfolge und Werte
  FEHLT     T6    run_dry` – Verdrahtung und Fehler
  FEHLT     T7    Nichts geht verloren
  FEHLT     T8    Als Skript

  Testskript tests/test_mail_zeitfenster.py: alle 8 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_mail_zeitfenster.py

8 Abweichung(en).
```

## unittest  (Exit 0)

```
test_t2_suche_since_und_bestand (tests.test_mail_zeitfenster.Abruf.test_t2_suche_since_und_bestand)
T2: fetch_mails sucht mit SINCE; ohne since wie bisher ALL und alles (Bestand-Aufruf) ... ok
test_t3_hoechstzahl_aelteste_zuerst (tests.test_mail_zeitfenster.Abruf.test_t3_hoechstzahl_aelteste_zuerst)
T3: höchstens max_anzahl neue Mails vollständig, älteste zuerst, Zusammenfassung mit Rest ... ok
test_t4_bekannte_und_ohne_message_id (tests.test_mail_zeitfenster.Abruf.test_t4_bekannte_und_ohne_message_id)
T4: bekannte Mails nur per Kopfzeile erkannt und übersprungen; ohne Message-ID immer geholt, zählt nicht ... ok
test_t1_zeitfenster_und_imap_datum (tests.test_mail_zeitfenster.Einstellungen.test_t1_zeitfenster_und_imap_datum)
T1: Standardwerte 0/20, gültige und ungültige Werte, IMAP-Datum unabhängig von der Locale ... ok
test_t8_als_skript (tests.test_mail_zeitfenster.Einstieg.test_t8_als_skript)
T8: als Skript (--dry-run und normal) – ungültige Einstellung: Exit 1, Meldung, kein Traceback, nichts angelegt ... ok
test_t7_nichts_geht_verloren (tests.test_mail_zeitfenster.EndeZuEnde.test_t7_nichts_geht_verloren)
T7: 5 Mails, Höchstzahl 2 – nach drei Läufen jede genau einmal in der Planung, vierter Lauf holt nichts ... ok
test_t5_main_reihenfolge_und_werte (tests.test_mail_zeitfenster.Verdrahtung.test_t5_main_reihenfolge_und_werte)
T5: main – ungültige Einstellung vor Schlüsselbund/IMAP mit Exit 1; sonst Zeitfenster, Höchstzahl, bekannte IDs ... /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/unittest/mock.py:2247: ResourceWarning: unclosed database in <sqlite3.Connection object at 0x10b578f40>
  def __init__(self, name, parent):
ResourceWarning: Enable tracemalloc to get the object allocation traceback
ok
test_t6_trockenlauf_verdrahtung (tests.test_mail_zeitfenster.Verdrahtung.test_t6_trockenlauf_verdrahtung)
T6: run_dry – gleiche Werte wie main, DB unverändert, Schlüsselbund-Fehler ohne Traceback mit Exit 1 ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.368s

OK
```

## gegenprobe gegen 248942c  (Exit 0)

```
Gegenprobe gegen 248942c: 8 Tests, je Datei einzeln zurueckgesetzt

  agents/mail_planung/mail_planung.py: 8 Test(s) rot

  rot   test_t1_zeitfenster_und_imap_datum  <- mail_planung.py
  rot   test_t2_suche_since_und_bestand  <- mail_planung.py
  rot   test_t3_hoechstzahl_aelteste_zuerst  <- mail_planung.py
  rot   test_t4_bekannte_und_ohne_message_id  <- mail_planung.py
  rot   test_t5_main_reihenfolge_und_werte  <- mail_planung.py
  rot   test_t6_trockenlauf_verdrahtung  <- mail_planung.py
  rot   test_t7_nichts_geht_verloren  <- mail_planung.py
  rot   test_t8_als_skript  <- mail_planung.py

8 von 8 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
