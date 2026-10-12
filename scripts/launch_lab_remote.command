#!/bin/bash
# "Buero-Tag"-Launcher: Router + MCP + Gedaechtnis-Proxy, per Tailscale Serve erreichbar.
# Duenner Doppelklick-Wrapper um launch_lab.command mit festen Schaltern:
#   LAB_MEMORY=1      Gedaechtnis-Proxy (local-memory) auf 8091 mitstarten
#   LAB_BIND=serve    Tailscale Serve -> https://<geraet>.ts.net zeigt auf 8091
#   LAB_KEEP_SERVE=1  Serve bleibt auch nach Ctrl+C aktiv (Router muss trotzdem laufen)
# Lokal bleibt 8080 (ohne Gedaechtnis) als Kontrollgruppe erreichbar.
# Fenster offen lassen; das MacBook darf nicht in den Ruhezustand gehen (caffeinate laeuft mit).
# Mode B: Lab. Beruehrt AskValentinAI nicht.
HERE="$(cd "$(dirname "$0")" && pwd)"
exec caffeinate -s env LAB_MEMORY=1 LAB_BIND=serve LAB_KEEP_SERVE=1 bash "$HERE/launch_lab.command" "${1:-read}"
