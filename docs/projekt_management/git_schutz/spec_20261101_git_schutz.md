# Spec: git_schutz

- **Datum:** 2026-11-01
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette_lauf` aus der Chat-UI
- **Betroffene Dateien:** `role-split/kette/kette.py` (nur `umsetzung_auto` und drei neue Hilfsfunktionen)

## Ziel

`umsetzung-auto` merkt, wenn der Umsetzer im Git-Verzeichnis `config`, `hooks/` oder `info/` ändert, und meldet das laut (Befund, Exit 1). Anlass 27.10. (K10-Lauf): Der Umsetzer setzte `user.name=Test` in `.git/config`; ~40 Commits liefen danach als „Test“. Die Schreibbereich-Prüfung sah es nicht, weil sie auf `git status` beruht und `git status` das Git-Verzeichnis nie zeigt. Zusätzlich: Macht der Umsetzer `.git/config` unlesbar, stürzt `umsetzung_auto` heute mit Traceback ab (`_git("rev-parse", "HEAD")` mit `check=True`) – ohne Protokollzeile. Das wird zu einem Befund.

## Nicht-Ziele

- **`tests/test_git_schutz.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- **Nichts zurücksetzen.** Wie bei Selbst-Commit und Schreibbereich: nur melden, Hawe entscheidet.
- Keine Änderung an `role-split/kette/testdata/opencode_fake.py` (die Vorgabe-Tests bringen einen eigenen Wrapper mit), an `automatik.py`, an den MCP-Werkzeugen oder an der Prompt-Vorlage.
- Kein Schutz der globalen Git-Konfiguration (`~/.gitconfig`) und keine Änderung der Umgebungsvariablen des Umsetzer-Prozesses (siehe „Abweichende Meinung“).
- Alle bestehenden Tests bleiben grün, besonders `tests/test_umsetzung_auto.py` (33 Tests).

## Schreibbereich

- `role-split/kette/kette.py`

## Vorgabe-Tests

- `tests/test_git_schutz.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Nichts. Die neuen Funktionen lesen nur (`git rev-parse`, Dateien lesen, `stat`).
- **Technische Sperre für Tests:** T1–T7 bauen ein eigenes Temp-Git-Repo und biegen `kette.ROOT`/`kette.PM` dorthin um. Statt opencode läuft ein Wrapper, der im Temp-Ordner geschrieben wird, nur im Temp-Ordner handelt und dann die vorhandene Attrappe `opencode_fake.py` startet (beide mit Temp-Sperre). Jeder Test prüft danach, dass HEAD, Arbeitsstand **und `.git/config`** des echten Repos unverändert sind. T8 ruft die neuen Funktionen am echten Repo nur lesend auf.

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `role-split/kette/kette.py` | `kette.py umsetzung-auto <kt> [--nacharbeit …]`, aus `automatik.lauf` bzw. `kette_lauf` | T1–T7 (über `umsetzung_auto`) |
| `role-split/kette/kette.py` | als Modul (`GIT_SCHUTZ`, `_git_verzeichnis`, `_git_schutz`) | T7, T8 |

## Quellen

- `role-split/kette/kette.py` Zeilen 1619–1626 – Konstanten der Umsetzung; `GIT_SCHUTZ` kommt direkt hinter `ABGELEHNT_TEXTE`
- `role-split/kette/kette.py` def _git – wirft bei git-Fehler (`check=True`), Ursache des Absturzes
- `role-split/kette/kette.py` def _stand – Muster für Prüfsummen (sha256)
- `role-split/kette/kette.py` def _in_diesem_lauf – Vergleich zweier Schnappschüsse, wird wiederverwendet
- `role-split/kette/kette.py` def umsetzung_auto – Einbaustelle (A7-Schnappschüsse, Befunde (a)/(b), (c)/(d), Protokoll, Schlussausgabe)

## Anforderungen

### A1: Git-Verzeichnis bestimmen
- **Anforderung:** Konstante `GIT_SCHUTZ = ("config", "hooks", "info")` direkt hinter `ABGELEHNT_TEXTE`. Funktion `_git_verzeichnis() -> Path | None`: `subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--git-common-dir"], capture_output=True, text=True)`; Exit ≠ 0 oder leere Ausgabe → `None`. Sonst den Pfad absolut machen (relativ → `ROOT / pfad`) und `.resolve()` zurückgeben. `ROOT` wird zur Aufrufzeit gelesen. Im verknüpften Worktree ist das das `.git` des Hauptrepos (dort liegen `config` und `hooks/`).
- **Stelle:** `role-split/kette/kette.py`, neue Funktion direkt vor `PROTOKOLL_RE`.
- **Akzeptanz:** T7, T8.

