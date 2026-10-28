# Verdikt: mail_server_test

- **Spec:** `spec_20261023_mail_server_test.md`
- **Handover:** `handover_20261023_mail_server_test.md`
- **Datum:** 2026-10-27
- **Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL
- **Gepruefte Dateien:** `agents/mail_planung/mail_planung.py`, `tests/mail_server_test/start_test_mailserver.sh`, `tests/mail_server_test/pruefen.py`, `tests/mail_server_test/erwartungen.json`, `tests/test_mail_server_test.py`, `tests/mail_server_test/mails/*.eml`

## Ergebnis

**NACHBESSERN** – Die Spec fordert Änderungen an `mail_planung.py` (A4, A5), die im diff enthalten, aber im Repository-Zustand zum Zeitpunkt der Prüfung nicht vorhanden oder nicht integriert sind. Zudem fehlen Tests für die kritischen E2E-Szenarien (Giftmails, Injections, Dedup-Verhalten) im Python-Testskript, was die Validierung der Anforderungen A12–A16 unmöglich macht.

## Anforderungen einzeln

| Nr. | Anforderung (kurz) | Befund | Fundstelle |
|---|---|---|---|
| A1 | 16 Testmails vorhanden | erfuellt | `tests/mail_server_test/mails/` |
| A2 | GreenMail Docker Container | erfuellt | `start_test_mailserver.sh:70` |
| A3 | Schlüsselbund-Eintrag Test | erfuellt | `start_test_mailserver.sh:60` |
| A4 | KEYCHAIN_SERVICE per Env | teilweise | `mail_planung.py` (Diff vorhanden, aber Datei-Status unklar/fehlend im Lauf) |
| A5 | Unverschlüsseltes IMAP localhost | teilweise | `mail_planung.py` (Diff vorhanden, aber Datei-Status unklar/fehlend im Lauf) |
| A6 | Einlieferungs-Skript | erfuellt | `start_test_mailserver.sh:110`, `einliefern.py` (fehlt im Paket, aber Referenz vorhanden) |
| A7 | Probelauf-Befehl (Skript) | erfuellt | `start_test_mailserver.sh` |
| A8 | Prüfskript Struktur | erfuellt | `pruefen.py` |
| A9 | Erwartungen JSON | erfuellt | `erwartungen.json` |
| A10 | Dedup-Prüfung (2. Lauf) | teilweise | `pruefen.py:215` (Byte-Identität geprüft, aber Logik in `mail_planung.py` fehlt im validierten Stand) |
| A11 | Trockenlauf-Prüfung | teilweise | `pruefen.py` (Prüfung auf Existenz/Leere vorhanden, aber `outbox`-Prüfung fehlt im Skript) |
| A12 | Giftmail-Prüfung | nicht | `pruefen.py` (Keine Prüfung auf `has_error_warning` für 09/10 in `erwartungen.json` aktiviert, Test fehlt) |
| A13 | Injections-Mail-Prüfung | nicht | `pruefen.py` (Keine spezifische Prüfung auf Injektions-Ignore, Test fehlt) |
| A14 | Leer-Mail-Prüfung | teilweise | `erwartungen.json:33` (Prüfung konfiguriert, aber Implementierung im Skript nur teilweise abgedeckt durch `has_kein_inhalt`) |
| A15 | Umlaut-Prüfung | erfuellt | `pruefen.py:184` |
| A16 | Kürzungshinweis-Prüfung | erfuellt | `pruefen.py:167` |
| A17 | End-to-End Test | nicht | `test_mail_server_test.py` (Als Skip markiert, kein echter Lauf gegen Docker/LLM) |

## Handover gegen Code

- Der Handover behauptet, `mail_planung.py` sei geänderten Code enthalten, aber die "Gegenprobe" zeigt, dass Tests, die gegen die *alte* Datei laufen, rot werden. Dies bestätigt, dass die Änderungen in A4/A5 **nicht** im aktuellen Repository-Status enthalten sind, der getestet wurde. Der Diff wurde geliefert, aber die Integration ist nicht verifiziert.
- Der Handover listet "NICHT GET" für T9, T11-T17 auf. Die Begründung "Test fehlt" ist korrekt. Die Spec fordert jedoch explizit diese Prüfungen (A10-A16). Das Fehlen der Tests ist ein Mangel.
- `einliefern.py` wird im Skript aufgerufen, ist aber im Paket "weggelassen". Dies ist ein Risiko für die Reproduzierbarkeit, wenn die Datei nicht separat bereitgestellt wird.

## Befunde

| # | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere | Datei:Zeile | Befund | Loesungsweg (in Worten) |
|---|---|---|---|---|---|---|---|
| 1 | nein | ja | ja | hoch | `mail_planung.py` | **A4/A5: Code-Änderungen nicht im validierten Stand.** Die Spec fordert explizite Änderungen an `mail_planung.py` (Env-Vars für Keychain und IMAP-Encryption). Der Diff zeigt die Änderungen, aber die Tests (T4, T5) schlagen fehl oder sind skippt, weil die Datei nicht den Anforderungen entspricht. Ohne diese Änderungen ist der Testlauf (A7) nicht sicher durchführbar (Schlüsselbund-Fehler oder SSL-Fehler). |
| 2 | nein | ja | ja | hoch | `tests/test_mail_server_test.py` | **A12-A16: Fehlende Tests für spezifische Mail-Szenarien.** Die Spec fordert Prüfungen für Giftmails (A12), Injections (A13), Leermails (A14), Umlaute (A15) und Kürzung (A16). Im Testskript fehlen die Methoden `test_t...` oder `test_k...` für diese spezifischen Fälle. Nur A15 (Umlaute) ist teilweise in `pruefen.py` abgedeckt, aber nicht als Unit-Test gegen die finale Planung. |
| 3 | nein | ja | nein | mittel | `tests/mail_server_test/start_test_mailserver.sh` | **A11: Trockenlauf-Prüfung unvollständig.** Die Spec (A11) fordert, dass unter `MAIL_PLAN_DIR/outbox/` 16 Preview-Dateien liegen. `pruefen.py` prüft dies nicht. Es prüft nur, dass `planung.md` und die DB nicht existieren. |
| 4 | nein | nein | nein | niedrig | `tests/mail_server_test/erwartungen.json` | **A9: Fehlende Felder für Giftmails.** In `erwartungen.json` fehlen für Mails 09 und 10 die Felder `has_error_warning`, `has_kein_inhalt`, etc. Der Handover erklärt dies damit, dass der LLM-Output nicht vorhersehbar sei. Dies ist eine Abweichung von der Spec, die strukturelle Prüfungen fordert. |

## Nicht geprueft

- **Kann Hawe selbst pruefen:** Der echte E2E-Lauf (T17) gegen GreenMail und den lokalen LLM-Server. Dies erfordert Docker und ein laufendes LLM.
- **Braucht externe Quelle:** Die korrekte Funktion von `einliefern.py` (fehlt im Paket).

## Abweichende Meinung

- Ich bewertet den Status von `mail_planung.py` als "Nicht erfüllt", da der Diff nicht im Repository-Status enthalten ist, der getestet wurde. Der Handover listet die Datei als "geaendert" auf, aber die Gegenprobe zeigt, dass der Code im Repo noch der alte ist. Dies ist ein kritischer Fehler für die Testbarkeit.