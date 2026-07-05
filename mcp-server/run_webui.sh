#!/usr/bin/env bash
# Startet den MCP-Server fuer die llama.cpp Web-UI (browser-basierter MCP-Client).
#
# Default: READ-ONLY — das lokale Modell im Frontend bekommt nur lesende Tools
# (list_directory, read_file, search_files, git_status/diff/log). Kein
# write/delete/commit, kein Code-Exec. Fuer bewussten Schreibzugriff:
#     MCP_READONLY=0 bash mcp-server/run_webui.sh
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$HERE/.." && pwd)"

export MCP_SCOPE_ROOT="${MCP_SCOPE_ROOT:-$PROJECT_ROOT}"
export MCP_TRANSPORT="streamable-http"
export MCP_HOST="${MCP_HOST:-127.0.0.1}"    # NUR localhost. Exposition = bewusste Entscheidung + ACL.
export MCP_PORT="${MCP_PORT:-8787}"
export MCP_READONLY="${MCP_READONLY:-1}"     # sicherer Default fuers Frontend
export MCP_ALLOW_PYTHON="0"

echo "=================================================="
echo " MCP-Server fuer die llama.cpp Web-UI"
echo "  UI-Server-URL : http://${MCP_HOST}:${MCP_PORT}/mcp"
echo "  Scope         : ${MCP_SCOPE_ROOT}"
echo "  READONLY      : ${MCP_READONLY}   (Schreibzugriff: MCP_READONLY=0)"
echo "--------------------------------------------------"
echo " In der Web-UI (WICHTIG: ueber http://127.0.0.1:8080 oeffnen, NICHT localhost):"
echo "  1) MCP Servers -> Add New Server -> URL: http://${MCP_HOST}:${MCP_PORT}/mcp"
echo "  2) Server per Stift-Icon EDITIEREN -> Toggle 'use llama-server proxy' AN"
echo "     (der Toggle erscheint NUR beim Editieren, nicht beim Hinzufuegen)"
echo "  Voraussetzung: llama-server mit --jinja UND --ui-mcp-proxy gestartet."
echo "=================================================="

exec "$HERE/.venv/bin/python" "$HERE/lab_mcp_server.py"
