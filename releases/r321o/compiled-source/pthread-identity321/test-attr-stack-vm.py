"""Read-only tests of supplied pthread/linker binaries; no runtime mutation."""
from pathlib import Path
import subprocess,argparse,json,os,hashlib
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--linker',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir();(a.out/'config').mkdir()
source=Path(__file__).with_name('attr-stack-fixture.c');exe=a.out/'attr-stack-fixture';subprocess.run(['gcc','-O2','-Wall','-Wextra','-pthread',str(source),'-ldl','-o',str(exe)],check=True)
guest_source=a.out/'guest.c';guest=a.out/'guest.so';guest_source.write_text('extern int pthread_attr_setstack(void*,void*,unsigned long);\nint guest_setstack(void*a,void*b,unsigned long n){return pthread_attr_setstack(a,b,n);}\nvoid*guest_setstack_address(void){return (void*)pthread_attr_setstack;}\n');subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-Wl,-z,separate-code',str(guest_source),'-o',str(guest)],check=True)
env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(a.out/'config'),LD_LIBRARY_PATH='/var/tmp/saidroid-native-service-lifecycle305-v1/payload/lib:/home/art/lib');rows=[]
for label,library,expected in [('baseline',a.baseline,7),('candidate',a.candidate,0)]:
 for mode in ['direct','android-relocation']:
  cmd=[str(exe),str(library.resolve()),mode];cmd+=[]if mode=='direct'else[str(a.linker.resolve()),str(guest.resolve())]
  q=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=20);row=dict(label=label,mode=mode,returncode=q.returncode,expected=expected,stdout=q.stdout,stderr=q.stderr);rows.append(row);(a.out/(label+'-'+mode+'.log')).write_text(q.stdout+q.stderr);print(json.dumps({k:v for k,v in row.items()if k!="stderr"}));assert q.returncode==expected,row
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
result=dict(passed=True,inputs={str(f):sha(f)for f in [source,a.baseline,a.candidate,a.linker]},rows=rows);(a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
