# Pruefung mail_planung

- Zeit: 2026-10-23 15:36
- Ruecksetzpunkt: 5d49488
- Kurz: abgleich: Abweichung | unittest: ok | gegenprobe: ok

## abgleich  (Exit 1)

```
Spec:     spec_20261022_mail_planung.md  (14 Tests)
Handover: handover_20261023_nachbesserung2_mail_planung.md

  FEHLT     T2    Nur-HTML-Mail
  FEHLT     T3    Umlaute + doppelte Zustellung (gleiche Message-ID)
  FEHLT     T4    Mail ohne `Message-ID`-Header
  FEHLT     T5    Leerer Text / nur Anhang
  FEHLT     T6    Weiterleitungskette + mögliche Duplikate (neue Message-ID, gleicher Inhalt)
  FEHLT     T7    Fehlerpfad — LLM liefert ungültiges JSON
  FEHLT     T8    Fehlerpfad — `os.replace` schlägt fehl (Absturz zwischen Write und Marker)
  FEHLT     T9    Leeres Postfach
  FEHLT     T10   Postfach bleibt unverändert (read-only)
  FEHLT     T11   Trockenlauf
  FEHLT     T12   Skript lädt als Skript (kein ImportError)
  FEHLT     T13   Modul-Import ohne Nebenwirkung
  FEHLT     T14   Schlüsselbund-Fehler
  FEHLT     T15   Projekt-Zuordnung über Konfigurationsdatei
  EXTRA     T21   Sehr langer Mailtext -> Kuerzung auf MAIL_MAX_CHARS** – bestanden  (nicht in der Spec)
  EXTRA     T22   HTTP 400 -> dauerhaft wie Validierungsfehler** – bestanden  (nicht in der Spec)
  EXTRA     T23   HTTP 503 -> voruebergehend** – bestanden  (nicht in der Spec)
  EXTRA     T24   content None -> dauerhaft** – bestanden  (nicht in der Spec)

  Testskript tests/test_mail_planung.py: alle 14 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_mail_planung.py

14 Abweichung(en).
```

## unittest  (Exit 0)

