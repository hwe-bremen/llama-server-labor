# Verdikt: mail_server_test

**Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
**Datum:** 2026-10-24
**Rücksetzpunkt:** 37b1da1
**Geprüfte Datei:** `agents/mail_planung/mail_planung.py` (Diff, 31 Zeilen)
**Maßstab:** Spec `spec_20261023_mail_server_test.md` (keine separate Anforderungsdatei)

## Ergebnis

**NACHBESSERN**

Befund 1 (unbemerkt, mittel) begründet das Urteil. Der Code ist korrekt, aber der Testplan deckt einen Teil der Spec nicht ab.

## Befunde

| # | Anforderung | Schwere | Datenverlust | Unbemerkt | Harte Vorgabe | Begründung | Lösungsweg |
|---|---|---|---|---|---|---|---|
| 1 | A11 (Trockenlauf — keine DB) | mittel | nein | ja | ja | T6 (`test_t6_dry_run_keine_datei`, Zeile 120) prüft nur `planung.md.exists()`, nicht `mail_planung.db.exists()`. `run_dry()` ruft `init_db()` auf (mail_planung.py:509), was die DB-Anlage (leere Tabelle) zur Folge hat. Spec A11 verlangt „DB existiert nicht oder ist leer". Der Test prüft das nicht. | T6 um DB-Existenzprüfung ergänzen. |
| 2 | T9–T17 (Testplan) | niedrig | nein | ja | nein | T9–T17 (strukturelle Prüfungen, E2E) werden nicht als Testmethoden ausgeführt. Begründung im Handover: Docker + LLM nicht verfügbar. Die Unit-Tests (K1–K15) prüfen die Logik isoliert, aber nicht die Integration. | Hawe muss T17 manuell ausführen. T9–T16 können durch `pruefen.py` nach einem echten Lauf geprüft werden. |

## Anforderungen einzeln

| Anforderung | Status | Begründung |
|---|---|---|
| A1 (16 Testmail-Dateien) | erfüllt | Keine Code-Änderung erforderlich. |
| A2 (GreenMail-Container) | erfüllt | Keine Code-Änderung erforderlich. |
| A3 (Schlüsselbund-Eintrag) | erfüllt | Keine Code-Änderung erforderlich. |
| A4 (KEYCHAIN_SERVICE per Env) | erfüllt | `os.getenv("MAIL_IMAP_KEYCHAIN_SERVICE", "lab-mail-imap")` (mail_planung.py:58). T4 prüft Default und Custom. |
| A5 (Unverschlüsseltes IMAP nur localhost) | erfüllt | `if MAIL_IMAP_UNENCRYPTED:` mit Host-Check und `sys.exit(1)` (mail_planung.py:186-193). T5 prüft alle drei Fälle. |
| A6 (Einlieferungs-Skript) | erfüllt | Keine Code-Änderung erforderlich. |
| A7 (Probelauf-Befehl) | erfüllt | Keine Code-Änderung erforderlich. |
| A8 (Prüfskript — strukturelle Prüfungen) | erfüllt | Keine Code-Änderung erforderlich. |
| A9 (Erwartungs-Datei) | erfüllt | Keine Code-Änderung erforderlich. |
| A10 (Dedup-Prüfung) | erfüllt | Keine Code-Änderung erforderlich. |
| A11 (Trockenlauf — keine Planungsdatei) | teilweise erfüllt | T6 prüft nur `planung.md`, nicht die DB. Siehe Befund 1. |
| A12 (Giftmail-Prüfung) | erfüllt | Keine Code-Änderung erforderlich. |
| A13 (Injections-Mail-Prüfung) | erfüllt | Keine Code-Änderung erforderlich. |
| A14 (Leer-Mail-Prüfung) | erfüllt | Keine Code-Änderung erforderlich. |
| A15 (Umlaut-Prüfung) | erfüllt | Keine Code-Änderung erforderlich. |
| A16 (Kürzungshinweis-Prüfung) | erfüllt | Keine Code-Änderung erforderlich. |
| A17 (End-to-End-Test) | erfüllt | Keine Code-Änderung erforderlich. |

## Nicht geprüft

- **T17 (End-to-End mit Docker + echtem LLM):** Erfordert Docker, GreenMail und ein lokales LLM-Modell. Kann im unbeaufsichtigten Modus nicht ausgeführt werden. Hawe muss den Test manuell starten.
- **T9–T16 (strukturelle Prüfungen mit echten Mails):** Werden durch Unit-Tests (K1–K15) abgedeckt, aber nicht durch Integrationstests.
- **T1–T3 als echter Skript-Aufruf:** Tests prüfen das Skript durch String-Suche (Code-Inspektion), nicht durch echten Aufruf. Das ist bewusst so gewählt (kein Außenwirkung), aber bedeutet, dass das Skript selbst nicht als Blackbox getestet wird.
- **Giftmails (09, 10) und Injections-Mail (11) im echten Lauf:** Die Unit-Tests (K10, K11) prüfen Validierung und Fehler-Blöcke isoliert, aber nicht mit echten LLM-Antworten.
