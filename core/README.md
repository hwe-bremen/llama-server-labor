# core/

Wiederverwendbare Bausteine, die mehrere Agenten/Skripte teilen.

Belegung:
- mcp_agent.py   MCPAgent: verbindet ein OpenAI-kompatibles Modell (llama-server)
                 mit den Tools eines MCP-Servers und faehrt die Tool-Call-Schleife.
                 One-shot:    await MCPAgent(scope_root=ROOT).run(task)
                 Persistent:  async with MCPAgent(...) as agent:
                                  await agent.run(t1, keep_history=True)
                                  await agent.run(t2, keep_history=True)
                 Der on_event-Callback macht Logging austauschbar (CLI vs. GUI/Chat).

Import aus einem Skript in einem Unterordner (Lab-Struktur ohne pip-Install):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from core.mcp_agent import MCPAgent

Genutzt von: agents/llama_harness.py
