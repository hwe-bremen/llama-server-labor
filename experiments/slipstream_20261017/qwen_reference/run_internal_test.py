#!/usr/bin/env python3
"""Authorized isolated Qwen/PGRN test A. No download, conversion, or external copy.
Unloads existing Qwen models by router API only; stops only its own subprocesses.
Leaves those router models unloaded after the test (no automatic reload).
"""
import argparse
import datetime
import errno
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import urllib.request
from urllib.error import HTTPError

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(EXP))
from experiment import listeners, lab_snapshot, wait_listener

HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
MODEL = Path('/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen35b-reference/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf')
PGRN = EXP / 'pgrn/Qwen3.6-35B-A3B-UD-Q4_K_XL.pgrn'
ENGINE = EXP / 'runtime/Slipstream.app/Contents/Resources/resources/llama-server'


def request(path, payload=None, port=8080, timeout=5):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f'http://127.0.0.1:{port}{path}', data=body,
                                 headers={'Content-Type': 'application/json'})
    try:
        with HTTP.open(req, timeout=timeout) as response:
            raw = response.read(2**20 + 1)
            if len(raw) > 2**20:
                raise RuntimeError('API response unexpectedly large')
            return json.loads(raw)
    except OSError as exc:
        reason = getattr(exc, 'reason', exc)
        if getattr(reason, 'errno', None) in (errno.EPERM, errno.EACCES):
            raise RuntimeError('localhost durch Ausführungsumgebung blockiert; kein Engine-Fehler') from exc
        raise


def loaded_models(data):
    result = []
    if not isinstance(data.get('data'), list):
        raise RuntimeError('Unbekanntes Router-Modelllistenformat')
    for model in data['data']:
        value = model.get('status', {})
        value = value.get('value') if isinstance(value, dict) else value
        if value in ('unloaded',):
            continue
        if value != 'loaded':
            raise RuntimeError(f'Unklarer/aktiver Modellzustand, nicht entladen: {model.get("id")} / {value}')
        if 'qwen' not in model.get('id', '').lower():
            raise RuntimeError(f'Anderes Modell geladen; keine Änderung: {model.get("id")}')
        result.append(model['id'])
    return result


def pending_after_unload(data):
    """Loading may be transient or a reload: wait, never start alongside it."""
    if not isinstance(data.get('data'), list):
        raise RuntimeError('Unbekanntes Router-Modelllistenformat')
    pending = []
    for model in data['data']:
        state = model.get('status', {})
        state = state.get('value') if isinstance(state, dict) else state
        if state == 'unloaded':
            continue
        if state in ('loaded', 'loading', 'unloading') and 'qwen' in model.get('id', '').lower():
            pending.append({'id': model['id'], 'state': state})
        else:
            raise RuntimeError(f'Unbekanntes/anderes aktives Modell: {model.get("id")} / {state}')
    return pending


