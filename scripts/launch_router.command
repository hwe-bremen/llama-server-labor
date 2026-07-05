#!/bin/bash
#
# Router-Launcher (macOS, doppelklickbar)
# ----------------------------------------
# Startet llama-server im ROUTER-MODUS (ohne festes Modell). Der Router
# entdeckt alle im Cache liegenden Modelle automatisch und macht sie in der
# Web-UI per Dropdown auswaehlbar. Ein Endpoint, ein Chat, alle Modelle.
#
# Netzwerk-Bind (Exposition) ueber Env LAB_BIND:
#   (nicht gesetzt) | local  -> nur localhost (Default, sicher)
#   tailscale               -> nur ans Tailscale-Interface (Tailnet, kein LAN)
#                              IP autom. via 'tailscale ip -4' oder LAB_TS_IP=...
#   all                     -> 0.0.0.0 (ALLE Interfaces, inkl. lokales LAN!)
# Bei Exposition ist die Tailscale-ACL (auf das eine Geraet begrenzt) Pflicht.
#
# Mode B: Lab-Komfortstarter. Rollback = Datei loeschen.
# Beruehrt AskValentinAI / produktive Infrastruktur nicht.

PORT=8080
# 127.0.0.1 statt localhost: die Web-UI-MCP-Anbindung scheitert ueber localhost
# oft an CORS. Konsistent die IP nutzen (fuer open UND curl).
URL="http://127.0.0.1:${PORT}"

# --- Bind-Modus bestimmen (Netzwerk-Exposition bewusst) ---
HOST_ARG=""
BIND_INFO="localhost (nur dieser Mac)"
case "${LAB_BIND:-local}" in
  local) : ;;
  tailscale)
    TS_CLI="$(command -v tailscale || echo /Applications/Tailscale.app/Contents/MacOS/Tailscale)"
    TS_IP="${LAB_TS_IP:-$("$TS_CLI" ip -4 2>/dev/null | head -1)}"
    if [ -z "$TS_IP" ]; then
      echo "FEHLER: keine Tailscale-IP gefunden. Ist Tailscale aktiv (tailscale up)?"
      echo "  Alternativ IP manuell: LAB_TS_IP=100.x.x.x LAB_BIND=tailscale bash scripts/launch_lab.command"
      exit 1
    fi
    HOST_ARG="--host ${TS_IP}"
    URL="http://${TS_IP}:${PORT}"
    BIND_INFO="Tailscale ${TS_IP} (nur Tailnet, kein LAN)"
    ;;
  all)
    HOST_ARG="--host 0.0.0.0"
    BIND_INFO="0.0.0.0 (ALLE Interfaces, inkl. lokales LAN!)"
    ;;
  *)
    echo "Unbekannter LAB_BIND '${LAB_BIND}' (erlaubt: local|tailscale|all) — nutze local."
    ;;
esac

echo "=================================================="
echo " llama-server ROUTER"
echo " Port: ${PORT}"
echo " Bind: ${BIND_INFO}"
echo "=================================================="

# --- Laeuft schon ein Server auf der ZIEL-Adresse? Dann nur Browser oeffnen. ---
# Auf die konkrete URL pruefen, nicht nur den Port: sonst wird beim Wechsel des
# Bind-Modus (localhost <-> Tailscale) faelschlich nur der Browser geoeffnet,
# obwohl auf der neuen Adresse gar nichts lauscht.
if curl -s -o /dev/null "${URL}/v1/models" 2>/dev/null; then
  echo "Router antwortet bereits auf ${URL} — oeffne nur den Browser."
  open "${URL}"
  echo "Fenster kann geschlossen werden."
  exit 0
fi
# Port belegt, aber Ziel-URL antwortet NICHT -> Instanz mit anderer Bind-Adresse.
if lsof -i ":${PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "WARNUNG: Auf Port ${PORT} laeuft bereits ein Server, aber NICHT auf ${URL}."
  echo "  Wahrscheinlich eine Instanz mit anderem Bind (z.B. localhost statt Tailscale)."
  echo "  Zuerst beenden:  pkill -f llama-server"
  echo "  Dann diesen Launcher erneut starten."
  exit 1
fi

# --- Warnung, falls noch Einzelserver auf 8081-8083 laufen ---
STRAY=$(lsof -i :8081 -i :8082 -i :8083 2>/dev/null | grep -c LISTEN)
if [ "${STRAY}" -gt 0 ]; then
  echo "HINWEIS: Es laufen noch Einzelserver auf 8081/8082/8083."
  echo "Fuer sauberen Router-Betrieb diese vorher beenden (Ctrl+C in deren Fenstern)."
  echo
fi

# --- Router starten mit Preset (faire Sampling-Parameter pro Modell). ---
# KEIN -hf / -m -> Router-Modus. jinja/ctx/ngl kommen aus der [*]-Section
# der INI, deshalb hier NICHT nochmal setzen (sonst doppelt).
# --ui-mcp-proxy: CORS-Proxy, damit die Web-UI lokale MCP-Server erreichen darf
#   (auch remote: der Proxy loest die MCP-URL serverseitig auf 127.0.0.1 auf).
PRESET="/Users/hans-wernereberhardt/PycharmProjects/llama-server/config/models.ini"
echo "Starte Router mit Preset: ${PRESET}"
llama-server --port "${PORT}" ${HOST_ARG} --models-preset "${PRESET}" --ui-mcp-proxy &
SERVER_PID=$!

# --- Router beim Schliessen des Fensters / Ctrl+C mit beenden ---
trap 'echo; echo "Stoppe Router ..."; kill ${SERVER_PID} 2>/dev/null' EXIT

# --- Warten bis der Router antwortet, dann Browser oeffnen ---
echo "Warte auf den Router ..."
READY=0
for i in $(seq 1 120); do
  if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
    echo "Router-Prozess wurde beendet. Abbruch."
    exit 1
  fi
  if curl -s "${URL}/v1/models" >/dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 1
done

if [ "${READY}" -eq 1 ]; then
  echo "Router bereit — entdeckte Modelle:"
  curl -s "${URL}/v1/models" \
    | tr ',' '\n' | grep '"id"' | sed 's/.*"id":"\([^"]*\)".*/  - \1/'
  echo
  echo "Oeffne ${URL}"
  open "${URL}"
else
  echo "Router hat nach Wartezeit nicht geantwortet. Bitte Ausgabe pruefen."
fi

echo
echo "Router laeuft auf Port ${PORT} (${BIND_INFO}). Fenster offen lassen."
echo "Modellwahl per Dropdown in der Web-UI. Zum Beenden: Ctrl+C."

wait ${SERVER_PID}
