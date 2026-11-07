#!/usr/bin/env python3
"""Exercise real Toybox timestamp operations as an ordinary Linux UID."""
from pathlib import Path
import os,json,subprocess,tempfile,shutil,sys,hashlib
binary=Path(sys.argv[1]).resolve();folder=Path(tempfile.mkdtemp(prefix='saidroid-command-contract-',dir='/var/tmp'));os.chown(folder,65534,65534)
source=binary;binary=folder/'toybox';shutil.copyfile(source,binary);binary.chmod(0o755);assert binary.read_bytes()==source.read_bytes()
child=r'''from pathlib import Path
import json,os,subprocess,sys
folder=Path(sys.argv[1]);binary=sys.argv[2];os.chdir(folder);checks=[]
def run(*args,good=True):
 p=subprocess.run([binary,'touch',*map(str,args)],capture_output=True,text=True,timeout=5)
 assert (p.returncode==0)==good,(args,p.returncode,p.stdout,p.stderr)
 return p
f=folder/'file';f.write_text('private original content');run('-d','2015-10-09T00:00:00Z',f);assert f.stat().st_mtime_ns==1444348800000000000;checks.append('ISO-Z-real-mtime')
run('-d','2015-10-09T01:00:00+01:00',f,good=False);assert f.stat().st_mtime_ns==1444348800000000000;checks.append('unsupported-colon-offset-rejected-no-mutation')
run('-d','2015-10-09T00:00:00.123456789Z',f);assert f.stat().st_mtime_ns==1444348800123456789;checks.append('nanosecond-precision')
old=f.stat().st_mtime_ns;run('-d','invalid-date',f,good=False);assert f.stat().st_mtime_ns==old;checks.append('invalid-date-rejected-no-mutation')
run('-c',folder/'not-created');assert not(folder/'not-created').exists();checks.append('no-create')
os.utime(f,ns=(1000000000,2000000000));run('-a','-d','2015-10-09T00:00:00Z',f);assert f.stat().st_atime_ns==1444348800000000000 and f.stat().st_mtime_ns==2000000000;checks.append('atime-only')
run('-m','-d','2016-10-09T00:00:00Z',f);assert f.stat().st_atime_ns==1444348800000000000 and f.stat().st_mtime_ns==1475971200000000000;checks.append('mtime-only')
r=folder/'reference';r.write_text('reference');os.utime(r,ns=(1111111111,2222222222));run('-r',r,f);assert f.stat().st_atime_ns==1111111111 and f.stat().st_mtime_ns==2222222222;checks.append('reference-times')
link=folder/'link';link.symlink_to('file');run('-h','-d','2015-10-09T00:00:00Z',link);assert link.lstat().st_mtime_ns==1444348800000000000 and f.stat().st_mtime_ns==2222222222;checks.append('symlink-not-followed')
assert f.read_text()=='private original content';checks.append('contents-preserved');assert os.getuid()==65534
print(json.dumps(dict(passed=True,uid=os.getuid(),checks=checks,binary=binary)))
'''
try:
 p=subprocess.run([sys.executable,'-c',child,str(folder),str(binary)],capture_output=True,text=True,timeout=30,user=65534,group=65534,extra_groups=[]);assert p.returncode==0,p.stderr;r=json.loads(p.stdout);r.update(source=str(source),sha256=hashlib.sha256(source.read_bytes()).hexdigest());print(json.dumps(r))
finally:shutil.rmtree(folder)
