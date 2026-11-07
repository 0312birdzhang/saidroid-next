#!/usr/bin/env python3
"""Bounded read-only phone HIDL Keymaster readiness; never touches key stores.

Run inside the configured build VM. This inspects public process/device/ELF
metadata only: no HAL RPC, credential enrollment, key creation or service change.
"""
from pathlib import Path
import argparse,json,os,subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--expected-boot',required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();assert not a.output.exists()
body='EXPECTED_BOOT='+repr(a.expected_boot)+'\n'+r'''
from pathlib import Path
import os,json,hashlib,stat,struct
assert 'ID=sailfishos'in Path('/etc/sailfish-release').read_text()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==EXPECTED_BOOT
processes=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  command=(proc/'cmdline').read_bytes().split(b'\0')[0].decode()
  if not command.startswith(('/vendor/bin/hw/android.hardware.keymaster','/system/bin/hwservicemanager')):continue
  exe=Path(os.readlink(proc/'exe'));metadata=exe.stat();raw=exe.read_bytes();assert raw[:4]==b'\x7fELF'
  status=(proc/'status').read_text().splitlines();fields=(proc/'stat').read_text().rsplit(') ',1)[1].split()
  maps=(proc/'maps').read_text().splitlines();paths=sorted({line.split()[-1]for line in maps if len(line.split())>=6 and line.split()[-1].startswith('/')})
  processes.append(dict(pid=int(proc.name),executable=str(exe),start_ticks=fields[19],uid=next(l.split()[1:]for l in status if l.startswith('Uid:')),gid=next(l.split()[1:]for l in status if l.startswith('Gid:')),elf_class=raw[4],machine=struct.unpack('<H',raw[18:20])[0],binary_sha256=hashlib.sha256(raw).hexdigest(),binary_uid=metadata.st_uid,binary_mode=oct(stat.S_IMODE(metadata.st_mode)),public_mapped_library_paths=[n for n in paths if any(x in n.lower()for x in ['keymaster','hidl','hwbinder','qsee','libc++'])]))
 except FileNotFoundError:pass
nodes=[]
for name in ['/dev/hwbinder','/dev/binder','/dev/vndbinder','/sys/fs/selinux/enforce']:
 node=Path(name);entry=dict(path=name,present=node.exists())
 if node.exists():
  s=node.stat();entry.update(mode=oct(stat.S_IMODE(s.st_mode)),uid=s.st_uid,gid=s.st_gid,char_device=stat.S_ISCHR(s.st_mode))
  if stat.S_ISCHR(s.st_mode):entry.update(major=os.major(s.st_rdev),minor=os.minor(s.st_rdev))
  if name.endswith('/enforce'):entry['value']=node.read_text().strip()
 nodes.append(entry)
print(json.dumps(dict(scope='Read-only public phone Keymaster/HIDL process, ELF, library path and device-node inventory; no HAL calls, key/credential data reads, signal/service changes, deployment or hardware-security acceptance.',boot=boot,processes=processes,nodes=nodes,brightness=Path('/sys/class/backlight/panel0-backlight/actual_brightness').read_text().strip())))
'''
r=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input=body,text=True,capture_output=True,timeout=12,env=dict(os.environ,SSHPASS=os.environ['SSHPASS']));assert r.returncode==0,r.stderr
v=json.loads(r.stdout);assert v['boot']==a.expected_boot and v['brightness']=='0'
a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))
