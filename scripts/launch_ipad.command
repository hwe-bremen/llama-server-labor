#!/bin/bash
#
# iPad-Launcher (macOS, doppelklickbar)
# -------------------------------------
# Ein Klick fuer den zuverlaessigen iPad-Weg: raeumt alte Instanzen weg,
# setzt Tailscale Serve zurueck und startet den Router im Direct-Bind an die
# Tailscale-IP. Danach ist die Chat-UI am iPad ueber http://<tailscale-ip>:8080
# erreichbar (read-only). Fenster offen lassen; Ctrl+C beendet alles.
#
# Fuer Schreibzugriff die Variante launch_ipad_write.command nutzen.
# Mode B: Lab. Beruehrt AskValentinAI nicht.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS_CLI="$(command -v tailscale || echo /Applications/Tailscale.app/Contents/MacOS/Tailscale)"

MODE="${1:-read}"   # read (Default) | write

echo "=================================================="
echo " iPad-Start (Direct-Bind an Tailscale-IP)"
echo " Modus: ${MODE}"
echo "=================================================="

# --- 1) Sauberer Ausgangszustand: alte Router weg, Serve zuruecksetzen ---
echo "Raeume alte llama-server-Instanzen ab ..."
pkill -f llama-server 2>/dev/null || true
echo "Setze Tailscale Serve zurueck (falls aktiv) ..."
"$TS_CLI" serve reset 2>/dev/null || true
sleep 1

# --- 2) Tailscale-IP ermitteln und anzeigen (fuer die iPad-URL) ---
TS_IP="$("$TS_CLI" ip -4 2>/dev/null | head -1)"
if [ -n "$TS_IP" ]; then
  echo
  echo "  >> Am iPad oeffnen:  http://${TS_IP}:8080"
  echo "     (im Zweifel Chrome statt Safari; Private Relay am iPad aus)"
  echo
else
  echo "WARNUNG: keine Tailscale-IP gefunden. Ist Tailscale aktiv (tailscale up)?"
fi

# --- 3) Router im Direct-Bind starten (ueber den bestehenden Orchestrator) ---
exec env LAB_BIND=tailscale bash "$HERE/launch_lab.command" "$MODE"
