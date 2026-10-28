# Spec: mcp_kette

- **Datum:** 2026-10-28
- **Modell:** Claude (Spec, Vorgabe-Tests, Referenzlösung); Umsetzung durch den lokalen Umsetzer per `kette.py lauf`
- **Betroffene Dateien:** neu `mcp-server/kette_werkzeuge.py`; in `mcp-server/lab_mcp_server.py` ein Block vor „Start“ und eine Banner-Zeile

## Ziel

Stufe 4: Die Kette lässt sich aus der Chat-UI (8092) bedienen – über vier feste MCP-Werkzeuge `kette_status`, `kette_lauf`, `kette_ergebnis`, `kette_commit`, ohne freie Shell und ohne Pfade als Parameter. Weil die Web-UI Werkzeugaufrufe nach ~5 min aktiv abbricht (Messung 28.10., `experiments/stufe4_probe/README.md`), startet `kette_lauf` einen **eigenen Prozess** und kehrt sofort zurück.

## Nicht-Ziele

- **`tests/test_mcp_kette.py` ist Vorgabe und wird nicht geändert – keine Zeile.**
- Kein Werkzeug `kette_einsortieren`: Seit K13b legt `anforderung` den Ordner an, neue Ketten liegen schon richtig (bewusst gestrichen, Größe R43).
- Kein Abbrechen eines laufenden Laufs, keine Warteschlange, kein zweiter gleichzeitiger Lauf.
- Keine Änderung an `kette.py`, `automatik.py`, `start_rollen.command`, Doku. Den Schalter `MCP_ALLOW_KETTE=1` in `start_rollen.command` setzt Hawe nach der Abnahme von Hand.
- Kein `shell=True`, kein `os.system`; jeder Prozess per argv-Liste.

## Schreibbereich

- `mcp-server/kette_werkzeuge.py`
- `mcp-server/lab_mcp_server.py`

## Vorgabe-Tests

- `tests/test_mcp_kette.py`

## Außenwirkung und Sperre

- **Was kann die Aufgabe außerhalb des Repos auslösen?** Im Betrieb: `kette_lauf` startet `kette.py lauf` (Umsetzer, Review über den Router), `kette_commit` committet im Repo. Laufdateien unter `~/.lab_mcp/kette/` (außerhalb des Repos, damit `git status` sauber bleibt).
- **Technische Sperre für Tests:** Jeder Test arbeitet in `tempfile.TemporaryDirectory()` und biegt `kette_werkzeuge.ROOT`, `KETTE_PY` (Ersatzskript, das nur schläft und druckt) und `LAUF_DIR` um; git nur in einem Wegwerf-Repo im Temp-Verzeichnis. Die Werkzeuge sind im Server **standardmäßig aus** (`MCP_ALLOW_KETTE`).

## Einstiegspunkte

| Datei | Wie gestartet | Test |
|---|---|---|
| `mcp-server/lab_mcp_server.py` | vom Launcher; importiert `kette_werkzeuge` und ruft `registrieren(mcp)` nur bei `MCP_ALLOW_KETTE=1` | T8 |
| `mcp-server/kette_werkzeuge.py` | als Modul (Werkzeuge, `registrieren`, `laufender`) | T1–T8 |
| `mcp-server/kette_werkzeuge.py` | als Skript `python kette_werkzeuge.py --laeufer <kt> <kette_py> <lauf_dir> <root>` (Läufer, von `kette_lauf` gestartet) | T2, T3, T5, T6; ohne `--laeufer` T8 |

## Quellen

- `role-split/kette/kette.py` Zeilen 1629–1643 – `_schreibbereich`, `_im_schreibbereich` (Dateien, die `kette_commit` mitnehmen darf)
- `role-split/kette/automatik.py` def lauf – was `kette.py lauf` tut, Exit-Codes, `HALT`
- `role-split/kette/automatik.py` def status – Ausgabe von `kette.py status`
- `mcp-server/lab_mcp_server.py` Zeilen 187–208 – `_logged_tool`: `mcp.tool()` protokolliert automatisch
- `mcp-server/lab_mcp_server.py` Zeilen 698–767 – Einfügestelle vor „Start“, `_banner`
- `experiments/stufe4_probe/README.md` – Messung: Abbruch nach ~5 min, Start → Status trägt

