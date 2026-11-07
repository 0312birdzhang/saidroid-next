#!/usr/bin/env python3
"""Compare actual terminal test events, preserving added/lost/skipped cases."""
from pathlib import Path
import argparse,collections,json
p=argparse.ArgumentParser();p.add_argument('before',type=Path);p.add_argument('after',type=Path);a=p.parse_args()
labels={0:'PASS',-1:'ERROR',-2:'FAIL',-3:'IGNORE',-4:'ASSUMPTION'}
def read(base):
 cases={};modules={};evidence={};unidentified=collections.Counter()
 for file in sorted((base/'modules').glob('*/attempt.json')):
  row=json.loads(file.read_text());modules[row['module']]=row
  for runner_index,runner in enumerate(row['runners']):
   if not runner.get('run'):continue
   events=file.parent/runner['run']/'instrumentation-events.jsonl'
   if not events.exists():continue
   occurrences=collections.Counter()
   for line in events.read_text().splitlines():
    event=json.loads(line);bundle=event.get('bundle',{});code=event.get('code')
    if event.get('event')!='status'or code not in labels:continue
    if not bundle.get('test')or not bundle.get('class'):
     unidentified[labels[code]]+=1;continue
    name=(row['module'],runner_index,runner.get('type'),runner.get('package'),bundle['class'],bundle['test']);ordinal=occurrences[name];occurrences[name]+=1;key=(*name,ordinal)
    assert key not in cases,'Ambiguous duplicate case identity '+str(key)
    cases[key]=labels[code]
    evidence[key]=dict(source=str(events.relative_to(base)),stack=bundle.get('stack'),stream=bundle.get('stream'))
 return cases,modules,evidence,unidentified
before,old,old_evidence,old_unidentified=read(a.before);after,new,new_evidence,new_unidentified=read(a.after);assert len(old)==len(new)==377
assert all(row['status']!='RUNNING'for row in new.values())
for name,row in new.items():
 assert old[name]['config_sha256']==row['config_sha256'],name
 def apks(value):return {x['entry']:x['sha256']for x in value.get('inputs',[])if x.get('entry','').endswith('.apk')}
 left,right=apks(old[name]),apks(row)
 for entry in left.keys()&right.keys():assert left[entry]==right[entry],(name,entry)
counts=collections.Counter();per_module=collections.defaultdict(collections.Counter);examples=collections.defaultdict(list);regressions=[];outcomes=collections.defaultdict(collections.Counter)
for key in sorted(before.keys()|after.keys()):
 left,right=before.get(key),after.get(key)
 if left is None:kind='only_round2'
 elif right is None:kind='only_round1'
 elif left in['FAIL','ERROR']and right=='PASS':kind='fixed'
 elif left=='PASS'and right in['FAIL','ERROR']:kind='regressed'
 elif left=='PASS'and right=='PASS':kind='still_passed'
 elif left in['FAIL','ERROR']and right in['FAIL','ERROR']:kind='still_failed'
 elif right in['IGNORE','ASSUMPTION']:kind='skipped_round2'
 else:kind='other_status_transition'
 counts[kind]+=1;per_module[key[0]][kind]+=1
 outcomes[kind][str(left)+'->'+str(right)]+=1
 detail=dict(module=key[0],runner_index=key[1],runner_type=key[2],package=key[3],test=key[4]+'#'+key[5],occurrence=key[6],before=left,after=right)
 if len(examples[kind])<60:examples[kind].append(detail)
 if kind=='regressed':regressions.append(dict(**detail,before_evidence=old_evidence[key],after_evidence=new_evidence[key]))
result=dict(scope='Latest terminal events for unchanged original configuration/APK identities; not API compatibility percentage',before=str(a.before),after=str(a.after),counts=dict(counts),before_terminal_statuses=dict(collections.Counter(before.values())),after_terminal_statuses=dict(collections.Counter(after.values())),modules=[dict(module=name,before=old[name]['status'],after=new[name]['status'],cases=dict(per_module[name]))for name in sorted(new)],examples=dict(examples),note='Missing terminal results and newly discovered cases remain separate. Skips/assumptions are never counted as fixes. Executor identity includes runner index/type/package; repeated identical names within that executor are paired by occurrence order.')
result['unidentified_terminal_statuses']=dict(before=dict(old_unidentified),after=dict(new_unidentified),note='Events without both a test class and name cannot be paired as individual test fixes/regressions')
timings=[]
for name in sorted(new):
 left=old[name].get('attempt_limits',{}).get('module_timeout_seconds')
 right=new[name].get('attempt_limits',{}).get('module_timeout_seconds')
 if left!=right:timings.append(dict(module=name,before_seconds=left,after_seconds=right,before_status=old[name]['status'],after_status=new[name]['status']))
result['deadline_differences']=timings
result['comparison_limits']='Counts reflect runtime and preparation changes plus recorded deadlines. Newly discovered, missing terminal and skipped cases are separate; interrupted runs do not prove module completion.'
result['transition_outcomes']={k:dict(v)for k,v in outcomes.items()}
diagnosis=a.after/'view-regression-diagnosis.json'
if diagnosis.exists():result['diagnostic_followup']=json.loads(diagnosis.read_text())
(a.after/'comparison-with-round1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in['modules','examples']},indent=2))
(a.after/'regressions-with-round1.json').write_text(json.dumps(dict(count=len(regressions),cases=regressions),indent=2)+'\n')
