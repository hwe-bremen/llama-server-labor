#!/usr/bin/env bash
# Stufe-4-Sonde starten (Experiment). Laeuft NEBEN start_rollen.command,
# eigener Port 8789, nur 127.0.0.1. Ctrl+C beendet.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
PY="$ROOT/mcp-server/.venv/bin/python"   # dasselbe venv wie der Lab-MCP-Server
if [[ ! -x "$PY" ]]; then
  echo "Fehlt: $PY  (venv des Lab-MCP-Servers)"; exit 1
fi
if lsof -ti :"${PROBE_PORT:-8789}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port ${PROBE_PORT:-8789} ist belegt – Sonde laeuft schon?"; exit 1
fi
exec "$PY" "$HERE/probe_mcp.py"
