"""Real ELF relocations: data/function name collisions must retain writable storage."""
from pathlib import Path
import subprocess,tempfile,argparse,os,json
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sd-object321-')as directory:
 root=Path(directory);(root/'config').mkdir()
 (root/'fixture.c').write_text('''typedef int(*fn)(void);fn collision;extern int imported(void);int defined_function(void){return 3;}int check(void){collision=defined_function;return collision()+imported();}\n''')
 subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-Wl,-z,relro','-Wl,-z,separate-code','-o',str(root/'fixture.so'),str(root/'fixture.c')],check=True)
 (root/'run.c').write_text(r'''
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
int bionic_collision(void){return 99;}
int bionic_imported(void){return 39;}
int main(int argc,char**argv){assert(argc==4);void*l=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(l);void*(*open)(const char*,int)=dlsym(l,"bionic_dlopen");void*(*sym)(void*,const char*)=dlsym(l,"bionic_dlsym");int(*close)(void*)=dlsym(l,"bionic_dlclose");int(*add)(const char*)=dlsym(l,"bionic_add_library_path");assert(open&&sym&&close&&add&&!add(argv[3]));void*h=open(argv[2],RTLD_NOW);assert(h);int(*check)(void)=sym(h,"check");assert(check&&check()==42&&check()==42);assert(bionic_collision()==99);assert(!close(h));puts("DEFINED_OBJECT=PASS|local-data-writable|function-hook-preserved|repeat-call|host-function-unchanged");}
''')
 subprocess.run(['gcc','-O2','-Wall','-Wextra','-Werror','-Wl,--export-dynamic','-o',str(root/'run'),str(root/'run.c'),'-ldl'],check=True)
 env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(root/'config'),LD_LIBRARY_PATH='/var/tmp/saidroid-native-service-lifecycle305-v1/payload/lib:/home/art/lib');rows=[]
 for label,library,expected in [('baseline',a.baseline,-11),('candidate',a.candidate,0)]:
  q=subprocess.run([str(root/'run'),str(library.resolve()),str(root/'fixture.so'),str(root)],env=env,capture_output=True,text=True,timeout=10);(a.out/(label+'.stdout')).write_text(q.stdout);(a.out/(label+'.stderr')).write_text(q.stderr);print(label,q.returncode,q.stdout,flush=True);assert q.returncode==expected,q.stderr[-3500:];rows.append(dict(label=label,rc=q.returncode,stdout=q.stdout))
 (a.out/'result.json').write_text(json.dumps(dict(passed=True,results=rows),indent=2)+'\n')
