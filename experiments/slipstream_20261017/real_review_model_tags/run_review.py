#!/usr/bin/env python3
"""Single authorized review. No service stop, unload, restart or automatic retry."""
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
import isolated_runner as runner
from review_client import verify_frozen


def main():
    frozen = verify_frozen()
    settings = json.loads((HERE / 'settings.json').read_text())
    if any(e['listeners'] for e in runner.stopped_lab_snapshot().values()) or runner.listeners(8083) or runner.llama_pids():
        raise RuntimeError('Labor oder Modellinstanz läuft; kein automatisches Stoppen/Entladen')
    ps = runner.capture(['/bin/ps', '-axo', 'pid=,command='])
    if ps['returncode']:
        raise RuntimeError('Modellprozesse nicht sicher prüfbar')
    pattern = re.compile(r'(?:^|/)llama-server(?:\s|$)|\bollama\s+runner\b|\bmlx_lm\.(?:server|generate)\b|\bvllm\.entrypoints\b|\bomlx\s+serve\b')
    active = [line for line in ps['stdout'].splitlines() if pattern.search(line)]
    if active:
        raise RuntimeError('Andere Modellinstanz sichtbar: ' + str(active))
    if hashlib.sha256(runner.ENGINE.read_bytes()).hexdigest() != '7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e':
        raise RuntimeError('Engine unterscheidet sich vom bewährten Stand')
    with socket.socket() as check:
        check.bind(('127.0.0.1', 8083))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run = HERE / 'runs' / stamp
    run.mkdir(parents=True, exist_ok=False)
    before = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=REPO, text=True)
    tracked_before = subprocess.check_output(['git', 'diff', 'HEAD', '--binary'], cwd=REPO)
    index_before = subprocess.check_output(['git', 'diff', '--cached', '--binary'], cwd=REPO)
    head_before = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO)
    # runner creates its own run directory; reserve path safely, then remove only the empty directory.
    run.rmdir()
    code = runner.main(lab_stopped=True, run_dir=run, client_script=HERE/'review_client.py',
                       load_timeout=420, context_size=settings['context'], client_timeout=1830,
                       no_context_shift=True, client_progress=True)
    verify_frozen()
    report = json.loads((run/'report.json').read_text())
    report['frozen_review_input'] = frozen
    report['reference_review_pending'] = True
    report['git_status_before'] = before
    report['git_status_after'] = subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=REPO, text=True)
    report['tracked_worktree_diff_unchanged'] = tracked_before == subprocess.check_output(['git', 'diff', 'HEAD', '--binary'], cwd=REPO)
    report['index_diff_unchanged'] = index_before == subprocess.check_output(['git', 'diff', '--cached', '--binary'], cwd=REPO)
    report['head_unchanged'] = head_before == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=REPO)
    report['harness_hashes'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                              (HERE/'run_review.py', HERE/'review_client.py', HERE/'isolated_runner.py')}
    (run/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Originalantwort gespeichert; Validierung und eigene nicht-blinde Referenzprüfung stehen aus.', flush=True)
    print('Ergebnisse:', run, flush=True)
    return code


if __name__ == '__main__':
    try:
        with (HERE.parent/'qwen_reference/logs/internal-test.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
            raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print('ABBRUCH:', exc, flush=True)
        raise SystemExit(1)
