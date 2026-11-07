#!/usr/bin/env python3
"""Aggregate preserved official event failures without changing their status."""
from pathlib import Path
import json,argparse,collections,re
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);a=p.parse_args();groups={};total=0;unfinished=[]
for module in sorted((a.evidence/'modules').iterdir()):
 if not module.is_dir():continue
 attempt=module/'attempt.json'
 if not attempt.is_file():continue
 row=json.loads(attempt.read_text())
 for source in module.glob('cts*/instrumentation-events.jsonl'):
  for line in source.read_text().splitlines():
   e=json.loads(line);bundle=e.get('bundle',{})
   if e.get('event')!='status'or e.get('code')not in[-1,-2]:continue
   stack=bundle.get('stack','');heading=stack.splitlines()[0]if stack else str(bundle.get('stream','(no exception stack)')).splitlines()[0]
   frame=next((l.strip()for l in stack.splitlines()if l.strip().startswith('at ')and not any(s in l for s in ['org.junit.','junit.framework.','java.lang.reflect.','androidx.test.internal.'])),'')
   key=heading.split(':',1)[0]+'|'+re.sub(r':\d+\)',')',frame)
   group=groups.setdefault(key,dict(exception=heading.split(':',1)[0],first_frame=frame,count=0,modules=collections.Counter(),examples=[]));group['count']+=1;group['modules'][module.name]+=1;total+=1
   if len(group['examples'])<3:group['examples'].append(dict(test=str(bundle.get('class')or'')+'#'+str(bundle.get('test')or''),message=heading,source=str(source.relative_to(a.evidence))))
 for r in row['runners']:
  if r['status']not in['COMPLETED','BLOCKED']:unfinished.append(dict(module=module.name,status=r['status'],reason=r.get('reason'),test_events=r.get('test_events',{})))
values=sorted(groups.values(),key=lambda v:-v['count'])
for value in values:value['modules']=dict(value['modules'])
result=dict(official_failed_event_count=total,distinct_failure_groups=len(values),groups=values,unfinished_runners=unfinished,note='Failure frequency is for tests actually attempted under this compatibility adapter; it is not an Android API completeness score.')
(a.evidence/'failure-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(failed_events=total,groups=len(values),top=[dict(exception=v['exception'],frame=v['first_frame'],count=v['count'])for v in values[:12]]),indent=2))
