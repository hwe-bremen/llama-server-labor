#!/usr/bin/env python3
"""Read only GGUF metadata/tensor directories, never the tensor payload.

Local paths only. Does not install, convert, requantize or start an engine.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import struct

SUPPORTED_EXPERT_TYPES = {0, 1, 12, 13, 14}
TYPE_NAMES = {0: 'F32', 1: 'F16', 2: 'Q4_0', 3: 'Q4_1', 6: 'Q5_0',
              7: 'Q5_1', 8: 'Q8_0', 12: 'Q4_K', 13: 'Q5_K', 14: 'Q6_K', 30: 'BF16'}
FORMATS = {0: '<B', 1: '<b', 2: '<H', 3: '<h', 4: '<I', 5: '<i',
           6: '<f', 7: '<?', 10: '<Q', 11: '<q', 12: '<d'}
EXPERT = re.compile(r'^blk\.(\d+)\.ffn_(gate|up|down)_exps\.weight$')


class HeaderReader:
    def __init__(self, file, limit=32 * 1024 * 1024):
        self.file = file
        self.limit = limit

    def read(self, n):
        if n < 0 or self.file.tell() + n > self.limit:
            raise ValueError('Metadatenlimit überschritten')
        data = self.file.read(n)
        if len(data) != n:
            raise ValueError('Unvollständiger GGUF-Header')
        return data

    def skip(self, n):
        if n < 0 or self.file.tell() + n > self.limit:
            raise ValueError('Metadatenlimit überschritten')
        self.file.seek(n, 1)

    def number(self, fmt):
        return struct.unpack(fmt, self.read(struct.calcsize(fmt)))[0]

    def string(self, keep=True):
        n = self.number('<Q')
        if keep:
            return self.read(n).decode('utf-8')
        self.skip(n)

    def value(self, kind, keep):
        if kind in FORMATS:
            if keep:
                return self.number(FORMATS[kind])
            self.skip(struct.calcsize(FORMATS[kind]))
        elif kind == 8:
            return self.string(keep)
        elif kind == 9:
            subtype, length = self.number('<I'), self.number('<Q')
            if subtype in FORMATS:
                self.skip(struct.calcsize(FORMATS[subtype]) * length)
            else:
                for _ in range(length):
                    self.value(subtype, False)
        else:
            raise ValueError(f'Unbekannter Metadatentyp {kind}')


def inspect(path):
    path = Path(path)
    with path.open('rb') as file:
        reader = HeaderReader(file)
        if reader.read(4) != b'GGUF':
            raise ValueError('Kein GGUF')
        version = reader.number('<I')
        if version not in (2, 3):
            raise ValueError(f'Nicht unterstützte GGUF-Version {version}')
        tensor_count, metadata_count = reader.number('<Q'), reader.number('<Q')
        metadata = {}
        for _ in range(metadata_count):
            key, kind = reader.string(), reader.number('<I')
            keep = key.startswith('split.') or key in ('general.architecture', 'general.file_type')
            keep |= key.endswith(('.block_count', '.expert_count', '.expert_used_count', '.nextn_predict_layers'))
            value = reader.value(kind, keep)
            if keep:
                metadata[key] = value
        tensors = []
        for _ in range(tensor_count):
            name, dimensions = reader.string(), reader.number('<I')
            if not 1 <= dimensions <= 4:
                raise ValueError('Ungültige Tensordimension')
            shape = [reader.number('<Q') for _ in range(dimensions)]
            kind, offset = reader.number('<I'), reader.number('<Q')
            match = EXPERT.fullmatch(name)
            group = match.group(2) if match else 'shared_expert_resident' if '_shexp.' in name else 'other_resident'
            tensors.append({'name': name, 'type_id': kind, 'type': TYPE_NAMES.get(kind, str(kind)),
                            'shape': shape, 'data_offset': offset, 'streamed_expert': bool(match),
                            'group': group, 'layer': int(match.group(1)) if match else None,
                            'converter_type_accepted': kind in SUPPORTED_EXPERT_TYPES if match else None})
        header_end = file.tell()
    return {'file': str(path), 'file_size': path.stat().st_size, 'gguf_version': version,
            'metadata': metadata, 'tensor_count': tensor_count,
            'header_end': header_end, 'tensor_payload_read': False, 'tensors': tensors}


def summarize(reports):
    names = [t['name'] for r in reports for t in r['tensors']]
    duplicates = [n for n, count in Counter(names).items() if count > 1]
    groups = defaultdict(Counter)
    layers = defaultdict(list)
    for report in reports:
        for tensor in report['tensors']:
            groups[tensor['group']][tensor['type']] += 1
            if tensor['streamed_expert']:
                layers[tensor['group'] + ':' + tensor['type']].append(tensor['layer'])
    return {'groups': {g: dict(c) for g, c in groups.items()},
            'expert_layers_by_group_and_type': dict(layers), 'duplicate_tensor_names': duplicates,
            'total_tensors': len(names), 'total_streamed_expert_tensors': sum(
                t['streamed_expert'] for r in reports for t in r['tensors']),
            'all_parts_type_compatible': not any(t['streamed_expert'] and not t['converter_type_accepted']
                                              for r in reports for t in r['tensors'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    reports = [inspect(file) for file in args.files]
    result = {'parts': reports, 'summary': summarize(reports)}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