### A2: Schnappschuss der geschützten Teile
- **Anforderung:** `_git_schutz(gitdir: Path) -> dict[str, str]`. Für jeden Namen aus `GIT_SCHUTZ`: Ist `gitdir/<name>` ein Symlink oder eine Datei → ein Eintrag unter `<name>`. Ist es ein Ordner → rekursiv (`os.walk`, Symlinks nicht verfolgen) je Datei **und je Symlink** (auch Symlink auf Ordner oder ins Leere) ein Eintrag; Ordner selbst sind keine Einträge. Fehlt es → kein Eintrag. Schlüssel = Pfad relativ zu `gitdir` in POSIX-Form (`config`, `hooks/pre-commit`, `hooks/tief/unten/hook`). Wert:
  - Symlink → `link:` + `os.readlink(p)`
  - Datei → sha256 (hex) des Inhalts, bei gesetztem Ausführbar-Bit (`st_mode & 0o111`) mit Anhang `:x`
  - `OSError` beim Lesen → `<unlesbar>`
  Nur exakte Namen: `hooks_alt/` oder `description` gehören nicht dazu. Die Funktion schreibt nichts.
- **Stelle:** neue Funktion (ggf. mit kleiner Hilfsfunktion für einen Eintrag) direkt hinter `_git_verzeichnis`.
- **Akzeptanz:** T3, T4, T5, T8.

### A3: Einbau in `umsetzung_auto`
- **Anforderung:**
  1. Vor dem Start, unmittelbar vor `head_vor = …` (Abschnitt „A7 Schnappschuss VOR dem Start“): `gitdir = _git_verzeichnis()`; `None` → `nein("Git-Verzeichnis nicht gefunden (git rev-parse --git-common-dir) – kein Lauf.")` (Exit 2, opencode startet nicht). Sonst `schutz_vor = _git_schutz(gitdir)`.
  2. **Sofort nach `_lauf`**, als erste Anweisung von „A7 Schnappschuss SOFORT nach dem Lauf“: `schutz = _in_diesem_lauf(schutz_vor, _git_schutz(gitdir))` – mit dem **vorher** bestimmten `gitdir` (nicht neu bestimmen; bei kaputter `config` ginge das nicht).
  3. Gilt für Erstlauf und Nacharbeit gleich.
  4. Befund direkt nach dem Selbst-Commit-Befund (a), wenn `schutz` nicht leer ist – genau dieser Text, Einträge in der Reihenfolge von `schutz` (sortiert):
     ```
     Git-Schutz verletzt – .git/ in diesem Lauf geändert (nichts zurückgesetzt):
       .git/<rel> (<neu|weg|geaendert>)
     ```
     Der Befund ändert nichts am Ablauf: (c)/(d) laufen wie bisher (wenn git benutzbar ist, A4), Exit wird 1, weil ein Befund vorliegt.
  5. Protokoll: Nach den bisherigen Unterzeilen (Tokens, Fehler) je Eintrag aus `schutz` eine Unterzeile `  - git-schutz: .git/<rel> (<art>)`. Die Laufzeile selbst bleibt unverändert (`_protokoll`/`automatik` lesen sie).
  6. Schlussausgabe: direkt nach der Zeile `In diesem Lauf geändert: …` die Zeile `Git-Schutz: unverändert` bzw. `Git-Schutz: geändert (<Anzahl Einträge>)`.
- **Stelle:** `def umsetzung_auto`
- **Akzeptanz:** T1–T5, T7.

