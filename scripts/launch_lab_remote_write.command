#!/bin/bash
# Buero-Tag im WRITE-Modus: wie launch_lab_remote.command, aber das Frontend-Modell
# darf Dateien im Repo-Scope schreiben und loeschen (MCP_READONLY=0).
# Achtung: gilt dann auch fuer Chats, die ueber Tailscale Serve hereinkommen.
# Vorher committen (Rollback-Punkt) — der Launcher warnt bei unsauberem Git-Baum.
HERE="$(cd "$(dirname "$0")" && pwd)"
exec bash "$HERE/launch_lab_remote.command" write
