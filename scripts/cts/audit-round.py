#!/usr/bin/env python3
"""Cross-check a completed attempt ledger against its preserved raw events."""
from pathlib import Path
import argparse, collections, json

p = argparse.ArgumentParser()
p.add_argument('evidence', type=Path)
p.add_argument('--runtime', required=True)
a = p.parse_args()
base = a.evidence
plan = json.loads((base / 'module-plan.json').read_text())
specs = {r['module']: r for r in plan['modules']}
assert len(specs) == 377
paths = {r.parent.name:r for r in (base / 'modules').glob('*/attempt.json')}
assert set(paths) == set(specs)
events = collections.Counter()
states = collections.Counter()
boots = collections.Counter()
interruptions = []
for name, path in sorted(paths.items()):
    row = json.loads(path.read_text())
    assert row['module'] == name and row['runtime'] == a.runtime
    assert row['config_sha256'] == specs[name]['config_sha256']
    assert row['status'] not in ['RUNNING', 'NOT_ATTEMPTED']
    states[row['status']] += 1
    for runner in row['runners']:
        if not runner.get('run'):
            continue
        source = path.parent / runner['run'] / 'instrumentation-events.jsonl'
        counts = collections.Counter()
        if source.exists():
            for line in source.read_text().splitlines():
                item = json.loads(line)
                if item.get('event') == 'status' and 'test' in item.get('bundle', {}):
                    counts[{1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}.get(item['code'],'other')] += 1
        assert dict(counts) == runner.get('test_events', {}), name
        events.update(counts)
        if runner.get('boot'):
            boots[runner['boot']] += 1
        if runner.get('status') == 'DEVICE_RESTART':
            assert runner.get('recovered_after_restart') and not runner.get('cleanup_safe')
            assert (base / row['interruption_evidence']).is_file()
            interruptions.append(dict(module=name, run=runner['run'], test_events=dict(counts),
                last_started_test=row.get('last_started_test'), full_module_rerun=row.get('full_module_rerun')))
        else:
            assert runner.get('cleanup_safe') is True, name
    raw = set(p.parent.name for p in path.parent.glob('cts*/instrumentation-events.jsonl'))
    referenced = set(r['run'] for r in row['runners'] if r.get('run'))
    assert raw <= referenced, 'Orphan event streams would contaminate failure aggregation: ' + name
summary = json.loads((base / 'suite-summary.json').read_text())
assert summary['processed'] == summary['attempted'] == 377 and summary['not_attempted'] == 0
assert summary['module_states'] == dict(states)
assert summary['instrumentation_test_events'] == dict(events)
assert summary['runtime_distribution'] == {a.runtime:377}
failure = json.loads((base / 'failure-analysis.json').read_text())
assert failure['official_failed_event_count'] == events['failed'] + events['error']
result = dict(status='PASS', configurations_verified=377, runtime=a.runtime,
    module_states=dict(states), raw_events=dict(events), runner_boots=dict(boots),
    interrupted_runs=interruptions, formal_tradefed_runs=0,
    scope='Ledger integrity and truthful dispositions; not acceptance of failed, interrupted or blocked modules')
(base / 'ledger-audit.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
