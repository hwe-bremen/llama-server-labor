# Pruefung mail_server_test

- Zeit: 2026-10-24 13:24
- Ruecksetzpunkt: 37b1da1
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: Abweichung

## abgleich  (Exit 1)

```
Spec:     spec_20261023_mail_server_test.md  (17 Tests)
Handover: handover_20261023_mail_server_test.md

  ok        T1    Port-Check
  ok        T2    Docker-Start
  ok        T3    SMTP-Einlieferung
  ok        T4    Schlüsselbund-Service per Umgebungsvariable
  ok        T5    Unverschlüsseltes IMAP nur für localhost
  ok        T6    Trockenlauf — keine Planungsdatei
  ok        T7    Echter Lauf — Planungsdatei vorhanden
  ok        T8    Dedup — gleiche Message-ID
  NICHT GET T9    Duplikat — neue Message-ID, gleicher Body  (unter 'Nicht getestet' -- Grund pruefen)
  FEHLT     T10   Zweiter Lauf — byte-identische Planungsdatei
  FEHLT     T11   Trockenlauf — Previews vorhanden
  FEHLT     T12   Giftmail — Fehler-Block
  FEHLT     T13   Injections-Mail — Eintrag vorhanden
  FEHLT     T14   Leere Mail — „Kein verwertbarer Inhalt"
  FEHLT     T15   Umlaut-Mail — UTF-8 korrekt
  NICHT GET T16   Sehr lange Mail — Kürzungshinweis  (unter 'Nicht getestet' -- Grund pruefen)
  NICHT GET T17   End-to-End — Gesamtlauf  (unter 'Nicht getestet' -- Grund pruefen)

  Testskript tests/test_mail_server_test.py: keine Methode test_<id> fuer T9, T10, T11, T12, T13, T14, T15, T16, T17
  Selbst ausfuehren: python3 -m unittest -v tests/test_mail_server_test.py

10 Abweichung(en).
```

## unittest  (Exit 0)

