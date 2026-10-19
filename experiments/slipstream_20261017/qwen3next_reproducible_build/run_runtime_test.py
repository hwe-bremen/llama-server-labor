#!/usr/bin/env python3
"""Kontrollierte Laufzeittests A (Referenz) und B (Diagnose) fuer den PGRN-Geometriefehler.

Aufruf:  python3 run_runtime_test.py reference [--dry-run]
         python3 run_runtime_test.py diagnostic [--dry-run]
Ein eigener Serverprozess auf 127.0.0.1:8083, genau eine Anfrage (A: 17 + 25), danach Prozess beenden.
Keine bestehenden Dienste werden gestoppt; LLAMA_ARG_* nur fuer den Kindprozess entfernt.
B laeuft nur, wenn der letzte Referenzlauf den Geometriefehler reproduziert hat.
"""
import datetime, hashlib, json, os, re, signal, socket, subprocess, sys, time, urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
BINARIES = {
    'reference':  (HERE / 'reference/bin/llama-server-reference',
                   'f70c092c08792f7d8d98ab6fb9dfdc116151fc4c0c92460fe87c7a8e29575469'),
    'diagnostic': (HERE / 'diagnostic/bin/llama-server-pgrn-diagnostic',
                   '975ba7c66a85bd650df4f9025f9c90e14d067dc1f43374a85c2ca2667737b73e'),
    # korrigierte Builds (build_fix.sh); Hash aus der beim Build geschriebenen .sha256-Datei
    'fixed':      (HERE / 'fixed/bin/llama-server-pgrn-fixed', None),
    'fixed-diag': (HERE / 'fixed_diag/bin/llama-server-pgrn-fixed-diag', None),
}
FIXED = ('fixed', 'fixed-diag')
GGUF = Path('/Volumes/Extern M4 Speicher/LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m/Qwen3-Coder-Next-Q4_K_M.gguf')
GGUF_SIZE = 48528320544
PGRN = EXP / 'pgrn/qwen3-coder-next/Qwen3-Coder-Next-Q4_K_M.pgrn'
PGRN_SIZE = 46909751296
PORT = 8083
LAB_PORTS = (8080, 8091, 8092, 8787)
ERR = 'top-k tensor geometry is incompatible with PGRN staging'
PAYLOAD = {'messages': [{'role': 'user', 'content': 'Antworte ausschließlich mit der Zahl: 17 + 25'}],
           'max_tokens': 32, 'temperature': 0, 'seed': 42, 'stream': False}
# Fuer die korrigierten Builds: die drei Tests des Originallaufs (run_first_inference.py), unveraendert.
_B = 'Lies die folgenden Zeilen. Antworte ausschließlich mit dem Wert hinter KENNWORT.\n'
_B += '\n'.join(f'Eintrag {i:03d}: Dies ist ein neutraler Eintrag für den Prefill-Test.' for i in range(1, 41))
_B += '\nKENNWORT: BernsteinFalke739\nGib ausschließlich das Kennwort zurück.'
FULL_TESTS = [('A', 32, 'Antworte ausschließlich mit der Zahl: 17 + 25'), ('B', 64, _B),
              ('C', 512, 'Prüfe diese Python-Funktion. Spezifikation: Mittelwert ausschließlich strikt positiver Werte; '
                         'falls keine existieren, None zurückgeben. Benenne beide Fehler und schlage eine Korrektur vor.\n'
                         '```python\ndef mean_positive(values):\n    positives = [x for x in values if x >= 0]\n'
                         '    return sum(positives) / len(positives)\n```')]
RUNS = HERE / 'runtime_runs'
DIAG_RE = re.compile(r'\[PGRN-DIAG\] layer=(\d+) name=(\S+) type=(\d+)\((\S+)\) '
                     r'ne=\[(-?\d+),(-?\d+),(-?\d+),(-?\d+)\] nb=\[(\d+),(\d+),(\d+),(\d+)\] '
                     r'n_expert_used=(\d+) ask=(\d) is_pgrn=(\d) compact=(\d)')