```
Trockenlauf: Preview geschrieben nach /var/folders/h7/gz_l9hwn5ldfmhk9yswb0rrh0000gn/T/mail_plan_test_ptkfl8xf/outbox/preview_dry-run_test.md
Verarbeitet: Mail-ID Check [Unzugeordnet]
Verarbeitet: Validation Error [Unzugeordnet]
Verarbeitet: Langer Text [Unzugeordnet]
Verarbeitet: HTTP 400 [Unzugeordnet]
Verarbeitet: Content None [Unzugeordnet]
Verarbeitet: HTML Test [Unzugeordnet]
Verarbeitet: Aenderung: Ueberfuehrung des Bueros [Unzugeordnet]
  (bereits verarbeitet) Aenderung: Ueberfuehrung des Bueros
Verarbeitet: Keine ID [Unzugeordnet]
Verarbeitet: Leere Mail [Unzugeordnet]
Verarbeitet: Nur Anhang [Unzugeordnet]
Verarbeitet: Original [Unzugeordnet]
Verarbeitet: Original (Weiterleitung) [Unzugeordnet]
Verarbeitet: Bad JSON [Unzugeordnet]
Keine neuen Mails
test_t10_readonly_select (tests.test_mail_planung.T10_Readonly.test_t10_readonly_select)
Prueft: A2 ... ok
test_t11_dry_run (tests.test_mail_planung.T11_Trockenlauf.test_t11_dry_run)
Prueft: A7 — Trockenlauf via run_dry(), fetch_mails & get_imap_password gemockt ... ok
test_t12_sript_ladet_als_skript (tests.test_mail_planung.T12_SkriptLoad.test_t12_sript_ladet_als_skript)
Prueft: Einstiegspunkt (Skript-Start) ... ok
test_t13_import_ohne_nebenwirkung (tests.test_mail_planung.T13_ModulImport.test_t13_import_ohne_nebenwirkung)
Prueft: Einstiegspunkt (Modul-Import) ... ok
test_t14_schlusselbund_fehler (tests.test_mail_planung.T14_SchlusselbundFehler.test_t14_schlusselbund_fehler)
Prueft: A8 ... Schluesselbund-Eintrag 'lab-mail-imap' nicht gefunden
ok
test_t15_projekt_treffer (tests.test_mail_planung.T15_ProjektZuordnung.test_t15_projekt_treffer)
Prueft: A10 ... ok
test_t15_projekt_unzugeordnet (tests.test_mail_planung.T15_ProjektZuordnung.test_t15_projekt_unzugeordnet)
Prueft: A10 (kein Treffer) ... ok
test_t16_mail_id_check_in_process_mail (tests.test_mail_planung.T16_MailIdKommentar.test_t16_mail_id_check_in_process_mail)
Prüft: Nachbesserung 1 — process_mail sucht mail-id-Kommentar, nicht ##-Zeile ... ok
test_t16_mail_id_comment_in_block (tests.test_mail_planung.T16_MailIdKommentar.test_t16_mail_id_comment_in_block)
Prüft: Nachbesserung 1 — Block enthält <!-- mail-id: ... --> ... ok
test_t17_strptime_gueltiges_datum (tests.test_mail_planung.T17_DatumValidierung.test_t17_strptime_gueltiges_datum)
Prüft: Nachbesserung 1 — gültiges Datum akzeptiert ... ok
test_t17_strptime_monat_13 (tests.test_mail_planung.T17_DatumValidierung.test_t17_strptime_monat_13)
Prüft: Nachbesserung 1 — Monat 13 ist ungültig ... ok
test_t17_strptime_tag_32 (tests.test_mail_planung.T17_DatumValidierung.test_t17_strptime_tag_32)
Prüft: Nachbesserung 1 — Tag 32 ist ungültig ... ok
test_t18_code_fence_json (tests.test_mail_planung.T18_JsonCleaning.test_t18_code_fence_json)
Prüft: Nachbesserung 1 — ```json ... ``` entfernen ... ok
test_t18_code_fence_plain (tests.test_mail_planung.T18_JsonCleaning.test_t18_code_fence_plain)
Prüft: Nachbesserung 1 — ``` ... ``` entfernen ... ok
test_t18_text_around_json (tests.test_mail_planung.T18_JsonCleaning.test_t18_text_around_json)
Prüft: Nachbesserung 1 — Text vor/nach JSON entfernen ... ok
test_t19_chat_template_kwargs (tests.test_mail_planung.T19_EnableThinking.test_t19_chat_template_kwargs)
Prüft: Nachbesserung 1 — chat_template_kwargs im Request ... ok
test_t20_network_error_no_entry (tests.test_mail_planung.T20_FehlerartenTrennen.test_t20_network_error_no_entry)
Prüft: Nachbesserung 1 — Netzwerkfehler → Exit 1, kein Eintrag, kein Marker ... Fehler bei LLM-Verbindung (<t20-net@test>): Connection refused
ok
test_t20_validation_error_with_entry (tests.test_mail_planung.T20_FehlerartenTrennen.test_t20_validation_error_with_entry)
Prüft: Nachbesserung 1 — Validierungsfehler → Block mit Warnung, Marker gesetzt ... ok
test_t21_langer_mailtext_kuerzung (tests.test_mail_planung.T21_LangerMailtext.test_t21_langer_mailtext_kuerzung)
Prueft: Nachbesserung 2 — LLM bekommt hochstens MAIL_MAX_CHARS, ... ok
test_t22_http_400_dauerhaft (tests.test_mail_planung.T22_HTTP400.test_t22_http_400_dauerhaft)
Prueft: Nachbesserung 2 — HTTP 400 -> Block 'Auswertung fehlgeschlagen', ... ok
test_t23_http_503_voruebergehend (tests.test_mail_planung.T23_HTTP503.test_t23_http_503_voruebergehend)
Prueft: Nachbesserung 2 — HTTP 503 -> kein Eintrag, kein Marker, Exit 1. ... Fehler bei LLM-Verbindung (<t23-503@test>): 503 Server Error
ok
test_t24_content_none (tests.test_mail_planung.T24_ContentNone.test_t24_content_none)
Prueft: Nachbesserung 2 — content None -> Block 'Auswertung fehlgeschlagen', ... ok
test_t2_html_mail (tests.test_mail_planung.T2_HTMLMail.test_t2_html_mail)
Prueft: A9 (HTML), A1 (Block-Format), A2 (read-only) ... ok
test_t3_umlaut_dedup (tests.test_mail_planung.T3_UmlauteDedup.test_t3_umlaut_dedup)
Prueft: A9 (Umlaute), A3 (Dedup), A1 ... ok
test_t4_synthetic_message_id (tests.test_mail_planung.T4_KeinMessageID.test_t4_synthetic_message_id)
Prueft: A3 (synthetische ID), A6 ... ok
test_t5_leerer_body_kein_llm_call (tests.test_mail_planung.T5_LeeererText.test_t5_leerer_body_kein_llm_call)
Prueft: A9 (leerer Text, Anhang), A1, A5 (LLM-Call wird uebersprungen) ... ok
test_t5_nur_anhang (tests.test_mail_planung.T5_LeeererText.test_t5_nur_anhang)
Mail mit nur Anhang (kein Textbody) ... ok
test_t6_duplikat_kennzeichnung (tests.test_mail_planung.T6_WeiterleitungDuplikat.test_t6_duplikat_kennzeichnung)
Prueft: A9 (Weiterleitung), A4 (Duplikat-Kennzeichnung) ... ok
test_t7_ungueltiges_json_validierungsfehler (tests.test_mail_planung.T7_UngueltigesJSON.test_t7_ungueltiges_json_validierungsfehler)
Prueft: Nachbesserung 1 — ungueltiges JSON ist Validierungsfehler: ... ok
test_t8_os_replace_fehler (tests.test_mail_planung.T8_OsReplaceFehler.test_t8_os_replace_fehler)
Prueft: A6 (Reihenfolge), A1 (atomares Schreiben) ... Fehler beim Schreiben der Planungsdatei: No space left on device
ok
test_t9_leeres_postfach (tests.test_mail_planung.T9_LeeeresPostfach.test_t9_leeres_postfach)
Prueft: A2 (leeres Postfach), A6 ... ok

----------------------------------------------------------------------
Ran 31 tests in 0.325s

OK
```