## Anforderungen

### K1: Gemeinsames
- **Anforderung:** Modul `mcp-server/kette_werkzeuge.py`, nur Standardbibliothek. Konstanten: `ROOT = Path(__file__).resolve().parent.parent`; `KETTE_PY = ROOT / "role-split" / "kette" / "kette.py"`; `KETTE_MODUL` = fester Ordner `role-split/kette` neben dieser Datei (Import der Hilfen, **nicht** aus `KETTE_PY` abgeleitet, weil Tests `KETTE_PY` umbiegen); `LAUF_DIR` = `KETTE_LAUF_DIR` oder `~/.lab_mcp/kette` (expanduser); `ERGEBNIS_ZEILEN = 80`; `ERGEBNIS_ZEICHEN = 12000`; `KURZ_TIMEOUT = 120`; `VERWAIST_S = 60`; Liste `_PROZESSE` der gestarteten `Popen`-Objekte. Alle Konstanten werden **zur Aufrufzeit** gelesen (Tests biegen sie um).
  1. Jedes Werkzeug gibt **immer einen String** zurück und prüft zuerst den Kurztitel (`[a-z0-9_]+` per `fullmatch`, auch Nicht-String). Ungültig → `FEHLER: Kurztitel '<kt>' ungültig (nur a-z, 0-9, _). Nichts ausgeführt.` – kein Ordner, keine Datei, kein Prozess.
  2. Sperre `LAUF_DIR / "lauf.lock"` (JSON `{"kurztitel", "start", "pid"}`). `laufender() -> dict | None`: zuerst `poll()` auf alle `_PROZESSE` (beendete entfernen – sonst gilt ein Zombie als lebend); Sperre fehlt → `None`; nicht lesbar/kein JSON-Objekt → verwaist; `pid` gesetzt → lebt, wenn `os.kill(pid, 0)` klappt (`PermissionError` = lebt); `pid` `None` → lebt, wenn `start` jünger als `VERWAIST_S`. Verwaist → Sperre löschen, `None`. Sonst die Sperrdaten.
  3. Hilfe `_kette(*args)`: `[sys.executable, str(KETTE_PY), *args]`, `cwd=ROOT`, `capture_output`, `timeout=KURZ_TIMEOUT`; Rückgabe stdout+stderr (rechts gekürzt) plus Zeile `(kette.py Exit <n>)`; Zeitlimit → `FEHLER: kette.py … nach 120 s abgebrochen.`
- **Stelle:** `mcp-server/kette_werkzeuge.py`
- **Akzeptanz:** T1, T4.

### K2: `kette_lauf(kurztitel)` und Läufer
- **Anforderung:**
  1. Lebt ein Lauf (`laufender()`), → `ABGELEHNT: Es läuft schon ein Lauf (<kt der Sperre>, seit <m> min). Es darf nur ein Lauf gleichzeitig laufen. Stand mit kette_status(kurztitel="<kt der Sperre>") abfragen.`
  2. Sonst `LAUF_DIR` anlegen, Sperre **exklusiv** anlegen (`os.open(..., O_CREAT | O_EXCL | O_WRONLY)`; `FileExistsError` → Antwort wie 1) mit `pid: None`, `LAUF_DIR/<kt>.json` löschen, Läufer starten: `Popen([sys.executable, <diese Datei>, "--laeufer", kt, str(KETTE_PY), str(LAUF_DIR), str(ROOT)], cwd=ROOT, stdin/stdout/stderr=DEVNULL, start_new_session=True, env=os.environ + PYTHONUNBUFFERED=1)`, in `_PROZESSE` merken, dann `pid` in die Sperre nachtragen, **nur** wenn sie noch existiert und `pid` noch `None` ist.
  3. Rückgabe sofort: `Lauf gestartet: <kt>. Er dauert meist 10–40 Minuten und läuft unabhängig vom Chat weiter. Stand mit kette_status(kurztitel="<kt>"), Ausgabe mit kette_ergebnis(kurztitel="<kt>") abfragen – nicht erneut starten.`
  4. Läufer `_laeufer(kt, kette_py, lauf_dir, root)`: schreibt `<lauf_dir>/<kt>.log` (erste Zeile `# kette.py lauf <kt> – Start <Zeit>`, dann stdout+stderr von `[sys.executable, kette_py, "lauf", kt]`, `cwd=root`). **Immer** (`finally`, auch bei Ausnahme → `exit: -1`, Meldung ins Log): `<kt>.json` mit `{"kurztitel", "exit", "start", "ende"}` schreiben, dann `lauf.lock` löschen.
  5. Skriptaufruf: `if __name__ == "__main__"`: genau `--laeufer` + 4 Argumente → `sys.exit(_laeufer(...))`; sonst Hinweis auf stderr, Exit 2.
