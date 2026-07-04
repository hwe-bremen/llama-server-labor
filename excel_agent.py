"""
excel_agent.py — Mode-B Experiment: LLM-Agent liest Excel-Einkaufslisten.

Variante B: Das MODELL macht die Aufbereitung (zusammenfassen, summieren,
Preis x Menge, nach Kategorie gruppieren, Gesamtsumme). Die Tools liefern
nur Rohdaten. So testest du, wie gut ein lokales Modell tabellarisch rechnet.

Scope: Tools fest auf EINKAUF_DIR begrenzt (Traversal-Schutz). Synthetische
Wegwerf-Daten, manueller Start, kein Dauerdienst.

Voraussetzung:
  - Router laeuft auf 8080 (dein launch_router.command)
  - pip install pandas openpyxl
"""


import os
import json
import subprocess
import pandas as pd
from openai import OpenAI

BASE_URL = "http://localhost:8080/v1"
PROJECT_ROOT = os.path.abspath("/Users/hans-wernereberhardt/PycharmProjects/llama-server")
EINKAUF_DIR = os.path.join(PROJECT_ROOT, "einkauf")
# Allgemeines Reasoning-Modell fuer Tabellen besser als der Code-Spezialist.
# Alternativen: "unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_XL"
MODEL = "unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL"
MAX_STEPS = 8

client = OpenAI(base_url=BASE_URL, api_key="not-needed")


# --------------------------------------------------------------------------
# Synthetische Testdaten anlegen (mit Duplikaten, damit "zusammenfassen" zaehlt)
# --------------------------------------------------------------------------
def ensure_demo_data():
    os.makedirs(EINKAUF_DIR, exist_ok=True)
    target = os.path.join(EINKAUF_DIR, "einkaufsliste.xlsx")
    if os.path.isfile(target):
        return
    rows = [
        ("Apfel", "Obst", 3, 0.50),
        ("Banane", "Obst", 5, 0.30),
        ("Milch", "Milchprodukte", 2, 1.20),
        ("Apfel", "Obst", 2, 0.50),          # Duplikat -> Apfel gesamt 5
        ("Kaese", "Milchprodukte", 1, 3.50),
        ("Brot", "Backwaren", 2, 2.00),
        ("Milch", "Milchprodukte", 1, 1.20),  # Duplikat -> Milch gesamt 3
        ("Butter", "Milchprodukte", 1, 2.40),
    ]
    df = pd.DataFrame(rows, columns=["Artikel", "Kategorie", "Menge", "Einzelpreis"])
    df.to_excel(target, index=False)


# --------------------------------------------------------------------------
# Scope-Guard + Tools (read-only, auf EINKAUF_DIR begrenzt)
# --------------------------------------------------------------------------
def _safe_path(relpath: str):
    full = os.path.abspath(os.path.join(EINKAUF_DIR, relpath))
    if full != EINKAUF_DIR and not full.startswith(EINKAUF_DIR + os.sep):
        return None
    return full


def list_excel_files() -> str:
    if not os.path.isdir(EINKAUF_DIR):
        return "FEHLER: Ordner fehlt."
    files = [n for n in sorted(os.listdir(EINKAUF_DIR)) if n.lower().endswith((".xlsx", ".xls"))]
    return "\n".join(files) if files else "(keine Excel-Dateien)"


def read_excel(filename: str) -> str:
    """Liest eine Excel-Datei aus EINKAUF_DIR und gibt die Zeilen als Text zurueck."""
    full = _safe_path(filename)
    if full is None:
        return "FEHLER: Pfad ausserhalb des Ordners verweigert."
    if not os.path.isfile(full):
        return f"FEHLER: Datei nicht gefunden: {filename}"
    try:
        df = pd.read_excel(full)  # pandas nutzt openpyxl fuer xlsx
    except Exception as e:
        return f"FEHLER beim Lesen: {e}"
    # Kompakt und modell-freundlich als CSV-artiger Text.
    return df.to_csv(index=False)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_excel_files",
            "description": "Listet die Excel-Dateien im Einkauf-Ordner.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_excel",
            "description": "Liest eine Excel-Einkaufsliste und gibt die Zeilen zurueck.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Dateiname, z.B. 'einkaufsliste.xlsx'"}
                },
                "required": ["filename"],
            },
        },
    },
]

DISPATCH = {"list_excel_files": list_excel_files, "read_excel": read_excel}


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
            model=MODEL, messages=messages, tools=TOOLS, temperature=0.2
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


TASK = (
    "Im Einkauf-Ordner liegt mindestens eine Excel-Einkaufsliste. Vorgehen: "
    "(1) Liste die Excel-Dateien. (2) Lies die Einkaufsliste. (3) Bereite sie auf:\n"
    "- fasse gleiche Artikel zusammen und summiere ihre Mengen,\n"
    "- berechne pro Artikel Einzelpreis x Gesamtmenge,\n"
    "- gruppiere nach Kategorie,\n"
    "- bilde die Gesamtsumme ueber alles.\n"
    "Gib das Ergebnis als uebersichtliche Tabelle plus Gesamtsumme aus."
)


def main():
    ensure_demo_data()
    print(f"Einkauf-Ordner: {EINKAUF_DIR}")
    print(f"Modell: {MODEL}")
    print(f"\n{'='*70}\nAUFGABE: Einkaufsliste aufbereiten\n{'='*70}")
    answer = chat(TASK)
    print(f"\nANTWORT:\n{answer}")


if __name__ == "__main__":
    main()
