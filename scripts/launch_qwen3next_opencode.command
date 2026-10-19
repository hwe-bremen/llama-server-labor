#!/bin/bash
#
# Qwen3-Coder-Next 80B (Slipstream-PGRN) fuer OpenCode: Kontext 131072 (doppelklickbar)
# ------------------------------------------------------------------------------------
# Wie launch_qwen3next.command, aber mit grossem Kontext. Grund (Diagnose 19.10.): OpenCode
# verdichtet den Verlauf bei (Kontextlimit - Output-Reserve); mit 65536 passierte das bei ~57k
# Token und kostete jeweils ein komplettes Neueinlesen (zusammen ~2 h im Umsetzungslauf).
# In ~/.config/opencode/opencode.json muss beim Modell "Qwen3-Coder-Next-80B-A3B"
# "limit.context" ebenfalls 131072 sein.
#
# Cache: automatisch (groesster passender, max 24 GiB). Vorher Lab beenden, ggf. sudo purge.
# Mode B: Lab. Beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CTX="${CTX:-131072}"
exec bash "$HERE/launch_qwen3next.command" "$@"