### A4: git nach dem Lauf nicht benutzbar – kein Absturz
- **Anforderung:** `head_nach` nicht mehr über `_git(...)` (wirft), sondern `subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)`; Exit ≠ 0 → `head_nach = None`. Dann statt des Selbst-Commit-Befunds der Befund `git nach dem Lauf nicht benutzbar (git rev-parse HEAD: <erste Zeile von stderr, sonst ?>) – (c)/(d) übersprungen.`; kein Selbst-Commit-Befund. (c)/(d) laufen nur, wenn der Lauf abgeschlossen **und** `head_nach` nicht `None` ist; sonst die bestehende Ausgabe `(c) übersprungen (…)` / `(d) übersprungen (…)` mit dem Grund `Lauf nicht abgeschlossen` bzw. `git nicht benutzbar`. Protokollzeile wird trotzdem geschrieben (`rot: –, pruefen: –`).
- **Stelle:** `def umsetzung_auto`, Abschnitte A7 nach dem Lauf, (a), (c)/(d).
- **Akzeptanz:** T6.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| A3 | `git config user.name Test` im Lauf | nichts von kette.py | Befund, Exit 1, Protokoll-Unterzeile, `user.name` bleibt `Test` | T2 |
| A2 | neuer Hook / Hook nur `chmod +x` / Symlink ins Leere / Hook gelöscht | – | je Eintrag `neu` / `geaendert` / `neu` / `weg` | T3 |
| A2 | Datei in Unterordner von `hooks/`, `info/exclude` geändert | – | gemeldet | T4 |
| A3 | Nacharbeit-Lauf ändert `.git/info/` | Handover, Nacharbeitsdatei | gleicher Befund, `art: nb1, Exit: 1` | T4 |
| A2 | `.git/description`, `.git/hooks_alt/…`, Commit (logs/refs/index) | – | **kein** Git-Schutz-Befund | T5 |
| A4 | `.git/config` unlesbar gemacht | – | kein Traceback, zwei Befunde, (c)/(d) übersprungen, Protokollzeile | T6 |
| A1 | Git-Verzeichnis nicht bestimmbar | nichts | Exit 2, opencode startet nicht | T7 |
| A1 | Lauf in verknüpftem Worktree | – | `config`/`hooks/` des Hauptrepos | T7 |
| A3 | Umsetzer ändert `.git/` und stellt es vor Laufende wieder her | – | nicht erkannt (nur Vorher/Nachher) | – (bewusst offen) |
| – | `git config --global …` | – | nicht erkannt (Nicht-Ziel) | – (bewusst offen) |

## Testplan

