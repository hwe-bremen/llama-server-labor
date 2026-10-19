"""Offline harness checks; synthetic metrics in temporary folders, no inference."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import speed_client as client
import run_comparison as manager


class FakeHTTP:
    def __init__(self,root):self.root=root;self.calls=[]
    def open(self,req,timeout):
        self.calls.append(json.loads(req.data));i=len(self.calls)
        with (self.root/'engine.log').open('a') as f:
            f.write(f'PGRN cache = 2046.03 MiB, high-water = 2136.04 MiB, hits = {i*10}, misses = {i*100} (10%)\n')
        events=[{'choices':[{'delta':{'content':'benchmark text'},'finish_reason':None}]},
                {'choices':[{'delta':{},'finish_reason':'length'}],
                 'usage':{'prompt_tokens':500,'completion_tokens':128},
                 'timings':{'cache_n':0,'prompt_n':500,'prompt_ms':1000,'prompt_per_second':500,'predicted_per_second':10}}]
        return io.BytesIO(b''.join(b'data: '+json.dumps(e).encode()+b'\n\n' for e in events)+b'data: [DONE]\n\n')


class Harness(unittest.TestCase):
    def test_fixed_requests_and_expected_length(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'engine.log').write_text('');http=FakeHTTP(root)
            with patch.object(client,'HTTP',http),patch.object(client,'io_sample',return_value={'ok':False,'error':'synthetic'}),patch.object(client,'post',side_effect=lambda path,data:{'prompt':'x'} if path=='/apply-template' else {'tokens':[1]*500}),patch.object(sys,'argv',['speed_client','--output',str(root/'responses.json')]),contextlib.redirect_stdout(io.StringIO()):
                client.main()
            records=json.loads((root/'responses.json').read_text());self.assertEqual(len(records),3)
            self.assertEqual(len(http.calls),3);self.assertTrue(all(r['bounded_request_pass'] for r in records))
            self.assertTrue(all(r['finish_reasons']==['length'] for r in records))
            self.assertTrue(all(r==http.calls[0] for r in http.calls))
            reports=[]
            for label,cache,rate in [('A2GiB',2,500),('B12GiB',12,1000)]:
                out=root/label;out.mkdir();data=json.loads(json.dumps(records))
                for r in data:r['timings']['prompt_per_second']=rate
                (out/'responses.json').write_text(json.dumps(data))
                (out/'engine.log').write_text(''.join(f'PGRN cache = {cache*1024-2}.00 MiB, high-water = {cache*1024+50}.00 MiB, hits = {i*10}, misses = {i*100} (10%)\n' for i in range(1,4)))
                reports.append((label,{'run':str(out),'command':['engine','--pgrn-cache-gb',str(cache),'--ctx-size','4096'],'inference_passed':True,'memory_before':{'swapouts':1},'memory_after':{'swapouts':1},'test_port_after':'frei','engine_exit_code':0,'lab_listeners_and_http_unchanged':True,'load_to_health_s':1}))
            result=manager.summarize(root,reports)
            self.assertTrue(result['technical_comparison_valid'])
            self.assertTrue(result['only_cache_cli_arg_differs'])
            self.assertTrue(result['all_six_outputs_identical'])
            self.assertEqual(result['ratios_B_over_A']['prompt_tps'],2)
            reports[1][1]['command'][-1]='8192'
            result=manager.summarize(root,reports)
            self.assertFalse(result['only_cache_cli_arg_differs'])
            self.assertFalse(result['technical_comparison_valid'])


if __name__=='__main__':unittest.main(verbosity=2)
