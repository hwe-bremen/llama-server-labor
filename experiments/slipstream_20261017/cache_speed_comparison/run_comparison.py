#!/usr/bin/env python3
"""Two fresh processes only: 2 vs12GiB PGRN cache. No service management."""
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import re
import socket
import statistics
import sys

HERE=Path(__file__).resolve().parent
import isolated_runner as runner
from speed_client import verify, CACHE_RE
sys.path.insert(0,str(HERE.parent/'qwen_reference'))
from disk_counters import snapshot


def quiet():
    if any(e['listeners'] for e in runner.stopped_lab_snapshot().values()) or runner.listeners(8083) or runner.llama_pids():
        raise RuntimeError('Labor/andere llama-Instanz läuft; kein automatisches Stoppen')
    processes=runner.capture(['/bin/ps','-axo','pid=,command='])
    if processes['returncode']:
        raise RuntimeError('Modellprozesse nicht sicher prüfbar')
    pattern=re.compile(r'(?:^|/)llama-server(?:\s|$)|\bollama\s+runner\b|\bmlx_lm\.(?:server|generate)\b|\bvllm\.entrypoints\b|\bomlx\s+serve\b')
    found=[line for line in processes['stdout'].splitlines() if pattern.search(line)]
    if found:
        raise RuntimeError('Andere Modellinstanz: '+str(found))


def stat(values):
    values=[x for x in values if isinstance(x,(int,float))]
    return {'median':statistics.median(values),'min':min(values),'max':max(values),'n':len(values)} if values else None


