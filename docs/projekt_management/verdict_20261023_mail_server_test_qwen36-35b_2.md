# Verdikt: mail_server_test

- **Spec:** `spec_20261023_mail_server_test.md`
- **Handover:** `handover_20261023_mail_server_test.md`
- **Datum:** 2026-10-25
- **Modell:** Qwen3.6-27B-MTP-GGUF
- **Gepruefte Dateien:** `tests/test_mail_server_test.py`, `tests/mail_server_test/start_test_mailserver.sh`, `tests/mail_server_test/einliefern.py`, `tests/mail_server_test/pruefen.py`, `tests/mail_server_test/erwartungen.json`, `agents/mail_planung/mail_planung.py` (Existenz geprüft, Inhalt nicht geändert)

## Ergebnis

**NACHBESSERN** – Die Umsetzung ist unvollständig. Der Kern der Anforderung (A4, A5, A17) fehlt, da die Datei `mail_planung.py` nicht existiert bzw. nicht geändert wurde. Die Tests sind größtenteils als `Skip` markiert oder prüfen nur Infrastruktur (Docker, Ports), nicht aber die eigentliche Logik des Mail-Planers. Der Handover behauptet fälschlicherweise, T4-T10 seien "ok", obwohl sie auf nicht-existentem Code basieren.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Testmail-Dateien (16 .eml) | erfuellt | `tests/mail_server_test/mails/` (Dateien vorhanden) |
| A2 | GreenMail-Docker-Container | erfuellt | `tests/mail_server_test/start_test_mailserver.sh` (Skript vorhanden) |
| A3 | Schlüsselbund-Eintrag | erfuellt | `tests/mail_server_test/start_test_mailserver.sh` (Logik vorhanden) |
| A4 | KEYCHAIN_SERVICE per Env-Var | nicht | `agents/mail_planung/mail_planung.py` (Datei existiert nicht/geändert) |
| A5 | Unverschlüsseltes IMAP nur localhost | nicht | `agents/mail_planung/mail_planung.py` (Datei existiert nicht/geändert) |
| A6 | Einlieferungs-Skript | erfuellt | `tests/mail_server_test/einliefern.py` (Skript vorhanden) |
| A7 | Probelauf-Befehl (Shell-Skript) | teilweise | `tests/mail_server_test/start_test_mailserver.sh` (Skript vorhanden, ruft nicht-existenten Code auf) |
| A8 | Prüfskript — strukturelle Prüfungen | teilweise | `tests/mail_server_test/pruefen.py` (Skript vorhanden, aber Logik unvollständig) |
| A9 | Erwartungs-Datei | erfuellt | `tests/mail_server_test/erwartungen.json` (Datei vorhanden) |
| A10 | Prüfskript — Dedup-Prüfung | teilweise | `tests/mail_server_test/pruefen.py` (Logik vorhanden, aber ungetestet) |
| A11 | Prüfskript — Trockenlauf | teilweise | `tests/mail_server_test/pruefen.py` (Logik vorhanden, aber ungetestet) |
| A12 | Prüfskript — Giftmail-Prüfung | teilweise | `tests/mail_server_test/pruefen.py` (Logik vorhanden, aber ungetestet) |
| A13 | Prüfskript — Injections-Mail-Prüfung | teilweise | `tests/mail_server_test/pruefen.py` (Logik vorhanden, aber ungetestet) |
| A14 | Prüfskript — Leer-Mail-Prüfung | teilweise | `tests/mail_server_test/pruefen.py` (Logik vorhanden, aber ungetestet) |
| A15 | Prüfskript — Umlaut-Prüfung | teilweise | `tests/mail_server_test/pruefen.py` (Logik vorhanden, aber ungetestet) |
| A16 | Prüfskript — Kürzungshinweis-Prüfung | teilweise | `tests/mail_server_test/pruefen.py` (Logik vorhanden, aber ungetestet) |
| A17 | End-to-End-Test | nicht | `tests/test_mail_server_test.py` (Test als Skip markiert, benötigt Docker/LLM) |

## Handover gegen Code

- Der Handover behauptet unter "Abweichungen", dass `mail_planung.py` nicht geändert wurde und Tests T4-T10 als Skip markiert sind. Dies ist korrekt, stellt aber eine **massive Abweichung von der Anforderung A4, A5 und A17** dar. Die Anforderung verlangt explizit die Code-Änderung in `mail_planung.py`. Das Fehlen dieser Änderung ist kein "Restrisiko", sondern ein fehlendes Deliverable.
- Der Handover listet T1-T3 als "ok" auf. T1-T3 prüfen nur Infrastruktur (Ports, Docker, Skript-Existenz). Sie testen nicht die Funktionalität des Mail-Planers.
- Der Handover behauptet, T10 sei "byte-identisch bestanden". Da `mail_planung.py` fehlt, kann dieser Test nicht laufen. Die Aussage ist irreführend.
- Der Handover ignoriert, dass A4 und A5 (die Kernanforderungen für die Sicherheit und Konfigurierbarkeit) nicht umgesetzt sind.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `agents/mail_planung/mail_planung.py` | A4/A5 nicht umgesetzt | Die Anforderung A4 und A5 verlangen Code-Änderungen in `mail_planung.py`. Diese Datei existiert im Repo nicht oder wurde nicht geändert. Ohne diese Änderungen ist der Test nicht möglich und die Sicherheitsanforderung (nur localhost unverschlüsselt) nicht erfüllt. |
| 2 | nein | ja | ja | hoch | `tests/test_mail_server_test.py` | A17 nicht umgesetzt | Der End-to-End-Test (A17) ist als Skip markiert. Die Anforderung verlangt einen unittest, der den kompletten Probelauf ausführt. Ohne diesen Test ist die Integration nicht verifiziert. |
| 3 | nein | ja | nein | mittel | `tests/mail_server_test/pruefen.py` | A8-A16 ungetestet | Die Prüfskripte sind vorhanden, aber ihre Logik wird nicht durch Unit-Tests abgedeckt, da sie von `mail_planung.py` abhängen, das fehlt. Die Tests T11-T16 fehlen im Testskript. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** `mail_planung.py` muss erstellt/geändert werden. Danach müssen die Tests T4-T10 und T17 aktiviert und ausgeführt werden.
- **Braucht externe Quelle:** Docker-Container (GreenMail) und LLM-Server (localhost:8080) für den E2E-Test (T17).

## Abweichende Meinung

- Die Review-Instanz bewertet das Fehlen der Kern-Code-Änderungen (A4, A5) als "FAIL" bzw. "NACHBESSERN", da dies eine harte Vorgabe der Spec ist. Der Handover versucht dies als "Abweichung" zu tarnen, aber es ist ein fehlendes Deliverable.
- Die Infrastruktur-Tests (T1-T3) sind gut, aber sie ersetzen nicht die Funktionalitätstests.