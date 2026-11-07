"""Wait for MCE's asynchronous blank request to reach the actual panel."""
from pathlib import Path
import subprocess
import time


def blank_display(timeout=6, brightness_path=Path(
        '/sys/class/backlight/panel0-backlight/actual_brightness'), run=subprocess.run):
    started = time.monotonic()
    record = dict(ready=False, samples=[], mce_display=None)
    try:
        run(['mcetool', '--set-never-blank=disabled', '--blank-screen'],
            check=True, timeout=5, capture_output=True, text=True)
        deadline = time.monotonic() + timeout
        while True:
            brightness = brightness_path.read_text().strip()
            record['samples'].append(dict(seconds=time.monotonic() - started,
                                           brightness=brightness))
            if brightness == '0':
                state = run(['gdbus', 'call', '--system', '--dest', 'com.nokia.mce',
                             '--object-path', '/com/nokia/mce/request', '--method',
                             'com.nokia.mce.request.get_display_status'],
                            check=True, timeout=2, capture_output=True, text=True)
                record['mce_display'] = state.stdout.strip()
                if record['mce_display'] == "('off',)":
                    record['ready'] = True
                    break
            if time.monotonic() >= deadline:
                record['error'] = 'MCE/panel did not finish blanking within the cleanup deadline'
                break
            time.sleep(.05)
    except Exception as failure:
        record['error'] = str(failure)
    record['seconds'] = time.monotonic() - started
    return record
