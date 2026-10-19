#!/usr/bin/env python3
"""Metadata only. Never starts an engine or converter or downloads a full model."""
import fcntl
import json
from pathlib import Path
import re
import sys
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from inspect_gguf_metadata import inspect, summarize
from probe_remote_metadata import HTTPSRedirect, validate_range_headers

REVISION = '5bc3e238d916f48a861bac2f8a1990a0e9b7e98d'
REPO = 'unsloth/Qwen3.6-35B-A3B-MTP-GGUF'
FILE = 'Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf'
SIZE = 22853663008
SHA = '55983c5a75a1ab969824077b3bb3de4146e82a9234072b48ad4e8f92ad3fe9f1'
LIMIT = 16 * 1024 * 1024
CHUNK = 256 * 1024


def assess(report):
    summary = summarize([report])
    experts = [t for t in report['tensors'] if t['streamed_expert']]
    unsupported = [t for t in experts if not t['converter_type_accepted']]
    unknown = [t for t in report['tensors'] if '_exps.weight' in t['name'] and not t['streamed_expert']]
    layers = {}
    for t in experts:
        layers.setdefault(t['layer'], set()).add(t['group'])
    triplets = bool(layers) and all(v == {'gate', 'up', 'down'} for v in layers.values())
    geometry = all(len(t['shape']) == 3 and t['shape'][2] == 256 and
                   (t['type_id'] not in (12, 13, 14) or t['shape'][0] % 256 == 0)
                   for t in experts)
    single = report['metadata'].get('split.count', 1) in (0, 1)
    arch = report['metadata'].get('general.architecture')
    return {'summary': summary, 'unsupported_experts': unsupported,
            'unrecognized_expert_weights': unknown,
            'complete_gate_up_down_triplets': triplets, 'expert_geometry_accepted': geometry,
            'single_file': single, 'architecture': arch,
            'reference_geometry_matches': len(layers) == 41 and len(experts) == 123 and geometry,
            'metadata_prerequisites_pass': bool(experts) and not unsupported and not unknown and
                 triplets and geometry and single and arch == 'qwen35moe' and
                 len(layers) == 41 and len(experts) == 123,
            'inference_tested': False, 'full_model_sha256_verified': False}


def main():
    logs = HERE / 'metadata'
    logs.mkdir(exist_ok=True)
    ledger_file = logs / 'budget.json'
    with (logs / 'probe.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = json.loads(ledger_file.read_text()) if ledger_file.exists() else {
            'reserved_bytes': 0, 'read_bytes': 0, 'verified_206_requests': 0}
        opener = urllib.request.build_opener(HTTPSRedirect())

        def reserve(n):
            # 70 MB lifetime body budget; 30 MB reserved for text research/HTTP overhead.
            if ledger['reserved_bytes'] + n > 70_000_000:
                raise RuntimeError('Budget erschöpft; kein weiterer Abruf')
            ledger['reserved_bytes'] += n
            ledger_file.write_text(json.dumps(ledger, indent=2) + '\n')

        print('Prüfe gepinnten LFS-Zeiger (max. 512 Bytes). Kein voller Modelldownload.', flush=True)
        reserve(513)
        url = f'https://huggingface.co/{REPO}/raw/{REVISION}/{FILE}'
        with opener.open(urllib.request.Request(url, headers={'Accept-Encoding': 'identity'}), timeout=30) as response:
            raw = response.read(513)
            if response.status != 200 or len(raw) > 512:
                raise RuntimeError('Unerwarteter LFS-Zeiger')
        ledger['read_bytes'] += len(raw)
        ledger_file.write_text(json.dumps(ledger, indent=2) + '\n')
        if not re.search(rb'^oid sha256:' + SHA.encode() + rb'\s*$', raw, re.M) or not re.search(
                rb'^size ' + str(SIZE).encode() + rb'\s*$', raw, re.M):
            raise RuntimeError('LFS-Größe/Hash weichen ab')
        (logs / 'lfs-pointer.txt').write_bytes(raw)
        prefix = logs / 'qwen.header'
        url = f'https://huggingface.co/{REPO}/resolve/{REVISION}/{FILE}?download=true'
        while True:
            if prefix.exists():
                try:
                    report = inspect(prefix)
                    break
                except ValueError as exc:
                    if str(exc) != 'Unvollständiger GGUF-Header':
                        raise
            start = prefix.stat().st_size if prefix.exists() else 0
            end = 23 if start == 0 else min(start + CHUNK - 1, LIMIT - 1)
            if end < start:
                raise RuntimeError('Tensorverzeichnis nicht vollständig innerhalb 16 MiB')
            reserve(end - start + 2)  # includes one overlength-detection byte
            print(f'Range {start:,}–{end:,} / Headerlimit {LIMIT:,} Bytes', flush=True)
            request = urllib.request.Request(url, headers={
                'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'})
            with opener.open(request, timeout=30) as response:
                validate_range_headers(response.status, response.headers, start, end, SIZE)
                data = response.read(end - start + 2)
                if len(data) != end - start + 1:
                    raise RuntimeError('Range-Länge falsch')
            with prefix.open('ab') as out:
                out.write(data)
            ledger['read_bytes'] += len(data)
            ledger['verified_206_requests'] += 1
            ledger_file.write_text(json.dumps(ledger, indent=2) + '\n')
        result = {'repository': REPO, 'revision': REVISION, 'filename': FILE,
                  'published_sha256': SHA, 'remote_size': SIZE,
                  'header_sha256_authentication': False,
                  'prefetched_beyond_header': prefix.stat().st_size - report['header_end'],
                  'report': report, **assess(report)}
        (logs / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps({k: v for k, v in result.items() if k not in ('report',)}, indent=2), flush=True)
        print('Nur Metadaten geprüft. Keine Konvertierung und keine Inferenzbestätigung.', flush=True)
        return 0 if result['metadata_prerequisites_pass'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print('UNBESTÄTIGT:', exc, flush=True)
        raise SystemExit(1)