def capture(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    return {'returncode': r.returncode, 'stdout': r.stdout, 'stderr': r.stderr}


def memory():
    vm = capture(['/usr/bin/vm_stat'])
    swap = capture(['/usr/sbin/sysctl', 'vm.swapusage'])
    found = re.search(r'^Swapouts:\s+(\d+)', vm['stdout'], re.M)
    return {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'vm_stat': vm, 'swapusage': swap,
            'swapouts': int(found.group(1)) if found else None}


def same_lab(before, after):
    return before == after


def stopped_lab_snapshot():
    return {str(port): {'listeners': listeners(port)} for port in (8080, 8091, 8092, 8093, 8787)}


def llama_pids():
    result = capture(['/usr/sbin/lsof', '-nP', '-c', 'llama-server', '-Fpc'])
    if result['returncode'] not in (0, 1) or result['stderr'].strip():
        raise RuntimeError('Vorhandene llama-server-Prozesse nicht sicher prüfbar')
    return {int(line[1:]) for line in result['stdout'].splitlines() if line.startswith('p')}


def main(lab_stopped=False, run_dir=None, client_script=None, disk_sampler=None, load_timeout=180,
         context_size=512, client_timeout=600, no_context_shift=False, client_progress=False):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run = Path(run_dir) if run_dir is not None else HERE / 'runs' / ('internal-' + stamp)
    run.mkdir(parents=True)
    report = {'run': str(run), 'variant': str(PGRN),
              'inference_passed': False, 'external_streaming_proven': False,
              'unloaded_models': [], 'model_reload_performed': False}
    process = None
    client = None
    caffeinator = None
    stop = threading.Event()
    monitor = None
    engine_log = None
    def save():
        (run / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    def disk_sample():
        try:
            return {'ok': True, 'data': disk_sampler()}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}
    try:
        if listeners(8083):
            raise RuntimeError('Port 8083 belegt; kein Prozess wird gestoppt')
        if not Path('/Volumes/Extern M4 Speicher').is_mount():
            raise RuntimeError('Externe SSD nicht eingehängt')
        manifest = json.loads((HERE / 'logs/download-complete.json').read_text())
        conversion = json.loads((HERE / 'logs/conversion-status.json').read_text())
        if not (manifest.get('sha256_verified') and conversion.get('matches_reference_sha256') and
                MODEL.stat().st_size == 22853663008 and PGRN.stat().st_size == 20128754176):
            raise RuntimeError('Verifizierte Modell-/PGRN-Artefakte fehlen')
        report['lab_mode'] = 'stopped' if lab_stopped else 'running'
        if lab_stopped:
            report['lab_before'] = stopped_lab_snapshot()
            if any(e['listeners'] for e in report['lab_before'].values()) or llama_pids():
                raise RuntimeError('--lab-stopped verlangt gestopptes Labor und keine weitere llama-server-Instanz')
            print('Labor gestoppt bestätigt; keine Router-API und keine Modellentladung nötig.', flush=True)
            save()
        else:
            # Read-only network preflight BEFORE any model unload or own server start.
            models = request('/v1/models')
            report['router_models_before'] = models
            report['lab_before'] = lab_snapshot()
            if any('http_error' in e or not e['listeners'] for e in report['lab_before'].values()):
                raise RuntimeError('Labor-Vorprüfung nicht vollständig; kein Modell wird entladen')
            targets = loaded_models(models)
            save()
            for model in targets:
                print('Gezieltes Entladen über Router-API:', model, flush=True)
                request('/models/unload', {'model': model}, timeout=60)
                report['unloaded_models'].append(model)
                save()
            deadline = time.monotonic() + 60
            stable = 0
            report['router_unload_observations'] = []
            while True:
                current = request('/v1/models')
                pending = pending_after_unload(current)
                report['router_last_observed'] = current
                report['router_unload_observations'].append({'at': time.time(), 'pending': pending})
                save()
                stable = stable + 1 if not pending else 0
                if stable >= 3:
                    report['router_unloaded_confirmed_before_start'] = True
                    break
                if time.monotonic() > deadline:
                    raise RuntimeError('Qwen nicht stabil entladen; möglicherweise weitere Client-Anfragen. Kein zusätzlicher Modellstart.')
                if pending:
                    print('Warte auf entladenes Labormodell:', pending, flush=True)
                time.sleep(1)
            report['router_models_after_unload'] = current
        report['memory_before'] = memory()
        report['pressure_before'] = capture(['/usr/bin/memory_pressure'])
        if report['memory_before']['swapouts'] is None:
            raise RuntimeError('Swapout-Zähler nicht lesbar; kein Modellstart')
        if listeners(8083):
            raise RuntimeError('Port 8083 inzwischen belegt')
        cmd = [str(ENGINE),
               '--model', str(MODEL), '--pgrn', str(PGRN),
               '--host', '127.0.0.1', '--port', '8083', '--alias', 'qwen-stream-reference',
               '--pgrn-cache-gb', '2', '--pgrn-headroom-gb', '8', '--pgrn-io-threads', '1',
               '--pgrn-hot-percent', '0', '--ctx-size', str(context_size), '--batch-size', '32',
               '--ubatch-size', '32', '--parallel', '1', '--gpu-layers', '99',
               '--no-mmap', '--no-repack', '--no-warmup', '--cache-type-k', 'f16',
               '--cache-type-v', 'f16', '--spec-type', 'draft-mtp',
               '--spec-draft-n-max', '4', '--temp', '0', '--seed', '42']
        if no_context_shift:
            cmd.append('--no-context-shift')
        report['command'] = cmd
        env = {'HOME': os.environ['HOME'], 'PATH': '/usr/bin:/bin:/usr/sbin:/sbin'}
        engine_log = (run / 'engine.log').open('w')
        if disk_sampler:
            report['physical_io_before_load'] = disk_sample()
        started = time.monotonic()
        process = subprocess.Popen(cmd, stdout=engine_log, stderr=subprocess.STDOUT, env=env)
        caffeinator = subprocess.Popen(['/usr/bin/caffeinate', '-im', '-w', str(process.pid)],
                                       stdout=subprocess.DEVNULL, stderr=engine_log, env=env)
        report['owned_engine_pid'] = process.pid
        print('Eigene Qwen-Engine gestartet, PID', process.pid,
              '— prüft Quellidentität und lädt PGRN:', PGRN, flush=True)
        save()

        def watch():
            tick = 0
            with (run / 'memory.jsonl').open('w') as out:
                while not stop.is_set():
                    try:
                        sample = memory()
                        sample['rss'] = capture(['/bin/ps', '-o', 'rss=', '-p', str(process.pid)])
                        if disk_sampler and tick % 2 == 0:
                            sample['physical_io'] = disk_sample()
                        out.write(json.dumps(sample) + '\n'); out.flush()
                        if caffeinator.poll() is not None:
                            raise RuntimeError('Eigene Sleep-Assertion vorzeitig beendet')
                        if tick % 5 == 0:
                            if lab_stopped:
                                if any(e['listeners'] for e in stopped_lab_snapshot().values()) or llama_pids() - {process.pid}:
                                    raise RuntimeError('Labor/andere llama-Instanz zwischenzeitlich gestartet')
                            elif loaded_models(request('/v1/models')):
                                raise RuntimeError('Router hat zwischenzeitlich wieder ein Qwen-Modell geladen')
                        tick += 1
                        base = report['memory_before']['swapouts']
                        if sample['swapouts'] is None or sample['swapouts'] > base:
                            report['safety_abort'] = 'Swapouts gestiegen oder Überwachung ausgefallen'
                            print('SICHERHEITSABBRUCH:', report['safety_abort'], flush=True)
                            if process.poll() is None:
                                process.terminate()
                            return
                    except Exception as exc:
                        report['safety_abort'] = str(exc)
                        if process.poll() is None:
                            process.terminate()
                        return
                    stop.wait(1)
        monitor = threading.Thread(target=watch, daemon=True)
        monitor.start()
        # Direct engine Popen handle owns the listener; caffeinate is separate.
        deadline = time.monotonic() + load_timeout
        next_notice = time.monotonic() + 10
        while True:
            if process.poll() is not None:
                raise RuntimeError(f'Engine vor Bereitschaft beendet, Exit {process.returncode}; engine.log lesen')
            try:
                health = request('/health', port=8083, timeout=3)
                if health.get('status') == 'ok':
                    break
            except (HTTPError, urllib.error.URLError, TimeoutError):
                pass
            if time.monotonic() > deadline:
                raise RuntimeError(f'Engine nach {load_timeout} Sekunden nicht bereit')
            if time.monotonic() > next_notice:
                print('Engine noch beim Laden; vergangen', round(time.monotonic() - started), 's', flush=True)
                next_notice = time.monotonic() + 10
            time.sleep(1)
        wait_listener(process, 8083, 'Qwen-Engine')
        report['load_to_health_s'] = time.monotonic() - started
        report['models'] = request('/v1/models', port=8083)
        report['props'] = request('/props', port=8083)
        if disk_sampler:
            report['physical_io_after_load'] = disk_sample()
        report['open_files'] = capture(['/usr/sbin/lsof', '-nP', '-p', str(process.pid)])
        if str(PGRN) not in report['open_files']['stdout']:
            raise RuntimeError('Geöffnete gewählte PGRN nicht nachweisbar')
        print('Qwen/PGRN bereit; Ladezeit bis /health:', round(report['load_to_health_s'], 2), 's', flush=True)
        report['io_before_requests'] = capture(['/usr/sbin/ioreg', '-r', '-c', 'IOBlockStorageDriver', '-l', '-w', '0'])
        save()
        print('Vorbereitete API-Anfragen; Speicherüberwachung aktiv.', flush=True)
        with (run / 'client.log').open('w') as out:
            client = subprocess.Popen([sys.executable, '-B', str(client_script or HERE / 'request_stream.py'),
                         '--output', str(run / 'responses.json')], stdout=out,
                         stderr=subprocess.STDOUT, env=env)
            end = time.monotonic() + client_timeout
            progress_offset = 0
            while client.poll() is None:
                if report.get('safety_abort') or process.poll() is not None:
                    raise RuntimeError('Engine/Speicherüberwachung hat Test abgebrochen')
                if time.monotonic() > end:
                    raise RuntimeError(f'Testanfragen nach {client_timeout} Sekunden abgebrochen')
                if client_progress:
                    with (run / 'client.log').open() as progress:
                        progress.seek(progress_offset)
                        text = progress.read()
                        progress_offset = progress.tell()
                    if text:
                        print(text, end='', flush=True)
                time.sleep(1)
        if client.returncode:
            raise RuntimeError('API-Anfrage fehlgeschlagen; client.log lesen')
        if client_progress:
            with (run / 'client.log').open() as progress:
                progress.seek(progress_offset)
                print(progress.read(), end='', flush=True)
        else:
            print((run / 'client.log').read_text(), flush=True)
        report['io_after_requests'] = capture(['/usr/sbin/ioreg', '-r', '-c', 'IOBlockStorageDriver', '-l', '-w', '0'])
        report['responses'] = json.loads((run / 'responses.json').read_text())
        report['api_requests_completed'] = True
    except KeyboardInterrupt:
        report['error'] = 'Durch Ctrl+C unterbrochen'
        print('Unterbrochen; nur eigene Testprozesse werden beendet.', flush=True)
    except Exception as exc:
        report['error'] = str(exc)
        print('ABBRUCH:', exc, flush=True)
    finally:
        # Only the two processes created above; never existing router/model PIDs.
        stop.set()
        for child in (client, process, caffeinator):
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait(timeout=10)
                    report['forced_cleanup'] = True
        stop.set()
        if monitor:
            monitor.join(timeout=15)
        if engine_log:
            engine_log.close()
        report['memory_after'] = memory()
        if 'lab_before' in report:
            report['lab_after'] = stopped_lab_snapshot() if lab_stopped else lab_snapshot()
            report['lab_listeners_and_http_unchanged'] = same_lab(report['lab_before'], report['lab_after'])
        report['test_port_after'] = listeners(8083) or 'frei'
        if process is not None:
            report['engine_exit_code'] = process.returncode
            log = (run / 'engine.log').read_text(errors='replace')
            report['native_cache_telemetry'] = re.findall(
                r'PGRN cache = .*hits = (\d+), misses = (\d+).*', log)
            report['cache_misses_observed'] = any(int(miss) > 0 for _, miss in report['native_cache_telemetry'])
        report['inference_passed'] = bool(report.get('api_requests_completed') and
            report.get('cache_misses_observed') and not report.get('error') and
            not report.get('safety_abort') and not report.get('forced_cleanup') and
            report.get('lab_listeners_and_http_unchanged') and report['test_port_after'] == 'frei')
        save()
        print('Ergebnis:', 'INFERENZTEST BESTANDEN' if report['inference_passed'] else 'NICHT BESTÄTIGT', flush=True)
        print('Labor weiterhin gestoppt:' if lab_stopped else 'Labor-Listener/HTTP unverändert:', report.get('lab_listeners_and_http_unchanged'), flush=True)
        print('Port 8083:', report['test_port_after'], flush=True)
        print('Entladeaufruf erfolgreich für:', report['unloaded_models'], flush=True)
        print('Router vollständig entladen vor Teststart bestätigt:',
              report.get('router_unloaded_confirmed_before_start', False), flush=True)
        print('Protokolle:', run, flush=True)
    return 0 if report['inference_passed'] else 1


if __name__ == '__main__':
    (HERE / 'logs').mkdir(exist_ok=True)
    with (HERE / 'logs/internal-test.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--lab-stopped', action='store_true', help='Labor aus; keine Router-API oder Modellentladung verwenden')
        args = parser.parse_args()
        raise SystemExit(main(lab_stopped=args.lab_stopped))
