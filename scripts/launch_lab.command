#!/bin/bash
#
# Lab-Orchestrator (macOS, doppelklickbar)
# ----------------------------------------
# Startet MCP-Server + llama-server-Router mit einem Aufruf und oeffnet die
# MCP-faehige URL (127.0.0.1:8080). Ctrl+C stoppt beide.
#
# Modus (read-only vs. write):
#   bash scripts/launch_lab.command           -> read-only (sicher, Default)
#   bash scripts/launch_lab.command write     -> write-faehig
#   Doppelklick launch_lab.command            -> read-only
#   Doppelklick launch_lab_write.command      -> write-faehig
#   (Env MCP_READONLY=0/1 wirkt nur, wenn KEIN Argument gegeben ist)
#
# Einzel-Launcher bleiben eigenstaendig nutzbar:
#   - nur MCP-Server: bash mcp-server/run_webui.sh
#   - nur Router    : scripts/launch_router.command
# Mode B: Lab, beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$HERE/.." && pwd)"
MCP_PORT="${MCP_PORT:-8787}"

# --- Modus aus 1. Argument bestimmen (explizites Argument gewinnt vor Env) ---
case "${1:-}" in
  write|rw|w) export MCP_READONLY=0 ;;
  read|ro|r)  export MCP_READONLY=1 ;;
  "")         export MCP_READONLY="${MCP_READONLY:-1}" ;;
  *) echo "Unbekannter Modus '${1:-}' (erlaubt: read | write) — nutze read-only."
     export MCP_READONLY=1 ;;
esac

if [ "${MCP_READONLY}" = "0" ]; then
  MODE_LABEL="WRITE (schreiben + loeschen erlaubt)"
else
  MODE_LABEL="read-only"
fi
echo "Lab-Modus: ${MODE_LABEL}"

# --- Hygiene: Warnung + Rollback-Check im Write-Modus ---
if [ "${MCP_READONLY}" = "0" ]; then
  echo "!!! Das Frontend-Modell darf jetzt Dateien SCHREIBEN und LOESCHEN."
  echo "    Eine unbedachte Chat-Eingabe kann Projektdateien veraendern."
  if git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    if [ -n "$(git -C "$PROJECT_ROOT" status --porcelain 2>/dev/null)" ]; then
      echo "    WARNUNG: uncommittete Aenderungen — fuer sauberen Rollback zuerst committen."
    else
      echo "    Git-Baum sauber — guter Rollback-Punkt."
    fi
  fi
fi
echo

# --- 1) MCP-Server im Hintergrund starten (nur wenn Port frei) ---
MCP_PID=""
if lsof -i ":${MCP_PORT}" >/dev/null 2>&1; then
  echo "MCP-Server laeuft bereits auf Port ${MCP_PORT} — nutze ihn (Modus evtl. abweichend!)."
else
  echo "Starte MCP-Server (${MODE_LABEL}) auf Port ${MCP_PORT} ..."
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
bash "$HERE/launch_router.command"
