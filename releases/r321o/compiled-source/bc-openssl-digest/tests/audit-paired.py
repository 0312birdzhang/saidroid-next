from pathlib import Path
import collections,hashlib,json
b=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();cohorts={}
for name in ['selected','regression']:
 raw=b/('original-bc-openssl-digest245-'+name+'-v1.json');d=json.loads(raw.read_text());counts={};order={};failed={}
 for label in ['before244','after245']:
  rows=[r for r in d['results']if r['runtime']==label];assert len(rows)==(1 if name=='selected'else 11);c=collections.Counter();events=[]
  for row in rows:c.update({k:row[k]for k in ['tests','failures','assumptions','ignored','real_passed']});events+=row['events']
  counts[label]=dict(c);order[label]=[e for e in events if e[0]in['start','finish']];failed[label]=[e[1]for e in events if e[0]=='failure']
 assert order['before244']==order['after245'];starts=[e[1]for e in order['after245']if e[0]=='start'];assert len(starts)==len(set(starts))
 if name=='selected':assert counts['before244']==dict(tests=5,failures=5,assumptions=0,ignored=0,real_passed=0)and counts['after245']==dict(tests=5,failures=0,assumptions=0,ignored=0,real_passed=5)
 else:assert counts['before244']==counts['after245']==dict(tests=102,failures=3,assumptions=0,ignored=0,real_passed=99)and failed['before244']==failed['after245']
 cohorts[name]=dict(counts=counts,same_ordered_callbacks=True,unique_original_tests=len(starts),before_failed_ids=failed['before244'],after_failed_ids=failed['after245'],raw_sha256=sha(raw),driver_sha256=sha(b/('run-original-bc-openssl-digest245-'+name+'-v1-vm.py')))
own=b/'bc-openssl-digest245-own-contract-v2.json';o=json.loads(own.read_text());assert o['passed']and o['results'][0]['marker']=='BC_OPENSSL_DIGEST245_CONTRACT=PASS|vectors=18|functions=6|checks=200|provider=AndroidOpenSSL|actual_EVP=true'
source=b.parents[2]/'scripts/api29/tests/application-cache-startup/BcOpenSslDigest245Contract.java';assert o['source_sha256']==sha(source)and o['runner_source_sha256']==sha(b/'BcOpenSslDigest245ContractRunner.java')and o['oracle_sha256']==sha(b/'bc-openssl-digest245-vectors-v1.json')
record=dict(scope='Whole original DigestTest5missingOpenSSLDigestclassfailures to5PASS with canonicalAndroid10sevenclassnamespace-onlyaddition. ElevenWHOLEcrypto/providerregression102same99PASS3FAIL. Independent6algorithms18knownvectors actualAndroidOpenSSL provider/ConscryptEVPSPI and200lifecycle/offset/boundschecks. AlloldBCclassbytes/registration/trust/native retained; no APK/assertion/clock/heap/budgets change. SelectedAPKJUnit diagnostics notfullAJUR/module/phoneacceptance.',passed=True,cohorts=cohorts,own_contract_sha256=sha(own),own_checks=200,full_module_passed=False,formal_module_acceptance=False,phone_staged=False)
p=b/'bc-openssl-digest245-paired-v1-audit.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
