from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from instrumentation_policy import hidden_api_checks

class OriginalPolicy(unittest.TestCase):
    def test_default_enforces(self):self.assertTrue(hidden_api_checks(dict(options=[])))
    def test_explicit_true_enforces(self):self.assertTrue(hidden_api_checks(dict(options=[dict(name='hidden-api-checks',value='true')])))
    def test_original_false_is_preserved(self):self.assertFalse(hidden_api_checks(dict(options=[dict(name='hidden-api-checks',value='false')])))
    def test_ambiguous_is_rejected(self):
        with self.assertRaises(ValueError):hidden_api_checks(dict(options=[dict(name='hidden-api-checks',value='false'),dict(name='hidden-api-checks',value='true')]))
    def test_unknown_value_is_rejected(self):
        with self.assertRaises(ValueError):hidden_api_checks(dict(options=[dict(name='hidden-api-checks',value='disable-all')]))
if __name__=='__main__':unittest.main()