- **Stelle:** `kette_lauf`, `_laeufer`, `__main__`
- **Akzeptanz:** T2, T3, T4.

### K3: `kette_status(kurztitel)`
- **Anforderung:** Erste Zeile: lebt ein Lauf → `Lauf: läuft (<kt der Sperre>, seit <m> min).`; sonst mit `<kt>.json` → `Lauf: letzter Lauf Exit <exit>, beendet <TT.MM. HH:MM>.`; sonst `Lauf: keiner über die Chat-UI gestartet.` Danach die Ausgabe von `_kette("status", kt)`.
- **Stelle:** `kette_status`
- **Akzeptanz:** T5.

### K4: `kette_ergebnis(kurztitel)`
- **Anforderung:** Ohne `<kt>.log` → `Kein Protokoll für <kt> – noch kein Lauf über die Chat-UI.` Sonst Kopf: lebt ein Lauf **dieses** Kurztitels → `Lauf <kt> läuft noch (seit <m> min). Bisherige Ausgabe:`, sonst `Lauf <kt>: Exit <exit oder ?>, beendet <Zeit oder ?>.`; dann `Letzte <n> von <N> Zeilen:` und die letzten `ERGEBNIS_ZEILEN` Zeilen, zusammen höchstens `ERGEBNIS_ZEICHEN` Zeichen (vom Ende her).
- **Stelle:** `kette_ergebnis`
- **Akzeptanz:** T6.

### K5: `kette_commit(kurztitel, bestaetigung="")` – zwei Schritte
- **Anforderung:**
  1. Lebt ein Lauf → `ABGELEHNT: Während ein Lauf läuft (<kt>), wird nicht committet. …`
  2. Spec `docs/projekt_management/<kt>/spec_<8 Ziffern>_<kt>.md`, sonst flach in `docs/projekt_management/` (jeweils der letzte nach Name; Name muss genau passen). Keine → `FEHLER: Keine Spec spec_<datum>_<kt>.md – ohne Schreibbereich kein Commit.`
  3. Erlaubt ist ein Pfad, wenn `_im_schreibbereich(pfad, _schreibbereich(spec) or [])` (Import aus `KETTE_MODUL`), oder er mit `docs/projekt_management/<kt>/` beginnt, oder er `tests/test_<kt>.py` ist.
  4. Änderungen aus `git -C ROOT status --porcelain=v1 -z --untracked-files=all`: je Eintrag `(XY, Pfad)` mit `Pfad = eintrag[3:]`; bei `X` in `RC` den folgenden NUL-Eintrag (Herkunft) überspringen. Teilen in `im` (erlaubt) und `aussen`, je sortiert.
  5. `im` leer → `Nichts zu committen für <kt>.` plus Liste `Nicht im Commit (<n>):`.
  6. Code = erste 6 Hex-Zeichen von `sha256("\n".join("XY Pfad" für im) + "\n" + kt)`. Nachricht: Betreff `Kette <kt>: Ergebnis aus der Chat-UI`, Leerzeile, `Per kette_commit: <n> Datei(en) aus Schreibbereich, Ketten-Ordner und Testdatei.`
  7. Ohne `bestaetigung` → Vorschau, **nichts** wird committet: Zeilen `Vorschau Commit <kt> – noch NICHT committet.`, `Nachricht: <Betreff>`, `Im Commit (<n>):` + je `  XY Pfad`, `Nicht im Commit (<m>):` + je `  XY Pfad` oder `  (keine)`, `Bestätigungscode: <code>`, `Nur nach ausdrücklicher Zustimmung des Nutzers im Chat: kette_commit(kurztitel="<kt>", bestaetigung="<code>").`
  8. `bestaetigung` (gestrippt) ≠ Code → `ABGELEHNT: Code passt nicht zur aktuellen Dateiliste (falsch oder Dateien geändert). Nichts committet. …`
  9. Passt → `git add -A -- <Pfade aus im>`, dann `git commit -F <tempdatei> -- <Pfade aus im>` (nur diese Pfade; vorher Vorgemerktes bleibt draußen); Rückgabe `Committet: <kurzer Hash> – <n> Datei(en). Nicht im Commit: <m> Datei(en).` + Liste. git-Fehler → `FEHLER: git … fehlgeschlagen: …`.
  10. Die Docstrings sind die Werkzeugbeschreibung fürs Modell: `kette_lauf` sagt „nicht erneut starten“, `kette_commit` „nur nach ausdrücklicher Zustimmung“ des Nutzers.
