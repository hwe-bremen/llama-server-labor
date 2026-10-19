#!/usr/bin/env python3
"""Compare using an already loaded Qwen on router8080; no server/model management."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import urllib.request

HERE = Path(__file__).resolve().parent
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
URL = 'http://127.0.0.1:8080'


def get_models():
    with HTTP.open(URL+'/v1/models', timeout=10) as response:
        return json.loads(response.read(2**20))


def swap():
    p = subprocess.run(['/usr/bin/vm_stat'], capture_output=True, text=True, timeout=10)
    m = re.search(r'^Swapouts:\s+(\d+)', p.stdout, re.M)
    return {'at': time.time(), 'swapouts': int(m.group(1)) if m else None,
            'vm_stat': p.stdout, 'error': p.stderr}


def state(model):
    s = model.get('status', {})
    return s.get('value') if isinstance(s, dict) else s


def main():
    frozen = json.loads((HERE/'FROZEN.json').read_text())
    for path, expected in frozen['files'].items():
        if hashlib.sha256((HERE/path).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Fixierter Kontext verändert: '+path)
    before = get_models()
    diagnostic = HERE/'logs/router-models-current.json'
    diagnostic.write_text(json.dumps(before, ensure_ascii=False, indent=2)+'\n')
    if '--inspect' in sys.argv:
        print('Nur lesende Routerdiagnose, kein Review und kein Modellstart.')
        print(json.dumps(before, ensure_ascii=False, indent=2))
        print('Gespeichert:', diagnostic)
        return 0
    loaded = [m for m in before.get('data', []) if state(m) == 'loaded']
    candidates = [m for m in loaded if 'qwen' in m.get('id', '').lower()]
    if len(candidates) != 1:
        observed = [{'id':m.get('id'), 'status':m.get('status', '<fehlt>')}
                    for m in before.get('data', [])]
        raise RuntimeError('Geladener Qwen durch diese API-Antwort nicht eindeutig belegt. '+
                           'Gemeldet: '+str(observed)+'. Rohantwort: '+str(diagnostic)+
                           '. Kein Modell automatisch laden.')
    model = candidates[0]
    args = model.get('status', {}).get('args', [])
    ctx = None
    for i, value in enumerate(args):
        if value in ('--ctx-size', '-c') and i+1 < len(args):
            ctx = int(args[i+1])
        elif value.startswith('--ctx-size='):
            ctx = int(value.split('=', 1)[1])
    if ctx is None:
        ctx = model.get('meta', {}).get('n_ctx')
    if not isinstance(ctx, int) or ctx < 16384:
        raise RuntimeError('Geladener Kontext>=16384 nicht belegt; gemeldet: '+str(ctx)+
                           '. Keine Anfrage und keine Konfigurationsänderung.')
    messages = json.loads((HERE/'prompt.json').read_text())['messages']
    payload = {'model': model['id'], 'messages': messages, 'max_tokens': 4096,
               'temperature': 0, 'seed': 42, 'stream': True, 'cache_prompt': False,
               'chat_template_kwargs': {'enable_thinking': False},
               'stream_options': {'include_usage': True}}
    root = HERE/'router_comparison'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    root.mkdir(parents=True, exist_ok=False)
    (root/'request.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n')
    record = {'model': model['id'], 'router_models_before': before, 'loaded_ctx': ctx,
              'same_frozen_messages': True, 'prompt_file_sha256': hashlib.sha256((HERE/'prompt.json').read_bytes()).hexdigest(),
              'engine_or_model_started_by_client': False, 'events': [], 'answer': '', 'reasoning': '',
              'done': False, 'complete': False, 'finish_reasons': [], 'error': None,
              'first_content_s': None, 'first_reasoning_s': None, 'swap_before': swap(),
              'comparison_limits': 'Different model/build/config possible. Existing server uses its own settings; request disables thinking where supported, no server flags changed.'}
    # Recheck loaded state immediately before POST. A concurrent external unload remains a race.
    now = get_models()
    if not any(m.get('id') == model['id'] and state(m) == 'loaded' for m in now.get('data', [])):
        raise RuntimeError('Qwen inzwischen entladen; keine Reviewanfrage')
    print('Verwende bereits geladen:', model['id'], '; Kontext', ctx, flush=True)
    print('Identischer Diff/Auftrag; 4096Ausgabetokens; Thinking=false; keine Serverstopps.', flush=True)
    print('Ergebnisse:', root, flush=True)
    stop = threading.Event()
    started = time.monotonic()
    def progress():
        while not stop.wait(30):
            print('Review aktiv,', round(time.monotonic()-started), 's; warte/verarbeite Stream.', flush=True)
    heartbeat = threading.Thread(target=progress, daemon=True)
    heartbeat.start()
    req = urllib.request.Request(URL+'/v1/chat/completions', data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    try:
        with (root/'stream.jsonl').open('x') as raw, HTTP.open(req, timeout=1800) as response:
            for line in response:
                elapsed = time.monotonic()-started
                if elapsed > 1800:
                    raise TimeoutError('Zeitlimit1800s; kein Retry')
                if not line.startswith(b'data:'):
                    continue
                body = line[5:].strip()
                if not body:
                    continue
                if body == b'[DONE]':
                    record['done'] = True
                    raw.write(json.dumps({'elapsed_s': elapsed, 'done': True})+'\n')
                    break
                event = json.loads(body)
                raw.write(json.dumps({'elapsed_s': elapsed, 'event': event}, ensure_ascii=False)+'\n')
                raw.flush()
                record['events'].append(event)
                if 'error' in event:
                    raise RuntimeError(str(event['error']))
                for c in event.get('choices', []):
                    delta = c.get('delta') or {}
                    for field, key in (('content', 'answer'), ('reasoning_content', 'reasoning'), ('reasoning', 'reasoning')):
                        text = delta.get(field) or ''
                        if text:
                            first = 'first_content_s' if key == 'answer' else 'first_reasoning_s'
                            if record[first] is None:
                                record[first] = elapsed
                            record[key] += text
                    if c.get('finish_reason'):
                        record['finish_reasons'].append(c['finish_reason'])
        record['complete'] = record['done'] and bool(record['answer'].strip()) and record['finish_reasons'] == ['stop']
    except (Exception, KeyboardInterrupt) as exc:
        record['error'] = str(exc) or type(exc).__name__
    finally:
        stop.set()
        heartbeat.join(timeout=2)
        record['wall_s'] = time.monotonic()-started
        record['swap_after'] = swap()
        b, a = record['swap_before']['swapouts'], record['swap_after']['swapouts']
        record['swapout_delta'] = a-b if a is not None and b is not None else None
        record['usage'] = next((e['usage'] for e in reversed(record['events']) if e.get('usage')), None)
        record['timings'] = next((e['timings'] for e in reversed(record['events']) if e.get('timings')), None)
        record['truncated'] = 'length' in record['finish_reasons']
        for name, key in (('answer.txt', 'answer'), ('reasoning.txt', 'reasoning')):
            (root/name).write_text(record[key])
            record[name+'_sha256'] = hashlib.sha256((root/name).read_bytes()).hexdigest()
        try:
            record['router_models_after'] = get_models()
        except Exception as exc:
            record['router_models_after_error'] = str(exc)
        (root/'response.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n')
        print('Ergebnis:', 'VOLLSTÄNDIG' if record['complete'] else 'UNVOLLSTÄNDIG',
              'Finish', record['finish_reasons'], 'Gesamt', round(record['wall_s'], 2),
              's; SwapoutsDelta', record['swapout_delta'], flush=True)
        print('Server bleibt unverändert laufen. Ergebnisse:', root, flush=True)
    return 0 if record['complete'] else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print('ABBRUCH:', exc, flush=True)
        raise SystemExit(1)
