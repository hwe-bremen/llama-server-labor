#!/bin/bash
#
# Lab-Orchestrator (macOS, doppelklickbar)
# ----------------------------------------
# Startet MCP-Server + llama-server-Router mit einem Aufruf. Ctrl+C stoppt alles.
#
# Zugriffs-Modus (read-only vs. write), 1. Argument:
#   bash scripts/launch_lab.command           -> read-only (sicher, Default)
#   bash scripts/launch_lab.command write     -> write-faehig
#   Doppelklick launch_lab.command / launch_lab_write.command
#
# Netzwerk-Modus ueber Env LAB_BIND:
#   (nicht gesetzt) -> nur lokal (127.0.0.1)
#   serve           -> Router lokal + Tailscale Serve davor (HTTPS ueber .ts.net,
#                      fuer iPad/iPhone/Mac-mini im Tailnet). Empfohlener Remote-Weg.
#   tailscale|all   -> direkter Bind (siehe launch_router.command; auf macOS ist
#                      Serve zuverlaessiger als der Direct-Bind)
#
# Serve-Persistenz ueber Env LAB_KEEP_SERVE (nur im serve-Modus relevant):
#   (nicht gesetzt/0) -> Serve wird beim Beenden (Ctrl+C) zurueckgesetzt (Default, sicher)
#   1                 -> Serve bleibt aktiv, auch nach Beenden des Launchers
#                        (iPad-Zugriff ohne laufendes Terminal). Manuell aus:
#                        'tailscale serve reset'. Nach Reboot Router wieder starten.
#
# Gedaechtnis-Proxy (Nachbar-Repo local-memory) ueber Env LAB_MEMORY:
#   (nicht gesetzt/0) -> aus; Chat direkt am Router (8080), ohne Gedaechtnis
#   1                 -> startet zusaetzlich 'lm.command proxy' (Port 8091, braucht Ollama/bge-m3),
#                        sobald der Router antwortet. Im serve-Modus zeigt Tailscale Serve dann
#                        auf 8091 statt 8080 -> Gedaechtnis auch vom iPad. 8080 bleibt lokal
#                        als Kontrollgruppe erreichbar. Nur Chats ueber 8091 landen im Chatlog.
#   LAB_MEMORY_DIR    -> Pfad zum local-memory-Repo (Default ~/PycharmProjects/local-memory)
#
# Beispiele:
#   LAB_BIND=serve bash scripts/launch_lab.command                    # remote, read-only
#   LAB_BIND=serve bash scripts/launch_lab.command write              # remote, schreibfaehig
#   LAB_BIND=serve LAB_KEEP_SERVE=1 bash scripts/launch_lab.command   # remote, Serve bleibt aktiv
#   LAB_MEMORY=1 bash scripts/launch_lab.command                      # lokal + Gedaechtnis auf 8091
#   LAB_MEMORY=1 LAB_BIND=serve bash scripts/launch_lab.command       # Gedaechtnis auch per Tailscale
#
# Mode B: Lab, beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$HERE/.." && pwd)"
MCP_PORT="${MCP_PORT:-8787}"
ROUTER_PORT="${ROUTER_PORT:-8080}"
MEMORY_ON="${LAB_MEMORY:-0}"
MEMORY_DIR="${LAB_MEMORY_DIR:-$HOME/PycharmProjects/local-memory}"
MEMORY_PORT="${LM_PROXY_PORT:-8091}"
TS_CLI="$(command -v tailscale || echo /Applications/Tailscale.app/Contents/MacOS/Tailscale)"

# --- Zugriffs-Modus (1. Argument gewinnt vor Env) ---
case "${1:-}" in
  write|rw|w) export MCP_READONLY=0 ;;
  read|ro|r)  export MCP_READONLY=1 ;;
  "")         export MCP_READONLY="${MCP_READONLY:-1}" ;;
  *) echo "Unbekannter Modus '${1:-}' (erlaubt: read | write) — nutze read-only."
     export MCP_READONLY=1 ;;
esac
[ "${MCP_READONLY}" = "0" ] && MODE_LABEL="WRITE (schreiben + loeschen erlaubt)" || MODE_LABEL="read-only"

# --- Netzwerk-Modus: LAB_BIND=serve -> Router lokal + Serve davor ---
SERVE_MODE=0
KEEP_SERVE="${LAB_KEEP_SERVE:-0}"
if [ "${LAB_BIND:-}" = "serve" ]; then
  SERVE_MODE=1
  export LAB_BIND=local   # llama-server bleibt localhost; Serve macht die Exposition
fi

# --- Gedaechtnis-Proxy: Voraussetzungen pruefen, Serve-Ziel festlegen ---
SERVE_PORT="$ROUTER_PORT"
if [ "$MEMORY_ON" = "1" ]; then
  if [ ! -x "$MEMORY_DIR/.venv/bin/python" ] || [ ! -f "$MEMORY_DIR/lm.command" ]; then
    echo "WARNUNG: LAB_MEMORY=1, aber ${MEMORY_DIR} hat kein venv/lm.command — Gedaechtnis-Proxy wird nicht gestartet."
    MEMORY_ON=0
  else
    SERVE_PORT="$MEMORY_PORT"   # im serve-Modus zeigt Tailscale auf den Proxy, nicht auf den Router
  fi
fi

