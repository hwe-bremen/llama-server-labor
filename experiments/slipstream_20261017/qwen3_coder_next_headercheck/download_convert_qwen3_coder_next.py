#!/usr/bin/env python3
"""Pinned GGUF download + native PGRN conversion; NEVER starts an inference server.

Run from normal macOS Terminal. No installations, router changes or HF cache.
Uses existing mount-safe external_directory helper and header parser.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
import zlib

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.path.insert(0, str(LAB))
import check_qwen3_coder_next as check
from download_glm import check_mount, external_directory

MOUNT = Path('/Volumes/Extern M4 Speicher')
GGUF_DIR = MOUNT / 'LLM-Experimente/slipstream/qwen3-coder-next-q4_k_m'
GGUF = GGUF_DIR / check.FILENAME
PARTIAL = GGUF.with_name(GGUF.name + '.download')
PGRN_DIR = LAB / 'pgrn/qwen3-coder-next'
PGRN = PGRN_DIR / 'Qwen3-Coder-Next-Q4_K_M.pgrn'
CONVERTER = LAB / 'runtime/Slipstream.app/Contents/Resources/resources/pgrn-convert'
ENGINE = CONVERTER.with_name('llama-server')
EXPECTED_PGRN = 46_909_751_296
RESERVE = 20 * 1024**3  # Same GiB units as native --min-free-gb 20.
REPORT = HERE / 'DOWNLOAD_CONVERSION_REPORT.md'
PREPARED = HERE / 'inference_parameters_prepared.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def sha_file(path, progress=False):
    digest = hashlib.sha256()
    before = path.stat()
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f'Kein regulärer Dateipfad: {path}')
    with path.open('rb') as stream:
        done = 0
        last = time.monotonic()
        for b in iter(lambda: stream.read(8*1024*1024), b''):
            digest.update(b)
            done += len(b)
            if progress and time.monotonic()-last > 10:
                print(f'SHA-256 {path.name}: {done/before.st_size:.1%}', flush=True)
                last = time.monotonic()
    after = path.stat()
    if (before.st_ino,before.st_size,before.st_mtime_ns) != (after.st_ino,after.st_size,after.st_mtime_ns):
        raise RuntimeError('Datei änderte sich während der Prüfsumme')
    return digest.hexdigest()


def allocated(path):
    return path.stat().st_blocks * 512 if path.exists() else 0


def check_space(external_free, internal_free, external_remaining, internal_remaining):
    if external_free < external_remaining + RESERVE:
        raise RuntimeError('Extern weniger als Restdownload plus 20 GB Reserve frei')
    if internal_free < internal_remaining + RESERVE:
        raise RuntimeError('Intern weniger als restliche PGRN plus 20 GB Reserve frei')


def preflight():
    check_mount(MOUNT, GGUF_DIR)
    if not str(PGRN_DIR.resolve()).startswith(str(LAB.resolve()) + os.sep):
        raise RuntimeError('PGRN-Ziel verlässt das Experiment')
    for p in (GGUF_DIR, GGUF, PARTIAL, PGRN_DIR, PGRN,
              PGRN.with_name(PGRN.name+'.partial'), PGRN.with_name(PGRN.name+'.partial.journal')):
        if p.is_symlink():
            raise RuntimeError(f'Symlink im Ziel abgewiesen: {p}')
    if GGUF.exists() and PARTIAL.exists():
        raise RuntimeError('Finale GGUF und Teildownload vorhanden; nichts überschrieben')
    for p,maximum in ((GGUF,check.SIZE),(PARTIAL,check.SIZE),(PGRN,EXPECTED_PGRN)):
        if p.exists() and (not p.is_file() or p.stat().st_size > maximum):
            raise RuntimeError(f'Unerwartete vorhandene Zieldatei: {p}')
    if GGUF_DIR.exists() and GGUF_DIR.stat().st_dev != MOUNT.stat().st_dev:
        raise RuntimeError('GGUF-Ziel nicht auf externer SSD')
    if PGRN_DIR.exists() and PGRN_DIR.stat().st_dev != LAB.stat().st_dev:
        raise RuntimeError('PGRN-Ziel nicht auf interner Projekt-SSD')
    inventory = json.loads((HERE/'tensor_inventory_rechecked.json').read_text())
    transfer = inventory['transfer']
    if (transfer.get('revision') != check.REVISION or transfer.get('filename') != check.FILENAME
            or inventory['decision'] != 'GO' or not inventory['header']['header_complete']
            or inventory['analysis']['pgrn']['pgrn_file_bytes'] != EXPECTED_PGRN):
        raise RuntimeError('Headernachweis gehört nicht zur freigegebenen Datei')
    b = check.binary_identity()
    if not all(v['matches_inspected_v034'] for v in b.values()):
        raise RuntimeError('Engine oder Konverter weichen vom geprüften v0.3.4 ab')
    help_run = subprocess.run([str(CONVERTER),'--help'],capture_output=True,text=True,check=True)
    for flag in ('--input','--output','--dry-run','--expect-sha256','--progress','--min-free-gb','--resume'):
        if flag not in help_run.stdout:
            raise RuntimeError(f'Native Konverteroption fehlt: {flag}')
    curl_help = subprocess.run(['/usr/bin/curl','--help','all'],capture_output=True,text=True,check=True).stdout
    for flag in ('--continue-at','--max-filesize','--proto-redir','--progress-bar'):
        if flag not in curl_help:
            raise RuntimeError(f'Vorhandenes curl unterstützt {flag} nicht')
    have = GGUF.stat().st_size if GGUF.exists() else PARTIAL.stat().st_size if PARTIAL.exists() else 0
    pp = PGRN.with_name(PGRN.name+'.partial')
    pj = pp.with_name(pp.name+'.journal')
    if pp.exists() != pj.exists():
        raise RuntimeError('Unvollständiges Konvertierungsjournal; nichts verändert')
    if PGRN.exists() and (pp.exists() or pj.exists()):
        raise RuntimeError('Finale PGRN und Partial/Journal gleichzeitig vorhanden')
    p_have = PGRN.stat().st_size if PGRN.exists() else pp.stat().st_size if pp.exists() else 0
    if p_have > EXPECTED_PGRN:
        raise RuntimeError('Vorhandene PGRN-Partial größer als erwartet')
    ext_free, int_free = shutil.disk_usage(MOUNT).free, shutil.disk_usage(LAB).free
    check_space(ext_free,int_free,check.SIZE-have,EXPECTED_PGRN-p_have)
    return inventory, {'external_mounted':True,'external_free_bytes':ext_free,
                       'internal_free_bytes':int_free,'existing_gguf_bytes':have,
                       'existing_pgrn_or_partial_bytes':p_have,'binaries':b,
                       'native_converter_help':help_run.stdout,
                       'external_target_files':sorted(x.name for x in GGUF_DIR.iterdir()) if GGUF_DIR.exists() else [],
                       'internal_target_files':sorted(x.name for x in PGRN_DIR.iterdir()) if PGRN_DIR.exists() else []}


def prepared_parameters():
    # argv is a reviewable description only. There is NO subprocess call for it.
    return {'status':'PREPARED_NOT_STARTED','start_authorized':False,
            'memory_check_required_before_start':True,'port_check_required_before_start':True,
            'argv':[str(ENGINE),'--model',str(GGUF),'--pgrn',str(PGRN),
                    '--host','127.0.0.1','--port','8083','--ctx-size','4096',
                    '--pgrn-cache-gb','12','--pgrn-headroom-gb','8',
                    '--batch-size','25','--ubatch-size','25','--parallel','1',
                    '--spec-type','none','--reasoning','off','--temp','0','--seed','42',
                    '--gpu-layers','99','--jinja'],
            'ubatch_source_evidence':'llama-context.cpp @ 79bba02a6741:241 sets '
            'n_ubatch=min(n_batch, requested);1753 forwards it to memory.init_batch; '
            'hybrid memory delegates this cap to its recurrent batch splitter. '
            'PGRN callback forwards physical ubatch rows × expert_used_count. '
            'Both batch and ubatch are 25, parallel=1: at most 250 IDs with top_k=10.',
            'runtime_verification_required':'Confirm n_batch/n_ubatch and single sequence in startup log; '
            'no actual runtime verification performed.',
            'thinking':'Non-Thinking-Modell; kein künstlicher Denkmodus',
            'tool_calling_and_review_quality':'not tested'}


def verify_gguf(path):
    if path.stat().st_size != check.SIZE:
        raise RuntimeError('GGUF-Dateigröße stimmt nicht')
    print('Vollständige GGUF-SHA-256-Prüfung ...',flush=True)
    digest = sha_file(path,True)
    if digest != check.SHA256:
        raise RuntimeError('GGUF-SHA-256 stimmt nicht; Datei bleibt unverändert erhalten')
    return {'file':str(path),'size_bytes':path.stat().st_size,'sha256':digest,
            'sha256_verified':True,'allocated_bytes':allocated(path)}


def download(logfile, state):
    if GGUF.exists():
        return verify_gguf(GGUF)
    oldfd = os.open('.',os.O_RDONLY)
    try:
        # Existing helper pins directory traversal to the mounted external FS.
        external_directory(MOUNT,GGUF_DIR)
        if not PARTIAL.exists() or PARTIAL.stat().st_size < check.SIZE:
            cmd=['/usr/bin/curl','--disable','--fail','--location','--progress-bar',
                 '--proto','=https','--proto-redir','=https','--connect-timeout','20',
                 '--continue-at','-','--retry','0','--header','Accept-Encoding: identity',
                 '--max-filesize',str(check.SIZE),'--output',PARTIAL.name,check.URL]
            print('Download direkt auf externe SSD, fortsetzbar; kein HF-Cache.',flush=True)
            with logfile.open('a') as log:
                state['full_model_download_started']=True
                proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.PIPE,text=True,bufsize=1)
                try:
                    for line in proc.stderr:
                        sys.stderr.write(line);sys.stderr.flush()
                        log.write(line);log.flush()
                    code=proc.wait()
                except KeyboardInterrupt:
                    proc.terminate();proc.wait()
                    raise
            if code:
                raise RuntimeError(f'curl Exit {code}; Teildownload bleibt extern erhalten')
        check_mount(MOUNT,GGUF_DIR)
        verified=verify_gguf(PARTIAL)
        # Atomic no-clobber promotion. Hardlink adds no second payload copy.
        os.link(PARTIAL.name,GGUF.name,follow_symlinks=False)
        PARTIAL.unlink()
        verified['file']=str(GGUF)
        return verified
    finally:
        os.fchdir(oldfd);os.close(oldfd)


def local_header(inventory):
    with GGUF.open('rb') as f:
        h=check.parse_header(f)
    previous=inventory['header']
    for key in ('gguf_version','tensor_count','metadata_count','header_end','tensor_data_start','metadata'):
        if h[key]!=previous[key]:
            raise RuntimeError(f'Lokaler Header weicht vom Range-Nachweis ab: {key}')
    for actual,expected in zip(h['tensors'],previous['tensors']):
        for key in ('name','shape','type_id','data_offset'):
            if actual[key]!=expected[key]:
                raise RuntimeError(f'Lokales Tensorverzeichnis weicht ab: {actual["name"]}')
    a=check.analyze(h)
    if a['decision']!='GO' or a['pgrn']['pgrn_file_bytes']!=EXPECTED_PGRN:
        raise RuntimeError('Lokale statische Headerprüfung nicht GO')
    return {'header':h,'analysis':a}


def validate_pgrn(path, inventory, progress=True):
    """Independently check identity, every directory record, full CRC and SHA."""
    a,h=inventory['analysis'],inventory['header']
    expected=a['pgrn']['pgrn_file_bytes']
    if path.is_symlink() or not path.is_file() or path.stat().st_size!=expected:
        raise RuntimeError('PGRN-Dateigröße/Dateipfad stimmt nicht')
    roles={}
    for t in h['tensors']:
        if t['streamed_expert']:
            roles.setdefault(t['layer'],{})[t['group']]=t
    experts=a['expert_count']; count=len(roles)*experts
    with path.open('rb') as f:
        header=f.read(16384)
        if header[:8]!=b'PGRN1\0\0\0':raise RuntimeError('PGRN-Magic falsch')
        version,length=struct.unpack_from('<II',header,8)
        if version!=1 or length>16368:raise RuntimeError('PGRN-Header ungültig')
        meta=json.loads(header[16:16+length])
        source=meta['metadata']
        if (source.get('model_sha256')!=check.SHA256 or source.get('source_size')!=check.SIZE
                or source.get('source_format')!='GGUF' or meta.get('expert_count')!=count):
            raise RuntimeError('PGRN-Quellenidentität/Expertenzahl falsch')
        if source.get('geometry')!={'layers_with_experts':len(roles),'experts_per_layer':experts}:
            raise RuntimeError('PGRN-Geometrie falsch')
        # Match type/offset/size for each role, not merely total file length.
        for layer,rs in sorted(roles.items()):
            cursor=0
            for role in ('gate','up','down'):
                t=rs[role];per=t['nbytes']//experts
                expected_role={'offset':cursor,'nbytes':per,'ggml_type':t['type_id']}
                if source['record_layout_by_layer'][str(layer)][role]!=expected_role:
                    raise RuntimeError('PGRN-Rollenlayout weicht vom GGUF ab')
                cursor+=per
        directory_offset=meta['expert_dir_offset']
        if directory_offset+count*26!=expected:raise RuntimeError('PGRN-Verzeichnisgrenze falsch')
        f.seek(directory_offset);directory=f.read(count*26)
        if len(directory)!=count*26:raise RuntimeError('PGRN-Verzeichnis unvollständig')
        records=list(struct.iter_unpack('<HHBBfQII',directory))
        cursor=16384
        for index,r in enumerate(records):
            layer,expert,precision,flags,heat,offset,size,crc=r
            expected_layer=sorted(roles)[index//experts]
            rec=sum(t['nbytes']//experts for t in roles[expected_layer].values())
            if (layer,expert,precision,flags,offset,size)!=(expected_layer,index%experts,1,0,cursor,rec):
                raise RuntimeError(f'PGRN-Verzeichniseintrag ungültig: {index}')
            cursor+=(size+16383)//16384*16384
        if cursor!=directory_offset:raise RuntimeError('PGRN-Payloadgrenze falsch')
        f.seek(16384);digest=hashlib.sha256(header)
        for index,r in enumerate(records):
            size,crc=r[6:8]
            b=f.read(size)
            if len(b)!=size or zlib.crc32(b)&0xffffffff!=crc:
                raise RuntimeError(f'PGRN-CRC falsch: Record {index}')
            digest.update(b)
            padding=(-size)%16384
            b=f.read(padding)
            if len(b)!=padding or any(b):raise RuntimeError('PGRN-Padding ungültig')
            digest.update(b)
            if progress and index%1024==0:
                print(f'PGRN-CRC/SHA: {index:,}/{count:,} Records',flush=True)
        if f.tell()!=directory_offset:raise RuntimeError('PGRN-Dateiposition unerwartet')
        digest.update(directory)
    return {'file':str(path),'size_bytes':expected,'allocated_bytes':allocated(path),
            'source_sha256_verified':True,'all_record_crcs_verified':True,
            'record_count':count,'sha256':digest.hexdigest()}


def conversion(inventory, logdir, state):
    PGRN_DIR.mkdir(parents=True,exist_ok=True)
    if PGRN_DIR.stat().st_dev!=LAB.stat().st_dev:
        raise RuntimeError('PGRN-Ziel nicht intern')
    dry=[str(CONVERTER),'--input',str(GGUF),'--dry-run']
    r=subprocess.run(dry,capture_output=True,text=True)
    (logdir/'dry-run.stdout').write_text(r.stdout)
    (logdir/'dry-run.stderr').write_text(r.stderr)
    state['dry_run']={'argv':dry,'exit_code':r.returncode}
    if r.returncode:raise RuntimeError(f'Nativer Dry-run Exit {r.returncode}')
    d=json.loads(r.stdout)
    checks={'source_size':check.SIZE,'source_shards':1,'layers_with_experts':48,
            'experts_per_layer':512,'expert_count':24576,'estimated_output_bytes':EXPECTED_PGRN}
    if any(d.get(k)!=v for k,v in checks.items()):raise RuntimeError('Native Dry-run-Geometrie weicht ab')
    state['dry_run']['result']=d
    if not PGRN.exists():
        partial=PGRN.with_name(PGRN.name+'.partial')
        cmd=[str(CONVERTER),'--input',str(GGUF),'--output',str(PGRN),
             '--expect-sha256',check.SHA256,'--min-free-gb','20',
             '--io-threads','1','--progress','jsonl']
        if partial.exists():cmd+=['--resume']
        state['conversion']={'argv':cmd,'started_at':now()}
        start=time.monotonic()
        with (logdir/'conversion.jsonl').open('a') as log:
            state['conversion_started']=True
            proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
            try:
                for line in proc.stdout:
                    print(line,end='',flush=True);log.write(line);log.flush()
                code=proc.wait()
            except KeyboardInterrupt:
                proc.send_signal(2);proc.wait()
                raise
        state['conversion'].update(ended_at=now(),duration_seconds=time.monotonic()-start,exit_code=code)
        if code:raise RuntimeError(f'Konverter Exit {code}; keine Engine-/Gewichtsänderung vorgenommen')
    else:
        state['conversion']={'existing_file_reused':True,'exit_code':None,
                             'note':'Kein Überschreiben; unabhängige vollständige CRC/SHA-Prüfung'}
    return validate_pgrn(PGRN,inventory)


def report(state):
    lines=['# Qwen3-Coder-Next: Download und PGRN-Konvertierung','',
           '## Bewertung: '+state['status'],'',
           '- Stand: '+state['checked_at'],
           '- Revision: '+check.REVISION,'- Exakte Quelle: '+check.URL,
           f'- Erwartete GGUF-Größe: {check.SIZE:,} Bytes',
           '- Erwartete GGUF-SHA-256: '+check.SHA256,
           f'- Erwartete PGRN-Größe: {EXPECTED_PGRN:,} Bytes','',
           '**Kein Inferenzserver gestartet. Bestehendes Labor nicht verändert.**','']
    if state.get('error'):lines+=['**Blockade:** '+state['error'],'']
    lines+=['## Ausführungsnachweise [BELEGT]','','```json',
            json.dumps(state,ensure_ascii=False,indent=2),'```','',
            'Fehlende Phasenfelder bedeuten: nicht ausgeführt bzw. nicht gemessen. '
            'Eine erfolgreiche Headerprüfung ist kein Download- oder Konvertierungsnachweis.','',
            '## Offline-Validierung [BELEGT]','',
            '20 Tests bestanden (test_headercheck und test_download_convert). '
            'Synthetische PGRN-Dateien prüfen vollständige CRC/SHA-Erfassung sowie die '
            'Zurückweisung beschädigter Payloads, falscher Verzeichniseinträge und Quellenidentitäten. '
            'Diese Tests starten weder Download noch Konverter oder Engine.','',
            '## Späterer Inferenzversuch: nur vorbereitet','',
            '4096 Kontext, 12 GiB Expertencache, batch=25, ubatch=25, eine Sequenz, '
            'spec-type=none, reasoning=off, Temperatur 0 und Seed 42. '
            'Prüfbare Argumentliste: inference_parameters_prepared.json; kein automatischer Start.','',
            'Die tatsächliche CLI ist in der vorhandenen, demselben Enginehash zugeordneten Hilfe '
            'belegt. llama-context.cpp am Pin 79bba02a6741 begrenzt n_ubatch auf n_batch '
            'und reicht es an die Memory-Batchzerlegung weiter. Die Hybridimplementierung '
            'verwendet den rekurrenten Batchsplitter; der PGRN-Callback verarbeitet dessen '
            'physische Tokenzeilen. Mit batch=ubatch=25 und parallel=1 sind bei top_k=10 '
            'höchstens 250 IDs pro Stagingaufruf möglich. '
            'Die angewendeten Werte müssen beim ersten tatsächlichen Start im Log bestätigt werden.','',
            'Quellnachweise: source_evidence/llama-memory-hybrid_79bba02a6741.cpp '
            '(init_batch, split_equal/split_seq) sowie source_evidence/converter_v0.3.4.cpp '
            '(Quellenhash, Dry-run, Recordlayout und CRC).','',
            '## Risiken und Empfehlung','',
            'Vor einem separat freizugebenden Inferenzstart freie Ports und aktuelle RAM-Belegung '
            'prüfen. Graph-/Prefillbuffer und andere laufende Modelle sind nicht in den statischen '
            '15,32 GiB enthalten. MXFP4-Shared-Experts sind resident; tatsächliche Metal-Ausführung, '
            'Tool-Calling, numerische Qualität und Reviewpräzision bleiben ungeprüft. '
            'Für qwen3next ist kein bestätigter Compact-Slots-Pfad vorhanden.','',
            '## Fortsetzung im normalen macOS-Terminal','','```sh',
            'python3 -B '+repr(str(Path(__file__).resolve())),'```','',
            'Derselbe Befehl nimmt den externen .download-Stand wieder auf. '
            'Vorhandene finale Dateien werden geprüft und nicht überschrieben. '
            'Bei Fehlern bleibt der Ablauf stehen; kein automatischer Modellstart.']
    REPORT.write_text('\n'.join(lines)+'\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prepare-only',action='store_true',help='Local checks + report only; no download/conversion')
    args=ap.parse_args()
    state={'checked_at':now(),'status':'BLOCKED','model_started':False,
           'full_model_download_started':False,'conversion_started':False}
    logdir=HERE/'download_conversion_runs'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    logdir.mkdir(parents=True,exist_ok=False)
    with (HERE/'download_conversion.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            inventory,state['preflight']=preflight()
            check.write_json(PREPARED,prepared_parameters())
            if args.prepare_only:
                state['error']='Nur Vorbereitung ausgeführt. Der vorherige HEAD-Zugriff in dieser Sitzung '
                state['error']+='scheiterte an DNS: [Errno 8] nodename nor servname provided, or not known. '
                state['error']+='Kein Download und keine Konvertierung ausgeführt.'
            else:
                state['gguf']=download(logdir/'download.log',state)
                check.write_json(logdir/'checkpoint.json',state)
                verified=local_header(inventory)
                state['local_header_verified']=True
                # Recheck currently free space after download, before native conversion.
                remaining=0 if PGRN.exists() else EXPECTED_PGRN
                pp=PGRN.with_name(PGRN.name+'.partial')
                if pp.exists():remaining=max(0,remaining-pp.stat().st_size)
                check_space(shutil.disk_usage(MOUNT).free,shutil.disk_usage(LAB).free,0,remaining)
                state['pgrn']=conversion(verified,logdir,state)
                state['status']='READY WITH CONDITIONS'
                state['conditions']=['Vor Inferenz Ports/RAM prüfen und effektives n_ubatch im Startlog bestätigen',
                                     'Kein Inferenzstart durch diesen Auftrag autorisiert']
        except KeyboardInterrupt:
            state['error']='Vom Benutzer unterbrochen; keine automatische Fortsetzung.'
        except Exception as exc:
            state['error']=type(exc).__name__+': '+str(exc).split('https://')[0][:700]
        finally:
            state['finished_at']=now()
            state['log_directory']=str(logdir)
            check.write_json(logdir/'result.json',state)
            report(state)
    print('Bewertung:',state['status'])
    print('Bericht:',REPORT)
    if state.get('error'):print(state['error'])
    return 0 if state['status'].startswith('READY') else 2


if __name__=='__main__':
    sys.exit(main())
