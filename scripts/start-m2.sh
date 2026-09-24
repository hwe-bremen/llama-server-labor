#!/usr/bin/env bash
# Router-Start fuer den M2 Mac mini: max. 1 Modell gleichzeitig im RAM.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
exec llama-server --port 8080 --models-preset config/models-m2.ini --models-max 1
