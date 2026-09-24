"""
mcp_agent.py — wiederverwendbare MCP-Agenten-Basis.

Kapselt: Verbindung zu einem MCP-Server (stdio-Subprozess), Abruf + Konvertierung
der Tools ins OpenAI-Format, automatische Modellwahl und die Tool-Call-Schleife
gegen ein OpenAI-kompatibles Modell (z.B. llama-server).

Zwei Nutzungsarten:

    # one-shot (Session wird intern geoeffnet und geschlossen)
    answer = await MCPAgent(scope_root=ROOT).run("Liste die Dateien.")

    # persistent (mehrere Turns, EINE Session, fortgefuehrte Historie)
    async with MCPAgent(scope_root=ROOT) as agent:
        await agent.run("Lies config/models.ini.", keep_history=True)
        await agent.run("Welche Temperatur hat das erste Modell?", keep_history=True)

Sicherheit: Der MCP-Server bringt Scope-Guard + Tool-Whitelist selbst mit. Hier
wird er per Default mit MCP_ALLOW_PYTHON=0 gestartet; readonly/allow_python sind
bewusste Flags. Kein freier Shell-Zugriff — nur die Tools des MCP-Servers.
"""
from __future__ import annotations

import json
import os
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Callable, Optional

from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

DEFAULT_BASE_URL = "http://localhost:8080/v1"

# Default-Systemprompt fuer alle Agenten auf dieser Basis. Hintergrund:
# kleinere/lokale Modelle brechen beim Schreiben groesserer Dateien mit
# Anfuehrungszeichen/Escapes (Python-Docstrings, f-Strings) regelmaessig mit
# ungueltigem JSON ab ("invalid string: missing closing quote"), weil
# verschachteltes Escaping (Python-Escape *in* JSON-Escape) fehleranfaellig
# ist. write_file bietet dafuer content_b64 (Base64) an, das strukturell
# keine Quotes/Backslashes/Newlines enthaelt.
#
# Messbefund 23.09.2026 (llama_harness, Aufgabe: models.ini lesen + Zusammen-
# fassung schreiben) — "IMMER content_b64" war die falsche Anweisung:
#   - Mellum2-12B-Q4 befolgt sie, erzeugt aber UNGUELTIGES Base64. write_file
#     scheitert zweimal, das Modell denkt rund 24.000 Zeichen und liefert am
#     Ende eine LEERE Antwort. Ohne Systemprompt loest dasselbe Modell die
#     Aufgabe in 3 Schritten mit content im Klartext fehlerfrei.
#   - Qwen3.6-27B schreibt content im Klartext ohne Escaping-Fehler.
# Base64 ist damit eine RUECKFALLEBENE fuer den konkreten Fehlerfall, keine
# Grundregel: Modelle, die es nicht sauber erzeugen koennen, werden sonst an
# einer Aufgabe festgehalten, die sie nicht beherrschen.
DEFAULT_SYSTEM_PROMPT = (
    "Du bist ein Agent mit Zugriff auf Datei-, Such- und Git-Tools ueber MCP.\n\n"
    "Beim Schreiben von Dateien (write_file) nutzt du normalerweise den "
    "Parameter content (Klartext). Nur wenn ein write_file-Aufruf an einem "
    "JSON-Fehler scheitert (z.B. 'invalid string', abgeschnittenes Argument, "
    "Probleme mit Anfuehrungszeichen, Backslashes oder Zeilenumbruechen), "
    "wiederholst du denselben Aufruf mit content_b64: dem vollstaendigen "
    "Dateiinhalt, als UTF-8 gelesen und korrekt Base64-kodiert. Base64 "
    "vermeidet Escaping-Fehler strukturell. Nutze content_b64 nur, wenn du "
    "die Kodierung zeichengenau erzeugen kannst — sonst bleib bei content und "
    "teile mit, woran der Schreibvorgang scheitert."
)


def default_logger(event: str, detail: str = "") -> None:
    """Simpler CLI-Logger; als on_event uebergebbar. Konsumenten koennen einen
    eigenen Callback (event, detail) reinreichen (z.B. fuer ein GUI/Chat)."""
    print(f"[{event}] {detail}" if detail else f"[{event}]")


def mcp_tools_to_openai(tools) -> list[dict]:
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


def result_to_text(result) -> str:
    """CallToolResult -> reiner Text (Content-Bloecke zusammenfuehren)."""
    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        parts.append(text if text is not None else str(block))
    body = "\n".join(parts) if parts else "(keine Ausgabe)"
    return ("[FEHLER] " + body) if getattr(result, "isError", False) else body


