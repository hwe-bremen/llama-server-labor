# agents/

Konkrete Agenten (jeweils eigenstaendig lauffaehig, sprechen den llama-server
per OpenAI-kompatibler API an).

Belegung:
- dev_agent.py       (laesst das Modell tool_demo.py per write_file editieren)
- dev_agent_diff.py  (Diff-Variante: apply_diff mit Eindeutigkeits-Guard)
- excel_agent.py     (liest Einkaufslisten aus ../einkauf/)
- llama_harness.py   (lokales Modell als MCP-Agent: nutzt die scope-
                      geschuetzten Tools des mcp-server/ per MCP-Client)

Pfad-Hinweis: dev_agent.py und dev_agent_diff.py operieren auf
scripts/tool_demo.py (Task-Text + py_compile-Verifikation wurden beim
Verschieben entsprechend angepasst).

llama_harness.py braucht im Ausfuehrungs-venv sowohl `openai` als auch `mcp`
und startet den MCP-Server (mcp-server/lab_mcp_server.py) selbst als
stdio-Subprozess. Details oben im Datei-Docstring.
