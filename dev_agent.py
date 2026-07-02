"""
dev_agent.py — Mode-B Experiment.

Zweck: den lokalen Mellum echte Projektdateien lesen UND schreiben lassen, um
einzuschaetzen, wie gut das Modell bei realer Entwicklungsarbeit ist.

Sicherheits-Scope (nicht verhandelbar):
  - Alle Tools sind fest auf PROJECT_ROOT begrenzt (Traversal-Schutz).
  - PROJECT_ROOT zeigt AUSSCHLIESSLICH auf das lokale llama-server-Testprojekt.
  - NIEMALS auf einen produktiven AskValentinAI-Repo richten -> das waere Mode A.

Rollback: Das Projekt liegt unter Git. VOR dem Lauf committen, dann sind alle
Modell-Aenderungen mit `git checkout -- <datei>` bzw. `git revert` trivial weg.

Voraussetzung: llama-server MIT --jinja gestartet (Tool-Calling), z.B.:
  llama-server -hf JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q6_K --port 8080 --jinja
"""

import os
import json
import subprocess
from openai import OpenAI

BASE_URL = "http://localhost:8080/v1"
PROJECT_ROOT = os.path.abspath("/Users/hans-wernereberhardt/PycharmProjects/llama-server")
MAX_STEPS = 8

client = OpenAI(base_url=BASE_URL, api_key="not-needed")


# --------------------------------------------------------------------------
# Scope-Guard: jeder Pfad muss INNERHALB von PROJECT_ROOT liegen
# --------------------------------------------------------------------------
def _safe_path(relpath: str):
    full = os.path.abspath(os.path.join(PROJECT_ROOT, relpath))
    if full != PROJECT_ROOT and not full.startswith(PROJECT_ROOT + os.sep):
        return None
    return full


# --------------------------------------------------------------------------
# Tools (auf das Projekt begrenzt)
# --------------------------------------------------------------------------
def list_files(subdir: str = ".") -> str:
    base = _safe_path(subdir)
    if base is None:
        return "FEHLER: Pfad ausserhalb des Projekts verweigert."
    if not os.path.isdir(base):
        return f"FEHLER: kein Verzeichnis: {subdir}"
    out = []
    for name in sorted(os.listdir(base)):
        if name.startswith("."):
            continue  # .git & versteckte Dateien ausblenden
        p = os.path.join(base, name)
        out.append(name + ("/" if os.path.isdir(p) else ""))
    return "\n".join(out) if out else "(leer)"


def read_file(path: str) -> str:
    full = _safe_path(path)
    if full is None:
        return "FEHLER: Pfad ausserhalb des Projekts verweigert."
    if not os.path.isfile(full):
        return f"FEHLER: Datei nicht gefunden: {path}"
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


def write_file(path: str, content: str) -> str:
    full = _safe_path(path)
    if full is None:
        return "FEHLER: Pfad ausserhalb des Projekts verweigert."
    if os.path.basename(full).startswith("."):
        return "FEHLER: Schreiben in versteckte Dateien verweigert."
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return f"OK: {path} geschrieben ({len(content)} Zeichen)."


# --------------------------------------------------------------------------
# Schemas + Dispatch
# --------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Listet Dateien/Ordner im Projekt (relativer Unterordner, Standard '.').",
            "parameters": {
                "type": "object",
                "properties": {
                    "subdir": {"type": "string", "description": "relativer Unterordner, z.B. '.' oder 'sandbox'"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Liest den Inhalt einer Projektdatei (relativer Pfad).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "relativer Pfad, z.B. 'tool_demo.py'"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Schreibt (ueberschreibt) eine Projektdatei mit dem gegebenen Inhalt.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "relativer Pfad, z.B. 'tool_demo.py'"},
                    "content": {"type": "string", "description": "der komplette neue Dateiinhalt"},
                },
                "required": ["path", "content"],
            },
        },
    },
]

DISPATCH = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}


def run_tool(name: str, args: dict) -> str:
    fn = DISPATCH.get(name)
    if fn is None:
        return f"FEHLER: unbekanntes Tool '{name}'"
    try:
        return str(fn(**args))
    except Exception as e:
        return f"FEHLER bei {name}: {e}"


# --------------------------------------------------------------------------
# Agenten-Schleife
# --------------------------------------------------------------------------
def chat(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    for _ in range(MAX_STEPS):
        resp = client.chat.completions.create(
            model="local", messages=messages, tools=TOOLS, temperature=0.2
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            }
        )
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            result = run_tool(tc.function.name, args)
            preview = result.replace("\n", " ")[:90]
            print(f"   [Tool] {tc.function.name}({list(args)}) -> {preview!r}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    return "(Abbruch: maximale Schrittzahl erreicht)"


# --------------------------------------------------------------------------
# Git-Sauberkeitscheck (Rollback-Punkt) + eingebaute Verifikation
# --------------------------------------------------------------------------
def git_status_hint():
    try:
        r = subprocess.run(
            ["git", "-C", PROJECT_ROOT, "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            print("Hinweis: kein Git-Repo erkannt — Rollback dann manuell.")
            return
        if r.stdout.strip():
            print("WARNUNG: uncommittete Aenderungen vorhanden.")
            print("Fuer sauberen Rollback zuerst committen, z.B.:")
            print("  git -C '%s' add -A && git -C '%s' commit -m 'vor dev_agent-Lauf'"
                  % (PROJECT_ROOT, PROJECT_ROOT))
        else:
            print("Git-Status sauber — guter Rollback-Punkt.")
    except Exception as e:
        print(f"Git-Check uebersprungen: {e}")


# Aufgabe, die echtes Editieren testet: mehrstellige, kohaerente Aenderung.
DEV_TASK = (
    "Lies die Datei tool_demo.py. Fuege dort ein neues Tool 'multiply_numbers(a, b)' "
    "hinzu, vollstaendig analog zu 'add_numbers': (1) die Python-Funktion, (2) den "
    "Schema-Eintrag in der TOOLS-Liste, (3) den Eintrag im DISPATCH-Dict. Aendere sonst "
    "nichts. Schreibe die vollstaendige geaenderte Datei mit write_file zurueck."
)


def main():
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    git_status_hint()
    print(f"\n{'='*70}\nAUFGABE: {DEV_TASK[:70]}...\n{'='*70}")
    answer = chat(DEV_TASK)
    print(f"\nANTWORT:\n{answer}")

    # Eingebauter Test: hat das Modell valides Python produziert?
    target = os.path.join(PROJECT_ROOT, "tool_demo.py")
    print(f"\n{'-'*70}\nVERIFIKATION: py_compile auf tool_demo.py")
    r = subprocess.run(["python3", "-m", "py_compile", target], capture_output=True, text=True)
    if r.returncode == 0:
        print("  -> OK, kompiliert sauber.")
    else:
        print("  -> FEHLER, kompiliert NICHT:")
        print(r.stderr)


if __name__ == "__main__":
    main()
