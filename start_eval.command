#!/bin/bash
#
# START 2/2 — Review-Eval (Modellvergleich), doppelklickbar
# ---------------------------------------------------------------
# Wie start_rollen.command (MCP mit Schreibgrenze, Rollen-Proxy 8092, Tailnet,
# Mac wach), nur drei Dinge anders, damit Modelle fair verglichen werden:
#   - Rollen-Proxy geht direkt auf den Router 8080 (kein Gedaechtnis, kein LM_NO_THINK)
#   - immer nur ein Modell im Speicher (LAB_MODELS_MAX=1)
#   - git_log aus (Fix-Commits wuerden die Loesung verraten)
# Ablauf und Lösungsschluessel: role-split/eval/README.md
#
# Wechsel zum normalen Betrieb: hier Ctrl+C, dann start_rollen.command.
# Mode B: Lab, beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

export MCP_WRITE_ROOTS="docs/projekt_management,docs/research"
export MCP_ALLOW_GITLOG=0
export LAB_MEMORY=1
export LAB_BIND=serve
export LAB_KEEP_SERVE=0
export LAB_MODELS_MAX=1
export ROLE_UPSTREAM="http://127.0.0.1:8080"
unset LAB_SERVE_PORT

echo "=============================================================="
echo " START: EVAL-LAUF   (direkt auf 8080, 1 Modell, git_log aus, Tailnet an)"
echo "  Vor jedem Kandidaten: neuer Chat, eingebaute Tools (Settings -> Tools) aus,"
echo "  neues Modell vorher laden (curl .../models/load, siehe role-split/eval/README.md)."
echo "=============================================================="
exec caffeinate -s bash "$HERE/scripts/launch_lab_roles.command"
