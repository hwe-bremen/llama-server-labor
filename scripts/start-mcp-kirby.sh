#!/usr/bin/env bash
# MCP-Server-Instanz fuer ein Kirby-Testprojekt.
# READ-ONLY, Port 8788, nur localhost. Aufruf: ./scripts/start-mcp-kirby.sh ~/Sites/<projekt>
set -euo pipefail
REPO="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
KIRBY_DIR="${1:-$HOME/Sites/bremer-kke.de}"
#KIRBY_DIR="${1:?Aufruf: $0 <pfad-zum-kirby-projekt>}"
KIRBY_DIR="$(cd "$KIRBY_DIR" && pwd -P)"
if ! git -C "$KIRBY_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "WARNUNG: $KIRBY_DIR ist kein Git-Repo — vor Schreibzugriffen 'git init' + Commit."
fi
export MCP_SCOPE_ROOT="$KIRBY_DIR" MCP_PORT=8788 MCP_HOST=127.0.0.1 \
       MCP_READONLY=1 MCP_ALLOW_PYTHON=0 MCP_TRANSPORT=streamable-http
echo "=== MCP Kirby | Scope: $MCP_SCOPE_ROOT | 127.0.0.1:$MCP_PORT | READONLY ==="
exec "$REPO/.venv/bin/python" "$REPO/mcp-server/lab_mcp_server.py"
