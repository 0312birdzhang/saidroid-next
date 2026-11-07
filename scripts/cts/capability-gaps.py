#!/usr/bin/env python3
"""Map observed missing service signatures to actual official test evidence."""
from pathlib import Path
import argparse,json,re,collections
p=argparse.ArgumentParser();p.add_argument('evidence',type=Path);a=p.parse_args();gaps={}
for file in sorted((a.evidence/'modules').glob('*/cts*/instrumentation-events.jsonl')):
 module=file.parent.parent.name
 for line in file.read_text().splitlines():
  event=json.loads(line);b=event.get('bundle',{});stack=b.get('stack','')or''
  if event.get('event')!='status'or event.get('code')not in[-1,-2]:continue
  for description,signature in re.findall(r'(?m)([^\n:]*): (public abstract [^\n]+)',stack):
   if description.startswith('\tat'):continue
   key=signature.strip();entry=gaps.setdefault(key,dict(signature=key,description=description.strip(),events=0,modules=collections.Counter(),tests=[]));entry['events']+=1;entry['modules'][module]+=1
   test=str(b.get('class')or'')+'#'+str(b.get('test')or'')
   if len(entry['tests'])<3 and test not in entry['tests']:entry['tests'].append(test)
rows=sorted(gaps.values(),key=lambda r:-r['events'])
for row in rows:row['modules']=dict(row['modules'])
(a.evidence/'capability-gaps.json').write_text(json.dumps(dict(observed_missing_signatures=len(rows),gaps=rows,note='Observed exceptions only; absence from this list does not imply an API is implemented or accepted.'),indent=2)+'\n')
print('OBSERVED_MISSING_SERVICE_SIGNATURES='+str(len(rows)))
for row in rows[:12]:print(str(row['events'])+' '+row['signature'])
