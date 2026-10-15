# Spec: E-Mail-Versand für LLM Scout

**Ziel:**
Der LLM Scout-Bericht wird automatisch als HTML-E-Mail an `askvalentinai@gmail.com` versendet, sobald er erfolgreich generiert wurde.

**Nicht-Ziele:**
- Kein Versand an andere Empfänger.
- Keine Anpassung des Scout-Agents (`llm_scout.py`).
- Kein Tracking oder Zustellungsbestätigung.

---

## Anforderungen

### 1. Skript: `scripts/send_scout_email.py`

- Liest die `.md`-Datei der **aktuellen Kalenderwoche** aus `agents/llm_scout/data/weekly-reports/`.
  - Dateiname-Muster: `llm_scout_kw{KW}_{Jahr}.md` (z.B. `llm_scout_kw42_2026.md`).
  - `KW` und `Jahr` werden zur Laufzeit über `datetime.now().isocalendar()` bestimmt.
- **Prüfung:** Falls die Datei für die aktuelle KW nicht existiert, beendet sich das Skript mit Exit-Code 0 (kein Fehler, nur kein Versand).
- Konvertiert Markdown zu HTML (Bibliothek: `markdown`).
- Versendet die HTML-Inhalte per SMTP an Gmail (`smtp.gmail.com:587`, STARTTLS).
- **Betreff:** `LLM Scout KW{KW} {Jahr}`.
- **Absender:** `askvalentinai@gmail.com`.
- **Empfänger:** `askvalentinai@gmail.com`.
- **Credentials:** Das App-Passwort wird aus dem macOS-Schlüsselbund gelesen:
  - Schlüsselbund-Eintrag: `-s lab-scout-smtp`
  - Lesebefehl: `security find-generic-password -s lab-scout-smtp -w`
  - Das Passwort wird **nicht** in der PLIST oder im Code abgelegt.
- Exit-Code 0 bei Erfolg oder "keine Datei", 1 bei Fehler (mit Fehlermeldung in stderr).

### 2. Launchd-PLIST: `config/launchd/llm_scout.plist` (Bestandteil ändern)

- Die bestehende PLIST wird angepasst:
  - `ProgramArguments` ruft ein kleines Wrapper-Skript auf, das beide Schritte nacheinander ausführt:
    ```
    python3 agents/llm_scout/llm_scout.py && python3 scripts/send_scout_email.py
    ```
  - Alternativ: Zwei separate `ProgramArguments`-Aufrufe sind in launchd nicht direkt möglich. Daher wird ein Shell-Wrapper verwendet oder die PLIST bleibt beim Python-Aufruf, aber das Python-Skript ruft das zweite Skript auf.
  - **Entscheidung:** Es wird ein Shell-Skript `scripts/run_scout_pipeline.sh` erstellt, das:
    1. `python3 agents/llm_scout/llm_scout.py` aufruft.
    2. Nur bei Exit-Code 0: `python3 scripts/send_scout_email.py` aufruft.
  - Die PLIST zeigt dann auf `scripts/run_scout_pipeline.sh`.

- **PLIST-Inhalt (angepasst):**
  - Label: `de.hawe.lab.llm_scout` (bleibt gleich).
  - ProgramArguments: `bash /Users/hans-wernereberhardt/PycharmProjects/llama-server/scripts/run_scout_pipeline.sh`
  - StartCalendarInterval: Montag, 8:00 Uhr (bleibt gleich).
  - EnvironmentVariables: `LAB_DIR` bleibt. `GMAIL_*` entfallen.
  - StandardOut/StdErr: Bleiben in `logs/llm_scout_{out,err}.log`.

### 3. Shell-Wrapper: `scripts/run_scout_pipeline.sh`

- Ruft `llm_scout.py` auf.
- Prüft Exit-Code.
- Bei 0: Ruft `send_scout_email.py` auf.
- Bei != 0: Beendet sich mit dem Exit-Code des Scouts (kein Versand).
- Selbst mit `bash -n` geprüft und `chmod +x`.

### 4. Abhängigkeiten

- `pip install markdown` im `.venv` des Lab-Repos.
- Das Paket `markdown` wandelt Markdown in HTML um.

### 5. Credentials (Einmalige Einrichtung)

- Das Gmail-App-Passwort wird im macOS-Schlüsselbund abgelegt:
  ```bash
  security add-generic-password -a askvalentinai@gmail.com -s lab-scout-smtp -w <APP_PASSWORD>
  ```
- Ein eigenes App-Passwort mit dem Namen "lab-scout" anlegen, isoliert von anderen Gmail-Nutzungen.

---

## Test

1. **Manueller Test:**
   - `pip install markdown` im `.venv`.
   - App-Passwort im Schlüsselbund ablegen.
   - `python3 scripts/send_scout_email.py` manuell ausführen (vorausgesetzt, es gibt eine aktuelle KW-Datei).
   - Prüfung, ob die E-Mail bei `askvalentinai@gmail.com` ankommt.
   - Prüfung des HTML-Renderings im E-Mail-Client.

2. **Pipeline-Test:**
   - `bash scripts/run_scout_pipeline.sh` manuell ausführen.
   - Prüfung, ob beide Skripte nacheinander laufen.
   - Prüfung, ob bei Scout-Fehler (z.B. llama-server aus) kein Versand stattfindet.

3. **Launchd-Test:**
   - PLIST neu laden: `launchctl load config/launchd/llm_scout.plist`.
   - Nächster Montag um 8:00 warten oder via `launchctl kickstart` manuell auslösen.

---

## Offene Fragen

- Keine.

---

## Abweichende Meinung (Review-Instanz)

- **Ursprünglicher Vorschlag:** Credentials in PLIST-EnvironmentVariables. **Korrektur:** Schlüsselbund ist sicherer, da keine Datei im Klartext liegt.
- **Ursprünglicher Vorschlag:** Separater Launchd-Job um 8:15. **Korrektur:** Sequenzieller Aufruf via `&&` ist robuster, da keine Zeitkopplung nötig ist und der Versand nur bei erfolgreichem Scout läuft.
- **All-Inkl-Bewertung:** Die Aussage "AllInkl hat oft komplexere SMTP-Einstellungen" war unbelegt. Gmail wurde aus anderen Gründen gewählt (App-Passwort-Isolation, Stabilität).
