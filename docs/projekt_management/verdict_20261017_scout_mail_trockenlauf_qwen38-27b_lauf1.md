<!-- Wiederhergestellt von Claude am 17.10. aus der Lesung um 11:13: Lauf 1 (11:08) wurde von Lauf 2 unter
     demselben Dateinamen überschrieben. Rekonstruktion: Kopf, Ergebnis und Anforderungsurteile sinngemäß, Befundtabelle gekürzt —
     NICHT wortgleich mit dem Original. Original ist verloren (war nie committet). -->
# Verdikt: scout_mail_trockenlauf

- **Spec:** `spec_20261017_scout_mail_trockenlauf.md`
- **Handover:** `handover_20261017_scout_mail_trockenlauf.md`
- **Datum:** 2026-10-17
- **Modell:** unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
- **Geprüfte Dateien:** `scripts/send_scout_email.py` (voll), `scripts/run_scout_pipeline.sh` (voll), `agents/llm_scout/llm_scout.py` (voll), `.gitignore`, `config/launchd/llm_scout.plist`; dazu `git diff` gegen Rücksetzpunkt `f03a455`

## Ergebnis

**NACHBESSERN** – Der Funktionsumfang (alle Modi, Rekursions-Schutz, Original-Exit-Code, gitignore) ist umgesetzt und die Testausgaben im Handover stimmen mit dem Code überein. Aber das zentrale Sicherheitsversprechen der Spec ist gebrochen: Der Trockenlauf kann den macOS-Schlüsselbund aufrufen, wenn die `SCOUT_SMTP_PORT`-Umgebungsvariable gesetzt, aber leer oder nicht numerisch ist.

## Befunde (Kurzfassung der Originaltabelle)

| # | Schwere | Datei:Zeile | Befund |
|---|---|---|---|
| 1 | hoch | `scripts/send_scout_email.py:39-40` | `int(os.getenv("SCOUT_SMTP_PORT"))` beim Import: leere/nicht numerische Variable → ValueError auch im `--dry-run`; behauptet zusätzlich, der dry-run-Pfad könne über `send_email_smtp` → `get_password` den Schlüsselbund erreichen. |
| 2 | mittel | `scripts/send_scout_email.py:259-275` | Zwei `--fail-mail`-Ausfälle in derselben Minute überschreiben `scout_error_{JJJJMMDD}_{HHMM}.eml`. |
| 3 | niedrig | `scripts/send_scout_email.py:259-261` | Fallback-Dateiname nutzt die Zeit nach dem gescheiterten SMTP-Versuch, nicht den Fehlerzeitpunkt. |
| 4 | niedrig | `scripts/run_scout_pipeline.sh:36` | `${SCOUT_EXIT}` ungequotet. |

Anforderungen: A1 und A7 „teilweise erfüllt" (wegen Befund 1), A2–A6, A8 erfüllt. „Abweichungen: Keine" im Handover bestritten.
Nicht geprüft: T7 mit echtem launchd-Log, T8. Abweichende Meinung: Befund 1 hätte das Handover stoppen müssen.