- **Stelle:** `kette_commit`, `_spec_text`, `_aenderungen`, `_git`
- **Akzeptanz:** T3, T7, T8.

### K6: Registrierung im Server
- **Anforderung:** In `kette_werkzeuge.py`: `WERKZEUGE = (kette_status, kette_lauf, kette_ergebnis, kette_commit)`; `registrieren(mcp) -> list[str]` ruft für jedes `mcp.tool()(fn)` und gibt die Namen zurück. In `lab_mcp_server.py` direkt vor dem Abschnitt „Start“: `ALLOW_KETTE = os.environ.get("MCP_ALLOW_KETTE", "0") == "1" and not READONLY`; `if ALLOW_KETTE:` Ordner der Datei in `sys.path`, `import kette_werkzeuge`, `kette_werkzeuge.registrieren(mcp)` (genau ein Aufruf). Im Kommentar darüber: Standard aus, bewusst mehr Recht als `MCP_WRITE_ROOTS`. In `_banner` nach `run_python` die Zeile `  kette      : {ALLOW_KETTE}`. Sonst nichts am Server ändern.
- **Stelle:** `registrieren`; `lab_mcp_server.py` vor „Start“ und `_banner`
- **Akzeptanz:** T8.

## Fehlerpfade

| Anforderung | Fall | Was ist vorher schon geschrieben/markiert? | Erwartetes Verhalten (Exit-Code, Datei, Meldung) | Test |
|---|---|---|---|---|
| K1 | Kurztitel ungültig (`../x`, Großbuchstaben, leer, Leerzeichen, `;`) | nichts | `FEHLER …`, kein `LAUF_DIR`, kein Prozess | T1 |
| K1 | Sperre kaputt / toter Prozess / alte Sperre ohne pid | Sperre liegt | gilt als verwaist, wird gelöscht | T4 |
| K1 | frische Sperre ohne pid (Start läuft gerade) | Sperre liegt | gilt als belegt | T4 |
| K2 | zweiter Start während eines Laufs (gleicher oder anderer Kurztitel) | Sperre, Läufer läuft | `ABGELEHNT`, kein zweiter Läufer, kein zweites Log | T3 |
| K2 | Läufer stürzt ab / `kette.py` fehlt | Sperre | `finally`: Ergebnis mit Exit, Sperre weg | – (folgt aus `finally`; Ersatzskript in T2 mit Exit 3) |
| K2 | MCP-Server wird während des Laufs neu gestartet | Sperre mit pid | Läufer läuft weiter (eigene Sitzung); `laufender()` erkennt ihn über `os.kill` | – (Betrieb) |
| K2 | Web-UI bricht nach ~5 min ab | – | tritt nicht auf: `kette_lauf` kehrt in < 1,5 s zurück | T2 |
| K3 | Status ohne Lauf / währenddessen / danach | – | drei Kopfzeilen, `kette.py status` immer dabei | T5 |
| K3 | `kette.py status` hängt | – | `FEHLER … nach 120 s` | – (Zeitlimit) |
| K4 | kein Protokoll / langes Protokoll | – | Meldung / nur die letzten 80 Zeilen | T6 |
| K5 | Commit während eines Laufs | Sperre | `ABGELEHNT` | T3 |
| K5 | keine Spec | – | `FEHLER`, nichts committet | T7 |
| K5 | falscher Code / Dateien seit Vorschau geändert | Vorschau gezeigt | `ABGELEHNT`, HEAD unverändert | T7 |
| K5 | Dateien außerhalb, Löschung außerhalb, vorher Vorgemerktes | liegen im Arbeitsbaum | nicht im Commit, bleiben offen | T7 |
| K5 | nichts Erlaubtes geändert | – | `Nichts zu committen …` | T7 |
| K6 | Schalter aus / `MCP_READONLY=1` | – | keine Ketten-Werkzeuge registriert | T8 (Bedingung im Quelltext); Live-Prüfung durch Claude |

