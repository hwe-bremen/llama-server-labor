#!/usr/bin/env python3
"""One authorized isolated smoke test. No download, unload, conversion or restart."""
import concurrent.futures
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import socket
import subprocess
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
ENGINE_SHA = '7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e'


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def capture(argv):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=15)
    return {'argv':argv, 'exit_code':p.returncode, 'stdout':p.stdout, 'stderr':p.stderr}


def listeners():
    d = capture(['/usr/sbin/lsof','-nP','-iTCP','-sTCP:LISTEN'])
    if d['exit_code'] not in (0,1):
        raise RuntimeError('Listener nicht zuverlässig lesbar')
    return d


def memory():
    vm = capture(['/usr/bin/vm_stat'])
    pressure = capture(['/usr/bin/memory_pressure','-Q'])
    match = re.search(r'free percentage:\s+(\d+)', pressure['stdout'])
    pages = re.search(r'page size of (\d+)', vm['stdout'])
    if not match or not pages:
        raise RuntimeError('Speicherzustand nicht ausreichend prüfbar')
    counts = {k:int(v) for k,v in re.findall(r'^([A-Za-z -]+):\s+(\d+)',vm['stdout'],re.M)}
    return {'at':now(),'vm_stat':vm,'pressure':pressure,'free_percentage':int(match[1]),
            'page_size':int(pages[1]),'counts':counts}


def request(path, payload=None, timeout=5):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request('http://127.0.0.1:8083'+path, data=data,
                                 headers={'Content-Type':'application/json'})
    with HTTP.open(req, timeout=timeout) as r:
        body = r.read(4*1024*1024+1)
        if len(body)>4*1024*1024:
            raise RuntimeError('Unerwartet große API-Antwort')
        return json.loads(body)


