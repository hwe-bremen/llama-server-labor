"""Offline integrity checks using synthetic PGRN records; no model/network/processes."""
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

import check_qwen3_coder_next as check
import download_convert_qwen3_coder_next as pipeline
from test_headercheck import fixture


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'synthetic.pgrn'
        raw, size = fixture()
        h = check.parse_header(io.BytesIO(raw))
        a = check.analyze(h, size)
        self.inventory = {'header':h,'analysis':a}
        roles = {}
        for t in h['tensors']:
            if t['streamed_expert']:
                roles.setdefault(t['layer'],{})[t['group']] = t
        layout = {}; payload = bytearray(); directory = bytearray()
        for layer, tensors in sorted(roles.items()):
            cursor = 0; layout[str(layer)] = {}
            for role in ('gate','up','down'):
                t = tensors[role]; per = t['nbytes']//a['expert_count']
                layout[str(layer)][role] = dict(offset=cursor,nbytes=per,ggml_type=t['type_id'])
                cursor += per
            for expert in range(a['expert_count']):
                record = bytes([layer+expert+1])*cursor
                offset = 16384+len(payload)
                directory += struct.pack('<HHBBfQII',layer,expert,1,0,0.,offset,cursor,zlib.crc32(record))
                payload += record+bytes((-cursor)%16384)
        self.meta = {'metadata':{'model_sha256':check.SHA256,'source_size':check.SIZE,
                                'source_format':'GGUF','geometry':{'layers_with_experts':len(roles),
                                'experts_per_layer':a['expert_count']},'record_layout_by_layer':layout},
                     'expert_count':len(directory)//26,'expert_dir_offset':16384+len(payload)}
        encoded = json.dumps(self.meta).encode()
        header = b'PGRN1\0\0\0'+struct.pack('<II',1,len(encoded))+encoded
        self.data = header+bytes(16384-len(header))+payload+directory
        self.path.write_bytes(self.data)

    def test_complete_crc_and_sha(self):
        result = pipeline.validate_pgrn(self.path,self.inventory,False)
        self.assertTrue(result['all_record_crcs_verified'])
        self.assertEqual(result['record_count'],8)
        self.assertEqual(result['sha256'],hashlib.sha256(self.data).hexdigest())

    def test_payload_corruption_rejected(self):
        data = bytearray(self.data); data[16384] ^= 1
        self.path.write_bytes(data)
        with self.assertRaisesRegex(RuntimeError,'CRC'):
            pipeline.validate_pgrn(self.path,self.inventory,False)

    def test_directory_corruption_rejected(self):
        data = bytearray(self.data); data[self.meta['expert_dir_offset']] = 99
        self.path.write_bytes(data)
        with self.assertRaisesRegex(RuntimeError,'Verzeichniseintrag'):
            pipeline.validate_pgrn(self.path,self.inventory,False)

    def test_wrong_source_rejected(self):
        data = self.data.replace(check.SHA256.encode(),b'0'*64,1)
        self.path.write_bytes(data)
        with self.assertRaisesRegex(RuntimeError,'Quellenidentität'):
            pipeline.validate_pgrn(self.path,self.inventory,False)

    def test_space_reserves(self):
        with self.assertRaises(RuntimeError):
            pipeline.check_space(pipeline.RESERVE-1,10**12,0,0)


if __name__ == '__main__':
    unittest.main()