```
Keine neuen Mails
Verarbeitet: Test [Unzugeordnet]
Verarbeitet: Test [Unzugeordnet]
  (bereits verarbeitet) Test
test_k15_atomares_schreiben (tests.test_mail_server_test.TestKAtomicWrite.test_k15_atomares_schreiben)
K15: Atomares Schreiben erzeugt keine Halbschreib-Datei. ... ok
test_k3_body_hash_deterministisch (tests.test_mail_server_test.TestKBodyHash.test_k3_body_hash_deterministisch)
K3: Body-Hash ist deterministisch und normalisiert. ... ok
test_k6_block_basis (tests.test_mail_server_test.TestKBuildBlock.test_k6_block_basis)
K6: Basis-Block ohne Evaluation. ... ok
test_k7_block_mit_duplikat (tests.test_mail_server_test.TestKBuildBlock.test_k7_block_mit_duplikat)
K7: Block mit Duplikat-Hinweis. ... ok
test_k8_block_mit_fehler (tests.test_mail_server_test.TestKBuildBlock.test_k8_block_mit_fehler)
K8: Block mit Fehlermeldung. ... ok
test_k4_text_plain (tests.test_mail_server_test.TestKExtractText.test_k4_text_plain)
K4: Plain-Text-Body wird korrekt extrahiert. ... ok
test_k5_html_zu_text (tests.test_mail_server_test.TestKExtractText.test_k5_html_zu_text)
K5: HTML wird in Text konvertiert. ... ok
test_k1_message_id_aus_header (tests.test_mail_server_test.TestKMessageId.test_k1_message_id_aus_header)
K1: Message-ID wird aus Header gelesen. ... ok
test_k2_synthetische_message_id (tests.test_mail_server_test.TestKMessageId.test_k2_synthetische_message_id)
K2: Fehlt Message-ID, wird synthetische ID erzeugt. ... ok
test_k10_unvollstaendige_evaluation (tests.test_mail_server_test.TestKValidateEvaluation.test_k10_unvollstaendige_evaluation)
K10: Fehlendes Feld liefert Fehlerstring. ... ok
test_k11_ungueltiges_datum (tests.test_mail_server_test.TestKValidateEvaluation.test_k11_ungueltiges_datum)
K11: Ungültiges Datum liefert Fehlerstring. ... ok
test_k9_gueltige_evaluation (tests.test_mail_server_test.TestKValidateEvaluation.test_k9_gueltige_evaluation)
K9: Gültige Evaluation liefert leeren Fehlerstring. ... ok
test_t1_ports_freiverfügbar (tests.test_mail_server_test.TestT1PortCheck.test_t1_ports_freiverfügbar)
T1: Ports 3025 und 3143 sind frei vor Start. ... ok
test_t2_docker_port_mapping (tests.test_mail_server_test.TestT2DockerStart.test_t2_docker_port_mapping)
T2: Docker-Start mit Ports 127.0.0.1:3143:3143 und 127.0.0.1:3025:3025. ... ok
test_t3_einliefern_script_exists (tests.test_mail_server_test.TestT3SmtpDelivery.test_t3_einliefern_script_exists)
T3: Einlieferungs-Skript existiert und ist aufgerufen. ... ok
test_t4_custom_keychain_service (tests.test_mail_server_test.TestT4KeychainService.test_t4_custom_keychain_service)
T4: Eigener Wert über Umgebungsvariable. ... ok
test_t4_default_keychain_service (tests.test_mail_server_test.TestT4KeychainService.test_t4_default_keychain_service)
T4: Standardwert lab-mail-imap. ... ok
test_t5_fremdhost_verboten (tests.test_mail_server_test.TestT5ImapUnencrypted.test_t5_fremdhost_verboten)
T5: Unverschlüsseltes IMAP auf fremdem Host führt zu sys.exit(1). ... Unverschlüsseltes IMAP wird nur für localhost unterstützt
ok
test_t5_localhost_erlaubt (tests.test_mail_server_test.TestT5ImapUnencrypted.test_t5_localhost_erlaubt)
T5: Unverschlüsseltes IMAP auf localhost nutzt IMAP4. ... ok
test_t5_normaler_betrieb_ssl (tests.test_mail_server_test.TestT5ImapUnencrypted.test_t5_normaler_betrieb_ssl)
T5: Ohne MAIL_IMAP_UNENCRYPTED wird IMAP4_SSL verwendet. ... ok
test_t6_dry_run_keine_datei (tests.test_mail_server_test.TestT6DryRun.test_t6_dry_run_keine_datei)
T6: Trockenlauf erzeugt keine Planungsdatei. ... ok
test_t7_real_run_datei_erzeugt (tests.test_mail_server_test.TestT7RealRun.test_t7_real_run_datei_erzeugt)
T7: Echter Lauf erzeugt Planungsdatei. ... ok
test_t8_zweiter_lauf_identisch (tests.test_mail_server_test.TestT8SecondRun.test_t8_zweiter_lauf_identisch)
T8: Zweiter Lauf erzeugt byte-identische Planungsdatei. ... ok

----------------------------------------------------------------------
Ran 23 tests in 0.201s

OK
```

## gegenprobe gegen 37b1da1  (Exit 1)

```
Gegenprobe gegen 37b1da1: 23 Tests, je Datei einzeln zurueckgesetzt

  agents/mail_planung/mail_planung.py: 3 Test(s) rot

  GRUEN test_k10_unvollstaendige_evaluation  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k11_ungueltiges_datum  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k15_atomares_schreiben  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k1_message_id_aus_header  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k2_synthetische_message_id  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k3_body_hash_deterministisch  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k4_text_plain  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k5_html_zu_text  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k6_block_basis  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k7_block_mit_duplikat  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k8_block_mit_fehler  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_k9_gueltige_evaluation  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t1_ports_freiverfügbar  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t2_docker_port_mapping  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t3_einliefern_script_exists  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t4_custom_keychain_service  <- mail_planung.py
  GRUEN test_t4_default_keychain_service  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  rot   test_t5_fremdhost_verboten  <- mail_planung.py
  rot   test_t5_localhost_erlaubt  <- mail_planung.py
  GRUEN test_t5_normaler_betrieb_ssl  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t6_dry_run_keine_datei  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t7_real_run_datei_erzeugt  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)
  GRUEN test_t8_zweiter_lauf_identisch  (wird mit keiner alten Datei rot -- prueft Bestehendes oder nichts)

3 von 23 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
GRUEN/LADEN-Tests einzeln ansehen: Pruefen sie bewusst Bestehendes (in Ordnung) oder gar nichts (Befund)? Tipp: Neue Funktionen im Test erst in der Methode importieren, dann wird die Gegenprobe je Test aussagekraeftig.
```
