from pathlib import Path
import hashlib
import json
import sys

repo = Path(__file__).resolve().parents[3]
base = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0, str(repo / 'scripts/cts'))
from instrumentation_outcome import inspect_finish

frozen = json.loads((base / 'original-crypto-provider-alias277-coupled-v2-frozen-inputs.json').read_text())
assert all(sha(repo / n) == h for n, h in frozen['sources'].items())
assert all(sha(base / n) == h for n, h in frozen['proofs'].items())
expected = json.loads((base / 'crypto-provider-alias277-expected-original-ids-v1.json').read_text())
assert len(expected['classes']) == 15 and len(expected['expected_ids']) == 204
results = [json.loads((base / ('original-crypto-provider-alias277-' + label + '-v2.json')).read_text())
           for label in ['before', 'after']]
ordered = []
for result in results:
    assert result['complete'] and result['original_inputs_unchanged'] and result['original_heap_options_unchanged']
    assert result['original_declared_listener_automatically_loaded']
    assert all(result[n] for n in ['owned_processes_reaped', 'private_state_and_apk_removed',
                                   'binderfs_removed', 'private_bus_removed', 'private_data_mount_removed'])
    name = lambda e: e['bundle'].get('class', '') + '#' + e['bundle']['test']
    status = [e for e in result['events'] if e.get('event') == 'status' and e.get('bundle', {}).get('test')]
    starts = [name(e) for e in status if e['code'] == 1]
    ends = [name(e) for e in status if e['code'] != 1]
    assert starts == ends and len(starts) == len(set(starts)) == 204
    assert set(starts) == set(expected['expected_ids'])
    assert ends == [v['test'] for v in result['terminal']]
    ordered.append(ends)
    assert len(result['actual_server_boot_images']) == 9
    assert sum(n.endswith('.art') for n in result['actual_client_runtime_maps']) == 9
    assert result['actual_request']['arguments'] == results[0]['actual_request']['arguments']
    assert result['vm_space_after_fixture']['available_blocks'] * result['vm_space_after_fixture']['blocksize'] > 200000000
    outcome = inspect_finish(result['instrumentation'], result['counts'])
    assert outcome['callback_present'] and not outcome['unattributed_failures']
    assert not result['runner_reporting_fatal']
assert ordered[0] == ordered[1]
assert results[0]['counts'] == dict(started=204, passed=201, failed=3)
assert results[1]['counts'] == dict(started=204, passed=202, failed=2)
for result, wanted in zip(results, [expected['before_failures'], expected['after_expected_failures']]):
    failures = [v for v in result['terminal'] if v['code'] != 0]
    assert {v['test'] for v in failures} == set(wanted)
    assert all(v['code'] == -2 for v in failures)
before_codes = {v['test']: v for v in results[0]['terminal']}
after_codes = {v['test']: v for v in results[1]['terminal']}
fixed = sorted(n for n in before_codes if before_codes[n]['code'] != 0 and after_codes[n]['code'] == 0)
assert fixed == ['org.apache.harmony.security.tests.java.security.Security2Test#test_getProvidersLjava_lang_String']
assert 'Unexpected number of providers returned for filter SECRETKEYFACTORY.DESEDE' in before_codes[fixed[0]]['stack']
assert all(after_codes[n]['code'] == before_codes[n]['code'] for n in before_codes if n not in fixed)
for key in ['apk_metadata', 'config_sha256', 'original_options', 'actual_fixture_bridge',
            'original_apk_native_files', 'actual_fixture_jar_sha256', 'actual_assignment', 'actual_kernel_policy_sha256']:
    assert results[0][key] == results[1][key]
own=json.loads((base/'crypto-provider-alias277-own-v1.json').read_text());module=json.loads((base/'crypto-provider-alias277-module-v1-boundary.json').read_text());assert own['passed']and module['passed']and module['changed_classes']==['SdCryptoProvider.class']and module['new_members']==[]and module['all_existing_member_flags_and_native_declarations_preserved']
assert own['source_sha256']==sha(repo/'scripts/api29/tests/crypto-provider-alias/CryptoProviderAlias277Contract.java')and own['runner_source_sha256']==sha(repo/'scripts/api29/tests/crypto-provider-alias/CryptoProviderAlias277Runner.java');assert len(own['results'])==2 and all(v['returncode']==0 for v in own['results'])
record = dict(passed=True,
              scope='VM paired15 WHOLE original crypto/PBE/provider classes204, same original Application/AJUR/manifestlistener/arguments/APK/orderedIDs. Onlycasepropertyduplicationremoved; sameeffectiveproviders/services/JKS andactualmixedcaseDESede/ARC4operations independently proven. Twootherproviderinventoryfailures retained. Not phone/fullmodule/certification/default promotion.',
              whole_classes=15, tests=204, before_pass=201, before_fail=3, after_pass=202, after_fail=2,
              fixed_original_tests=fixed, retained_original_failures=expected['after_expected_failures'],
              ordered_original_ids=ordered[0], expected_main_original_id_set_exact=True,
              original_arguments=results[0]['actual_request']['arguments'], all_cleanup_safe=True,
              own_actual_checks_each=module['own_checks_each'], actual_ART_and_native_nine_images=True,
              module_boundary_sha256=sha(base / 'crypto-provider-alias277-module-v1-boundary.json'),
              own_contract_sha256=sha(base / 'crypto-provider-alias277-own-v1.json'),
              frozen_sources_unchanged=len(frozen['sources']), frozen_proofs_unchanged=len(frozen['proofs']),
              raw_results={label: sha(base / ('original-crypto-provider-alias277-' + label + '-v2.json'))
                           for label in ['before', 'after']},
              driver_sha256=sha(base / 'run-original-crypto-provider-alias277-coupled-v2-vm.py'),
              full_module_passed=False, phone_executed=False)
target = base / 'crypto-provider-alias277-paired-v2-audit.json'
assert not target.exists()
target.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'ordered_original_ids'}, indent=2))