def summarize(parent,reports):
    summary={'order':['A2GiB','B12GiB'],'full_pair':len(reports)==2,
             'os_cache':'Uncontrolled; A then B; no purge, no cold-cache claim',
             'replication':'One fresh process per cache;3repeated identical requests. Request1arena-cold,2/3warmer, no process-replication/statistical claim.',
             'variants':{},'review_quality_evaluated':False}
    normalized=[];all_answers=[]
    for label,report in reports:
        cmd=report.get('command',[]).copy()
        if '--pgrn-cache-gb' in cmd:
            cmd[cmd.index('--pgrn-cache-gb')+1]='<CACHE_VARIANT>'
        normalized.append(cmd)
        root=Path(report['run']);responses=json.loads((root/'responses.json').read_text()) if (root/'responses.json').exists() else []
        text=(root/'engine.log').read_text(errors='replace') if (root/'engine.log').exists() else ''
        counters=CACHE_RE.findall(text)
        rows=[];last_hit=last_miss=0
        for index,r in enumerate(responses):
            timing=r.get('timings') or {};usage=r.get('usage') or {}
            row={'request':index+1,'arena_state':'cold' if index==0 else 'warmer',
                 'prompt_tokens':usage.get('prompt_tokens'),'output_tokens':usage.get('completion_tokens'),
                 'native_prompt_tokens':timing.get('prompt_n'),'native_prompt_cache_tokens':timing.get('cache_n'),
                 'prompt_s':timing.get('prompt_ms',0)/1000,'prompt_tps':timing.get('prompt_per_second'),
                 'ttft_s':r.get('first_content_s'),'decode_tps':timing.get('predicted_per_second'),
                 'wall_s':r.get('wall_s'),'bounded_pass':r.get('bounded_request_pass'),
                 'finish':r.get('finish_reasons'),'physical_io_delta':r.get('physical_io_delta')}
            if index<len(counters):
                cache,water,hits,misses=counters[index];hits=int(hits);misses=int(misses)
                row.update({'cache_mib':float(cache),'highwater_mib':float(water),
                    'hits_delta':hits-last_hit,'misses_delta':misses-last_miss})
                last_hit,last_miss=hits,misses
            rows.append(row)
        all_answers.extend([r.get('answer') for r in responses])
        samples=[json.loads(l) for l in (root/'memory.jsonl').read_text().splitlines()] if (root/'memory.jsonl').exists() else []
        rss=[int(s['rss']['stdout'].strip()) for s in samples if s.get('rss',{}).get('returncode')==0 and s['rss']['stdout'].strip().isdigit()]
        swaps=[s['swapouts'] for s in samples if isinstance(s.get('swapouts'),int)]
        variant={'report':str(root/'report.json'),'inference_passed':report.get('inference_passed'),
                 'load_s':report.get('load_to_health_s'),'rows':rows,
                 'native_counter_rows':len(counters),
                 'peak_rss_gib':max(rss)/1048576 if rss else None,
                 'swapout_delta':report.get('memory_after',{}).get('swapouts',0)-report.get('memory_before',{}).get('swapouts',0),
                 'swapout_sample_range':[min(swaps),max(swaps)] if swaps else None,
                 'port_after':report.get('test_port_after'),'engine_exit':report.get('engine_exit_code'),
                 'lab_stayed_stopped':report.get('lab_listeners_and_http_unchanged')}
        for key in ('prompt_s','prompt_tps','ttft_s','decode_tps','wall_s','misses_delta','cache_mib'):
            variant[key]=stat([row.get(key) for row in rows])
        variant['warmer_requests']={key:stat([row.get(key) for row in rows[1:]]) for key in ('prompt_s','ttft_s','decode_tps','misses_delta')}
        summary['variants'][label]=variant
    summary['only_cache_cli_arg_differs']=len(normalized)==2 and normalized[0]==normalized[1]
    summary['all_six_outputs_identical']=len(all_answers)==6 and len(set(all_answers))==1
    rows=[r for v in summary['variants'].values() for r in v['rows']]
    summary['all_prompt_cache_n_zero']=len(rows)==6 and all(r['native_prompt_cache_tokens']==0 for r in rows)
    summary['matching_token_workloads']=len(rows)==6 and len({(r['prompt_tokens'],r['output_tokens']) for r in rows})==1
    a=summary['variants'].get('A2GiB',{});b=summary['variants'].get('B12GiB',{})
    summary['actual_cache_larger_in_B']=bool(a.get('cache_mib') and b.get('cache_mib') and b['cache_mib']['min']>a['cache_mib']['max'])
    summary['technical_comparison_valid']=bool(summary['full_pair'] and summary['only_cache_cli_arg_differs'] and
        summary['actual_cache_larger_in_B'] and summary['all_prompt_cache_n_zero'] and summary['matching_token_workloads'] and
        all(v['inference_passed'] and len(v['rows'])==3 and v['native_counter_rows']==3 for v in summary['variants'].values()))
    if summary['technical_comparison_valid']:
        summary['ratios_B_over_A']={key:b[key]['median']/a[key]['median'] for key in ('prompt_s','prompt_tps','ttft_s','decode_tps','wall_s') if a[key]['median']}
    (parent/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    lines=['# PGRN-Cache2GiB gegen12GiB','',
       'Nur2frische Prozesse, je3gleiche Anfragen. Erste arena-kalt, danach wärmer. OS-Dateicache unkontrolliert, kein Kaltstartbenchmark.','',
       '| Messgröße | A2GiB | B12GiB |','|---|---:|---:|']
    for key in ('load_s','cache_mib','prompt_s','prompt_tps','ttft_s','decode_tps','wall_s','misses_delta','peak_rss_gib','swapout_delta'):
        def fmt(v):
            if isinstance(v,dict):return f"{v['median']:.3f} ({v['min']:.3f}–{v['max']:.3f})"
            return str(v)
        lines.append('| '+key+' | '+fmt(a.get(key))+' | '+fmt(b.get(key))+' |')
    lines+=['','Median (Min–Max), bei Anfragemetriken3Werte; erster/wärmer getrennt in summary.json.',
            'Technisch auswertbar: '+str(summary['technical_comparison_valid']),
            'Alle sechs Ausgaben identisch: '+str(summary['all_six_outputs_identical']),
            'Nur Cache-CLI-Argument verschieden: '+str(summary['only_cache_cli_arg_differs']),
            'B/A-Raten: '+str(summary.get('ratios_B_over_A')),
            'Datenträgerzähler sind geräteweit, nicht exklusiv Prozess/Datei. Keine Qualitäts- oder Langkontextaussage.']
    (parent/'ERGEBNIS.md').write_text('\n'.join(lines)+'\n')
    return summary


def main():
    frozen=verify();quiet()
    if hashlib.sha256(runner.ENGINE.read_bytes()).hexdigest()!='7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e':
        raise RuntimeError('Engine differs from qualified build')
    with socket.socket() as s:s.bind(('127.0.0.1',8083))
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');parent=HERE/'runs'/stamp
    parent.mkdir(parents=True,exist_ok=False)
    (parent/'frozen.json').write_text(json.dumps(frozen,indent=2)+'\n')
    (parent/'harness-hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE/'run_comparison.py',HERE/'speed_client.py',HERE/'isolated_runner.py')},indent=2)+'\n')
    reports=[]
    try:
        for label,cache in [('A2GiB',2),('B12GiB',12)]:
            quiet()
            print('START',label,'Cache-Obergrenze',cache,'GiB; Reserve8GiB;3Anfragen.',flush=True)
            code=runner.main(lab_stopped=True,run_dir=parent/label,client_script=HERE/'speed_client.py',
                 disk_sampler=snapshot,load_timeout=420,context_size=4096,client_timeout=780,
                 no_context_shift=True,client_progress=True,cache_gib=cache)
            report=json.loads((parent/label/'report.json').read_text());reports.append((label,report))
            summarize(parent,reports)
            if code:
                raise RuntimeError(label+' fehlgeschlagen; kein nächster Start oder Retry')
        verify()
    finally:
        result=summarize(parent,reports)
        print('Vergleich technisch auswertbar:',result['technical_comparison_valid'],flush=True)
        print('Ergebnisse:',parent,flush=True)
    return 0 if result['technical_comparison_valid'] else 1


if __name__=='__main__':
    try:
        with (HERE.parent/'qwen_reference/logs/internal-test.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            raise SystemExit(main())
    except (OSError,RuntimeError,ValueError) as e:
        print('ABBRUCH:',e,flush=True)
        raise SystemExit(1)
