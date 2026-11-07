from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runner_arguments import instrumentation_arguments,LIBCORE_RUNNER
from instrumentation_policy import original_disabled_runners

def runner(kind=LIBCORE_RUNNER,**unused):return dict(**{'class':kind},options=[])
def policy(kind=LIBCORE_RUNNER,value='false'):
    return '<test class="'+kind+'"><option name="package" value="test.package"/><option name="hidden-api-checks" value="'+value+'"/></test>'

class OriginalRunnerContract(unittest.TestCase):
    def test_original_expectations_and_filters_are_retained(self):
        r=runner();r['options']=[dict(name='core-expectation',value='/one.txt'),dict(name='core-expectation',value='/two.txt'),dict(name='instrumentation-arg',key='filter',value='original.Filter'),dict(name='include-annotation',value='original.Shard')]
        self.assertEqual(instrumentation_arguments(r),dict(filter='original.Filter',annotation='original.Shard',**{'core-expectations':'/one.txt,/two.txt','timeout_msec':'300000'}))
    def test_original_package_option_overrides_class_option(self):
        r=runner();r['options']=[dict(name='class',value='original.Test'),dict(name='test-package',value='original.package')]
        self.assertNotIn('class',instrumentation_arguments(r));self.assertEqual(instrumentation_arguments(r)['package'],'original.package')
    def test_raw_instrumentation_class_is_not_a_host_class_option(self):
        r=runner();r['options']=[dict(name='instrumentation-arg',key='class',value='original.Test'),dict(name='test-package',value='original.package')]
        self.assertEqual(instrumentation_arguments(r)['class'],'original.Test')
    def test_normal_android_runner_does_not_gain_libcore_options(self):
        r=runner('com.android.tradefed.testtype.AndroidJUnitTest');r['options']=[dict(name='core-expectation',value='/ignored.txt')]
        self.assertNotIn('core-expectations',instrumentation_arguments(r))
    def test_two_original_false_shards_are_accepted(self):
        self.assertEqual(original_disabled_runners('<configuration>'+policy()+policy()+'</configuration>','test.package'),2)
    def test_mixed_shard_policy_is_rejected(self):
        with self.assertRaises(ValueError):original_disabled_runners('<configuration>'+policy()+policy(value='true')+'</configuration>','test.package')
    def test_unknown_runner_class_cannot_authorize_policy(self):
        with self.assertRaises(ValueError):original_disabled_runners('<configuration>'+policy('untrusted.LibcoreTest')+'</configuration>','test.package')
    def test_other_package_cannot_authorize_policy(self):
        with self.assertRaises(ValueError):original_disabled_runners('<configuration>'+policy()+'</configuration>','different.package')
    def test_default_checks_in_one_shard_are_not_false(self):
        source='<configuration>'+policy()+'<test class="'+LIBCORE_RUNNER+'"><option name="package" value="test.package"/></test></configuration>'
        with self.assertRaises(ValueError):original_disabled_runners(source,'test.package')

if __name__=='__main__':unittest.main()
