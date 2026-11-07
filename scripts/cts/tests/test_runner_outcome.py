"""A complete callback and per-test PASS events cannot erase a runner failure."""
from pathlib import Path
import importlib.util, unittest
path=Path(__file__).resolve().parents[1]/'instrumentation_outcome.py'
spec=importlib.util.spec_from_file_location('runner_outcome_fixture',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class RunnerOutcome(unittest.TestCase):
 def test_listener_failure_without_individual_failure_event(self):
  result=module.inspect_finish(dict(code=-1,results=dict(stream='There was 1 failure:\n1) Test mechanism\njava.lang.IllegalStateException\nFAILURES!!!\nTests run: 744,  Failures: 1\n')),dict(started=744,passed=744))
  self.assertTrue(result['has_failures']);self.assertEqual(result['unattributed_failures'],1);self.assertEqual(result['reported_tests'],744)
 def test_actual_success(self):
  result=module.inspect_finish(dict(code=-1,results=dict(stream='Time: 33.194\nOK (123 tests)\n')),dict(started=123,passed=123))
  self.assertFalse(result['has_failures']);self.assertEqual(result['reported_failures'],0)
 def test_individual_failure_not_double_counted(self):
  result=module.inspect_finish(dict(code=-1,results=dict(stream='FAILURES!!!\nTests run: 4,  Failures: 2\n')),dict(started=4,passed=2,failed=2))
  self.assertTrue(result['has_failures']);self.assertEqual(result['unattributed_failures'],0)
 def test_aborted_callback_is_not_a_success(self):
  self.assertTrue(module.inspect_finish(dict(code=0,results=dict(shortMsg='Instrumentation aborted')),dict(started=1,passed=1))['has_failures'])
 def test_official_default_is_not_the_old_diagnostic_interrupt(self):
  self.assertEqual(module.test_timeout_msec(dict(options=[])),300000)
 def test_declared_timeouts_are_preserved(self):
  self.assertEqual(module.test_timeout_msec(dict(options=[dict(name='test-timeout',value='600000')])),600000)
  self.assertEqual(module.test_timeout_msec(dict(options=[dict(name='test-timeout',value='600000'),dict(name='instrumentation-arg',key='timeout_msec',value='42000')])),42000)
 def test_missing_callback_never_invents_success(self):
  self.assertFalse(module.inspect_finish(None,{})['callback_present'])

if __name__=='__main__':unittest.main()
