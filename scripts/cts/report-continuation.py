#!/usr/bin/env python3
"""Audit the latest continuation attempts without merging candidate versions."""
from pathlib import Path
import argparse,collections,datetime,json
from instrumentation_outcome import inspect_finish
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);a=p.parse_args();base=a.evidence
rows=[];totals=collections.Counter();by_release=collections.defaultdict(collections.Counter)
for path in sorted((base/'modules').glob('*/attempt.json')):
 value=json.loads(path.read_text());runners=[];counts=collections.Counter()
 for runner in value.get('runners',[]):
  events=runner.get('test_events',{});counts.update(events);outcome=inspect_finish(runner.get('finish'),events)
  accepted=runner.get('status')=='COMPLETED'and runner.get('cleanup_safe')is True and outcome['callback_present']and not outcome['has_failures']and not(events.get('failed',0)+events.get('error',0))and events.get('started',0)>0 and events.get('started',0)==sum(events.get(k,0)for k in ['passed','failed','error','ignored','assumption'])
  runners.append(dict(run=runner.get('run'),status=runner.get('status'),accepted=accepted,test_events=events,finish=outcome,cleanup_safe=runner.get('cleanup_safe')))
 accepted=value['status']=='EXECUTED'and bool(runners)and all(r['accepted']for r in runners)
 row=dict(module=value['module'],release=value['runtime'],status=value['status'],config_sha256=value['config_sha256'],complete_original_apk_execution_accepted=accepted,formal_tradefed_accepted=False,counts=dict(counts),runners=runners)
 rows.append(row)
 if accepted:totals['accepted_complete_apk_modules']+=1;totals['accepted_test_pass_events']+=counts['passed'];by_release[value['runtime']]['modules']+=1;by_release[value['runtime']]['pass_events']+=counts['passed']
 elif value['status']=='RUNNING':totals['running_modules']+=1
 else:totals['other_attempts']+=1
report=dict(scope='Latest continuation attempts only; mixed release results remain separate; not CTS certification or aggregate API coverage',generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_tradefed_runs=0,totals=dict(totals),accepted_by_release=dict(by_release),note='RUNNING attempts have no final acceptance. Intermediate event counts are not complete-module results. Historical ledgers and earlier summaries are retained unchanged.',modules=rows)
(base/'continuation-progress.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='modules'},indent=2))
