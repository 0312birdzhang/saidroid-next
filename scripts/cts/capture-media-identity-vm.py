#!/usr/bin/env python3
"""Read the real private frontend and host software-codec identities.

No processes, codec configuration, routes or device state are modified.
"""
from pathlib import Path
import argparse,json,os,subprocess

p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--root',required=True);p.add_argument('--expected-boot',required=True);p.add_argument('--allow-unmapped',action='store_true');a=p.parse_args()
assert not a.output.exists();assert a.root.startswith('/home/art/releases/api29-r')
body='ROOT='+repr(a.root)+'\nEXPECTED_BOOT='+repr(a.expected_boot)+'\nREQUIRE_MAPPING='+repr(not a.allow_unmapped)+'\n'+r'''
from pathlib import Path
import hashlib,json,os,stat
assert 'ID=sailfishos' in Path('/etc/sailfish-release').read_text()
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();assert boot==EXPECTED_BOOT
def identity(file):
 file=Path(file);real=file.resolve(strict=True);s=real.stat();assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and s.st_size<32*1024*1024
 return dict(path=str(file),canonical=str(real),sha256=hashlib.sha256(real.read_bytes()).hexdigest(),bytes=s.st_size)
root=Path(ROOT);private={name:identity(root/'android-libs'/name)for name in ['libmedia_jni.so','libstagefright.so','libmediandk.so']}
host=identity('/system/lib/vndk-28/libstagefright_soft_vpxenc.so')
vendor=identity('/vendor/etc/media_codecs_performance.xml')
processes=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  maps=(proc/'maps').read_text()
  if host['canonical'] not in maps and host['path'] not in maps:continue
  fields=dict(line.split(':',1)for line in(proc/'status').read_text().splitlines()if ':' in line)
  processes.append(dict(pid=int(proc.name),uid=fields['Uid'].split()[0],executable=str((proc/'exe').resolve()),start_ticks=(proc/'stat').read_text().split(') ',1)[1].split()[19],mapped_codec=host['canonical']))
 except (FileNotFoundError,ProcessLookupError,PermissionError):continue
assert processes or not REQUIRE_MAPPING,'The actual host VP8 encoder mapping is required for measurement provenance'
print(json.dumps(dict(scope='Read-only actual media implementation identity',boot=boot,private_root=ROOT,private=private,host_encoder=host,host_performance_xml=vendor,host_codec_processes=sorted(processes,key=lambda v:v['pid'])),indent=2))
'''
env=dict(os.environ,SSHPASS=os.environ['SSHPASS'])
result=subprocess.run(['sshpass','-e','ssh','-o','ConnectTimeout=6','root@bonito','python3','-'],input=body,text=True,capture_output=True,timeout=18,env=env)
assert result.returncode==0,result.stderr
value=json.loads(result.stdout);a.output.write_text(json.dumps(value,indent=2)+'\n');print('MEDIA_IDENTITY=recorded|host_encoder_mappings='+str(len(value['host_codec_processes'])))
