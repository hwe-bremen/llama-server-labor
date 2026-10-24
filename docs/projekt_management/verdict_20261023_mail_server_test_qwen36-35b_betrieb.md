# Verdikt: mail_server_test — Betriebswinkel

**Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL  
**Datum:** 2026-10-23  
**Review-Typ:** BETRIEB (zweites Review)  
**Urteil:** NACHBESSERN

---

## Befunde

| # | Schwere | Datenverlust | Unbemerkt | Harte Vorgabe | Beschreibung |
|---|---------|:-----------:|:---------:|:-------------:|--------------|
| B1 | **hoch** | nein | ja | ja | **Dateiname-Discrepanz (planung.json vs. planning.md):** Start-Skript Zeilen 185-186 prüfen auf `planung.json`, aber `mail_planung.py` Zeile 52 schreibt `planung.md`. Der Test bricht bei Schritt 8 mit Exit 1 ab ("Planungsdatei nicht gefunden!"). Der Test läuft nie bis zum Prüfskript. |
| B2 | **hoch** | nein | ja | ja | **`pruefen.py` kennt `--plan-dir` nicht:** Start-Skript Zeile 147 übergibt `--plan-dir "$SCRIPT_DIR/output"`, aber `pruefen.py` Zeile 126 (`parse_args()`) kennt dieses Argument nicht. Das Skript bricht mit "unrecognized arguments" ab, bevor es etwas prüft. |
| B3 | **hoch** | nein | ja | ja | **`pruefen.py` nutzt IMAP4_SSL auf unverschlüsseltem Port:** `pruefen.py` Zeile 47 verbindet per `imaplib.IMAP4_SSL` mit Port 3143 (unverschlüsselt). GreenMail auf Port 3143 bietet kein TLS. Die Verbindung schlägt fehl, Exit 1. |
| B4 | **hoch** | nein | ja | ja | **`einliefern.py` ruft `starttls()` auf unverschlüsseltem SMTP:** `einliefern.py` Zeile 42 ruft `server.starttls()` auf. GreenMail auf Port 3025 (unverschlüsselt) unterstützt kein STARTTLS. Das Skript bricht mit einem SMTP-Fehler ab, keine Mails werden eingeliefert. |
| B5 | **mittel** | nein | ja | nein | **`erwartungen.json`-Format weicht von Spec A9 ab:** Spec A9 definiert Felder wie `block_exists`, `has_aufgaben`, `has_duplikat_warning` etc. Die tatsächliche Datei hat nur `file`, `message_id`, `expected_project`, `expected_status`. `pruefen.py` nutzt nur diese vier Felder und prüft weder Blocks noch Warnungen in der Planungsdatei. |
| B6 | **mittel** | nein | ja | nein | **Trockenlauf erstellt DB-Datei:** `run_dry()` (Zeile 752) erstellt `mail_planung.db` mit leerer Tabelle `processed_mails`. Spec A11 sagt: "Die DB existiert nicht (oder ist leer)". Eine leere Tabelle ist technisch "leer", aber die Datei existiert — das ist ein Randfall, der bei strenger Prüfung als Abweichung gelten könnte. |
| B7 | **mittel** | nein | nein | nein | **Halbfertige Planungsdatei bei LLM-Fehler:** Wenn `main()` bei Mail N fehlschlägt (z.B. LLM-Timeout), enthält `planung.md` die Blöcke von Mail 1..N-1. Der Exit-Code ist 1, `set -euo pipefail` bricht ab, Trap löscht Container und Keychain, aber die halbfertige Datei bleibt. Der Nutzer muss manuell bereinigen. |

---

## Nicht geprüft

- **T17 (End-to-End mit Docker + echtem LLM):** Kann nicht geprüft werden, da keine echte Docker/LLM-Umgebung verfügbar.
- **LLM-Verhalten bei echten Mails:** Die 16 Testmail-Dateien sind statisch; das LLM-Verhalten bei echten Daten ist nicht prüfbar.
- **Schlüsselbund-Integration auf echtem System:** `security add-generic-password` und `delete-generic-password` können nur auf macOS mit Keychain geprüft werden.
- **GreenMail-Verhalten mit echten RFC 5322-Mails:** Sonderfälle (Umlaute, sehr lange Bodies, Injection-Texte) werden nur durch die Attrappe GreenMail abgedeckt.
- **Start als Modul vs. als Skript:** Import-Zeilen und `sys.path`-Anpassung in `mail_planung.py` (Zeilen 37-40) könnten beim Import als Modul Probleme verursachen.
