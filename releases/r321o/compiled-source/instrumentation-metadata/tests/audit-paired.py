from pathlib import Path
import json,hashlib,stat
r=Path('/media/psf/Home/WorkSpace/saidroid-next');b=r/'build/evidence/cts-frame-repair-20261031';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();frozen=json.loads((b/'original-instrumentation-metadata260-coupled-v1-frozen-inputs.json').read_text());assert all(sha(r/n)==v for n,v in frozen['sources'].items())and all(sha(b/n)==v for n,v in frozen['proofs'].items())
expected=json.loads((b/'instrumentation-metadata260-expected-original-ids-v1.json').read_text());records=[]
for which in ['before','after']:
 p=b/('original-instrumentation-metadata260-'+which+'-v1.json');v=json.loads(p.read_text());assert v['complete']and all(v[n]for n in ['private_state_and_apk_removed','owned_processes_reaped','binderfs_removed','private_bus_removed','private_data_mount_removed','original_inputs_unchanged'])
 start=[e['bundle']['class']+'#'+e['bundle']['test']for e in v['events']if e.get('event')=='status'and e.get('code')==1 and e.get('bundle',{}).get('test')];end=[e['test']for e in v['terminal']];assert len(start)==len(set(start))==80 and set(start)==set(expected['expected_ids'])and start==end
 assert v['actual_request']['arguments']==dict(filter='com.android.cts.core.runner.ExpectationBasedFilter',**{'core-expectations':'/knownfailures.txt','timeout_msec':'300000','class':','.join(expected['classes'])})
 log=Path('/var/lib/saidroid-original-instrumentation-metadata260-'+which+'-v1/run/instrumentation.log');text=log.read_text(errors='replace');listeners=[l for l in text.splitlines()if 'Adding listener' in l];listener=[l for l in listeners if 'com.android.cts.runner.CtsTestRunListener'in l];print(which,'LISTENERS',listeners)
 # Preserve all listener warnings/exception context for review, even if tests pass.
 lines=text.splitlines();diagnostic=[]
 for i,l in enumerate(lines):
  if 'Exception' in l or 'Error' in l or 'CtsTestRunListener'in l:diagnostic.append(dict(line=i+1,text='\n'.join(lines[max(0,i-2):min(len(lines),i+6)])))
 (b/('instrumentation-metadata260-'+which+'-listener-diagnostics-v1.json')).write_text(json.dumps(diagnostic,indent=2)+'\n')
 if which=='after':assert len(listener)==1, listeners
 else:assert not listener, listeners
 failures=[e['test']for e in v['terminal']if e['code']!=0];assert failures==(['libcore.java.lang.SystemTest#testSystemProperties_mutable']if which=='before'else[])
 records.append(dict(which=which,counts=v['counts'],raw_sha256=sha(p),log_sha256=sha(log),listeners=listeners,original_declared_listener_loaded=bool(listener),actual_client_runtime_maps=v['actual_client_runtime_maps'],actual_client_command=v['actual_client_command'],all_cleanup_safe=True))
oldroot=Path('/var/tmp/saidroid-idn-root-label254-v1-formal-vm-component/root');newroot=Path('/var/tmp/saidroid-instrumentation-metadata260-prototype-v1/root');actual={}
for label,root in [('before',oldroot),('after',newroot)]:
 m=json.loads((root/'install-manifest.json').read_text());assert all(sha(root/n)==v['sha256']and stat.S_IMODE((root/n).stat().st_mode)==v['mode']for n,v in m['files'].items());actual[label]=dict(root=str(root),runtime_sha256=sha(root/'lib/runtime.jar'),hidden_manifest_sha256=sha(root/'share/build/hiddenapi-manifest.json'),boot_manifest_sha256=sha(root/'share/build/boot-image-manifest.json'))
own=json.loads((b/'instrumentation-metadata260-own-contract-v4.json').read_text());assert own['passed']and 'checks=14|'in own['results'][1]['marker']and all(x['actual_runtime_sha256']==actual[w]['runtime_sha256']for x,w in zip(own['results'],['before','after']))
result=dict(scope='Paired same80 unique original methods on exact original APK/defaultApplication/AJUR; no extra listener args/manual resets/APK/assertions/filter/heap/clock/budget changes. Actual declared listener automatically loads after generic InstrumentationInfo metadata fix. VM fixtures explicitly retained; not phone/fullmodule acceptance.',passed=True,tests=80,before_pass=79,before_fail=1,after_pass=80,after_fail=0,exact_original_ids=True,records=records,components=actual,own_contract_checks=14,frozen_sources_unchanged=len(frozen['sources']),frozen_proofs_unchanged=len(frozen['proofs']),own_contract_sha256=sha(b/'instrumentation-metadata260-own-contract-v4.json'),full_module_passed=False,phone_tested=False)
out=b/'instrumentation-metadata260-paired-v1-audit.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print('INSTRUMENTATION_METADATA260_PAIRED=PASS|original=80|before=79|after=80|automatic_declared_listener=true|phone=false')
