from pathlib import Path
import collections,hashlib,json
b=Path('/media/psf/Home/WorkSpace/saidroid-next/build/evidence/cts-frame-repair-20261031');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();raw=b/'original-idn-root-label254-selected-v1.json';d=json.loads(raw.read_text());assert d['status']=='COMPLETE';counts={};order={};failed={};classes={}
for label in ['before252','after254']:
 rows=[r for r in d['results']if r['runtime']==label];assert len(rows)==4;c=collections.Counter();events=[];classes[label]={}
 for r in rows:
  for ext in ['stdout','stderr']:assert sha(Path('/var/tmp/saidroid-original-idn-root-label254-selected-v1')/(label+'-'+r['selection']+'.'+ext))==r[ext+'_sha256']
  starts=[e[1]for e in r['events']if e[0]=='start'];ends=[e[1]for e in r['events']if e[0]=='finish'];assert starts==ends and len(starts)==r['tests']==len(set(starts))
  assert len([e for e in r['events']if e[0]=='failure'])==r['failures'];assert r['uid']==65534 and not r['assumptions']and not r['ignored']
  c.update({k:r[k]for k in ['tests','failures','assumptions','ignored','real_passed']});events+=r['events'];classes[label][r['selection']]={k:r[k]for k in ['tests','failures','real_passed']}
 counts[label]=dict(c);order[label]=[e for e in events if e[0]in ['start','finish']];failed[label]=[e[1]for e in events if e[0]=='failure']
assert order['before252']==order['after254'];starts=[e[1]for e in order['after254']if e[0]=='start'];assert len(starts)==len(set(starts))==134
assert counts['before252']==dict(tests=134,failures=1,assumptions=0,ignored=0,real_passed=133)and counts['after254']==dict(tests=134,failures=0,assumptions=0,ignored=0,real_passed=134)
assert failed['before252']==['test_TrailingDots(org.apache.harmony.tests.java.net.IDNTest)']and not failed['after254']
own=b/'idn-root-label254-own-contract-v1.json';o=json.loads(own.read_text());assert o['passed']and o['results'][0]['marker']=='IDN_ROOT_LABEL254_CONTRACT=PASS|checks=47|backend=actual-ICU63|invalid_domains_rejected=true';assert o['source_sha256']==sha(b.parents[2]/'scripts/api29/tests/application-cache-startup/IdnRootLabel254Contract.java')and o['runner_source_sha256']==sha(b/'IdnRootLabel254ContractRunner.java')
r=dict(scope='CanonicalAndroid10rootlabeldotfallback only; actualoriginaltwoIDN/twoURIwholeclasses134unique methods 133PASS1FAIL->134PASS with identicalorderedcallbacks. Independent47rootlabel/realICU63punycode/Unicode/STD3invalid/nullchecks. SDK29UID65534actualJNI104/ART/9images. No originalAPK/assertion/filter/clock/heap/budgetchanges; notfullAJUR/module/phoneacceptance.',passed=True,counts=counts,classes=classes,same_ordered_callbacks=True,unique_original_tests=len(starts),before_failed_ids=failed['before252'],after_failed_ids=failed['after254'],raw_sha256=sha(raw),driver_sha256=sha(b/'run-original-idn-root-label254-selected-v1-vm.py'),own_contract_sha256=sha(own),own_checks=47,full_module_passed=False,formal_module_acceptance=False,phone_staged=False)
p=b/'idn-root-label254-paired-v1-audit.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
