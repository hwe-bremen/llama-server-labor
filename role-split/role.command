#!/bin/bash
# role-split · Rollen-Proxy starten (Doppelklick im Finder oder: bash role.command [check|test])
#
# Kette:  Web-UI  ->  :8092 role-split  ->  ROLE_UPSTREAM
#   ROLE_UPSTREAM=http://127.0.0.1:8091  Gedächtnis-Proxy local-memory (Standard)
#   ROLE_UPSTREAM=http://127.0.0.1:8080  direkt auf den Router, ohne Gedächtnis
#
# Bindet nur an 127.0.0.1. Für iPad/iPhone NICHT einfach ROLE_HOST=0.0.0.0 setzen,
# sondern bewusst über Tailscale Serve gehen (siehe README).

cd "$(dirname "$0")" || exit 1

export ROLE_PORT="${ROLE_PORT:-8092}"
export ROLE_HOST="${ROLE_HOST:-127.0.0.1}"
export ROLE_UPSTREAM="${ROLE_UPSTREAM:-http://127.0.0.1:8091}"

case "${1:-serve}" in
  check)
    python3 role_proxy.py --check
    ;;
  test)
    python3 -m unittest -v test_role_proxy
    ;;
  serve)
    echo "Web-UI danach öffnen: http://${ROLE_HOST}:${ROLE_PORT}"
    python3 role_proxy.py
    ;;
  *)
    echo "Aufruf: bash role.command [serve|check|test]"
    exit 2
    ;;
esac
