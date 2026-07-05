"""
llama_harness.py — lokales Modell (llama-server) als MCP-Agent.

Verbindet das lokale Modell ueber die OpenAI-kompatible llama-server-API mit
dem llama-server-lab MCP-Server und faehrt die Tool-Call-Schleife:
  Modell schlaegt Tool-Call vor -> Harness ruft ihn per MCP aus -> Ergebnis
  zurueck ans Modell -> bis das Modell fertig ist.

Damit nutzt das lokale Modell exakt dieselben scope-geschuetzten Tools wie
Claude (list_directory, read_file, search_files, write_file, delete_file,
git_*). Der MCP-Server wird als stdio-Subprozess gestartet — kein Port, keine
Netzwerk-Exposition.

Sicherheit:
  - Scope-Guard + Tool-Whitelist kommen aus dem MCP-Server selbst.
  - Start mit MCP_ALLOW_PYTHON=0 (kein Code-Exec fuers lokale Modell).
  - Fuer vorsichtige erste Laeufe: HARNESS_READONLY=1 setzen -> der Server
    startet mit MCP_READONLY=1 (nur lesende Tools, kein write/delete/commit).
  - Vor schreibenden Laeufen committen (Rollback). Der Harness warnt, wenn der
    Git-Baum nicht sauber ist.

Voraussetzung:
  - llama-server (Router) laeuft auf 8080, MIT --jinja (Tool-Calling).
  - mcp-server/.venv existiert (mcp-server/setup.sh ausgefuehrt).
  - pip install openai mcp   (im venv, aus dem der Harness laeuft)

Start:
  python agents/llama_harness.py "Deine Aufgabe hier"
  python agents/llama_harness.py            # nutzt den read-only Default-Task
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --------------------------------------------------------------------------
# Konfiguration
# --------------------------------------------------------------------------
LLAMA_BASE_URL = os.environ.get("LLAMA_BASE_URL", "http://localhost:8080/v1")
# Bei llama-server ist der Modellname i.d.R. egal (ein Modell pro Port bzw.
# Router-Auswahl). Fuer den Router die exakte Modell-ID aus /v1/models setzen.
MODEL = os.environ.get("HARNESS_MODEL", "local")
MAX_STEPS = int(os.environ.get("HARNESS_MAX_STEPS", "8"))
READONLY = os.environ.get("HARNESS_READONLY", "0") == "1"

# agents/llama_harness.py -> Projekt-Root ist der Elternordner von agents/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER = PROJECT_ROOT / "mcp-server" / "lab_mcp_server.py"
MCP_PYTHON = PROJECT_ROOT / "mcp-server" / ".venv" / "bin" / "python"


def _server_params() -> StdioServerParameters:
    """Startparameter fuer den MCP-Server als stdio-Subprozess."""
    env = {
        **os.environ,
        "MCP_TRANSPORT": "stdio",
        "MCP_SCOPE_ROOT": str(PROJECT_ROOT),
        "MCP_ALLOW_PYTHON": "0",
    }
    if READONLY:
        env["MCP_READONLY"] = "1"
    return StdioServerParameters(command=str(MCP_PYTHON), args=[str(MCP_SERVER)], env=env)


def _mcp_tools_to_openai(tools) -> list[dict]:
    """MCP-Tool-Definitionen -> OpenAI-function-calling-Format."""
    out = []
    for t in tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema or {"type": "object", "properties": {}},
                },
            }
        )
    return out


def _result_to_text(result) -> str:
    """CallToolResult -> reiner Text (Content-Bloecke zusammenfuehren)."""
    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        parts.append(text if text is not None else str(block))
    body = "\n".join(parts) if parts else "(keine Ausgabe)"
    return ("[FEHLER] " + body) if getattr(result, "isError", False) else body


def _git_clean_hint() -> None:
    """Warnt, wenn uncommittete Aenderungen vorliegen (Rollback-Hygiene)."""
    try:
        r = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
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


# --------------------------------------------------------------------------
# Agenten-Schleife
# --------------------------------------------------------------------------
async def run(task: str) -> str:
    client = AsyncOpenAI(base_url=LLAMA_BASE_URL, api_key="not-needed")
    async with stdio_client(_server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            tools = _mcp_tools_to_openai(listed.tools)
            print(f"MCP-Tools ({len(tools)}): {', '.join(t.name for t in listed.tools)}")
            if READONLY:
                print("Modus: READONLY (nur lesende Tools).")

            messages = [{"role": "user", "content": task}]
            for _ in range(MAX_STEPS):
                resp = await client.chat.completions.create(
                    model=MODEL, messages=messages, tools=tools, temperature=0.2
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
                    result = await session.call_tool(tc.function.name, args)
                    text = _result_to_text(result)
                    preview = text.replace("\n", " ")[:90]
                    print(f"   [Tool] {tc.function.name}({list(args)}) -> {preview!r}")
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": text})
            return "(Abbruch: maximale Schrittzahl erreicht)"


DEFAULT_TASK = (
    "Liste die Dateien im Projekt-Root. Lies dann config/models.ini und fasse "
    "in zwei Saetzen zusammen, welche Modelle konfiguriert sind."
)


def main() -> None:
    task = " ".join(sys.argv[1:]).strip() or DEFAULT_TASK
    print(f"Modell-Endpoint: {LLAMA_BASE_URL}  (Modell: {MODEL})")
    print(f"Scope-Root     : {PROJECT_ROOT}")
    _git_clean_hint()
    print(f"{'='*70}\nAUFGABE: {task}\n{'='*70}")
    answer = asyncio.run(run(task))
    print(f"\nANTWORT:\n{answer}")


if __name__ == "__main__":
    main()
