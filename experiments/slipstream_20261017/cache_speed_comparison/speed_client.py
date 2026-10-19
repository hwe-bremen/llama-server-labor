"""Three bounded identical requests. Store text, never execute it."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import threading
import time
import urllib.request

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'qwen_reference'))
from disk_counters import snapshot, delta
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
CACHE_RE = re.compile(r'PGRN cache = ([\d.]+) MiB, high-water = ([\d.]+) MiB, hits = (\d+), misses = (\d+)')


def verify():
    frozen = json.loads((HERE/'FROZEN.json').read_text())
    for p, h in frozen['files'].items():
        if hashlib.sha256((HERE/p).read_bytes()).hexdigest() != h:
            raise RuntimeError('Frozen input modified: '+p)
    return frozen


def post(path, data):
    request = urllib.request.Request('http://127.0.0.1:8083'+path, data=json.dumps(data).encode(),
                                     headers={'Content-Type':'application/json'})
    with HTTP.open(request, timeout=30) as r:
        raw=r.read(2**20+1)
        if len(raw)>2**20:
            raise RuntimeError('Unexpected preflight size')
        return json.loads(raw)


def io_sample():
    try:
        return {'ok':True, 'sample':snapshot()}
    except Exception as e:
        return {'ok':False, 'error':str(e)}


def cache_rows(root):
    text=(root/'engine.log').read_text(errors='replace')
    return [{'cache_mib':float(c), 'highwater_mib':float(w), 'hits':int(h), 'misses':int(m)}
            for c,w,h,m in CACHE_RE.findall(text)]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verify();root=args.output.parent
    if args.output.exists():
        raise RuntimeError('Refusing to overwrite responses')
    settings=json.loads((HERE/'settings.json').read_text())
    messages=json.loads((HERE/'prompt.json').read_text())['messages']
    rendered=post('/apply-template',{'messages':messages,'chat_template_kwargs':{'enable_thinking':False}})
    tokens=post('/tokenize',{'content':rendered['prompt'],'add_special':True,'parse_special':True})['tokens']
    if len(tokens)+128+128>settings['context']:
        raise RuntimeError('Prompt does not fit')
    records=[]
    for index in range(1,4):
        payload={'model':'qwen-stream-reference','messages':messages,'max_tokens':128,
                 'temperature':0,'seed':42,'cache_prompt':False,
                 'chat_template_kwargs':{'enable_thinking':False},'stream':True,
                 'stream_options':{'include_usage':True}}
        (root/f'request-{index}.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
        record={'index':index,'prompt_tokens_preflight':len(tokens),'answer':'','reasoning':'',
                'events':[],'done':False,'finish_reasons':[],'bounded_request_pass':False,
                'first_content_s':None,'error':None,'io_before':io_sample(),
                'cache_before':cache_rows(root)}
        started=time.monotonic();record['start_epoch']=time.time()
        stop=threading.Event()
        def notice():
            while not stop.wait(30):
                print('Anfrage',index,'aktiv seit',round(time.monotonic()-started),'s',flush=True)
        thread=threading.Thread(target=notice,daemon=True);thread.start()
        print('Anfrage',index,'/3; Prompt',len(tokens),'Tokens; Ausgabe128.',flush=True)
        try:
            req=urllib.request.Request('http://127.0.0.1:8083/v1/chat/completions',
                    data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with (root/f'stream-{index}.jsonl').open('x') as raw, HTTP.open(req,timeout=240) as response:
                for line in response:
                    elapsed=time.monotonic()-started
                    if elapsed>240:
                        raise TimeoutError('240s/request; no retry')
                    if not line.startswith(b'data:'):
                        continue
                    body=line[5:].strip()
                    if not body:
                        continue
                    if body==b'[DONE]':
                        record['done']=True
                        raw.write(json.dumps({'elapsed_s':elapsed,'done':True})+'\n')
                        break
                    event=json.loads(body)
                    raw.write(json.dumps({'elapsed_s':elapsed,'event':event},ensure_ascii=False)+'\n');raw.flush()
                    record['events'].append(event)
                    if 'error' in event:
                        raise RuntimeError(str(event['error']))
                    for c in event.get('choices',[]):
                        d=c.get('delta') or {}
                        if d.get('content'):
                            if record['first_content_s'] is None:
                                record['first_content_s']=elapsed
                            record['answer']+=d['content']
                        record['reasoning']+=d.get('reasoning_content') or d.get('reasoning') or ''
                        if c.get('finish_reason'):
                            record['finish_reasons'].append(c['finish_reason'])
        except (Exception,KeyboardInterrupt) as e:
            record['error']=str(e) or type(e).__name__
        finally:
            stop.set();thread.join(timeout=2)
            record['wall_s']=time.monotonic()-started
            record['end_epoch']=time.time()
            record['io_after']=io_sample()
            record['cache_after']=cache_rows(root)
            record['usage']=next((e['usage'] for e in reversed(record['events']) if e.get('usage')),None)
            record['timings']=next((e['timings'] for e in reversed(record['events']) if e.get('timings')),None)
            if record['io_before']['ok'] and record['io_after']['ok']:
                try:record['physical_io_delta']=delta(record['io_before']['sample'],record['io_after']['sample'])
                except Exception as e:record['physical_io_error']=str(e)
            record['bounded_request_pass']=bool(not record['error'] and record['done'] and record['answer'] and
                  record['finish_reasons'] in (['stop'],['length']) and record['timings'] and record['usage'])
            record['length_is_expected_workload_cap']='length' in record['finish_reasons']
            record['review_quality_not_evaluated']=True
            (root/f'answer-{index}.txt').write_text(record['answer'])
            (root/f'reasoning-{index}.txt').write_text(record['reasoning'])
            records.append(record)
            args.output.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
            print('Anfrage',index,'bounded-pass',record['bounded_request_pass'],
                  'TTFT',record['first_content_s'],'wall',record['wall_s'],
                  'native',record['timings'],'error',record['error'],flush=True)
        if not record['bounded_request_pass']:
            raise RuntimeError('Bounded request failed; no remaining requests or retry')


if __name__=='__main__':
    main()
