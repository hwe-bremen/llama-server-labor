# Review-Paket: umsetzung_auto


Erzeugt 2026-10-27 14:38 von `kette.py paket`. Ruecksetzpunkt: `3700da7`. Geaenderte Code-Dateien: `.opencode/agents/umsetzung_nacht.md`, `role-split/kette/RUNBOOK.md`, `role-split/kette/kette.py`, `role-split/kette/prompts/umsetzung_nacht.md`, `role-split/kette/testdata/opencode_fake.py`, `tests/test_umsetzung_auto.py`.
Alles Noetige steht hier. Ganze Dateien nur lesen, wenn eine Frage anders nicht zu klaeren ist – dann gezielt (search_files, Zeilenbereich), nicht komplett.


## 1. Anforderung (verbindlich, woertlich)

# Anforderung: umsetzung_auto

Verbindliche Vorgabe von Hawe, woertlich. Spec, Umsetzung und Review werden an diesem Text gemessen;
die Spec ist ein Loesungsvorschlag und kann falsch sein. Nur Hawe aendert diese Datei.

## Aufgabe

> Die Umsetzung soll ohne TUI laufen, damit ich nicht mehr Prompts kopieren und Befehle freigeben muss.
> 1. Neuer Befehl `kette.py umsetzung-auto <kurztitel>`: startet `opencode run --format json` mit Agent `umsetzung_nacht` und Modell aus `KETTE_UMSETZUNG_MODEL` (Vorgabe `llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL`). Prompt wie `prompt umsetzung`, aber ohne Ausgabe/Zwischenablage. Jeder Lauf ist eine neue Sitzung (kein `--continue`).
> 2. Vor dem Start prüfen, sonst Exit 2 ohne Lauf: Commit „Spec <kurztitel>" existiert; die Spec hat einen Abschnitt `## Schreibbereich` (Dateien/Ordner, die die Umsetzung ändern darf); Arbeitsstand sauber (erster Lauf) bzw. nur Änderungen im Schreibbereich (Nacharbeit); `opencode` ist installiert; das Modell beginnt mit `llamacpp/`.
> 3. `umsetzung_nacht` verbietet zusätzlich ausdrücklich (deny): `git commit`, `reset`, `checkout`, `restore`, `clean`, `stash`, `push`, `rm`, `mv`. Kein `ask` im Agenten.
> 4. Zeitlimits: ganzer Lauf `KETTE_UMSETZUNG_TIMEOUT` (Vorgabe 7200 s), danach OpenCode samt Unterprozessen beenden, Exit 1; Einzelbefehl über `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS` (Vorgabe 300000).
> 5. Ausgewertet wird nur das JSON, nie der Exit-Code von OpenCode: Dauer, Werkzeugaufrufe, fehlgeschlagene und abgelehnte Befehle (mit Wortlaut), Tokens, letzter `reason`, Schlusstext. Ohne `reason: stop` am Ende gilt der Lauf als „nicht abgeschlossen" (Exit 1). Rohdaten nach `role-split/results/`, je Lauf eine Protokollzeile in `docs/projekt_management/umsetzung_<datum>_<kurztitel>.md`.
> 6. Danach mechanisch: (a) HEAD unverändert, sonst lauter Fehler „Selbst-Commit"; (b) jede in diesem Lauf geänderte oder neue Datei liegt im Schreibbereich, ist `tests/test_<kurztitel>.py` oder der Handover der Kette – Spec, Anforderung, Quellen und Vorlagen nie; bei Verstoß Liste, Exit 1, nichts zurücksetzen (entscheide ich); (c) Handover wurde in diesem Lauf geschrieben oder ergänzt; (d) `pruefen`.
> 7. Nacharbeit: `kette.py umsetzung-auto <kurztitel> --nacharbeit <datei.md>` – Auftrag aus der Datei, Handover wird unter „## Nachbesserung n" ergänzt. Zwei Nachbesserungen in Folge ohne Fortschritt (rote Tests nicht weniger, `pruefen` nicht besser) ⇒ keine weitere starten, Exit 1, „Übergabe an Hawe".
> 8. Während des Laufs: je Werkzeugaufruf eine kurze Zeile, dazu jede Minute ein Lebenszeichen.
> 9. Exit 0 nur, wenn der Lauf abgeschlossen ist, kein Verstoß vorliegt und `pruefen` 0 meldet. RUNBOOK Phase B und die Spec-Vorlage (`## Schreibbereich`) werden ergänzt.
> 10. Der Prompt von `umsetzung-auto` verweist auf `docs/learnings/LERNREGELN.md`, Abschnitte „Umsetzung" und „Tests", als Pflichtlektüre vor der ersten Änderung.
> Tests nutzen eine Attrappe statt `opencode` (Pfad über `KETTE_OPENCODE`), nie ein echtes Modell. Bestehende Tests bleiben grün, Code läuft unter Python 3.10. Abnahme: echter Lauf mit dem 35B an einer Mini-Spec, die Claude schreibt; Dauer wird gemessen.
> Lies NUR zwei Dateien: diese Anforderung und docs/projekt_management/spec_paket_20261027_umsetzung_auto.md. Weitere Stellen nur, wenn wirklich etwas fehlt: search_files, dann read_file mit start_line/end_line, höchstens drei Mal.

## Antworten auf Rueckfragen

**2026-10-27 09:56** — Frage (Hawe): Dann läuft alles ohne Gedächtnis?

> Verstehe ich, kein Gedächtnis! Nimm Punkt 10 auf!
> (Von Claude nach Hawes Zustimmung am 27.10. 09:59 eingetragen: neue Sitzung je Lauf und kein Gedächtnis-Proxy sind gewollt; Zustand liegt in Dateien, Kettenwissen kommt über Punkt 10.)
**2026-10-27 10:08** — Frage: Globale ~/.config/opencode/AGENTS.md verlangt Erklärung vor Architekturänderungen und englische Bezeichner – Widerspruch zum Automatikbetrieb?

> Ja. Die globale AGENTS.md bleibt unverändert. Zu Punkt 3: umsetzung_nacht sagt ausdrücklich, dass er Vorrang vor allgemeinen Kommunikationsregeln hat: nicht vorab erklären oder auf Freigabe warten, sondern umsetzen und Begründungen ins Handover schreiben; Bezeichner wie in Spec und bestehendem Code (in diesem Repo deutsch).

## 2. Spec (Auszug aus `spec_20261027_umsetzung_auto.md`)

### Ziel
Neuer Befehl `kette.py umsetzung-auto <kurztitel>` startet `opencode run --format json` mit Agent `umsetzung_nacht` und einem konfigurierbaren Modell vollständig unbeaufsichtigt. `kette.py` prüft Vorbedingungen (Exit 2), überwacht den Lauf (Exit 1 bei Timeout oder fehlendem `reason: stop`), wertet das JSON aus, führt mechanische Nachprüfungen aus (HEAD, Schreibbereich, Handover, `pruefen`) und beendet sich nur mit Exit 0, wenn alles grün ist. Optionaler `--nacharbeit <datei.md>` für gezielte Nachbesserungen.

### Nicht-Ziele (bewusst ausgeschlossen – kein Befund)
- Keine Änderung des bestehenden `prompt umsetzung`-Workflows (TUI bleibt bestehen).
- Keine Änderung des Agenten `umsetzung` (Handbetrieb).
- Keine Integration des Gedächtnis-Providers (`gedaechtnis`); der Lauf nutzt `llamacpp/` direkt am Router.
- Keine automatische Rücksetzung oder Korrektur von Verletzungen durch `kette.py`; die Liste wird ausgegeben, die Entscheidung liegt bei Hawe.
- Keine Änderung der globalen `~/.config/opencode/AGENTS.md`.
- Kein Parallel-Lauf zweier `umsetzung-auto` für denselben Kurztitel (nicht gefordert; falls es passiert, ist das Ergebnis unbestimmt).

### Anforderungen
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

### Testplan (nur Titel und Erwartungen)
### T1: Vorab-Prüfung – Kurztitel ungültig
- **Erwartung:** Exit 2, Meldung enthält „ungültig".
### T2: Vorab-Prüfung – kein Spec-Commit
- **Erwartung:** Exit 2, Meldung enthält „Spec".
### T3: Vorab-Prüfung – Spec ohne `## Schreibbereich`
- **Erwartung:** Exit 2, Meldung enthält „Schreibbereich".
### T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)
- **Erwartung:** Exit 2, Meldung enthält „Arbeitsstand".
### T5: Vorab-Prüfung – `opencode` fehlt
- **Erwartung:** Exit 2, Meldung enthält „opencode".
### T6: Vorab-Prüfung – Modell kein `llamacpp/`
- **Erwartung:** Exit 2, Meldung enthält „llamacpp".
### T7: Erfolgreicher Lauf, `reason: stop`, alle Prüfungen grün
- **Erwartung:** Exit 0. Protokollzeile in `umsetzung_<datum>_g.md`. Rohdaten-Datei in `role-split/results/`. `pruefen`-Ergebnis = 0.
### T8: Lauf ohne `reason: stop`
- **Erwartung:** Exit 1, Meldung enthält „nicht abgeschlossen" oder „reason".
### T9: Timeout
- **Erwartung:** Exit 1, Meldung enthält „Timeout". Prozess wird beendet.
### T10: Selbst-Commit
- **Erwartung:** Exit 1, Meldung enthält „Selbst-Commit".
### T11: Datei außerhalb Schreibbereich
- **Erwartung:** Exit 1, Meldung enthält den Pfad der verbotenen Datei.
### T12: Handover fehlt
- **Erwartung:** Exit 1, Meldung enthält „Handover".
### T13: Nacharbeit – Auftrag aus Datei
- **Erwartung:** Exit 0. Prompt enthält den Auftragstext. Handover hat neuen Abschnitt `## Nachbesserung 1`.
### T14: Nacharbeit – zwei ohne Fortschritt
- **Erwartung:** Exit 1, Meldung enthält „Übergabe an Hawe". Kein neuer Lauf.
### T15: Lebendsignal – Werkzeugzeile
- **Erwartung:** stdout enthält eine Zeile mit dem Werkzeugnamen und dem Wortlaut (gekürzt).
### T16: `pruefen` rot
- **Erwartung:** Exit 1.
### T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen
- **Erwartung:** Exit 2, Meldung enthält die fremde Datei.
### T18: Schreibbereich – Ordner-Eintrag
- **Erwartung:** Exit 0 (Datei liegt im Schreibbereich).
### T19: Schreibbereich – Verbotene Dateien
- **Erwartung:** Exit 1, Meldung enthält den Pfad der Spec-Datei.
### T20: main() – gleicher Exit wie Funktionsaufruf
- **Erwartung:** Exit-Code identisch mit dem von `kette.umsetzung_auto("g")` (0). Damit ist belegt, dass der argparse-Pfad denselben Code durchläuft.
### T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)
- **Erwartung:** **Kein Exit 2.** Der Lauf startet (weitere Exit-Codes gemäß Laufergebnis, s. A7/A8). Die offene Kettendatei ist nach A2.4 erlaubt.

