# Verdikt: mail_planung — Betrieb (2. Review)

**Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL  
**Datum:** 2026-10-23  
**Basis:** Review-Paket `experiments/probe_k6/review_paket_probe.md`  
**Geprüfte Dateien:** `agents/mail_planung/mail_planung.py` (718 Z.), `agents/mail_planung/test_mail_planung.py` (599 Z.), Anforderung + Antworten auf Rückfragen (im Review-Paket)  
**Urteil:** NACHBESSERN

---

## Befunde

| # | Anforderung | Befund | Datenverlust | Unbemerkt | Harte Vorgabe | Schwere |
|---|------------|--------|-------------|-----------|---------------|---------|
| B1 | A7 (Trockenlauf) | `run_dry()` (Zeile 620) ruft `get_imap_password()` auf — Schlüsselbund-Zugriff trotz Vorgabe "kein Schlüsselbund-Zugriff". | nein | teilweise — fehlschlägt sichtbar, wenn Eintrag fehlt | ja | hoch |
| B2 | A6 (Verifikation) | `block_marker` (Zeile 571) ist nur `## <Datum>`. Bei zwei Mails am selben Tag findet String-Suche den falschen Block → Verifikation positiv, obwohl falscher Eintrag geschrieben wurde. | nein | ja | ja | hoch |
| B3 | A5 (LLM-JSON) | `json.loads(content)` (Zeile 470) scheitert an Markdown-Codeblöcken (````json ... ````). LLMs liefern das häufig. Kein Fallback. | nein | ja — wiederkehrender Fehler, nur stderr | ja | hoch |
| B4 | A8 (Schlüsselbund) | `.decode().strip()` (Zeile 85) entfernt End-Leerzeichen des Passworts. Gültige Passwörter mit trailing space werden falsch. | nein | ja — IMAP-Auth-Fehler, Ursache nicht offensichtlich | ja | mittel |
| B5 | A6 (Fehlerwiederholung) | Bei LLM-Fehler (B3) bleibt Mail offen, wird bei jedem Lauf wiederholt. Exit 1 + stderr. Ohne Log-Überwachung (launchd) unbemerkt. | nein | ja | teilweise | mittel |

## Nicht geprüft

- Echter IMAP-Server mit TLS-Verhandlung und MIME-Parsing.
- Echte LLM-Antworten (Markdown-Codeblöcke, Tool-Use, lange Antworten).
- launchd-Integration (Nicht-Ziel der Spec, aber Betriebskontext).
- HTML-Parsing bei komplexen Strukturen (Tabellen, verschachtelte Divs).
- Schlüsselbund-Erfolgsfall (Passwort mit Sonderzeichen, die `security`-CLI beeinflusst).

---
