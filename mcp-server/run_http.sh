#!/usr/bin/env bash
# Startet den Server im streamable-http-Modus (fuer MCP-Inspector-Tests und
# spaeter das iPad/Tailscale-Szenario). Fuer Claude Desktop wird NICHT dieses
# Skript genutzt, sondern der stdio-Eintrag in claude_desktop_config.json.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Scope = Projekt-Root = Elternordner von mcp-server/ (aufhebbar per Env).
PROJECT_ROOT="$(cd "$HERE/.." && pwd)"

export MCP_SCOPE_ROOT="${MCP_SCOPE_ROOT:-$PROJECT_ROOT}"
export MCP_TRANSPORT="${MCP_TRANSPORT:-streamable-http}"
export MCP_HOST="${MCP_HOST:-127.0.0.1}"   # NUR localhost. Exposition = bewusste Entscheidung.
export MCP_PORT="${MCP_PORT:-8787}"
# Schreibende/gefaehrliche Tools bleiben konservativ, bis bewusst aktiviert:
export MCP_ALLOW_PYTHON="${MCP_ALLOW_PYTHON:-0}"

exec "$HERE/.venv/bin/python" "$HERE/lab_mcp_server.py"
