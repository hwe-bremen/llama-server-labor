#!/usr/bin/env python3
"""Pruefskript fuer alle Testdateien (R50): richtig aufrufen, Exit-Code zaehlt."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FUNDORTE = ("tests", "role-split", "mcp-server", "scripts")
AUSGESCHLOSSEN = {".venv", "venv", "__pycache__", "testdata"}
TIMEOUT = 300
SCHWANZ = 20
SONDERAUFRUFE = {"mcp-server/test_tool_log.py": ["mcp-server/lab_mcp_server.py"]}


def finden():
    """Alle test_*.py rekursiv unter ROOT/<Fundort>, ohne AUSGESCHLOSSEN, sortiert."""
    ergebnis = []
    gesehen = set()
    for fundort in FUNDORTE:
        pfad = ROOT / fundort
        if not pfad.is_dir():
            continue
        for w, dirs, fns in os.walk(pfad):
            wp = Path(w)
            if any(t in wp.parts for t in AUSGESCHLOSSEN):
                dirs.clear()
                continue
            for fn in fns:
                if fn.startswith("test_") and fn.endswith(".py"):
                    rel = wp.joinpath(fn).relative_to(ROOT).as_posix()
                    if rel not in gesehen:
                        gesehen.add(rel)
                        ergebnis.append(rel)
    return sorted(ergebnis)


def art(rel):
    """'unittest' wenn unittest-Import, sonst 'skript'."""
    pfad = ROOT / rel
    if not pfad.is_file():
        return "skript"
    text = pfad.read_text(encoding="utf-8", errors="replace")
    for zeile in text.splitlines():
        if zeile.strip().startswith("import unittest") or zeile.strip().startswith("from unittest"):
            return "unittest"
    return "skript"


def aufruf(rel):
    """argv und env fuer unittest oder Skript."""
    py = interpreter(rel)
    if art(rel) == "unittest":
        argv = [py, "-m", "unittest", rel]
    else:
        argv = [py, rel, *SONDERAUFRUFE.get(rel, [])]
    env = os.environ.copy()
    ordner = str((ROOT / rel).parent)
    alt = env.get("PYTHONPATH")
    if alt:
        env["PYTHONPATH"] = ordner + os.pathsep + alt
    else:
        env["PYTHONPATH"] = ordner
    return argv, env


def interpreter(rel):
    """Nächstes .venv/bin/python vom Ordner der Datei aufwaerts, sonst sys.executable."""
    start = (ROOT / rel).resolve().parent
    for ordner in [start] + list(start.parents):
        if ordner == ROOT:
            venv_py = ordner / ".venv" / "bin" / "python"
            if venv_py.exists():
                return str(venv_py)
            break
        venv_py = ordner / ".venv" / "bin" / "python"
        if venv_py.exists():
            return str(venv_py)
    return sys.executable


def main(argv=None):
    p = argparse.ArgumentParser(description="Testdateien laufen lassen")
    p.add_argument("--liste", action="store_true", help="Nur auflisten, nichts ausfuehren")
    p.add_argument("--timeout", type=int, default=TIMEOUT, help="Zeitlimit pro Datei in Sekunden")
    args = p.parse_args(argv)

    if args.timeout < 1:
        p.error("--timeout muss >= 1 sein")

    Dateien = finden()
    if not Dateien:
        print("Keine Testdateien gefunden.")
        return 2

    if args.liste:
        print(f"Testdateien: {len(Dateien)}")
        for rel in Dateien:
            a = art(rel)
            i = interpreter(rel)
            i_rel = str(Path(i).relative_to(ROOT)) if str(i).startswith(str(ROOT)) else "python"
            line = f"  {a:<8} {rel}  [{i_rel}]"
            if a == "skript" and rel in SONDERAUFRUFE:
                line += " " + " ".join(SONDERAUFRUFE[rel])
            print(line)
        return 0

    print(f"Testdateien: {len(Dateien)} (Zeitlimit {args.timeout} s je Datei)")

    rot = []
    zeit = []
    ok = 0
    ausgaben = {}
    for rel in Dateien:
        argv, env = aufruf(rel)
        t0 = time.monotonic()
        try:
            r = subprocess.run(argv, cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
                               capture_output=True, text=True, errors="replace", timeout=args.timeout)
        except subprocess.TimeoutExpired as e:
            print(f"  ZEIT  {rel}  nach {args.timeout} s abgebrochen")
            zeit.append(rel)
            teil = e.stdout or ""
            ausgaben[rel] = teil.decode("utf-8", "replace") if isinstance(teil, bytes) else teil
            continue

        elapsed = time.monotonic() - t0
        if r.returncode == 0:
            print(f"  ok    {rel}  ({elapsed:.1f} s)")
            ok += 1
        else:
            print(f"  ROT   {rel}  Exit {r.returncode}  ({elapsed:.1f} s)")
            rot.append(rel)
            ausgaben[rel] = (r.stdout or "") + (r.stderr or "")

    for rel in [d for d in Dateien if d in ausgaben]:
        ausgabe = ausgaben[rel].rstrip()
        zeilen = [z.rstrip() for z in ausgabe.splitlines()]
        gezeigt = zeilen[-SCHWANZ:] if len(zeilen) > SCHWANZ else zeilen
        print(f"\n--- {rel} – letzte {len(gezeigt)} Zeilen ---")
        for z in gezeigt:
            print(z)

    gesamt = len(Dateien)
    rot_n = len(rot)
    zeit_n = len(zeit)
    print(f"\n{gesamt} Datei(en): {ok} ok, {rot_n} rot, {zeit_n} Zeit.")
    return 0 if rot_n == 0 and zeit_n == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
