"""One fresh, frozen real-code review. Save model text; never execute it."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time
import threading
import urllib.request

HERE = Path(__file__).resolve().parent
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def verify_frozen():
    frozen = json.loads((HERE / 'FROZEN.json').read_text())
    for relative, expected in frozen['files'].items():
        if hashlib.sha256((HERE / relative).read_bytes()).hexdigest() != expected:
            raise RuntimeError('Eingefrorene Datei verändert: ' + relative)
    return frozen


def post(path, payload):
    req = urllib.request.Request('http://127.0.0.1:8083' + path,
        data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with HTTP.open(req, timeout=30) as response:
        raw = response.read(2**20 + 1)
        if len(raw) > 2**20:
            raise RuntimeError('Vorprüfungsantwort unerwartet groß')
        return json.loads(raw)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Ergebnisdatei existiert bereits')
    frozen = verify_frozen()
    settings = json.loads((HERE / 'settings.json').read_text())
    messages = json.loads((HERE / 'prompt.json').read_text())['messages']
    root = args.output.parent
    record = {'complete': False, 'done': False, 'events': [], 'answer': '',
              'reasoning': '', 'settings': settings, 'frozen': frozen,
              'fresh_conversation': True, 'first_content_s': None,
              'first_reasoning_s': None, 'finish_reasons': [], 'truncated': False,
              'error': None}
    started = None
    heartbeat = None
    stop_progress = threading.Event()
    try:
        rendered = post('/apply-template', {'messages': messages,
                         'chat_template_kwargs': {'enable_thinking': False}})
        tokens = post('/tokenize', {'content': rendered['prompt'],
                      'add_special': True, 'parse_special': True})['tokens']
        record['template_prompt_tokens'] = len(tokens)
        if len(tokens) + settings['max_output_tokens'] + 128 > settings['context']:
            raise RuntimeError('Vollständiger Kontext plus4096Ausgabe passt nicht; kein Reviewrequest')
        payload = {'model': 'qwen-stream-reference', 'messages': messages,
                   'max_tokens': 4096, 'temperature': 0, 'seed': 42,
                   'chat_template_kwargs': {'enable_thinking': False},
                   'cache_prompt': False, 'stream': True,
                   'stream_options': {'include_usage': True}}
        (root / 'request.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
        record['request'] = payload
        print('Eine Diskussionsrunde; Prompttokens', len(tokens), '; Reserve4096; Thinking off; kein automatischer Retry.', flush=True)
        started = time.monotonic()
        record['start_epoch'] = time.time()
        record['started_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        req = urllib.request.Request('http://127.0.0.1:8083/v1/chat/completions',
             data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        last_notice = started
        def progress():
            while not stop_progress.wait(30):
                print('Diskussionslauf aktiv,', round(time.monotonic()-started), 's; Eingabe wird verarbeitet oder Antwort generiert.', flush=True)
        heartbeat = threading.Thread(target=progress, daemon=True)
        heartbeat.start()
        with (root / 'stream.jsonl').open('x') as raw, HTTP.open(req, timeout=settings['timeout_s']) as response:
            for line in response:
                elapsed = time.monotonic() - started
                if elapsed > settings['timeout_s']:
                    raise TimeoutError('Zeitlimit1800s; keine Wiederholung')
                if not line.startswith(b'data:'):
                    continue
                body = line[5:].strip()
                if not body:
                    continue
                if body == b'[DONE]':
                    record['done'] = True
                    raw.write(json.dumps({'elapsed_s': elapsed, 'done': True}) + '\n')
                    raw.flush()
                    break
                event = json.loads(body)
                raw.write(json.dumps({'elapsed_s': elapsed, 'event': event}, ensure_ascii=False) + '\n')
                raw.flush()
                record['events'].append(event)
                if 'error' in event:
                    raise RuntimeError(str(event['error']))
                for choice in event.get('choices', []):
                    delta = choice.get('delta') or {}
                    if delta.get('content'):
                        if record['first_content_s'] is None:
                            record['first_content_s'] = elapsed
                        record['answer'] += delta['content']
                    thought = delta.get('reasoning_content') or delta.get('reasoning') or ''
                    if thought:
                        if record['first_reasoning_s'] is None:
                            record['first_reasoning_s'] = elapsed
                        record['reasoning'] += thought
                    if choice.get('finish_reason'):
                        record['finish_reasons'].append(choice['finish_reason'])
                if elapsed - (last_notice - started) >= 30:
                    print('Review läuft seit', round(elapsed), 's', flush=True)
                    last_notice = time.monotonic()
        record['complete'] = record['done'] and bool(record['answer'].strip()) and record['finish_reasons'] == ['stop']
    except Exception as exc:
        record['error'] = str(exc)
    finally:
        stop_progress.set()
        if heartbeat is not None:
            heartbeat.join(timeout=2)
        record['wall_s'] = time.monotonic() - started if started else None
        record['truncated'] = 'length' in record['finish_reasons']
        record['timings'] = next((e['timings'] for e in reversed(record['events']) if e.get('timings')), None)
        record['usage'] = next((e['usage'] for e in reversed(record['events']) if e.get('usage')), None)
        record['reasoning_tokens_reported'] = ((record['usage'] or {}).get('completion_tokens_details') or {}).get('reasoning_tokens')
        record['reasoning_token_count_status'] = 'reported' if record['reasoning_tokens_reported'] is not None else 'not_reported'
        record['word_count_final'] = len(record['answer'].split())
        # Original strings: no trimming, reformatting or extra trailing newline.
        for name, text in (('answer.txt', record['answer']), ('reasoning.txt', record['reasoning'])):
            with (root / name).open('x') as f:
                f.write(text)
            record[name + '_sha256'] = hashlib.sha256((root / name).read_bytes()).hexdigest()
        args.output.write_text(json.dumps([record], ensure_ascii=False, indent=2) + '\n')
        print('Diskussion', 'vollständig' if record['complete'] else 'UNVOLLSTÄNDIG',
              'Finish', record['finish_reasons'], 'Gesamt', record['wall_s'],
              'Wörter', record['word_count_final'], 'Fehler', record['error'], flush=True)
    if not record['complete']:
        raise RuntimeError('Review nicht vollständig; Originalantwort erhalten; kein automatischer Retry')


if __name__ == '__main__':
    main()