## Testplan

Die Tests stehen in `tests/test_mcp_kette.py` (Vorgabe, nicht ändern). Kein Test hat Außenwirkung. Vorab 8/8 rot (Modul fehlt; `kette.py tests-pruefen mcp_kette` → „Keine Abweichung.“); gegen die Referenz 8/8 grün, dreimal hintereinander stabil (~9 s). Mutationsprüfung der Referenz: 22 von 22 gefangen.

### T1: Ungültiger Kurztitel – jedes Werkzeug meldet FEHLER und tut nichts
- **Prüft:** K1.1
- **Aufbau:** fünf ungültige Kurztitel gegen alle vier Werkzeuge.
- **Erwartung:** Antwort beginnt mit `FEHLER` und enthält `ungültig`; `LAUF_DIR` existiert nicht; `_PROZESSE` leer.
- **Warum misst der Test das Richtige?** Der Kurztitel landet in Dateinamen und argv – ohne Prüfung wäre `../x` ein Pfadausbruch.
- **Gegenprobe:** alter Stand → rot (Modul fehlt).

### T2: kette_lauf kehrt sofort zurück; Läufer schreibt Protokoll und Ergebnis und gibt die Sperre frei
- **Prüft:** K2.2–K2.4, Fehlerpfad „Web-UI bricht ab“
- **Aufbau:** Ersatzskript schläft 2 s, druckt, Exit 3.
- **Erwartung:** Rückkehr < 1,5 s, Text beginnt `Lauf gestartet: k`, nennt `kette_status(kurztitel="k")`; Sperre mit `kurztitel` während des Laufs; danach `k.json` mit Exit 3, Dauer ≥ 1,5 s, Log mit Ausgabe, Sperre weg.
- **Warum misst der Test das Richtige?** Genau das blockierende Warten würde die Web-UI nach 5 min abbrechen.
- **Gegenprobe:** alter Stand → rot.

### T3: Während eines Laufs: zweiter Start und Commit abgelehnt; danach wieder frei
- **Prüft:** K2.1, K5.1
- **Aufbau:** Lauf `k` (3 s), dann `kette_lauf("k2")`, `kette_lauf("k")`, `kette_commit("k")`.
- **Erwartung:** dreimal `ABGELEHNT`, ein Läufer, kein `k2.log`; nach dem Ende startet `k2`.
- **Warum misst der Test das Richtige?** Zwei Läufe auf einem Modell und ein Commit mitten im Lauf sind die teuersten Bedienfehler.
- **Gegenprobe:** alter Stand → rot.

### T4: Verwaiste Sperre wird entfernt; frische ohne pid gilt als belegt
- **Prüft:** K1.2
- **Aufbau:** Sperre mit pid eines beendeten Prozesses; alte Sperre ohne pid; frische ohne pid; kaputte Sperre; zuletzt ein echter Läufer, der per `os.killpg(…, SIGKILL)` abgeschossen wird (Sperre bleibt liegen, Prozess ist Zombie).
- **Erwartung:** die ersten beiden → `laufender()` `None`, Sperre gelöscht; frische → `ABGELEHNT`; kaputte → Start klappt; abgeschossener Läufer → `laufender()` `None` (nur mit `poll()` vor der Prüfung), Sperre gelöscht.
- **Warum misst der Test das Richtige?** Nach Absturz oder Neustart darf keine Leiche die Kette dauerhaft sperren.
- **Gegenprobe:** alter Stand → rot.

