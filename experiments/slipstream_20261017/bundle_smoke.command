#!/bin/bash
# Local-only bundle provision and MODEL-LESS smoke test; run in macOS Terminal.
# No GUI launch, model download, model start, PGRN conversion or security changes.
set -euo pipefail
cd -- "$(dirname -- "$0")"
mkdir -p logs
exec > >(tee -a logs/bundle-smoke-terminal.log) 2>&1
echo "Slipstream bundle / model-less smoke: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"

# Refuse to replace any current port owner. This check does not contact HTTP.
python3 -B - <<'PY'
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('slipstream_experiment', Path('experiment.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for port in (module.CFG['engine_port'], module.CFG['role_port']):
    if module.listeners(port):
        raise SystemExit(f'ABBRUCH: Port {port} belegt; kein Prozess wird gestoppt.')
print('Experimentports frei; bestehende Labor-Listener:')
for port in module.LAB_PORTS:
    print(port, module.listeners(port))
PY

mkdir -p runtime
archive='runtime/Slipstream_0.3.4_aarch64.zip'
if [ ! -f "$archive" ]; then
  # No automatic retries. A failed partial remains identifiable, never executable.
  curl --fail --location --proto '=https' --proto-redir '=https' \
    --connect-timeout 15 --max-time 180 \
    --output "${archive}.download" \
    'https://github.com/Schero94/slipstream/releases/download/v0.3.4/Slipstream_0.3.4_aarch64.zip'
  mv -- "${archive}.download" "$archive"
fi
python3 -B - <<'PY'
import hashlib
from pathlib import Path
archive = Path('runtime/Slipstream_0.3.4_aarch64.zip')
# Compared to BOTH release-body checksum and GitHub release asset digest.
expected = '8f2106b66ac1f809f0d1d82d1f1b17ad404974f158ce3d5e361ce0eb11fb9ce7'
if archive.stat().st_size != 65780310:
    raise SystemExit('ABBRUCH: ZIP-Größe weicht vom veröffentlichten Release ab.')
actual = hashlib.sha256(archive.read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit('ABBRUCH: SHA-256 weicht von veröffentlichter Prüfsumme ab.')
print('ZIP-Größe und veröffentlichte SHA-256 bestätigt:', actual)
PY

if [ ! -e runtime/Slipstream.app ]; then
  /usr/bin/ditto -x -k "$archive" runtime
fi
# Ad-hoc signature verifies bundle integrity; not a Developer ID identity proof.
/usr/bin/codesign --verify --deep --strict runtime/Slipstream.app
unset SLIPSTREAM_BUNDLE
python3 -B experiment.py capabilities
python3 -B experiment.py smoke
