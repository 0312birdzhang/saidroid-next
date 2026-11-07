from pathlib import Path
import subprocess,json,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args();a.output.mkdir();repo=Path(__file__).resolve().parents[3];old=repo/'build/hwui/pthread-helper/libpthread.c';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();expected='633c378247b5f40db3832f8ba39c5c7ace8a6efc6cd2efa43e72f2a5d2ade878';commands=[]
def compile(source,target,extra=[]):
 cmd=['gcc','-shared','-fPIC','-O2','-D_GNU_SOURCE','-fno-exceptions','-Wl,-soname,libpthread_bio.so.0','-Wl,--no-as-needed','-o',str(target),str(source),*map(str,extra),'-ldl','-lpthread'];commands.append(cmd)
 with(a.output/(target.name+'.log')).open('w')as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=60)
compile(old,a.output/'baseline.so');assert sha(a.output/'baseline.so')==expected,'Accepted baseline differs'
s=old.read_text()
for name in ['pthread_create','pthread_getattr_np']:
 assert s.count('int bionic_'+name+'(')==1;s=s.replace('int bionic_'+name+'(','int sd_legacy_bionic_'+name+'(',1)
source=a.output/'legacy.c';source.write_text(s);compile(source,a.output/'libpthread_bio.so.0',[Path(__file__).parent/'thread-identity.c'])
result=dict(passed=True,baseline_byte_identical=True,baseline_sha256=expected,sha256=sha(a.output/'libpthread_bio.so.0'),path=str(a.output/'libpthread_bio.so.0'),sources={str(old):sha(old),str(source):sha(source),str(Path(__file__).parent/'thread-identity.c'):sha(Path(__file__).parent/'thread-identity.c')},commands=commands);(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in ['sources','commands']}))