SUFFIX=""
[ "$SERVE_MODE" = "1" ] && SUFFIX=" + Tailscale Serve"
[ "$SERVE_MODE" = "1" ] && [ "$KEEP_SERVE" = "1" ] && SUFFIX="${SUFFIX} (bleibt aktiv)"
[ "$MEMORY_ON" = "1" ] && SUFFIX="${SUFFIX} + Gedaechtnis-Proxy :${MEMORY_PORT}"
echo "Lab-Modus: ${MODE_LABEL}${SUFFIX}"

# --- Hygiene: Write-Warnung + Rollback-Check ---
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

# --- 1b) Tailscale Serve (nur im serve-Modus) ---
# Idempotent: setzt das Mapping SERVE_PORT -> .ts.net bei jedem Start neu, egal ob es
# einen Reboot ueberlebt hat oder nicht. Zeigt die Remote-URL deutlich an.
if [ "$SERVE_MODE" = "1" ]; then
  echo "Starte Tailscale Serve fuer Port ${SERVE_PORT} (HTTPS ueber .ts.net) ..."
  if "$TS_CLI" serve --bg "${SERVE_PORT}" 2>/tmp/lab_serve_err; then
    "$TS_CLI" serve status
    SERVE_URL="$("$TS_CLI" serve status 2>/dev/null | grep -oE 'https://[a-zA-Z0-9.-]+\.ts\.net[^ ]*' | head -n1)"
    if [ -n "$SERVE_URL" ]; then
      echo
      echo "  >> Remote-URL (iPad/iPhone im Tailnet): ${SERVE_URL}"
      [ "$MEMORY_ON" = "1" ] && echo "     (fuehrt ueber den Gedaechtnis-Proxy; antwortet erst, wenn Router + Proxy laufen)"
    else
      echo "  Hinweis: keine .ts.net-URL im Serve-Status gefunden — 'tailscale serve status' pruefen."
    fi
    if [ "$KEEP_SERVE" = "1" ]; then
      echo "  Serve bleibt nach Beenden aktiv (LAB_KEEP_SERVE=1) — iPad-Zugriff auch ohne Launcher."
      echo "  Manuell abschalten: ${TS_CLI} serve reset"
    fi
  else
    echo "WARNUNG: 'tailscale serve' fehlgeschlagen:"
    sed 's/^/    /' /tmp/lab_serve_err
    echo "    Haeufig: HTTPS/MagicDNS im Tailscale-Admin (login.tailscale.com -> DNS) aktivieren."
  fi
fi

# --- 1c) Gedaechtnis-Proxy im Hintergrund: wartet, bis der Router antwortet ---
MEM_PID=""
if [ "$MEMORY_ON" = "1" ]; then
  if lsof -i ":${MEMORY_PORT}" >/dev/null 2>&1; then
    echo "Gedaechtnis-Proxy laeuft bereits auf Port ${MEMORY_PORT} — nutze ihn."
  else
    (
      for _ in $(seq 1 90); do   # bis 3 Minuten (Modell-Laden)
        curl -sf "http://127.0.0.1:${ROUTER_PORT}/v1/models" >/dev/null 2>&1 && break
        sleep 2
      done
      if curl -sf "http://127.0.0.1:${ROUTER_PORT}/v1/models" >/dev/null 2>&1; then
        echo; echo "Starte Gedaechtnis-Proxy (local-memory) auf Port ${MEMORY_PORT} ..."
        LM_PROXY_PORT="$MEMORY_PORT" bash "$MEMORY_DIR/lm.command" proxy
      else
        echo "WARNUNG: Router antwortet nicht auf ${ROUTER_PORT} — Gedaechtnis-Proxy nicht gestartet."
      fi
    ) &
    MEM_PID=$!
    echo "Gedaechtnis-Proxy wartet auf den Router, dann: http://127.0.0.1:${MEMORY_PORT}  (8080 = ohne Gedaechtnis)"
  fi
fi

# --- Aufraeumen beim Beenden (MCP-Server + Gedaechtnis-Proxy stoppen; Serve nur ohne KEEP_SERVE) ---
cleanup() {
  if [ "$SERVE_MODE" = "1" ] && [ "$KEEP_SERVE" != "1" ]; then
    echo
    echo "Setze Tailscale Serve zurueck (serve reset) ..."
    "$TS_CLI" serve reset 2>/dev/null
  elif [ "$SERVE_MODE" = "1" ] && [ "$KEEP_SERVE" = "1" ]; then
    echo
    echo "Serve bleibt aktiv (LAB_KEEP_SERVE=1). Abschalten mit: ${TS_CLI} serve reset"
  fi
  if [ -n "${MEM_PID}" ]; then
    echo "Stoppe Gedaechtnis-Proxy (Port ${MEMORY_PORT}) ..."
    pkill -P "${MEM_PID}" 2>/dev/null; kill "${MEM_PID}" 2>/dev/null
    pkill -f "lm.proxy" 2>/dev/null
  fi
  if [ -n "${MCP_PID}" ]; then
    echo "Stoppe MCP-Server (Port ${MCP_PORT}) ..."
    kill "${MCP_PID}" 2>/dev/null
  fi
}
trap cleanup EXIT

# --- 2) Router im Vordergrund (oeffnet Browser lokal, blockiert bis Ctrl+C) ---
bash "$HERE/launch_router.command"