Die Tests stehen in `tests/test_git_schutz.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Vorab 8/8 rot (6 failures, 2 errors); gegen die Referenz 8/8 grün, dreimal stabil (< 1 s). Mutationsprüfung der Referenz: 24 von 24 gefangen (u. a. Schutzbereich zu eng/zu weit, Präfix statt Name, Ausführbar-Bit, Symlink verfolgt, nicht rekursiv, nur Erstlauf, `--git-dir` statt `--git-common-dir`, zurücksetzen, Schnappschuss zu spät, Absturz bei kaputter config).

### T1: Unverändertes Git-Verzeichnis – Lauf OK, Zeile „Git-Schutz: unverändert“
- **Prüft:** A3.6
- **Aufbau:** Attrappe ändert nur `src/modul.py` und den Handover.
- **Erwartung:** Exit 0, Zeile `Git-Schutz: unverändert`, kein Befund, keine `git-schutz:`-Unterzeile, `pruefen` einmal.
- **Warum misst der Test das Richtige?** Ein normaler Lauf (`git status` frischt dabei den Index auf) darf keinen Fehlalarm geben.
- **Gegenprobe:** alter Stand → rot (Zeile fehlt).

### T2: git config user.name Test (Fall vom 27.10.) – lauter Befund, Exit 1, nichts zurückgesetzt
- **Prüft:** A3.2, A3.4, A3.5, A3.6
- **Aufbau:** Wrapper führt `git config user.name Test` im Temp-Repo aus.
- **Erwartung:** Exit 1, Befund mit `  .git/config (geaendert)`, `Git-Schutz: geändert (1)`, Protokoll `art: erst, Exit: 1` plus Unterzeile, `user.name` ist weiter `Test`, `pruefen` lief, kein Schreibbereich-Befund.
- **Warum misst der Test das Richtige?** Genau der Vorfall vom 27.10.
- **Gegenprobe:** alter Stand → rot (Exit 0).

### T3: hooks/ – neuer Hook, nur ausführbar gemacht, Symlink, gelöscht
- **Prüft:** A2, A3.4, A3.5
- **Aufbau:** neuer `hooks/pre-commit`; `pre-commit.sample` nur `chmod 755` (Inhalt gleich); Symlink `hooks/post-merge` ins Leere; `pre-push.sample` gelöscht.
- **Erwartung:** genau vier Einträge, sortiert, mit `neu`/`geaendert`/`neu`/`weg`; vier Unterzeilen im Protokoll.
- **Warum misst der Test das Richtige?** Ein Hook wird schon durch das Ausführbar-Bit aktiv; ein Symlink zeigt auf fremden Code.
- **Gegenprobe:** alter Stand → rot.

### T4: info/ und Unterordner – auch im Nacharbeit-Lauf
- **Prüft:** A2 (rekursiv), A3.3
- **Aufbau:** Nacharbeit; Wrapper ändert `info/exclude` und legt `hooks/tief/unten/hook` an.
- **Erwartung:** beide Einträge, `Git-Schutz: geändert (2)` (Ordner zählen nicht), `art: nb1, Exit: 1`.
- **Warum misst der Test das Richtige?** `info/exclude` blendet Dateien aus `git status` aus – damit fiele eine Änderung aus der Schreibbereich-Prüfung.
- **Gegenprobe:** alter Stand → rot.

### T5: Änderungen in .git/ außerhalb von config/hooks/info – kein Git-Schutz-Befund
- **Prüft:** A2 (nur exakte Namen)
- **Aufbau:** `.git/description` und `.git/hooks_alt/notiz` ändern; danach (nach Zwischencommit) Lauf mit Selbst-Commit.
- **Erwartung:** erster Lauf Exit 0, `unverändert`; zweiter Lauf nur Selbst-Commit-Befund, `unverändert`.
- **Warum misst der Test das Richtige?** Ein zu weiter Schutz (ganzes `.git/`) meldete jeden Commit und jeden `git status`.
- **Gegenprobe:** alter Stand → rot (Zeile fehlt).

### T6: config kaputt – kein Absturz, Befund, Protokollzeile, (c)/(d) übersprungen
- **Prüft:** A4, A3.2
- **Aufbau:** Wrapper hängt `[kaputt` an `.git/config`.
- **Erwartung:** keine Ausnahme, Exit 1, Git-Schutz-Befund für `config`, Befund `git nach dem Lauf nicht benutzbar (git rev-parse HEAD: …`, `(c) übersprungen (git nicht benutzbar)`, `pruefen` nicht aufgerufen, kein Selbst-Commit-Befund, Protokoll mit `rot: –, pruefen: –, art: erst, Exit: 1`.
- **Warum misst der Test das Richtige?** Heute endet dieser Fall in einem Traceback ohne Protokoll – der lauteste Fall wäre der stillste.
- **Gegenprobe:** alter Stand → rot (`CalledProcessError`).

### T7: Git-Verzeichnis – Worktree nutzt das des Hauptrepos; nicht bestimmbar → Exit 2, kein Start
- **Prüft:** A1, A3.1
- **Aufbau:** `_git_verzeichnis()` im Temp-Repo, in einem `git worktree add`-Ordner, in einem Ordner ohne Repo; Lauf mit `_git_verzeichnis` → `None`.
- **Erwartung:** zweimal `<temp>/.git` (aufgelöst), einmal `None`; Lauf Exit 2, Meldung mit „Git-Verzeichnis“, opencode nicht gestartet.
- **Warum misst der Test das Richtige?** Im Worktree ist `.git` eine Datei; `--git-dir` zeigte auf `.git/worktrees/<name>` ohne `config`/`hooks`.
- **Gegenprobe:** alter Stand → rot (ImportError).

### T8: Standardwerte im echten Pfad – GIT_SCHUTZ, echtes Git-Verzeichnis, nur lesend
- **Prüft:** A1, A2 (R58: Tests biegen ROOT um, also Standardwerte am echten Pfad prüfen)
- **Aufbau:** `GIT_SCHUTZ`; `_git_verzeichnis()` mit echtem `ROOT`; `_git_schutz` darauf zweimal.
- **Erwartung:** `("config", "hooks", "info")`; Pfad = `git rev-parse --path-format=absolute --git-common-dir`; `config` als 64-stelliger Hash, nur Schlüssel `config`, `hooks/…`, `info/…`; zweiter Aufruf gleich.
- **Warum misst der Test das Richtige?** Bei `mcp_kette` waren genau umgebogene Standardwerte falsch, und kein Test sah es.
- **Gegenprobe:** alter Stand → rot (ImportError).

## Offene Fragen

- Keine

## Abweichende Meinung

- **Globale Git-Konfiguration:** `git config --global user.name Test` träfe `~/.gitconfig` – außerhalb des Repos, also weder von dieser Kette noch von der Schreibbereich-Prüfung gesehen. Ein Schutz bräuchte einen Schnappschuss außerhalb von `ROOT` (Datei in `$HOME`, ggf. `XDG_CONFIG_HOME`). Vorschlag: eigene kleine Folgekette oder eine opencode-Regel, die `git config` für den Umsetzer ganz verbietet.
- **Umgebungsvariablen:** Den Umsetzer-Prozess ohne `GIT_*`-Variablen zu starten hätte den Vorfall vom 27.10. nicht verhindert (`git config` schreibt ohne sie in `.git/config`). Deshalb hier nicht.
- **Vorher/Nachher-Vergleich** erkennt keine Änderung, die der Umsetzer vor Laufende selbst zurücknimmt (z. B. Hook kurz anlegen, ausführen, löschen). Das bräuchte eine Sperre zur Laufzeit (opencode-Regel), keine Prüfsumme.
