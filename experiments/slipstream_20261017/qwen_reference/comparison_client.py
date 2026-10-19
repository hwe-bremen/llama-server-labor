"""Identical existing prompts, both capped at 128 tokens; no engine lifecycle."""
import argparse
import datetime
import json
import time
import urllib.request
from request_stream import PROMPTS
from disk_counters import snapshot, delta


def maybe_snapshot():
    try:
        return {'ok': True, 'data': snapshot()}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    from pathlib import Path
    target = Path(args.output)
    if target.exists():
        raise RuntimeError('Ausgabedatei existiert bereits')
    records = []
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for index, (prompt, _) in enumerate(PROMPTS, 1):
        # Quiet baseline, then counters at the exact request boundary. No hashing here.
        idle_start = maybe_snapshot()
        time.sleep(3)
        before = maybe_snapshot()
        payload = {'model': 'qwen-stream-reference', 'messages': [{'role': 'user', 'content': prompt}],
                   'temperature': 0, 'seed': 42, 'max_tokens': 128, 'stream': True,
                   'cache_prompt': False, 'chat_template_kwargs': {'enable_thinking': True},
                   'stream_options': {'include_usage': True}}
        req = urllib.request.Request('http://127.0.0.1:8083/v1/chat/completions',
                  data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        epoch = time.time(); started = time.monotonic()
        first = None; events = []; done = False
        with opener.open(req, timeout=600) as response:
            for line in response:
                if not line.startswith(b'data:'):
                    continue
                body = line[5:].strip()
                if body == b'[DONE]':
                    done = True; break
                if not body:
                    continue
                e = json.loads(body)
                if 'error' in e:
                    raise RuntimeError(str(e['error']))
                events.append(e)
                if first is None and any(any(c.get('delta', {}).get(k) for k in
                    ('content', 'reasoning', 'reasoning_content')) for c in e.get('choices', [])):
                    first = time.monotonic() - started
        wall = time.monotonic() - started
        after = maybe_snapshot()
        record = {'prompt_index': index, 'request': payload, 'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'start_epoch': epoch, 'first_visible_token_s': first, 'wall_s': wall,
                  'done': done, 'events': events, 'io_idle_start': idle_start,
                  'io_before_request': before, 'io_after_request': after}
        if before['ok'] and after['ok']:
            record['physical_io_delta'] = delta(before['data'], after['data'])
        if idle_start['ok'] and before['ok']:
            record['idle_io_delta'] = delta(idle_start['data'], before['data'])
            record['idle_window_s'] = before['data']['end_epoch'] - idle_start['data']['end_epoch']
        records.append(record)
        target.write_text(json.dumps(records, indent=2) + '\n')
        print('Prompt', index, '128 Tokens: TTFT', first, 'Gesamt', wall, 'DONE', done, flush=True)
        if not done or first is None:
            raise RuntimeError('SSE nicht vollständig')


if __name__ == '__main__':
    main()
