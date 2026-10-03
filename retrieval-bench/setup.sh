#!/usr/bin/env bash
# Einmalig: eigenes venv fuer retrieval-bench (getrennt vom Projekt-venv).
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
echo "retrieval-bench venv bereit: source retrieval-bench/.venv/bin/activate"
