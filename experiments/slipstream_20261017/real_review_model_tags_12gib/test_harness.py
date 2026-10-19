"""Offline tests of transport/storage only; no model or project reference review."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import review_client as client


class FakeHTTP:
    def __init__(self, finish):
        self.finish = finish
        self.payload = None

    def open(self, request, timeout):
        self.payload = json.loads(request.data)
        events = [
            {'choices': [{'delta': {'reasoning_content': 'test thought'}, 'finish_reason': None}]},
            {'choices': [{'delta': {'content': '  Originaltext\n'}, 'finish_reason': None}]},
            {'choices': [{'delta': {}, 'finish_reason': self.finish}],
             'usage': {'prompt_tokens': 2000, 'completion_tokens': 10},
             'timings': {'predicted_n': 10, 'predicted_per_second': 5.0}},
        ]
        return io.BytesIO(b''.join(b'data: '+json.dumps(e).encode()+b'\n\n' for e in events)+b'data: [DONE]\n\n')


class HarnessTests(unittest.TestCase):
    def run_fake(self, finish):
        fake = FakeHTTP(finish)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root/'responses.json'
            with patch.object(client, 'HTTP', fake), patch.object(client, 'post', side_effect=lambda path, payload:
                {'prompt': 'rendered'} if path == '/apply-template' else {'tokens': [1]*2000}), \
                patch.object(sys, 'argv', ['review_client', '--output', str(output)]), \
                contextlib.redirect_stdout(io.StringIO()):
                if finish == 'length':
                    with self.assertRaises(RuntimeError):
                        client.main()
                else:
                    client.main()
            record = json.loads(output.read_text())[0]
            self.assertEqual((root/'answer.txt').read_text(), '  Originaltext\n')
            self.assertEqual((root/'reasoning.txt').read_text(), 'test thought')
            self.assertIsNone(record['reasoning_tokens_reported'])
            self.assertEqual(record['complete'], finish == 'stop')
            self.assertEqual(record['truncated'], finish == 'length')
            self.assertEqual(len(fake.payload['messages']), 2)
            self.assertEqual(fake.payload['max_tokens'], 4096)
            self.assertFalse(fake.payload['chat_template_kwargs']['enable_thinking'])
            self.assertNotIn('tools', fake.payload)
            self.assertEqual(len(list(root.glob('request.json'))), 1)

    def test_complete_storage(self):
        self.run_fake('stop')

    def test_truncated_no_retry(self):
        self.run_fake('length')


if __name__ == '__main__':
    unittest.main(verbosity=2)
