# Spec: umsetzung_auto

- **Anforderung:** `docs/projekt_management/anforderung_20261027_umsetzung_auto.md`
- **Stand:** 27.10.2026, Commit `c7a81af`
- **Autor:** Qwen3.8-27B-GGUF:Q4_K_XL

## Ziel

Neuer Befehl `kette.py umsetzung-auto <kurztitel>` startet `opencode run --format json` mit Agent `umsetzung_nacht` und einem konfigurierbaren Modell vollständig unbeaufsichtigt. `kette.py` prüft Vorbedingungen (Exit 2), überwacht den Lauf (Exit 1 bei Timeout oder fehlendem `reason: stop`), wertet das JSON aus, führt mechanische Nachprüfungen aus (HEAD, Schreibbereich, Handover, `pruefen`) und beendet sich nur mit Exit 0, wenn alles grün ist. Optionaler `--nacharbeit <datei.md>` für gezielte Nachbesserungen.

## Nicht-Ziele

- Keine Änderung des bestehenden `prompt umsetzung`-Workflows (TUI bleibt bestehen).
- Keine Änderung des Agenten `umsetzung` (Handbetrieb).
- Keine Integration des Gedächtnis-Providers (`gedaechtnis`); der Lauf nutzt `llamacpp/` direkt am Router.
- Keine automatische Rücksetzung oder Korrektur von Verletzungen durch `kette.py`; die Liste wird ausgegeben, die Entscheidung liegt bei Hawe.
- Keine Änderung der globalen `~/.config/opencode/AGENTS.md`.
- Kein Parallel-Lauf zweier `umsetzung-auto` für denselben Kurztitel (nicht gefordert; falls es passiert, ist das Ergebnis unbestimmt).

## Schreibbereich

- `role-split/kette/kette.py`
- `role-split/kette/RUNBOOK.md`
- `docs/projekt_management/_vorlage_spec.md`
- `role-split/kette/prompts/umsetzung_nacht.md`
- `.opencode/agents/umsetzung_nacht.md`
- `tests/test_umsetzung_auto.py`
- `role-split/kette/testdata/`

## Einstiegspunkte

- Start im Betrieb: `python3 role-split/kette/kette.py umsetzung-auto <kurztitel> [--nacharbeit <datei.md>]` (Terminal, wie die anderen `kette.py`-Befehle).
- Modulaufruf: `kette.umsetzung_auto(kurztitel, nacharbeit=None, datums=None, commit=None)`.
- Test T20 prüft, dass `main(["umsetzung-auto", "g"])` mit Attrappe denselben Exit-Code liefert wie der direkte Funktionsaufruf `kette.umsetzung_auto("g")`.

## Außenwirkung und Sperre

| Schritt | Außenwirkung | Sperre / Zeitlimit |
|---|---|---|
| Vorab-Prüfung (Exit 2) | keine (nur `git log`, `opencode --version`, Dateilesen) | – |
| `opencode run` | Modell-Lauf am Router, Dateischreibzugriffe durch Agent | ganzer Lauf: `KETTE_UMSETZUNG_TIMEOUT` (Default 7200 s), Einzelbefehl: `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS` (Default 300000) |
| JSON-Auswertung | keine | – |
| Mechanische Prüfung (a)–(d) | `git rev-parse`, `git diff`, `git status`, `pruefen` (unittest, gegenprobe) | `pruefen` hat eigenes Timeout (Default 300 s) |
| Protokoll schreiben | `role-split/results/`, `docs/projekt_management/umsetzung_<datum>_<kurztitel>.md` | – |

## Quellen

- `role-split/kette/kette.py` Zeilen 437–445 – `spec_commit(kurztitel)`: findet den Commit „Spec <kurztitel>" (Rücksetzpunkt, A2.2, A7a)
- `role-split/kette/kette.py` Zeilen 487–512 – `pruefen(kurztitel)`: abgleich + unittest + gegenprobe, liefert Exit-Code und schreibt `pruefung_<datum>_<kurztitel>.md` (A7d)
- `role-split/kette/kette.py` Zeilen 525–526 – `_git(*a)`: git-Wrapper mit `git -C ROOT` (A2, A7)
- `role-split/kette/kette.py` Zeilen 78–81 – `ROOT`, `PM`, `PROMPTS`: Pfade (A1, A3, A6)
- `role-split/kette/kette.py` Zeilen 1194–1202 – `KETTE_HERZSCHLAG_S` (Default 60) und Umgebungsmuster für Env-Variablen (A5, A9)
- `role-split/kette/kette.py` Zeilen 1216–1229 – `_herzschlag_stopp_event`: Herzschlag-Thread als Muster (A9)
- `role-split/kette/kette.py` Zeilen 1326–1328 – `review_auto`: Kurztitel-Prüfung und Funktionsmuster für `umsetzung_auto` (A1, A2.1)
- `role-split/kette/kette.py` Zeilen 1463–1512 – `main`: argparse-Struktur, hier `umsetzung-auto`-Subparser ergänzen (Einstiegspunkte)
- `.opencode/agents/umsetzung_nacht.md` Zeilen 1–27 – bestehendes Frontmatter mit `bash: "*": deny` und Allow-Liste (A4)
- `role-split/kette/prompts/umsetzung.md` – Prompt-Vorlage für `umsetzung_nacht.md` (A3)
- `docs/projekt_management/_vorlage_spec.md` – Spec-Vorlage, um `## Schreibbereich` zu ergänzen (A11)
- `role-split/kette/RUNBOOK.md` Zeilen 111–123 – Phase B, um `umsetzung-auto` zu ergänzen (A11)
- `tests/test_kette_review_auto.py` Zeilen 78–150 – Testmuster: `sys.path.insert`, `setattr`/`addCleanup`, `kette.PM` → Tempdir (Testplan)
- `docs/projekt_management/anforderung_20261027_umsetzung_auto.md` – verbindliche Vorgabe, alle Anforderungen P1–P10

