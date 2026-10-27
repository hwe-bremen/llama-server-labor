#!/usr/bin/env python3
"""Attrappe fuer `opencode run --format json` (nur fuer tests/test_umsetzung_auto.py).

Gibt einen JSON-Ereignisstrom im Format von opencode 1.19.3 aus (Spec-Paket umsetzung_auto §1) und
kann ueber Umgebungsvariablen Dateien aendern, committen oder haengen.

TECHNISCHE SPERRE (R04): Das Arbeitsverzeichnis (--dir bzw. cwd) muss im System-Temp-Ordner liegen.
Sonst gibt die Attrappe nur eine Fehlermeldung aus und beendet sich mit Exit 3 – ohne irgendetwas zu
schreiben oder zu committen. So kann ein falsch aufgebauter Test nie das echte Repo veraendern.

Steuerung:
  FAKE_REASON     reason des letzten step_finish (Vorgabe: stop)
  FAKE_SLEEP      Sekunden warten, bevor das letzte Ereignis kommt (Timeout-Test)
  FAKE_EDIT       kommagetrennte Pfade (relativ zum Arbeitsverzeichnis), an die eine Zeile angehaengt wird
  FAKE_HANDOVER   Pfad des Handovers (relativ), an den eine Zeile angehaengt wird
  FAKE_COMMIT     "1": leerer git commit im Arbeitsverzeichnis
  FAKE_ABGELEHNT  "1": zusaetzlich ein abgelehnter Werkzeugaufruf im Strom
  FAKE_KAPUTT     "1": nur Zeilen, die kein JSON sind
  FAKE_ARGS       Pfad (im Temp-Ordner), in den die Argumente als JSON geschrieben werden
  FAKE_NACHBESSERUNG  Nummer n: der Handover bekommt zusaetzlich den Abschnitt "## Nachbesserung n"
  FAKE_FEHLER     "1": zusaetzlich ein fehlgeschlagener (nicht abgelehnter) Werkzeugaufruf
  FAKE_KIND       Pfad (im Temp-Ordner): startet ein Kind `sleep 60` und schreibt dessen PID dorthin
  FAKE_EXIT       Exit-Code der Attrappe am Ende (Vorgabe 0; opencode 1.19.3 gibt immer 0)

Auch jedes Schreibziel muss im Temp-Ordner liegen (kein ../ oder absoluter Pfad hinaus).
"""
import json
import os
import subprocess
import sys
import tempfile
import time


def im_temp(pfad: str) -> bool:
    temp = os.path.realpath(tempfile.gettempdir())
    echt = os.path.realpath(pfad)
    return echt == temp or echt.startswith(temp + os.sep)


def main(argv: list[str]) -> int:
    arbeitsordner = os.getcwd()
    if "--dir" in argv:
        i = argv.index("--dir")
        if i + 1 < len(argv):
            arbeitsordner = argv[i + 1]
    if not im_temp(arbeitsordner):
        print(f"opencode_fake: Arbeitsordner {arbeitsordner} liegt nicht im Temp-Ordner – Sperre, nichts getan.",
              file=sys.stderr)
        return 3

    args_ziel = os.environ.get("FAKE_ARGS")
    if args_ziel and im_temp(args_ziel):
        with open(args_ziel, "w", encoding="utf-8") as f:
            json.dump(argv, f, ensure_ascii=False)

    if os.environ.get("FAKE_KAPUTT") == "1":
        print("das ist kein JSON")
        print("{abgebrochen")
        return 0

    def aus(ereignis: dict) -> None:
        ereignis.setdefault("timestamp", int(time.time() * 1000))
        ereignis.setdefault("sessionID", "ses_fake")
        print(json.dumps(ereignis, ensure_ascii=False), flush=True)

    aus({"type": "step_start", "part": {"type": "step-start"}})
    aus({"type": "tool_use", "part": {"type": "tool", "tool": "bash", "state": {
        "status": "completed", "input": {"command": "python3 -m unittest -v tests/test_fake.py"},
        "output": "OK"}}})
    kind_ziel = os.environ.get("FAKE_KIND")
    if kind_ziel and im_temp(kind_ziel):
        kind = subprocess.Popen(["sleep", "60"])
        with open(kind_ziel, "w", encoding="utf-8") as f:
            f.write(str(kind.pid))
    if os.environ.get("FAKE_FEHLER") == "1":
        aus({"type": "tool_use", "part": {"type": "tool", "tool": "bash", "state": {
            "status": "error", "input": {"command": "python3 kaputt.py --x"},
            "error": "Traceback: ModuleNotFoundError: No module named 'kaputt'"}}})
    if os.environ.get("FAKE_ABGELEHNT") == "1":
        aus({"type": "tool_use", "part": {"type": "tool", "tool": "bash", "state": {
            "status": "error", "input": {"command": "git commit -m checkpoint"},
            "error": "The user has specified a rule which prevents you from using this specific tool call."}}})

    for rel in filter(None, (os.environ.get("FAKE_EDIT") or "").split(",")):
        ziel = os.path.join(arbeitsordner, rel.strip())
        if not im_temp(ziel):
            print(f"opencode_fake: Ziel {ziel} liegt nicht im Temp-Ordner – Sperre.", file=sys.stderr)
            return 3
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        with open(ziel, "a", encoding="utf-8") as f:
            f.write("geaendert von opencode_fake\n")
    handover = os.environ.get("FAKE_HANDOVER")
    if handover:
        ziel = os.path.join(arbeitsordner, handover)
        if not im_temp(ziel):
            print(f"opencode_fake: Ziel {ziel} liegt nicht im Temp-Ordner – Sperre.", file=sys.stderr)
            return 3
        os.makedirs(os.path.dirname(ziel), exist_ok=True)
        with open(ziel, "a", encoding="utf-8") as f:
            f.write("# Handover (Attrappe)\n")
            if os.environ.get("FAKE_NACHBESSERUNG"):
                f.write(f"\n## Nachbesserung {os.environ['FAKE_NACHBESSERUNG']}\n\nNachgebessert (Attrappe).\n")
    if os.environ.get("FAKE_COMMIT") == "1":
        subprocess.run(["git", "-C", arbeitsordner, "-c", "user.name=fake", "-c", "user.email=fake@fake",
                        "commit", "--allow-empty", "-qm", "checkpoint (Attrappe)"], check=False)

    aus({"type": "step_finish", "part": {"type": "step-finish", "reason": "tool-calls",
                                         "tokens": {"total": 100, "input": 90, "output": 10}}})
    time.sleep(float(os.environ.get("FAKE_SLEEP") or 0))
    aus({"type": "text", "part": {"type": "text", "text": "Umsetzung fertig (Attrappe)."}})
    aus({"type": "step_finish", "part": {"type": "step-finish", "reason": os.environ.get("FAKE_REASON", "stop"),
                                         "tokens": {"total": 50, "input": 40, "output": 8, "reasoning": 2}}})
    return int(os.environ.get("FAKE_EXIT") or 0)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
