#!/usr/bin/env python3
"""Keep raw JUnit failures and distinguish adapter prerequisites from API assertions."""
from pathlib import Path
import argparse,json,collections
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);a=p.parse_args();ev=a.evidence
inputs=[('util','cts-util-r114-4'),('os','cts-os-r114-3')];rows=[];totals=collections.Counter()
for module,run in inputs:
 value=json.loads((ev/run/'result.json').read_text())
 if 'blocked'in value:raise RuntimeError(value['blocked'])
 for cls in value['classes']:
  for failure in cls.get('details',[]):
   test,trace=failure['test'],failure['trace'];kind='FAIL';reason='official assertion/exception'
   if cls['class']=='android.util.cts.DisplayMetricsTest'and 'Context'in trace:kind='BLOCKED';reason='CTS test Context was not injected by the full instrumentation runner'
   if cls['class']=='android.os.cts.ParcelTest'and any(s in test for s in ['testExceptionOverwritesObject','testObjectDoubleFree']):kind='BLOCKED';reason='Requires CTS-declared helper Service/target-package Context'
   if cls['class']=='android.os.cts.BuildVersionTest'and 'testReleaseVersion'in test:kind='BLOCKED';reason='Requires official CTS expected-release asset in target-package Context'
   if 'initializationError'in test:kind='BLOCKED';reason='JUnit runner initialization; no API assertion ran'
   rows.append(dict(module=module,run=run,test=test,status=kind,reason=reason,trace=trace));totals[kind]+=1
  totals['PASS']+=cls.get('run',0)-cls.get('failures',0)-cls.get('ignored',0);totals['IGNORED']+=cls.get('ignored',0)
summary=dict(formal_cts_status='BLOCKED',formal_cts_test_count=0,diagnostic_adapter='direct-junit-diagnostic-not-cts-certification',diagnostic_counts=dict(totals),diagnostic_record_count=sum(totals.values()),r114_promoted=False,daily_release='r112-native-candidate',excluded_blocked_classes=[dict(test='android.os.cts.BinderTest',run='cts-os-r114-2',status='BLOCKED',reason='Helper-component setup did not complete within bounded 120-second window; raw log retained')],details=rows)
(ev/'diagnostic-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items()if k!='details'},indent=2))
