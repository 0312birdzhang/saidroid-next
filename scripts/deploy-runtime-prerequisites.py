#!/usr/bin/env python3
"""Add missing files only below /home/art; never replace a differing existing file."""
from pathlib import Path
import json
import subprocess
import sys

output = Path(sys.argv[1])
manifest = json.loads((output / 'manifest.json').read_text())
if manifest['schema'] not in ('saidroid-runtime-prerequisites-v1', 'saidroid-runtime-prerequisites-v2',
                             'saidroid-runtime-prerequisites-v3'):
    raise SystemExit('Unexpected runtime asset manifest')
if set(manifest['files']) not in ({'graphics-interfaces-hostdex.jar', 'tzdata'},
                                {'framework-compat-hostdex.jar', 'tzdata'}, {'icudt55l.dat'}):
    raise SystemExit('Unexpected runtime asset inventory')
ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
expected_boot = '5db879ed-48ea-4bf0-b5c1-64e271c11045'
if subprocess.check_output(ssh + ['/bin/cat /proc/sys/kernel/random/boot_id'],
                           timeout=10).decode().strip() != expected_boot:
    raise SystemExit('Refresh device identity before staging')
if 'ID=sailfishos' not in subprocess.check_output(
        ssh + ['/bin/cat /etc/sailfish-release'], timeout=10).decode():
    raise SystemExit('Endpoint is not Sailfish OS')
stage = '/home/art/test/' + output.name
subprocess.run(ssh + ['test ! -e ' + stage + ' && test ! -L ' + stage
                     + ' && install -d -m0700 ' + stage], check=True, timeout=10)
subprocess.run(['scp', '-O', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                *[str(output / name) for name in manifest['files']],
                'root@bonito:' + stage + '/'], check=True, timeout=15)
config = dict(boot=expected_boot, stage=stage, files=manifest['files'])
body = ('CONFIG=' + repr(config) + '\n' + r'''
from pathlib import Path
import hashlib,json,os
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
root=Path('/home/art');assert root.is_dir() and not root.is_symlink()
destinations={'tzdata':root/'usr/share/zoneinfo/tzdata',
              'icudt55l.dat':root/'usr/icu/icudt55l.dat',
              'graphics-interfaces-hostdex.jar':root/'java/dex/art/graphics-interfaces-hostdex.jar',
              'framework-compat-hostdex.jar':root/'java/dex/art/framework-compat-hostdex.jar'}
for name in CONFIG['files']:
 destination=destinations[name]
 source=Path(CONFIG['stage'])/name;pin=CONFIG['files'][name]
 assert not source.is_symlink() and source.stat().st_uid==0
 assert source.stat().st_size==pin['bytes'] and hashlib.sha256(source.read_bytes()).hexdigest()==pin['sha256']
 for parent in destination.parents:
  if parent==root:break
  assert not parent.is_symlink()
 if destination.exists() or destination.is_symlink():
  assert destination.is_file() and not destination.is_symlink()
  assert hashlib.sha256(destination.read_bytes()).hexdigest()==pin['sha256'],'Preserve differing existing runtime asset'
 else:
  destination.parent.mkdir(parents=True,exist_ok=True)
  with destination.open('xb') as f:f.write(source.read_bytes())
  destination.chmod(0o644)
 assert hashlib.sha256(destination.read_bytes()).hexdigest()==pin['sha256']
 print(json.dumps({'path':str(destination),'sha256':pin['sha256'],'bytes':pin['bytes']}),flush=True)
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
''').encode()
subprocess.run(ssh + ['python3 -'], input=body, check=True, timeout=15)
