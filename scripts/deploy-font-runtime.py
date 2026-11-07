#!/usr/bin/env python3
"""Install the verified private font payload and its two path-only class changes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

output = Path(sys.argv[1])
manifest = json.loads((output / 'manifest.json').read_text())
if manifest['schema'] != 'saidroid-private-font-runtime-v1':
    raise SystemExit('Unexpected private font manifest')
if hashlib.sha256((output / 'framework2-hostdex.jar').read_bytes()).hexdigest() != manifest['new_jar_sha256']:
    raise SystemExit('Framework candidate changed after verification')
boot = '5db879ed-48ea-4bf0-b5c1-64e271c11045'
ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
if subprocess.check_output(ssh + ['/bin/cat /proc/sys/kernel/random/boot_id'], timeout=10).decode().strip() != boot:
    raise SystemExit('Refresh device identity before installation')
stage = '/home/art/test/' + output.name
subprocess.run(ssh + ['test ! -e ' + stage + ' && install -d -m0700 ' + stage], check=True, timeout=10)
subprocess.run(['scp', '-O', '-r', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                str(output / 'fonts'), str(output / 'fonts.xml'), str(output / 'framework2-hostdex.jar'),
                'root@bonito:' + stage + '/'], check=True, timeout=45)
config = dict(manifest, boot=boot, stage=stage)
body = ('CONFIG=' + repr(config) + '\n' + r'''
from pathlib import Path
import hashlib,json,os,stat,subprocess
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:exe=os.readlink(process/'exe')
 except OSError:continue
 assert not exe.startswith('/home/art/bin/dalvikvm'),'Private ART application is active'
lipstick=subprocess.check_output(['pidof','lipstick'],text=True,timeout=3).strip()
assert len(lipstick.split())==1
def start(pid):
 raw=(Path('/proc')/pid/'stat').read_text();return raw[raw.rfind(') ')+2:].split()[19]
lipstick_start=start(lipstick)
root=Path('/home/art');stage=Path(CONFIG['stage'])
for p in [root,root/'etc',root/'fonts',root/'etc/fonts.xml',root/'java/dex/art']:
 assert not p.is_symlink()
assert not(root/'fonts').exists() and not(root/'etc/fonts.xml').exists(),'Preserve existing font installation'
assert {p.name for p in(stage/'fonts').iterdir()}==set(CONFIG['fonts'])
for name,record in CONFIG['fonts'].items():
 p=stage/'fonts'/name;assert p.is_file()and not p.is_symlink()
 assert p.stat().st_size==record['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
 p.chmod(0o644)
assert hashlib.sha256((stage/'fonts.xml').read_bytes()).hexdigest()==CONFIG['config_sha256']
candidate=(stage/'framework2-hostdex.jar').read_bytes()
assert hashlib.sha256(candidate).hexdigest()==CONFIG['new_jar_sha256']
target=root/'java/dex/art/framework2-hostdex.jar';assert target.is_file() and not target.is_symlink()
s=target.stat();assert s.st_uid==0
old=target.read_bytes();assert hashlib.sha256(old).hexdigest()==CONFIG['original_jar_sha256']
backup=target.with_name(target.name+'.before-codex-fonts-20261025')
assert not backup.exists()and not backup.is_symlink()
with backup.open('xb')as f:f.write(old);f.flush();os.fsync(f.fileno())
os.chown(backup,s.st_uid,s.st_gid);backup.chmod(stat.S_IMODE(s.st_mode))
(stage/'fonts').chmod(0o755)
(stage/'fonts.xml').chmod(0o644)
(stage/'fonts').rename(root/'fonts')
(stage/'fonts.xml').rename(root/'etc/fonts.xml')
temporary=target.with_name(target.name+'.codex-fonts-new')
assert not temporary.exists()and not temporary.is_symlink()
with temporary.open('xb')as f:f.write(candidate);f.flush();os.fsync(f.fileno())
os.chown(temporary,s.st_uid,s.st_gid);temporary.chmod(stat.S_IMODE(s.st_mode))
os.replace(temporary,target)
assert hashlib.sha256(target.read_bytes()).hexdigest()==CONFIG['new_jar_sha256']
assert subprocess.check_output(['pidof','lipstick'],text=True,timeout=3).strip()==lipstick
assert start(lipstick)==lipstick_start
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
record=dict(result='private_font_runtime=ready',framework_sha256=CONFIG['new_jar_sha256'],
 fonts=len(CONFIG['fonts']),backup=str(backup),boot=CONFIG['boot'],lipstick=lipstick)
(stage/'installation.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
''').encode()
subprocess.run(ssh + ['python3 -'], input=body, check=True, timeout=30)