## Anforderungen

### A1: Befehl `umsetzung-auto`

- `kette.py umsetzung-auto <kurztitel>` startet `opencode run --format json --agent umsetzung_nacht --model <KETTE_UMSETZUNG_MODEL> <prompt>`:
  - `<prompt>` ist das **Positionsargument** `message` von `opencode run` (Spec-Paket §1), kein `--message`-Flag.
  - `--model <KETTE_UMSETZUNG_MODEL>` (Env-Var, Default `llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL`)
  - Das Subprozess-CWD ist `ROOT`; zusätzlich wird `--dir <ROOT>` übergeben, damit das Arbeitsverzeichnis auch dann stimmt, wenn `kette.py` von anderswo aufgerufen wird.
- Jeder Lauf ist eine **neue Sitzung**: kein `--continue`, kein `--session`, kein `--fork`.
- Der Aufruf läuft in einem Subprozess (`subprocess.Popen`), damit `kette.py` die stdout-JSON-Stream lesen, überwachen und bei Timeout beenden kann.
- `opencode` wird über `shutil.which("opencode")` oder `KETTE_OPENCODE` (Env-Var, für Tests) aufgelöst. Ist keiner der beiden vorhanden → Exit 2.

  **Pfad- vs. Pfad+Interpreter:** `KETTE_OPENCODE` ist ein **Pfad** (kein vollständiger Befehl). Wenn er auf `.py` endet, startet `kette.py` den Pfad mit `sys.executable` als Interpreter, da neu committete `.py`-Dateien nicht automatisch ausführbar sind. Beispiel: `KETTE_OPENCODE=/pfad/zu/opencode_fake.py` → Aufruf `[sys.executable, "/pfad/zu/opencode_fake.py", ...]`. Endet er nicht auf `.py`, wird er direkt als Programm aufgerufen.

### A2: Vorab-Prüfungen (Exit 2 ohne Lauf)

Vor dem Start von `opencode` prüft `kette.py` in dieser Reihenfolge; bei jedem Versagen: Meldung auf stderr, Exit 2, **kein Lauf**:

