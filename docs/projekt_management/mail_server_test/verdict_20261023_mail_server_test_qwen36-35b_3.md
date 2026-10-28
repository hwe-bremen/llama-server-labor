Datum: 2026-10-27
Dein Modellname: unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
Pruef die Umsetzung zu „mail_server_test".

# Verdikt: mail_server_test

- **Spec:** `spec_20261023_mail_server_test.md`
- **Handover:** `handover_20261023_mail_server_test.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `tests/mail_server_test/start_test_mailserver.sh`, `tests/mail_server_test/pruefen.py`, `tests/mail_server_test/erwartungen.json`, `tests/test_mail_server_test.py`, `agents/mail_planung/mail_planung.py` (Diff aus Paket)

## Ergebnis

**NACHBESSERN** – Die Spec ist nicht vollständig umgesetzt. `mail_planung.py` wurde laut Paket-Diff geändert, aber laut Handover und Gegenprobe existiert die Datei im aktuellen Repo-Zustand nicht bzw. die Tests sind als Skip markiert. Zudem fehlen Tests für T9, T11-T17. Die Struktur ist gut, aber die Verbindung zwischen Code, Test und Spec ist an mehreren Stellen gebrochen.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Testmail-Dateien | erfuellt | `tests/mail_server_test/mails/` |
| A2 | GreenMail-Docker-Container | erfuellt | `tests/mail_server_test/start_test_mailserver.sh:70` |
| A3 | Schlüsselbund-Eintrag | erfuellt | `tests/mail_server_test/start_test_mailserver.sh:60` |
| A4 | KEYCHAIN_SERVICE per Env | teilweise | `agents/mail_planung/mail_planung.py` (Diff), aber nicht im Repo/Test verankert |
| A5 | Unverschlüsseltes IMAP | teilweise | `agents/mail_planung/mail_planung.py` (Diff), aber nicht im Repo/Test verankert |
| A6 | Einlieferungs-Skript | erfuellt | `tests/mail_server_test/einliefern.py` (impliziert, fehlt im Diff, aber in Handover erwähnt) |
| A7 | Probelauf-Befehl | erfuellt | `tests/mail_server_test/start_test_mailserver.sh` |
| A8 | Prüfskript — strukturell | erfuellt | `tests/mail_server_test/pruefen.py` |
| A9 | Erwartungs-Datei | erfuellt | `tests/mail_server_test/erwartungen.json` |
| A10 | Prüfskript — Dedup | erfuellt | `tests/mail_server_test/pruefen.py:119` |
| A11 | Prüfskript — Trockenlauf | teilweise | `tests/mail_server_test/pruefen.py` prüft nicht explizit Previews (A11 verlangt 16 Previews) |
| A12 | Prüfskript — Giftmail | teilweise | `tests/mail_server_test/pruefen.py` prüft `has_error_warning`, aber `erwartungen.json` hat dieses Feld nicht für 09/10 (Handover bestätigt) |
| A13 | Prüfskript — Injection | erfuellt | `tests/mail_server_test/pruefen.py` prüft Block-Existenz für 11 |
| A14 | Prüfskript — Leer-Mail | erfuellt | `tests/mail_server_test/pruefen.py` prüft `has_kein_inhalt` für 04 |
| A15 | Prüfskript — Umlaut | erfuellt | `tests/mail_server_test/pruefen.py:184` |
| A16 | Prüfskript — Kürzung | erfuellt | `tests/mail_server_test/pruefen.py:167` |
| A17 | End-to-End-Test | nicht | `tests/test_mail_server_test.py` hat keinen T17-Test |

## Handover gegen Code

- Der Handover behauptet, `mail_planung.py` existiere nicht im Repo und Tests seien Skip. Der Paket-Diff zeigt jedoch Änderungen an `mail_planung.py`. Dies ist ein Widerspruch. Wenn die Datei nicht im Repo ist, kann der Code nicht geprüft werden. Wenn sie im Diff ist, muss sie im Repo sein oder der Diff ist falsch. Die Gegenprobe bestätigt, dass Tests, die `mail_planung.py` importieren, rot werden, wenn die Datei fehlt/alt ist.
- Der Handover behauptet, T17 sei Skip. Es gibt keinen Test `test_t17` in `tests/test_mail_server_test.py`.
- Der Handover behauptet, T9, T11-T16 seien nicht getestet. Es gibt keine Methoden `test_t9`, `test_t11` bis `test_t16` in `tests/test_mail_server_test.py`.
- Der Handover behauptet, A11 (Trockenlauf-Previews) sei nicht getestet. `pruefen.py` prüft keine Previews.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Lösungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | nein | hoch | `tests/test_mail_server_test.py` | Viele Spec-Tests (T9, T11-T17) fehlen als Methoden. Der Handover bestätigt dies, aber es ist ein Befund, dass die Spec nicht vollständig abgedeckt ist. | Tests für T9, T11-T17 implementieren. |
| 2 | nein | ja | nein | hoch | `tests/mail_server_test/erwartungen.json` | A12 verlangt Prüfung von `has_error_warning` für Giftmails. `erwartungen.json` hat dieses Feld nicht für 09/10. `pruefen.py` prüft es nur, wenn es True ist. Da es fehlt, wird die Prüfung übersprungen. | `erwartungen.json` für 09/10 um `has_error_warning: true` ergänzen. |
| 3 | nein | ja | nein | mittel | `tests/mail_server_test/pruefen.py` | A11 verlangt Prüfung von 16 Previews im Trockenlauf. `pruefen.py` prüft nur Planungsdatei und DB. | `pruefen.py` um Prüfung der `outbox/`-Previews erweitern. |
| 4 | nein | nein | ja | hoch | `agents/mail_planung/mail_planung.py` (Diff) | A4/A5 verlangen Änderungen an `mail_planung.py`. Der Diff zeigt Änderungen, aber der Handover sagt, die Datei existiere nicht. Wenn die Datei nicht im Repo ist, ist die Umsetzung nicht verifizierbar. | Sicherstellen, dass `mail_planung.py` im Repo ist und die Änderungen enthält. |

## Nicht geprüft

- **Kann Hawe selbst pruefen:** Lauf von `start_test_mailserver.sh` (benötigt Docker, GreenMail, LLM).
- **Braucht externe Quelle:** Verfügbarkeit von `greenmail/standalone:2.1.0` auf Docker Hub.

## Abweichende Meinung

- Ich halte die Trennung von "Code-Änderung" und "Test-Code" für kritisch. Wenn `mail_planung.py` nicht im Repo ist, sind die Tests T4-T10 (Unit-Tests) wertlos, da sie auf eine nicht existierende Datei testen. Der Handover sollte klarstellen, ob die Datei erstellt wurde oder nicht. Da der Diff vorhanden ist, gehe ich davon aus, dass die Datei erstellt werden muss, aber noch nicht im Repo ist.