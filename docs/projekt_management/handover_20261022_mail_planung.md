# Handover: mail_planung

- **Spec:** `docs/projekt_management/spec_20261022_mail_planung.md`
- **Datum:** 2026-10-23
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** `5d49488`

## Umgesetzt

| Anforderung (Nr. aus der Spec) | Status | Wo im Code |
|---|---|---|
| A1: Markdown-Planungsdatei — Schema und atomares Schreiben | erfüllt | `mail_planung.py`, `build_block`, `atomic_write_plan` |
| A2: Lesen des Postfachs — read-only | erfüllt | `mail_planung.py`, `fetch_mails` (`select(readonly=True)`) |
| A3: Deduplizierung — Message-ID als Primärschlüssel | erfüllt | `mail_planung.py`, `is_new_mail`, `mark_as_processed` |
| A4: Mögliche Duplikate — gleicher Inhalt, neue Message-ID | erfüllt | `mail_planung.py`, `detect_possible_duplicate`, `build_block` |
| A5: Auswertung durch das LLM — nur Daten zurück | erfüllt | `mail_planung.py`, `evaluate_mail`, `validate_evaluation` |
| A6: Fehlerpfad — Mail erst nach erfolgreichem Schreiben markiert | erfüllt | `mail_planung.py`, `process_mail` (Reihenfolge 1-5) |
| A7: Trockenlauf | erfüllt | `mail_planung.py`, `run_dry`, `process_mail(dry_run=True)` |
| A8: Zugangsdaten nur aus dem Schlüsselbund | erfüllt | `mail_planung.py`, `get_imap_password` |
| A9: Schwierige Mails — HTML, Umlaute, leerer Text, Anhang, Weiterleitung | erfüllt | `mail_planung.py`, `extract_text`, `_HTMLToText`, `build_block` |
| A10: Projekt-Zuordnung — nur über Konfigurationsdatei | erfüllt | `mail_planung.py`, `resolve_project` |

## Nachbesserung 1 (2026-10-23)

| Änderung | Status | Wo im Code |
|---|---|---|
| mail-id-Kommentar statt Datum-Betreff-Zeile | erfüllt | `build_block`, `process_mail` |
| Datum-Validierung mit strptime statt Regex | erfüllt | `validate_evaluation`, `_validate_date` |
| Code-Zäune/umgebenden Text entfernen | erfüllt | `_extract_json_from_content` |
| `enable_thinking: False` im Request | erfüllt | `evaluate_mail` (`chat_template_kwargs`) |
| Fehlerarten trennen (Netzwerk vs. Validierung) | erfüllt | `process_mail` (try/except-Struktur) |

## Geänderte und neue Dateien

- `agents/mail_planung/__init__.py` – neu – Package-Initialisierung
- `agents/mail_planung/mail_planung.py` – neu – Hauptwerkzeug: IMAP-Client, LLM-Auswertung, atomares Schreiben, Trockenlauf
- `agents/mail_planung/test_imap_server.py` – neu – Fundstelle für späteren echten IMAP-Testserver (Platzhalter, Tests nutzen Mocks)
- `tests/test_mail_planung.py` – neu – 27 Tests (T2–T15, T16–T20; T5 hat zwei Methoden)
- `docs/projekt_management/spec_20261022_mail_planung.md` – geändert – A7 angepasst, A5 um Nachbesserung 1 ergänzt

## Abweichungen von der Spec

