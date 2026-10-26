# Gesamtbefund: mail_planung

Mechanisch zusammengeführt mit `kette.py zusammenfuehren` (2026-10-23 13:51). Kein Befund wurde weggelassen oder umformuliert.

## Ergebnis

**NACHBESSERN** – Regel: ein hoher Befund in irgendeinem Lauf ergibt NACHBESSERN.

| Lauf | Ergebnis des Laufs |
|---|---|
| `verdict_20261022_mail_planung_qwen36-35b.md` | NACHBESSERN |
| `verdict_20261023_probe_k6_qwen36-35b_betrieb.md` | NACHBESSERN |

## Befunde (alle Läufe)

| Lauf | Schwere | hoch nach Regel | Fundstelle | Befund |
|---|---|---|---|---|
| `verdict_20261022_mail_planung_qwen36-35b.md` | hoch | ja | A7 | `run_dry()` (Zeile 620) ruft `get_imap_password()` auf. A7 verlangt "kein Schlüsselbund-Zugriff" im Trockenlauf. |
| `verdict_20261022_mail_planung_qwen36-35b.md` | hoch | ja | A6 | `block_marker` (Zeile 571) ist `f"## {mail.get('date', '')}"`. Bei leerem Datum ist der Marker `"## "` — zu allgemein, matcht fälschlich andere Überschriften. Die Prüfung (4a) läuft ins Leere. |
| `verdict_20261022_mail_planung_qwen36-35b.md` | mittel | nein | A5 | `validate_evaluation` (Zeile 427) prüft nur Regex `\d{4}-\d{2}-\d{2}` für Datumsformat, nicht die Gültigkeit (Monat 13, Tag 32 durchrutschen). Anforderung sagt "Datum gültig". |
| `verdict_20261023_probe_k6_qwen36-35b_betrieb.md` | hoch | ja | A7 (Trockenlauf) | `run_dry()` (Zeile 620) ruft `get_imap_password()` auf — Schlüsselbund-Zugriff trotz Vorgabe "kein Schlüsselbund-Zugriff". |
| `verdict_20261023_probe_k6_qwen36-35b_betrieb.md` | hoch | ja | A6 (Verifikation) | `block_marker` (Zeile 571) ist nur `## <Datum>`. Bei zwei Mails am selben Tag findet String-Suche den falschen Block → Verifikation positiv, obwohl falscher Eintrag geschrieben wurde. |
| `verdict_20261023_probe_k6_qwen36-35b_betrieb.md` | hoch | ja | A5 (LLM-JSON) | `json.loads(content)` (Zeile 470) scheitert an Markdown-Codeblöcken (````json ... ````). LLMs liefern das häufig. Kein Fallback. |
| `verdict_20261023_probe_k6_qwen36-35b_betrieb.md` | mittel | ja | A8 (Schlüsselbund) | `.decode().strip()` (Zeile 85) entfernt End-Leerzeichen des Passworts. Gültige Passwörter mit trailing space werden falsch. |
| `verdict_20261023_probe_k6_qwen36-35b_betrieb.md` | mittel | ja | A6 (Fehlerwiederholung) | Bei LLM-Fehler (B3) bleibt Mail offen, wird bei jedem Lauf wiederholt. Exit 1 + stderr. Ohne Log-Überwachung (launchd) unbemerkt. |
