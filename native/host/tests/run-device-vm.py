#!/usr/bin/env python3
"""Serialized device gate launcher with automatic evidence collection.
Run inside MeeGo Build; the device scripts are host-side test tooling only.
"""
from pathlib import Path
import argparse,os,re,subprocess,hashlib,json
repo=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('gate',choices=['cold','multiapp']);p.add_argument('label');p.add_argument('--cards-only',action='store_true');p.add_argument('--close-only',action='store_true');a=p.parse_args();assert re.fullmatch('[a-z0-9-]+',a.label)
assert not(a.cards_only and a.close_only);assert not(a.cards_only or a.close_only)or a.gate=='multiapp';os.environ.setdefault('SSHPASS','sailfish');ssh=['sshpass','-e','ssh','-o','ConnectTimeout=8','root@bonito'];scp=['sshpass','-e','scp','-O','-o','ConnectTimeout=8'];evidence=repo/'build/evidence/native-host'/a.label;assert not evidence.exists();evidence.mkdir(parents=True)
lock=repo/'scripts/devlock.sh';subprocess.run(['bash',str(lock),'acquire','0',a.label],check=True,timeout=20)
try:
 source=Path(__file__).with_name('device-cold-launch.py'if a.gate=='cold'else'device-multiapp.py');(evidence/'device-source.py').write_bytes(source.read_bytes());(evidence/'test-input.json').write_text(json.dumps(dict(gate=a.gate,label=a.label,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),cards_only=a.cards_only,close_only=a.close_only),indent=2)+'\n');command=ssh+['python3','-',a.label]+(['cards-only']if a.cards_only else['close-only']if a.close_only else[])
 with(evidence/'device.log').open('wb')as log:r=subprocess.run(command,input=source.read_bytes(),stdout=log,stderr=subprocess.STDOUT,timeout=200)
 for source in ['/home/art/test/'+a.label,'/home/defaultuser/Downloads/SailDroid-Screenshots/matrix-'+a.label]:subprocess.run(scp+['-r','root@bonito:'+source,str(evidence)],timeout=45,check=False)
 r.check_returncode();print('NATIVE_DEVICE_GATE=PASS|evidence='+str(evidence))
finally:subprocess.run(['bash',str(lock),'release',a.label],check=True,timeout=20)
