# Verdikt: mail_planung

**Modell:** unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL  
**Datum:** 2026-10-23  
**Rücksetzpunkt:** 5d49488  
**Urteil:** NACHBESSERN

---

## Ergebnis

Zwei Befunde sind **hoch** (Unbemerkt: ja, Harte Vorgabe: ja), eine Anforderung ist teilweise erfüllt. Das Verdikt lautet **NACHBESSERN**.

---

## Befunde

| Nr. | Anforderung | Schwere | Datenverlust | Unbemerkt | Harte Vorgabe | Begründung | Lösungsweg |
|-----|-------------|---------|--------------|-----------|---------------|------------|------------|
| B1  | A7          | hoch    | nein         | ja        | ja            | `run_dry()` (Zeile 620) ruft `get_imap_password()` auf. A7 verlangt "kein Schlüsselbund-Zugriff" im Trockenlauf. | Passwort-Abfrage aus `run_dry()` entfernen; stattdessen IMAP mocken oder `--dry-run` vor dem Passwort-Call abfangen. |
| B2  | A6          | hoch    | nein         | ja        | ja            | `block_marker` (Zeile 571) ist `f"## {mail.get('date', '')}"`. Bei leerem Datum ist der Marker `"## "` — zu allgemein, matcht fälschlich andere Überschriften. Die Prüfung (4a) läuft ins Leere. | Marker spezifischer machen: z. B. `f"## {mail.get('date', '')} — {mail.get('subject', '')}"` oder Message-ID im Block suchen. |
| B3  | A5          | mittel  | nein         | teilweise | teilweise     | `validate_evaluation` (Zeile 427) prüft nur Regex `\d{4}-\d{2}-\d{2}` für Datumsformat, nicht die Gültigkeit (Monat 13, Tag 32 durchrutschen). Anforderung sagt "Datum gültig". | Datumsvalidierung mit `datetime.strptime` erweitern, nicht nur Regex. |

---

## Anforderungen einzeln

**A1 (Markdown-Planungsdatei — Schema und atomares Schreiben):** Erfüllt. Schema wird durch `build_block` erzwungen, atomares Schreiben per `mkstemp` + `os.replace` (Zeilen 382–408). Kein Befund.

**A2 (Lesen des Postfachs — read-only):** Erfüllt. `imap.select("INBOX", readonly=True)` (Zeile 186). Keine IMAP-Write-Befehle. Kein Befund.

**A3 (Deduplizierung — Message-ID als Primärschlüssel):** Erfüllt. `is_new_mail` prüft UNIQUE-Index (Zeile 114–119). Synthetische ID bei fehlendem Header (Zeile 153–165). Kein Befund.

**A4 (Mögliche Duplikate — gleicher Inhalt, neue Message-ID):** Erfüllt. `detect_possible_duplicate` (Zeile 134–146) prüft body_hash, `build_block` (Zeile 336–337) fügt Warnung ein. Kein Befund.

**A5 (Auswertung durch das LLM — nur Daten zurück, keine Werkzeuge):** Teilweise erfüllt. Kein `tools`-Parameter, JSON-Validierung vorhanden. Aber Datumsprüfung prüft nur Format, nicht Gültigkeit (B3).

**A6 (Fehlerpfad — Mail wird erst nach erfolgreichem Schreiben markiert):** Teilweise erfüllt. Reihenfolge ist korrekt (LLM → Block → Schreiben → Check → Marker). Aber `block_marker` ist zu allgemein (B2).

**A7 (Trockenlauf):** Nicht erfüllt. `run_dry()` ruft `get_imap_password()` auf (Zeile 620), obwohl A7 "kein Schlüsselbund-Zugriff" verlangt (B1).

**A8 (Zugangsdaten nur aus dem Schlüsselbund):** Erfüllt. `get_imap_password` nutzt nur `security find-generic-password`. Kein Logging des Passworts. Kein Befund.

**A9 (Schwierige Mails — HTML, Umlaute, leerer Text, Anhang, Weiterleitungskette):** Erfüllt. `extract_text` (Zeile 265–301) behandelt alle fünf Fälle. Kein Befund.

**A10 (Projekt-Zuordnung — nur über Konfigurationsdatei):** Erfüllt. `resolve_project` (Zeile 486–516) liest Konfigdatei, ignoriert LLM-Wert. Kein Befund.

---

## Nicht geprüft

- Echter IMAP-Server-Connect (per Mock ersetzt, wie in der Spec vorgesehen).
- Echter Schlüsselbund-Zugriff (per Mock ersetzt).
- Echter LLM-API-Call (per Mock ersetzt).
- launchd-Integration (Nicht-Ziel der Spec).
- T1: In der Spec nicht als Testmethode definiert, daher kein Test vorhanden — kein Befund.
- Test T11 prüft `process_mail(dry_run=True)` direkt, nicht `run_dry()` — erfasst den A7-Verstoß nicht.
