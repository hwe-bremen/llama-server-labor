#!/bin/bash
#
# Review mit Qwen3-Coder-Next 80B (Slipstream-PGRN) wie im Review-Eval (doppelklickbar)
# ------------------------------------------------------------------------------------
# Startet in EINEM Fenster:
#   - MCP-Server 8787 wie start_eval: Schreibgrenze docs/projekt_management,docs/research, git_log AUS
#   - eigener Rollen-Proxy auf 8093 -> Upstream 8083 (der Labor-Proxy 8092 bleibt unberuehrt)
#   - Qwen3-Next-Server auf 8083 (scripts/launch_qwen3next.command), Kontext 65536
# Browser: http://127.0.0.1:8093  (MCP-Eintrag http://127.0.0.1:8787/mcp anlegen, dann per Stift EDITIEREN
#          und "Use llama-server proxy" AN;
#          Settings -> Tools: eingebaute Tools aus). Ctrl+C stoppt alles, was dieser Starter gestartet hat.
#
# Router 8080 und Gedaechtnis 8091 werden NICHT gestartet (Speicher gehoert dem 80B-Modell).
# Ueberschreibbar: CACHE_GB (auto = groesster passender, max 24), CTX (65536), ROLE_PORT (8093), MCP_PORT (8787).
# Mode B: Lab. Beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$HERE/.." && pwd)"
export MCP_WRITE_ROOTS="docs/projekt_management,docs/research"
export MCP_ALLOW_GITLOG=0
export MCP_READONLY=0
MCP_PORT="${MCP_PORT:-8787}"
ROLE_PORT="${ROLE_PORT:-8093}"
export CTX="${CTX:-65536}"
export MCP_PROXY=1   # Web-UI -> /cors-proxy des Servers -> MCP 8787 (wie im Labor-Router)
case "$ROLE_PORT" in 8080|8083|8091|8092|8787) echo "ABBRUCH: ROLE_PORT $ROLE_PORT ist belegt/reserviert"; exit 1;; esac

# --- MCP: vorhandenen Server nur mit genau dieser Konfiguration weiterbenutzen (fail-loud) ---
MCP_PID=""; MCP_STARTED=""
RUN_PID="$(lsof -ti ":${MCP_PORT}" -sTCP:LISTEN 2>/dev/null | head -n1)"
if [ -n "$RUN_PID" ]; then
  ENV_DUMP="$(ps eww -p "$RUN_PID" 2>/dev/null | tr ' ' '\n')"
  RUN_ROOTS="$(printf '%s\n' "$ENV_DUMP" | grep '^MCP_WRITE_ROOTS=' | head -n1 | cut -d= -f2-)"
  RUN_RO="$(printf '%s\n' "$ENV_DUMP" | grep '^MCP_READONLY=' | head -n1 | cut -d= -f2-)"
  RUN_GL="$(printf '%s\n' "$ENV_DUMP" | grep '^MCP_ALLOW_GITLOG=' | head -n1 | cut -d= -f2-)"
  if [ "$RUN_ROOTS" != "$MCP_WRITE_ROOTS" ] || [ "$RUN_RO" != "0" ] || [ "${RUN_GL:-1}" != "0" ]; then
    echo "ABBRUCH: Auf ${MCP_PORT} laeuft ein MCP-Server (PID ${RUN_PID}) mit anderer Konfiguration"
    echo "         (Schreibgrenze='${RUN_ROOTS:-?}', readonly='${RUN_RO:-?}', git_log='${RUN_GL:-1}'). Erst beenden."
    exit 1
  fi
  echo "MCP-Server auf ${MCP_PORT} passt (Schreibgrenze, git_log aus) — wird weiterbenutzt."
else
  echo "Starte MCP-Server auf ${MCP_PORT} (Schreibgrenze ${MCP_WRITE_ROOTS}, git_log aus) ..."
  ( cd "$PROJECT_ROOT" && exec bash "$PROJECT_ROOT/mcp-server/run_webui.sh" ) &
  MCP_PID=$!; MCP_STARTED=1
fi

# --- eigener Rollen-Proxy -> 8083 ---
if [ -n "$(lsof -ti ":${ROLE_PORT}" -sTCP:LISTEN 2>/dev/null)" ]; then
  echo "ABBRUCH: Port ${ROLE_PORT} ist belegt."; [ -n "$MCP_PID" ] && kill "$MCP_PID" 2>/dev/null; exit 1
fi
( cd "$PROJECT_ROOT/role-split" && ROLE_PORT="$ROLE_PORT" ROLE_UPSTREAM="http://127.0.0.1:8083" \
    ROLE_DEFAULT_MODEL="Qwen3-Coder-Next-80B-A3B" exec python3 role_proxy.py ) &
ROLE_PID=$!

cleanup() {
  echo; echo "Stoppe Rollen-Proxy (${ROLE_PORT}) ..."; kill "$ROLE_PID" 2>/dev/null
  if [ -n "$MCP_STARTED" ]; then echo "Stoppe MCP-Server (${MCP_PORT}) ..."; pkill -P "$MCP_PID" 2>/dev/null; kill "$MCP_PID" 2>/dev/null; fi
}
trap cleanup EXIT INT TERM

echo
echo ">> Browser: http://127.0.0.1:${ROLE_PORT}   (erst nutzbar, wenn das Modell geladen ist, ca. 5 min)"
echo ">> Modell im Dropdown: Qwen3-Coder-Next-80B-A3B  -> Verdikt-Kuerzel qwen3-80b"
echo
# --- Qwen3-Next im Vordergrund ---
bash "$HERE/launch_qwen3next.command"
