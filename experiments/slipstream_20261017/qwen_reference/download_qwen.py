#!/usr/bin/env python3
"""Authorized pinned Qwen download only, directly to mounted external SSD.
Re-run to resume. Never converts, loads models, or stops existing services.
"""
import fcntl
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import download_glm as helpers  # reuse reviewed mount/dir_fd and hash helpers only
from probe_remote_metadata import HTTPSRedirect

REPO = 'unsloth/Qwen3.6-35B-A3B-MTP-GGUF'
REV = '5bc3e238d916f48a861bac2f8a1990a0e9b7e98d'
NAME = 'Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf'
SIZE = 22853663008
SHA = '55983c5a75a1ab969824077b3bb3de4146e82a9234072b48ad4e8f92ad3fe9f1'
MOUNT = Path('/Volumes/Extern M4 Speicher')
DEST = MOUNT / 'LLM-Experimente/slipstream/qwen35b-reference'
LOGS = HERE / 'logs'


def message(text):
    print(text, flush=True)
    with (LOGS / 'download.log').open('a') as out:
        out.write(datetime.now(timezone.utc).isoformat() + ' ' + text + '\n')


def published_pointer():
    url = f'https://huggingface.co/{REPO}/raw/{REV}/{NAME}'
    opener = urllib.request.build_opener(HTTPSRedirect())
    request = urllib.request.Request(url, headers={'Accept-Encoding': 'identity'})
    with opener.open(request, timeout=30) as response:
        raw = response.read(513)
        if response.status != 200 or len(raw) > 512:
            raise RuntimeError('Unerwartete LFS-Zeigerantwort')
    if not re.search(rb'^oid sha256:' + SHA.encode() + rb'\s*$', raw, re.M) or not re.search(
            rb'^size ' + str(SIZE).encode() + rb'\s*$', raw, re.M):
        raise RuntimeError('Veröffentlichte Modellgröße/Prüfsumme weicht ab')
    return f'https://huggingface.co/{REPO}/resolve/{REV}/{NAME}?download=true'


def main():
    # Stop before any external mkdir/network if the volume is missing.
    helpers.check_mount(MOUNT, DEST)
    metadata = json.loads((HERE / 'metadata/results.json').read_text())
    if not (metadata.get('metadata_prerequisites_pass') is True and
            metadata.get('repository') == REPO and metadata.get('revision') == REV and
            metadata.get('filename') == NAME and metadata.get('remote_size') == SIZE and
            metadata.get('published_sha256') == SHA):
        raise RuntimeError('Positive Metadatenprüfung des exakten Artefakts fehlt')
    LOGS.mkdir(exist_ok=True)
    helpers.message = message
    with (LOGS / 'download.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        message(f'Download freigegeben: 22,85 GB; Ziel {DEST}; Revision {REV}')
        final = DEST / NAME
        partial = DEST / (NAME + '.download')
        for path in (final, partial):
            if path.is_symlink() or (path.exists() and not path.is_file()):
                raise RuntimeError(f'Kein regulärer Zielpfad: {path}')
        have = final.stat().st_size if final.exists() else partial.stat().st_size if partial.exists() else 0
        if have > SIZE:
            raise RuntimeError('Vorhandene Datei größer als erwartetes Modell; bleibt erhalten')
        if shutil.disk_usage(MOUNT).free < SIZE - have + 10 * 2**30:
            raise RuntimeError('Zu wenig externer Platz einschließlich 10 GiB Reserve')
        url = published_pointer()
        helpers.external_directory(MOUNT, DEST)
        final, partial = Path(NAME), Path(NAME + '.download')
        item = {'size_bytes': SIZE, 'sha256': SHA}
        if final.exists():
            helpers.validate_file(final, item)
        else:
            if not partial.exists() or partial.stat().st_size < SIZE:
                message('Lade Qwen; .download-Datei bleibt extern und ist fortsetzbar.')
                subprocess.run([
                    '/usr/bin/curl', '--fail', '--location', '--progress-bar',
                    '--proto', '=https', '--proto-redir', '=https', '--connect-timeout', '20',
                    '--continue-at', '-', '--header', 'Accept-Encoding: identity',
                    '--max-filesize', str(SIZE), '--output', str(partial), url,
                ], check=True)
            helpers.check_mount(MOUNT, DEST)
            helpers.validate_file(partial, item)
            # Hard-link then unlink: no full copy, atomic refusal if final appeared.
            import os
            os.link(partial, final, follow_symlinks=False)
            partial.unlink()
        helpers.check_mount(MOUNT, DEST)
        manifest = {'completed_at': datetime.now(timezone.utc).isoformat(),
                    'repository': REPO, 'revision': REV, 'filename': NAME,
                    'directory': str(DEST), 'size_bytes': SIZE, 'sha256': SHA,
                    'sha256_verified': True, 'converted': False, 'model_started': False}
        (LOGS / 'download-complete.json').write_text(json.dumps(manifest, indent=2) + '\n')
        message('FERTIG: Qwen extern vollständig und SHA-256-verifiziert. Keine Konvertierung, kein Modellstart.')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Unterbrochen. Gleicher Befehl setzt externe .download-Datei fort.', file=sys.stderr)
        raise SystemExit(130)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('ABBRUCH:', exc, file=sys.stderr)
        raise SystemExit(1)
