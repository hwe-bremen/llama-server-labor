#!/bin/bash
# "Buero-Tag" mit Rollen: wie launch_lab_remote.command, aber mit role-split.
# Router + MCP (Schreibgrenze docs/projekt_management,docs/research) + Gedaechtnis-Proxy
# + Rollen-Proxy 8092; Tailscale Serve zeigt auf 8092 -> @review/@research auch vom iPad/Mini.
#   LAB_BIND=serve    Tailscale Serve -> https://<geraet>.ts.net zeigt auf 8092
#   LAB_KEEP_SERVE=1  Serve bleibt auch nach Ctrl+C aktiv (Proxys muessen trotzdem laufen)
# Immer write-faehig, aber nur innerhalb der Schreibgrenze (fail-loud bei falschem MCP-Server).
# Fenster offen lassen; das MacBook darf nicht in den Ruhezustand gehen (caffeinate laeuft mit).
# Mode B: Lab. Beruehrt AskValentinAI nicht.
HERE="$(cd "$(dirname "$0")" && pwd)"
exec caffeinate -s env LAB_BIND=serve LAB_KEEP_SERVE=1 bash "$HERE/launch_lab_roles.command"