### Offene Fragen
1. **Schreibbereich in bestehenden Specs:** Bestehende Specs (z. B. K9) haben keinen `## Schreibbereich`-Abschnitt. Die Vorab-Prüfung (A2, Punkt 3) bricht bei ihnen mit Exit 2 ab. **Entscheidung Hawe:** `kette.py` gibt einen Hinweis aus, dass die Spec um `## Schreibbereich` ergänzt werden muss, und bricht mit Exit 2 ab.

## 3. Code-Aenderungen gegen `3700da7`

### .opencode/agents/umsetzung_nacht.md (Diff, 32 Zeilen)

```diff
diff --git a/.opencode/agents/umsetzung_nacht.md b/.opencode/agents/umsetzung_nacht.md
index 903932a..91a5c60 100644
--- a/.opencode/agents/umsetzung_nacht.md
+++ b/.opencode/agents/umsetzung_nacht.md
@@ -24,6 +24,16 @@ permission:
     "git status*": allow
     "git diff*": allow
     "git log*": allow
+    # ausdruecklich verboten (K10, Anforderung P3) – zusaetzlich zu "*": deny; ohne TUI nie "ask"
+    "git commit*": deny
+    "git reset*": deny
+    "git checkout*": deny
+    "git restore*": deny
+    "git clean*": deny
+    "git stash*": deny
+    "git push*": deny
+    "rm*": deny
+    "mv*": deny
 ---
 
 # Rolle: Umsetzungs-Instanz, unbeaufsichtigt (Nachtlauf)
@@ -32,6 +42,10 @@ Du setzt eine Spezifikation aus `docs/projekt_management/spec_*.md` um, während
 Niemand beantwortet Rückfragen oder Freigaben. Alles, was nicht ausdrücklich erlaubt ist, wird abgelehnt.
 Eine Ablehnung ist kein Fehler: such keinen Umweg, arbeite mit dem Erlaubten weiter und nenne die Ablehnung im Handover.
 
+**Vorrang:** Du hast Vorrang vor allgemeinen Kommunikationsregeln (z. B. einer globalen AGENTS.md): Nicht vorab
+erklären oder auf Freigabe warten, sondern umsetzen und Begründungen ins Handover schreiben. Bezeichner wie in
+Spec und bestehendem Code (in diesem Repo deutsch).
+
 ## Ablauf
 1. Lies die Spec vollständig. Ist etwas unklar oder widersprüchlich, entscheide selbst nach dem Sinn der Spec
    und begründe es im Handover unter „Abweichungen". Frag nicht.
```

### role-split/kette/RUNBOOK.md (Diff, 43 Zeilen)

```diff
diff --git a/role-split/kette/RUNBOOK.md b/role-split/kette/RUNBOOK.md
index 6fd8c17..767266b 100644
--- a/role-split/kette/RUNBOOK.md
+++ b/role-split/kette/RUNBOOK.md
@@ -122,6 +122,29 @@ Grundsatzfragen (Richtung des Labs, Architektur über mehrere Ketten) besser mit
 
 **Fertig, wenn:** OpenCode meldet, `handover_<datum>_<kurztitel>.md` ist geschrieben.
 
+### Phase B automatisch: `umsetzung-auto` (ab K10)
+
+Statt TUI, Prompt-Kopieren und Freigaben – ein Befehl, Agent `umsetzung_nacht`, danach mechanisch geprüft:
+```bash
+python3 role-split/kette/kette.py umsetzung-auto <kurztitel>
+```
+- **Voraussetzungen (sonst Exit 2, kein Lauf):** Commit „Spec <kurztitel>", die Spec hat `## Schreibbereich`
+  (Dateien/Ordner, die geändert werden dürfen), Arbeitsstand sauber, `opencode` installiert, Modell beginnt mit `llamacpp/`.
+- **Einstellungen:** `KETTE_UMSETZUNG_MODEL` (Vorgabe 35B-A3B), `KETTE_UMSETZUNG_TIMEOUT` (7200 s für den ganzen Lauf),
+  `OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS` (300000 je Befehl).
+- **Danach prüft das Werkzeug selbst:** kein Selbst-Commit (HEAD unverändert), nur Dateien aus dem Schreibbereich,
+  Testdatei und Handover geändert, Handover in diesem Lauf geschrieben, `pruefen` grün. Es setzt **nichts** zurück.
+- **Ergebnis:** Exit 0 = alles in Ordnung → weiter mit **Phase D**. Exit 1 = Liste der Befunde lesen. Je Lauf eine Zeile in
+  `umsetzung_<datum>_<kurztitel>.md`, Rohdaten (JSON-Strom) in `role-split/results/`.
+- **Nacharbeit:** Den Auftrag (von Claude) als `docs/projekt_management/nacharbeit_<datum>_<kurztitel>_<n>.md` ablegen, dann
+  ```bash
+  python3 role-split/kette/kette.py umsetzung-auto <kurztitel> --nacharbeit docs/projekt_management/nacharbeit_<datum>_<kurztitel>_<n>.md
+  ```
+  Offene Kettendateien (Prüfung, Verdikte, Protokoll) stören dabei nicht. Nach zwei Nachbesserungen in Folge ohne
+  Fortschritt startet keine weitere: „Übergabe an Hawe" (Exit 1).
+- Gemessen an opencode 1.19.3: `ask` wird ohne TUI sofort abgelehnt und beendet den Lauf stumm; der Exit-Code von OpenCode
+  ist immer 0 – deshalb wertet `kette.py` nur den JSON-Strom aus.
+
 ---
 
 ## Phase C – Maschinelle Prüfung (ein Befehl)