GGML_TYPE_I32 = 26  # ggml.h enum; wird zusaetzlich ueber den Typnamen 'i32' abgesichert


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def listeners():
    r = subprocess.run(['/usr/sbin/lsof', '-nP', '-iTCP', '-sTCP:LISTEN'], capture_output=True, text=True)
    ports = set()
    for line in r.stdout.splitlines()[1:]:
        m = re.search(r':(\d+) \(LISTEN\)', line)
        if m:
            ports.add(int(m.group(1)))
    return sorted(ports)


def free_percent():
    r = subprocess.run(['/usr/bin/memory_pressure', '-Q'], capture_output=True, text=True)
    m = re.search(r'free percentage: (\d+)%', r.stdout)
    return int(m.group(1)) if m else None


def request(path, payload=None, timeout=5):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f'http://127.0.0.1:{PORT}{path}', data=data,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def analyse_diag(text, n_expert_used_fallback=None):
    """Wertet [PGRN-DIAG]-Zeilen aus: letzte Zeile vor dem Fehler + jede Guard-Bedingung einzeln."""
    lines = text.splitlines()
    err_idx = next((i for i, l in enumerate(lines) if ERR in l), None)
    recs = []
    for i, l in enumerate(lines):
        m = DIAG_RE.search(l)
        if m:
            g = m.groups()
            recs.append({'line': i, 'layer': int(g[0]), 'name': g[1], 'type': int(g[2]), 'type_name': g[3],
                         'ne': [int(x) for x in g[4:8]], 'nb': [int(x) for x in g[8:12]],
                         'n_expert_used': int(g[12]), 'ask': int(g[13]), 'is_pgrn': int(g[14]),
                         'compact': int(g[15])})
    out = {'diag_lines': len(recs), 'error_line': err_idx}
    if not recs:
        return out
    before = [r for r in recs if err_idx is None or r['line'] < err_idx]
    failing = before[-1] if before else None
    def guard(r):
        return {
            'type_is_i32': r['type_name'] == 'i32' or r['type'] == GGML_TYPE_I32,
            'ne0_eq_n_expert_used': r['ne'][0] == r['n_expert_used'],
            'ne1_gt_0': r['ne'][1] > 0,
            'ne2_eq_1': r['ne'][2] == 1,
            'ne3_eq_1': r['ne'][3] == 1,
            'nb0_eq_4': r['nb'][0] == 4,
        }
    out['failing_candidate'] = failing
    if failing:
        out['failing_guard'] = guard(failing)
        out['failing_violated'] = [k for k, v in out['failing_guard'].items() if not v]
    pgrn_ok = [r for r in before[:-1] if r['is_pgrn']] if before else []
    out['earlier_pgrn_callbacks'] = len(pgrn_ok)
    if pgrn_ok:
        out['earlier_example'] = pgrn_ok[-1]
        out['earlier_all_pass'] = all(all(guard(r).values()) for r in pgrn_ok)
    out['distinct_geometries'] = sorted({json.dumps([r['type_name'], r['ne'], r['nb'], r['compact']]) for r in recs})[:20]
    return out


def last_reference_result():
    if not RUNS.exists():
        return None
    for d in sorted(RUNS.glob('*_reference'), reverse=True):
        f = d / 'result.json'
        if f.exists():
            return json.loads(f.read_text())
    return None


