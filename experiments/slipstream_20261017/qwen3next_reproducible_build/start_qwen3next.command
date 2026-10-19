#!/usr/bin/env bash
# Qwen3-Coder-Next 80B-A3B (Q4_K_M) mit Slipstream-PGRN-Streaming und Labor-Korrektur (pgrn_empty_ubatch_fix).
# Startet einen eigenen Server im Vordergrund; Strg+C beendet ihn. Bestehende Dienste werden nicht angefasst.
#
# Einstellbar per Umgebungsvariable, z. B.:  CACHE_GB=18 CTX=32768 bash start_qwen3next.command
#   PORT       (8083)    Host bleibt fest 127.0.0.1
#   CACHE_GB   (18)      PGRN-Expertencache in GiB  (18.10.: 18 GiB ~7,7 tok/s / 88,7 % Treffer; 12 GiB ~5,3 tok/s / 79 %)
#   HEADROOM_GB (8)      Reserve fuer das System
#   CTX        (16384)   Kontext; gemessen nur 4096 (fuer OpenCode eher 32768, KV-Bedarf ungeprueft)
#   IO_THREADS (leer)    --pgrn-io-threads, nur gesetzt wenn angegeben
#   VERBOSITY  (3)
#   MCP_PROXY  (0)       1 = --ui-mcp-proxy (Web-UI erreicht MCP 8787 ueber den Server; nur 127.0.0.1)
# Ubatch bleibt 25: Staging erlaubt max. 256 verschiedene Experten pro Layer und Schritt (25 x 10 = 250).
set -euo pipefail
B="$(cd "$(dirname "$0")" && pwd)"
BIN="$B/fixed/bin/llama-server-pgrn-fixed"
GGUF="/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf"
PGRN="$B/../pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn"
PORT="${PORT:-8083}"; CACHE_GB="${CACHE_GB:-18}"; HEADROOM_GB="${HEADROOM_GB:-8}"; CTX="${CTX:-16384}"
IO_THREADS="${IO_THREADS:-}"; VERBOSITY="${VERBOSITY:-3}"; MCP_PROXY="${MCP_PROXY:-0}"
die(){ echo "ABBRUCH: $*" >&2; exit 1; }

case "$PORT" in 8080|8091|8092|8787) die "Port $PORT gehoert zum Labor";; esac
[ -x "$BIN" ] || die "Binary fehlt: $BIN (bash build_fix.sh)"
[ "$(shasum -a 256 "$BIN" | awk '{print $1}')" = "$(cat "$BIN.sha256")" ] || die "Binary-Hash stimmt nicht"
[ -f "$GGUF" ] || die "GGUF fehlt – externe SSD angeschlossen?"
[ "$(stat -f %z "$GGUF")" = 48528320544 ] || die "GGUF-Groesse unerwartet"
[ -f "$PGRN" ] && [ "$(stat -f %z "$PGRN")" = 46909751296 ] || die "PGRN fehlt oder Groesse unerwartet"
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then die "Port $PORT ist belegt"; fi
FREE=$(memory_pressure -Q 2>/dev/null | sed -n 's/.*free percentage: \([0-9]*\)%.*/\1/p')
echo "Freier Speicher: ${FREE:-?} %   Cache: ${CACHE_GB} GiB   Reserve: ${HEADROOM_GB} GiB   Kontext: ${CTX}"
[ -z "$FREE" ] || [ "$FREE" -ge 50 ] || die "nur ${FREE} % frei (laeuft ein grosses Modell auf 8080?)"

# geerbte llama-Voreinstellungen nur fuer diesen Prozess entfernen
for v in $(env | sed -n 's/^\(LLAMA_ARG_[A-Z0-9_]*\)=.*/\1/p'); do unset "$v"; done

ARGS=(--model "$GGUF" --pgrn "$PGRN" --host 127.0.0.1 --port "$PORT" --alias Qwen3-Coder-Next-80B-A3B
      --ctx-size "$CTX" --pgrn-cache-gb "$CACHE_GB" --pgrn-headroom-gb "$HEADROOM_GB"
      --batch-size 25 --ubatch-size 25 --parallel 1 --spec-type none --reasoning off
      --gpu-layers 99 --jinja --verbosity "$VERBOSITY" --log-colors off)
[ -z "$IO_THREADS" ] || ARGS+=(--pgrn-io-threads "$IO_THREADS")
[ "$MCP_PROXY" != 1 ] || ARGS+=(--ui-mcp-proxy)

LOGDIR="$B/serve_logs"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/serve_$(date +%Y%m%dT%H%M%S)_c${CACHE_GB}.log"
echo "Log: $LOG"
echo "Laden dauert ca. 5 Minuten. Danach: http://127.0.0.1:$PORT  (OpenAI-API: http://127.0.0.1:$PORT/v1, Modell Qwen3-Coder-Next-80B-A3B)"
echo "Beenden mit Strg+C."
caffeinate -i "$BIN" "${ARGS[@]}" 2>&1 | tee "$LOG"
