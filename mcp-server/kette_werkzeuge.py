"""kette_werkzeuge.py – MCP-Werkzeuge fuer die Kette (Stufe 4, Kette mcp_kette).

Vier feste Werkzeuge fuer die Chat-UI, keine freie Shell, keine Pfade als Parameter:
    kette_status, kette_lauf, kette_ergebnis, kette_commit

Messung 28.10. (experiments/stufe4_probe): Die Web-UI bricht Werkzeugaufrufe nach ~5 min
aktiv ab. Darum startet kette_lauf einen eigenen Prozess (Laeufer) und kehrt sofort zurueck.

Registrierung: lab_mcp_server.py ruft registrieren(mcp), wenn MCP_ALLOW_KETTE=1.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KETTE_PY = ROOT / "role-split" / "kette" / "kette.py"
# Fester Ort der Hilfsfunktionen (_schreibbereich) – unabhaengig von umgebogenem KETTE_PY.
KETTE_MODUL = Path(__file__).resolve().parent.parent / "role-split" / "kette"
LAUF_DIR = Path(os.path.expanduser(os.environ.get("KETTE_LAUF_DIR", "~/.lab_mcp/kette")))
ERGEBNIS_ZEILEN = 80
ERGEBNIS_ZEICHEN = 12000
KURZ_TIMEOUT = 120
VERWAIST_S = 60

_KT = re.compile(r"[a-z0-9_]+")
_SPEC = re.compile(r"^spec_\d{8}_(?P<kt>[a-z0-9_]+)\.md$")
_PROZESSE: list[subprocess.Popen] = []


# ---------------------------------------------------------------- K1 Gemeinsames

def _kt_fehler(kurztitel) -> str | None:
    if not isinstance(kurztitel, str) or not _KT.fullmatch(kurztitel):
        return f"FEHLER: Kurztitel '{kurztitel}' ungültig (nur a-z, 0-9, _). Nichts ausgeführt."
    return None


def _sperre() -> Path:
    return LAUF_DIR / "lauf.lock"


def _minuten(start) -> int:
    try:
        return max(0, int((time.time() - float(start)) // 60))
    except (TypeError, ValueError):
        return 0


def laufender() -> dict | None:
    """Daten der Sperre, wenn ein Lauf lebt. Verwaiste Sperre wird entfernt (-> None)."""
    for p in list(_PROZESSE):
        if p.poll() is not None:
            _PROZESSE.remove(p)
    s = _sperre()
    try:
        daten = json.loads(s.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        daten = {}
    if not isinstance(daten, dict):
        daten = {}
    pid = daten.get("pid")
    if pid is None:
        try:
            lebt = time.time() - float(daten.get("start", 0)) < VERWAIST_S
        except (TypeError, ValueError):
            lebt = False
    else:
        try:
            os.kill(int(pid), 0)
            lebt = True
        except ProcessLookupError:
            lebt = False
        except PermissionError:
            lebt = True
        except (TypeError, ValueError):
            lebt = False
    if lebt:
        return daten
    s.unlink(missing_ok=True)
    return None


def _belegt(daten: dict) -> str:
    kt = daten.get("kurztitel", "?")
    return (f"ABGELEHNT: Es läuft schon ein Lauf ({kt}, seit {_minuten(daten.get('start'))} min). "
            f"Es darf nur ein Lauf gleichzeitig laufen. Stand mit kette_status(kurztitel=\"{kt}\") abfragen.")


def _ergebnis(kurztitel: str) -> dict | None:
    try:
        return json.loads((LAUF_DIR / f"{kurztitel}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _zeit(ts) -> str:
    try:
        return datetime.fromtimestamp(float(ts)).strftime("%d.%m. %H:%M")
    except (TypeError, ValueError, OSError):
        return "?"


def _kette(*args: str) -> str:
    try:
        r = subprocess.run([sys.executable, str(KETTE_PY), *args], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=KURZ_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"FEHLER: kette.py {' '.join(args)} nach {KURZ_TIMEOUT} s abgebrochen."
    return ((r.stdout or "") + (r.stderr or "")).rstrip() + f"\n(kette.py Exit {r.returncode})"


# ---------------------------------------------------------------- K2 Lauf

def kette_lauf(kurztitel: str) -> str:
    """Startet `kette.py lauf <kurztitel>` im Hintergrund und kehrt SOFORT zurück.

    Ein Lauf dauert meist 10–40 Minuten und läuft unabhängig vom Chat weiter.
    Danach NICHT erneut starten, sondern mit kette_status den Stand und mit
    kette_ergebnis die Ausgabe abfragen. Es läuft immer nur ein Lauf gleichzeitig.

    Args:
        kurztitel: Kurztitel der Kette (nur a-z, 0-9, _), z. B. "mcp_kette".
    """
    f = _kt_fehler(kurztitel)
    if f:
        return f
    l = laufender()
    if l:
        return _belegt(l)
    LAUF_DIR.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(_sperre()), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return _belegt(laufender() or {})
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump({"kurztitel": kurztitel, "start": time.time(), "pid": None}, fh)
    (LAUF_DIR / f"{kurztitel}.json").unlink(missing_ok=True)
    env = dict(os.environ, PYTHONUNBUFFERED="1")
    p = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--laeufer", kurztitel,
         str(KETTE_PY), str(LAUF_DIR), str(ROOT)],
        cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, start_new_session=True, env=env)
    _PROZESSE.append(p)
    try:
        daten = json.loads(_sperre().read_text(encoding="utf-8"))
        if daten.get("pid") is None:
            daten["pid"] = p.pid
            _sperre().write_text(json.dumps(daten), encoding="utf-8")
    except (OSError, ValueError):
        pass  # Laeufer schon fertig und Sperre entfernt
    return (f"Lauf gestartet: {kurztitel}. Er dauert meist 10–40 Minuten und läuft unabhängig vom Chat "
            f"weiter. Stand mit kette_status(kurztitel=\"{kurztitel}\"), Ausgabe mit "
            f"kette_ergebnis(kurztitel=\"{kurztitel}\") abfragen – nicht erneut starten.")


def _laeufer(kurztitel: str, kette_py: str, lauf_dir: str, root: str) -> int:
    """Eigener Prozess: fuehrt kette.py lauf aus, schreibt Protokoll und Ergebnis, gibt die Sperre frei."""
    d = Path(lauf_dir)
    start = time.time()
    code = -1
    log = d / f"{kurztitel}.log"
    try:
        with log.open("w", encoding="utf-8") as fh:
            fh.write(f"# kette.py lauf {kurztitel} – Start {datetime.now().isoformat(timespec='seconds')}\n")
            fh.flush()
            r = subprocess.run([sys.executable, kette_py, "lauf", kurztitel], cwd=root,
                               stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT)
            code = r.returncode
    except Exception as e:  # Laeufer darf die Sperre nie haengen lassen
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"\nFEHLER im Läufer: {type(e).__name__}: {e}\n")
    finally:
        (d / f"{kurztitel}.json").write_text(
            json.dumps({"kurztitel": kurztitel, "exit": code, "start": start, "ende": time.time()}),
            encoding="utf-8")
        (d / "lauf.lock").unlink(missing_ok=True)
    return 0


# ---------------------------------------------------------------- K3 Status

def kette_status(kurztitel: str) -> str:
    """Stand der Kette: läuft gerade ein Lauf, wie endete der letzte, und was `kette.py status` meldet.

    Kurz, blockiert nicht. Dafür gedacht, nach kette_lauf regelmäßig nachzusehen.

    Args:
        kurztitel: Kurztitel der Kette (nur a-z, 0-9, _).
    """
    f = _kt_fehler(kurztitel)
    if f:
        return f
    l = laufender()
    if l:
        kopf = f"Lauf: läuft ({l.get('kurztitel', '?')}, seit {_minuten(l.get('start'))} min)."
    else:
        e = _ergebnis(kurztitel)
        kopf = (f"Lauf: letzter Lauf Exit {e.get('exit')}, beendet {_zeit(e.get('ende'))}." if e
                else "Lauf: keiner über die Chat-UI gestartet.")
    return kopf + "\n" + _kette("status", kurztitel)


# ---------------------------------------------------------------- K4 Ergebnis

def kette_ergebnis(kurztitel: str) -> str:
    """Ausgabe des letzten Laufs (Ende des Protokolls) – auch während der Lauf noch läuft.

    Args:
        kurztitel: Kurztitel der Kette (nur a-z, 0-9, _).
    """
    f = _kt_fehler(kurztitel)
    if f:
        return f
    log = LAUF_DIR / f"{kurztitel}.log"
    if not log.is_file():
        return f"Kein Protokoll für {kurztitel} – noch kein Lauf über die Chat-UI."
    l = laufender()
    if l and l.get("kurztitel") == kurztitel:
        kopf = f"Lauf {kurztitel} läuft noch (seit {_minuten(l.get('start'))} min). Bisherige Ausgabe:"
    else:
        e = _ergebnis(kurztitel) or {}
        kopf = f"Lauf {kurztitel}: Exit {e.get('exit', '?')}, beendet {_zeit(e.get('ende'))}."
    zeilen = log.read_text(encoding="utf-8", errors="replace").splitlines()
    rest = zeilen[-ERGEBNIS_ZEILEN:]
    text = "\n".join(rest)[-ERGEBNIS_ZEICHEN:]
    return f"{kopf}\nLetzte {len(rest)} von {len(zeilen)} Zeilen:\n{text}"


# ---------------------------------------------------------------- K5 Commit

def _spec_text(kurztitel: str) -> str | None:
    pm = ROOT / "docs" / "projekt_management"
    for ordner in (pm / kurztitel, pm):
        treffer = sorted(p for p in ordner.glob(f"spec_*_{kurztitel}.md")
                         if (m := _SPEC.match(p.name)) and m.group("kt") == kurztitel)
        if treffer:
            return treffer[-1].read_text(encoding="utf-8")
    return None


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=60)


def _aenderungen() -> list[tuple[str, str]]:
    """(Status, Pfad) aller Aenderungen laut git status --porcelain=v1 -z --untracked-files=all."""
    teile = _git("status", "--porcelain=v1", "-z", "--untracked-files=all").stdout.split("\0")
    aus, i = [], 0
    while i < len(teile):
        e = teile[i]
        i += 1
        if len(e) < 4:
            continue
        xy, pfad = e[:2], e[3:]
        if xy[0] in "RC":
            i += 1  # Herkunftspfad der Umbenennung ueberspringen
        aus.append((xy, pfad))
    return aus


def kette_commit(kurztitel: str, bestaetigung: str = "") -> str:
    """Committet das Ergebnis einer Kette – in ZWEI Schritten.

    1. Ohne `bestaetigung`: Vorschau (Dateien im Commit, Dateien außerhalb, Bestätigungscode).
       Es wird NICHTS committet. Zeige die Vorschau dem Nutzer.
    2. Erst wenn der Nutzer im Chat ausdrücklich zustimmt: erneut aufrufen mit
       bestaetigung=<Code aus der Vorschau>. Nie ohne diese Zustimmung.
    Im Commit sind nur Dateien aus dem Schreibbereich der Spec, dem Ordner
    docs/projekt_management/<kurztitel>/ und tests/test_<kurztitel>.py.

    Args:
        kurztitel: Kurztitel der Kette (nur a-z, 0-9, _).
        bestaetigung: Code aus der Vorschau; leer = nur Vorschau.
    """
    f = _kt_fehler(kurztitel)
    if f:
        return f
    l = laufender()
    if l:
        return (f"ABGELEHNT: Während ein Lauf läuft ({l.get('kurztitel', '?')}), wird nicht committet. "
                f"Erst kette_status abwarten.")
    spec = _spec_text(kurztitel)
    if spec is None:
        return f"FEHLER: Keine Spec spec_<datum>_{kurztitel}.md – ohne Schreibbereich kein Commit."
    if str(KETTE_MODUL) not in sys.path:
        sys.path.insert(0, str(KETTE_MODUL))
    from kette import _im_schreibbereich, _schreibbereich
    eintraege = _schreibbereich(spec) or []

    def erlaubt(pfad: str) -> bool:
        return (_im_schreibbereich(pfad, eintraege)
                or pfad.startswith(f"docs/projekt_management/{kurztitel}/")
                or pfad == f"tests/test_{kurztitel}.py")

    alle = _aenderungen()
    im = sorted((xy, p) for xy, p in alle if erlaubt(p))
    aussen = sorted((xy, p) for xy, p in alle if not erlaubt(p))
    liste_aussen = "".join(f"\n  {xy} {p}" for xy, p in aussen) or "\n  (keine)"
    if not im:
        return f"Nichts zu committen für {kurztitel}.\nNicht im Commit ({len(aussen)}):{liste_aussen}"
    code = hashlib.sha256(("\n".join(f"{xy} {p}" for xy, p in im) + "\n" + kurztitel)
                          .encode("utf-8")).hexdigest()[:6]
    nachricht = (f"Kette {kurztitel}: Ergebnis aus der Chat-UI\n\n"
                 f"Per kette_commit: {len(im)} Datei(en) aus Schreibbereich, Ketten-Ordner und Testdatei.\n")
    if not bestaetigung:
        liste_im = "".join(f"\n  {xy} {p}" for xy, p in im)
        return (f"Vorschau Commit {kurztitel} – noch NICHT committet.\n"
                f"Nachricht: {nachricht.splitlines()[0]}\n"
                f"Im Commit ({len(im)}):{liste_im}\n"
                f"Nicht im Commit ({len(aussen)}):{liste_aussen}\n"
                f"Bestätigungscode: {code}\n"
                f"Nur nach ausdrücklicher Zustimmung des Nutzers im Chat: "
                f"kette_commit(kurztitel=\"{kurztitel}\", bestaetigung=\"{code}\").")
    if bestaetigung.strip() != code:
        return (f"ABGELEHNT: Code passt nicht zur aktuellen Dateiliste (falsch oder Dateien geändert). "
                f"Nichts committet. Neue Vorschau mit kette_commit(kurztitel=\"{kurztitel}\").")
    pfade = [p for _, p in im]
    r = _git("add", "-A", "--", *pfade)
    if r.returncode != 0:
        return f"FEHLER: git add fehlgeschlagen: {(r.stdout + r.stderr).strip()[:500]}"
    fd, tmp = tempfile.mkstemp(prefix="kette_commit_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(nachricht)
        r = _git("commit", "-F", tmp, "--", *pfade)
    finally:
        Path(tmp).unlink(missing_ok=True)
    if r.returncode != 0:
        return f"FEHLER: git commit fehlgeschlagen: {(r.stdout + r.stderr).strip()[:500]}"
    kurz = _git("rev-parse", "--short", "HEAD").stdout.strip()
    return (f"Committet: {kurz} – {len(im)} Datei(en). "
            f"Nicht im Commit: {len(aussen)} Datei(en).{liste_aussen if aussen else ''}")


# ---------------------------------------------------------------- K6 Registrierung

WERKZEUGE = (kette_status, kette_lauf, kette_ergebnis, kette_commit)


def registrieren(mcp) -> list[str]:
    """Registriert die vier Werkzeuge am MCP-Server (mcp.tool()) und gibt ihre Namen zurueck."""
    for fn in WERKZEUGE:
        mcp.tool()(fn)
    return [fn.__name__ for fn in WERKZEUGE]


if __name__ == "__main__":
    if len(sys.argv) == 6 and sys.argv[1] == "--laeufer":
        sys.exit(_laeufer(*sys.argv[2:]))
    print("Aufruf nur intern: kette_werkzeuge.py --laeufer <kurztitel> <kette_py> <lauf_dir> <root>",
          file=sys.stderr)
    sys.exit(2)