def main():
    args = sys.argv[1:]
    if not args or args[0] not in BINARIES:
        sys.exit('Aufruf: python3 run_runtime_test.py reference|diagnostic|fixed|fixed-diag [--dry-run] '
                 '[--cache-gb N] [--io-threads N]   (Optionen nur fuer fixed/fixed-diag)')
    which, dry = args[0], '--dry-run' in args
    def opt(name):
        if name in args:
            i = args.index(name)
            if i + 1 >= len(args) or not args[i + 1].isdigit():
                sys.exit(f'{name} braucht eine ganze Zahl')
            return int(args[i + 1])
        return None
    cache_gb, io_threads = opt('--cache-gb'), opt('--io-threads')
    if (cache_gb is not None or io_threads is not None) and which not in FIXED:
        sys.exit('--cache-gb/--io-threads nur fuer fixed/fixed-diag (A/B bleiben beim Originallauf)')
    cache_gb = 12 if cache_gb is None else cache_gb
    binary, want_sha = BINARIES[which]
    if want_sha is None:
        f = Path(str(binary) + '.sha256')
        want_sha = f.read_text().strip() if f.exists() else 'fehlt'
    state = {'which': which, 'started_at': now(), 'dry_run': dry, 'server_started': False, 'requests_sent': 0}
    checks = state['checks'] = {}

    # --- Vorbedingungen (alles nur lesend) ---
    if which == 'diagnostic':
        ref = last_reference_result()
        checks['reference_reproduced'] = bool(ref and ref.get('reproduced'))
        if not checks['reference_reproduced']:
            sys.exit('ABBRUCH: Test B nur nach Test A mit reproduziertem Geometriefehler (letzter Referenzlauf: '
                     + (ref.get('outcome', '?') if ref else 'keiner') + ')')
    checks['binary_sha256_ok'] = binary.exists() and sha256(binary) == want_sha
    checks['gguf_size_ok'] = GGUF.exists() and GGUF.stat().st_size == GGUF_SIZE
    checks['pgrn_size_ok'] = PGRN.exists() and PGRN.stat().st_size == PGRN_SIZE
    ports_before = listeners()
    checks['port_8083_free'] = PORT not in ports_before
    checks['lab_ports_before'] = [p for p in LAB_PORTS if p in ports_before]
    checks['memory_free_percent'] = free_percent()
    # Bindprobe ohne Listener. Direkt nach einem Lauf haelt macOS den Port kurz in TIME_WAIT -> bis 120 s warten.
    checks['port_8083_bindable'] = False
    for attempt in range(61):
        with socket.socket() as s:
            try:
                s.bind(('127.0.0.1', PORT)); checks['port_8083_bindable'] = True; break
            except OSError:
                pass
        if attempt == 0:
            print('Port 8083 noch nicht frei (TIME_WAIT nach letztem Lauf?), warte bis 120 s ...', flush=True)
        time.sleep(2)
    failed = [k for k in ('binary_sha256_ok', 'gguf_size_ok', 'pgrn_size_ok', 'port_8083_free', 'port_8083_bindable')
              if not checks[k]]
    argv = [str(binary), '--model', str(GGUF), '--pgrn', str(PGRN), '--host', '127.0.0.1', '--port', str(PORT),
            '--ctx-size', '4096', '--pgrn-cache-gb', str(cache_gb), '--pgrn-headroom-gb', '8', '--batch-size', '25',
            '--ubatch-size', '25', '--parallel', '1', '--spec-type', 'none', '--reasoning', 'off', '--temp', '0',
            '--seed', '42', '--gpu-layers', '99', '--jinja', '--verbosity', '5', '--log-colors', 'off']
    if io_threads is not None:
        argv += ['--pgrn-io-threads', str(io_threads)]
    state.update(cache_gb=cache_gb, io_threads=io_threads)
    env = {k: v for k, v in os.environ.items() if not k.startswith('LLAMA_ARG_')}
    state.update(argv=argv, env_removed=sorted(k for k in os.environ if k.startswith('LLAMA_ARG_')))
    print(json.dumps(checks, indent=1, ensure_ascii=False))
    if checks['memory_free_percent'] is not None and checks['memory_free_percent'] < 50:
        failed.append('memory_free_percent<50 (Originallauf: 91 %)')
    if failed:
        sys.exit('ABBRUCH, Vorbedingung nicht erfuellt: ' + ', '.join(failed))
    if dry:
        print('TROCKENLAUF ok. argv:\n  ' + ' '.join(argv)); print('entfernte Variablen:', state['env_removed'] or 'keine')
        return

    # --- Lauf ---
    suffix = (f'_c{cache_gb}' + (f'_io{io_threads}' if io_threads is not None else '')) if which in FIXED else ''
    run = RUNS / (datetime.datetime.now().strftime('%Y%m%dT%H%M%S') + '_' + which + suffix)
    run.mkdir(parents=True)
    (run / 'request.json').write_text(json.dumps(PAYLOAD, ensure_ascii=False, indent=1))
    log = (run / 'engine.log').open('x')
    proc = None
    try:
        proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, cwd=EXP, env=env,
                                start_new_session=True)
        state.update(server_started=True, pid=proc.pid)
        print(f'Eigener Testserver PID {proc.pid}, laedt (Original: ~280 s) ...', flush=True)
        t0 = time.monotonic(); last = 0
        while True:
            if proc.poll() is not None:
                raise RuntimeError(f'Server beendet sich beim Laden (exit {proc.returncode})')
            if time.monotonic() - t0 > 1200:
                raise TimeoutError('Laden > 20 min')
            try:
                if request('/health', timeout=2).get('status') == 'ok':
                    break
            except urllib.error.HTTPError as e:
                if e.code != 503: raise
            except (urllib.error.URLError, ConnectionError, socket.timeout):
                pass
            if time.monotonic() - last > 30:
                print(f'  {int(time.monotonic() - t0)} s', flush=True); last = time.monotonic()
            time.sleep(2)
        state['load_seconds'] = round(time.monotonic() - t0, 1)
        print('Geladen nach', state['load_seconds'], 's.', flush=True)
        if which in FIXED:
            state['tests'] = {}
            for label, limit, prompt in FULL_TESTS:
                payload = {'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': limit,
                           'temperature': 0, 'seed': 42, 'stream': False}
                (run / f'request_{label}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=1))
                print(f'Test {label} ...', flush=True)
                state['requests_sent'] += 1; t1 = time.monotonic()
                res = {}
                try:
                    resp = request('/v1/chat/completions', payload, timeout=600)
                    (run / f'response_{label}.json').write_text(json.dumps(resp, ensure_ascii=False, indent=1))
                    res.update(http_status=200, content=resp['choices'][0]['message'].get('content') or '',
                               usage=resp.get('usage'), timings=resp.get('timings'),
                               finish_reason=resp['choices'][0].get('finish_reason'))
                except urllib.error.HTTPError as e:
                    res.update(http_status=e.code, http_body=e.read().decode(errors='replace')[:2000])
                res['seconds'] = round(time.monotonic() - t1, 1)
                if res.get('http_status') == 200:
                    c = res['content'].strip()
                    if label == 'A': res['passed'] = c == '42'
                    elif label == 'B': res['passed'] = c == 'BernsteinFalke739' and (res.get('usage') or {}).get('prompt_tokens', 0) >= 200
                    else: res['passed'] = None; res['assessment'] = 'fachlich pruefen: x >= 0 statt > 0; Division durch null'
                else:
                    res['passed'] = False
                state['tests'][label] = res
                print(f'  {label}: HTTP {res.get("http_status")} | {res.get("seconds")} s | '
                      + repr((res.get('content') or res.get('http_body') or '')[:300]), flush=True)
                if res['passed'] is False:
                    break
        else:
            print('Sende Anfrage A ...', flush=True)
            state['requests_sent'] = 1; t1 = time.monotonic()
            try:
                resp = request('/v1/chat/completions', PAYLOAD, timeout=600)
                (run / 'response.json').write_text(json.dumps(resp, ensure_ascii=False, indent=1))
                state['http_status'] = 200
                state['content'] = resp['choices'][0]['message'].get('content')
            except urllib.error.HTTPError as e:
                state['http_status'] = e.code
                state['http_body'] = e.read().decode(errors='replace')[:2000]
            state['request_seconds'] = round(time.monotonic() - t1, 1)
    except Exception as exc:
        state['error'] = f'{type(exc).__name__}: {exc}'
    finally:
        if proc and proc.poll() is None:
            proc.send_signal(signal.SIGTERM)
            try: proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(timeout=10)
        if proc:
            state['own_process_exit_code'] = proc.returncode
        log.close()
        text = (run / 'engine.log').read_text(errors='replace')
        state['geometry_error_in_log'] = ERR in text
        state['reproduced'] = state['geometry_error_in_log']
        if which in FIXED:
            t = state.get('tests', {})
            ok = [k for k, v in t.items() if v.get('passed')]
            if not state['geometry_error_in_log'] and t.get('A', {}).get('passed') and t.get('B', {}).get('passed') \
                    and t.get('C', {}).get('http_status') == 200:
                state['outcome'] = 'LAUFFAEHIG: A und B bestanden, C beantwortet (fachlich pruefen)'
            else:
                state['outcome'] = ('GEOMETRIEFEHLER TROTZ KORREKTUR' if state['geometry_error_in_log'] else
                                    'NICHT BESTANDEN: ' + (state.get('error') or f'bestanden {ok} von {list(t)}'))
        elif state['reproduced']:
            state['outcome'] = 'GEOMETRIEFEHLER REPRODUZIERT'
        elif state.get('content') is not None:
            state['outcome'] = 'KEIN FEHLER, Antwort: ' + repr(state['content'])
        else:
            state['outcome'] = 'ANDERES VERHALTEN: ' + state.get('error', f"HTTP {state.get('http_status')}")
        if which in ('diagnostic', 'fixed-diag'):
            state['diag'] = analyse_diag(text)
        m = re.findall(r'PGRN cache = ([\d.]+) MiB.*?hits = (\d+), misses = (\d+) \(([\d.]+)%\)', text)
        if m:
            state['pgrn_cache_last'] = {'cache_mib': float(m[-1][0]), 'hits': int(m[-1][1]), 'misses': int(m[-1][2]),
                                        'hit_percent': float(m[-1][3])}
        m = re.findall(r'PGRN stage = ([\d.]+) ms \(fetch ([\d.]+) ms, upload ([\d.]+) ms\)', text)
        if m:
            state['pgrn_stage_ms_last'] = {'stage': float(m[-1][0]), 'fetch': float(m[-1][1]), 'upload': float(m[-1][2])}
        for pat in ('PGRN staging failed', 'failed to decode', 'Compute error', 'GGML_ASSERT', 'error:'):
            n = text.count(pat)
            if n: state.setdefault('log_errors', {})[pat] = n
        ports_after = listeners()
        state['port_8083_free_after'] = PORT not in ports_after
        state['lab_ports_after'] = [p for p in LAB_PORTS if p in ports_after]
        state['lab_ports_unchanged'] = state['lab_ports_after'] == checks['lab_ports_before']
        state['finished_at'] = now()
        (run / 'result.json').write_text(json.dumps(state, ensure_ascii=False, indent=1))
        print('\n==', state['outcome'])
        if which in FIXED:
            for k, v in state.get('tests', {}).items():
                t = v.get('timings') or {}
                print(f"  {k}: prefill {t.get('prompt_per_second', 0):.1f} tok/s, generieren {t.get('predicted_per_second', 0):.2f} tok/s")
            if state.get('pgrn_cache_last'):
                print('  PGRN-Cache am Ende:', state['pgrn_cache_last'], '| Staging kumuliert:', state.get('pgrn_stage_ms_last'))
        if state.get('log_errors'):
            print('Fehlermarken im Log:', state['log_errors'])
        if which in ('diagnostic', 'fixed-diag') and state.get('diag'):
            d = state['diag']
            print('DIAG-Zeilen:', d['diag_lines'])
            if d.get('failing_candidate'):
                print('Letzter Callback vor Fehler:', json.dumps(d['failing_candidate'], ensure_ascii=False))
                print('Verletzte Guard-Bedingungen:', d.get('failing_violated'))
        print('Port 8083 frei danach:', state['port_8083_free_after'], '| Labor-Ports unveraendert:',
              state['lab_ports_unchanged'])
        print('Ergebnis:', run / 'result.json')


if __name__ == '__main__':
    main()