1. **Kurztitel gültig:** `re.fullmatch(r"[a-z0-9_]+", kurztitel)` (wie in `review_auto`, Zeile 1328).
2. **Commit „Spec <kurztitel>" existiert:** `spec_commit(kurztitel)` liefert nicht `None` (Zeilen 437–445).
3. **Spec hat Abschnitt `## Schreibbereich`:** Die Spec-Datei (`datei_suchen("spec", kurztitel, None)`) enthält die Zeile `## Schreibbereich`. Fehlt die Spec-Datei → Exit 2. Fehlt der Abschnitt → Hinweis auf stderr („Spec um ‚## Schreibbereich' ergänzen, sonst kein umsetzung-auto-Lauf"), Exit 2.
4. **Arbeitsstand:**
   - **Ohne `--nacharbeit`:** `git status --porcelain` muss leer sein (sauberer Arbeitsstand), egal ob ein Handover existiert oder nicht. Andernfalls Exit 2.
   - **Mit `--nacharbeit`:** Änderungen sind erlaubt, aber **nur**:
     - Dateien im Abschnitt `## Schreibbereich` der Spec.
     - `tests/test_<kurztitel>.py`.
     - Offene Kettendateien `docs/projekt_management/*_<kurztitel>*.md` mit Präfixen `pruefung_`, `umsetzung_`, `review_paket_`, `verdict_`, `gesamt_` oder `nacharbeit_` (Prüfungs-, Umsetzungs-, Paket-, Verdict-, Gesamt- und Nacharbeitsdateien der Kette).
     - Die Handover-Datei `handover_<datum>_<kurztitel>.md` (Datum s. A7c: das der Spec).
     - Die Nacharbeitsdatei selbst (`--nacharbeit <datei.md>`), falls sie im Repo liegt.

     **Strenge Unveränderlichkeitspflicht:** `spec_*.md`, `anforderung_*.md` und `quellen_*.md` müssen gegenüber `HEAD` unverändert sein. Jede offene Änderung an einer dieser Dateien → Exit 2. Jede andere offene Änderung (außerhalb der erlaubten Liste) → ebenfalls Exit 2.
5. **`opencode` installiert:** `shutil.which("opencode")` liefert einen Pfad, oder `KETTE_OPENCODE` ist gesetzt **und die Datei existiert**.
6. **Modell beginnt mit `llamacpp/`:** `KETTE_UMSETZUNG_MODEL` (Default s. A1) muss mit `llamacpp/` anfangen. Andernfalls Exit 2.

### A3: Prompt

Der Prompt für `umsetzung_nacht` ist der Text aus `prompts/umsetzung_nacht.md` (neue Datei) mit denselben Platzhaltern wie `umsetzung.md` (`{kurztitel}`, `{datum}`, `{commit}`, `{anforderung}`, `{quellen}`), **ohne** `pbcopy` und **ohne** Ausgabe auf stdout (der Prompt wird intern als String gebaut und als Positionsargument `message` an `opencode run` übergeben, s. A1).

Zusätzlich zum Inhalt von `umsetzung.md` enthält der Prompt:

- Verweis auf `docs/learnings/LERNREGELN.md`, Abschnitte „Umsetzung" und „Tests", als **Pflichtlektüre vor der ersten Änderung** (Anforderung P10).
- Bei `--nacharbeit <datei.md>`: Der Auftrag aus der Datei wird an den Prompt angehängt, und der Hinweis „Handover unter ‚## Nachbesserung n' ergänzen" wird ergänzt.

### A4: Agent `umsetzung_nacht` – zusätzliche deny-Regeln

Die Agent-Datei `.opencode/agents/umsetzung_nacht.md` wird um folgende `bash`-Regeln ergänzt (alle `deny`, explizit genannt, zusätzlich zum bestehenden `"*": deny`):

```yaml
    "git commit*": deny
    "git reset*": deny
    "git checkout*": deny
    "git restore*": deny
    "git clean*": deny
    "git stash*": deny
    "git push*": deny
    "rm*": deny
    "mv*": deny
```

Kein `ask` im Agenten: Alle Kategorien, die nicht explizit `allow` sind, bleiben `deny` (bestehend). Es gibt keine Kategorie `bash: "*": ask`.

**Vorrang-Satz:** Der Agent-Text (Body unter dem Frontmatter) von `.opencode/agents/umsetzung_nacht.md` enthält zusätzlich den Satz aus der Rückfrage-Antwort vom 2026-10-27 10:08: „Du hast Vorrang vor allgemeinen Kommunikationsregeln: Nicht vorab erklären oder auf Freigabe warten, sondern umsetzen und Begründungen ins Handover schreiben. Bezeichner wie in Spec und bestehendem Code (in diesem Repo deutsch)." Damit übersteuert der Agent die globale `~/.config/opencode/AGENTS.md`, die vorab Erklärungen verlangt. Der Satz steht primär im Agent; der Prompt (A3) muss ihn nicht wiederholen.

**Begründung für explizite deny-Nennung:** Das bestehende `"*": deny` verbietet bereits alle bash-Befehle. Die explizite Nennung ist redundant, aber die Anforderung verlangt sie ausdrücklich („verbietet zusätzlich ausdrücklich (deny)"). Sie dient als Dokumentation und schützt vor einem versehentlichen Wechsel von `"*": deny` zu `"*": ask`.

### A5: Zeitlimits

- **Ganzer Lauf:** `KETTE_UMSETZUNG_TIMEOUT` (Env-Var, Default 7200 Sekunden). `kette.py` misst die Wandtime vom Prozessstart bis zum Prozessende. Nach Ablauf sendet `kette.py` `SIGKILL` an den `opencode`-Prozess **und alle seine Kinder** (Prozessgruppe). Exit-Code: 1.
- **Einzelbefehl:** `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS` wird als Umgebungsvariable an den `opencode`-Prozess übergeben (Default 300000 ms = 300 s). Diese Variable wird von OpenCode selbst ausgewertet (gemessen in Probe P3, Spec-Paket §1).

**Umsetzung der Prozessbeendigung:** `kette.py` startet `opencode` mit `start_new_session=True` (eigene Prozessgruppe). Bei Timeout: `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)`. Fällt das auf (z. B. Prozess schon beendet), ist das kein Fehler.

### A6: JSON-Auswertung

`kette.py` liest die stdout-Zeilen von `opencode` (JSON, eine Zeile je Ereignis). Ausgewertet werden:

| Feld | Quelle | Zweck |
|---|---|---|
| Dauer | Zeitstempel erstes und letztes Ereignis, bzw. Wandtime des Subprozesses | Protokoll |
| Werkzeugaufrufe | `tool_use`-Ereignisse: `part.tool`, `part.state.input` (Wortlaut) | Protokoll, Lebendsignal |
| Fehlgeschlagene Befehle | `tool_use` mit `state.status == "error"` | Protokoll (Wortlaut) |
| Abgelehnte Befehle | `tool_use` mit `state.status == "error"` und Fehlermeldung enthält „rejected permission" oder „rule which prevents" | Protokoll (Wortlaut) |
| Tokens | `step_finish` → `part.tokens` (total, input, output, reasoning) | Protokoll |
| Letzter `reason` | Letztes `step_finish`-Ereignis: `part.reason` | Abschlussprüfung |
| Schlusstext | Letztes `text`-Ereignis: `part.text` | Protokoll |

**Abschlussprüfung:** Das letzte `step_finish` muss `reason: stop` haben. Andernfalls gilt der Lauf als **nicht abgeschlossen** → Exit 1.

**Rohdaten:** Der komplette JSON-Stream (alle Zeilen) wird nach `role-split/results/umsetzung_auto_<datum>_<kurztitel>_<uhrzeit>.jsonl` geschrieben.

**Protokollzeile:** Je Lauf wird eine Zeile in `docs/projekt_management/umsetzung_<datum>_<kurztitel>.md` angehängt (Datei wird bei Bedarf angelegt). Format:

```markdown
- **<datum> <uhrzeit>** – Modell: <modell>, Dauer: <sek> s, Tools: <n>, Fehler: <n>, Abgelehnt: <n>, Tokens: <total>, reason: <reason>, rot: <n|–>, pruefen: <code|–>, art: <erst|nb<n>>, Exit: <code>
```

`rot` und `pruefen` können `–` (unbekannt) sein, wenn der Lauf abgebrochen ist ((d) übersprungen, s. A7d).

`rot` wird wie folgt bestimmt:
- Zeile `OK` in der unittest-Ausgabe (in `pruefung_<datum>_<kurztitel>.md`): `rot = 0`.
- Zeile `FAILED (failures=x, errors=y)`: `rot = x + y`.
- Sonst (keine dieser Zeilen, z. B. kein Testskript): `rot = „–"` (unbekannt).

`pruefen`-Code = Rückgabewert des `pruefen`-Aufrufs (0 = grün, ≠ 0 = Verstoß). `art` = `erst` beim Ersten Lauf, `nb<n>` bei Nachbesserung mit Nummer `n`.

**Wichtig für A8 (Fortschrittsprüfung):** `rot = „–"` (unbekannt) zählt **nie** als Fortschritt – weder als gesunken noch als besser. Nur ein bekannter, gesunkener Wert oder ein bekannter, kleinerer `pruefen`-Code gilt als Fortschritt (s. A8).

### A7: Mechanische Prüfung nach dem Lauf

**Vor dem Lauf** (immer, auch bei späterem Timeout) nimmt `kette.py` einen Dateistand auf:
- `head_vor` = `git rev-parse HEAD`.
- `stand_vor` = dict `{relativer Pfad: Prüfsumme}` über alle Dateien aus `git status --porcelain --untracked-files=all` (bestehende geänderte, vorgemerkte und unversionierte Dateien, lesbar). Gelesene Prüfsumme: SHA-256 des Dateiinhalts. Nicht lesbare Dateien (z. B. verlinkt, leer) bekommen den Schlüsselwert `"<unlesbar>"`.
- **Warum nicht `_aenderungen`:** `_aenderungen` (kette.py Z. 543) filtert `PAKET_NIE = ("docs/", "experiments/")` aus – jede geänderte Datei unter `docs/` wäre unsichtbar, aber genau dort liegen Spec, Handover und Protokoll.
- **Trennung Vorab-Prüfung vs. Lauf:** `stand_vor`/`stand_nach` erfassen nur **offene und unversionierte** Dateien (git status). `kette.py` schreibt `pruefung_`, `umsetzung_`, Protokoll und Rohdaten **uncommittet**, aber erst **nach** `stand_nach` (siehe unten) – sie können den Vergleich daher nicht verfälschen. Kettendateien früherer Läufe (z. B. bei Nacharbeit) stehen unverändert in beiden Schnappschüssen und gelten nicht als „in diesem Lauf geändert". Die Vorab-Prüfung A2.4 (sauberer Arbeitsstand ohne `--nacharbeit`) bleibt davon unberührt (T4). *(Absatz präzisiert von Claude, 27.10.)*

  **Wichtig:** `stand_nach` wird **SOFORT nach Ende des `opencode`-Laufs** aufgenommen, **bevor** `kette.py` selbst Dateien schreibt (Prüfungs-, Protokoll-, Rohdaten-Datei). Alle Dateien, die `kette.py` **nach** `stand_nach` selbst anlegt (Prüfung, Protokoll, Rohdaten), gehören **nicht** zum Vergleich in (b). Nur der Zustand **beim Laufende** (also vor dem Schreiben durch `kette.py`) wird mit `stand_vor` verglichen.

**Nach dem Lauf** (vor Exit-Code-Bestimmung) führt `kette.py` vier Prüfungen durch:

**(a) HEAD unverändert (Selbst-Commit) – IMMER:**
- `head_nach` = `git rev-parse HEAD`.
- `head_vor != head_nach` → Meldung „Selbst-Commit" (mit beiden Hashes), Exit 1.
- Läuft auch nach Timeout und ohne `reason: stop`.

**(b) Schreibbereich – IMMER:**
- `stand_nach` wird wie `stand_vor` aufgenommen.
- „In diesem Lauf geändert" = jede Datei, die in `stand_vor` oder `stand_nach` vorkommt und für die gilt: neu (nur in `stand_nach`), weg (nur in `stand_vor`) oder andere Prüfsumme.
- Erlaubt sind:
  - Dateien, die im Abschnitt `## Schreibbereich` der Spec aufgeführt sind (Pfad exakt oder als Präfix eines Ordner-Eintrags).
  - `tests/test_<kurztitel>.py`
  - Die Handover-Datei `handover_<datum>_<kurztitel>.md` (Datum = das der Spec, s. A3: `{datum}` im Prompt)
- **Nie erlaubt:** Spec-Dateien (`spec_*.md`), Anforderungsdateien (`anforderung_*.md`), Quellen (`quellen_*.md`), Vorlagen (`_vorlage_*.md`).
- Bei Verstoß: Liste der verbotenen Dateien (mit Änderungsart: neu/weg/geändert) auf stdout, Exit 1. **Nichts wird zurückgesetzt.**

**Parsing des Schreibbereichs:** Die Zeilen unter `## Schreibbereich` bis zur nächsten `##`-Überschrift werden gelesen. Jeder `-`-Eintrag ist ein Pfad relativ zum ROOT (Datei exakt oder Ordner mit `/` am Ende). Eine Datei ist im Schreibbereich, wenn sie exakt mit einem Eintrag übereinstimmt oder mit einem Ordner-Eintrag beginnt.

**(c) Handover geschrieben – nur bei abgeschlossenem Lauf:**
- Die Handover-Datei `handover_<datum>_<kurztitel>.md` (Datum = das der Spec, s. A3: `{datum}` im Prompt) gilt als geschrieben, wenn ihre Prüfsumme in `stand_nach` gegenüber `stand_vor` sich geändert hat (neu oder andere Prüfsumme) – dasselbe Verfahren wie (b), keine `git status`-/mtime-Prüfung.
- Fehlt die Datei oder ist sie unverändert → Exit 1.
- Bei nicht abgeschlossenem Lauf (Timeout, kein `reason: stop`): wird **übersprungen** und als „(c) übersprungen (Lauf nicht abgeschlossen)" gemeldet.

**(d) `pruefen` – nur bei abgeschlossenem Lauf:**
- `pruefen(kurztitel)` wird aufgerufen (Zeilen 487–512). Exit-Code 0 = grün, ≠ 0 = Verstoß (Exit 1).
- Bei nicht abgeschlossenem Lauf: wird **übersprungen** und als „(d) übersprungen (Lauf nicht abgeschlossen)" gemeldet.

### A8: Nacharbeit

- `kette.py umsetzung-auto <kurztitel> --nacharbeit <datei.md>`:
  - `<datei.md>` ist eine Datei mit dem Auftrag (freier Text). Sie wird an den Prompt angehängt.
  - Die Vorab-Prüfung (A2, Punkt 4) erlaubt offene Änderungen, **aber nur**: im Schreibbereich, in `tests/test_<kurztitel>.py`, in offenen Kettendateien (`pruefung_`, `umsetzung_`, `review_paket_`, `verdict_`, `gesamt_`, `nacharbeit_`), in der Handover oder in der Nacharbeitsdatei selbst. `spec_*.md`, `anforderung_*.md` und `quellen_*.md` müssen gegenüber `HEAD` unverändert sein (s. A2.4).
  - Die Handover wird unter einem neuen Abschnitt `## Nachbesserung n` ergänzt, wobei `n` die Anzahl der bestehenden `## Nachbesserung`-Abschnitte + 1 ist.
  - Die mechanische Prüfung (A7) gilt wie beim Ersten Lauf.
- **Fortschrittsprüfung (Anforderung P7):**
  - Vor dem Nacharbeit-Lauf liest `kette.py` die **zuletzt geschriebenen `nb`-Zeilen** aus der Protokoll-Datei `umsetzung_<datum>_<kurztitel>.md` (Format s. A6) und nimmt deren `rot`- und `pruefen`-Werte.
  - Nach dem Lauf: Neuer Zustand wird aus der neuen Protokollzeile ermittelt.
  - „Fortschritt" heißt: **rot ist bekannt und gesunken** ODER **`pruefen`-Exit-Code ist bekannt und kleiner (besser)** als im Vorlauf – **und** keiner der beiden Werte ist dabei schlechter geworden (`rot` nicht größer, `pruefen` nicht größer). *(präzisiert von Claude, 27.10.)* `rot = „–"` (unbekannt) zählt **nie** als Fortschritt. Bricht ein `nb`-Lauf ab ((d) übersprungen, s. A7d), lautet seine Protokollzeile `rot: –, pruefen: –` → **kein Fortschritt** (s. A6).
  - **Halt-Regel:** Gibt es in der Protokoll-Datei bereits zwei aufeinanderfolgende `nb`-Zeilen (zuletzt geschriebene `nb`-Zeilen), die beide keinen Fortschritt zeigen, und würde ein weiterer Nacharbeit-Lauf gestartet, wird er **nicht** gestartet: Meldung „Übergabe an Hawe", Exit 1. Es gibt **keinen separaten Zähler** – die Regel wird direkt aus den letzten zwei `nb`-Zeilen berechnet.
  - Nach einer `nb`-Zeile mit Fortschritt sind frühere `nb`-Zeilen ohne Fortschritt wieder erlaubt (die beiden letzten `nb`-Zeilen zählen jeweils für sich).

### A9: Lebendsignal während des Laufs

- **Je Werkzeugaufruf:** Wenn ein `tool_use`-Ereignis mit `state.status == "completed"` oder `"error"` eintrifft, gibt `kette.py` eine kurze Zeile auf stdout: `[<uhrzeit>] <tool>: <kurz>…` (Werkzeugname + erste 60 Zeichen des Wortlauts, abgeschnitten).
- **Lebenszeichen:** Alle 60 Sekunden (konfigurierbar über `KETTE_HERZSCHLAG_S`, bestehende Konstante, Default 60) gibt `kette.py` eine Zeile aus: `[<uhrzeit>] Lebenszeichen, Lauf läuft seit <min> min`.
- Die Herzschlag-Logik folgt dem bestehenden Muster `_herzschlag_stopp_event` (Zeilen 1216–1229), wird aber als Thread gestartet, der auf einen `threading.Event` wartet, das bei Prozessende gesetzt wird.

### A10: Exit-Codes

| Exit | Bedingung |
|---|---|
| 0 | Lauf abgeschlossen (`reason: stop`), keine Verletzung in (a)–(d), `pruefen` = 0 |
| 1 | Timeout, kein `reason: stop`, Verletzung in (a)–(d), `pruefen` ≠ 0, Nacharbeit ohne Fortschritt (Übergabe an Hawe) |
| 2 | Kurztitel ungültig, Vorab-Prüfung fehlgeschlagen (A2), `opencode` nicht gefunden, Modell nicht `llamacpp/` |

### A11: Ergänzungen

- **RUNBOOK Phase B** (`role-split/kette/RUNBOOK.md`, ab Zeile 111): Abschnitt `umsetzung-auto` ergänzen: Aufruf, Vorbedingungen, Exit-Codes, Nacharbeit.
- **Spec-Vorlage** (`docs/projekt_management/_vorlage_spec.md`): Abschnitt `## Schreibbereich` ergänzen (leer, mit Platzhalter-Kommentar: `<!-- Dateien/Ordner, die die Umsetzung ändern darf, z. B. role-split/kette/ oder einzelne Pfade -->`).
- **Prompt-Vorlage** `role-split/kette/prompts/umsetzung_nacht.md`: neue Datei (Inhalt s. A3).
- **Attrappe** `role-split/kette/testdata/opencode_fake.py`: Python-Skript, wird committet (Testplan, T20).

## Fehlerpfade

| Anforderung | Fehlerfall | Was wurde vor dem Fehler schon gemacht? | Was geht verloren / bleibt liegen? | Exit-Code | Sieht ein Überwacher den Fehler? |
|---|---|---|---|---|---|
| A2: Spec fehlt oder kein `## Schreibbereich` | Spec-Datei existiert nicht, oder Abschnitt fehlt | Nur `git log` und Dateilesen, keine Änderungen | nichts | 2 | Ja: Meldung auf stderr, Exit 2 |
| A2: Arbeitsstand nicht sauber (erster Lauf) | `git status --porcelain` nicht leer | keine Änderungen | nichts | 2 | Ja: Meldung + Liste der offenen Dateien auf stderr |
| A2: Nacharbeit mit fremden Änderungen | Offene Dateien außerhalb Schreibbereich | keine Änderungen | nichts | 2 | Ja: Meldung + Liste |
| A5: Timeout (7200 s) | `opencode` hängt oder läuft zu lange | Prüfsummen-`stand_vor` und `head_vor` aufgenommen, JSON-Stream bis dahin gelesen | Laufabbruch; Rohdaten-Datei wird **nach** dem Kill geschrieben; (a)/(b) laufen trotzdem, (c)/(d) „übersprungen" | 1 | Ja: Meldung „Timeout nach 7200 s", Protokollzeile mit `reason: timeout` |
| A5: Einzelbefehl läuft zu lange (300 s) | OpenCode killt den Bash-Befehl selbst (Probe P3) | Werkzeugergebnis enthält Timeout-Meldung | kein Datenverlust; Modell meldet es im Text | 0 (wenn `reason: stop` folgt) oder 1 | Ja: Fehlermeldung im JSON-Stream, Protokoll |
| A6: Kein `reason: stop` | Lauf endet mit `reason: tool-calls` (Probe P1) oder bricht ab | JSON-Stream gelesen, Rohdaten geschrieben | kein Datenverlust; Handover evtl. unvollständig | 1 | Ja: Meldung „Nicht abgeschlossen (reason: …)" |
| A6: JSON-Stream leer oder kaputt | `opencode` startet nicht, gibt nichts aus, oder nicht-JSON-Zeilen | keine Änderungen | kein Datenverlust; Rohdaten-Datei (evtl. leer) | 1 | Ja: Meldung „Keine gültigen JSON-Ereignisse" |
| A7a: Selbst-Commit | `opencode` committet trotz deny | HEAD vor/nach Lauf abweichend | nichts (Commit bleibt, `kette.py` setzt nichts zurück) | 1 | Ja: Meldung „Selbst-Commit" + Commit-Hash |
| A7b: Datei außerhalb Schreibbereich | Agent ändert eine Datei, die nicht im Schreibbereich steht | Datei ist geändert (uncommittet) | nichts (Datei bleibt, wird nicht zurückgesetzt) | 1 | Ja: Liste der Verletzter Dateien |
| A7c: Handover fehlt | Agent schreibt kein Handover | keine Änderungen an Handover | nichts | 1 | Ja: Meldung „Handover fehlt" |
| A7d: `pruefen` rot | Unit-Tests rot, abgleich oder gegenprobe fehlerhaft | `pruefen`-Datei geschrieben | nichts | 1 | Ja: `pruefen`-Meldung + Protokoll |
| A8: Zwei Nachbesserungen ohne Fortschritt | Rote Tests nicht gesunken, `pruefen` nicht besser, oder `rot = „–"` (unbekannt) | Protokollzeilen der zwei `nb`-Läufe liegen vor | nichts | 1 | Ja: Meldung „Übergabe an Hawe" |
| A9: Herzschlag-Thread hängt | Thread blockiert sich | keine Auswirkungen auf Hauptprozess | nichts | unverändert | Nein (aber irrelevant, Thread ist Daemon) |

## Testplan

Tests in `tests/test_umsetzung_auto.py` (neue Datei). Muster wie `tests/test_kette_review_auto.py`: `sys.path.insert`, `import kette`, Abhängigkeiten per `setattr`/`addCleanup` ersetzen, `kette.PM` → `tempfile.TemporaryDirectory()`, `redirect_stdout`.

**Attrappe für `opencode`:** Ein Python-Skript `role-split/kette/testdata/opencode_fake.py`, das **committet** wird:
- Die Argumente liest (Positionsargument = Prompt, Flags ignoriert) und auf stdout ein vordefiniertes JSON-Ereignis-Set ausgibt (eine Zeile je Ereignis, Format s. A6).
- Der Test setzt über `KETTE_OPENCODE` den Pfad auf `role-split/kette/testdata/opencode_fake.py` (ohne `python3` – `kette.py` erkennt die `.py`-Endung und ruft sie mit `sys.executable` auf, s. A1).
- Verhalten über Umgebungsvariablen steuern: `FAKE_REASON` (z. B. `stop` oder `tool-calls`), `FAKE_SLEEP` (Sekunden, für Timeout-Test), `FAKE_COMMIT` (setzt `git commit` im Repo, um Selbst-Commit zu testen), `FAKE_EDIT` (Pfad einer Datei, die die Attrappe ändert, um Schreibbereich zu testen), `FAKE_HANDOVER` (schreibt eine Handover-Datei), `FAKE_UNittest` (unittest-Ausgabe mit `FAILED (failures=x, errors=y)` für den `rot`-Wert).

### T1: Vorab-Prüfung – Kurztitel ungültig

- **Vorbereitung:** Kein Repo nötig.
- **Aktion:** `kette.umsetzung_auto("Ungültig-Titel")`.
- **Erwartung:** Exit 2, Meldung enthält „ungültig".

### T2: Vorab-Prüfung – kein Spec-Commit

- **Vorbereitung:** Temp-Repo mit `git init`, ein Commit „foo" (kein „Spec g"). `kette.ROOT`/`kette.PM` umgebogen.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 2, Meldung enthält „Spec".

### T3: Vorab-Prüfung – Spec ohne `## Schreibbereich`

- **Vorbereitung:** Temp-Repo, Commit „Spec g", Spec-Datei ohne `## Schreibbereich`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 2, Meldung enthält „Schreibbereich".

### T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)

- **Vorbereitung:** Temp-Repo, Commit „Spec g", Spec mit `## Schreibbereich`, eine Datei uncommitted geändert, keine Handover.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 2, Meldung enthält „Arbeitsstand".

### T5: Vorab-Prüfung – `opencode` fehlt

- **Vorbereitung:** Alle anderen Vorbedingungen erfüllt. `KETTE_OPENCODE` nicht gesetzt, `shutil.which("opencode")` → `None` (im Test per `mock.patch` oder `PATH`-Manipulation).
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 2, Meldung enthält „opencode".

### T6: Vorab-Prüfung – Modell kein `llamacpp/`

- **Vorbereitung:** Alle anderen Vorbedingungen erfüllt. `KETTE_UMSETZUNG_MODEL` = `gedaechtnis/test-model`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 2, Meldung enthält „llamacpp".

### T7: Erfolgreicher Lauf, `reason: stop`, alle Prüfungen grün

- **Vorbereitung:** Temp-Repo, Commit „Spec g", Spec mit `## Schreibbereich` (enthält `role-split/kette/` und `handover`), sauberes Repo. Attrappe: `FAKE_REASON=stop`, `FAKE_EDIT` = Datei im Schreibbereich, `FAKE_HANDOVER=1`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 0. Protokollzeile in `umsetzung_<datum>_g.md`. Rohdaten-Datei in `role-split/results/`. `pruefen`-Ergebnis = 0.

### T8: Lauf ohne `reason: stop`

- **Vorbereitung:** Wie T7, aber `FAKE_REASON=tool-calls`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 1, Meldung enthält „nicht abgeschlossen" oder „reason".

### T9: Timeout

- **Vorbereitung:** Wie T7, aber `FAKE_SLEEP=5`, `KETTE_UMSETZUNG_TIMEOUT=1`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 1, Meldung enthält „Timeout". Prozess wird beendet.

### T10: Selbst-Commit

- **Vorbereitung:** Wie T7, aber `FAKE_COMMIT=1` (Attrappe macht `git commit`).
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 1, Meldung enthält „Selbst-Commit".

### T11: Datei außerhalb Schreibbereich

- **Vorbereitung:** Wie T7, aber `FAKE_EDIT` = Datei **außerhalb** des Schreibbereichs.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 1, Meldung enthält den Pfad der verbotenen Datei.

### T12: Handover fehlt

- **Vorbereitung:** Wie T7, aber `FAKE_HANDOVER=0` (Attrappe schreibt kein Handover).
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 1, Meldung enthält „Handover".

### T13: Nacharbeit – Auftrag aus Datei

- **Vorbereitung:** Wie T7, aber `--nacharbeit <datei.md>` mit Text. Handover existiert bereits.
- **Aktion:** `kette.umsetzung_auto("g", nacharbeit=datei)`.
- **Erwartung:** Exit 0. Prompt enthält den Auftragstext. Handover hat neuen Abschnitt `## Nachbesserung 1`.

### T14: Nacharbeit – zwei ohne Fortschritt

- **Vorbereitung:** Protokoll-Datei `umsetzung_<datum>_g.md` mit zwei aufeinanderfolgenden `nb`-Zeilen, die beide keinen Fortschritt zeigen (gleiche `rot`, gleicher `pruefen`-Code wie im jeweiligen Vorlauf). `pruefen`-Ergebnis gleich (kein Fortschritt).
- **Aktion:** `kette.umsetzung_auto("g", nacharbeit=datei)`.
- **Erwartung:** Exit 1, Meldung enthält „Übergabe an Hawe". Kein neuer Lauf.

### T15: Lebendsignal – Werkzeugzeile

- **Vorbereitung:** Wie T7. Attrappe erzeugt ein `tool_use`-Ereignis mit `status: completed`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** stdout enthält eine Zeile mit dem Werkzeugnamen und dem Wortlaut (gekürzt).

### T16: `pruefen` rot

- **Vorbereitung:** Wie T7, aber `kette.pruefen` per `setattr` auf Lambda mit Return 1.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 1.

### T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen

- **Vorbereitung:** Temp-Repo, Commit „Spec g", Spec mit `## Schreibbereich`, Handover existiert, eine Datei **außerhalb** Schreibbereich uncommitted geändert.
- **Aktion:** `kette.umsetzung_auto("g", nacharbeit=datei)`.
- **Erwartung:** Exit 2, Meldung enthält die fremde Datei.

### T18: Schreibbereich – Ordner-Eintrag

- **Vorbereitung:** Spec-Schreibbereich: `role-split/kette/`. Attrappe ändert `role-split/kette/kette.py`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 0 (Datei liegt im Schreibbereich).

### T19: Schreibbereich – Verbotene Dateien

- **Vorbereitung:** Spec-Schreibbereich: `role-split/kette/`. Attrappe ändert `docs/projekt_management/spec_20261027_g.md`.
- **Aktion:** `kette.umsetzung_auto("g")`.
- **Erwartung:** Exit 1, Meldung enthält den Pfad der Spec-Datei.

### T20: main() – gleicher Exit wie Funktionsaufruf

- **Vorbereitung:** Wie T7 (Attrappe, sauberes Repo, alle Vorbedingungen erfüllt).
- **Aktion:** `kette.main(["umsetzung-auto", "g"])`.
- **Erwartung:** Exit-Code identisch mit dem von `kette.umsetzung_auto("g")` (0). Damit ist belegt, dass der argparse-Pfad denselben Code durchläuft.

### T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)

- **Vorbereitung:** Temp-Repo, Commit „Spec g", Spec mit `## Schreibbereich`, Handover existiert, eine offene Kettendatei `pruefung_<datum>_g.md` (oder `verdict_<datum>_g.md`) uncommitted geändert. Alle anderen Voraussetzungen wie T17.
- **Aktion:** `kette.umsetzung_auto("g", nacharbeit=datei)`.
- **Erwartung:** **Kein Exit 2.** Der Lauf startet (weitere Exit-Codes gemäß Laufergebnis, s. A7/A8). Die offene Kettendatei ist nach A2.4 erlaubt.

## Offene Fragen

1. **Schreibbereich in bestehenden Specs:** Bestehende Specs (z. B. K9) haben keinen `## Schreibbereich`-Abschnitt. Die Vorab-Prüfung (A2, Punkt 3) bricht bei ihnen mit Exit 2 ab. **Entscheidung Hawe:** `kette.py` gibt einen Hinweis aus, dass die Spec um `## Schreibbereich` ergänzt werden muss, und bricht mit Exit 2 ab.

## Abweichende Meinung

Keine. Die Anforderung ist konsistent und die Umsetzung ist klar.
