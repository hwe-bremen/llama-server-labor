#!/usr/bin/env python3
"""Authorized A/B: verified external PGRN copy and six sequential bounded tests.
Never unloads/stops lab services, downloads weights, converts, or purges caches.
"""
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import statistics
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import download_glm as paths
import run_internal_test as runner
from disk_counters import snapshot, delta

SIZE = 20128754176
SHA = '732a314b95cb3a63e31c3c9cd44e284757721d13a29d7aecd10360d13e193269'
INTERNAL = runner.PGRN
MOUNT = Path('/Volumes/Extern M4 Speicher')
DEST = MOUNT / 'LLM-Experimente/slipstream/qwen35b-pgrn-comparison'
EXTERNAL = DEST / INTERNAL.name
ORDER = ['A1', 'B1', 'B2', 'A2', 'B3', 'A3']


def require_quiet():
    if any(e['listeners'] for e in runner.stopped_lab_snapshot().values()) or runner.listeners(8083) or runner.llama_pids():
        raise RuntimeError('Labor oder andere llama-Instanz läuft. Nichts wird automatisch gestoppt.')
    paths.check_mount(MOUNT, DEST)


def hash_file(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size != SIZE:
        raise RuntimeError('Kein unverändertes reguläres PGRN-Artefakt: ' + str(path))
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(block)
    if h.hexdigest() != SHA:
        raise RuntimeError('PGRN-SHA weicht vom Referenzwert ab: ' + str(path))
    return h.hexdigest()


def phase(label, action, journal):
    print(label, flush=True)
    before = snapshot(); start = time.time()
    value = action()
    after = snapshot()
    journal.append({'phase': label, 'start_epoch': start, 'end_epoch': time.time(),
                    'before': before, 'after': after, 'delta': delta(before, after)})
    return value


def copy_verified():
    paths.check_mount(MOUNT, DEST)
    if EXTERNAL.exists():
        return 'existing_copy'
    if shutil.disk_usage(MOUNT).free < SIZE + 10 * 2**30:
        raise RuntimeError('Externer Platz reicht nicht inklusive 10 GiB Reserve')
    paths.external_directory(MOUNT, DEST)  # anchored external dir_fd, no missing-mount fallback
    part = Path(INTERNAL.name + '.copying')
    if part.exists() or part.is_symlink():
        raise RuntimeError('Vorhandenes Kopier-Teilziel bleibt erhalten: ' + str(DEST / part))
    copied = 0; next_notice = 2**30
    with INTERNAL.open('rb') as src, part.open('xb') as dst:
        for block in iter(lambda: src.read(8 * 1024 * 1024), b''):
            dst.write(block); copied += len(block)
            if copied >= next_notice:
                paths.check_mount(MOUNT, DEST)
                print('Kopie:', round(100 * copied / SIZE), '%', flush=True)
                next_notice += 2**30
        dst.flush(); os.fsync(dst.fileno())
    paths.check_mount(MOUNT, DEST)
    if copied != SIZE:
        raise RuntimeError('Quellgröße während Kopie geändert')
    # No overwrite; rename completion after byte-for-byte hash validation below.
    return str(DEST / part)


def stat(values):
    return {'n': len(values), 'median': statistics.median(values),
            'min': min(values), 'max': max(values)} if values else None


def summarize(parent, runs):
    result = {'order': ORDER, 'variants': {}, 'per_prompt': {}, 'complete_six_runs': len(runs) == 6,
              'cache_state': 'OS cache uncontrolled; copy/hash warmup recorded; no cold claim',
              'physical_counter_scope': 'Whole physical device, not exclusive process/file attribution'}
    normalized = []
    for label, report in runs:
        cmd = report.get('command', []).copy()
        if '--pgrn' in cmd:
            cmd[cmd.index('--pgrn') + 1] = '<ONLY_VARIANT_DIFFERENCE>'
        normalized.append(cmd)
    result['only_pgrn_command_argument_differs'] = bool(normalized) and all(x == normalized[0] for x in normalized)
    for variant in ('A', 'B'):
        group = [(label, r) for label, r in runs if label.startswith(variant)]
        rows = []
        peaks = []
        for label, r in group:
            sample_file = Path(r['run']) / 'memory.jsonl'
            samples = [json.loads(line) for line in sample_file.read_text().splitlines()] if sample_file.exists() else []
            rss = [int(x['rss']['stdout'].strip()) for x in samples if x.get('rss', {}).get('stdout', '').strip().isdigit()]
            if rss:
                peaks.append(max(rss) / 2**20)
            prior_hits = prior_miss = 0
            for i, response in enumerate(r.get('responses', [])):
                timing = next((e['timings'] for e in reversed(response['events']) if e.get('timings')), {})
                row = {'run': label, 'prompt': response['prompt_index'],
                       'ttft_s': response['first_visible_token_s'], 'wall_s': response['wall_s'],
                       'decode_tokens_s': timing.get('predicted_per_second'),
                       'actual_output_tokens': timing.get('predicted_n'),
                       'physical_io_delta': response.get('physical_io_delta'),
                       'idle_io_delta': response.get('idle_io_delta'),
                       'idle_window_s': response.get('idle_window_s')}
                telemetry = r.get('native_cache_telemetry', [])
                if i < len(telemetry):
                    hits, miss = map(int, telemetry[i])
                    row.update(cache_hits_delta=hits-prior_hits, cache_misses_delta=miss-prior_miss)
                    prior_hits, prior_miss = hits, miss
                # Strictly inside decode: counter snapshots after first visible token
                # and before request finish, excluding model load/prefill/copy/hash.
                start = response['start_epoch'] + response['first_visible_token_s']
                end = response['start_epoch'] + response['wall_s']
                inside = [x['physical_io']['data'] for x in samples if x.get('physical_io', {}).get('ok') and
                          x['physical_io']['data']['start_epoch'] >= start and
                          x['physical_io']['data']['end_epoch'] <= end]
                if len(inside) >= 2:
                    row['decode_subset_io_delta'] = delta(inside[0], inside[-1])
                    row['decode_subset_window_s'] = inside[-1]['end_epoch'] - inside[0]['end_epoch']
                rows.append(row)
        result['variants'][variant] = {
            'runs_passed': len(group) == 3 and all(r.get('inference_passed') for _, r in group),
            'load_s': stat([r['load_to_health_s'] for _, r in group if 'load_to_health_s' in r]),
            'peak_rss_gib': stat(peaks),
            'swapout_deltas': [r['memory_after']['swapouts'] - r['memory_before']['swapouts']
                 if r.get('memory_before', {}).get('swapouts') is not None and
                    r.get('memory_after', {}).get('swapouts') is not None else None for _,r in group],
            'requests': rows,
            'all_requested_128_tokens': bool(rows) and all(row['actual_output_tokens'] == 128 for row in rows),
            'ttft_s': stat([x['ttft_s'] for x in rows]),
            'wall_s': stat([x['wall_s'] for x in rows]),
            'decode_tokens_s': stat([x['decode_tokens_s'] for x in rows if x['decode_tokens_s'] is not None])}
        for prompt in (1, 2):
            selected = [x for x in rows if x['prompt'] == prompt]
            result['per_prompt'][f'{variant}/prompt{prompt}'] = {
                k: stat([x[k] for x in selected if x.get(k) is not None])
                for k in ('ttft_s', 'wall_s', 'decode_tokens_s', 'cache_misses_delta')}
    b = result['variants']['B']['requests']
    result['external_pgrn_path_verified'] = len([r for label,r in runs if label.startswith('B') and
        str(EXTERNAL) in r.get('open_files', {}).get('stdout', '')]) == 3
    result['external_cache_misses_verified'] = len(b) == 6 and all(x.get('cache_misses_delta', 0) > 0 for x in b)
    result['external_device_reads_during_requests'] = len(b) == 6 and all(
        (x.get('physical_io_delta') or {}).get('external', {}).get('read_bytes', 0) > 0 for x in b)
    result['external_device_reads_during_decode_subsets'] = len(b) == 6 and all(
        x.get('decode_subset_io_delta', {}).get('external', {}).get('read_bytes', 0) > 0 for x in b)
    (parent / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    def fmt(s):
        return f"{s['median']:.2f} ({s['min']:.2f}–{s['max']:.2f})" if s else 'offen'
    lines = ['# PGRN intern / Samsung T7', '', 'Median (Minimum–Maximum). A/B jeweils 3 neue Prozesse.',
        'Je Prozess beide bisherigen Prompts, jeweils Limit 128; Prompt 1 prozessfrisch, Prompt 2 arena-vorgewärmt.',
        'OS-Dateicache nicht kontrolliert; kein Kaltstart-Benchmark.', '',
        '| Messgröße | A intern | B T7 |','|---|---:|---:|']
    for k, name in [('load_s','Ladezeit s'),('ttft_s','TTFT s, beide Prompts'),
                    ('decode_tokens_s','Decode Tokens/s, beide Prompts'),('wall_s','Anfrage gesamt s'),
                    ('peak_rss_gib','Peak Prozess-RSS GiB')]:
        lines.append('| '+name+' | '+fmt(result['variants']['A'][k])+' | '+fmt(result['variants']['B'][k])+' |')
    lines.append('| Zusätzliche Swapouts je Prozess, Seiten | '+str(result['variants']['A']['swapout_deltas'])+
                 ' | '+str(result['variants']['B']['swapout_deltas'])+' |')
    for physical in ('internal', 'external'):
        cells = []
        for variant in ('A','B'):
            values = [x['physical_io_delta'][physical]['read_bytes'] / 1e9
                for x in result['variants'][variant]['requests'] if x.get('physical_io_delta')]
            cells.append(fmt(stat(values)))
        lines.append('| Physische '+physical+' Reads GB/Anfrage | '+' | '.join(cells)+' |')
    lines += ['', 'Die kombinierte Spanne mischt zwei Prompts; die saubere Gegenüberstellung pro Prompt folgt.', '',
              '| Prompt / Größe | A intern | B T7 |','|---|---:|---:|']
    for prompt in (1,2):
        for k in ('ttft_s','wall_s','decode_tokens_s','cache_misses_delta'):
            lines.append(f"| {prompt} / {k} | {fmt(result['per_prompt'][f'A/prompt{prompt}'][k])} | {fmt(result['per_prompt'][f'B/prompt{prompt}'][k])} |")
    lines += ['', 'Reihenfolge: '+', '.join(label for label,_ in runs), '',
        '- Externer PGRN-Pfad in allen B-Läufen belegt: '+str(result['external_pgrn_path_verified']),
        '- Positive native Cache-Misses in allen B-Anfragen: '+str(result['external_cache_misses_verified']),
        '- Physische T7-Lesezähler steigen in allen B-Anfragefenstern: '+str(result['external_device_reads_during_requests']),
        '- Auch in allen engeren Decode-Teilfenstern: '+str(result['external_device_reads_during_decode_subsets']),
        '- Identische Engineargumente außer PGRN-Pfad: '+str(result['only_pgrn_command_argument_differs']),
        '', 'Gerätezähler sind echte Blocktreiberzähler, aber nicht exklusiv einem Prozess/einer Datei zugeordnet.',
        'Leerlaufzähler und Rohsamples in summary.json und den einzelnen Läufen auswerten; Hintergrund-I/O kann mitwirken.',
        'Bei fehlenden/mehrdeutigen Zählern bleibt der physische externe Streaming-Nachweis offen.']
    complete = result['complete_six_runs'] and all(result['variants'][v]['runs_passed'] and
                 result['variants'][v]['all_requested_128_tokens'] for v in ('A','B'))
    if complete:
        a = result['variants']['A']['decode_tokens_s']['median']
        b_rate = result['variants']['B']['decode_tokens_s']['median']
        lines += ['', f'B/A Median-Decode: {b_rate/a:.3f}; Änderung {(b_rate/a-1)*100:.1f} %.']
        if not result['external_device_reads_during_decode_subsets']:
            lines += ['Empfehlung: aktive PGRN vorläufig intern belassen; physische T7-Bereitstellung noch nicht entscheidbar.']
        elif b_rate < a:
            lines += ['Empfehlung: aktive PGRN intern für Geschwindigkeit; externe Ablage funktional bestanden, gemessenen Zeitnachteil beachten.']
        else:
            lines += ['Empfehlung: externe Ablage in diesem kurzen, cachebeeinflussten Profil praktikabel; kein allgemeiner SSD-Geschwindigkeitsvorteil daraus ableiten.']
    else:
        lines += ['', 'Empfehlung: noch nicht entscheidbar; sechs vollständige, identische 128-Token-Prozesse fehlen.']
    lines += ['', 'Kein Nachweis für Modelle oberhalb 48 GB, GLM oder Reviewer-/Haiku-Qualität.']
    (parent / 'ERGEBNIS.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines), flush=True)


def main():
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    parent = HERE / 'comparisons' / stamp
    parent.mkdir(parents=True)
    operations, runs = [], []
    status = {'started_at': stamp, 'order': ORDER, 'output': str(parent), 'completed': False}
    try:
        require_quiet()
        engine_sha = hashlib.sha256(runner.ENGINE.read_bytes()).hexdigest()
        if engine_sha != '7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e':
            raise RuntimeError('Engine weicht vom erfolgreichen Referenzlauf ab')
        status['engine_sha256'] = engine_sha
        # Check execution context before any 20-GB copy. No model involved.
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 8083))
        status['initial_devices'] = snapshot()
        (parent / 'initial-ioreg.txt').write_bytes(__import__('subprocess').check_output(
            ['/usr/sbin/ioreg','-r','-c','IOBlockStorageDriver','-l','-w','0']))
        phase('Original intern vollständig hashen', lambda: hash_file(INTERNAL), operations)
        copied = phase('PGRN-Kopie auf T7 (kein Benchmark)', copy_verified, operations)
        copied_path = EXTERNAL if copied == 'existing_copy' else Path(copied)
        phase('Externe Kopie vollständig hashen', lambda: hash_file(copied_path), operations)
        if copied_path != EXTERNAL:
            os.link(copied_path, EXTERNAL, follow_symlinks=False)
            copied_path.unlink()
        status['verified_copy'] = {'path': str(EXTERNAL), 'bytes': SIZE, 'sha256': SHA}
        print('Kopie verifiziert. Keine kalten Dateicaches behauptet. Beginn A/B.', flush=True)
        for label in ORDER:
            require_quiet()
            status['active_run'] = label
            (parent/'status.json').write_text(json.dumps(status,indent=2)+'\n')
            runner.PGRN = INTERNAL if label.startswith('A') else EXTERNAL
            print('\nSTART', label, runner.PGRN, flush=True)
            code = runner.main(lab_stopped=True, run_dir=parent/label,
                client_script=HERE/'comparison_client.py', disk_sampler=snapshot, load_timeout=420)
            report = json.loads((parent/label/'report.json').read_text())
            runs.append((label, report))
            if code:
                raise RuntimeError('Lauf '+label+' nicht bestanden; keine weiteren Modelle starten')
        status['completed'] = True
    except KeyboardInterrupt:
        status['error'] = 'Durch Nutzer unterbrochen'
        print('Unterbrochen; Quellen bleiben erhalten.', flush=True)
    except Exception as exc:
        status['error'] = str(exc)
        print('ABBRUCH:',exc,flush=True)
    finally:
        runner.PGRN = INTERNAL
        status['lab_after'] = runner.stopped_lab_snapshot()
        status['port_8083_after'] = runner.listeners(8083) or 'frei'
        status['operations'] = operations
        (parent/'status.json').write_text(json.dumps(status,indent=2)+'\n')
        if runs:
            summarize(parent,runs)
        print('Labor wird nicht neu gestartet. Ergebnisse:',parent,flush=True)
    return 0 if status['completed'] else 1


if __name__ == '__main__':
    (HERE/'logs').mkdir(exist_ok=True)
    # Same lifecycle lock as the existing single-run starter.
    with (HERE/'logs/internal-test.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raise SystemExit(main())
