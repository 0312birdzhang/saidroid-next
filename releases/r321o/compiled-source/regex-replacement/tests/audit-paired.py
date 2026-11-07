from pathlib import Path
import collections,hashlib,json
b=Path('/media/psf/Home/WorkSpace/saidroid-next/build/evidence/cts-frame-repair-20261031');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cohorts={}
for name,version in [('selected','v1'),('regression','v2')]:
 stem='original-regex-replacement248-'+name+'-'+version;raw=b/(stem+'.json');d=json.loads(raw.read_text());assert d['status']=='COMPLETE';counts={};order={};failed={};raw_stacks={}
 for label in ['before245','after248']:
  rows=[r for r in d['results']if r['runtime']==label];assert len(rows)==(1 if name=='selected'else 11);c=collections.Counter();events=[]
  for r in rows:
   for ext in ['stdout','stderr']:assert sha(Path('/var/tmp/saidroid-'+stem)/(label+'-'+r['selection']+'.'+ext))==r[ext+'_sha256']
   starts=[e[1]for e in r['events']if e[0]=='start'];ends=[e[1]for e in r['events']if e[0]=='finish'];assert starts==ends and len(starts)==r['tests']==len(set(starts))
   assert len([e for e in r['events']if e[0]=='failure'])==r['failures'];assert r['uid']==65534 and not r['assumptions']and not r['ignored']
   c.update({k:r[k]for k in ['tests','failures','assumptions','ignored','real_passed']});events+=r['events']
   if name=='regression'and r['failures']:
    text=(Path('/var/tmp/saidroid-'+stem)/(label+'-'+r['selection']+'.stderr')).read_text();head='java.util.regex.PatternSyntaxException: Look-behind pattern matches must have a bounded maximum length near index 312';assert head in text and 'PatternTest.test_bug_40103(PatternTest.java:754)'in text;raw_stacks[label]=dict(exception=head,original_apk_frame='PatternTest.test_bug_40103(PatternTest.java:754)',stderr_sha256=r['stderr_sha256'])
  counts[label]=dict(c);order[label]=[e for e in events if e[0]in ['start','finish']];failed[label]=[e[1]for e in events if e[0]=='failure']
 assert order['before245']==order['after248'];starts=[e[1]for e in order['after248']if e[0]=='start'];assert len(starts)==len(set(starts))
 if name=='selected':assert counts['before245']==dict(tests=6,failures=3,assumptions=0,ignored=0,real_passed=3)and counts['after248']==dict(tests=6,failures=0,assumptions=0,ignored=0,real_passed=6)
 else:assert counts['before245']==counts['after248']==dict(tests=303,failures=1,assumptions=0,ignored=0,real_passed=302)and failed['before245']==failed['after248']==['test_bug_40103(org.apache.harmony.regex.tests.java.util.regex.PatternTest)']
 cohorts[name]=dict(counts=counts,same_ordered_callbacks=True,unique_original_tests=len(starts),before_failed_ids=failed['before245'],after_failed_ids=failed['after248'],raw_stack_identity=raw_stacks,raw_sha256=sha(raw),driver_sha256=sha(b/('run-'+stem+'-vm.py')))
own=b/'regex-replacement248-own-contract-v2.json';o=json.loads(own.read_text());assert o['passed'];assert o['source_sha256']==sha(b.parents[2]/'scripts/api29/tests/application-cache-startup/RegexReplacement248Contract.java')and o['runner_source_sha256']==sha(b/'RegexReplacement248ContractRunner.java')
r=dict(scope='Paired original APK12whole regexclasses309unique callbacks. Target6:3failures fixed;11class303regression same302PASS1knownPatterncompileFAIL with actual same boundedlookbehind exception. Independent own replacement contract on actual248Matcher/JNI104/9images. No originalAPK/assertion/filter/clock/heap/budget changes; notfullAJUR/module/phoneacceptance.',passed=True,cohorts=cohorts,own_contract_sha256=sha(own),own_marker=o['results'][0]['marker'],full_module_passed=False,formal_module_acceptance=False,phone_staged=False)
p=b/'regex-replacement248-paired-v1-audit.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