def effective(log):
    found = {}
    for k in ('n_ctx','n_batch','n_ubatch','n_seq_max'):
        vals = re.findall(r'\b'+k+r'\s*=\s*(\d+)',log)
        if vals: found[k] = int(vals[-1])
    if found != {'n_ctx':4096,'n_batch':25,'n_ubatch':25,'n_seq_max':1}:
        raise RuntimeError('Effektive Parameter fehlen/weichen ab: '+str(found))
    m = re.search(r'PGRN admitted cache = ([\d.]+) MiB, scratch = ([\d.]+) MiB, headroom = ([\d.]+) MiB',log)
    # v0.3.4 runtime rounds its hard cache cap down to complete fixed slots.
    inventory=json.loads((HERE/'tensor_inventory_rechecked.json').read_text())
    slot_bytes=max(r['record_bytes'] for r in inventory['analysis']['pgrn']['records'])
    expected_cache_bytes=(12*1024**3//slot_bytes)*slot_bytes
    expected_cache_mib=expected_cache_bytes/1024**2
    # Admission diagnostics print two decimal places; allow only that rounding.
    if not m or abs(float(m[1])-expected_cache_mib)>0.006 or abs(float(m[3])-8192)>0.006:
        raise RuntimeError('PGRN-Cache/Headroom nicht wie vorbereitet bestätigt')
    if 'qwen3next' not in log:
        raise RuntimeError('qwen3next nicht im Startlog bestätigt')
    return {'context':found,'cache_MiB':float(m[1]),'expected_cache_bytes':expected_cache_bytes,
            'slot_bytes':slot_bytes,'scratch_MiB':float(m[2]),
            'headroom_MiB':float(m[3]),'source_identity':'Successful native load implies mandatory GGUF SHA check in unchanged inspected loader'}


def main():
    run = HERE/'first_inference_runs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True,exist_ok=False)
    state = {'status':'BLOCKED','started_at':now(),'run_directory':str(run),
             'server_started':False,'requests_sent':0,'existing_processes_changed':False}
    process = None
    log = None
    pool = None
    started = time.monotonic()
    last_sample = 0
    last_swapouts = None

    def sample():
        nonlocal last_sample, last_swapouts
        m = memory()
        if process and process.poll() is None:
            m['own_process_rss'] = capture(['/bin/ps','-p',str(process.pid),'-o','pid=,rss=,etime=,command='])
        with (run/'memory.jsonl').open('a') as f: f.write(json.dumps(m)+'\n')
        last_sample = time.monotonic()
        swaps = m['counts'].get('Swapouts')
        delta = swaps-last_swapouts if swaps is not None and last_swapouts is not None else 0
        last_swapouts = swaps
        if m['free_percentage']<15 or (m['free_percentage']<25 and delta*m['page_size']>256*1024**2):
            raise RuntimeError('Kritisches Speicherbudget/Swapaktivität; eigener Test wird abgebrochen')
        return m

    def guard():
        if time.monotonic()-started>3600: raise TimeoutError('Gesamttest maximal 60 Minuten')
        if process.poll() is not None: raise RuntimeError('Eigener Server beendet: '+str(process.returncode))
        if time.monotonic()-last_sample>10: sample()
        text = (run/'engine.log').read_text(errors='replace')
        for marker in ('PGRN model identity does not match','PGRN artifact header, directory, or CRC validation failed',
                       'PGRN live headroom check failed','GGML_ASSERT','MTLCommandBufferError','PGRN stage failed',
                       'failed to stage','too many unique experts'):
            if marker.lower() in text.lower(): raise RuntimeError('Enginefehler: '+marker)

    try:
        before = listeners(); write(run/'listeners_before.json',before)
        if re.search(r':8083 \(LISTEN\)', before['stdout']): raise RuntimeError('Port 8083 belegt')
        m = sample(); state['memory_before']=m
        if 48*m['free_percentage']/100<23:
            raise RuntimeError('Kein plausibles RAM-Budget: mindestens 23 GiB Planungsspielraum erforderlich')
        if not Path('/Volumes/Extern M4 Speicher').is_mount(): raise RuntimeError('Externe SSD fehlt')
        records=[]
        for p in (HERE/'download_conversion_runs').glob('*/result.json'):
            d=json.loads(p.read_text())
            if d['status'].startswith('READY'): records.append((d['finished_at'],p,d))
        _, source, d = max(records)
        state['verification_record']=str(source)
        if not (d['gguf']['sha256_verified'] and d['pgrn']['all_record_crcs_verified']
                and d['pgrn']['source_sha256_verified'] and d['pgrn']['record_count']==24576):
            raise RuntimeError('Vollständiger Integritätsnachweis fehlt')
        verified_at = datetime.fromisoformat(d['finished_at']).timestamp()
        state['files']={}
        for key,size in (('gguf',48528320544),('pgrn',46909751296)):
            p=Path(d[key]['file']); s=p.stat()
            if p.is_symlink() or not p.is_file() or s.st_size!=size or max(s.st_mtime,s.st_ctime)>verified_at:
                raise RuntimeError('Datei seit Prüfung verändert oder ungültig: '+str(p))
            state['files'][key]={'path':str(p),'size':s.st_size,'verified_sha256':d[key]['sha256']}
        prepared=json.loads((HERE/'inference_parameters_prepared.json').read_text())
        argv=list(prepared['argv'])
        # Default verbosity 3 omits core parameter/admission diagnostics in this bundle.
        # Retain fail-closed parameter checks and request debug diagnostics explicitly.
        argv+=['--verbosity','5','--log-colors','off']
        engine=Path(argv[0])
        digest=hashlib.sha256(engine.read_bytes()).hexdigest(); state['engine_sha256']=digest
        if digest!=ENGINE_SHA: raise RuntimeError('Enginehash stimmt nicht')
        help_run=capture([str(engine),'--help']); write(run/'engine_help.json',help_run)
        if help_run['exit_code'] or any(flag not in help_run['stdout'] for flag in argv[1:] if flag.startswith('--')):
            raise RuntimeError('Vorbereitete CLI nicht bestätigt')
        state['argv']=argv
        # Check binding permission before allocating any model memory. No listener is started here.
        with socket.socket() as sock: sock.bind(('127.0.0.1',8083))
        state['phase']='startup'
        log=(run/'engine.log').open('x')
        env=os.environ.copy()
        env={k:v for k,v in env.items() if not k.startswith('LLAMA_ARG_')}
        state['environment_note']='Inherited LLAMA_ARG_* defaults excluded for this subprocess only'
        process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,cwd=HERE.parent,env=env)
        state.update(server_started=True,pid=process.pid,server_started_at=now())
        print('Eigener Testserver PID',process.pid,'— Start-/Hashprüfung läuft.',flush=True)
        start=time.monotonic(); last_print=0
        while True:
            guard()
            if time.monotonic()-start>1200: raise TimeoutError('Laden maximal 20 Minuten')
            try:
                ready=request('/health',timeout=2)
                if ready.get('status')=='ok': break
            except urllib.error.HTTPError as e:
                if e.code!=503: raise
            except urllib.error.URLError as e:
                if isinstance(e.reason,PermissionError): raise
            if time.monotonic()-last_print>20:
                print('Laden:',round(time.monotonic()-start),'Sekunden',flush=True);last_print=time.monotonic()
            time.sleep(2)
        state['load_seconds']=time.monotonic()-start
        state['effective_parameters']=effective((run/'engine.log').read_text(errors='replace'))
        state['phase']='inference'; state['tests']={}
        pool=concurrent.futures.ThreadPoolExecutor(max_workers=1)
        b='Lies die folgenden Zeilen. Antworte ausschließlich mit dem Wert hinter KENNWORT.\n'
        b+='\n'.join(f'Eintrag {i:03d}: Dies ist ein neutraler Eintrag für den Prefill-Test.' for i in range(1,41))
        b+='\nKENNWORT: BernsteinFalke739\nGib ausschließlich das Kennwort zurück.'
        prompts=[('A',32,'Antworte ausschließlich mit der Zahl: 17 + 25'),('B',64,b),
                 ('C',512,'Prüfe diese Python-Funktion. Spezifikation: Mittelwert ausschließlich strikt positiver Werte; falls keine existieren, None zurückgeben. Benenne beide Fehler und schlage eine Korrektur vor.\n```python\ndef mean_positive(values):\n    positives = [x for x in values if x >= 0]\n    return sum(positives) / len(positives)\n```')]
        write(run/'expected_results.json',{'A':'42','B':'BernsteinFalke739','B_prompt_tokens_minimum':200,
              'C':['Null fälschlich eingeschlossen','Division durch null bei leerer Auswahl']})
        for label,limit,prompt in prompts:
            guard()
            payload={'messages':[{'role':'user','content':prompt}],'max_tokens':limit,
                     'temperature':0,'seed':42,'stream':False}
            write(run/('request_'+label+'.json'),payload)
            print('Test',label,'läuft ...',flush=True)
            state['requests_sent']+=1; t=time.monotonic()
            future=pool.submit(request,'/v1/chat/completions',payload,600)
            while not future.done():
                guard()
                if time.monotonic()-t>600: raise TimeoutError('Anfrage maximal 10 Minuten')
                time.sleep(2)
            response=future.result(); write(run/('response_'+label+'.json'),response)
            content=response['choices'][0]['message'].get('content') or ''
            result={'seconds':time.monotonic()-t,'content':content,'usage':response.get('usage'),
                    'timings':response.get('timings'),'finish_reason':response['choices'][0].get('finish_reason')}
            if label=='A': result['passed']=content.strip()=='42'
            elif label=='B':
                result['passed']=content.strip()=='BernsteinFalke739' and response.get('usage',{}).get('prompt_tokens',0)>=200
            else:
                result['passed']=None
                result['assessment']='Vollständige Antwort gespeichert; fachliche Prüfung beider Befunde erforderlich'
            state['tests'][label]=result
            print('Test',label,':',content,flush=True)
            if result['passed'] is False: raise RuntimeError('Funktionstest '+label+' nicht bestanden; keine weiteren Anfragen')
        state['status']='PARTIAL'
        state['reason']='Inferenztests ausgeführt; Code-Review-Antwort C muss noch fachlich geprüft werden'
    except PermissionError as exc:
        state['status']='BLOCKED'; state['reason']='Ausführungsumgebung verweigert lokale Operation: '+str(exc)
    except KeyboardInterrupt:
        state['status']='PARTIAL' if state['requests_sent'] else 'BLOCKED'; state['reason']='Benutzerabbruch'
    except Exception as exc:
        state['status']='FAIL' if state['server_started'] else 'BLOCKED'
        state['reason']=type(exc).__name__+': '+str(exc)
    finally:
        if process:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=10)
            state['own_process_ended']=process.poll() is not None
            state['own_process_exit_code']=process.returncode
        if log: log.close()
        if pool: pool.shutdown(wait=True,cancel_futures=True)
        state['finished_at']=now()
        try:
            after=listeners(); write(run/'listeners_after.json',after)
            def lab(d):
                return sorted(x for x in d['stdout'].splitlines() if re.search(r':(?:8080|8091|8092|8093|8787|11434|64908) \(LISTEN\)',x))
            state['same_observed_lab_listeners']=lab(before)==lab(after)
            state['port_8083_free_after']=not bool(re.search(r':8083 \(LISTEN\)',after['stdout']))
        except Exception as exc: state['final_observation_error']=str(exc)
        write(run/'result.json',state)
        body='# Qwen3-Coder-Next: isolierter Inferenztest\n\n## Status: '+state['status']+'\n\n'
        body+='[BELEGT] '+state.get('reason','')+'\n\n'
        body+='## Vorprüfung und Modellidentität\n\nDateigrößen, Prüfprotokoll, Enginehash und Speichermessungen stehen im folgenden Ergebnis. '
        body+='Historische SHA-/CRC-Nachweise sind [DOKUMENTIERT]; aktuelle Größen und Änderungszeiten [BELEGT].\n\n'
        body+='## Start und effektive Parameter\n\n'
        if state.get('argv'): body+='```sh\n'+shlex.join(state['argv'])+'\n```\n\n'
        body+='Effektive Werte gelten ausschließlich bei vorhandenem effective_parameters-Nachweis. '
        body+='Kein erfolgreicher Start wird aus vorbereiteten Argumenten abgeleitet.\n\n'
        body+='## Speicherbeobachtung\n\nRohmessungen: memory.jsonl. Prozentwerte sind keine exakte Allokationsgarantie; RSS erfasst nicht den gesamten Unified-Memory-Bedarf. '
        body+='Swapouts sind kumulativ; nur Differenzen beschreiben Änderungen. Laufzeitgrenzen: Laden 20 Minuten, Anfrage 10 Minuten, insgesamt 60 Minuten.\n\n'
        body+='## Funktionstests\n\nA: 42; B: Kennwort und mindestens 200 tatsächliche Prompttokens; C: Null ausgeschlossen und leere Auswahl behandelt. '
        body+='Request-/Response-Dateien nur für tatsächlich vorbereitete bzw. gesendete Anfragen. Kein umfassender Nachweis der Reviewqualität.\n\n'
        body+='## Offene Fragen und Abschluss\n\n[HYPOTHESE] Nicht getestete Metal-/PGRN-Pfade bleiben offen. '
        body+='Ausschließlich die eigene Prozessreferenz wird beendet. Kein Download, keine Konvertierung, keine Modellentladung und keine Änderung bestehender Dienste. '
        body+='Listenervergleich ist keine umfassende Funktionsprüfung. Ein BLOCKED erfordert einen erneuten bewussten Aufruf im normalen Terminal.\n\n'
        body+='## Vollständiges Ergebnis\n\n```json\n'+json.dumps(state,ensure_ascii=False,indent=2)+'\n```\n'
        with (run/'FIRST_INFERENCE_REPORT.md').open('x') as f:f.write(body)
        print('Bewertung:',state['status'],flush=True)
        print('Bericht:',run/'FIRST_INFERENCE_REPORT.md',flush=True)
    return 0 if state['status']=='PASS' else 2


if __name__=='__main__':
    with (HERE/'first_inference.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        raise SystemExit(main())
