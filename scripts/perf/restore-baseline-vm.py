#!/usr/bin/env python3
"""Atomically point /home/art/api29-root back at the delivered baseline release.

Run inside the MeeGo Build VM while holding the device lock and with no ART
process alive. The perf release directory is left on disk as evidence.
"""
from pathlib import Path
import base64, os, subprocess, sys

SSH = ['sshpass', '-e', 'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=8',
       'root@bonito']


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else 'api29-20261026-r63'
    assert target.startswith('api29-'), 'release name expected'
    body = '''
from pathlib import Path
import os, pwd
base = Path('/home/art'); link = base / 'api29-root'
target = base / 'releases' / TARGET
assert target.is_dir(), 'release is missing'
assert not link.exists() or link.is_symlink(), 'api29-root is not a symlink'
temp = base / ('.api29-root-restore-' + str(os.getpid()))
temp.symlink_to(str(target)); os.replace(temp, link)
print('ROOT_RESTORED=' + os.readlink(link))
'''
    body = body.replace("target = base / 'releases' / TARGET",
                        "target = base / 'releases' / %r" % target)
    payload = base64.b64encode(body.encode()).decode()
    r = subprocess.run(
        SSH + ['echo ' + payload + ' | base64 -d | python3 -'],
        capture_output=True, text=True, timeout=30,
        env=dict(os.environ, SSHPASS=os.environ['SSHPASS']))
    print(r.stdout.strip())
    print(r.stderr.strip()[-500:])
    r.check_returncode()


if __name__ == '__main__':
    main()
