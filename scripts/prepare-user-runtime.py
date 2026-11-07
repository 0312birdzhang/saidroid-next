#!/usr/bin/env python3
"""Make the existing /home/art component runnable by the existing Sailfish user.

Only private component metadata changes. Record original owners/modes before any
changes, never follow symlinks, and never alter a system account or system path.
"""
import subprocess

ssh = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'root@bonito']
body = r'''
from pathlib import Path
import hashlib,json,os,pwd,stat
boot=Path('/proc/sys/kernel/random/boot_id');expected='5db879ed-48ea-4bf0-b5c1-64e271c11045'
assert boot.read_text().strip()==expected
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
account=pwd.getpwnam('defaultuser');assert account.pw_uid>0
root=Path('/home/art');assert root.is_dir() and not root.is_symlink()
audit=root/'test/codex-user-runtime-20261025-r1'
assert not audit.exists() and not audit.is_symlink()
audit.mkdir(mode=0o700)
changes={}
def record(path,data):
 assert path==root or root in path.parents
 s=path.lstat()
 if stat.S_ISLNK(s.st_mode):return
 assert stat.S_ISDIR(s.st_mode)or stat.S_ISREG(s.st_mode),str(path)
 mode=stat.S_IMODE(s.st_mode)
 if data:
  new_uid=account.pw_uid;new_mode=0o700 if path.is_dir()else 0o600|(0o100 if mode&0o111 else 0)
 else:
  new_uid=s.st_uid
  new_mode=(mode&0o700)|0o040|(0o010 if path.is_dir()or mode&0o111 else 0)
 changes[str(path)]={'dev':s.st_dev,'inode':s.st_ino,'old_uid':s.st_uid,'old_gid':s.st_gid,
                    'old_mode':mode,'uid':new_uid,'gid':account.pw_gid,'mode':new_mode,'data':data}
def tree(path,data):
 assert path.is_dir() and not path.is_symlink(),str(path)
 for directory,dirs,files in os.walk(path,followlinks=False):
  record(Path(directory),data)
  for name in files:record(Path(directory)/name,data)
record(root,False);record(root/'env.sh',False);record(root/'test',False)
for name in ['bin','lib','bio2','java','framework','usr','realapps']:tree(root/name,False)
for name in ['data','storage']:tree(root/name,True)
plan={'schema':'saidroid-user-runtime-permissions-v1','boot':expected,
      'account':account.pw_name,'uid':account.pw_uid,'gid':account.pw_gid,'changes':changes}
raw=(json.dumps(plan,indent=2)+'\n').encode();plan_path=audit/'permissions-before.json'
with plan_path.open('xb')as f:f.write(raw)
plan_path.chmod(0o600)
for name,change in changes.items():
 path=Path(name);s=path.lstat()
 assert (s.st_dev,s.st_ino,s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))==(
  change['dev'],change['inode'],change['old_uid'],change['old_gid'],change['old_mode']),name
 os.chown(path,change['uid'],change['gid'],follow_symlinks=False)
 path.chmod(change['mode'])
assert boot.read_text().strip()==expected
print(json.dumps({'user_runtime':'ready','uid':account.pw_uid,'gid':account.pw_gid,
                  'managed_entries':len(changes),'data_entries':sum(v['data']for v in changes.values()),
                  'previous_metadata':str(plan_path),'previous_metadata_sha256':hashlib.sha256(raw).hexdigest()}))
'''.encode()
subprocess.run(ssh + ['python3 -'], input=body, check=True, timeout=45)
