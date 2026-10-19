"""Post-answer, non-blind validation. No model text, SMTP or pipeline execution."""
import ast
import contextlib
import datetime
import io
import json
from pathlib import Path
import sys

RUN = Path(__file__).resolve().parent
ROOT = RUN.parents[1]


def main():
    results = {'at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'blind': False, 'network_smtp_keychain_used': False, 'calendar': []}
    for s in ('2026-12-29', '2027-01-01', '2026-10-19', '2026-10-20'):
        date = datetime.date.fromisoformat(s)
        iso = date.isocalendar()
        results['calendar'].append({'date': s, 'weekday': date.strftime('%A'),
            'iso_year': iso.year, 'iso_week': iso.week,
            'writer_filename': f'llm_scout_kw{iso.week}_{date.year}.md',
            'sender_filename': f'llm_scout_kw{iso.week}_{iso.year}.md'})
    assert results['calendar'][0]['iso_week'] == 53
    assert results['calendar'][1]['weekday'] == 'Friday'
    assert results['calendar'][1]['writer_filename'] == 'llm_scout_kw53_2027.md'
    assert results['calendar'][1]['sender_filename'] == 'llm_scout_kw53_2026.md'
    assert results['calendar'][2]['iso_week'] == results['calendar'][3]['iso_week']
    # Execute only the trusted frozen mode_normal definition with in-memory stubs.
    # No module imports/initialization or actual SMTP function from source executed.
    source = (ROOT/'snapshots/scripts/send_scout_email.py').read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'mode_normal')
    sends = []
    env = {'sys': sys, 'find_current_report': lambda: Path('virtual/llm_scout_kw43_2026.md'),
           'build_email_message': lambda path: ('stub', str(path)),
           'send_email_smtp': lambda message: sends.append(message)}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'frozen-mode_normal', 'exec'), env)
    with contextlib.redirect_stdout(io.StringIO()):
        codes = [env['mode_normal'](), env['mode_normal']()]
    assert codes == [0, 0] and len(sends) == 2
    results['mode_normal_twice_with_inmemory_smtp_stub'] = {'exit_codes': codes, 'send_stub_calls': len(sends)}
    results['daily_dedupe_counterexample'] = '2026-10-19 und20 sind verschiedene Tage derselben ISO-Woche2026-W43. Ein pro-Tag-Status würde beide zulassen.'
    results['overwrite_claim'] = 'Codelektüre main321-324: ohne neue Items sys.exit(0), vor Reportschreiben337. Überschreiben bei neuem Bericht möglich, nicht bei jedem zweiten Lauf.'
    (RUN/'claim-checks.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
