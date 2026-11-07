#!/usr/bin/env python3
"""Install the tested private ART library with an exact previous-file backup."""
from pathlib import Path
import hashlib
import json
import subprocess

build = Path('/var/tmp/saidroid-next-jit-policy-20261025-r1')
art = Path('/tmp/art-build/art-standalone/out/host/linux-x86')
proof = json.loads((build / 'behavior-tests/proof.json').read_text())
source = art / 'lib64/libart.so'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
if proof['result'] != 'PASS' or sha(source) != proof['libart_sha256']:
    raise SystemExit('Native runtime changed after behavioral validation')
candidate = build / 'libart.stripped.so'
if candidate.exists():
    raise SystemExit('Preserve the existing native candidate')
subprocess.run(['cp', str(source), str(candidate)], check=True)
subprocess.run(['strip', '--strip-unneeded', str(candidate)], check=True)
if candidate.read_bytes()[:4] != b'\x7fELF':
    raise SystemExit('Native candidate is not ELF')
ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
boot = '5db879ed-48ea-4bf0-b5c1-64e271c11045'
if subprocess.check_output(ssh + ['/bin/cat /proc/sys/kernel/random/boot_id'], timeout=10).decode().strip() != boot:
    raise SystemExit('Refresh device identity before installing')
stage = '/home/art/test/codex-jit-loading-policy-20261025-r1'
subprocess.run(ssh + ['test ! -e ' + stage + ' && install -d -m0700 ' + stage], check=True, timeout=10)
subprocess.run(['scp', '-O', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                str(candidate), 'root@bonito:' + stage + '/libart.so'], check=True, timeout=20)
config = dict(boot=boot, stage=stage, candidate_sha256=sha(candidate))
body = ('CONFIG=' + repr(config) + '\n' + r'''
from pathlib import Path
import hashlib,json,os,stat
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
executables={(p.stat().st_dev,p.stat().st_ino) for p in
             [Path('/home/art/bin/dalvikvm'),Path('/home/art/bin/dex2oat')]}
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:s=(proc/'exe').stat()
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
 assert(s.st_dev,s.st_ino)not in executables,'Private ART is active: '+proc.name
target=Path('/home/art/lib/libart.so');assert target.is_file()and not target.is_symlink()
s=target.stat();assert s.st_uid==0 and not s.st_mode&0o022
old=target.read_bytes();candidate=(Path(CONFIG['stage'])/'libart.so').read_bytes()
assert hashlib.sha256(candidate).hexdigest()==CONFIG['candidate_sha256']
backup=target.with_name('libart.so.before-codex-jit-20261025')
assert not backup.exists()and not backup.is_symlink()
with backup.open('xb')as f:f.write(old);f.flush();os.fsync(f.fileno())
os.chown(backup,s.st_uid,s.st_gid);backup.chmod(stat.S_IMODE(s.st_mode))
temporary=target.with_name('libart.so.codex-new');assert not temporary.exists()
with temporary.open('xb')as f:f.write(candidate);f.flush();os.fsync(f.fileno())
os.chown(temporary,s.st_uid,s.st_gid);temporary.chmod(stat.S_IMODE(s.st_mode))
os.replace(temporary,target)
fd=os.open(str(target.parent),os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
assert hashlib.sha256(target.read_bytes()).hexdigest()==CONFIG['candidate_sha256']
result={'native_art_install':'ready','target':str(target),
        'sha256':CONFIG['candidate_sha256'],'previous_sha256':hashlib.sha256(old).hexdigest(),
        'backup':str(backup),'boot':CONFIG['boot']}
(Path(CONFIG['stage'])/'installation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
''').encode()
subprocess.run(ssh + ['python3 -'], input=body, check=True, timeout=25)
subprocess.run(['scp', '-O', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                'root@bonito:' + stage + '/installation.json', str(build / 'device-installation.json')],
               check=True, timeout=10)
