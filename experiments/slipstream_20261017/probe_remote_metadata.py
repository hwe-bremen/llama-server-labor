#!/usr/bin/env python3
"""Strictly bounded HTTP-206 metadata probe. No engine, conversion or full download.

Run in normal Terminal if network is restricted in the execution sandbox.
70 MB lifetime payload reservation leaves 30 MB of the authorized 100 MB for
source pages, redirects and HTTP overhead. Failed reservations are not refunded.
Each file is capped at 16 MiB. Chunk prefetch may include at most 256 KiB beyond
the exact header end; no such bytes are used for inference or conversion.
"""
import fcntl
import json
from pathlib import Path
import re
import urllib.request
from urllib.error import HTTPError
from urllib.parse import urlparse

from inspect_gguf_metadata import inspect, summarize

HERE = Path(__file__).resolve().parent
PAYLOAD_LIMIT = 70_000_000
FILE_LIMIT = 16 * 1024 * 1024
CHUNK = 256 * 1024


class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != 'https':
            raise RuntimeError('Redirect auf Nicht-HTTPS abgewiesen')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_range(url, start, end, total, ledger, path):
    size = end - start + 1
    if ledger['reserved_payload_bytes'] + size > PAYLOAD_LIMIT:
        raise RuntimeError('Gesamtbudget ausgeschöpft; keine weitere Anfrage')
    ledger['reserved_payload_bytes'] += size
    path.write_text(json.dumps(ledger, indent=2) + '\n')
    request = urllib.request.Request(url, headers={
        'Range': f'bytes={start}-{end}', 'Accept-Encoding': 'identity'})
    opener = urllib.request.build_opener(HTTPSRedirect())
    with opener.open(request, timeout=30) as response:
        # urlopen returns after headers: do not read a 200 response body.
        validate_range_headers(response.status, response.headers, start, end, total)
        data = response.read(size + 1)
        if len(data) != size:
            raise RuntimeError('Range-Antwort hat falsche Nutzdatenlänge')
    ledger['verified_206_requests'] += 1
    ledger['read_payload_bytes'] += len(data)
    path.write_text(json.dumps(ledger, indent=2) + '\n')
    return data


def validate_range_headers(status, headers, start, end, total):
    if status != 206:
        raise RuntimeError(f'HTTP {status} statt 206: kein Dateibody gelesen')
    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', headers.get('Content-Range', ''))
    if not match or tuple(map(int, match.groups())) != (start, end, total):
        raise RuntimeError('Content-Range stimmt nicht mit angefordertem Bereich überein')
    if headers.get('Content-Encoding', 'identity').lower() != 'identity':
        raise RuntimeError('Komprimierte Range-Antwort abgewiesen')
    if headers.get('Content-Length') != str(end - start + 1):
        raise RuntimeError('Content-Length stimmt nicht mit Range überein')


def main():
    directory = HERE / 'logs/remote-metadata'
    directory.mkdir(parents=True, exist_ok=True)
    ledger_path = directory / 'budget.json'
    with (directory / 'probe.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
            'payload_limit': PAYLOAD_LIMIT, 'reserved_payload_bytes': 0,
            'read_payload_bytes': 0, 'verified_206_requests': 0}
        candidates = json.loads((HERE / 'range_candidates.json').read_text())['candidates']
        results = []
        for candidate in candidates:
            reports = []
            failure = None
            for index, item in enumerate(candidate['files']):
                url = f"https://huggingface.co/{candidate['repository']}/resolve/{candidate['revision']}/{item['path']}?download=true"
                prefix = directory / f"{candidate['name']}-{index + 1}.header"
                try:
                    if not prefix.exists():
                        # First request proves range behavior with exactly 24 bytes.
                        data = fetch_range(url, 0, 23, item['size'], ledger, ledger_path)
                        if data[:4] != b'GGUF':
                            raise RuntimeError('Kein GGUF-Header')
                        prefix.write_bytes(data)
                    while True:
                        try:
                            report = inspect(prefix)
                            break
                        except ValueError as exc:
                            if str(exc) != 'Unvollständiger GGUF-Header':
                                raise
                        start = prefix.stat().st_size
                        end = min(start + CHUNK - 1, FILE_LIMIT - 1, item['size'] - 1)
                        if end < start:
                            raise RuntimeError('Header nicht vollständig innerhalb des Dateibudgets')
                        data = fetch_range(url, start, end, item['size'], ledger, ledger_path)
                        with prefix.open('ab') as stream:
                            stream.write(data)
                    report['remote_url'] = url
                    report['remote_file_size'] = item['size']
                    report['prefetched_beyond_header'] = prefix.stat().st_size - report['header_end']
                    if report['metadata'].get('split.count') != len(candidate['files']):
                        raise RuntimeError('Splitzahl stimmt nicht mit Kandidatenmanifest überein')
                    if report['metadata'].get('split.no') != index:
                        raise RuntimeError('Splitindex stimmt nicht mit Kandidatenmanifest überein')
                    reports.append(report)
                    print(candidate['name'], index + 1, 'Metadaten vollständig', flush=True)
                except (OSError, ValueError, RuntimeError) as exc:
                    failure = str(exc)
                    print(candidate['name'], 'UNBESTÄTIGT:', failure, flush=True)
                    break
            complete = len(reports) == len(candidate['files']) and failure is None
            result = {'candidate': candidate, 'all_parts_examined': complete,
                      'failure': failure, 'parts': reports,
                      'pgrn_split_inference_supported_by_installed_engine': False,
                      'practical_inference_tested': False}
            if complete:
                result['summary'] = summarize(reports)
            results.append(result)
            (directory / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
        print('Fertig. Nur Ergebnisse mit all_parts_examined=true sind vollständig geprüft.')
        print('PGRN-Inferenz mit unveränderten Split-Dateien bleibt blockiert.')
        print('Nutzdaten:', ledger['read_payload_bytes'], 'Bytes; reserviert:', ledger['reserved_payload_bytes'])


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Unterbrochen. Header und Budget bleiben erhalten; gleicher Befehl setzt fort.')
        raise SystemExit(130)
    except (OSError, RuntimeError, ValueError) as exc:
        print('ABBRUCH:', exc)
        raise SystemExit(1)
