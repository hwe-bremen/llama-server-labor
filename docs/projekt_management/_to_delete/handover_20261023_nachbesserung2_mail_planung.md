# Handover: Nachbesserung 2 mail_planung

- **Spec:** `docs/projekt_management/spec_20261022_mail_planung.md` (Nachbesserung 2, Punkte 1–5)
- **Datum:** 2026-10-23
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** Kein Commit angelegt (Auftrag: „Nein kein Commit bitte direkt weitermachen!")

## Umgesetzt

| Anforderung | Status | Wo im Code |
|---|---|---|
| 1. MAIL_MAX_CHARS-Konstante + Kuerzung | erfueellt | `mail_planung.py` Zeile 66, `evaluate_mail()` |
| 1. Kuerzungshinweis im Block | erfueellt | `build_block()` Parameter `truncation_hint` |
| 2. HTTP 4xx (außer 429) = dauerhaft | erfueellt | `evaluate_mail()` try/except um `raise_for_status()` |
| 2. 429/5xx/Verbindungsfehler/Timeout = voruebergehend | erfueellt | `evaluate_mail()` weiterwerfen, `process_mail()` except HTTPError |
| 3. choices/message/content fehlt oder None = dauerhaft | erfueellt | `evaluate_mail()` Pruefung nach `response.json()` |
| 4. T21–T24 Tests | erfueellt | `tests/test_mail_planung.py` |
| 5. Alle Tests laufen | erfueellt | 31/31 OK |

## Geaenderte und neue Dateien

- `agents/mail_planung/mail_planung.py` – geaendert – Konstante `MAIL_MAX_CHARS`, `evaluate_mail()` gibt jetzt Tuple `(data, was_truncated)` zurueck, HTTP-Fehler-Trennung, content-Pruefung, `build_block()` mit `truncation_hint`, `process_mail()` passt Tuple und truncation_hint an.
- `tests/test_mail_planung.py` – geaendert – Tests T21–T24 angehaengt.

## Abweichungen von der Spec

- Keine.

## Annahmen

- Der Kuerzungshinweis `"> (Mailtext für die Auswertung gekürzt)"` steht im Block nach der eventuellen `error_reason`-Zeile (beides kann gleichzeitig vorkommen, z. B. wenn gekuerzter Text trotzdem zu einem Validierungsfehler fuehrt).
- `MAIL_MAX_CHARS` wird als Modul-Konstante bei Import eingelesen (nicht pro-Aufruf), analog zu `LLM_TIMEOUT`.

## Getestet (mit echter Ausgabe)

**T21: Sehr langer Mailtext -> Kuerzung auf MAIL_MAX_CHARS** – bestanden

**T22: HTTP 400 -> dauerhaft wie Validierungsfehler** – bestanden

**T23: HTTP 503 -> voruebergehend** – bestanden

**T24: content None -> dauerhaft** – bestanden

```
$ python3 -m unittest -v tests/test_mail_planung.py
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
Prüft: Nachbesserung 1 — Netzwerkfehler → Exit 1, kein Eintrag, kein Marker ... ok
test_t20_validation_error_with_entry (tests.test_mail_planung.T20_FehlerartenTrennen.test_t20_validation_error_with_entry)
Prüft: Nachbesserung 1 — Validierungsfehler → Block mit Warnung, Marker gesetzt ... ok
test_t21_langer_mailtext_kuerzung (tests.test_mail_planung.T21_LangerMailtext.test_t21_langer_mailtext_kuerzung)
Prueft: Nachbesserung 2 — LLM bekommt hochstens MAIL_MAX_CHARS, ... ok
test_t22_http_400_dauerhaft (tests.test_mail_planung.T22_HTTP400.test_t22_http_400_dauerhaft)
Prueft: Nachbesserung 2 — HTTP 400 -> Block 'Auswertung fehlgeschlagen', ... ok
test_t23_http_503_voruebergehend (tests.test_mail_planung.T23_HTTP503.test_t23_http_503_voruebergehend)
Prueft: Nachbesserung 2 — HTTP 503 -> kein Eintrag, kein Marker, Exit 1. ... ok
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
Prueft: A6 (Reihenfolge), A1 (atomares Schreiben) ... ok
test_t9_leeres_postfach (tests.test_mail_planung.T9_LeeeresPostfach.test_t9_leeres_postfach)
Prueft: A2 (leeres Postfach), A6 ... ok

----------------------------------------------------------------------
Ran 31 tests in 0.374s

OK
```

## Gegenprobe (fuehrt Hawe aus, Ausgabe hier einfuegen)

```
$ python3 role-split/kette/kette.py gegenprobe nachbesserung2_mail_planung --commit a5ddc6e
<Ausgabe>
```

## Aussenwirkung

- Keine Befehle mit Aussenwirkung ausgefuehrt.

## Hawe muss ausfuehren

- Nichts.

## Nicht getestet

- Nichts.

## Offene Punkte / bekannte Schwaechen

- Die Kuerzung des Mailtextes auf `MAIL_MAX_CHARS` Zeichen kann mitten in einem Wort oder Satz brechen. Fuer eine sauberere Kuerzung waere ein Word-Boundary-Cut sinnvoll, war aber nicht in der Spec gefordert.
- HTTP 429 wird aktuell als voruebergehend behandelt (kein Eintrag, Exit 1). Es gibt keine Retry-Logik; der Benutzer muss den Lauf manuell wiederholen.
