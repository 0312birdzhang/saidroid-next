#!/usr/bin/env python3
"""Install matched text-native declarations and real hyphenation data privately."""
from pathlib import Path
import subprocess,json,hashlib,sys
out=Path(sys.argv[1]);record=json.loads((out/'manifest.json').read_text())
assert hashlib.sha256((out/'framework3-hostdex.jar').read_bytes()).hexdigest()==record['new_sha256']
ssh=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','root@bonito']
stage='/home/art/test/'+out.name
subprocess.run(ssh+['test ! -e '+stage+' && install -d -m0700 '+stage],check=True,timeout=8)
subprocess.run(['scp','-O','-r','-o','BatchMode=yes',str(out/'framework3-hostdex.jar'),str(out/'hyphen-data'),'root@bonito:'+stage+'/'],check=True,timeout=20)
body=('CONFIG='+repr(dict(record,stage=stage))+'\n'+r'''
from pathlib import Path
import hashlib,os,stat,json,subprocess
assert Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='5db879ed-48ea-4bf0-b5c1-64e271c11045'
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text()
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:exe=os.readlink(process/'exe')
 except OSError:continue
 assert not exe.startswith('/home/art/bin/dalvikvm'),'Stop owned runtime before update'
root=Path('/home/art');target=root/'java/dex/art/framework3-hostdex.jar';source=Path(CONFIG['stage'])
assert not target.is_symlink()
old=target.read_bytes();assert hashlib.sha256(old).hexdigest()==CONFIG['original_sha256']
new=(source/'framework3-hostdex.jar').read_bytes();assert hashlib.sha256(new).hexdigest()==CONFIG['new_sha256']
for name,digest in CONFIG['dictionaries'].items():
 file=source/'hyphen-data'/name
 assert file.is_file()and not file.is_symlink()and hashlib.sha256(file.read_bytes()).hexdigest()==digest
 file.chmod(0o644)
destination=root/'usr/hyphen-data';assert not destination.exists()and not destination.is_symlink()
assert not destination.parent.is_symlink()
backup=target.with_name(target.name+'.before-codex-text-20261025');assert not backup.exists()
s=target.stat()
with backup.open('xb')as f:f.write(old)
os.chown(backup,s.st_uid,s.st_gid);backup.chmod(stat.S_IMODE(s.st_mode))
(source/'hyphen-data').chmod(0o755);(source/'hyphen-data').rename(destination)
temporary=target.with_name(target.name+'.text-new');assert not temporary.exists()
with temporary.open('xb')as f:f.write(new);f.flush();os.fsync(f.fileno())
os.chown(temporary,s.st_uid,s.st_gid);temporary.chmod(stat.S_IMODE(s.st_mode));os.replace(temporary,target)
print(json.dumps(dict(result='text_runtime=ready',sha256=CONFIG['new_sha256'],backup=str(backup))))
''').encode()
subprocess.run(ssh+['python3 -'],input=body,check=True,timeout=20)
