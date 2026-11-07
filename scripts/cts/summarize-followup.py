#!/usr/bin/env python3
"""Audit selected follow-up runs without presenting them as a full CTS round."""
from pathlib import Path
import argparse,collections,json
from instrumentation_outcome import inspect_finish
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--candidate',required=True);a=p.parse_args();base=a.evidence
rows=[]
labels={1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}
for path in sorted((base/'modules').glob('*/attempt.json')):
 value=json.loads(path.read_text());assert value['status']!='RUNNING'
 runners=[]
 for runner in value['runners']:
  count=collections.Counter()
  if runner.get('run'):
   directory=path.parent/runner['run'];source=directory/'instrumentation-events.jsonl'
   if source.exists():
    for line in source.read_text().splitlines():
     event=json.loads(line)
     if event.get('event')=='status'and'test'in event.get('bundle',{}):count[labels.get(event['code'],'other')]+=1
   assert dict(count)==runner.get('test_events',{}),value['module']
   result=json.loads((directory/'run-result.json').read_text())
   assert result['compositor_before']['ready']and result['compositor_after']['ready'],value['module']
   assert result['brightness']=='0'and result['boot_unchanged']and result['lipstick_unchanged']and result['daily_root_unchanged']
   assert not any(result.get(k)for k in ['cleanup_error','cleanup_timeout','cleanup_process_alive'])
  outcome=inspect_finish(runner.get('finish'),count)
  assert not(value['status']=='EXECUTED'and outcome['has_failures']),value['module']
  runners.append(dict(status=runner['status'],run=runner.get('run'),test_events=dict(count),run_outcome=outcome,compositor_before=runner.get('compositor_before'),compositor_after=runner.get('compositor_after')))
 rows.append(dict(module=value['module'],runtime=value['runtime'],module_disposition=value['status'],original_config_sha256=value['config_sha256'],limits=value.get('attempt_limits'),runners=runners))
gates=[]
for path in sorted((base/'gates').glob('*/summary.json')):
 value=json.loads(path.read_text())
 # Historical failed candidates remain separate, and do not contribute to
 # arithmetic changes in the original full-cohort ledger.
 gates.append(dict(path=str(path.relative_to(base)),**value))
health=json.loads((base/'final-health.json').read_text())if(base/'final-health.json').exists()else None
if health:assert health['status']=='PASS'and health['candidate']==a.candidate
result=dict(scope='Selected affected-module follow-up, not a full 377-module rerun or CTS certificate',formal_tradefed_runs=0,candidate=a.candidate,original_round2_ledger_unchanged=True,selected_module_count=len(rows),modules=rows,diagnostic_selections=gates,frame_followup=json.loads((base/'frame-followup.json').read_text()),device_health=health,note='Runtime identity is per row; partial and failed runs remain explicit. Selected diagnostic class subsets never replace complete-module results.')
(base/'followup-summary.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(scope=result['scope'],selected_module_count=len(rows),candidate=a.candidate,modules=rows,device_health=health),indent=2))
