#!/bin/bash
#
# Qwen3-Coder-Next 80B-A3B per Slipstream-PGRN-Streaming (macOS, doppelklickbar)
# -----------------------------------------------------------------------------
# Duenner Wrapper um experiments/slipstream_20261017/qwen3next_reproducible_build/start_qwen3next.command
# (dort Logik, Pruefungen und Doku). Eigener Server auf 127.0.0.1:8083, laeuft neben dem Labor
# (8080/8091/8092/8787 werden nicht angefasst). Fenster offen lassen; Ctrl+C beendet.
#
# Einstellungen per Env, z. B.:
#   bash scripts/launch_qwen3next.command
#   CACHE_GB=18 CTX=32768 bash scripts/launch_qwen3next.command
# OpenAI-API: http://127.0.0.1:8083/v1, Modell "Qwen3-Coder-Next-80B-A3B". Laden ca. 5 min.
#
# Achtung: launch_ipad.command raeumt mit 'pkill -f llama-server' ab und beendet dabei auch diesen Server.
# Mode B: Lab. Beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$HERE/../experiments/slipstream_20261017/qwen3next_reproducible_build/start_qwen3next.command"
[ -f "$TARGET" ] || { echo "ABBRUCH: $TARGET fehlt"; exit 1; }
exec bash "$TARGET" "$@"
