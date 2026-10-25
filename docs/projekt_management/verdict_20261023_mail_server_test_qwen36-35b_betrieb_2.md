# Verdikt: mail_server_test – Betrieb

- **Spec:** `spec_20261023_mail_server_test.md`
- **Handover:** `handover_20261023_mail_server_test.md`
- **Datum:** 2026-10-25
- **Modell:** kette.py (Review-Instanz)
- **Gepruefte Dateien:** `tests/test_mail_server_test.py`, `tests/mail_server_test/start_test_mailserver.sh`, `tests/mail_server_test/einliefern.py`, `tests/mail_server_test/pruefen.py`, `tests/mail_server_test/erwartungen.json`

## Ergebnis

**NACHBESSERN** – Die Spec verlangt Änderungen an `mail_planung.py` (A4, A5), die im Repo fehlen. Der Handover listet dies korrekt als Abweichung auf, aber die Tests T4-T10 sind nur als Skip markiert, was den Nachweis der Betriebsfähigkeit (Keychain-Service, unverschlüsseltes IMAP) verhindert. Zudem fehlen Tests für die Prüflogik (T11-T16) und der E2E-Test (T17) ist nicht automatisiert.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | Testmail-Dateien | erfuellt | `tests/mail_server_test/mails/*.eml` |
| A2 | GreenMail-Docker-Container | erfuellt | `start_test_mailserver.sh` |
| A3 | Schlüsselbund-Eintrag | erfuellt | `start_test_mailserver.sh` |
| A4 | KEYCHAIN_SERVICE per Env | nicht | `mail_planung.py` fehlt |
| A5 | Unverschlüsseltes IMAP | nicht | `mail_planung.py` fehlt |
| A6 | Einlieferungs-Skript | erfuellt | `einliefern.py` |
| A7 | Probelauf-Befehl | teilweise | `start_test_mailserver.sh` (A4/A5 fehlen) |
| A8 | Prüfskript — Struktur | erfuellt | `pruefen.py` |
| A9 | Erwartungs-Datei | erfuellt | `erwartungen.json` |
| A10 | Dedup-Prüfung | teilweise | `pruefen.py` (Logik fehlt, da A4/A5 fehlen) |
| A11 | Trockenlauf-Prüfung | teilweise | `pruefen.py` (Logik fehlt) |
| A12 | Giftmail-Prüfung | teilweise | `pruefen.py` (Logik fehlt) |
| A13 | Injections-Mail-Prüfung | teilweise | `pruefen.py` (Logik fehlt) |
| A14 | Leer-Mail-Prüfung | teilweise | `pruefen.py` (Logik fehlt) |
| A15 | Umlaut-Prüfung | teilweise | `pruefen.py` (Logik fehlt) |
| A16 | Kürzungshinweis-Prüfung | teilweise | `pruefen.py` (Logik fehlt) |
| A17 | End-to-End-Test | nicht | `test_mail_server_test.py` (Skip) |

## Handover gegen Code

- Der Handover behauptet korrekt, dass `mail_planung.py` nicht existiert und Tests T4-T10 als Skip markiert sind.
- Der Handover behauptet, T17 sei als Skip markiert. Dies ist korrekt.
- Der Handover listet "NICHT GET" für T9, T16, T17 auf. T9 und T16 sind Unit-Tests, die eigentlich laufen sollten, wenn die Abhängigkeiten da wären. Da `mail_planung.py` fehlt, sind sie nicht ausführbar.
- Der Handover listet "FEHLT" für T11-T15. Diese Tests existieren im Skript nicht.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `mail_planung.py` | Verstoß gegen A4/A5 | `mail_planung.py` muss erstellt/geändert werden, um A4 und A5 zu erfüllen. Ohne diese Änderungen ist der Testlauf nicht möglich. |
| 2 | nein | ja | nein | mittel | `tests/test_mail_server_test.py` | Unvollständige Testabdeckung | Tests T11-T16 fehlen. Diese prüfen spezifische Edge-Cases (Umlaute, Kürzung, Giftmails), die in der Spec gefordert sind. |
| 3 | nein | ja | nein | niedrig | `tests/test_mail_server_test.py` | E2E-Test nicht automatisiert | T17 ist als Skip markiert. Für einen echten Betriebsnachweis muss der E2E-Test laufen können (Docker + LLM). |

## Nicht geprüft

- **Kann Hawe selbst pruefen:** `mail_planung.py` muss erstellt werden. Danach können T4-T10 und T11-T16 getestet werden.
- **Braucht externe Quelle:** Docker-Container und LLM-Server für T17.