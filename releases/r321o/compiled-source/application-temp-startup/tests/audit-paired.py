from pathlib import Path
import collections, hashlib, json
b = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before, after = [json.loads((b / ('original-temp-startup237-' + label + '-v1.json')).read_text()) for label in ['before', 'after']]
assert before['complete'] and after['complete']
assert before['counts'] == dict(started=145, passed=128, failed=17)
assert after['counts'] == dict(started=145, passed=144, failed=1)
def callbacks(record, code):
    return [e['bundle']['class'] + '#' + e['bundle']['test'] for e in record['events']
            if e.get('event') == 'status' and e.get('code') == code and e.get('bundle', {}).get('test')]
old, new = callbacks(before, 1), callbacks(after, 1)
assert old == new and len(old) == len(set(old)) == 145
assert set(n.split('#')[0] for n in old) == {'libcore.java.lang.SystemTest', 'libcore.java.nio.file.Files2Test', 'libcore.java.nio.file.FilesTest', 'org.apache.harmony.tests.javax.xml.parsers.SAXParserFactoryTest', 'org.apache.harmony.tests.javax.xml.parsers.SAXParserTest'}
for d in [before, after]:
    assert all(d[n] for n in ['private_state_and_apk_removed', 'owned_processes_reaped', 'binderfs_removed', 'private_bus_removed', 'private_data_mount_removed', 'original_inputs_unchanged'])
    assert callbacks(d, 1) == [e['test'] for e in d['terminal']]
oldfail = set(callbacks(before, -2)); newfail = set(callbacks(after, -2))
assert newfail == {'libcore.java.lang.SystemTest#testSystemProperties_mutable'}
assert len(oldfail - newfail) == 16 and all('.SAXParserTest#' in n for n in oldfail - newfail)
assert before['actual_client_runtime_maps'] == after['actual_client_runtime_maps']
cmd0, cmd1 = before['actual_client_command'], after['actual_client_command']
normalize = lambda c: [s.replace('before-v1', 'PAIRED-v1').replace('after-v1', 'PAIRED-v1') for s in c if not s.startswith('-Djava.io.tmpdir=')]
assert normalize(cmd0) == normalize(cmd1)
assert [s for s in cmd0 if s.startswith('-Ddexmaker.dexcache=')] == [s for s in cmd1 if s.startswith('-Ddexmaker.dexcache=')] and not any(s.startswith('-Djava.io.tmpdir=') for s in cmd0)
assert [s for s in cmd1 if s.startswith('-Djava.io.tmpdir=')] == ['-Djava.io.tmpdir=/home/art/apps/android.libcore.cts/data/cache']
assert before['actual_request']['arguments'] == after['actual_request']['arguments']
assert before['apk_metadata'] == after['apk_metadata'] and before['config_sha256'] == after['config_sha256']
record = dict(scope='Five WHOLE original classes in one real original APK/AJUR/Application process, same ordered145 unique methods and original knownfailure filter. Only after command adds app-private startup java.io.tmpdir; both retain236DexMakerconfiguration. All actual current236 ART/JNI/core/runtime/9images mappings byte-identical. VM Binder/keystore/root-MCE fixtures explicit and native host not invoked by this fixture. Original remaining mutable-property failure retained; no phone/fullmodule/formal CTS acceptance.', passed=True,
              tests=145, before_counts=before['counts'], after_counts=after['counts'], fixed_tests=sorted(oldfail-newfail), remaining_failures=sorted(newfail),
              same_ordered_original_ids=True, original_inputs_unchanged=True, all_fixture_cleanup_safe=True,
              native_build_manifest_sha256=sha(b/'application-temp-startup237-native-v1-build.json'),
              before_sha256=sha(b/'original-temp-startup237-before-v1.json'), after_sha256=sha(b/'original-temp-startup237-after-v1.json'),
              phone_staged=False, full_module_passed=False, formal_module_acceptance=False)
out=b/'original-temp-startup237-paired-v1-audit.json'; assert not out.exists(); out.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k!='fixed_tests'},indent=2))