@@ -280,6 +303,8 @@ python3 role-split/kette/kette.py quellen <kurztitel>
 git add docs/projekt_management/*_<kurztitel>.md && git commit -m "Spec <kurztitel>"
 # B
 python3 role-split/kette/kette.py prompt umsetzung <kurztitel>     # → opencode, Qwen3.6, Agent umsetzung
+#    oder automatisch (Spec braucht ## Schreibbereich):
+python3 role-split/kette/kette.py umsetzung-auto <kurztitel>
 # C
 python3 role-split/kette/kette.py pruefen <kurztitel>
 # D  Ctrl+C, start_eval | Qwen3.6-35B-A3B, Reasoning aus | Lauf 1: prompt review | Lauf 2 (neuer Chat): prompt review2
```

### role-split/kette/kette.py (Diff, 476 Zeilen)

```diff
diff --git a/role-split/kette/kette.py b/role-split/kette/kette.py
index ec05576..65f2b61 100644
--- a/role-split/kette/kette.py
+++ b/role-split/kette/kette.py
@@ -55,6 +55,12 @@ Befehle, nur Standardbibliothek, liest/schreibt nur im Projekt:
         oder eine Anforderung "teilweise"/"nicht" ergibt NACHBESSERN.
         --anhaengen schreibt das Ergebnis als Abschnitt ans Verdikt.
 
+  python3 role-split/kette/kette.py umsetzung-auto <kurztitel> [--nacharbeit <datei.md>]
+        Umsetzung bzw. Nacharbeit ohne TUI: opencode run --format json, Agent umsetzung_nacht,
+        Modell KETTE_UMSETZUNG_MODEL (nur llamacpp/), Zeitlimit KETTE_UMSETZUNG_TIMEOUT (7200 s).
+        Danach mechanisch: Selbst-Commit, Schreibbereich der Spec, Handover, pruefen. Protokollzeile in
+        docs/projekt_management/umsetzung_<datum>_<kurztitel>.md, Rohdaten in role-split/results/.
+
 Exit-Codes: 0 = in Ordnung / PASS, 1 = Abweichung / NACHBESSERN, 2 = Datei/Format-Fehler.
 Mode B: Lab, beruehrt AskValentinAI nicht.
 """
@@ -68,6 +74,7 @@ import json
 import os
 import re
 import shutil
+import signal
 import socket
 import subprocess
 import sys
@@ -1458,6 +1465,432 @@ def review_auto(kurztitel: str) -> int:
     return gesamt_exit
 
 
+# ---------------------------------------------------------------- umsetzung-auto (K10)
+#
+# Startet die Umsetzung ohne TUI ueber `opencode run --format json` (Agent umsetzung_nacht) und
+# prueft danach mechanisch. Gemessen an opencode 1.19.3 (Spec-Paket §1): Exit-Code ist immer 0,
+# Erfolg steht nur im JSON; `ask` wird ohne TUI sofort abgelehnt; OPENCODE_PERMISSION kann
+# Agent-Regeln nicht ueberstimmen -> Sperren stehen in der Agent-Datei, Schreibgrenze prueft kette.py.
+
+UMSETZUNG_AGENT = "umsetzung_nacht"
+UMSETZUNG_MODELL_STANDARD = "llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL"
+UMSETZUNG_TIMEOUT_STANDARD = 7200          # s, ganzer Lauf (A5)
+UMSETZUNG_BASH_MS_STANDARD = 300000        # ms, Einzelbefehl, wertet OpenCode selbst aus (Probe P3)
+# Kettendateien, die bei Nacharbeit offen sein duerfen (A2.4); Spec/Anforderung/Quellen nie.
+KETTEN_PRAEFIXE = ("pruefung", "umsetzung", "review_paket", "verdict", "gesamt", "nacharbeit", "handover")
+VORGABE_PRAEFIXE = ("spec_", "anforderung_", "quellen_", "_vorlage_")
+ABGELEHNT_TEXTE = ("rejected permission", "rule which prevents")
+
+
+def _schreibbereich(spec_text: str) -> list[str] | None:
+    """Eintraege unter '## Schreibbereich' (je '- pfad', Backticks erlaubt). None, wenn der Abschnitt fehlt."""
+    if not re.search(r"^##\s+Schreibbereich\s*$", spec_text, re.M):
+        return None
+    eintraege = []
+    for z in abschnitt(spec_text, "Schreibbereich").splitlines():
+        m = re.match(r"^\s*[-*]\s+`?([^`\s]+)`?", z)
+        if m:
+            eintraege.append(m.group(1).lstrip("./") if m.group(1).startswith("./") else m.group(1))
+    return eintraege
+
+
+def _im_schreibbereich(pfad: str, eintraege: list[str]) -> bool:
+    """Exakter Dateipfad oder Ordner-Eintrag mit '/' am Ende als Praefix."""
+    return any(pfad == e or (e.endswith("/") and pfad.startswith(e)) for e in eintraege)
+
+
+def _ist_vorgabe(pfad: str) -> bool:
+    """Spec, Anforderung, Quellen, Vorlagen der Kette – darf die Umsetzung nie aendern."""
+    name = Path(pfad).name
+    return name.endswith(".md") and name.startswith(VORGABE_PRAEFIXE)
+
+
+def _ist_kettendatei(pfad: str, kurztitel: str) -> bool:
+    """Von der Kette erzeugte Datei dieses Kurztitels in docs/projekt_management/ (ohne Vorgaben)."""
+    p = Path(pfad)
+    if p.parent.as_posix() != "docs/projekt_management":
+        return False
+    muster = rf"^(?:{'|'.join(KETTEN_PRAEFIXE)})_\d{{8}}_{re.escape(kurztitel)}(?:_[\w.-]+)?\.md$"
+    return re.match(muster, p.name) is not None
+
+
+def _offene_dateien() -> list[str] | None:
+    """Pfade aus `git status --porcelain -z --untracked-files=all` (geaendert, vorgemerkt, neu, geloescht).
+    -z: keine Anfuehrungszeichen, Umbenennungen liefern Ziel und Quelle. None bei git-Fehler."""
+    r = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "-z", "--untracked-files=all"],
+                       capture_output=True, text=True)
+    if r.returncode != 0:
+        return None
+    teile, pfade, i = r.stdout.split("\0"), [], 0
+    while i < len(teile):
+        eintrag = teile[i]
+        i += 1
+        if len(eintrag) < 4:
+            continue
+        status, pfad = eintrag[:2], eintrag[3:]
+        pfade.append(pfad)
+        if "R" in status or "C" in status:       # Umbenennung/Kopie: naechstes Feld ist die Quelle
+            if i < len(teile) and teile[i]:
+                pfade.append(teile[i])
+            i += 1
+    return sorted(set(pfade))
+
+
+def _stand() -> dict[str, str] | None:
+    """Pruefsummen aller offenen Dateien: {pfad: sha256 | '<geloescht>' | '<unlesbar>'} (A7)."""
+    pfade = _offene_dateien()
+    if pfade is None:
+        return None
+    stand = {}
+    for d in pfade:
+        p = ROOT / d
+        if not p.exists():
+            stand[d] = "<geloescht>"
+        elif p.is_file():
+            try:
+                stand[d] = hashlib.sha256(p.read_bytes()).hexdigest()
+            except OSError:
+                stand[d] = "<unlesbar>"
+        else:
+            stand[d] = "<kein-file>"
+    return stand
+
+
+def _in_diesem_lauf(vor: dict[str, str], nach: dict[str, str]) -> dict[str, str]:
+    """{pfad: 'neu'|'weg'|'geaendert'} fuer alles, was sich zwischen den Schnappschuessen unterscheidet.
+    Eine vorher saubere Datei, die der Lauf aendert, taucht nur in `nach` auf -> 'neu' (= jetzt offen)."""
+    raus = {}
+    for d in sorted(set(vor) | set(nach)):
+        if d not in vor:
+            raus[d] = "neu"
+        elif d not in nach:
+            raus[d] = "weg"
+        elif vor[d] != nach[d]:
+            raus[d] = "geaendert"
+    return raus
+
+
+PROTOKOLL_RE = re.compile(r"rot: (?P<rot>[^,]+), pruefen: (?P<pruefen>[^,]+), art: (?P<art>erst|nb\d+)")
+
+
+def _protokoll(pfad: Path) -> list[dict]:
+    """Protokollzeilen (A6) in Dateireihenfolge: [{'rot', 'pruefen', 'art'}, ...]."""
+    if not pfad.is_file():
+        return []
+    zeilen = []
+    for z in pfad.read_text(encoding="utf-8").splitlines():
+        m = PROTOKOLL_RE.search(z)
+        if m:
+            zeilen.append({k: m.group(k).strip() for k in ("rot", "pruefen", "art")})
+    return zeilen
+
+
+def _zahl(wert: str) -> int | None:
+    return int(wert) if re.fullmatch(r"\d+", str(wert).strip()) else None
+
+
+def _fortschritt(alt: dict, neu: dict) -> bool:
+    """A8: rot bekannt und gesunken ODER pruefen bekannt und kleiner – und keiner der beiden schlechter.
+    Unbekannte Werte ('–') zaehlen nie als Fortschritt."""
+    ar, nr, ap, np_ = _zahl(alt["rot"]), _zahl(neu["rot"]), _zahl(alt["pruefen"]), _zahl(neu["pruefen"])
+    if None in (ar, nr, ap, np_):
+        return False
+    return (nr < ar or np_ < ap) and nr <= ar and np_ <= ap
+
+
+def _halt_noetig(zeilen: list[dict]) -> bool:
+    """Die letzten zwei nb-Laeufe zeigten beide keinen Fortschritt gegenueber ihrem jeweiligen Vorlauf."""
+    nb = [i for i, z in enumerate(zeilen) if z["art"].startswith("nb") and i > 0]
+    if len(nb) < 2:
+        return False
+    return all(not _fortschritt(zeilen[i - 1], zeilen[i]) for i in nb[-2:])
+
+
+def _rot_aus_pruefung(kurztitel: str) -> str:
+    """failures+errors aus der unittest-Ausgabe der pruefung-Datei; 'OK' -> 0; sonst '–' (A6)."""
+    pfad = datei_suchen("pruefung", kurztitel, None)
+    if not pfad:
+        return "–"
+    ut = abschnitt(pfad.read_text(encoding="utf-8"), "unittest")
+    m = re.search(r"^FAILED \(([^)]*)\)", ut, re.M)
+    if m:
+        werte = dict(re.findall(r"(\w+)=(\d+)", m.group(1)))
+        return str(int(werte.get("failures", 0)) + int(werte.get("errors", 0)))
+    if re.search(r"^OK\b", ut, re.M):
+        return "0"
+    return "–"
+
+
+def _opencode_programm() -> list[str] | None:
+    """KETTE_OPENCODE (Pfad; .py wird mit sys.executable gestartet) oder `opencode` im PATH."""
+    eigen = os.environ.get("KETTE_OPENCODE", "").strip()
+    if eigen:
+        if not Path(eigen).is_file():
+            return None
+        return [sys.executable, eigen] if eigen.endswith(".py") else [eigen]
+    gefunden = shutil.which("opencode")
+    return [gefunden] if gefunden else None
+
+
+def _umsetzung_prompt(kurztitel: str, datum: str, commit: str, nacharbeit: Path | None, nb: int) -> str | None:
+    vorlage = PROMPTS / "umsetzung_nacht.md"
+    if not vorlage.is_file():
+        return None
+    anf = datei_suchen("anforderung", kurztitel, None)
+    anf_pfad = f"docs/projekt_management/{anf.name}" if anf else \
+        f"docs/projekt_management/anforderung_{datum}_{kurztitel}.md"
+    text = (vorlage.read_text(encoding="utf-8")
+            .replace("{kurztitel}", kurztitel).replace("{datum}", datum).replace("{commit}", commit)
+            .replace("{anforderung}", anf_pfad)
+            .replace("{quellen}", f"docs/projekt_management/quellen_{datum}_{kurztitel}.md"))
+    text = "\n".join(z for z in text.splitlines() if not z.startswith("<!--")).strip() + "\n"
+    if nacharbeit:
+        text += (f"\n## Nachbesserung {nb}\n\nDas ist Nachbesserung {nb}. Der Auftrag steht unten (aus "
+                 f"`{_rel(nacharbeit)}`). Ergänze den Handover docs/projekt_management/handover_{datum}_"
+                 f"{kurztitel}.md um den Abschnitt „## Nachbesserung {nb}\" – nichts Bestehendes löschen.\n\n"
+                 + nacharbeit.read_text(encoding="utf-8").strip() + "\n")
+    return text
+
+
+def _lauf(befehl: list[str], env: dict, timeout: int, rohdaten: Path) -> dict:
+    """Startet opencode in eigener Prozessgruppe, liest den JSON-Strom zeilenweise (sofort in die
+    Rohdaten), gibt je Werkzeugaufruf eine Zeile aus und beendet die Gruppe nach `timeout` s (A5, A6, A9)."""
+    info = {"werkzeuge": 0, "fehler": [], "abgelehnt": [], "tokens": 0, "reason": None, "text": "",
+            "ereignisse": 0, "kaputt": 0, "timeout": False}
+    rohdaten.parent.mkdir(parents=True, exist_ok=True)
+    stderr_datei = rohdaten.with_suffix(".err")
+    start = dt.datetime.now()
+    with open(rohdaten, "w", encoding="utf-8") as roh, open(stderr_datei, "w", encoding="utf-8") as fehlerkanal:
+        try:
+            proc = subprocess.Popen(befehl, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=fehlerkanal,
+                                    text=True, encoding="utf-8", errors="replace", start_new_session=True)
+        except OSError as e:
+            info["startfehler"] = f"{type(e).__name__}: {e}"
+            info["dauer"] = 0
+            return info
+
+        def lesen():
+            for zeile in proc.stdout:
+                roh.write(zeile); roh.flush()
+                zeile = zeile.strip()
+                if not zeile:
+                    continue
+                try:
+                    e = json.loads(zeile)
+                except json.JSONDecodeError:
+                    info["kaputt"] += 1
+                    continue
+                info["ereignisse"] += 1
+                teil = e.get("part") or {}
+                typ = e.get("type")
+                if typ == "tool_use":
+                    zustand = teil.get("state") or {}
+                    status = zustand.get("status")
+                    if status not in ("completed", "error"):
+                        continue
+                    info["werkzeuge"] += 1
+                    eingabe = zustand.get("input")
+                    wortlaut = (eingabe.get("command") or eingabe.get("filePath") or json.dumps(eingabe,
+                                ensure_ascii=False)) if isinstance(eingabe, dict) else str(eingabe or "")
+                    kurz = wortlaut.replace("\n", " ")[:60]
+                    print(f"[{dt.datetime.now():%H:%M:%S}] {teil.get('tool', '?')}: {kurz}"
+                          + ("…" if len(wortlaut) > 60 else "") + ("  [FEHLER]" if status == "error" else ""),
+                          flush=True)
+                    if status == "error":
+                        fehlertext = str(zustand.get("error") or "")
+                        eintrag = f"{teil.get('tool', '?')}: {wortlaut[:200]} – {fehlertext[:200]}"
+                        info["fehler"].append(eintrag)
+                        if any(t in fehlertext for t in ABGELEHNT_TEXTE):
+                            info["abgelehnt"].append(eintrag)
+                elif typ == "step_finish":
+                    info["reason"] = teil.get("reason")
+                    info["tokens"] += int((teil.get("tokens") or {}).get("total") or 0)
+                elif typ == "text":
+                    info["text"] = teil.get("text") or info["text"]
+
+        leser = threading.Thread(target=lesen, daemon=True)
+        leser.start()
+        stopp = threading.Event()
+
+        def puls():
+            while not stopp.wait(KETTE_HERZSCHLAG_S):
+                minuten = int((dt.datetime.now() - start).total_seconds()) // 60
+                print(f"[{dt.datetime.now():%H:%M:%S}] Lebenszeichen, Lauf läuft seit {minuten} min", flush=True)
+
+        herz = threading.Thread(target=puls, daemon=True)
+        herz.start()
+        try:
+            proc.wait(timeout=timeout)
+        except subprocess.TimeoutExpired:
+            info["timeout"] = True
+            try:
+                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
+            except (ProcessLookupError, PermissionError, OSError):
+                pass
+            proc.wait()
+        finally:
+            stopp.set()
+        leser.join(timeout=10)
+    info["dauer"] = int((dt.datetime.now() - start).total_seconds())
+    return info
+
+
+def umsetzung_auto(kurztitel: str, nacharbeit: str | None = None) -> int:
+    """K10: Umsetzung bzw. Nacharbeit ueber `opencode run` ohne TUI, danach mechanisch pruefen.
+    Exit 0 = abgeschlossen + keine Verletzung + pruefen 0; 1 = Lauf/Pruefung nicht in Ordnung; 2 = Voraussetzung."""
+    def nein(meldung: str, code: int = 2) -> int:
+        print(meldung, file=sys.stderr)
+        return code
+
+    # A2.1 Kurztitel
+    if not re.fullmatch(r"[a-z0-9_]+", kurztitel):
+        return nein(f"Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _).")
+    # A2.2 Spec-Commit
+    commit = spec_commit(kurztitel)
+    if not commit:
+        return nein(f"Kein Commit 'Spec {kurztitel}' gefunden – erst die Spec committen.")
+    # A2.3 Spec mit Schreibbereich
+    spec_p = datei_suchen("spec", kurztitel, None)
+    if not spec_p:
+        return nein(f"Keine Spec spec_<datum>_{kurztitel}.md in {_rel(PM)}.")
+    bereich = _schreibbereich(spec_p.read_text(encoding="utf-8"))
+    if bereich is None:
+        return nein(f"Spec {spec_p.name} hat keinen Abschnitt '## Schreibbereich'. Spec um '## Schreibbereich' "
+                    "ergaenzen (Dateien/Ordner, die die Umsetzung aendern darf), sonst kein umsetzung-auto-Lauf.")
+    if not bereich:
+        return nein(f"'## Schreibbereich' in {spec_p.name} ist leer – mindestens einen Pfad eintragen.")
+    datum = _datum_aus(spec_p) or dt.date.today().strftime("%Y%m%d")
+    testdatei = f"tests/test_{kurztitel}.py"
+    handover_rel = f"docs/projekt_management/handover_{datum}_{kurztitel}.md"
+    protokoll_p = PM / f"umsetzung_{datum}_{kurztitel}.md"
+    nach_p = None
+    if nacharbeit:
+        nach_p = Path(nacharbeit)
+        if not nach_p.is_absolute():
+            nach_p = (ROOT / nach_p) if (ROOT / nach_p).is_file() else nach_p.resolve()
+        if not nach_p.is_file():
+            return nein(f"Nacharbeitsdatei {nacharbeit} nicht gefunden.")
+    # A2.4 Arbeitsstand
+    offen = _offene_dateien()
+    if offen is None:
+        return nein("git status fehlgeschlagen – ist ROOT ein Git-Repo?")
+    if not nach_p:
+        if offen:
+            return nein("Arbeitsstand nicht sauber – ohne --nacharbeit muss alles committet sein:\n"
+                        + "\n".join(f"  {d}" for d in offen))
+    else:
+        try:
+            nach_rel = nach_p.resolve().relative_to(ROOT.resolve()).as_posix()
+        except ValueError:
+            nach_rel = None
+        fremd = [d for d in offen
+                 if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d == testdatei or d == handover_rel
+                                             or _ist_kettendatei(d, kurztitel) or d == nach_rel)]
+        if fremd:
+            return nein("Nacharbeit: unzulaessige offene Aenderungen (Vorgaben oder ausserhalb von Schreibbereich/"
+                        "Testdatei/Kettendateien):\n" + "\n".join(f"  {d}" for d in fremd))
+    # A2.5 opencode
+    programm = _opencode_programm()
+    if not programm:
+        ziel = os.environ.get("KETTE_OPENCODE") or "opencode im PATH"
+        return nein(f"opencode nicht gefunden ({ziel}).")
+    # A2.6 Modell
+    modell = os.environ.get("KETTE_UMSETZUNG_MODEL", UMSETZUNG_MODELL_STANDARD)
+    if not modell.startswith("llamacpp/"):
+        return nein(f"Modell '{modell}' beginnt nicht mit 'llamacpp/' (nur direkt am Router, ohne Gedaechtnis).")
+    # A8 Halt-Regel und Nummer
+    zeilen = _protokoll(protokoll_p)
+    nb = sum(1 for z in zeilen if z["art"].startswith("nb")) + 1
+    if nach_p and _halt_noetig(zeilen):
+        return nein("Zwei Nachbesserungen in Folge ohne Fortschritt – keine weitere. Übergabe an Hawe.", 1)
+    art = f"nb{nb}" if nach_p else "erst"
+    # A3 Prompt
+    prompt_text = _umsetzung_prompt(kurztitel, datum, commit, nach_p, nb)
+    if prompt_text is None:
+        return nein(f"Prompt-Vorlage {_rel(PROMPTS / 'umsetzung_nacht.md')} fehlt.")
+    try:
+        timeout = int(os.environ.get("KETTE_UMSETZUNG_TIMEOUT", UMSETZUNG_TIMEOUT_STANDARD))
+        bash_ms = int(os.environ.get("OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS", UMSETZUNG_BASH_MS_STANDARD))
+    except ValueError:
+        return nein("KETTE_UMSETZUNG_TIMEOUT / OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS muessen ganze Zahlen sein.")
+
+    # A7 Schnappschuss VOR dem Start
+    head_vor = _git("rev-parse", "HEAD").strip()
+    stand_vor = _stand()
+    if stand_vor is None:
+        return nein("git status fehlgeschlagen.")
+    befehl = programm + ["run", "--format", "json", "--agent", UMSETZUNG_AGENT, "--model", modell,
+                         "--dir", str(ROOT), "--title", f"kette {kurztitel} {art}", prompt_text]
+    env = dict(os.environ, OPENCODE_EXPERIMENTAL_BASH_DEFAULT_TIMEOUT_MS=str(bash_ms))
+    rohdaten = ROOT / "role-split" / "results" / f"umsetzung_auto_{datum}_{kurztitel}_{dt.datetime.now():%H%M%S}.jsonl"
+    print(f"umsetzung-auto {kurztitel} ({art}): Modell {modell}, Agent {UMSETZUNG_AGENT}, "
+          f"Zeitlimit {timeout} s, Rücksetzpunkt {commit}", flush=True)
+    info = _lauf(befehl, env, timeout, rohdaten)
+
+    # A7 Schnappschuss SOFORT nach dem Lauf, bevor kette.py selbst etwas schreibt
+    stand_nach = _stand() or {}
+    head_nach = _git("rev-parse", "HEAD").strip()
+    aenderungen = _in_diesem_lauf(stand_vor, stand_nach)
+    abgeschlossen = not info["timeout"] and info["reason"] == "stop"
+    befunde = []
+
+    if info.get("startfehler"):
+        befunde.append(f"opencode liess sich nicht starten: {info['startfehler']}")
+    elif info["timeout"]:
+        befunde.append(f"Timeout nach {timeout} s – opencode samt Unterprozessen beendet.")
+    elif info["ereignisse"] == 0:
+        befunde.append("Keine gültigen JSON-Ereignisse von opencode.")
+    elif info["reason"] != "stop":
+        befunde.append(f"Lauf nicht abgeschlossen (reason: {info['reason']}).")
+    # (a) immer
+    if head_vor != head_nach:
+        befunde.append(f"Selbst-Commit: HEAD {head_vor[:7]} -> {head_nach[:7]} (nichts zurückgesetzt).")
+    # (b) immer
+    verstoesse = [(d, a) for d, a in aenderungen.items()
+                  if _ist_vorgabe(d) or not (_im_schreibbereich(d, bereich) or d in (testdatei, handover_rel))]
+    if verstoesse:
+        befunde.append("Schreibbereich verletzt (nichts zurückgesetzt):\n"
+                       + "\n".join(f"  {d} ({a})" for d, a in verstoesse))
+    # (c) und (d) nur bei abgeschlossenem Lauf
+    rot, pruefen_code = "–", "–"
+    if abgeschlossen:
+        if handover_rel not in aenderungen or not (ROOT / handover_rel).is_file():
+            befunde.append(f"Handover {handover_rel} in diesem Lauf nicht geschrieben.")
+        code = pruefen(kurztitel)
+        pruefen_code = str(code)
+        rot = _rot_aus_pruefung(kurztitel)
+        if code != 0:
+            befunde.append(f"pruefen: Exit {code}.")
+    else:
+        print("(c) übersprungen (Lauf nicht abgeschlossen)\n(d) übersprungen (Lauf nicht abgeschlossen)")
+
+    exit_code = 1 if befunde else 0
+    reason = "timeout" if info["timeout"] else (info["reason"] or "–")
+    zeile = (f"- **{dt.datetime.now():%Y-%m-%d %H:%M}** – Modell: {modell}, Dauer: {info['dauer']} s, "
+             f"Tools: {info['werkzeuge']}, Fehler: {len(info['fehler'])}, Abgelehnt: {len(info['abgelehnt'])}, "
+             f"Tokens: {info['tokens']}, reason: {reason}, rot: {rot}, pruefen: {pruefen_code}, art: {art}, "
+             f"Exit: {exit_code}\n")
+    if not protokoll_p.exists():
+        protokoll_p.write_text(f"# Umsetzungs-Protokoll: {kurztitel}\n\nJe Lauf eine Zeile (kette.py umsetzung-auto).\n\n",
+                               encoding="utf-8")
+    with open(protokoll_p, "a", encoding="utf-8") as f:
+        f.write(zeile)
+
+    print(f"\n=== umsetzung-auto {kurztitel} ({art}) ===")
+    print(f"Dauer {info['dauer']} s, Werkzeugaufrufe {info['werkzeuge']}, Fehler {len(info['fehler'])}, "
+          f"abgelehnt {len(info['abgelehnt'])}, Tokens {info['tokens']}, reason {reason}")
+    for e in info["abgelehnt"]:
+        print(f"  abgelehnt: {e}")
+    if info["text"]:
+        print(f"Schlusstext: {info['text'][:300]}")
+    print(f"In diesem Lauf geändert: {', '.join(aenderungen) or 'nichts'}")
+    for b in befunde:
+        print(f"!!! {b}")
+    print(f"Rohdaten: {_rel(rohdaten)}\nProtokoll: {_rel(protokoll_p)}")
+    print(f"==> {'OK' if exit_code == 0 else 'NICHT IN ORDNUNG'} (Exit {exit_code})")
+    return exit_code
+
+
 # ---------------------------------------------------------------- main
 
 def main(argv=None) -> int:
@@ -1482,6 +1915,8 @@ def main(argv=None) -> int:
     pr.add_argument("kurztitel"); pr.add_argument("--commit"); pr.add_argument("--timeout", type=int, default=300)
     ra = sub.add_parser("review-auto", help="Review-Paket, zwei API-Laeufe, Verdikte, Zusammenfassung")
     ra.add_argument("kurztitel")
+    ua = sub.add_parser("umsetzung-auto", help="Umsetzung/Nacharbeit ueber opencode run ohne TUI, danach pruefen")
+    ua.add_argument("kurztitel"); ua.add_argument("--nacharbeit", help="Datei mit dem Nachbesserungs-Auftrag")
     args = ap.parse_args(argv)
     if args.cmd == "zusammenfuehren":
         return zusammenfuehren([Path(v) if Path(v).is_absolute() or Path(v).exists() else PM / Path(v).name
@@ -1492,6 +1927,8 @@ def main(argv=None) -> int:
         return pruefen(args.kurztitel, args.commit, args.timeout)
     if args.cmd == "review-auto":
         return review_auto(args.kurztitel)
+    if args.cmd == "umsetzung-auto":
+        return umsetzung_auto(args.kurztitel, args.nacharbeit)
     if args.cmd == "gegenprobe":
         return gegenprobe(args.kurztitel, args.commit, args.timeout)
     if args.cmd == "quellen":
```

### role-split/kette/prompts/umsetzung_nacht.md (neue Datei, mit Zeilennummern, 17 Zeilen)

```
   1  <!-- Schritt 2 automatisch: kette.py umsetzung-auto, Agent „umsetzung_nacht", opencode run ohne TUI. Rücksetzpunkt = Commit „Spec <kurztitel>". -->
   2  Setz docs/projekt_management/spec_{datum}_{kurztitel}.md um. Niemand ist anwesend: keine Rückfragen, kein Warten auf Freigabe.
   3  
   4  Pflichtlektüre vor der ersten Änderung: docs/learnings/LERNREGELN.md, Abschnitte „Umsetzung" und „Tests".
   5  
   6  Lies keine großen Dateien ganz. Erst search_files bzw. grep (liefert Zeilennummern), dann read mit Zeilenbereich. Die Spec nennt die Fundstellen unter „Quellen". Große Dateien (z. B. role-split/kette/kette.py) änderst du nur gezielt (edit), nie durch Neuschreiben der ganzen Datei.
   7  
   8  Konstanten, Formate, Schnittstellen und Optionen nimmst du ausschließlich aus {quellen} und dem Code selbst, nie aus dem Gedächtnis. Fehlt dort etwas, setz nichts Erfundenes ein, sondern nenne es im Handover unter „Abweichungen".
   9  Verbindliche Vorgabe ist {anforderung}. Widerspricht die Spec ihr an einer Stelle, setzt du die Spec um und nennst den Widerspruch im Handover unter „Abweichungen".
  10  
  11  - Rücksetzpunkt ist Commit {commit}; nicht selbst committen, kein git reset/checkout/restore/stash.
  12  - Du änderst nur Dateien aus dem Abschnitt „## Schreibbereich" der Spec, dazu tests/test_{kurztitel}.py und den Handover. Alles andere meldet das Werkzeug danach als Verstoß.
  13  - Die Tests der Spec schreibst du als tests/test_{kurztitel}.py (unittest), je Test-ID eine Methode test_<id>_… (z. B. test_t1_timeout), Testtitel und Nummern exakt wie in der Spec. Kein Test darf Außenwirkung haben: keine echten Server außer 127.0.0.1, keine echten Datenordner und kein echtes Repo (immer temporäres Verzeichnis), kein echter Versand.
  14  - Ein Test, der sich nicht wie in der Spec bauen lässt, wird NICHT durch einen anderen ersetzt: unter „Abweichungen" und „Nicht getestet" nennen.
  15  - Befehle mit Außenwirkung führst du nie aus. Nenne sie im Handover unter „Hawe muss ausführen".
  16  - Nach jeder Datei: python3 -m py_compile bzw. bash -n.
  17  - Handover nach docs/projekt_management/handover_{datum}_{kurztitel}.md, Vorlage docs/projekt_management/_vorlage_handover.md. Testtitel exakt wie in der Spec, darunter die echte Ausgabe von python3 -m unittest -v tests/test_{kurztitel}.py.
```

### role-split/kette/testdata/opencode_fake.py (neue Datei, mit Zeilennummern, 95 Zeilen)

```
   1  #!/usr/bin/env python3
   2  """Attrappe fuer `opencode run --format json` (nur fuer tests/test_umsetzung_auto.py).
   3  
   4  Gibt einen JSON-Ereignisstrom im Format von opencode 1.19.3 aus (Spec-Paket umsetzung_auto §1) und
   5  kann ueber Umgebungsvariablen Dateien aendern, committen oder haengen.
   6  
   7  TECHNISCHE SPERRE (R04): Das Arbeitsverzeichnis (--dir bzw. cwd) muss im System-Temp-Ordner liegen.
   8  Sonst gibt die Attrappe nur eine Fehlermeldung aus und beendet sich mit Exit 3 – ohne irgendetwas zu
   9  schreiben oder zu committen. So kann ein falsch aufgebauter Test nie das echte Repo veraendern.
  10  
  11  Steuerung:
  12    FAKE_REASON     reason des letzten step_finish (Vorgabe: stop)
  13    FAKE_SLEEP      Sekunden warten, bevor das letzte Ereignis kommt (Timeout-Test)
  14    FAKE_EDIT       kommagetrennte Pfade (relativ zum Arbeitsverzeichnis), an die eine Zeile angehaengt wird
  15    FAKE_HANDOVER   Pfad des Handovers (relativ), an den eine Zeile angehaengt wird
  16    FAKE_COMMIT     "1": leerer git commit im Arbeitsverzeichnis
  17    FAKE_ABGELEHNT  "1": zusaetzlich ein abgelehnter Werkzeugaufruf im Strom
  18    FAKE_KAPUTT     "1": nur Zeilen, die kein JSON sind
  19    FAKE_ARGS       Pfad (im Temp-Ordner), in den die Argumente als JSON geschrieben werden
  20  """
  21  import json
  22  import os
  23  import subprocess
  24  import sys
  25  import tempfile
  26  import time
  27  
  28  
  29  def im_temp(pfad: str) -> bool:
  30      temp = os.path.realpath(tempfile.gettempdir())
  31      echt = os.path.realpath(pfad)
  32      return echt == temp or echt.startswith(temp + os.sep)
  33  
  34  
  35  def main(argv: list[str]) -> int:
  36      arbeitsordner = os.getcwd()
  37      if "--dir" in argv:
  38          i = argv.index("--dir")
  39          if i + 1 < len(argv):
  40              arbeitsordner = argv[i + 1]
  41      if not im_temp(arbeitsordner):
  42          print(f"opencode_fake: Arbeitsordner {arbeitsordner} liegt nicht im Temp-Ordner – Sperre, nichts getan.",
  43                file=sys.stderr)
  44          return 3
  45  
  46      args_ziel = os.environ.get("FAKE_ARGS")
  47      if args_ziel and im_temp(args_ziel):
  48          with open(args_ziel, "w", encoding="utf-8") as f:
  49              json.dump(argv, f, ensure_ascii=False)
  50  
  51      if os.environ.get("FAKE_KAPUTT") == "1":
  52          print("das ist kein JSON")
  53          print("{abgebrochen")
  54          return 0
  55  
  56      def aus(ereignis: dict) -> None:
  57          ereignis.setdefault("timestamp", int(time.time() * 1000))
  58          ereignis.setdefault("sessionID", "ses_fake")
  59          print(json.dumps(ereignis, ensure_ascii=False), flush=True)
  60  
  61      aus({"type": "step_start", "part": {"type": "step-start"}})
  62      aus({"type": "tool_use", "part": {"type": "tool", "tool": "bash", "state": {
  63          "status": "completed", "input": {"command": "python3 -m unittest -v tests/test_fake.py"},
  64          "output": "OK"}}})
  65      if os.environ.get("FAKE_ABGELEHNT") == "1":
  66          aus({"type": "tool_use", "part": {"type": "tool", "tool": "bash", "state": {
  67              "status": "error", "input": {"command": "git commit -m checkpoint"},
  68              "error": "The user has specified a rule which prevents you from using this specific tool call."}}})
  69  
  70      for rel in filter(None, (os.environ.get("FAKE_EDIT") or "").split(",")):
  71          ziel = os.path.join(arbeitsordner, rel.strip())
  72          os.makedirs(os.path.dirname(ziel), exist_ok=True)
  73          with open(ziel, "a", encoding="utf-8") as f:
  74              f.write("geaendert von opencode_fake\n")
  75      handover = os.environ.get("FAKE_HANDOVER")
  76      if handover:
  77          ziel = os.path.join(arbeitsordner, handover)
  78          os.makedirs(os.path.dirname(ziel), exist_ok=True)
  79          with open(ziel, "a", encoding="utf-8") as f:
  80              f.write("# Handover (Attrappe)\n")
  81      if os.environ.get("FAKE_COMMIT") == "1":
  82          subprocess.run(["git", "-C", arbeitsordner, "-c", "user.name=fake", "-c", "user.email=fake@fake",
  83                          "commit", "--allow-empty", "-qm", "checkpoint (Attrappe)"], check=False)
  84  
  85      aus({"type": "step_finish", "part": {"type": "step-finish", "reason": "tool-calls",
  86                                           "tokens": {"total": 100, "input": 90, "output": 10}}})
  87      time.sleep(float(os.environ.get("FAKE_SLEEP") or 0))
  88      aus({"type": "text", "part": {"type": "text", "text": "Umsetzung fertig (Attrappe)."}})
  89      aus({"type": "step_finish", "part": {"type": "step-finish", "reason": os.environ.get("FAKE_REASON", "stop"),
  90                                           "tokens": {"total": 50, "input": 40, "output": 10}}})
  91      return 0
  92  
  93  
  94  if __name__ == "__main__":
  95      sys.exit(main(sys.argv[1:]))
```

### tests/test_umsetzung_auto.py (neue Datei, mit Zeilennummern, 359 Zeilen)

```
   1  #!/usr/bin/env python3
   2  """Tests fuer kette.py umsetzung-auto (K10, spec_20261027_umsetzung_auto.md, T1–T21).
   3  
   4  Keine Aussenwirkung: Jeder Test baut ein eigenes temporaeres Git-Repo und biegt kette.ROOT/kette.PM
   5  dorthin um. Statt opencode laeuft die Attrappe role-split/kette/testdata/opencode_fake.py; sie
   6  verweigert jede Aktion ausserhalb des Temp-Ordners (technische Sperre). Zusaetzlich prueft jeder Test,
   7  dass HEAD und Arbeitsstand des echten Repos unveraendert bleiben. Kein echtes Modell, kein Netz.
   8  Neue Funktionen werden in den Methoden importiert (Gegenprobe).
   9  """
  10  import io
  11  import json
  12  import os
  13  import subprocess
  14  import sys
  15  import tempfile
  16  import time
  17  import unittest
  18  from contextlib import redirect_stderr, redirect_stdout
  19  from pathlib import Path
  20  from unittest import mock
  21  
  22  ECHT = Path(__file__).resolve().parent.parent
  23  sys.path.insert(0, str(ECHT / "role-split" / "kette"))
  24  import kette  # noqa: E402
  25  
  26  FAKE = ECHT / "role-split" / "kette" / "testdata" / "opencode_fake.py"
  27  DATUM = "20261027"
  28  HANDOVER = f"docs/projekt_management/handover_{DATUM}_g.md"
  29  SPEC = (
  30      "# Spec: g\n\n## Ziel\nTest.\n\n## Schreibbereich\n\n"
  31      "- `src/`\n- `role-split/kette/`\n- `docs/projekt_management/`\n\n"
  32      "## Testplan\n\n### T1: Erster\n- **Erwartung:** x\n"
  33  )
  34  
  35  
  36  def _echter_stand() -> tuple[str, str]:
  37      """HEAD und Status des echten Repos (Schutz gegen Tests, die dort etwas tun)."""
  38      def g(*a):
  39          return subprocess.run(["git", "-C", str(ECHT), *a], capture_output=True, text=True).stdout
  40      return g("rev-parse", "HEAD").strip(), g("status", "--porcelain")
  41  
  42  
  43  class Basis(unittest.TestCase):
  44      pruefen_code = 0
  45      pruefen_ausgabe = "Ran 1 test in 0.001s\n\nOK"
  46  
  47      def setUp(self):
  48          self.echt_vorher = _echter_stand()
  49          d = tempfile.TemporaryDirectory()
  50          self.addCleanup(d.cleanup)
  51          self.root = root = Path(d.name).resolve()
  52          self.pm = root / "docs" / "projekt_management"
  53          self.pm.mkdir(parents=True)
  54          (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC, encoding="utf-8")
  55          (self.pm / f"anforderung_{DATUM}_g.md").write_text("# Anforderung g\n\n## Aufgabe\n\n> X\n", encoding="utf-8")
  56          (self.pm / f"quellen_{DATUM}_g.md").write_text("# Quellen g\n", encoding="utf-8")
  57          (root / "src").mkdir()
  58          (root / "src" / "modul.py").write_text("X = 1\n", encoding="utf-8")
  59          (root / "role-split" / "kette").mkdir(parents=True)
  60          (root / "role-split" / "kette" / "kette.py").write_text("# Platzhalter\n", encoding="utf-8")
  61          (root / ".gitignore").write_text("role-split/results/\n", encoding="utf-8")
  62          self.git("init", "-q")
  63          self.git("add", ".")
  64          self.git("commit", "-qm", "Spec g")
  65          for name, wert in (("ROOT", root), ("PM", self.pm)):
  66              alt = getattr(kette, name)
  67              setattr(kette, name, wert)
  68              self.addCleanup(setattr, kette, name, alt)
  69          self.aufrufe_pruefen = 0
  70  
  71          def pruefen_attrappe(kurztitel, commit=None, timeout=300):
  72              self.aufrufe_pruefen += 1
  73              (self.pm / f"pruefung_{DATUM}_{kurztitel}.md").write_text(
  74                  f"# Pruefung {kurztitel}\n\n## unittest  (Exit {self.pruefen_code})\n\n```\n"
  75                  f"{self.pruefen_ausgabe}\n```\n", encoding="utf-8")
  76              return self.pruefen_code
  77          alt_pruefen = kette.pruefen
  78          kette.pruefen = pruefen_attrappe
  79          self.addCleanup(setattr, kette, "pruefen", alt_pruefen)
  80          self.argsdatei = root.parent / f"{root.name}_args.json"
  81          self.addCleanup(lambda: self.argsdatei.unlink(missing_ok=True))
  82          umgebung = {k: v for k, v in os.environ.items() if not k.startswith("FAKE_")}
  83          umgebung.update({"KETTE_OPENCODE": str(FAKE), "KETTE_UMSETZUNG_TIMEOUT": "60",
  84                           "FAKE_ARGS": str(self.argsdatei)})
  85          umgebung.pop("KETTE_UMSETZUNG_MODEL", None)
  86          p = mock.patch.dict(os.environ, umgebung, clear=True)
  87          p.start()
  88          self.addCleanup(p.stop)
  89          self.addCleanup(self._echt_unveraendert)
  90  
  91      def _echt_unveraendert(self):
  92          self.assertEqual(_echter_stand(), self.echt_vorher, "Test hat das echte Repo veraendert!")
  93  
  94      def git(self, *a) -> str:
  95          return subprocess.run(["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t", *a],
  96                                check=True, capture_output=True, text=True).stdout
  97  
  98      def lauf(self, kurztitel="g", nacharbeit=None, **fake):
  99          from kette import umsetzung_auto
 100          os.environ.update({k: str(v) for k, v in fake.items()})
 101          aus, fehler = io.StringIO(), io.StringIO()
 102          with redirect_stdout(aus), redirect_stderr(fehler):
 103              code = umsetzung_auto(kurztitel, nacharbeit)
 104          return code, aus.getvalue() + fehler.getvalue()
 105  
 106      def protokoll(self) -> str:
 107          p = self.pm / f"umsetzung_{DATUM}_g.md"
 108          return p.read_text(encoding="utf-8") if p.exists() else ""
 109  
 110      def gestartet(self) -> bool:
 111          return self.argsdatei.exists()
 112  
 113      def nacharbeit_vorbereiten(self, auftrag="Bitte A3 korrigieren: Feld X fehlt."):
 114          (self.root / HANDOVER).write_text("# Handover g\n\nErstumsetzung.\n", encoding="utf-8")
 115          datei = self.pm / f"nacharbeit_{DATUM}_g_1.md"
 116          datei.write_text(auftrag + "\n", encoding="utf-8")
 117          return datei
 118  
 119  
 120  class VorabTests(Basis):
 121  
 122      def test_t1_vorab_pruefung_kurztitel_ungueltig(self):
 123          """T1: Vorab-Prüfung – Kurztitel ungültig"""
 124          code, out = self.lauf("Ungültig-Titel")
 125          self.assertEqual(code, 2, out)
 126          self.assertIn("ungültig", out)
 127          self.assertFalse(self.gestartet())
 128  
 129      def test_t2_vorab_pruefung_kein_spec_commit(self):
 130          """T2: Vorab-Prüfung – kein Spec-Commit"""
 131          (self.pm / f"spec_{DATUM}_anders.md").write_text(SPEC, encoding="utf-8")
 132          self.git("add", ".")
 133          self.git("commit", "-qm", "foo")
 134          code, out = self.lauf("anders")
 135          self.assertEqual(code, 2, out)
 136          self.assertIn("Spec", out)
 137          self.assertFalse(self.gestartet())
 138  
 139      def test_t3_vorab_pruefung_spec_ohne_schreibbereich(self):
 140          """T3: Vorab-Prüfung – Spec ohne ## Schreibbereich"""
 141          (self.pm / f"spec_{DATUM}_ohne.md").write_text("# Spec: ohne\n\n## Ziel\nX\n", encoding="utf-8")
 142          self.git("add", ".")
 143          self.git("commit", "-qm", "Spec ohne")
 144          code, out = self.lauf("ohne")
 145          self.assertEqual(code, 2, out)
 146          self.assertIn("Schreibbereich", out)
 147          self.assertIn("ergaenzen", out)
 148          self.assertFalse(self.gestartet())
 149  
 150      def test_t4_vorab_pruefung_unrunder_arbeitsstand(self):
 151          """T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)"""
 152          (self.root / "src" / "modul.py").write_text("X = 2\n", encoding="utf-8")
 153          code, out = self.lauf()
 154          self.assertEqual(code, 2, out)
 155          self.assertIn("Arbeitsstand", out)
 156          self.assertIn("src/modul.py", out)
 157          self.assertFalse(self.gestartet())
 158  
 159      def test_t5_vorab_pruefung_opencode_fehlt(self):
 160          """T5: Vorab-Prüfung – opencode fehlt"""
 161          os.environ.pop("KETTE_OPENCODE")
 162          with mock.patch("kette.shutil.which", return_value=None):
 163              code, out = self.lauf()
 164          self.assertEqual(code, 2, out)
 165          self.assertIn("opencode", out)
 166          os.environ["KETTE_OPENCODE"] = str(self.root / "gibt_es_nicht.py")
 167          code, out = self.lauf()
 168          self.assertEqual(code, 2, out)
 169          self.assertFalse(self.gestartet())
 170  
 171      def test_t6_vorab_pruefung_modell_kein_llamacpp(self):
 172          """T6: Vorab-Prüfung – Modell kein llamacpp/"""
 173          code, out = self.lauf(KETTE_UMSETZUNG_MODEL="gedaechtnis/test-model")
 174          self.assertEqual(code, 2, out)
 175          self.assertIn("llamacpp", out)
 176          self.assertFalse(self.gestartet())
 177  
 178  
 179  class LaufTests(Basis):
 180  
 181      def test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen(self):
 182          """T7: Erfolgreicher Lauf, reason: stop, alle Prüfungen grün"""
 183          code, out = self.lauf(FAKE_EDIT="src/modul.py", FAKE_HANDOVER=HANDOVER)
 184          self.assertEqual(code, 0, out)
 185          self.assertEqual(self.aufrufe_pruefen, 1)
 186          zeile = self.protokoll()
 187          self.assertIn("reason: stop, rot: 0, pruefen: 0, art: erst, Exit: 0", zeile)
 188          roh = list((self.root / "role-split" / "results").glob(f"umsetzung_auto_{DATUM}_g_*.jsonl"))
 189          self.assertEqual(len(roh), 1)
 190          ereignisse = [json.loads(z) for z in roh[0].read_text(encoding="utf-8").splitlines() if z.strip()]
 191          self.assertGreaterEqual(len(ereignisse), 5)            # ganzer Strom, nicht nur die letzte Zeile
 192          argv = json.loads(self.argsdatei.read_text(encoding="utf-8"))
 193          self.assertEqual(argv[:7], ["run", "--format", "json", "--agent", "umsetzung_nacht", "--model",
 194                                      "llamacpp/unsloth/Qwen3.6-35B-A3B-MTP-GGUF:Q4_K_XL"])
 195          self.assertIn("--dir", argv)
 196          self.assertNotIn("--continue", argv)
 197          self.assertNotIn("--message", argv)
 198          self.assertIn(f"spec_{DATUM}_g.md", argv[-1])          # Prompt = letztes Positionsargument
 199          self.assertIn("LERNREGELN.md", argv[-1])
 200  
 201      def test_t8_lauf_ohne_reason_stop(self):
 202          """T8: Lauf ohne reason: stop"""
 203          code, out = self.lauf(FAKE_REASON="tool-calls", FAKE_HANDOVER=HANDOVER)
 204          self.assertEqual(code, 1, out)
 205          self.assertIn("nicht abgeschlossen", out)
 206          self.assertIn("(d) übersprungen", out)
 207          self.assertEqual(self.aufrufe_pruefen, 0)
 208          self.assertIn("reason: tool-calls, rot: –, pruefen: –, art: erst, Exit: 1", self.protokoll())
 209  
 210      def test_t9_timeout(self):
 211          """T9: Timeout"""
 212          start = time.monotonic()
 213          code, out = self.lauf(FAKE_SLEEP="5", KETTE_UMSETZUNG_TIMEOUT="1", FAKE_HANDOVER=HANDOVER)
 214          dauer = time.monotonic() - start
 215          self.assertEqual(code, 1, out)
 216          self.assertIn("Timeout", out)
 217          self.assertLess(dauer, 4.5, "Prozess wurde nicht nach dem Zeitlimit beendet")
 218          self.assertIn("reason: timeout", self.protokoll())
 219          self.assertEqual(self.aufrufe_pruefen, 0)
 220  
 221      def test_t10_selbst_commit(self):
 222          """T10: Selbst-Commit"""
 223          head = self.git("rev-parse", "HEAD").strip()
 224          code, out = self.lauf(FAKE_COMMIT="1", FAKE_HANDOVER=HANDOVER)
 225          self.assertEqual(code, 1, out)
 226          self.assertIn("Selbst-Commit", out)
 227          self.assertNotEqual(self.git("rev-parse", "HEAD").strip(), head)    # Commit bleibt, nichts zurueckgesetzt
 228  
 229      def test_t11_datei_ausserhalb_schreibbereich(self):
 230          """T11: Datei außerhalb Schreibbereich"""
 231          code, out = self.lauf(FAKE_EDIT="anderes/datei.txt", FAKE_HANDOVER=HANDOVER)
 232          self.assertEqual(code, 1, out)
 233          self.assertIn("anderes/datei.txt", out)
 234          self.assertIn("Schreibbereich verletzt", out)
 235          self.assertTrue((self.root / "anderes" / "datei.txt").exists())       # nichts zurueckgesetzt
 236  
 237      def test_t12_handover_fehlt(self):
 238          """T12: Handover fehlt"""
 239          code, out = self.lauf(FAKE_EDIT="src/modul.py")
 240          self.assertEqual(code, 1, out)
 241          self.assertIn("Handover", out)
 242  
 243      def test_t15_lebendsignal_werkzeugzeile(self):
 244          """T15: Lebendsignal – Werkzeugzeile"""
 245          code, out = self.lauf(FAKE_HANDOVER=HANDOVER, FAKE_ABGELEHNT="1")
 246          self.assertIn("] bash: python3 -m unittest -v tests/test_fake.py", out)
 247          self.assertIn("abgelehnt: bash: git commit -m checkpoint", out)
 248          self.assertIn("Abgelehnt: 1", self.protokoll())
 249  
 250      def test_t16_pruefen_rot(self):
 251          """T16: pruefen rot"""
 252          self.pruefen_code = 1
 253          self.pruefen_ausgabe = "Ran 3 tests in 0.01s\n\nFAILED (failures=1, errors=1)"
 254          code, out = self.lauf(FAKE_HANDOVER=HANDOVER)
 255          self.assertEqual(code, 1, out)
 256          self.assertIn("rot: 2, pruefen: 1, art: erst, Exit: 1", self.protokoll())
 257  
 258      def test_t18_schreibbereich_ordner_eintrag(self):
 259          """T18: Schreibbereich – Ordner-Eintrag"""
 260          code, out = self.lauf(FAKE_EDIT="role-split/kette/kette.py", FAKE_HANDOVER=HANDOVER)
 261          self.assertEqual(code, 0, out)
 262  
 263      def test_t19_schreibbereich_verbotene_dateien(self):
 264          """T19: Schreibbereich – Verbotene Dateien"""
 265          # docs/projekt_management/ liegt im Schreibbereich – die Spec selbst bleibt trotzdem verboten
 266          code, out = self.lauf(FAKE_EDIT=f"docs/projekt_management/spec_{DATUM}_g.md", FAKE_HANDOVER=HANDOVER)
 267          self.assertEqual(code, 1, out)
 268          self.assertIn(f"docs/projekt_management/spec_{DATUM}_g.md", out)
 269  
 270  
 271  class NacharbeitTests(Basis):
 272  
 273      def test_t13_nacharbeit_auftrag_aus_datei(self):
 274          """T13: Nacharbeit – Auftrag aus Datei"""
 275          auftrag = self.nacharbeit_vorbereiten()
 276          code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
 277          self.assertEqual(code, 0, out)
 278          prompt = json.loads(self.argsdatei.read_text(encoding="utf-8"))[-1]
 279          self.assertIn("Bitte A3 korrigieren: Feld X fehlt.", prompt)
 280          self.assertIn("„## Nachbesserung 1\"", prompt)
 281          self.assertIn("art: nb1", self.protokoll())
 282  
 283      def test_t14_nacharbeit_zwei_ohne_fortschritt(self):
 284          """T14: Nacharbeit – zwei ohne Fortschritt"""
 285          auftrag = self.nacharbeit_vorbereiten()
 286          z = "- **2026-10-27 10:00** – Modell: m, Dauer: 1 s, Tools: 1, Fehler: 0, Abgelehnt: 0, Tokens: 1, reason: stop, "
 287          (self.pm / f"umsetzung_{DATUM}_g.md").write_text(
 288              "# Protokoll\n\n" + z + "rot: 2, pruefen: 1, art: erst, Exit: 1\n"
 289              + z + "rot: 2, pruefen: 1, art: nb1, Exit: 1\n"
 290              + z + "rot: –, pruefen: –, art: nb2, Exit: 1\n", encoding="utf-8")
 291          code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
 292          self.assertEqual(code, 1, out)
 293          self.assertIn("Übergabe an Hawe", out)
 294          self.assertFalse(self.gestartet(), "trotz Halt-Regel gestartet")
 295  
 296      def test_t14_gegenfall_fortschritt_hebt_halt_auf(self):
 297          """T14: Nacharbeit – zwei ohne Fortschritt (Gegenfall: einer mit Fortschritt)"""
 298          from kette import _halt_noetig
 299          def z(rot, pr, art):
 300              return {"rot": rot, "pruefen": pr, "art": art}
 301          self.assertTrue(_halt_noetig([z("2", "1", "erst"), z("2", "1", "nb1"), z("3", "1", "nb2")]))
 302          self.assertFalse(_halt_noetig([z("2", "1", "erst"), z("1", "1", "nb1"), z("1", "1", "nb2")]))
 303          self.assertFalse(_halt_noetig([z("2", "1", "erst"), z("2", "1", "nb1")]))
 304          self.assertTrue(_halt_noetig([z("2", "1", "erst"), z("0", "2", "nb1"), z("0", "2", "nb2")]))  # pruefen schlechter
 305          self.assertTrue(_halt_noetig([z("–", "–", "erst"), z("–", "–", "nb1"), z("–", "–", "nb2")]))
 306  
 307      def test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen(self):
 308          """T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen"""
 309          auftrag = self.nacharbeit_vorbereiten()
 310          (self.root / "fremd.txt").write_text("x\n", encoding="utf-8")
 311          code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
 312          self.assertEqual(code, 2, out)
 313          self.assertIn("fremd.txt", out)
 314          self.assertFalse(self.gestartet())
 315          (self.root / "fremd.txt").unlink()
 316          (self.pm / f"spec_{DATUM}_g.md").write_text(SPEC + "\ngeaendert\n", encoding="utf-8")
 317          code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
 318          self.assertEqual(code, 2, out)                                          # Vorgabe offen -> nie erlaubt
 319          self.assertIn(f"spec_{DATUM}_g.md", out)
 320  
 321      def test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei(self):
 322          """T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)"""
 323          auftrag = self.nacharbeit_vorbereiten()
 324          (self.pm / f"pruefung_{DATUM}_g.md").write_text("# Pruefung\n", encoding="utf-8")
 325          (self.pm / f"verdict_{DATUM}_g_qwen36-35b.md").write_text("# Verdikt\n", encoding="utf-8")
 326          (self.root / "role-split" / "results").mkdir(parents=True)
 327          (self.root / "role-split" / "results" / "alt.jsonl").write_text("{}\n", encoding="utf-8")
 328          code, out = self.lauf(nacharbeit=str(auftrag), FAKE_HANDOVER=HANDOVER)
 329          self.assertNotEqual(code, 2, out)
 330          self.assertTrue(self.gestartet())
 331          self.assertEqual(code, 0, out)
 332  
 333  
 334  class EinstiegTests(Basis):
 335  
 336      def test_t20_main_gleicher_exit_wie_funktionsaufruf(self):
 337          """T20: main() – gleicher Exit wie Funktionsaufruf"""
 338          os.environ.update({"FAKE_HANDOVER": HANDOVER})
 339          aus = io.StringIO()
 340          with redirect_stdout(aus), redirect_stderr(aus):
 341              code = kette.main(["umsetzung-auto", "g"])
 342          self.assertEqual(code, 0, aus.getvalue())
 343          self.assertIn("art: erst, Exit: 0", self.protokoll())
 344          # Fehlerfall ueber denselben Weg: ungueltiger Kurztitel -> 2 wie T1
 345          with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
 346              self.assertEqual(kette.main(["umsetzung-auto", "Ungültig-Titel"]), 2)
 347  
 348      def test_t20_attrappe_sperrt_echtes_repo(self):
 349          """T20: main() – gleicher Exit wie Funktionsaufruf (Absicherung: Attrappe sperrt das echte Repo)"""
 350          r = subprocess.run([sys.executable, str(FAKE), "run", "--dir", str(ECHT), "x"],
 351                             capture_output=True, text=True, timeout=30,
 352                             env=dict(os.environ, FAKE_COMMIT="1", FAKE_EDIT="sperrtest.txt"))
 353          self.assertEqual(r.returncode, 3, r.stderr)
 354          self.assertIn("Sperre", r.stderr)
 355          self.assertFalse((ECHT / "sperrtest.txt").exists())
 356  
 357  
 358  if __name__ == "__main__":
 359      unittest.main()
```

## 4. Testskript `tests/test_umsetzung_auto.py` (Methoden)

- `test_t1_vorab_pruefung_kurztitel_ungueltig` (Zeile 122): T1: Vorab-Prüfung – Kurztitel ungültig
- `test_t2_vorab_pruefung_kein_spec_commit` (Zeile 129): T2: Vorab-Prüfung – kein Spec-Commit
- `test_t3_vorab_pruefung_spec_ohne_schreibbereich` (Zeile 139): T3: Vorab-Prüfung – Spec ohne ## Schreibbereich
- `test_t4_vorab_pruefung_unrunder_arbeitsstand` (Zeile 150): T4: Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)
- `test_t5_vorab_pruefung_opencode_fehlt` (Zeile 159): T5: Vorab-Prüfung – opencode fehlt
- `test_t6_vorab_pruefung_modell_kein_llamacpp` (Zeile 171): T6: Vorab-Prüfung – Modell kein llamacpp/
- `test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen` (Zeile 181): T7: Erfolgreicher Lauf, reason: stop, alle Prüfungen grün
- `test_t8_lauf_ohne_reason_stop` (Zeile 201): T8: Lauf ohne reason: stop
- `test_t9_timeout` (Zeile 210): T9: Timeout
- `test_t10_selbst_commit` (Zeile 221): T10: Selbst-Commit
- `test_t11_datei_ausserhalb_schreibbereich` (Zeile 229): T11: Datei außerhalb Schreibbereich
- `test_t12_handover_fehlt` (Zeile 237): T12: Handover fehlt
- `test_t15_lebendsignal_werkzeugzeile` (Zeile 243): T15: Lebendsignal – Werkzeugzeile
- `test_t16_pruefen_rot` (Zeile 250): T16: pruefen rot
- `test_t18_schreibbereich_ordner_eintrag` (Zeile 258): T18: Schreibbereich – Ordner-Eintrag
- `test_t19_schreibbereich_verbotene_dateien` (Zeile 263): T19: Schreibbereich – Verbotene Dateien
- `test_t13_nacharbeit_auftrag_aus_datei` (Zeile 273): T13: Nacharbeit – Auftrag aus Datei
- `test_t14_nacharbeit_zwei_ohne_fortschritt` (Zeile 283): T14: Nacharbeit – zwei ohne Fortschritt
- `test_t14_gegenfall_fortschritt_hebt_halt_auf` (Zeile 296): T14: Nacharbeit – zwei ohne Fortschritt (Gegenfall: einer mit Fortschritt)
- `test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen` (Zeile 307): T17: Vorab-Prüfung – Nacharbeit mit fremden Änderungen
- `test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei` (Zeile 321): T21: Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)
- `test_t20_main_gleicher_exit_wie_funktionsaufruf` (Zeile 336): T20: main() – gleicher Exit wie Funktionsaufruf
- `test_t20_attrappe_sperrt_echtes_repo` (Zeile 348): T20: main() – gleicher Exit wie Funktionsaufruf (Absicherung: Attrappe sperrt das echte Repo)

## 5. Handover – nur Abweichungen, Annahmen, offene und nicht getestete Punkte

## Abweichungen von der Spec

- Prompt enthält zusätzlich eine Leseregel (erst suchen, dann Zeilenbereiche lesen, große Dateien nur gezielt editieren). Anlass: Der 35B-Lauf hat `kette.py` ganz gelesen und den Kontext erschöpft.
- Leerer Abschnitt `## Schreibbereich` (Überschrift ohne Einträge) gilt wie fehlend → Exit 2.
- `FAKE_UNITTEST` der Attrappe nicht gebaut: „rot“ kommt aus der `pruefung_*.md`, die `pruefen` schreibt; im Test wird `kette.pruefen` durch einen Stub ersetzt, der diese Datei schreibt.
- T14 und T20 haben je eine zusätzliche Methode (`test_t14_gegenfall_fortschritt_hebt_halt_auf`, `test_t20_attrappe_sperrt_echtes_repo`), damit die Halt-Regel nicht immer greift bzw. die Attrappen-Sperre selbst geprüft ist.
- T13 prüft, dass der Nacharbeitsauftrag im Prompt steht (über `FAKE_ARGS`), nicht nur, dass die Datei existiert.
- Signatur `umsetzung_auto(kurztitel, nacharbeit=None)` statt Argument-Objekt.
- `opencode run` bekommt zusätzlich `--title`, damit Läufe in OpenCode wiederzufinden sind.
- Startfehler (Programm lässt sich nicht starten) werden abgefangen und als Befund gemeldet statt als Traceback.

## Annahmen

- `step_finish` mit `reason: stop` als letztes Ereignis bedeutet „Modell hat selbst beendet“ (aus Probe P1/P2, `claude/k10-opencode-probe.md`).
- Die Attrappe gibt das Ereignisformat von opencode 1.19.3 wieder, so wie es die Proben gezeigt haben; Abweichungen späterer Versionen sind nicht abgedeckt.

## Nicht getestet

- Kein echter `opencode run`-Lauf mit Modell: alle Tests laufen gegen die Attrappe. Ob die deny-Regeln im Agenten im echten Lauf greifen und ob der Ereignisstrom einer echten Sitzung so ausgewertet wird wie erwartet, zeigt erst die Abnahme.
- Verhalten bei mehr als zwei Nacharbeiten nur über die Protokoll-Auswertung geprüft, nicht über echte Folgeläufe.

## Offene Punkte / bekannte Schwächen

- Die Schreibbereichs-Prüfung erkennt Änderungen über Snapshots von `git status`; eine Datei, die im Lauf geändert und exakt zurückgesetzt wird, bleibt unsichtbar (gewollt, aber zu wissen).
- Vermutung: Der Selbst-Commit aus K9 stammt aus Schritt 2 des Agenten `umsetzung`, nicht aus `umsetzung_nacht`; nicht geprüft.
- `opencode.db` ist 1,6 GB groß – für die Vormerkungen.

## 6. Maschinelle Pruefung (Kurzfassung)

- Kurz: abgleich: ok | unittest: ok | gegenprobe: ok

#### abgleich
```
Spec:     spec_20261027_umsetzung_auto.md  (21 Tests)
Handover: handover_20261027_umsetzung_auto.md

  ok        T1    Vorab-Prüfung – Kurztitel ungültig
  ok        T2    Vorab-Prüfung – kein Spec-Commit
  ok        T3    Vorab-Prüfung – Spec ohne `## Schreibbereich
  ok        T4    Vorab-Prüfung – unrunder Arbeitsstand (erster Lauf)
  ok        T5    Vorab-Prüfung – `opencode` fehlt
  ok        T6    Vorab-Prüfung – Modell kein `llamacpp/
  ok        T7    Erfolgreicher Lauf, `reason: stop`, alle Prüfungen grün
  ok        T8    Lauf ohne `reason: stop
  ok        T9    Timeout
  ok        T10   Selbst-Commit
  ok        T11   Datei außerhalb Schreibbereich
  ok        T12   Handover fehlt
  ok        T13   Nacharbeit – Auftrag aus Datei
  ok        T14   Nacharbeit – zwei ohne Fortschritt
  ok        T15   Lebendsignal – Werkzeugzeile
  ok        T16   pruefen` rot
  ok        T17   Vorab-Prüfung – Nacharbeit mit fremden Änderungen
  ok        T18   Schreibbereich – Ordner-Eintrag
  ok        T19   Schreibbereich – Verbotene Dateien
  ok        T20   main() – gleicher Exit wie Funktionsaufruf
  ok        T21   Vorab-Prüfung – Nacharbeit mit offener Kettendatei (kein Exit 2)

  Testskript tests/test_umsetzung_auto.py: alle 21 Tests als Methode vorhanden
  Selbst ausfuehren: python3 -m unittest -v tests/test_umsetzung_auto.py

Keine Abweichung.
```

#### gegenprobe
```
Gegenprobe gegen 3700da7: 23 Tests, je Datei einzeln zurueckgesetzt

  role-split/kette/kette.py: 22 Test(s) rot
  role-split/kette/testdata/opencode_fake.py: 16 Test(s) rot

  rot   test_t10_selbst_commit  <- kette.py, opencode_fake.py
  rot   test_t11_datei_ausserhalb_schreibbereich  <- kette.py, opencode_fake.py
  rot   test_t12_handover_fehlt  <- kette.py, opencode_fake.py
  rot   test_t13_nacharbeit_auftrag_aus_datei  <- kette.py, opencode_fake.py
  rot   test_t14_gegenfall_fortschritt_hebt_halt_auf  <- kette.py
  rot   test_t14_nacharbeit_zwei_ohne_fortschritt  <- kette.py, opencode_fake.py
  rot   test_t15_lebendsignal_werkzeugzeile  <- kette.py, opencode_fake.py
  rot   test_t16_pruefen_rot  <- kette.py, opencode_fake.py
  rot   test_t17_vorab_pruefung_nacharbeit_mit_fremden_aenderungen  <- kette.py
  rot   test_t18_schreibbereich_ordner_eintrag  <- kette.py, opencode_fake.py
  rot   test_t19_schreibbereich_verbotene_dateien  <- kette.py, opencode_fake.py
  rot   test_t1_vorab_pruefung_kurztitel_ungueltig  <- kette.py
  rot   test_t20_attrappe_sperrt_echtes_repo  <- opencode_fake.py
  rot   test_t20_main_gleicher_exit_wie_funktionsaufruf  <- kette.py, opencode_fake.py
  rot   test_t21_vorab_pruefung_nacharbeit_mit_offener_kettendatei  <- kette.py, opencode_fake.py
  rot   test_t2_vorab_pruefung_kein_spec_commit  <- kette.py
  rot   test_t3_vorab_pruefung_spec_ohne_schreibbereich  <- kette.py
  rot   test_t4_vorab_pruefung_unrunder_arbeitsstand  <- kette.py
  rot   test_t5_vorab_pruefung_opencode_fehlt  <- kette.py
  rot   test_t6_vorab_pruefung_modell_kein_llamacpp  <- kette.py, opencode_fake.py
  rot   test_t7_erfolgreicher_lauf_reason_stop_alle_pruefungen_gruen  <- kette.py, opencode_fake.py
  rot   test_t8_lauf_ohne_reason_stop  <- kette.py, opencode_fake.py
  rot   test_t9_timeout  <- kette.py, opencode_fake.py

23 von 23 Tests werden durch eine einzelne alte Datei rot. Aktueller Stand ist wiederhergestellt.
```

#### unittest (Zusammenfassung)
Ran 23 tests in 3.762s
OK
