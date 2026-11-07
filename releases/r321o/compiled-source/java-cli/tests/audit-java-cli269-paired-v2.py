from pathlib import Path
import json,hashlib,sys
repo=Path(__file__).resolve().parents[3];b=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();f=json.loads((b/'original-java-cli269-coupled-v3-frozen-inputs.json').read_text())
assert all(sha(repo/n)==h for n,h in f['sources'].items());assert all(sha(b/n)==h for n,h in f['proofs'].items())
results=[json.loads((b/('original-java-cli269-'+n+'-v3.json')).read_text())for n in ['before','after']];expected=json.loads((b/'java-cli268-expected-original-ids-v1.json').read_text())['expected_ids'];assert len(expected)==len(set(expected))==79
ordered=[]
for r in results:
 assert r['complete']and r['original_inputs_unchanged']and r['original_heap_options_unchanged']
 assert all(r[n]for n in ['owned_processes_reaped','private_state_and_apk_removed','binderfs_removed','private_bus_removed','private_data_mount_removed'])
 ids=[x['test']for x in r['terminal']];assert len(ids)==len(set(ids))==79 and set(ids)==set(expected);ordered.append(ids)
 assert r['counts']['started']==79 and len(r['actual_server_boot_images'])==9
 assert sum(n.endswith('.art')for n in r['actual_client_runtime_maps'])==9
 assert r['actual_request']['arguments']==results[0]['actual_request']['arguments']
 assert r['vm_space_after_fixture']['available_blocks']*r['vm_space_after_fixture']['blocksize']>200000000
assert ordered[0]==ordered[1], 'Before-after actual callback order must be identical'
assert results[0]['counts']==dict(started=79,passed=78,failed=1)and results[1]['counts']==dict(started=79,passed=79)
fail=[t for t in results[0]['terminal']if t['code']!=0];assert len(fail)==1 and fail[0]['test']=='org.apache.harmony.tests.java.lang.Process2Test#test_streams'and'Cannot run program "dalvikvm"'in fail[0]['stack']
for key in ['apk_metadata','config_sha256','original_options','actual_fixture_bridge','original_apk_native_files','actual_fixture_jar_sha256','actual_assignment','actual_kernel_policy_sha256']:assert results[0][key]==results[1][key]
own=json.loads((b/'java-cli268-basic-contract-v5.json').read_text());policy=json.loads((b/'java-cli268-policy-contract-v1.json').read_text());assert own['passed']and policy['passed']
r=dict(passed=True,scope='VM paired seven WHOLE original Runtime/Process classes; same Application/AJUR/originallistener/options/APK/79orderedIDs; actual functionalCLI proof, not phone/fullmodule acceptance',whole_classes=7,tests=79,before_pass=78,before_fail=1,after_pass=79,after_fail=0,ordered_ids=ordered[0],expected_main_order_differs=True,expected_id_set_exact=True,original_arguments=results[0]['actual_request']['arguments'],all_cleanup_safe=True,existing_component_files_unchanged=True,own_basic_sha256=sha(b/'java-cli268-basic-contract-v5.json'),own_policy_sha256=sha(b/'java-cli268-policy-contract-v1.json'),frozen_sources=len(f['sources']),frozen_proofs=len(f['proofs']),raw_results={n:sha(b/n)for n in ['original-java-cli269-before-v3.json','original-java-cli269-after-v3.json']},driver_sha256=sha(b/'run-original-java-cli269-coupled-v3-vm.py'),full_module_passed=False,phone_executed=False)
p=b/'java-cli269-paired-v2-audit.json';assert not p.exists();p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k!='ordered_ids'},indent=2))
