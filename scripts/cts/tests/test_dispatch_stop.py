"""The dispatcher must not advance without authoritative device cleanup proof."""
from pathlib import Path
import importlib.util, json, subprocess, sys, tempfile, types, unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'scripts/cts'))

class Archive:
    entries = {'android-cts/testcases/Fixture.apk': {}}
    def __init__(self, path): pass
    def extract(self, entry, path):
        path.write_bytes(b'isolated harness fixture, not an APK executed on a device')
        return dict(entry=entry, sha256='a' * 64, bytes=path.stat().st_size)

def manifest(path):
    return dict(package='example.fixture', application={}, instrumentation=[dict(name='example.Runner', targetPackage='example.fixture')])

class StopContract(unittest.TestCase):
    def check_stop(self, timeout=False, unhealthy_compositor=False):
        with tempfile.TemporaryDirectory(dir=REPO / 'build', prefix='cts-dispatch-stop-') as directory:
            evidence = Path(directory)
            modules = [dict(module=name, config_sha256='b' * 64,
                preparers=[dict(options=[dict(name='test-file-name', value='Fixture.apk')])],
                runners=[dict(**{'class':'com.android.tradefed.testtype.AndroidJUnitTest'},
                    options=[dict(name='package', value='example.fixture')])]) for name in ['First', 'MustNotStart']]
            (evidence / 'module-plan.json').write_text(json.dumps(dict(modules=modules)))
            archive = types.ModuleType('official_archive'); archive.Archive = Archive
            parser = types.ModuleType('apk_manifest'); parser.parse = manifest
            spec = importlib.util.spec_from_file_location('cts_dispatch_stop_fixture', REPO / 'scripts/cts/run-modules.py')
            module = importlib.util.module_from_spec(spec)
            calls = []
            def run(command, **kwargs):
                calls.append(command)
                if timeout: raise subprocess.TimeoutExpired(command, 1)
                if unhealthy_compositor:
                    plan=json.loads((evidence/'modules/First/inputs/plan.json').read_text())
                    out=evidence/'modules/First/inputs'/plan['label'];out.mkdir()
                    (out/'run-result.json').write_text(json.dumps(dict(status='COMPLETED',brightness='0',boot_unchanged=True,lipstick_unchanged=True,daily_root_unchanged=True,compositor_before=dict(ready=True),compositor_after=dict(ready=False))))
                    (out/'instrumentation-events.jsonl').write_text(json.dumps(dict(event='status',code=-2,bundle=dict(test='originalFailure',**{'class':'example.Fixture'},stack='AssertionError: preserved original failure'))) + '\n')
                    return subprocess.CompletedProcess(command, 0)
                return subprocess.CompletedProcess(command, 1)
            with patch.dict(sys.modules, {'official_archive':archive, 'apk_manifest':parser}):
                spec.loader.exec_module(module)
                with patch.object(sys, 'argv', ['run-modules.py', str(evidence)]), patch.object(subprocess, 'run', run):
                    with self.assertRaisesRegex(RuntimeError, 'Device cleanup/identity'):
                        module.main()
            self.assertEqual(len(calls), 1)
            row = json.loads((evidence / 'modules/First/attempt.json').read_text())
            self.assertEqual(row['status'], 'ERROR')
            self.assertFalse((evidence / 'modules/MustNotStart/attempt.json').exists())
            if not timeout:
                self.assertEqual(row['runners'][0]['status'], 'BLOCKED_CLEANUP')
            if unhealthy_compositor:
                self.assertEqual(row['runners'][0]['test_events'],dict(failed=1))
                self.assertFalse(row['runners'][0]['cleanup_safe'])
                self.assertTrue((evidence/'modules/First'/row['runners'][0]['run']/'instrumentation-events.jsonl').exists())

    def test_unknown_selected_module_never_starts_device(self):
        with tempfile.TemporaryDirectory(dir=REPO / 'build', prefix='cts-selection-') as directory:
            evidence=Path(directory)
            (evidence/'module-plan.json').write_text(json.dumps(dict(modules=[dict(module='CtsRsBlasTestCases')])))
            archive=types.ModuleType('official_archive');archive.Archive=Archive
            parser=types.ModuleType('apk_manifest');parser.parse=manifest
            spec=importlib.util.spec_from_file_location('cts_selection_fixture',REPO/'scripts/cts/run-modules.py')
            module=importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules,{'official_archive':archive,'apk_manifest':parser}):
                spec.loader.exec_module(module)
                with patch.object(sys,'argv',['run-modules.py',str(evidence),'--modules','CtsRsBlasTestCases','CtsRenderscriptBlasTestCases']),patch.object(subprocess,'run')as device:
                    with self.assertRaises(SystemExit)as error:module.main()
                    self.assertEqual(error.exception.code,2)
                    device.assert_not_called()
            self.assertFalse((evidence/'modules').exists())

    def test_missing_device_result_stops_suite(self): self.check_stop()
    def test_orchestration_timeout_stops_suite(self): self.check_stop(timeout=True)
    def test_unresponsive_compositor_stops_and_preserves_failure(self): self.check_stop(unhealthy_compositor=True)

if __name__ == '__main__': unittest.main()
