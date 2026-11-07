#!/usr/bin/env python3
"""Quarantine duplicate host-ABI bridge libraries from the Android loader path.

VM-side, bounded private-runtime repair. Each regular file must equal its
canonical /home/art/lib copy; symlinks must point to one of those duplicates.
"""
import json
import subprocess

ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
body = r'''
from pathlib import Path
import hashlib,json,os
boot=Path('/proc/sys/kernel/random/boot_id')
assert boot.read_text().strip()=='5db879ed-48ea-4bf0-b5c1-64e271c11045'
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
root=Path('/home/art'); source=root/'bio2'; host=root/'lib'
assert not root.is_symlink() and not source.is_symlink() and not host.is_symlink()
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:exe=os.readlink(process/'exe')
 except OSError:continue
 assert not exe.startswith('/home/art/bin/dalvikvm'),'Stop owned ART runs before rearranging private libraries'
lipstick=os.popen('pidof lipstick').read().strip()
assert len(lipstick.split())==1
before=(Path('/proc')/lipstick/'stat').read_text()
prefixes=('libc_bio.so','libdl_bio.so','libpthread_bio.so','libstdc++_bio.so')
files=sorted(f for f in source.iterdir() if any(f.name==p or f.name.startswith(p+'.') for p in prefixes))
assert files,'No misplaced bridges found; do not repeat a completed repair'
records=[]
for f in files:
 if f.is_symlink():
  target=f.resolve(strict=True)
  assert target.parent==source and target in files,'Unexpected bridge symlink target'
  records.append(dict(name=f.name,symlink=os.readlink(f)))
 else:
  canonical=host/f.name
  assert f.is_file() and canonical.is_file() and not canonical.is_symlink()
  digest=hashlib.sha256(f.read_bytes()).hexdigest()
  assert digest==hashlib.sha256(canonical.read_bytes()).hexdigest(),'Preserve differing bridge library'
  records.append(dict(name=f.name,sha256=digest,canonical=str(canonical)))
backup=root/'test/codex-native-layout-20261025-r1'
assert not backup.exists() and not backup.is_symlink()
backup.mkdir(mode=0o700)
(backup/'manifest.json').write_text(json.dumps(dict(boot=boot.read_text().strip(),files=records),indent=2)+'\n')
for f in files:f.rename(backup/f.name)
for record in records:
 if 'sha256' in record:
  assert hashlib.sha256((backup/record['name']).read_bytes()).hexdigest()==record['sha256']
assert not any(any(f.name==p or f.name.startswith(p+'.') for p in prefixes) for f in source.iterdir())
assert boot.read_text().strip()=='5db879ed-48ea-4bf0-b5c1-64e271c11045'
after=os.popen('pidof lipstick').read().strip()
assert after==lipstick
# Compare process start time, not mutable CPU counters in /proc/stat.
stat=(Path('/proc')/lipstick/'stat').read_text()
assert before[before.rfind(') ')+2:].split()[19]==stat[stat.rfind(') ')+2:].split()[19]
print(json.dumps(dict(result='native_library_layout=ready',backup=str(backup),files=len(files),lipstick=lipstick)))
'''
result = subprocess.run(ssh + ['python3 -'], input=body.encode(), capture_output=True, timeout=20)
print(result.stdout.decode(), end='')
print(result.stderr.decode(), end='')
raise SystemExit(result.returncode)
