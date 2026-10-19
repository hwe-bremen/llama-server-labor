#!/usr/bin/env python3
"""Authorized six-case review. Own engine only, internal PGRN, no lab stop/start."""
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import re
import socket
import sys

HERE=Path(__file__).resolve().parent
QWEN=HERE.parent/'qwen_reference'
sys.path.insert(0,str(QWEN))
import run_internal_test as runner
from eval_client import verify_freeze


def main():
    frozen=verify_freeze()
    settings=json.loads((HERE/'settings.json').read_text())
    if any(e['listeners'] for e in runner.stopped_lab_snapshot().values()) or runner.listeners(8083) or runner.llama_pids():
        raise RuntimeError('Labor/llama-Instanz läuft; nichts wird automatisch gestoppt')
    processes=runner.capture(['/bin/ps','-axo','pid=,command='])
    if processes['returncode']:
        raise RuntimeError('Andere Modellprozesse nicht sicher prüfbar')
    pattern=re.compile(r'(?:^|/)llama-server(?:\s|$)|\bollama\s+runner\b|\bmlx_lm\.(?:server|generate)\b|\bvllm\.entrypoints\b|\bomlx\s+serve\b')
    active=[line for line in processes['stdout'].splitlines() if pattern.search(line)]
    if active:
        raise RuntimeError('Andere Modellinstanz sichtbar; kein Start: '+str(active))
    if hashlib.sha256(runner.ENGINE.read_bytes()).hexdigest()!='7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e':
        raise RuntimeError('Engine vom qualifizierten Stand verschieden')
    with socket.socket() as preflight:
        preflight.bind(('127.0.0.1',8083))
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=HERE/'runs'/stamp
    print('Eingefrorene Suite:',frozen['frozen_at'],flush=True)
    print('Sechs neue Unterhaltungen, Kontext4096, Cache2GiB/Reserve8GiB, Limit1024, Thinking aus.',flush=True)
    code=runner.main(lab_stopped=True,run_dir=run,client_script=HERE/'eval_client.py',
                     load_timeout=420,context_size=settings['context'],client_timeout=3660,
                     no_context_shift=True,client_progress=True)
    verify_freeze()
    result=json.loads((run/'report.json').read_text())
    result['frozen_suite']=frozen
    result['harness_hashes']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        (HERE/'run_eval.py',HERE/'eval_client.py',QWEN/'run_internal_test.py')}
    result['review_quality_scored']=False
    (run/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Ausführung abgeschlossen. Fachliche Einzelfallbewertung steht noch aus.',flush=True)
    print('Ergebnisse:',run,flush=True)
    return code


if __name__=='__main__':
    try:
        with (QWEN/'logs/internal-test.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            raise SystemExit(main())
    except (OSError,RuntimeError,ValueError) as exc:
        print('ABBRUCH:',exc,flush=True)
        raise SystemExit(1)
