#!/usr/bin/env python3
"""Rebuild module status from preserved raw events, without rerunning tests.
Never upgrades an interrupted run, failed preparation, or a missing callback.
The original attempt remains preserved as an audit backup.
"""
from pathlib import Path
import json,argparse,collections
from instrumentation_outcome import inspect_finish
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);p.add_argument('--write',action='store_true');a=p.parse_args();summary=collections.Counter();changes=[]
for path in sorted((a.evidence/'modules').glob('*/attempt.json')):
 attempt=json.loads(path.read_text());before=json.dumps(attempt,sort_keys=True);runners=attempt['runners']
 rawdirs=sorted(path.parent.glob('cts*/run-result.json'))
 for raw in rawdirs:
  data=json.loads(raw.read_text());run=data['run'];row=next((r for r in runners if r.get('run')==run),None)
  if row is None:
   row=dict(type='preserved-instrumentation-evidence',run=run,package=data.get('package'));runners.append(row)
  row.update(status=data['status'],pid=data.get('pid'),runtime=data.get('runtime'),boot=data.get('boot'),cleanup_safe=data.get('brightness')=='0'and data.get('boot_unchanged')and data.get('lipstick_unchanged')and data.get('daily_root_unchanged')and not any(data.get(k)for k in ['cleanup_error','cleanup_timeout','cleanup_process_alive'])and all(data.get(k,{}).get('ready',True)for k in ['compositor_before','compositor_after']))
  for key in ['compositor_before','compositor_after']:
   if key in data:row[key]=data[key]
  if not row['cleanup_safe']:row['status']='BLOCKED_CLEANUP'
  events=raw.parent/'instrumentation-events.jsonl';counts=collections.Counter()
  if events.exists():
   for line in events.read_text().splitlines():
    e=json.loads(line)
    if e['event']=='status'and'test'in e['bundle']:counts[{1:'started',0:'passed',-1:'error',-2:'failed',-3:'ignored',-4:'assumption'}.get(e['code'],'other')]+=1
  row['test_events']=dict(counts)
  if row['status']=='COMPLETED'and not counts:row['status']='NO_TESTS'
  if data.get('instrumentation'):row['finish']=data['instrumentation']
  row['run_outcome']=inspect_finish(data.get('instrumentation'),counts)
  row.pop('reason',None);row.pop('exit',None)
  if row['status']=='NO_TESTS':row['reason']='Runner finished without any individual test status; no test execution is claimed'
 states={r['status']for r in runners}
 if attempt['status']=='RUNNING'and not rawdirs:summary['INTERRUPTED']+=1;continue
 if states=={'COMPLETED'}:
  attempt['status']='FAILED'if any(r['test_events'].get('failed',0)or r['test_events'].get('error',0)or r.get('run_outcome',{}).get('has_failures')for r in runners)else'EXECUTED'
 elif states=={'EXECUTED'}:attempt['status']='NATIVE_HOST_EXECUTED'
 elif states=={'NO_TESTS'}:attempt['status']='NO_TESTS'
 elif states=={'BLOCKED'}:attempt['status']='BLOCKED'
 elif states:attempt['status']='ATTEMPTED_WITH_FAILURES'
 if attempt.get('reason','').startswith('Device cleanup/identity'):attempt.pop('reason',None);attempt.pop('traceback',None)
 summary[attempt['status']]+=1
 if json.dumps(attempt,sort_keys=True)!=before:
  changes.append(attempt['module'])
  if a.write:
   backup=path.with_name('attempt-before-reconciliation.json')
   if not backup.exists():backup.write_bytes(path.read_bytes())
   pending=path.with_suffix('.reconciled');pending.write_text(json.dumps(attempt,indent=2)+'\n');pending.replace(path)
print(json.dumps(dict(changed=len(changes),states=dict(summary),modules=changes),indent=2))
