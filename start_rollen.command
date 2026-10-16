#!/bin/bash
#
# START 1/2 — Lab mit Rollen (normaler Betrieb), doppelklickbar
# ---------------------------------------------------------------
# Immer gleich, keine Optionen:
#   - MCP-Server 8787 mit Schreibrechten, Schreibgrenze docs/projekt_management + docs/research
#   - Router 8080, Gedaechtnis-Proxy 8091, Rollen-Proxy 8092 (@review / @research / @aus)
#   - Tailscale Serve -> 8092: erreichbar vom Mac, iPad und Mac mini im Tailnet
#   - Mac schlaeft nicht ein, solange das Fenster offen ist
# Browser Mac: http://127.0.0.1:8092   remote: die .ts.net-URL aus dem Banner
# Ctrl+C stoppt alles und setzt Serve zurueck.
#
# Wechsel zum Eval-Lauf: hier Ctrl+C, dann start_eval.command.
# Mode B: Lab, beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

export MCP_WRITE_ROOTS="docs/projekt_management,docs/research"
export MCP_ALLOW_GITLOG=1
export LAB_MEMORY=1
export LAB_BIND=serve
export LAB_KEEP_SERVE=0
unset ROLE_UPSTREAM LAB_MODELS_MAX LAB_SERVE_PORT

echo "=============================================================="
echo " START: ROLLEN-LAUF   (Gedaechtnis an, git_log an, Tailnet an)"
echo "=============================================================="
exec caffeinate -s bash "$HERE/scripts/launch_lab_roles.command"