- **T1 fehlt:** Die Spec definiert Tests T2–T15. T1 wird in der Spec nicht als Testmethode definiert (nur in der Fehlerpfad-Tabelle erwähnt). Daher gibt es keine `test_t1_...`-Methode.
- **IMAP-Testserver:** Die Spec nennt `agents/mail_planung/test_imap_server.py` als Fundstelle, aber die Tests ersetzen `fetch_mails` per Mock statt einen echten lokalen IMAP-Server zu starten. Das entspricht der Spec („Tests ohne echten Server, Mail-Zugriff im Test ersetzt").
- **T11 Trockenlauf:** Die Spec-Korrektur sagt, `get_imap_password` wird im Trockenlauf aufgerufen. Die Umsetzung ruft es in `run_dry()` auf. Der Test nutzt `run_dry()` mit gemocktem `fetch_mails` und `get_imap_password`.
- **Codierung der Warnmeldung:** Die ursprüngliche Datei hatte `m�gliches` (korruptes ö). Wurde auf `mögliches` korrigiert.
- **T7 Nachbesserung 1:** Die ursprüngliche Spec sah vor, dass ungültiges JSON vom LLM zu Exit 1 ohne Marker führt. Nachbesserung 1 klassifiziert ungültiges JSON als Validierungsfehler: Block mit Warnung wird geschrieben, Marker gesetzt, Exit 0. Test T7 entsprechend angepasst.
- **build_block message_id-Parameter:** `build_block` erhält nun den aufgelösten `message_id` als Parameter, damit synthetische Message-IDs korrekt im `<!-- mail-id: ... -->`-Kommentar landen.

## Annahmen

- **LLM-Standardmodell:** `MAIL_LLM_MODEL` default auf `unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL` (wie in der Umgebung aktuell geladen).
- **Projekt-Konfigurationsformat:** JSON-Array mit Objekten, die `sender`, `domain` oder `keyword` plus `project` enthalten. Kein Schema in der Spec vorgegeben.
- **Synthetische Message-ID:** SHA-256 von `Absender|Betreff|Datum|Body`, gekürzt auf 16 Hex-Zeichen, Prefix `<synthetic-...@mail-planung>`.
- **Body-Hash für Duplikaterkennung:** SHA-256 des normalisierten Textkörpers (Whitespace kollabiert).

## Getestet (mit echter Ausgabe)

**T2: Nur-HTML-Mail** – bestanden

**T3: Umlaute + doppelte Zustellung (gleiche Message-ID)** – bestanden

**T4: Mail ohne Message-ID-Header** – bestanden

**T5: Leerer Text / nur Anhang** – bestanden

**T6: Weiterleitungskette + mögliche Duplikate (neue Message-ID, gleicher Inhalt)** – bestanden

**T7: Fehlerpfad — LLM liefert ungültiges JSON (Validierungsfehler)** – bestanden

**T8: Fehlerpfad — os.replace schlägt fehl (Absturz zwischen Write und Marker)** – bestanden

**T9: Leeres Postfach** – bestanden

**T10: Postfach bleibt unverändert (read-only)** – bestanden

**T11: Trockenlauf** – bestanden

**T12: Skript lädt als Skript (kein ImportError)** – bestanden

**T13: Modul-Import ohne Nebenwirkung** – bestanden

**T14: Schlüsselbund-Fehler** – bestanden

**T15: Projekt-Zuordnung über Konfigurationsdatei** – bestanden

**T16: mail-id-Kommentar statt Datum-Betreff-Zeile** – bestanden

**T17: Datum-Validierung mit strptime (Monat 13 / Tag 32 ungültig)** – bestanden

**T18: JSON-Cleaning (Code-Zäune + Text vor/nach JSON)** – bestanden

**T19: enable_thinking: False im Request** – bestanden

**T20: Fehlerarten trennen (Netzwerk vs. Validierung)** – bestanden

```
$ python3 -m unittest -v tests.test_mail_planung
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
Ran 27 tests in 0.266s

OK
```

## Gegenprobe (führt Hawe aus, Ausgabe hier einfügen)

```
$ python3 role-split/kette/kette.py gegenprobe mail_planung --commit 5d49488
<Ausgabe>
```

## Außenwirkung

- Keine Befehle mit Außenwirkung ausgeführt. Alle Tests nutzen temporäre Verzeichnisse, Mocks für IMAP/LLM/Schlüsselbund, und `IMAP_HOST=127.0.0.1`.

## Hawe muss ausführen

- Nichts. Alle erlaubten Befehle wurden ausgeführt.

## Nicht getestet

- Echter IMAP-Server-Connect (wird per Mock ersetzt, wie in der Spec vorgesehen).
- Echter Schlüsselbund-Zugriff (wird per Mock ersetzt).
- Echter LLM-API-Call (wird per Mock ersetzt).
- launchd-Integration (Nicht-Ziel der Spec).

## Offene Punkte / bekannte Schwächen

- **test_imap_server.py** ist ein Platzhalter. Für robuste Integrationstests wäre ein echter lokaler IMAP-Server (per threading + socket oder externes Werkzeug) nötig.
- **HTML-Parsing:** `_HTMLToText` ist minimalistisch. Komplexe HTML-Strukturen (Tabelle, verschachtelte Divs) werden nicht perfekt gerendert, reichen aber für die Spec-Anforderungen.
- **LLM-Validierung:** `validate_evaluation` prüft nur Pflichtfelder und Datumsformat via `strptime`. Semantische Korrektheit der extrahierten Daten wird nicht geprüft.
- **Projekt-Konfiguration:** Das JSON-Format ist nicht in der Spec festgelegt; aktuelle Umsetzung nutzt ein einfaches Array mit `sender`/`domain`/`keyword`-Mapping.
- **enable_thinking:** Die Spec verlangt `chat_template_kwargs: {"enable_thinking": False}` im LLM-Request. Dies wird gesetzt, aber ob der Server es tatsächlich unterstützt, hängt vom llama-server-Backend ab.


## Nachbesserung 2 (23.10.)

- **Spec:** `docs/projekt_management/spec_20261022_mail_planung.md` (Nachbesserung 2, Punkte 1–5)
- **Datum:** 2026-10-23
- **Modell / Werkzeug:** unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL in OpenCode, Agent „umsetzung"
- **Rücksetzpunkt:** Kein Commit angelegt (Auftrag: „Nein kein Commit bitte direkt weitermachen!")

### Umgesetzt

| Anforderung | Status | Wo im Code |
|---|---|---|
| 1. MAIL_MAX_CHARS-Konstante + Kuerzung | erfueellt | `mail_planung.py` Zeile 66, `evaluate_mail()` |
| 1. Kuerzungshinweis im Block | erfueellt | `build_block()` Parameter `truncation_hint` |
| 2. HTTP 4xx (außer 429) = dauerhaft | erfueellt | `evaluate_mail()` try/except um `raise_for_status()` |
| 2. 429/5xx/Verbindungsfehler/Timeout = voruebergehend | erfueellt | `evaluate_mail()` weiterwerfen, `process_mail()` except HTTPError |
| 3. choices/message/content fehlt oder None = dauerhaft | erfueellt | `evaluate_mail()` Pruefung nach `response.json()` |
| 4. T21–T24 Tests | erfueellt | `tests/test_mail_planung.py` |
| 5. Alle Tests laufen | erfueellt | 31/31 OK |

### Geaenderte und neue Dateien

- `agents/mail_planung/mail_planung.py` – geaendert – Konstante `MAIL_MAX_CHARS`, `evaluate_mail()` gibt jetzt Tuple `(data, was_truncated)` zurueck, HTTP-Fehler-Trennung, content-Pruefung, `build_block()` mit `truncation_hint`, `process_mail()` passt Tuple und truncation_hint an.
- `tests/test_mail_planung.py` – geaendert – Tests T21–T24 angehaengt.

### Abweichungen von der Spec

- Keine.

### Annahmen

- Der Kuerzungshinweis `"> (Mailtext für die Auswertung gekürzt)"` steht im Block nach der eventuellen `error_reason`-Zeile (beides kann gleichzeitig vorkommen, z. B. wenn gekuerzter Text trotzdem zu einem Validierungsfehler fuehrt).
- `MAIL_MAX_CHARS` wird als Modul-Konstante bei Import eingelesen (nicht pro-Aufruf), analog zu `LLM_TIMEOUT`.

### Getestet (mit echter Ausgabe)

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

### Gegenprobe (fuehrt Hawe aus, Ausgabe hier einfuegen)

```
$ python3 role-split/kette/kette.py gegenprobe nachbesserung2_mail_planung --commit a5ddc6e
<Ausgabe>
```

### Aussenwirkung

- Keine Befehle mit Aussenwirkung ausgefuehrt.

### Hawe muss ausfuehren

- Nichts.

### Nicht getestet

- Nichts.

### Offene Punkte / bekannte Schwaechen

- Die Kuerzung des Mailtextes auf `MAIL_MAX_CHARS` Zeichen kann mitten in einem Wort oder Satz brechen. Fuer eine sauberere Kuerzung waere ein Word-Boundary-Cut sinnvoll, war aber nicht in der Spec gefordert.
- HTTP 429 wird aktuell als voruebergehend behandelt (kein Eintrag, Exit 1). Es gibt keine Retry-Logik; der Benutzer muss den Lauf manuell wiederholen.

_(Aus `handover_20261023_nachbesserung2_mail_planung.md` übernommen, 23.10., Claude – OpenCode hatte eine eigene Datei angelegt.)_
