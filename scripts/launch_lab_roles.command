#!/bin/bash
#
# Lab für role-split (doppelklickbar)
# -----------------------------------
# Startet in EINEM Fenster: MCP-Server mit Schreibgrenze + Router + Gedächtnis-Proxy
# (über launch_lab.command write) und den Rollen-Proxy auf 8092. Ctrl+C stoppt alles.
#
#   bash scripts/launch_lab_roles.command                 -> Browser: http://127.0.0.1:8092
#   LAB_BIND=serve bash scripts/launch_lab_roles.command  -> zusätzlich iPad/Büro über .ts.net
#   Büro-Tag (Serve bleibt, kein Ruhezustand): launch_lab_roles_remote.command
#
# Im serve-Modus zeigt Tailscale Serve auf den Rollen-Proxy (8092) statt auf 8091,
# damit @review/@research auch remote wirken. Der Rollen-Proxy selbst bleibt auf
# 127.0.0.1; nach außen öffnet nur Serve (Tailnet, wie bisher bei 8091).
#
# Fail-loud: Läuft auf 8787 schon ein MCP-Server, der NICHT mit genau dieser
# Schreibgrenze (und mit Schreibzugriff) gestartet wurde, bricht der Starter ab,
# statt ihn stillschweigend weiterzubenutzen (Befund 14.10.: Grenze war unbemerkt aus).
#
# Überschreibbar: MCP_WRITE_ROOTS, LAB_MEMORY (Default 1), LAB_BIND, LAB_KEEP_SERVE,
# LAB_SERVE_PORT (Default = ROLE_PORT), ROLE_UPSTREAM.
# Mode B: Lab, berührt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$HERE/.." && pwd)"

export MCP_WRITE_ROOTS="${MCP_WRITE_ROOTS:-docs/projekt_management,docs/research}"
export LAB_MEMORY="${LAB_MEMORY:-1}"
MCP_PORT="${MCP_PORT:-8787}"
ROLE_PORT="${ROLE_PORT:-8092}"
export ROLE_PORT
export LAB_SERVE_PORT="${LAB_SERVE_PORT:-$ROLE_PORT}"   # wirkt nur mit LAB_BIND=serve

# --- Fail-loud: vorhandenen MCP-Server prüfen ---
MCP_PID="$(lsof -ti ":${MCP_PORT}" -sTCP:LISTEN 2>/dev/null | head -n1)"
if [ -n "$MCP_PID" ]; then
  ENV_DUMP="$(ps eww -p "$MCP_PID" 2>/dev/null | tr ' ' '\n')"
  RUN_ROOTS="$(printf '%s\n' "$ENV_DUMP" | grep '^MCP_WRITE_ROOTS=' | head -n1 | cut -d= -f2-)"
  RUN_RO="$(printf '%s\n' "$ENV_DUMP" | grep '^MCP_READONLY=' | head -n1 | cut -d= -f2-)"
  if [ "$RUN_ROOTS" != "$MCP_WRITE_ROOTS" ] || [ "$RUN_RO" != "0" ]; then
    echo "ABBRUCH: Auf Port ${MCP_PORT} läuft bereits ein MCP-Server (PID ${MCP_PID})"
    echo "         mit MCP_WRITE_ROOTS='${RUN_ROOTS:-<nicht gesetzt>}', MCP_READONLY='${RUN_RO:-?}'."
    echo "         Erwartet: MCP_WRITE_ROOTS='${MCP_WRITE_ROOTS}', MCP_READONLY='0'."
    echo "         Den alten Server beenden (Ctrl+C in seinem Launcher-Fenster oder: kill ${MCP_PID})"
    echo "         und diesen Starter erneut aufrufen."
    exit 1
  fi
  echo "MCP-Server auf ${MCP_PORT} läuft bereits mit passender Schreibgrenze — wird weiterbenutzt."
fi

# --- Rollen-Proxy im Hintergrund (braucht 8091 erst bei der ersten Chat-Anfrage) ---
ROLE_PID=""
if [ -n "$(lsof -ti ":${ROLE_PORT}" -sTCP:LISTEN 2>/dev/null)" ]; then
  echo "Rollen-Proxy läuft bereits auf ${ROLE_PORT} — wird weiterbenutzt."
else
  bash "$PROJECT_ROOT/role-split/role.command" &
  ROLE_PID=$!
fi

cleanup() {
  if [ -n "$ROLE_PID" ]; then
    echo "Stoppe Rollen-Proxy (Port ${ROLE_PORT}) ..."
    pkill -P "$ROLE_PID" 2>/dev/null
    kill "$ROLE_PID" 2>/dev/null
  fi
}
trap cleanup EXIT

echo
echo ">> role-split: Browser http://127.0.0.1:${ROLE_PORT}  (Schreibgrenze: ${MCP_WRITE_ROOTS})"
[ "${LAB_BIND:-}" = "serve" ] && echo ">> remote: Tailscale Serve -> Port ${LAB_SERVE_PORT} (Remote-URL steht gleich im Lab-Banner)"
echo

# --- Lab im Vordergrund (blockiert bis Ctrl+C) ---
bash "$HERE/launch_lab.command" write
