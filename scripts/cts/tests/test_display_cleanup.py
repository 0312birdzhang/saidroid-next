import importlib.util
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest

spec = importlib.util.spec_from_file_location(
    'display_cleanup', Path(__file__).resolve().parents[1] / 'display_cleanup.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DisplayCleanupTest(unittest.TestCase):
    def test_request_completion_does_not_mean_panel_off(self):
        with tempfile.TemporaryDirectory() as directory:
            brightness = Path(directory) / 'brightness'
            brightness.write_text('574')
            mce_off = threading.Event()
            def transition():
                time.sleep(.08)
                brightness.write_text('0')
                time.sleep(.08)
                mce_off.set()
            worker = threading.Thread(target=transition)
            worker.start()
            def command(args, **kwargs):
                return subprocess.CompletedProcess(args, 0,
                    "('off',)" if mce_off.is_set() else "('on',)", '')
            result = module.blank_display(timeout=1, brightness_path=brightness, run=command)
            worker.join()
            self.assertTrue(result['ready'])
            self.assertEqual(result['samples'][0]['brightness'], '574')
            self.assertEqual(result['samples'][-1]['brightness'], '0')
            self.assertEqual(result['mce_display'], "('off',)")

    def test_panel_never_blanks_is_a_real_cleanup_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            brightness = Path(directory) / 'brightness'
            brightness.write_text('574')
            def command(args, **kwargs):
                return subprocess.CompletedProcess(args, 0, "('on',)", '')
            result = module.blank_display(timeout=.1, brightness_path=brightness, run=command)
            self.assertFalse(result['ready'])
            self.assertIn('deadline', result['error'])

    def test_command_failure_is_not_hidden(self):
        def command(args, **kwargs):
            raise subprocess.CalledProcessError(1, args)
        result = module.blank_display(timeout=.1, run=command)
        self.assertFalse(result['ready'])
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