### T5: kette_status – keiner / läuft / letzter Exit, jeweils mit der Ausgabe von kette.py status
- **Prüft:** K3, K1.3
- **Aufbau:** vor, während und nach einem Ersatz-Lauf.
- **Erwartung:** Kopf `Lauf: keiner…` / `Lauf: läuft (k` / `Lauf: letzter Lauf Exit 3`; `Status k` und `Exit 0` aus dem Ersatz enthalten.
- **Warum misst der Test das Richtige?** Das ist die Abfrage, die das Modell nach dem Start wiederholt (Messung Schritt 4).
- **Gegenprobe:** alter Stand → rot.

### T6: kette_ergebnis – ohne Protokoll, nach dem Lauf, nur das Ende langer Protokolle
- **Prüft:** K4
- **Aufbau:** ohne Log; nach Ersatz-Lauf; ein Protokoll mit 200 Zeilen.
- **Erwartung:** `Kein Protokoll für k`; `Lauf k: Exit 3` mit `HALT`; `Letzte 80 von 200 Zeilen`, `zeile 120`–`zeile 199`, nicht `zeile 119`.
- **Warum misst der Test das Richtige?** Ein volles Protokoll würde den Kontext des Bedienmodells sprengen.
- **Gegenprobe:** alter Stand → rot.

### T7: kette_commit – Vorschau ohne Commit, falscher Code abgelehnt, richtiger Code committet nur Erlaubtes
- **Prüft:** K5.2–K5.9
- **Aufbau:** Wegwerf-Repo mit Spec (`pkg/`, `einzeln.py`); geändert, neu, Testdatei, Handover im Ketten-Ordner (4 erlaubt); `fremd.txt`, gelöschtes `alt.py`, vorgemerktes `vorgemerkt.txt` (3 außen).
- **Erwartung:** Vorschau: HEAD gleich, `Im Commit (4)`, `Nicht im Commit (3)`, 6-stelliger Code; falscher Code → `ABGELEHNT`, HEAD gleich; richtiger → genau die 4 Dateien im Commit, Betreff `Kette k:`, die 3 bleiben offen, vorgemerkt ist danach nur `vorgemerkt.txt`; danach `Nichts zu committen`; ohne Spec `FEHLER`.
- **Warum misst der Test das Richtige?** Der Commit ist der einzige Schritt, der den Stand festschreibt – er darf nichts Fremdes mitnehmen.
- **Gegenprobe:** alter Stand → rot.

### T8: registrieren meldet genau vier Werkzeuge an; lab_mcp_server schaltet sie nur mit MCP_ALLOW_KETTE=1 frei
- **Prüft:** K6, K5.10, K2.5
- **Aufbau:** Attrappe mit `tool()`; `ast` von `lab_mcp_server.py`; Skript ohne `--laeufer`.
- **Erwartung:** vier Namen mit Beschreibung; Docstrings mit „nicht erneut“ / „Zustimmung“; `MCP_ALLOW_KETTE` im Server, genau ein `registrieren`-Aufruf innerhalb eines `if`, dessen Bedingung `ALLOW_KETTE` prüft; genau eine Zuweisung `ALLOW_KETTE = …` mit `MCP_ALLOW_KETTE` und `READONLY`; Skript ohne Argumente Exit 2.
- **Warum misst der Test das Richtige?** Ohne Bedingung wären schreibende Ketten-Werkzeuge auch im Claude-Desktop- und Eval-Betrieb aktiv.
- **Gegenprobe:** alter Stand → rot.

## Offene Fragen

- Keine

## Abweichende Meinung

- Die Bestätigung in `kette_commit` erzwingt keine Zustimmung: Das Modell sieht den Code und könnte ihn selbst weiterreichen. Entscheidung Hawe 28.10.: Risiko tragen, weil der Commit nur Erlaubtes nimmt und per `git reset` leicht rückgängig ist.
