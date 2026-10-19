#!/usr/bin/env python3
"""Later authorized inference only: fixed prompts, SSE TTFT, raw response timings.
Does not start/stop a server or alter any model. Run only after explicit model-start approval.
"""
import argparse
import datetime
import json
from pathlib import Path
import time
import urllib.request

PROMPTS = [
    ('Review this Python function for correctness. Explain one problem and a correction.\n'
     'def mean(xs):\n    return sum(xs) / len(xs)\n', 64),
    ('Review this Python cache for concurrency and correctness. Explain concrete risks.\n'
     'cache = {}\ndef get_value(key, load):\n'
     '    if key not in cache:\n        cache[key] = load(key)\n'
     '    return cache[key]\n', 128),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; use a new run directory/name')
    records = []
    for prompt, limit in PROMPTS:
        payload = {'model': 'qwen-stream-reference', 'messages': [{'role': 'user', 'content': prompt}],
                   'temperature': 0, 'seed': 42, 'max_tokens': limit, 'stream': True,
                   'cache_prompt': False, 'chat_template_kwargs': {'enable_thinking': True},
                   'stream_options': {'include_usage': True}}
        started = time.monotonic()
        first = None
        events = []
        done = False
        request = urllib.request.Request('http://127.0.0.1:8083/v1/chat/completions',
                    data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=1800) as response:
            for raw in response:
                if not raw.startswith(b'data:'):
                    continue
                body = raw[5:].strip()
                if body == b'[DONE]':
                    done = True
                    break
                if not body:
                    continue
                event = json.loads(body)
                if 'error' in event:
                    raise RuntimeError(str(event['error']))
                events.append(event)
                for choice in event.get('choices', []):
                    delta = choice.get('delta', {})
                    if first is None and any(delta.get(key) for key in ('content', 'reasoning_content', 'reasoning')):
                        first = time.monotonic() - started
        records.append({'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'request': payload, 'first_visible_token_s': first,
                        'wall_s': time.monotonic() - started, 'done': done, 'events': events})
        args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
        print('limit', limit, 'TTFT', first, 'wall', records[-1]['wall_s'], 'DONE', done, flush=True)
        if not done or first is None:
            raise RuntimeError('Incomplete SSE response; not a passing measurement')


if __name__ == '__main__':
    main()
