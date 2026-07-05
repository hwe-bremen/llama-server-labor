#!/usr/bin/env bash
# Einmaliges Setup: venv + Abhaengigkeiten fuer den Lab-MCP-Server.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo
echo "Fertig. venv: $HERE/.venv"
echo "Python fuer die Claude-Desktop-Config: $HERE/.venv/bin/python"
