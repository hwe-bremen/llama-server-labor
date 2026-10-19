"""Non-blind checks authored after reading Qwen. Never executes model output."""
import datetime
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    result = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'blind': False, 'qwen_answer_already_read': True,
              'existing_tests': {}, 'behavior_checks': []}
    for version in ('base', 'target'):
        path = ROOT/'snapshots'/version/'role-split'
        proxy = load('role_proxy', path/'role_proxy.py')
        tests = load('snapshot_tests_'+version, path/'test_role_proxy.py')
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(cls)
                                   for cls in (tests.TriggerTests, tests.ModelTests))
        log = io.StringIO()
        run = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
        (RUN/(version+'-existing-tests.txt')).write_text(log.getvalue())
        result['existing_tests'][version] = {'run': run.testsRun,
            'failures': len(run.failures), 'errors': len(run.errors),
            'success': run.wasSuccessful(),
            'excluded': 'RoleFileTests require roles fixtures absent from pinned snapshot; ProxyIntegrationTests bind sockets. Neither relevant integration nor full suite claimed.'}
    # Handwritten comparisons, independent of executing or trusting any generated text.
    proxy = sys.modules['role_proxy']
    examples = [
        ('JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF', 'mellum2-12b'),
        ('unsloth/Qwen3.6-27B-MTP-GGUF', 'qwen36-27b'),
        ('unsloth/Qwen3.8-27B-GGUF', 'qwen38-27b'),
        ('unsloth/gemma-4-26B-A4B-it-GGUF', 'gemma4-26b'),
        ('unsloth/gemma-4-31B-it-GGUF', 'gemma4-31b'),
        ('jondale/Apertus-8B-Instruct-2509-GGUF:Q4_K_M', 'apertus-8b'),
        ('mistral-7b', 'mistral-7b'),
        ('mistral-0.1b', 'mistral-01b'),
        ('phi-3.1', 'phi31'),
        ('foo-10B-20B-test', 'foo10b20btest'),
        ('foo-1.5b-2.0b', 'foo15b20b'),
        ('vendor/Devstral-24B-GGUF:Q4_K_M', 'devstral-24b'),
    ]
    for model, expected in examples:
        actual = proxy.model_tag(model)
        result['behavior_checks'].append({'model': model, 'actual': actual,
                                          'expected': expected, 'pass': actual == expected})
        assert actual == expected, (model, actual, expected)
    for model in (None, '', 'default', 12):
        assert proxy.model_line(model) == ''
    result['model_line_guards_pass'] = True
    result['expert_size_regex'] = {'mellum_matches': proxy._SIZE_RE.findall('mellum2-12b-a2.5b'),
                                  'gemma_matches': proxy._SIZE_RE.findall('gemma-4-26b-a4b-it-gguf')}
    assert result['expert_size_regex']['mellum_matches'] == ['12']
    assert result['expert_size_regex']['gemma_matches'] == ['26']
    (RUN/'reference-checks.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    assert all(r['success'] for r in result['existing_tests'].values())


if __name__ == '__main__':
    main()
