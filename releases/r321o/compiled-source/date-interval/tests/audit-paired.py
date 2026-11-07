from pathlib import Path
import collections,hashlib,json
b=Path('/media/psf/Home/WorkSpace/saidroid-next/build/evidence/cts-frame-repair-20261031');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cohorts={}
for name in ['selected','regression']:
 stem='original-date-interval252-'+name+'-v1';raw=b/(stem+'.json');d=json.loads(raw.read_text());assert d['status']=='COMPLETE';counts={};order={};failed={}
 for label in ['before248','after252']:
  rows=[r for r in d['results']if r['runtime']==label];assert len(rows)==(1 if name=='selected'else 4);c=collections.Counter();events=[]
  for r in rows:
   for ext in ['stdout','stderr']:assert sha(Path('/var/tmp/saidroid-'+stem)/(label+'-'+r['selection']+'.'+ext))==r[ext+'_sha256']
   starts=[e[1]for e in r['events']if e[0]=='start'];ends=[e[1]for e in r['events']if e[0]=='finish'];assert starts==ends and len(starts)==r['tests']==len(set(starts))
   assert len([e for e in r['events']if e[0]=='failure'])==r['failures'];assert r['uid']==65534 and not r['assumptions']and not r['ignored']
   c.update({k:r[k]for k in ['tests','failures','assumptions','ignored','real_passed']});events+=r['events']
  counts[label]=dict(c);order[label]=[e for e in events if e[0]in ['start','finish']];failed[label]=[e[1]for e in events if e[0]=='failure']
 assert order['before248']==order['after252'];starts=[e[1]for e in order['after252']if e[0]=='start'];assert len(starts)==len(set(starts))
 if name=='selected':assert counts['before248']==dict(tests=16,failures=1,assumptions=0,ignored=0,real_passed=15)and counts['after252']==dict(tests=16,failures=0,assumptions=0,ignored=0,real_passed=16)and failed['before248']==['testEndAtMidnight_dateAndTime(libcore.libcore.icu.DateIntervalFormatTest)']
 else:assert counts['before248']==counts['after252']==dict(tests=81,failures=0,assumptions=0,ignored=0,real_passed=81)
 cohorts[name]=dict(counts=counts,same_ordered_callbacks=True,unique_original_tests=len(starts),before_failed_ids=failed['before248'],after_failed_ids=failed['after252'],raw_sha256=sha(raw),driver_sha256=sha(b/('run-'+stem+'-vm.py')))
r=dict(scope='CanonicalAndroid10 midnight interval policy preserving originalprivateisMidnightname and exactdisplayminutehelper. Fivewhole originalAPKclasses97unique methods: target16 15PASS1FAIL->16PASS, surrounding81allPASS before/after; matchingorderedactualcallbacks, SDK29 UID65534 actualJNI104/ART/9images. No originalAPK/assertion/filter/clock/heap/budget changes; notfullAJUR/module/phoneacceptance.',passed=True,cohorts=cohorts,full_module_passed=False,formal_module_acceptance=False,phone_staged=False)
p=b/'date-interval252-paired-v1-audit.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
