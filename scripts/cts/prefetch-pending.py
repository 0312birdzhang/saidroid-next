#!/usr/bin/env python3
"""Download only pending test inputs. Device execution remains strictly serial."""
from pathlib import Path
import argparse,json,concurrent.futures,fcntl
from official_archive import Archive
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);a=p.parse_args();ev=a.evidence;arc=Archive(ev/'official-index.json');plan=json.loads((ev/'module-plan.json').read_text());inputs=[]
for module in plan['modules']:
 out=ev/'modules'/module['module'];record=out/'attempt.json'
 if record.exists():continue
 names=sorted({o['value']for prep in module['preparers']for o in prep['options']if o.get('name')=='test-file-name'and o['value'].endswith('.apk')})
 for name in names:
  candidates=[n for n in arc.entries if n.startswith('android-cts/testcases/')and Path(n).name==name]
  if len(candidates)==1:inputs.append((module['module'],candidates[0],out/'inputs'/name))
def fetch(item):
 module,name,target=item;target.parent.mkdir(parents=True,exist_ok=True)
 with target.with_suffix(target.suffix+'.lock').open('a+b')as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);record=target.parent.parent/'attempt.json'
  if(target.parent/'plan.json').exists():return dict(module=module,entry=name,status='already-consumed')
  if record.exists()and json.loads(record.read_text())['status']!='RUNNING':return dict(module=module,entry=name,status='already-processed')
  try:return dict(arc._extract_unlocked(name,target),module=module,status='downloaded')
  except Exception as error:return dict(module=module,entry=name,status='download-error',reason=str(error))
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=5)as pool:
 for result in pool.map(fetch,inputs):results.append(result);print('PREFETCH='+result['module']+'|'+result['status'],flush=True)
(ev/'prefetch-manifest.json').write_text(json.dumps(results,indent=2)+'\n');print('PREFETCH_DONE='+str(len(results)))
