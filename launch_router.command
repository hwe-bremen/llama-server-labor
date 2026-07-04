#!/bin/bash
#
# Router-Launcher (macOS, doppelklickbar)
# ----------------------------------------
# Startet llama-server im ROUTER-MODUS (ohne festes Modell). Der Router
# entdeckt alle im Cache liegenden Modelle automatisch und macht sie in der
# Web-UI per Dropdown auswaehlbar. Ein Endpoint, ein Chat, alle Modelle.
#
# Mode B: Lab-Komfortstarter. Rollback = Datei loeschen.
# Beruehrt AskValentinAI / produktive Infrastruktur nicht.

PORT=8080
URL="http://localhost:${PORT}"

echo "=================================================="
echo " llama-server ROUTER"
echo " Port: ${PORT}"
echo "=================================================="

# --- Laeuft schon etwas auf dem Port? Dann nur Browser oeffnen. ---
if lsof -i ":${PORT}" >/dev/null 2>&1; then
  echo "Es laeuft bereits ein Server auf Port ${PORT} — oeffne nur den Browser."
  open "${URL}"
  echo "Fenster kann geschlossen werden."
  exit 0
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
# --ui-mcp-proxy: CORS-Proxy, damit die Web-UI lokale MCP-Server erreichen
#   darf. Nur fuer lokales Lab (127.0.0.1) gedacht.
PRESET="/Users/hans-wernereberhardt/PycharmProjects/llama-server/models.ini"
echo "Starte Router mit Preset: ${PRESET}"
llama-server --port "${PORT}" --models-preset "${PRESET}" --ui-mcp-proxy &
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
  # Modell-IDs kompakt auflisten (ohne jq, reines grep/sed)
  curl -s "${URL}/v1/models" \
    | tr ',' '\n' | grep '"id"' | sed 's/.*"id":"\([^"]*\)".*/  - \1/'
  echo
  echo "Oeffne ${URL}"
  open "${URL}"
else
  echo "Router hat nach Wartezeit nicht geantwortet. Bitte Ausgabe pruefen."
fi

echo
echo "Router laeuft auf Port ${PORT}. Fenster offen lassen."
echo "Modellwahl per Dropdown in der Web-UI. Zum Beenden: Ctrl+C."

# --- Im Vordergrund bleiben, Router-Ausgabe anzeigen ---
wait ${SERVER_PID}
