#!/bin/bash
#
# Lab-Orchestrator (macOS, doppelklickbar)
# ----------------------------------------
# Startet das komplette Web-UI-Lab mit EINEM Aufruf:
#   1) MCP-Server (read-only) auf Port 8787  -> Tools fuer die Web-UI
#   2) llama-server-Router auf Port 8080     -> Modelle + Chat-UI (127.0.0.1)
# Beim Beenden (Ctrl+C) werden beide Dienste gemeinsam gestoppt.
#
# Die Einzel-Launcher bleiben eigenstaendig nutzbar:
#   - nur MCP-Server: bash mcp-server/run_webui.sh
#   - nur Router    : scripts/launch_router.command
#
# Schreibzugriff im Frontend statt read-only: MCP_READONLY=0 vor dem Start
# setzen (idealerweise vorher committen). Mode B: Lab, beruehrt AskValentinAI
# nicht.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$HERE/.." && pwd)"
MCP_PORT="${MCP_PORT:-8787}"

# --- 1) MCP-Server im Hintergrund starten (nur wenn Port frei) ---
MCP_PID=""
if lsof -i ":${MCP_PORT}" >/dev/null 2>&1; then
  echo "MCP-Server laeuft bereits auf Port ${MCP_PORT} — nutze ihn."
else
  echo "Starte MCP-Server (read-only) auf Port ${MCP_PORT} ..."
  bash "$PROJECT_ROOT/mcp-server/run_webui.sh" &
  MCP_PID=$!
fi

# --- MCP-Server beim Beenden mit aufraeumen (nur den selbst gestarteten) ---
cleanup() {
  if [ -n "${MCP_PID}" ]; then
    echo
    echo "Stoppe MCP-Server (Port ${MCP_PORT}) ..."
    kill "${MCP_PID}" 2>/dev/null
  fi
}
trap cleanup EXIT

# --- 2) Router im Vordergrund (oeffnet Browser, blockiert bis Ctrl+C) ---
# Kein exec: nach Router-Ende soll der cleanup-trap noch laufen.
bash "$HERE/launch_router.command"
