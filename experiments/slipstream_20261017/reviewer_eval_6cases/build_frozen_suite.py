"""One-time prompt/rubric freeze. Never run after model responses exist."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
INSTRUCTION = 'Prüfe den bereitgestellten Code auf konkrete Fehler und relevante Designrisiken. Nenne pro Befund Datei und Stelle, Auslöser, Auswirkung und Begründung. Trenne nachgewiesene Fehler von Vermutungen. Wenn du keinen belastbaren Befund findest, sage das. Keine Änderungen am Code.'


def main():
    if (HERE/'FROZEN.json').exists() or (HERE/'runs').exists():
        raise RuntimeError('Suite bereits eingefroren/benutzt; nicht neu schreiben')
    test = subprocess.run([sys.executable,'-B',str(HERE/'private/verify_cases.py')],
                          capture_output=True,text=True)
    (HERE/'private/verification.txt').write_text(test.stdout+test.stderr)
    if test.returncode:
        raise RuntimeError('Verifizierende Tests fehlgeschlagen')
    (HERE/'instruction.txt').write_text(INSTRUCTION+'\n')
    settings = {'context':4096,'max_output_tokens':1024,'enable_thinking':False,
        'expert_cache_gib':2,'headroom_gib':8,'batch':32,'ubatch':32,'parallel':1,
        'io_threads':1,'mtp_draft_max':4,'temperature':0,'seed':42,
        'per_case_timeout_s':600,'order':[f'case{i:02d}' for i in range(1,7)],
        'api':'/v1/chat/completions','cache_prompt':False,'tools':None,
        'conversation_policy':'Fresh system+user messages per case; no history, memory, tools, or repository access.',
        'context_change_reason':'512 tokens cannot hold complete code plus review; 4096 with unchanged 2GiB cache/8GiB reserve.',
        'output_policy':'1024 tokens, thinking off, no retry with extra clues. Length/transport truncation is incomplete.'}
    (HERE/'settings.json').write_text(json.dumps(settings,ensure_ascii=False,indent=2)+'\n')
    prompts=HERE/'prompts';prompts.mkdir()
    for case in settings['order']:
        folder=HERE/'model_cases'/case
        parts=['Rahmenbedingungen:\n'+(folder/'CONTEXT.txt').read_text(),
               'Die folgenden Dateien bilden ein Python-Paket; alle für diesen Ausschnitt benötigten Implementierungen sind enthalten.']
        for file in sorted(folder.glob('*.py')):
            lines='\n'.join(f'{i:3d}: {line}' for i,line in enumerate(file.read_text().splitlines(),1))
            parts.append(f'Datei: {file.name}\n```python\n{lines}\n```')
        # Explicit allowlist. No private solution/test/rubric text enters this payload.
        payload={'messages':[{'role':'system','content':INSTRUCTION},
                             {'role':'user','content':'\n\n'.join(parts)}]}
        (prompts/(case+'.json')).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    key=HERE/'private/answer_key.json';answers=json.loads(key.read_text())
    hotspots={'case01':('retrieval.py','        key = question.strip().casefold()',3),
              'case02':('provider.py','        await self._slots.acquire()',8),
              'case03':('memory.py','        value = await self.store.load(session_id)',8),
              'case04':('chat.py','            conn.execute("BEGIN IMMEDIATE")',7)}
    for case,(file,needle,length) in hotspots.items():
        lines=(HERE/'model_cases'/case/file).read_text().splitlines();start=lines.index(needle)+1
        answers[case]['primary_position']={'file':file,'start_line':start,'end_line':min(start+length-1,len(lines))}
    key.write_text(json.dumps(answers,ensure_ascii=False,indent=2)+'\n')
    paths=[p for folder in ('model_cases','private','prompts') for p in (HERE/folder).rglob('*')
           if p.is_file() and '__pycache__' not in p.parts]
    paths += [HERE/'instruction.txt',HERE/'settings.json']
    manifest={'frozen_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'verification_exit_code':test.returncode,
              'files':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},
              'model_responses_present_at_freeze':False}
    (HERE/'FROZEN.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Sechs Fälle, vollständige Prompts, private Tests/Lösung/Rubrik eingefroren. Noch keine Modellantworten.')


if __name__=='__main__':
    main()
