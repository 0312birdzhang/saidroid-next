from pathlib import Path
import hashlib
import json
import sys

repo = Path(__file__).resolve().parents[3]
base = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0, str(repo / 'scripts/cts'))
from instrumentation_outcome import inspect_finish

frozen = json.loads((base / 'original-pbe-api29274-coupled-v1-frozen-inputs.json').read_text())
assert all(sha(repo / n) == h for n, h in frozen['sources'].items())
assert all(sha(base / n) == h for n, h in frozen['proofs'].items())
expected = json.loads((base / 'pbe-api29274-expected-original-ids-v1.json').read_text())
assert len(expected['classes']) == 15 and len(expected['expected_ids']) == 204
results = [json.loads((base / ('original-pbe-api29274-' + label + '-v1.json')).read_text())
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
assert results[0]['counts'] == dict(started=204, passed=200, failed=4)
assert results[1]['counts'] == dict(started=204, passed=201, failed=3)
for result, wanted in zip(results, [expected['before_failures'], expected['after_expected_failures']]):
    failures = [v for v in result['terminal'] if v['code'] != 0]
    assert {v['test'] for v in failures} == set(wanted)
    assert all(v['code'] == -2 for v in failures)
before_codes = {v['test']: v for v in results[0]['terminal']}
after_codes = {v['test']: v for v in results[1]['terminal']}
fixed = sorted(n for n in before_codes if before_codes[n]['code'] != 0 and after_codes[n]['code'] == 0)
assert fixed == ['com.android.org.conscrypt.javax.crypto.CipherTest#test_PBKDF2WITHHMACSHA1_SKFactory_and_PBEAESCBC_Cipher_noIV']
assert 'No IV set when using PBE key' in before_codes[fixed[0]]['stack']
assert all(after_codes[n]['code'] == before_codes[n]['code'] for n in before_codes if n not in fixed)
for key in ['apk_metadata', 'config_sha256', 'original_options', 'actual_fixture_bridge',
            'original_apk_native_files', 'actual_fixture_jar_sha256', 'actual_assignment', 'actual_kernel_policy_sha256']:
    assert results[0][key] == results[1][key]
own = json.loads((base / 'pbe-api29274-own-v5.json').read_text())
module = json.loads((base / 'pbe-api29274-module-v2-boundary-v1.json').read_text())
assert own['passed'] and module['passed'] and module['own_actual_after_checks'] == 321
assert module['no_added_members'] and module['all_other_classfiles_and_resources_unchanged']
assert module['nested_classfiles_retained_byte_identical']
assert module['source_meta_sha256'] == sha(repo / 'scripts/api29/core/pbe-api29-compat-v2/sources.json')
assert own['source_sha256'] == sha(repo / 'scripts/api29/tests/pbe-api29/PbeApi29Contract.java')
assert own['runner_source_sha256'] == sha(repo / 'scripts/api29/tests/pbe-api29/PbeApi29ContractRunner.java')
record = dict(passed=True,
              scope='VM paired15 WHOLE original crypto/PBE/provider classes204, same original Application/AJUR/manifestlistener/arguments/APK/orderedIDs. SDK29 legacy missing-IV compatibility only, actual crypto/normal IV/newSDK rejection independently proven. Three provider inventory failures retained. Not phone/fullmodule/certification/default promotion.',
              whole_classes=15, tests=204, before_pass=200, before_fail=4, after_pass=201, after_fail=3,
              fixed_original_tests=fixed, retained_original_failures=expected['after_expected_failures'],
              ordered_original_ids=ordered[0], expected_main_original_id_set_exact=True,
              original_arguments=results[0]['actual_request']['arguments'], all_cleanup_safe=True,
              own_actual_after_checks=321, actual_ART_and_native_nine_images=True,
              module_boundary_sha256=sha(base / 'pbe-api29274-module-v2-boundary-v1.json'),
              own_contract_sha256=sha(base / 'pbe-api29274-own-v5.json'),
              frozen_sources_unchanged=len(frozen['sources']), frozen_proofs_unchanged=len(frozen['proofs']),
              raw_results={label: sha(base / ('original-pbe-api29274-' + label + '-v1.json'))
                           for label in ['before', 'after']},
              driver_sha256=sha(base / 'run-original-pbe-api29274-coupled-v1-vm.py'),
              full_module_passed=False, phone_executed=False)
target = base / 'pbe-api29274-paired-v1-audit.json'
assert not target.exists()
target.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({k: v for k, v in record.items() if k != 'ordered_original_ids'}, indent=2))
