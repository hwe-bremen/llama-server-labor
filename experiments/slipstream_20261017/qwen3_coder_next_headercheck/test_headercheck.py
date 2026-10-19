"""Offline safety/geometry tests: no real model, network, engine or converter."""
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from email.message import Message
import urllib.request

import check_qwen3_coder_next as p


def string(s):
    b = s.encode()
    return struct.pack('<Q', len(b)) + b


def fixture(modify=None, unknown_metadata=False):
    metadata = [
        ('general.architecture', 8, 'qwen3next'),
        ('general.alignment', 4, 32),
        ('qwen3next.block_count', 4, 2),
        ('qwen3next.expert_count', 4, 4),
        ('qwen3next.expert_used_count', 4, 2),
        ('qwen3next.embedding_length', 4, 256),
        ('qwen3next.expert_feed_forward_length', 4, 256),
        ('tokenizer.chat_template', 8, '{{ messages }}'),
        ('tokenizer.ggml.tokens', 9, (8, ['abc'] * 1000)),
        ('qwen3next.attention.recurrent_layers', 9, (7, [True, False])),
        ('qwen3next.attention.head_count_kv', 4, 2),
        ('qwen3next.attention.key_length', 4, 128),
        ('qwen3next.attention.value_length', 4, 128),
    ]
    ts = []
    offset = 0
    for layer in range(2):
        for role in ('gate', 'up', 'down'):
            ts.append({'name': f'blk.{layer}.ffn_{role}_exps.weight',
                       'shape': [256, 256, 4], 'type_id': 12, 'offset': offset})
            offset += 256 * 256 * 4 // 256 * 144
    ts.append({'name': 'blk.0.ffn_gate_shexp.weight', 'shape': [256,256],
               'type_id': 30, 'offset': offset})
    offset += 256*256*2
    if modify:
        modify(metadata, ts)
    b = b'GGUF' + struct.pack('<IQQ', 3, len(ts), len(metadata))
    for key, kind, value in metadata:
        b += string(key) + struct.pack('<I', kind)
        if unknown_metadata and key == 'general.architecture':
            b = b[:-4] + struct.pack('<I', 999)
            return b, offset
        if kind == 8:
            b += string(value)
        elif kind == 9:
            sub, vals = value
            b += struct.pack('<IQ', sub, len(vals))
            for v in vals:
                b += string(v) if sub == 8 else struct.pack(p.FORMATS[sub], v)
        else:
            b += struct.pack(p.FORMATS[kind], value)
    for t in ts:
        b += string(t['name']) + struct.pack('<I', len(t['shape']))
        b += b''.join(struct.pack('<Q', n) for n in t['shape'])
        b += struct.pack('<IQ', t['type_id'], t['offset'])
    return b, ((len(b)+31)//32*32) + offset


class Response:
    def __init__(self, body, status=206, start=0, size=p.SIZE, content_length=None):
        self.status = status
        self.body = io.BytesIO(body)
        self.read_calls = 0
        self.headers = Message()
        self.headers['Content-Range'] = f'bytes {start}-{start+len(body)-1}/{size}'
        self.headers['Content-Length'] = str(len(body) if content_length is None else content_length)

    def read(self, n):
        self.read_calls += 1
        return self.body.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class Opener:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def open(self, req, timeout):
        self.calls.append(req)
        return self.response


class FakeRanges:
    def __init__(self, header):
        self.header = header
        self.requests = []

    def fetch(self, start, count):
        if start + count > len(self.header):
            raise AssertionError('Tensor payload would be requested')
        self.requests.append((start,count))
        return self.header[start:start+count]


class Tests(unittest.TestCase):
    def test_complete_header_and_exact_no_payload_prefetch(self):
        raw, size = fixture()
        ranges = FakeRanges(raw)
        stream = p.RangePrefix(ranges)
        h = p.parse_header(stream)
        a = p.analyze(h, size)
        self.assertEqual(a['decision'], 'GO')
        self.assertEqual(h['header_end'], len(raw))
        self.assertEqual(len(stream.buf), len(raw))
        self.assertEqual(sum(n for _,n in ranges.requests), len(raw))
        self.assertEqual(a['summary']['total_streamed_expert_tensors'],6)
        self.assertEqual(h['metadata']['tokenizer.chat_template'],'{{ messages }}')
        self.assertEqual(a['memory']['routed_tensor_payload_bytes'],6*147456)
        self.assertEqual(a['pgrn']['header_reserved_bytes'],16384)
        self.assertEqual(a['pgrn']['padding_bytes'],32768)
        self.assertTrue(a['pgrn']['header_fits'])

    def test_late_unsupported_expert_not_a_sample(self):
        def bad(m, ts):
            ts[-2]['type_id'] = 8
        raw,size = fixture(bad)
        a = p.analyze(p.parse_header(io.BytesIO(raw)), size+1000000)
        self.assertEqual(a['decision'],'NO-GO')
        self.assertTrue(any('Expertentyp 8' in x for x in a['blockers']))

    def test_large_metadata_controlled_ranges_do_not_cross_header_end(self):
        def large(m,ts):
            m.append(('large.synthetic.metadata',8,'x'*(3*p.CHUNK+17)))
        raw,size=fixture(large)
        ranges=FakeRanges(raw)
        stream=p.RangePrefix(ranges)
        h=p.parse_header(stream)
        self.assertEqual(sum(n for _,n in ranges.requests),len(raw))
        self.assertEqual(len(stream.buf),len(raw))
        self.assertGreater(len(ranges.requests),3)
        self.assertEqual(p.analyze(h,size)['decision'],'GO')

    def test_unknown_resident_type_cannot_produce_go(self):
        def unknown(m,ts):ts[-1]['type_id']=999
        raw,size=fixture(unknown)
        a=p.analyze(p.parse_header(io.BytesIO(raw)),size)
        self.assertEqual(a['decision'],'UNGEKLÄRT')
        self.assertIsNone(a['memory'])

    def test_mxfp4_resident_allowed_but_routed_still_rejected(self):
        def resident(m,ts):ts[-1]['type_id']=39
        raw,size=fixture(resident)
        a=p.analyze(p.parse_header(io.BytesIO(raw)),size)
        self.assertEqual(a['decision'],'GO')
        self.assertEqual(a['summary']['groups']['shared_expert_resident']['MXFP4'],1)
        self.assertEqual(a['memory']['resident_tensor_payload_bytes'],256*256//32*17)
        def routed(m,ts):ts[0]['type_id']=39
        raw,size=fixture(routed)
        a=p.analyze(p.parse_header(io.BytesIO(raw)),size)
        self.assertEqual(a['decision'],'NO-GO')
        self.assertTrue(any('Expertentyp 39' in x for x in a['blockers']))

    def test_fused_name_and_missing_triplet(self):
        def bad(m,ts):
            ts[0]['name']='blk.0.ffn_gate_up_exps.weight'
        raw,size=fixture(bad)
        a=p.analyze(p.parse_header(io.BytesIO(raw)),size)
        self.assertEqual(a['decision'],'NO-GO')
        self.assertTrue(any('fusionierter' in x for x in a['blockers']))

    def test_bad_expert_count_and_overlap(self):
        def bad(m,ts):
            ts[-2]['shape'][-1]=3
            ts[1]['offset']=0
        raw,size=fixture(bad)
        a=p.analyze(p.parse_header(io.BytesIO(raw)),size)
        self.assertTrue(any('gestapelt' in x for x in a['blockers']))
        self.assertTrue(any('Überlappende' in x for x in a['blockers']))

    def test_block_alignment_split_and_out_of_file(self):
        def bad(m,ts):
            m.append(('split.count',2,2))
            ts[0]['shape'][0]=1408
            ts[1]['offset']=p.SIZE
        raw,size=fixture(bad)
        a=p.analyze(p.parse_header(io.BytesIO(raw)),size)
        for phrase in ('Blockbreite','Geteilte','Dateigrenze'):
            self.assertTrue(any(phrase in x for x in a['blockers']))

    def test_unknown_metadata_and_truncation_fail(self):
        raw,_=fixture(unknown_metadata=True)
        with self.assertRaises(ValueError):
            p.parse_header(io.BytesIO(raw))
        raw,_=fixture()
        with self.assertRaises(ValueError):
            p.parse_header(io.BytesIO(raw[:-1]))

    def test_200_never_read(self):
        with tempfile.TemporaryDirectory() as d:
            r=Response(b'x'*24,status=200)
            t=p.Transport(Path(d)/'budget.json',Opener(r))
            with self.assertRaises(RuntimeError):
                t.fetch(0,24)
            self.assertEqual(r.read_calls,0)
            self.assertEqual(t.ledger['body_bytes_read'],0)

    def test_wrong_total_encoding_and_content_length_never_read(self):
        for mode in ('size','encoding','length'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                r=Response(b'x'*24,size=1 if mode=='size' else p.SIZE,
                           content_length=25 if mode=='length' else 24)
                if mode=='encoding':r.headers['Content-Encoding']='gzip'
                t=p.Transport(Path(d)/'budget.json',Opener(r))
                with self.assertRaises(RuntimeError):t.fetch(0,24)
                self.assertEqual(r.read_calls,0)

    def test_valid_range_persistent_budget_and_limit(self):
        with tempfile.TemporaryDirectory() as d:
            ledger=Path(d)/'budget.json'
            t=p.Transport(ledger,Opener(Response(b'GGUF'+b'0'*20)))
            self.assertEqual(len(t.fetch(0,24)),24)
            t2=p.Transport(ledger,Opener(Response(b'GGUF'+b'0'*20)))
            self.assertEqual(t2.ledger['body_bytes_read'],24)
            t2.ledger['reserved_bytes']=p.BUDGET-23
            with self.assertRaises(p.ProbeError):t2.fetch(0,24)
            self.assertEqual(len(t2.opener.calls),0)

    def test_short_body_is_accounted_and_aborts(self):
        with tempfile.TemporaryDirectory() as d:
            r=Response(b'GGUF'+b'0'*20)
            r.body=io.BytesIO(b'GGUF')
            t=p.Transport(Path(d)/'budget.json',Opener(r))
            with self.assertRaises(p.ProbeError):t.fetch(0,24)
            self.assertEqual(t.ledger['body_bytes_read'],4)
            self.assertEqual(t.ledger['reserved_bytes'],24)

    def test_https_redirect_preserves_range_and_does_not_drain_body(self):
        h=p.HttpsOnly()
        req=urllib.request.Request(p.URL,headers={'Range':'bytes=0-23','Accept-Encoding':'identity'})
        req.timeout=30
        response=Response(b'not metadata',status=302)
        response.close=lambda:None
        response.headers['Location']='https://cdn.example/model'
        class Parent:
            def open(self,new,timeout):
                self.request=new
                return 'redirected'
        parent=Parent();h.parent=parent
        self.assertEqual(h.http_error_302(req,response,302,'redirect',response.headers),'redirected')
        self.assertEqual(response.read_calls,0)
        self.assertEqual(parent.request.get_header('Range'),'bytes=0-23')
        self.assertEqual(parent.request.get_header('Accept-encoding'),'identity')
        with self.assertRaises(p.ProbeError):
            h.redirect_request(req,response,302,'redirect',response.headers,'http://cdn.example/model')

    def test_prefill_counterexample_vs_safe_ubatch(self):
        self.assertLessEqual(len(set(range(25*10))),256)
        self.assertGreater(len(set(range(26*10))),256)


if __name__=='__main__':
    unittest.main(verbosity=2)