class MCPAgent:
    """Agent, der ein OpenAI-kompatibles Modell mit den Tools eines MCP-Servers
    verbindet und die Tool-Call-Schleife fuehrt."""

    def __init__(
        self,
        *,
        scope_root,
        server_script=None,
        server_python=None,
        base_url: str = DEFAULT_BASE_URL,
        model: Optional[str] = None,
        model_hint: str = "Mellum",
        max_steps: int = 8,
        readonly: bool = False,
        allow_python: bool = False,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        on_event: Optional[Callable[[str, str], None]] = None,
    ):
        self.scope_root = Path(scope_root).resolve()
        # Default: MCP-Server unter <scope_root>/mcp-server/
        self.server_script = (
            Path(server_script) if server_script else self.scope_root / "mcp-server" / "lab_mcp_server.py"
        )
        self.server_python = (
            Path(server_python) if server_python else self.scope_root / "mcp-server" / ".venv" / "bin" / "python"
        )
        self.base_url = base_url
        self.model = model            # None/"local" -> Auto-Discovery
        self.model_hint = model_hint
        self.max_steps = max_steps
        self.readonly = readonly
        self.allow_python = allow_python
        self.temperature = temperature
        # None -> nicht an den Client uebergeben (Server-Default greift).
        # Explizit setzen, falls finish_reason="length" beobachtet wird
        # (z.B. bei Thinking-Modellen, deren Denkkette das Budget aufbraucht).
        self.max_tokens = max_tokens
        # None -> Default-Systemprompt (siehe oben). "" (leerer String) ->
        # bewusst deaktiviert. Eigener String -> ersetzt den Default.
        self.system_prompt = DEFAULT_SYSTEM_PROMPT if system_prompt is None else system_prompt
        self.on_event = on_event or default_logger
        self.history: list[dict] = []
        self._stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None
        self._client: Optional[AsyncOpenAI] = None
        self._tools: Optional[list[dict]] = None
        self._resolved_model: Optional[str] = None

    # -- Konfiguration des MCP-Server-Subprozesses ---------------------------
    def _server_params(self) -> StdioServerParameters:
        env = {
            **os.environ,
            "MCP_TRANSPORT": "stdio",
            "MCP_SCOPE_ROOT": str(self.scope_root),
            "MCP_ALLOW_PYTHON": "1" if self.allow_python else "0",
        }
        if self.readonly:
            env["MCP_READONLY"] = "1"
        return StdioServerParameters(
            command=str(self.server_python), args=[str(self.server_script)], env=env
        )

    async def _resolve_model(self) -> str:
        if self.model and self.model != "local":
            return self.model
        try:
            listed = await self._client.models.list()
            ids = [m.id for m in listed.data]
        except Exception as e:
            self.on_event("modell", f"Discovery fehlgeschlagen ({e}) -> '{self.model or 'local'}'")
            return self.model or "local"
        if not ids:
            self.on_event("modell", "Router meldet keine Modelle")
            return self.model or "local"
        for mid in ids:
            if self.model_hint.lower() in mid.lower():
                self.on_event("modell", f"auto: {mid} (Hinweis '{self.model_hint}')")
                return mid
        self.on_event("modell", f"auto: {ids[0]} (erstes; verfuegbar: {', '.join(ids)})")
        return ids[0]

    # -- Session-Lifecycle (persistent via async with, oder intern one-shot) --
    async def __aenter__(self):
        await self._open()
        return self

    async def __aexit__(self, *exc):
        await self._close()

    async def _open(self):
        self._stack = AsyncExitStack()
        read, write = await self._stack.enter_async_context(stdio_client(self._server_params()))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        listed = await self._session.list_tools()
        self._tools = mcp_tools_to_openai(listed.tools)
        self.on_event(
            "tools", f"{len(self._tools)}: {', '.join(t['function']['name'] for t in self._tools)}"
        )
        if self.readonly:
            self.on_event("modus", "READONLY (nur lesende Tools)")
        self._client = AsyncOpenAI(base_url=self.base_url, api_key="not-needed")
        self._resolved_model = await self._resolve_model()

    async def _close(self):
        if self._stack:
            await self._stack.aclose()
        self._stack = self._session = self._client = self._tools = None

    # -- Ausfuehrung ---------------------------------------------------------
    async def run(self, task: str, *, keep_history: bool = False) -> str:
        """Eine Aufgabe abarbeiten. Ohne offene Session (kein async with) wird
        eine temporaere Session fuer diesen Aufruf geoeffnet und geschlossen."""
        if self._session is None:
            async with self:
                return await self._loop(task, keep_history)
        return await self._loop(task, keep_history)

    async def _loop(self, task: str, keep_history: bool) -> str:
        messages = self.history if keep_history else []
        if self.system_prompt and not any(m.get("role") == "system" for m in messages):
            messages.insert(0, {"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": task})
        for step in range(self.max_steps):
            kwargs = dict(
                model=self._resolved_model,
                messages=messages,
                tools=self._tools,
                temperature=self.temperature,
            )
            if self.max_tokens is not None:
                kwargs["max_tokens"] = self.max_tokens
            try:
                resp = await self._client.chat.completions.create(**kwargs)
            except Exception as e:
                return f"[Modell-Fehler] {type(e).__name__}: {e}"

            choice = resp.choices[0]
            msg = choice.message
            reasoning = getattr(msg, "reasoning_content", None)
            self.on_event(
                "antwort",
                f"schritt={step + 1} finish_reason={choice.finish_reason} "
                f"content_len={len(msg.content or '')} "
                f"reasoning_len={len(reasoning) if reasoning else 0} "
                f"tool_calls={len(msg.tool_calls or [])}",
            )

            if not msg.tool_calls:
                if keep_history:
                    messages.append({"role": "assistant", "content": msg.content or ""})
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
                result = await self._session.call_tool(tc.function.name, args)
                text = result_to_text(result)
                self.on_event(
                    "tool", f"{tc.function.name}({list(args)}) -> {text.replace(chr(10), ' ')[:80]!r}"
                )
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": text})
        return "(Abbruch: maximale Schrittzahl erreicht)"