## gegenprobe gegen 5d49488  (Exit 0)

```
Gegenprobe gegen 5d49488: 31 Tests, je Datei einzeln zurueckgesetzt

  agents/mail_planung/__init__.py: 0 Test(s) rot
  agents/mail_planung/mail_planung.py: 31 Test(s) rot
  agents/mail_planung/test_imap_server.py: 0 Test(s) rot

  rot   test_t10_readonly_select  <- mail_planung.py
  rot   test_t11_dry_run  <- mail_planung.py
  rot   test_t12_sript_ladet_als_skript  <- mail_planung.py
  rot   test_t13_import_ohne_nebenwirkung  <- mail_planung.py
  rot   test_t14_schlusselbund_fehler  <- mail_planung.py
  rot   test_t15_projekt_treffer  <- mail_planung.py
  rot   test_t15_projekt_unzugeordnet  <- mail_planung.py
  rot   test_t16_mail_id_check_in_process_mail  <- mail_planung.py
  rot   test_t16_mail_id_comment_in_block  <- mail_planung.py
  rot   test_t17_strptime_gueltiges_datum  <- mail_planung.py
  rot   test_t17_strptime_monat_13  <- mail_planung.py
  rot   test_t17_strptime_tag_32  <- mail_planung.py
  rot   test_t18_code_fence_json  <- mail_planung.py
  rot   test_t18_code_fence_plain  <- mail_planung.py
  rot   test_t18_text_around_json  <- mail_planung.py
  rot   test_t19_chat_template_kwargs  <- mail_planung.py
  rot   test_t20_network_error_no_entry  <- mail_planung.py
  rot   test_t20_validation_error_with_entry  <- mail_planung.py
  rot   test_t21_langer_mailtext_kuerzung  <- mail_planung.py
  rot   test_t22_http_400_dauerhaft  <- mail_planung.py
  rot   test_t23_http_503_voruebergehend  <- mail_planung.py
  rot   test_t24_content_none  <- mail_planung.py
  rot   test_t2_html_mail  <- mail_planung.py
  rot   test_t3_umlaut_dedup  <- mail_planung.py
  rot   test_t4_synthetic_message_id  <- mail_planung.py
  rot   test_t5_leerer_body_kein_llm_call  <- mail_planung.py
  rot   test_t5_nur_anhang  <- mail_planung.py
  rot   test_t6_duplikat_kennzeichnung  <- mail_planung.py
  rot   test_t7_ungueltiges_json_validierungsfehler  <- mail_planung.py
  rot   test_t8_os_replace_fehler  <- mail_planung.py
  rot   test_t9_leeres_postfach  <- mail_planung.py

31 von 31 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```
