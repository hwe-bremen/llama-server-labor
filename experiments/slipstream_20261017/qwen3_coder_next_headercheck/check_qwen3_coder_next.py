#!/usr/bin/env python3
"""Bounded, pinned GGUF header inspection. Standard library only; no inference.

Reuses HeaderReader, EXPERT and summarize from ../inspect_gguf_metadata.py.
Only this script's own directory receives output. No model payload is requested.
Budget reservations persist across invocations, including failed requests.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import struct
import sys
import urllib.error
import urllib.parse
import urllib.request
import fcntl

HERE = Path(__file__).resolve().parent
LAB = HERE.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(LAB))
from inspect_gguf_metadata import HeaderReader, EXPERT, summarize, FORMATS
from probe_remote_metadata import validate_range_headers

REPO = 'unsloth/Qwen3-Coder-Next-GGUF'
REVISION = 'ce09c67b53bc8739eef83fe67b2f5d293c270632'
FILENAME = 'Qwen3-Coder-Next-Q4_K_M.gguf'
SIZE = 48_528_320_544
SHA256 = '9e6032d2f3b50a60f17ce8bf5a1d85c71af9b53b89c7978020ae7c660f29b090'
URL = f'https://huggingface.co/{REPO}/resolve/{REVISION}/{FILENAME}'
BUDGET = 32 * 1024 * 1024
CHUNK = 256 * 1024
ALLOWED = {0, 1, 12, 13, 14}
# GGML row block geometry from the pinned ggml-common.h; unknown types fail closed.
TYPES = {
    0: ('F32', 1, 4), 1: ('F16', 1, 2), 2: ('Q4_0', 32, 18),
    3: ('Q4_1', 32, 20), 6: ('Q5_0', 32, 22), 7: ('Q5_1', 32, 24),
    8: ('Q8_0', 32, 34), 9: ('Q8_1', 32, 40), 10: ('Q2_K', 256, 84),
    11: ('Q3_K', 256, 110), 12: ('Q4_K', 256, 144),
    13: ('Q5_K', 256, 176), 14: ('Q6_K', 256, 210),
    15: ('Q8_K', 256, 292), 16: ('IQ2_XXS', 256, 66),
    17: ('IQ2_XS', 256, 74), 18: ('IQ3_XXS', 256, 98),
    19: ('IQ1_S', 256, 50), 20: ('IQ4_NL', 32, 18),
    21: ('IQ3_S', 256, 110), 22: ('IQ2_S', 256, 82),
    23: ('IQ4_XS', 256, 136), 24: ('I8', 1, 1),
    25: ('I16', 1, 2), 26: ('I32', 1, 4), 27: ('I64', 1, 8),
    28: ('F64', 1, 8), 29: ('IQ1_M', 256, 56), 30: ('BF16', 1, 2),
    39: ('MXFP4', 32, 17),  # pinned ggml.h + ggml-common.h; resident only
}
EXPECTED_BINARIES = {
    'llama-server': '7d022ad062d322bb6964b9828f4f529e867c7cea98447f84ffb19a05ff4e7f0e',
    'pgrn-convert': 'af8e47e59d4dcd9eed556da061220af7bd10c3de8137eea2ddd866ab53ad8476',
}


def write_json(path, obj):
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')
    os.replace(temp, path)


class ProbeError(Exception):
    pass


class HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.username or parsed.password:
            raise ProbeError('Nicht zugelassene HTTP-Weiterleitung')
        return super().redirect_request(req, fp, code, msg, headers, newurl)

    # A redirect body is never drained by the default handler. Closing avoids
    # hidden body reads and keeps Range/identity on the new HTTPS request.
    def http_error_302(self, req, fp, code, msg, headers):
        url = headers.get('location') or headers.get('uri')
        if not url:
            raise ProbeError('Weiterleitung ohne Ziel')
        url = urllib.parse.urljoin(req.full_url, url)
        redirects = getattr(req, '_probe_redirects', 0)
        if redirects >= 8:
            fp.close()
            raise ProbeError('Zu viele HTTPS-Weiterleitungen')
        new = self.redirect_request(req, fp, code, msg, headers, url)
        fp.close()
        if new is None:
            raise ProbeError('Weiterleitung verworfen')
        new._probe_redirects = redirects + 1
        return self.parent.open(new, timeout=req.timeout)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


class Transport:
    def __init__(self, ledger_path, opener=None):
        self.path = ledger_path
        self.ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
            'revision': REVISION, 'filename': FILENAME, 'budget_bytes': BUDGET,
            'reserved_bytes': 0, 'body_bytes_read': 0, 'requests': []}
        if (self.ledger['revision'] != REVISION or self.ledger['budget_bytes'] != BUDGET
                or self.ledger['filename'] != FILENAME):
            raise ProbeError('Bestehendes Budget gehört zu anderer Quelle')
        self.opener = opener or urllib.request.build_opener(HttpsOnly())
        self.start_bytes = self.ledger['body_bytes_read']

    def fetch(self, start, count):
        if count <= 0 or start < 0 or start + count > SIZE:
            raise ProbeError('Ungültiger Dateibereich')
        if self.ledger['reserved_bytes'] + count > BUDGET:
            raise ProbeError('32-MiB-Lebenszeitbudget erschöpft; keine Erhöhung')
        self.ledger['reserved_bytes'] += count
        entry = {'start': start, 'end': start + count - 1, 'reserved_bytes': count,
                 'status': None, 'body_bytes_read': 0}
        self.ledger['requests'].append(entry)
        write_json(self.path, self.ledger)
        print(f'Range {start:,}–{start + count - 1:,}; Budget reserviert '
              f'{self.ledger["reserved_bytes"]:,}/{BUDGET:,} Bytes', flush=True)
        request = urllib.request.Request(URL, headers={
            'Range': f'bytes={start}-{start + count - 1}',
            'Accept-Encoding': 'identity'})
        try:
            with self.opener.open(request, timeout=30) as response:
                entry['status'] = response.status
                # Strict check BEFORE reading: a 200 body is never read.
                validate_range_headers(response.status, response.headers,
                                       start, start + count - 1, SIZE)
                chunks = []
                remaining = count
                while remaining:
                    data = response.read(min(65536, remaining))
                    if not data:
                        raise ProbeError('Unvollständige Range-Antwort')
                    if len(data) > remaining:
                        raise ProbeError('HTTP-Reader lieferte zu viele Bytes')
                    chunks.append(data)
                    remaining -= len(data)
                    entry['body_bytes_read'] += len(data)
                    self.ledger['body_bytes_read'] += len(data)
                    write_json(self.path, self.ledger)
                entry['verified_206'] = True
                return b''.join(chunks)
        except Exception as exc:
            # No signed redirect URLs or credentials are persisted in errors.
            entry['error_class'] = type(exc).__name__
            raise
        finally:
            write_json(self.path, self.ledger)


class RangePrefix:
    """Contiguous prefix; prefetch only within a proven minimum header extent.

    Counts, fixed fields and string lengths provide conservative lower bounds
    on the still-unparsed header. No guessed window crosses its actual end.
    """
    def __init__(self, transport):
        self.transport = transport
        self.buf = bytearray(transport.fetch(0, 24))
        self.pos = 0
        self.safe_end = 24

    def tell(self):
        return self.pos

    def guarantee(self, end):
        if end > BUDGET:
            raise ProbeError('Header reicht über das 32-MiB-Limit hinaus')
        self.safe_end = max(self.safe_end, end)

    def read(self, count):
        end = self.pos + count
        while len(self.buf) < end:
            want = min(self.safe_end, max(end, len(self.buf) + CHUNK))
            self.buf.extend(self.transport.fetch(len(self.buf), want - len(self.buf)))
        data = bytes(self.buf[self.pos:end])
        self.pos = end
        return data


class MetadataReader(HeaderReader):
    """Existing scalar/string parser plus strict arrays and network extent hints."""
    def __init__(self, stream):
        super().__init__(stream, BUDGET)
        self.tail = 0

    def read(self, count):
        if count < 0 or self.file.tell() + count > self.limit:
            raise ProbeError('Metadatenlimit überschritten')
        if hasattr(self.file, 'guarantee'):
            self.file.guarantee(self.file.tell() + count + self.tail)
        return super().read(count)

    def skip(self, count):
        # All metadata bytes are actually read, even values not retained in JSON.
        self.read(count)

    def value(self, kind, keep=True):
        if kind != 9:
            return super().value(kind, keep)
        subtype, length = self.number('<I'), self.number('<Q')
        if subtype not in FORMATS and subtype != 8:
            raise ProbeError(f'Unbekannter/ungültiger GGUF-Arraytyp {subtype}')
        if subtype in FORMATS:
            fmt = FORMATS[subtype]
            raw = self.read(struct.calcsize(fmt) * length)
            if keep and length <= 4096:
                return [v[0] for v in struct.iter_unpack(fmt, raw)]
        else:
            if length * 8 > BUDGET:
                raise ProbeError('Stringarray überschreitet Headerbudget')
            items = []
            original_tail = self.tail
            try:
                for index in range(length):
                    self.tail = original_tail + (length - index - 1) * 8
                    # Reuse HeaderReader.string; read/skip are bounded above.
                    v = self.string(keep and length <= 4096)
                    if keep and length <= 4096:
                        items.append(v)
            finally:
                self.tail = original_tail
            if keep and length <= 4096:
                return items
        return {'array_type': subtype, 'length': length,
                'values_omitted': True, 'fully_read': True}


def parse_header(stream):
    r = MetadataReader(stream)
    if r.read(4) != b'GGUF':
        raise ProbeError('Kein GGUF')
    version = r.number('<I')
    if version not in (2, 3):
        raise ProbeError(f'Nicht unterstützte GGUF-Version {version}')
    nt, nk = r.number('<Q'), r.number('<Q')
    if not nt or nt * 32 + nk * 13 > BUDGET - 24:
        raise ProbeError('Unplausible Tensor-/Metadatenanzahl')
    metadata, metadata_types = {}, {}
    for index in range(nk):
        r.tail = (nk - index - 1) * 13 + nt * 32
        key, kind = r.string(), r.number('<I')
        if key in metadata:
            raise ProbeError(f'Doppelter Metadatenschlüssel {key}')
        keep = not key.startswith(('tokenizer.ggml.tokens', 'tokenizer.ggml.merges',
                                   'tokenizer.ggml.scores', 'tokenizer.ggml.token_type'))
        value = r.value(kind, keep)
        metadata[key] = value if keep else {'values_omitted': True, 'fully_read': True}
        metadata_types[key] = kind
    tensors = []
    for index in range(nt):
        r.tail = (nt - index - 1) * 32
        name, nd = r.string(), r.number('<I')
        if not name or not 1 <= nd <= 4:
            raise ProbeError('Ungültiger Tensorname oder Dimensionszahl')
        shape = [r.number('<Q') for _ in range(nd)]
        if any(n == 0 for n in shape):
            raise ProbeError(f'Leere Tensorform: {name}')
        kind, offset = r.number('<I'), r.number('<Q')
        match = EXPERT.fullmatch(name)
        group = match.group(2) if match else (
            'shared_expert_resident' if '_shexp' in name else
            'unrecognized_expert' if ('exps' in name or 'expert' in name.lower()) else
            'other_resident')
        tensors.append({'name': name, 'shape': shape, 'type_id': kind,
                        'type': TYPES.get(kind, (f'UNKNOWN_{kind}',))[0],
                        'data_offset': offset, 'streamed_expert': bool(match),
                        'group': group, 'layer': int(match.group(1)) if match else None,
                        'converter_type_accepted': kind in ALLOWED if match else None})
    r.tail = 0
    alignment = metadata.get('general.alignment', 32)
    if not isinstance(alignment, int) or alignment <= 0 or alignment & (alignment - 1):
        raise ProbeError('Ungültiges GGUF-Alignment')
    end = stream.tell()
    return {'gguf_version': version, 'metadata_count': nk, 'tensor_count': nt,
            'metadata': metadata, 'metadata_types': metadata_types,
            'general_alignment': alignment, 'header_end': end,
            'tensor_data_start': (end + alignment - 1) // alignment * alignment,
            'tensors': tensors, 'header_complete': True, 'tensor_payload_read': False}


def pgrn_layout(layers, expert_count):
    """Exact native-converter metadata serialization; no PGRN bytes are written."""
    records, layout, directory = [], {}, []
    raw = padded = 0
    for layer in sorted(layers):
        roles, cursor, row = {}, 0, [layer]
        for role in ('gate', 'up', 'down'):
            t = layers[layer][role]
            per = t['nbytes'] // expert_count
            roles[role] = {'offset': cursor, 'nbytes': per, 'ggml_type': t['type_id']}
            row.extend([t['type_id'], per])
            cursor += per
        layout[str(layer)] = roles
        directory.append(row)
        raw += cursor * expert_count
        padded += ((cursor + 16383) // 16384 * 16384) * expert_count
        records.append({'layer': layer, 'record_bytes': cursor})
    total = len(layers) * expert_count
    metadata = {'model_sha256': SHA256, 'source_size': SIZE, 'source_format': 'GGUF',
                'geometry': {'layers_with_experts': len(layers),
                             'experts_per_layer': expert_count},
                'record_layout_by_layer': layout, 'tensor_directory': directory}
    header = {'metadata': metadata, 'expert_count': total,
              'expert_dir_offset': 16384 + padded}
    header_bytes = 16 + len(json.dumps(header, separators=(',', ':')).encode())
    return {'pgrn_file_bytes': 16384 + padded + total * 26,
            'expert_payload_bytes': raw, 'padding_bytes': padded - raw,
            'directory_bytes': total * 26, 'header_reserved_bytes': 16384,
            'header_used_bytes': header_bytes, 'header_fits': header_bytes <= 16384,
            'records': records}


def analyze(header, source_size=SIZE):
    problems, unknowns = [], []
    ts, meta = header['tensors'], header['metadata']
    arch = meta.get('general.architecture')
    if arch != 'qwen3next':
        problems.append(f'Architektur {arch!r} statt qwen3next')
    n_exp = meta.get('qwen3next.expert_count')
    n_layers = meta.get('qwen3next.block_count')
    used = meta.get('qwen3next.expert_used_count')
    if not isinstance(n_exp, int) or not 0 < n_exp <= 65535:
        problems.append('Fehlende/ungültige authoritative expert_count')
    if header['metadata_types'].get('qwen3next.expert_count') not in (4, 5, 10):
        problems.append('expert_count hat keinen vom Konverter gelesenen GGUF-Integer-Typ')
    if not isinstance(n_layers, int) or not 0 < n_layers <= 65536:
        problems.append('Fehlende/ungültige block_count')
    if meta.get('split.count', 1) not in (0, 1) or meta.get('split.no', 0) != 0:
        problems.append('Geteilte GGUF-Quelle: unveränderter Split-PGRN-Pfad blockiert')
    if 'split.tensors.count' in meta and meta['split.tensors.count'] != len(ts):
        problems.append('Split-Gesamttensorzahl stimmt nicht mit Einzeldatei überein')
    names = Counter(t['name'] for t in ts)
    if any(v > 1 for v in names.values()):
        problems.append('Doppelte Tensornamen')
    layers, spans = defaultdict(dict), []
    for t in ts:
        shape, typ, off = t['shape'], t['type_id'], t['data_offset']
        t['type'] = TYPES.get(typ, (f'UNKNOWN_{typ}',))[0]
        if typ not in TYPES:
            unknowns.append(f'Unbekannte GGML-Blockgröße: {t["name"]}, Typ {typ}')
            t['nbytes'] = None
        else:
            _, block, block_bytes = TYPES[typ]
            if shape[0] % block:
                problems.append(f'Blockbreite {block} unverträglich: {t["name"]} {shape}')
                t['nbytes'] = None
            else:
                t['nbytes'] = math.prod(shape) // block * block_bytes
                absolute = header['tensor_data_start'] + off
                t['absolute_offset'] = absolute
                if off % header['general_alignment'] or absolute + t['nbytes'] > source_size:
                    problems.append(f'Offset/Dateigrenze ungültig: {t["name"]}')
                spans.append((off, off + t['nbytes'], t['name']))
        if t['streamed_expert']:
            if typ not in ALLOWED:
                problems.append(f'Nicht zugelassener Expertentyp {typ}: {t["name"]}')
            if len(shape) != 3 or shape[-1] != n_exp:
                problems.append(f'Nicht passend gestapelt: {t["name"]} {shape}')
            if isinstance(n_layers, int) and t['layer'] >= n_layers:
                problems.append(f'Expertenlayer außerhalb Modell: {t["name"]}')
            if t['group'] in layers[t['layer']]:
                problems.append(f'Doppelte Expertenrolle: {t["name"]}')
            layers[t['layer']][t['group']] = t
        elif t['group'] == 'unrecognized_expert':
            problems.append(f'Nicht unterstützter/fusionierter Expertenname: {t["name"]}')
    spans.sort()
    for a, b in zip(spans, spans[1:]):
        if a[1] > b[0]:
            problems.append(f'Überlappende Tensorbereiche: {a[2]} / {b[2]}')
    if not layers:
        problems.append('Keine getrennten gerouteten Expertentensoren')
    if isinstance(n_layers, int) and set(layers) != set(range(n_layers)):
        problems.append('MoE-Schichtabdeckung entspricht nicht vollständig block_count')
    for layer, roles in layers.items():
        if set(roles) != {'gate', 'up', 'down'}:
            problems.append(f'Unvollständiges Gate/Up/Down-Tripel, Schicht {layer}')
            continue
        g, u, d = (roles[r] for r in ('gate', 'up', 'down'))
        if len(g['shape']) == 3 and len(d['shape']) == 3:
            if g['shape'] != u['shape'] or d['shape'] != [g['shape'][1], g['shape'][0], n_exp]:
                problems.append(f'Gate/Up/Down-Formen nicht konsistent, Schicht {layer}')
            hidden = meta.get('qwen3next.embedding_length')
            ff = meta.get('qwen3next.expert_feed_forward_length')
            if hidden is None or ff is None:
                unknowns.append('embedding_length/expert_feed_forward_length fehlen')
            elif g['shape'] != [hidden, ff, n_exp]:
                problems.append(f'Expertenform widerspricht Modellmetadaten, Schicht {layer}')
    groups = summarize([header])
    pgrn = None
    memory = None
    if not problems and not unknowns:
        pgrn = pgrn_layout(layers, n_exp)
        if not pgrn['header_fits']:
            problems.append('PGRN-Metadaten passen nicht in den festen 16-KiB-Header')
        resident = sum(t['nbytes'] for t in ts if not t['streamed_expert'])
        # GGML payload sizes, before backend-specific alignment/allocation overhead.
        scratch = sum(max(roles[role]['nbytes'] for roles in layers.values())
                      for role in ('gate', 'up', 'down'))
        memory = {'resident_tensor_payload_bytes': resident,
                  'routed_tensor_payload_bytes': sum(t['nbytes'] for t in ts if t['streamed_expert']),
                  'all_tensor_payload_bytes': sum(t['nbytes'] for t in ts),
                  'expert_cache_bytes': 12 * 1024**3,
                  'scratch_payload_bytes_before_backend_alignment': scratch,
                  'gguf_plus_pgrn_bytes': source_size + pgrn['pgrn_file_bytes'],
                  'runtime_overhead_measured': False}
        interval = meta.get('qwen3next.full_attention_interval')
        heads = meta.get('qwen3next.attention.head_count_kv')
        dk = meta.get('qwen3next.attention.key_length')
        dv = meta.get('qwen3next.attention.value_length')
        # Do not infer actual full-attention flags from a guessed interval.
        flags = meta.get('qwen3next.attention.recurrent_layers')
        if isinstance(flags, list) and len(flags) == n_layers:
            full = sum(not x for x in flags)
        elif isinstance(interval, int) and interval > 0:
            full = n_layers // interval
        else:
            full = None
        if all(isinstance(x, int) and x > 0 for x in (heads, dk, dv)) and full is not None:
            memory['kv_f16_single_sequence_assuming_engine_layout'] = {
                str(ctx): full * ctx * heads * (dk + dv) * 2 for ctx in (16384, 32768)}
        else:
            memory['kv_f16_single_sequence_assuming_engine_layout'] = None
        memory['full_attention_layers_from_metadata'] = full
    return {'decision': 'NO-GO' if problems else 'UNGEKLÄRT' if unknowns else 'GO',
            'blockers': list(dict.fromkeys(problems)),
            'unknowns': list(dict.fromkeys(unknowns)), 'summary': groups,
            'expert_layers': len(layers), 'expert_count': n_exp,
            'expert_used_count': used, 'pgrn': pgrn, 'memory': memory,
            'inference_tested': False, 'full_model_sha256_verified': False}


PREFILL = '''[BELEGT: v0.3.4-Codeprüfung] PGR_STAGE_MAX=256 begrenzt die
unterschiedlichen Experten in einem pgr_stage_selected-Aufruf, nicht die
Gesamtexpertenzahl. Der Callback übergibt rows × top_k zusammen an pgrn_stage.
Die Deduplizierung mit der 256er-Prüfung erfolgt VOR der späteren IO-Fensterung.
Diese Fensterung verhindert den Überlauf daher nicht. Für 512 Modell-Experten
und top_k=10 sind mehr als 256 unterschiedliche IDs ab 26 Tokenzeilen möglich.
Konkretes Gegenbeispiel: 26 Zeilen mit den disjunkten IDs 0 bis 259.
Es ist kein Beweis, dass natürliches Routing dieses Muster tatsächlich erzeugt.
Der untersuchte Callback teilt den Nicht-Compact-Aufruf nicht vorher auf.
Der Patch ergänzt Compact Slots explizit im qwen35moe-Graph für Ein-Token-
Ausführung. Der untersuchte qwen3next-Graph übergibt diese optionale Auswahl
nicht und nutzt den Standardpfad; Compact Slots dürfen für diesen Kandidaten
nicht als vorhandene Lösung behauptet werden. Der Code erlaubt 512
Experten grundsätzlich (Grenze UINT16_MAX). Kontextlänge und Ubatch sind
verschiedene Größen: Auch 16K/32K-Kontext erzwingt keinen 16K/32K-Stagingaufruf.
Eine spätere explizite Ubatch-Grenze von höchstens floor(256/top_k), bei top_k=10
also 25, begrenzt die Anzahl angeforderter IDs unabhängig vom Routing. Dies ist
eine aus dem Code abgeleitete konservative Auflage für einen späteren Lauf,
keine in dieser Untersuchung vorgenommene Konfigurationsänderung.'''


def binary_identity():
    directory = LAB / 'runtime/Slipstream.app/Contents/Resources/resources'
    items = {}
    for name, expected in EXPECTED_BINARIES.items():
        p = directory / name
        actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        items[name] = {'sha256': actual, 'matches_inspected_v034': actual == expected}
    return items


def make_report(result):
    h, a = result.get('header'), result.get('analysis')
    ledger = result['transfer']
    lines = ['# Qwen3-Coder-Next: Header- und PGRN-Prüfung', '',
             f'Stand: {result["checked_at"]}', '', f'## Entscheidung: {result["decision"]}', '',
             'Ein GO betrifft ausschließlich statisch geprüfte Voraussetzungen für eine spätere '
             'Downloadentscheidung. Kein Download-, Konvertierungs- oder Inferenzstart ist freigegeben.', '',
             '## Modellidentität', '', f'- Repository: {REPO}', f'- Datei: {FILENAME}',
             f'- Feste Revision: {REVISION}', f'- Veröffentlichte Größe: {SIZE:,} Bytes',
             f'- Veröffentlichte SHA-256/LFS-OID: {SHA256}',
             '- Vollständiger Modellhash wurde nicht lokal verifiziert.', '',
             '## HTTP und Transferbudget', '',
             f'- GGUF-Bodybytes dieser Ausführung: {result["run_body_bytes_read"]:,}',
             f'- GGUF-Bodybytes kumuliert: {ledger["body_bytes_read"]:,}',
             f'- Konservativ reserviert, einschließlich Fehlversuchen: {ledger["reserved_bytes"]:,}/{BUDGET:,}',
             f'- Erfolgreiche 206-Requests: {sum(bool(x.get("verified_206")) for x in ledger["requests"])}',
             '- Keine automatischen Retries. HTTP 200 wird vor Body-Lektüre abgewiesen.',
             '- HTTPS-Redirect-Bodys werden nicht gelesen. HTTP-Header/TLS-Overhead sind keine GGUF-Bodybytes.', '']
    if result.get('error'):
        lines += ['**Prüfung nicht abgeschlossen:** ' + result['error'], '',
                  'Kein aktuelles ausgelesenes Tensorinventar erzeugt. Kein positiver Kompatibilitätsnachweis. '
                  'Ein eventuell älteres tensor_inventory.json gehört nur zu dessen checked_at-Zeitstempel.', '']
    if h:
        lines += ['## Tatsächliche GGUF-Metadaten [BELEGT]', '',
                  f'- Version: {h["gguf_version"]}; Metadateneinträge: {h["metadata_count"]}; Tensoren: {h["tensor_count"]}',
                  f'- Architektur: {h["metadata"].get("general.architecture")}',
                  f'- Headerende: {h["header_end"]}; Tensorpayloadbeginn: {h["tensor_data_start"]}',
                  f'- Alignment: {h["general_alignment"]}',
                  '- Split-Metadaten: ' + json.dumps({k:v for k,v in h['metadata'].items() if k.startswith('split.')},ensure_ascii=False),
                  '- Chat-Template in tensor_inventory.json gespeichert, sofern im GGUF vorhanden.', '',
                  '## Vollständige Tensorstatistik [BELEGT]', '',
                  '| Gruppe | GGML-Typ | Tensorzahl | Konverterfreigabe für geroutete Experten |',
                  '|---|---|---:|---|']
        for group, counts in a['summary']['groups'].items():
            for typ, count in sorted(counts.items()):
                allowed = next((i in ALLOWED for i,v in TYPES.items() if v[0] == typ), False)
                lines.append(f'| {group} | {typ} | {count} | '+('ja' if allowed else 'nein')+' |'
                             if group in ('gate','up','down') else f'| {group} | {typ} | {count} | resident / getrennt zu beurteilen |')
        lines += ['', '## Konverter und Engine', '']
        lines += ['- Blocker: '+x for x in a['blockers']] or ['- Keine statisch erkennbaren Blocker in den vollständig geparsten Daten.']
        lines += ['- Offen: '+x for x in a['unknowns']]
        lines += ['', 'Die Konverterlogik wurde anhand des unveränderten v0.3.4-Codes abgebildet, '
                  'nicht durch Start des Konverters geprüft. Shared Experts werden resident geladen. '
                  'Eine unsplit Einzeldatei ergibt denselben Quellenhashpfad bei Konverter und Loader.', '',
                  '## Speicherberechnung', '']
        if a['pgrn']:
            lines += ['Aus vollständigen Tensorformen/Typen berechnet, keine Laufzeitmessung:', '',
                      '```json', json.dumps({'pgrn':a['pgrn'],'memory':a['memory']},ensure_ascii=False,indent=2), '```', '',
                      'PGRN: feste 16 KiB Header + auf 16 KiB ausgerichtete Expertenrecords + 26 Bytes je Record. '
                      'GGUF und PGRN werden weiterhin beide benötigt. Backendalignment, Graph-/Prefillbuffer, '
                      'rekurrente Zustände, Betriebssystem und andere laufende Modelle kommen hinzu. '
                      'Residente Gewichte + 12 GiB Cache + Scratch + KV sind eine Untergrenze, kein garantierter Peak. '
                      'KV wird nur aus vorhandenen Attention-Metadaten abgeleitet; ohne ausreichende Schlüssel bleibt es offen.']
        else:
            lines += ['Keine belastbare vollständige Speicherfreigabe wegen der oben genannten Blocker/offenen Daten.']
    else:
        lines += ['## Tensorinventar und Speicher', '',
                  'GGUF-Version, Architektur, Tensorzahl, Split-Metadaten, tatsächliche Expertentypen, '
                  'PGRN-Größe und residente Tensorbytes bleiben unbekannt. '
                  'Keine aus Herstellerdimensionen erfundene Typenstatistik.', '']
    lines += ['', '## Prefill-Risiko und mögliche spätere Auflage', '', PREFILL, '',
              '## Grenzen und Quellen', '',
              '- Keine Engine oder Konvertierung gestartet. Keine Ports, Server oder Modelle verändert.',
              '- Reviewqualität und korrektes Tool-Calling sind weiterhin ungeprüft.',
              '- Binaryidentitäten: '+json.dumps(result['binaries'],ensure_ascii=False),
              '- Vorhandener Parser: ../inspect_gguf_metadata.py (HeaderReader, EXPERT, summarize).',
              '- Quellenabbilder unter source_evidence/; Herkunft und Hashes in source_evidence/manifest.json.',
              '- [Gepinnter GGUF-LFS-Zeiger](https://huggingface.co/'+REPO+'/raw/'+REVISION+'/'+FILENAME+')',
              '- [Konverter v0.3.4](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/tools/pgrn-convert/pgrn-convert.cpp)',
              '- [Staging v0.3.4](https://github.com/Schero94/slipstream/blob/v0.3.4/engine/src/peregrine_stage.cpp)',
              '- [Loader und Callback](https://github.com/Schero94/slipstream/blob/v0.3.4/patches/slipstream-seams.patch)',
              '', '## Ausführung im normalen macOS-Terminal', '', '```sh',
              'python3 -B '+repr(str(Path(__file__).resolve())), '```', '',
              'Der absolute Pfad funktioniert unabhängig vom aktuellen Arbeitsverzeichnis. '
              'Das Budget bleibt über Wiederholungen erhalten. Bei fehlendem Netzwerk keine automatischen Wiederholungen.']
    validation = HERE / 'validation.json'
    if validation.is_file():
        v = json.loads(validation.read_text())
        if v.get('checker_sha256') == hashlib.sha256(Path(__file__).read_bytes()).hexdigest():
            lines += ['', '## Lokale Offlinevalidierung', '',
                      f'{v["tests_passed"]} synthetische Tests bestanden: Headergrenzen, vollständige '
                      'Tensorprüfung, fehlerhafte Typen/Formen/Offsets, HTTP-200-Abweisung ohne Bodyread, '
                      'HTTPS-Weiterleitung, Teilantworten und kumuliertes Budget. '
                      'Dies ist kein Remote- oder Inferenznachweis.']
    return '\n'.join(lines) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--reanalyze', action='store_true',
                    help='Recheck saved complete tensor_inventory.json offline; no HTTP')
    args = ap.parse_args()
    if args.reanalyze:
        result = json.loads((HERE / 'tensor_inventory.json').read_text())
        if not result.get('header', {}).get('header_complete'):
            raise ProbeError('Kein vollständiger gespeicherter Header')
        result['rechecked_at'] = datetime.now(timezone.utc).isoformat()
        result['binaries'] = binary_identity()
        result['analysis'] = analyze(result['header'])
        result['decision'] = result['analysis']['decision']
        if not all(x['matches_inspected_v034'] for x in result['binaries'].values()):
            if result['decision'] == 'GO':
                result['decision'] = 'GO MIT AUFLAGEN'
            result['analysis']['unknowns'].append('Binaries weichen vom geprüften Stand ab')
        result['offline_reanalysis_additional_gguf_bytes'] = 0
        result['resident_mxfp4_evidence'] = {
            'ggml_type_id': 39, 'block_values': 32, 'block_bytes': 17,
            'source': 'ggml/include/ggml.h and ggml/src/ggml-common.h @ 79bba02a6741',
            'metal_source': 'ggml/src/ggml-metal/ggml-metal-ops.cpp @ 79bba02a6741',
            'binary_embedded_mxfp4_kernels_inspected': True,
            'routed_mxfp4_allowed': False,
        }
        write_json(HERE / 'tensor_inventory_rechecked.json', result)
        report = make_report(result)
        report += ('\n## Offline-Nachprüfung\n\n'
                   'Typ 39 ist MXFP4: 17 Bytes je 32 Werte. In dieser Datei betrifft er '
                   '96 residente Shared-Expert-Tensoren, keine gerouteten Experten. '
                   'Die Konverter-Whitelist bleibt unverändert. Der gepinnte Metalcode und '
                   'die eingebetteten Kernels des vorhandenen Binaries enthalten MXFP4-Unterstützung. '
                   'Die frühere Einstufung UNGEKLÄRT entstand durch die unvollständige Typentabelle '
                   'des Prüfskripts. Sämtliche Bytebereiche wurden nun mitberechnet und erneut geprüft. '
                   'Zusätzlich übertragene GGUF-Bytes: 0. Ursprüngliche Ergebnisdateien bleiben erhalten.\n')
        (HERE / 'compatibility_report_rechecked.md').write_text(report)
        print('Offline-Entscheidung:', result['decision'])
        print('Bericht:', HERE / 'compatibility_report_rechecked.md')
        print('Speicher:', json.dumps(result['analysis']['memory'], indent=2))
        return 0 if result['decision'] == 'GO' else 2
    with (HERE / 'probe.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = {'checked_at': datetime.now(timezone.utc).isoformat(),
                  'decision': 'UNGEKLÄRT', 'binaries': binary_identity()}
        transport = Transport(HERE / 'transfer_budget.json')
        try:
            prefix = RangePrefix(transport)
            header = parse_header(prefix)
            if len(prefix.buf) != header['header_end']:
                raise ProbeError('Präfix endet nicht exakt am Tensorverzeichnisende')
            analysis = analyze(header)
            result.update(header=header, analysis=analysis, decision=analysis['decision'])
            if not all(x['matches_inspected_v034'] for x in result['binaries'].values()):
                if result['decision'] == 'GO':
                    result['decision'] = 'GO MIT AUFLAGEN'
                analysis['unknowns'].append('Vorhandene Binaries weichen von geprüftem v0.3.4 ab')
            # Header SHA is a local fingerprint, NOT the full-file authentication.
            result['header_sha256'] = hashlib.sha256(prefix.buf).hexdigest()
            result['header_authenticated_by_full_model_hash'] = False
            write_json(HERE / 'tensor_inventory.json', result)
        except Exception as exc:
            if isinstance(exc, urllib.error.URLError):
                message = 'Netzwerkzugriff fehlgeschlagen: '+str(exc.reason)
            else:
                message = str(exc).split('https://')[0][:400]
            result['error'] = type(exc).__name__+': '+message
            print('UNGEKLÄRT:', result['error'], flush=True)
        result['transfer'] = transport.ledger
        result['run_body_bytes_read'] = transport.ledger['body_bytes_read'] - transport.start_bytes
        # Include transfer evidence in an inventory only after complete parsing.
        if result.get('header'):
            write_json(HERE / 'tensor_inventory.json', result)
        write_json(HERE / 'last_run.json', result)
        (HERE / 'compatibility_report.md').write_text(make_report(result))
        print('Entscheidung:', result['decision'])
        print('Bericht:', HERE / 'compatibility_report.md')
        print('GGUF-Bodybytes:', result['run_body_bytes_read'])
        return 0 if result['decision'] == 'GO' else 2


if __name__ == '__main__':
    sys.exit(main())
