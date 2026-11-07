#!/usr/bin/env python3
"""Integrate verified API additions into the existing default framework classpath.

The temporary boot-append proof changes component count only in the parent VM;
the standalone ART compiler child uses its default classpath. Merge into the last
framework dex instead, retaining all original classes and a device backup.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess
import sys
import zipfile

mode = sys.argv[1]
output = Path(sys.argv[2])
if not str(output).startswith('/var/tmp/saidroid-next-'):
    raise SystemExit('Isolated VM output required')
ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
boot = '5db879ed-48ea-4bf0-b5c1-64e271c11045'
target = '/home/art/java/dex/art/framework4-hostdex.jar'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def definitions(data):
    def u32(offset):
        return struct.unpack_from('<I', data, offset)[0]
    if not data.startswith(b'dex\n'):
        raise ValueError('Expected dex input')
    strings, types, count, table = u32(60), u32(68), u32(96), u32(100)
    result = set()
    for index in range(count):
        string = u32(types + 4 * u32(table + index * 32))
        offset = u32(strings + 4 * string)
        for _ in range(5):
            value = data[offset]
            offset += 1
            if not value & 128:
                break
        else:
            raise ValueError('Invalid dex string length')
        end = data.index(0, offset)
        result.add(data[offset:end].decode('utf-8'))
    if len(result) != count:
        raise ValueError('Duplicate dex class definitions')
    return result

if mode == 'prepare':
    assets = Path(sys.argv[3])
    output.mkdir(mode=0o700)
    observed = subprocess.check_output(ssh + ['/bin/cat /proc/sys/kernel/random/boot_id'], timeout=10)
    if observed.decode().strip() != boot:
        raise SystemExit('Device boot changed')
    subprocess.run(['scp', '-O', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                    'root@bonito:' + target, str(output / 'original-framework4.jar')],
                   check=True, timeout=15)
    with zipfile.ZipFile(output / 'original-framework4.jar') as archive:
        original = archive.read('classes.dex')
    with zipfile.ZipFile(assets / 'framework-compat-hostdex.jar') as archive:
        extra = archive.read('classes.dex')
    before, additions = definitions(original), definitions(extra)
    if before & additions:
        raise SystemExit('Do not replace existing framework class definitions')
    (output / 'original.dex').write_bytes(original)
    (output / 'additions.dex').write_bytes(extra)
    subprocess.run(['/tmp/jdkfull/jdk-21.0.13+9/bin/java', '-cp',
                    '/tmp/art-build/art-standalone/out/host/linux-x86/framework/dx.jar',
                    'com.android.dx.merge.DexMerger', str(output / 'merged.dex'),
                    str(output / 'original.dex'), str(output / 'additions.dex')], check=True)
    merged = (output / 'merged.dex').read_bytes()
    if definitions(merged) != before | additions:
        raise SystemExit('Merged framework class inventory changed')
    with zipfile.ZipFile(output / 'framework4-hostdex.jar', 'w') as archive:
        info = zipfile.ZipInfo('classes.dex', (1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, merged)
    manifest = dict(schema='saidroid-default-framework-completion-v1', boot=boot,
                    target=target, original_sha256=sha(output / 'original-framework4.jar'),
                    new_sha256=sha(output / 'framework4-hostdex.jar'),
                    additions_sha256=sha(assets / 'framework-compat-hostdex.jar'),
                    original_classes=len(before), added_classes=len(additions),
                    total_classes=len(before | additions))
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))
elif mode == 'install':
    manifest = json.loads((output / 'manifest.json').read_text())
    if manifest['boot'] != boot or manifest['target'] != target:
        raise SystemExit('Unexpected framework manifest identity')
    if sha(output / 'framework4-hostdex.jar') != manifest['new_sha256']:
        raise SystemExit('Framework candidate checksum changed')
    stage = '/home/art/test/' + output.name
    subprocess.run(ssh + ['test ! -e ' + stage + ' && install -d -m0700 ' + stage],
                   check=True, timeout=10)
    subprocess.run(['scp', '-O', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5',
                    str(output / 'framework4-hostdex.jar'), 'root@bonito:' + stage + '/candidate.jar'],
                   check=True, timeout=15)
    config = dict(manifest, stage=stage)
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
 assert(s.st_dev,s.st_ino)not in executables,'Private ART process still active: '+proc.name
target=Path(CONFIG['target']);assert target.is_file()and not target.is_symlink()
s=target.stat();assert s.st_uid==0 and not s.st_mode&0o022
original=target.read_bytes();assert hashlib.sha256(original).hexdigest()==CONFIG['original_sha256']
candidate=(Path(CONFIG['stage'])/'candidate.jar').read_bytes()
assert hashlib.sha256(candidate).hexdigest()==CONFIG['new_sha256']
backup=target.with_name(target.name+'.before-codex-20261025')
assert not backup.exists()and not backup.is_symlink()
with backup.open('xb')as f:f.write(original);f.flush();os.fsync(f.fileno())
os.chown(backup,s.st_uid,s.st_gid);backup.chmod(stat.S_IMODE(s.st_mode))
temporary=target.with_name(target.name+'.codex-new');assert not temporary.exists()
with temporary.open('xb')as f:f.write(candidate);f.flush();os.fsync(f.fileno())
os.chown(temporary,s.st_uid,s.st_gid);temporary.chmod(stat.S_IMODE(s.st_mode))
os.replace(temporary,target)
fd=os.open(str(target.parent),os.O_RDONLY|os.O_DIRECTORY);os.fsync(fd);os.close(fd)
assert hashlib.sha256(target.read_bytes()).hexdigest()==CONFIG['new_sha256']
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()==CONFIG['boot']
print(json.dumps({'framework_install':'ready','target':str(target),'sha256':CONFIG['new_sha256'],'backup':str(backup)}))
''').encode()
    subprocess.run(ssh + ['python3 -'], input=body, check=True, timeout=20)
else:
    raise SystemExit('Use prepare or install')
