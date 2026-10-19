#!/usr/bin/env python3
"""Prepared diagnosis; run only in a host session permitting localhost and ps.

Reuses the prior runner without any router unload or lab configuration change.
API success records transport only; answers still require a substantive review.
"""
import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
sys.path.insert(0, str(EXP / 'real_review_model_tags_12gib'))
import isolated_runner as runner

CODE = '''def clamp(value: int, lower: int, upper: int) -> int:
    if lower > upper:
        raise ValueError("lower must not exceed upper")
    return min(max(value, lower), upper)
'''
MESSAGES = [
    {'role': 'system', 'content': 'Prüfe den vollständig gegebenen Python-Code ausschließlich gegen die angegebene Spezifikation. Erfinde keine zusätzlichen Anforderungen. Ein fehlerfreies Ergebnis ist ausdrücklich zulässig. Antworte knapp mit einem abschließenden Urteil und einer kurzen Begründung. Suche nicht weiter, wenn kein Fehler vorliegt.'},
    {'role': 'user', 'content': 'Spezifikation: Für Python-int-Eingaben liefert clamp den Wert begrenzt auf das inklusive Intervall [lower, upper]. Bei lower > upper muss ValueError ausgelöst werden. Keine Typprüfung, keine anderen Eingabetypen und keine Nebenläufigkeit gefordert.\n\n```python\n' + CODE + '```\nPrüfe auf Verletzungen dieser Spezifikation. Wenn keine vorliegen, schreibe ausdrücklich „Keine Beanstandung“.'},
]


def payload(temperature):
    return {'model': 'qwen-stream-reference', 'messages': MESSAGES,
            'temperature': temperature, 'seed': 42, 'max_tokens': 512,
            'cache_prompt': False, 'chat_template_kwargs': {'enable_thinking': False},
            'stream': True, 'stream_options': {'include_usage': True}}


def verify_sample():
    scope = {}
    exec(CODE, scope)
    clamp = scope['clamp']
    checked = 0
    for lower in range(-5, 6):
        for upper in range(-5, 6):
            for value in range(-10, 11):
                checked += 1
                if lower > upper:
                    try:
                        clamp(value, lower, upper)
                    except ValueError:
                        continue
                    raise AssertionError('Missing ValueError')
                expected = lower if value < lower else upper if value > upper else value
                assert clamp(value, lower, upper) == expected
    return {'verified_cases': checked, 'argument': 'For lower <= upper: max chooses at least lower; min caps at upper. The guard rejects reversed bounds.'}


def client(output):
    run = output.parent
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    results = []
    for label, temperature in [('A', 0), ('B', 0.6)]:
        request = payload(temperature)
        (run / f'{label}-request.json').write_text(json.dumps(request, ensure_ascii=False, indent=2) + '\n')
        item = {'label': label, 'temperature': temperature, 'answer': '', 'reasoning': '',
                'finish_reasons': [], 'usage': None, 'done': False}
        results.append(item)
        started = time.monotonic()
        req = urllib.request.Request('http://127.0.0.1:8083/v1/chat/completions',
                                     data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'})
        try:
            with opener.open(req, timeout=600) as response, (run / f'{label}-stream.sse').open('wb') as log:
                item['http_status'] = response.status
                item['http_headers'] = dict(response.headers)
                for line in response:
                    log.write(line); log.flush()
                    if not line.startswith(b'data: '):
                        continue
                    raw = line[6:].strip()
                    if raw == b'[DONE]':
                        item['done'] = True
                        break
                    event = json.loads(raw)
                    if event.get('error'):
                        raise RuntimeError(str(event['error']))
                    if event.get('usage') is not None:
                        item['usage'] = event['usage']
                    if 'timings' in event:
                        item['timings'] = event['timings']
                    for choice in event.get('choices', []):
                        delta = choice.get('delta', {})
                        item['answer'] += delta.get('content') or ''
                        item['reasoning'] += delta.get('reasoning_content') or ''
                        if choice.get('finish_reason') is not None:
                            item['finish_reasons'].append(choice['finish_reason'])
            if not item['done'] or not item['finish_reasons']:
                raise RuntimeError('Incomplete stream')
        except Exception as exc:
            item['error'] = str(exc)
            raise
        finally:
            item['elapsed_s'] = time.monotonic() - started
            (run / f'{label}-answer.txt').write_text(item['answer'])
            output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
        print(label, item['finish_reasons'], item['usage'], round(item['elapsed_s'], 2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        client(args.output)
        return 0
    # Denied checks fail before starting any model. Never stop existing services.
    with socket.socket() as check:
        check.bind(('127.0.0.1', 8083))
    ps = subprocess.run(['/bin/ps', '-axo', 'pid=,command='], check=True,
                        capture_output=True, text=True).stdout
    pattern = re.compile(r'(?:^|/)llama-server(?:\s|$)|\bollama\s+runner\b|\bmlx_lm\.(?:server|generate)\b|\bvllm\.entrypoints\b|\bomlx\s+serve\b')
    if any(pattern.search(line) for line in ps.splitlines()):
        raise RuntimeError('Andere Modellinstanz sichtbar; keine Änderung')
    if any(e['listeners'] for e in runner.stopped_lab_snapshot().values()) or runner.llama_pids():
        raise RuntimeError('Labor/Modell läuft; keine automatische Änderung')
    if hashlib.sha256(runner.ENGINE.read_bytes()).hexdigest() != '7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e':
        raise RuntimeError('Engine differs from baseline')
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run = HERE / 'runs' / stamp
    with (EXP / 'qwen_reference/logs/internal-test.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        code = runner.main(lab_stopped=True, run_dir=run, client_script=Path(__file__),
                           load_timeout=420, context_size=16384, client_timeout=1230,
                           no_context_shift=True, client_progress=True, cache_gib=12)
    (run / 'sample-verification.json').write_text(json.dumps(verify_sample(), indent=2) + '\n')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
