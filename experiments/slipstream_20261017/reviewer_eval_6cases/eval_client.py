"""Six frozen text-only reviews. Model output is saved, NEVER executed."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time
import urllib.request

HERE=Path(__file__).resolve().parent
HTTP=urllib.request.build_opener(urllib.request.ProxyHandler({}))


def verify_freeze():
    frozen=json.loads((HERE/'FROZEN.json').read_text())
    for relative,expected in frozen['files'].items():
        if hashlib.sha256((HERE/relative).read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Eingefrorene Datei verändert: '+relative)
    return frozen


def post(path,payload,timeout=15):
    request=urllib.request.Request('http://127.0.0.1:8083'+path,data=json.dumps(payload).encode(),
                                   headers={'Content-Type':'application/json'})
    with HTTP.open(request,timeout=timeout) as response:
        return json.loads(response.read(2**20))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();verify_freeze()
    settings=json.loads((HERE/'settings.json').read_text())
    if args.output.exists():raise RuntimeError('Ergebnisdatei existiert schon')
    root=args.output.parent
    all_records=[]
    for case in settings['order']:
        messages=json.loads((HERE/'prompts'/f'{case}.json').read_text())['messages']
        record={'case':case,'settings':settings,'fresh_conversation':True,'done':False,
                'complete':False,'request':None,'events':[],'first_visible_token_s':None}
        try:
            # Apply the actual installed model template and count tokens, not characters.
            rendered=post('/apply-template',{'messages':messages,
                           'chat_template_kwargs':{'enable_thinking':False}})
            if not isinstance(rendered.get('prompt'),str):raise RuntimeError('Chattemplate nicht prüfbar')
            tokenized=post('/tokenize',{'content':rendered['prompt'],'add_special':True,'parse_special':True})
            record['template_prompt_tokens']=len(tokenized['tokens'])
            record['context_margin_tokens']=128
            if record['template_prompt_tokens']+settings['max_output_tokens']+128>settings['context']:
                raise RuntimeError('Vollständiger Prompt plus Ausgabelimit passt nicht in Kontext')
            payload={'model':'qwen-stream-reference','messages':messages,'temperature':0,'seed':42,
                     'max_tokens':settings['max_output_tokens'],'stream':True,'cache_prompt':False,
                     'chat_template_kwargs':{'enable_thinking':False},'stream_options':{'include_usage':True}}
            record['request']=payload
            (root/(case+'-request.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
            print(case,'Start;',record['template_prompt_tokens'],'Prompttokens; Limit1024; Thinking aus.',flush=True)
            epoch=time.time();started=time.monotonic();last_notice=started
            record['start_epoch']=epoch
            req=urllib.request.Request('http://127.0.0.1:8083/v1/chat/completions',
                 data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
            with (root/(case+'-stream.jsonl')).open('w') as raw, HTTP.open(req,timeout=600) as response:
                for line in response:
                    if time.monotonic()-started>settings['per_case_timeout_s']:
                        raise TimeoutError('Fall überschreitet600Sekunden')
                    if not line.startswith(b'data:'):continue
                    body=line[5:].strip()
                    if body==b'[DONE]':record['done']=True;break
                    if not body:continue
                    event=json.loads(body)
                    raw.write(json.dumps({'elapsed_s':time.monotonic()-started,'event':event},ensure_ascii=False)+'\n');raw.flush()
                    if 'error' in event:raise RuntimeError(str(event['error']))
                    record['events'].append(event)
                    if record['first_visible_token_s'] is None and any(
                        any(choice.get('delta',{}).get(k) for k in ('content','reasoning_content','reasoning'))
                        for choice in event.get('choices',[])):
                        record['first_visible_token_s']=time.monotonic()-started
                    if time.monotonic()-last_notice>=30:
                        print(case,'läuft seit',round(time.monotonic()-started),'s',flush=True);last_notice=time.monotonic()
            record['wall_s']=time.monotonic()-started
            record['answer']=''.join(choice.get('delta',{}).get('content') or ''
                for e in record['events'] for choice in e.get('choices',[]))
            record['reasoning']=''.join(choice.get('delta',{}).get('reasoning_content') or
                choice.get('delta',{}).get('reasoning') or '' for e in record['events'] for choice in e.get('choices',[]))
            record['finish_reasons']=[choice['finish_reason'] for e in record['events']
                for choice in e.get('choices',[]) if choice.get('finish_reason')]
            record['timings']=next((e['timings'] for e in reversed(record['events']) if e.get('timings')),None)
            record['usage']=next((e['usage'] for e in reversed(record['events']) if e.get('usage')),None)
            record['complete']=record['done'] and bool(record['answer'].strip()) and record['finish_reasons']==['stop']
            record['truncated']= 'length' in record['finish_reasons']
            record['at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            (root/(case+'-answer.md')).write_text(record['answer']+'\n')
            print(case,'vollständig' if record['complete'] else 'UNVOLLSTÄNDIG',
                  'TTFT',record['first_visible_token_s'],'Gesamt',record['wall_s'],
                  'Finish',record['finish_reasons'],flush=True)
        except Exception as exc:
            record['error']=str(exc)
            print(case,'UNVOLLSTÄNDIG:',exc,flush=True)
        all_records.append(record)
        args.output.write_text(json.dumps(all_records,ensure_ascii=False,indent=2)+'\n')
        # A local context/template failure must not trigger six misleading failures.
        if record.get('error') and not record.get('request'):
            raise RuntimeError('Vorprüfung fehlgeschlagen, keine weiteren Fallanfragen')
    lines=['# Durchführung der sechs Reviewer-Fälle','',
           'Fachliche Bewertung anhand vorab eingefrorener Rubrik noch ausstehend. Keine automatische Schlüsselwortbenotung.','',
           '| Fall | Vollständig | TTFT s | Gesamtdauer s | Finish |','|---|---|---:|---:|---|']
    for r in all_records:
        lines.append(f"| {r['case']} | {r['complete']} | {r.get('first_visible_token_s')} | {r.get('wall_s')} | {r.get('finish_reasons',r.get('error'))} |")
    lines += ['', 'Rohantworten niemals als Befehle ausgeführt. Keine Aussage über allgemeine Qualität oder Haiku.']
    (root/'DURCHFUEHRUNG.md').write_text('\n'.join(lines)+'\n')
    if len(all_records)!=6 or not all(r['complete'] for r in all_records):
        raise RuntimeError('Mindestens eine Review-Antwort unvollständig; Rohdaten bleiben erhalten')


if __name__=='__main__':main()
