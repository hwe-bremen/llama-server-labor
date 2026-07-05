"""
dev_agent_diff.py — Mode-B Experiment (Variante zu dev_agent.py).

Idee: Statt die ganze Datei neu schreiben zu lassen (fehleranfaellig bei
lokalen Modellen), gibt das Modell nur einen kleinen Diff: old_str -> new_str.
DIESES Skript wendet ihn per str.replace an — MIT assert-Guard: old_str muss
genau EINMAL vorkommen, sonst wird abgelehnt (kein stilles Zerschiessen).

Sicherheits-Scope: alle Tools fest auf PROJECT_ROOT begrenzt (Traversal-Schutz).
NIEMALS auf produktive AskValentinAI-Repos richten -> das waere Mode A.

Rollback: Projekt liegt unter Git. Vor dem Lauf committen, dann
`git checkout -- scripts/tool_demo.py`.

Voraussetzung: llama-server MIT --jinja. Server laeuft aktuell auf 8081.
"""

import os
import json
import subprocess
from openai import OpenAI

BASE_URL = "http://localhost:8081/v1"  # Q6-Server laeuft auf 8081
PROJECT_ROOT = os.path.abspath("/Users/hans-wernereberhardt/PycharmProjects/llama-server")
MAX_STEPS = 10

client = OpenAI(base_url=BASE_URL, api_key="not-needed")


def _safe_path(relpath: str):
    full = os.path.abspath(os.path.join(PROJECT_ROOT, relpath))
    if full != PROJECT_ROOT and not full.startswith(PROJECT_ROOT + os.sep):
        return None
    return full


# --------------------------------------------------------------------------
# Tools
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
            continue
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


def apply_diff(path: str, old_str: str, new_str: str) -> str:
    """Ersetzt old_str durch new_str — nur wenn old_str GENAU EINMAL vorkommt."""
    full = _safe_path(path)
    if full is None:
        return "FEHLER: Pfad ausserhalb des Projekts verweigert."
    if not os.path.isfile(full):
        return f"FEHLER: Datei nicht gefunden: {path}"
    if not old_str:
        return "FEHLER: old_str ist leer."
    with open(full, "r", encoding="utf-8") as f:
        src = f.read()

    # assert-Guard: eindeutige Trefferstelle erzwingen
    count = src.count(old_str)
    if count == 0:
        return "FEHLER: old_str nicht gefunden. Anker exakt aus read_file kopieren."
    if count > 1:
        return f"FEHLER: old_str nicht eindeutig ({count} Treffer). Groesseren, eindeutigen Anker waehlen."

    new_src = src.replace(old_str, new_str)
    with open(full, "w", encoding="utf-8") as f:
        f.write(new_src)
    delta = len(new_src) - len(src)
    return f"OK: 1 Ersetzung in {path} ({delta:+d} Zeichen)."


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Listet Dateien/Ordner im Projekt.",
            "parameters": {
                "type": "object",
                "properties": {"subdir": {"type": "string", "description": "relativer Unterordner, Standard '.'"}},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Liest den Inhalt einer Projektdatei.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "relativer Pfad, z.B. 'scripts/tool_demo.py'"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_diff",
            "description": (
                "Ersetzt eine EINDEUTIGE Textstelle in einer Datei. old_str muss "
                "woertlich und genau einmal in der Datei vorkommen (inkl. Einrueckung)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "relativer Pfad, z.B. 'scripts/tool_demo.py'"},
                    "old_str": {"type": "string", "description": "exakter, eindeutiger Textblock aus der Datei"},
                    "new_str": {"type": "string", "description": "der Ersatztext"},
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
]

DISPATCH = {
    "list_files": list_files,
    "read_file": read_file,
    "apply_diff": apply_diff,
}


def run_tool(name: str, args: dict) -> str:
    fn = DISPATCH.get(name)
    if fn is None:
        return f"FEHLER: unbekanntes Tool '{name}'"
    try:
        return str(fn(**args))
    except Exception as e:
        return f"FEHLER bei {name}: {e}"


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


def git_status_hint():
    try:
        r = subprocess.run(
            ["git", "-C", PROJECT_ROOT, "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode != 0:
            print("Hinweis: kein Git-Repo erkannt — Rollback dann manuell.")
        elif r.stdout.strip():
            print("WARNUNG: uncommittete Aenderungen. Fuer sauberen Rollback zuerst committen.")
        else:
            print("Git-Status sauber — guter Rollback-Punkt.")
    except Exception as e:
        print(f"Git-Check uebersprungen: {e}")


DEV_TASK = (
    "Du sollst scripts/tool_demo.py um ein Tool 'multiply_numbers(a, b)' erweitern, analog "
    "zu 'add_numbers'. Vorgehen: (1) Lies scripts/tool_demo.py mit read_file. (2) Fuege mit "
    "apply_diff an DREI Stellen etwas hinzu — die Python-Funktion, den Schema-Eintrag "
    "in TOOLS, den Eintrag in DISPATCH. Nutze fuer jeden apply_diff einen kleinen, "
    "EINDEUTIGEN Anker (old_str woertlich aus der Datei, inkl. Einrueckung) und haenge "
    "im new_str den alten Anker plus deine Ergaenzung an. Schreibe NICHT die ganze Datei."
)


def main():
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    git_status_hint()
    print(f"\n{'='*70}\nAUFGABE (diff-basiert): multiply_numbers einbauen\n{'='*70}")
    answer = chat(DEV_TASK)
    print(f"\nANTWORT:\n{answer}")

    target = os.path.join(PROJECT_ROOT, "scripts", "tool_demo.py")
    print(f"\n{'-'*70}\nVERIFIKATION: py_compile auf scripts/tool_demo.py")
    r = subprocess.run(["python3", "-m", "py_compile", target], capture_output=True, text=True)
    if r.returncode == 0:
        print("  -> OK, kompiliert sauber.")
    else:
        print("  -> FEHLER, kompiliert NICHT:")
        print(r.stderr)


if __name__ == "__main__":
    main()
