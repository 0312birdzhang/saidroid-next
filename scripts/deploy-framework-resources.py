#!/usr/bin/env python3
"""Replace only the private framework resource APK, preserving the exact original."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

output = Path(sys.argv[1])
manifest = json.loads((output / 'manifest.json').read_text())
if manifest['schema'] != 'saidroid-framework-resources-v1':
    raise SystemExit('Unexpected framework resource manifest')
candidate = output / 'framework-res.apk'
digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
if digest != manifest['file']['sha256']:
    raise SystemExit('Resource candidate changed after packaging verification')
ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
boot = '5db879ed-48ea-4bf0-b5c1-64e271c11045'
if subprocess.check_output(ssh + ['/bin/cat /proc/sys/kernel/random/boot_id'], timeout=10).decode().strip() != boot:
    raise SystemExit('Refresh device identity before deployment')
stage = '/home/art/test/' + output.name
subprocess.run(ssh + ['test ! -e ' + stage + ' && install -d -m0700 ' + stage], check=True, timeout=10)
subprocess.run(['scp', '-O', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', str(candidate),
                'root@bonito:' + stage + '/framework-res.apk'], check=True, timeout=20)
config = dict(boot=boot, stage=stage, sha256=digest)
body = ('CONFIG=' + repr(config) + '\n' + r'''
from pathlib import Path
import hashlib,json,os,stat,subprocess
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:exe=os.readlink(process/'exe')
 except OSError:continue
 assert not exe.startswith('/home/art/bin/dalvikvm'),'An ART application is still active'
lipstick=subprocess.check_output(['pidof','lipstick'],text=True,timeout=3).strip()
assert len(lipstick.split())==1
def start(pid):
 raw=(Path('/proc')/pid/'stat').read_text()
 return raw[raw.rfind(') ')+2:].split()[19]
lipstick_start=start(lipstick)
target=Path('/home/art/framework/framework-res.apk')
assert target.is_file() and not target.is_symlink() and not target.parent.is_symlink()
s=target.stat();assert s.st_uid==0
old=target.read_bytes()
assert hashlib.sha256(old).hexdigest()=='304760dff9f0b3909cf092992e8c631876c9d3effdf60143a6aafe52e798ea29'
data=(Path(CONFIG['stage'])/'framework-res.apk').read_bytes()
assert hashlib.sha256(data).hexdigest()==CONFIG['sha256']
backup=target.with_name('framework-res.apk.before-codex-20261025')
assert not backup.exists() and not backup.is_symlink()
with backup.open('xb') as f:f.write(old);f.flush();os.fsync(f.fileno())
os.chown(backup,s.st_uid,s.st_gid);backup.chmod(stat.S_IMODE(s.st_mode))
temporary=target.with_name('framework-res.apk.codex-new')
assert not temporary.exists() and not temporary.is_symlink()
with temporary.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
os.chown(temporary,s.st_uid,s.st_gid);temporary.chmod(stat.S_IMODE(s.st_mode))
os.replace(temporary,target)
assert hashlib.sha256(target.read_bytes()).hexdigest()==CONFIG['sha256']
assert subprocess.check_output(['pidof','lipstick'],text=True,timeout=3).strip()==lipstick
assert start(lipstick)==lipstick_start
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
record=dict(result='private_framework_resources=ready',target=str(target),backup=str(backup),
 sha256=CONFIG['sha256'],boot=CONFIG['boot'],lipstick=lipstick,lipstick_start=lipstick_start)
(Path(CONFIG['stage'])/'installation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
''').encode()
subprocess.run(ssh + ['python3 -'], input=body, check=True, timeout=20)
