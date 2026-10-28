# Gesamtbefund: mail_server_test

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-24 13:39). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261023_mail_server_test_qwen36-35b.md` | NACHBESSERN |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | NACHBESSERN |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261023_mail_server_test_qwen36-35b.md` | mittel | ja | A11 (Trockenlauf — keine DB) | T6 (`test_t6_dry_run_keine_datei`, Zeile 120) prüft nur `planung.md.exists()`, nicht `mail_planung.db.exists()`. `run_dry()` ruft `init_db()` auf (mail_planung.py:509), was die DB-Anlage (leere Tabelle) zur Folge hat. Spec A11 verlangt „DB existiert nicht oder ist leer". Der Test prüft das nicht. |
| `verdict_20261023_mail_server_test_qwen36-35b.md` | niedrig | ja | T9–T17 (Testplan) | T9–T17 (strukturelle Prüfungen, E2E) werden nicht als Testmethoden ausgeführt. Begründung im Handover: Docker + LLM nicht verfügbar. Die Unit-Tests (K1–K15) prüfen die Logik isoliert, aber nicht die Integration. |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | **hoch** | ja |  | B1 / **hoch** / nein / ja / ja / **Dateiname-Discrepanz (planung.json vs. planning.md):** Start-Skript Zeilen 185-186 prüfen auf `planung.json`, aber `mail_planung.py` Zeile 52 schreibt `planung.md`. Der Test bricht bei Schritt 8 mit Exit 1 ab ("Planungsdatei nicht gefunden!"). Der Test läuft nie bis zum Prüfskript. |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | **hoch** | ja |  | B2 / **hoch** / nein / ja / ja / **`pruefen.py` kennt `--plan-dir` nicht:** Start-Skript Zeile 147 übergibt `--plan-dir "$SCRIPT_DIR/output"`, aber `pruefen.py` Zeile 126 (`parse_args()`) kennt dieses Argument nicht. Das Skript bricht mit "unrecognized arguments" ab, bevor es etwas prüft. |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | **hoch** | ja |  | B3 / **hoch** / nein / ja / ja / **`pruefen.py` nutzt IMAP4_SSL auf unverschlüsseltem Port:** `pruefen.py` Zeile 47 verbindet per `imaplib.IMAP4_SSL` mit Port 3143 (unverschlüsselt). GreenMail auf Port 3143 bietet kein TLS. Die Verbindung schlägt fehl, Exit 1. |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | **hoch** | ja |  | B4 / **hoch** / nein / ja / ja / **`einliefern.py` ruft `starttls()` auf unverschlüsseltem SMTP:** `einliefern.py` Zeile 42 ruft `server.starttls()` auf. GreenMail auf Port 3025 (unverschlüsselt) unterstützt kein STARTTLS. Das Skript bricht mit einem SMTP-Fehler ab, keine Mails werden eingeliefert. |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | **mittel** | ja |  | B5 / **mittel** / nein / ja / nein / **`erwartungen.json`-Format weicht von Spec A9 ab:** Spec A9 definiert Felder wie `block_exists`, `has_aufgaben`, `has_duplikat_warning` etc. Die tatsächliche Datei hat nur `file`, `message_id`, `expected_project`, `expected_status`. `pruefen.py` nutzt nur diese vier Felder und prüft weder Blocks noch Warnungen in der Planungsdatei. |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | **mittel** | ja |  | B6 / **mittel** / nein / ja / nein / **Trockenlauf erstellt DB-Datei:** `run_dry()` (Zeile 752) erstellt `mail_planung.db` mit leerer Tabelle `processed_mails`. Spec A11 sagt: "Die DB existiert nicht (oder ist leer)". Eine leere Tabelle ist technisch "leer", aber die Datei existiert — das ist ein Randfall, der bei strenger Prüfung als Abweichung gelten könnte. |
| `verdict_20261023_mail_server_test_qwen36-35b_betrieb.md` | **mittel** | nein |  | B7 / **mittel** / nein / nein / nein / **Halbfertige Planungsdatei bei LLM-Fehler:** Wenn `main()` bei Mail N fehlschlägt (z.B. LLM-Timeout), enthält `planung.md` die Blöcke von Mail 1..N-1. Der Exit-Code ist 1, `set -euo pipefail` bricht ab, Trap löscht Container und Keychain, aber die halbfertige Datei bleibt. Der Nutzer muss manuell bereinigen. |
