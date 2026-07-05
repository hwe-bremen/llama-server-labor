"""
Mode-B Tool-Calling-Demo gegen llama-server.

Zeigt mechanisch, wie ein Agent funktioniert: Das Modell gibt strukturierte
Tool-Calls zurueck, DIESES Skript fuehrt sie aus und reicht das Ergebnis
zurueck. Zwei Beispiel-Tools:
  - add_numbers(a, b)          -> reine Rechenfunktion
  - read_textfile(filename)    -> liest NUR aus ./sandbox (kein Ausbruch)

Voraussetzung: llama-server MIT --jinja gestartet, z.B.:
  llama-server -hf JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q6_K --port 8080 --jinja

Hinweis: Tool-Calling ist quantisierungs-empfindlich. Q6_K liefert deutlich
robustere Tool-Argumente als Q4. Wenn Argumente leer/kaputt sind -> Q6 nehmen.

Mode B: synthetisch, isoliert, Rollback = Datei loeschen. Keine AskValentinAI-
Imports, kein Zugriff ausserhalb ./sandbox.
"""

import os
import json
from openai import OpenAI

BASE_URL = "http://localhost:8080/v1"
SANDBOX = os.path.abspath("/Users/hans-wernereberhardt/PycharmProjects/llama-server/sandbox")
MAX_STEPS = 6  # Sicherheitsnetz gegen Endlosschleifen

client = OpenAI(base_url=BASE_URL, api_key="not-needed")


# --------------------------------------------------------------------------
# Tools (die tatsaechlichen Python-Funktionen)
# --------------------------------------------------------------------------
def add_numbers(a: float, b: float) -> float:
    return a + b


def read_textfile(filename: str) -> str:
    """Liest eine Datei — ausschliesslich innerhalb von ./sandbox."""
    full = os.path.abspath(os.path.join(SANDBOX, filename))
    # Sandbox-Schutz: Pfad muss INNERHALB von SANDBOX liegen (kein ../-Ausbruch)
    if full != SANDBOX and not full.startswith(SANDBOX + os.sep):
        return "FEHLER: Zugriff ausserhalb der Sandbox verweigert."
    if not os.path.isfile(full):
        return f"FEHLER: Datei nicht gefunden: {filename}"
    with open(full, "r", encoding="utf-8") as f:
        return f.read()


# --------------------------------------------------------------------------
# Tool-Schemas (das, was das Modell zu sehen bekommt) + Dispatch
# --------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_numbers",
            "description": "Addiert zwei Zahlen und gibt die Summe zurueck.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "erster Summand"},
                    "b": {"type": "number", "description": "zweiter Summand"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_textfile",
            "description": "Liest den Inhalt einer Textdatei aus dem sandbox-Ordner.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Dateiname innerhalb von ./sandbox, z.B. 'beispiel.txt'",
                    },
                },
                "required": ["filename"],
            },
        },
    },
]

DISPATCH = {
    "add_numbers": add_numbers,
    "read_textfile": read_textfile,
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
# Die Agenten-Schleife
# --------------------------------------------------------------------------
def chat(prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]

    for step in range(MAX_STEPS):
        resp = client.chat.completions.create(
            model="local",
            messages=messages,
            tools=TOOLS,
            temperature=0.2,
        )
        msg = resp.choices[0].message

        # Kein Tool-Call -> das ist die finale Antwort.
        if not msg.tool_calls:
            return msg.content or ""

        # Assistant-Nachricht MIT den Tool-Calls in die Historie aufnehmen.
        messages.append(
            {
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        # Jeden Tool-Call ausfuehren und Ergebnis zurueckreichen.
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            result = run_tool(tc.function.name, args)
            print(f"   [Tool] {tc.function.name}({args}) -> {result[:80]!r}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    return "(Abbruch: maximale Schrittzahl erreicht)"


# --------------------------------------------------------------------------
# Sandbox beim Start vorbereiten (synthetische Demo-Datei)
# --------------------------------------------------------------------------
def ensure_sandbox():
    os.makedirs(SANDBOX, exist_ok=True)
    demo = os.path.join(SANDBOX, "beispiel.txt")
    if not os.path.isfile(demo):
        with open(demo, "w", encoding="utf-8") as f:
            f.write(
                "Notiz fuer den Tool-Calling-Test.\n"
                "AskValentinAI ist eine mandantenfaehige Chatbot-Plattform.\n"
                "Dieser Text ist synthetisch und dient nur der Demo.\n"
            )


DEMO_PROMPTS = [
    "Was ist 47 + 58? Nutze das passende Tool.",
    "Lies die Datei beispiel.txt und fasse ihren Inhalt in einem Satz zusammen.",
    # Sandbox-Test: sollte abgelehnt werden
    "Lies die Datei ../../etc/hosts.",
]


def main():
    ensure_sandbox()
    for p in DEMO_PROMPTS:
        print(f"\n{'='*70}\nPROMPT: {p}\n{'='*70}")
        answer = chat(p)
        print(f"\nANTWORT: {answer}")


if __name__ == "__main__":
    main()
