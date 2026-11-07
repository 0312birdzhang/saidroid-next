"""NOLOAD must preserve constructors, residency, reference counts, and dlerror."""
from pathlib import Path
import argparse,subprocess,tempfile,os,json
p=argparse.ArgumentParser();p.add_argument('linker',type=Path);a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='sd-noload320-')as directory:
 root=Path(directory);(root/'config').mkdir()
 (root/'fixture.c').write_text('extern void event(int);__attribute__((constructor))static void init(void){event(1);}\n__attribute__((destructor))static void fini(void){event(-1);}\nint identity(void){return 81;}\n')
 subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-Wl,-soname,fixture.so','-o',str(root/'fixture.so'),str(root/'fixture.c')],check=True)
 (root/'run.c').write_text(r'''
#define _GNU_SOURCE
#include <dlfcn.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
static int creates,destroys;
void event(int which){if(which==1)++creates;else if(which==-1)++destroys;}
int main(int argc,char**argv){
 assert(argc==4);void*l=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(l);
 void*(*open)(const char*,int)=dlsym(l,"bionic_dlopen");void*(*sym)(void*,const char*)=dlsym(l,"bionic_dlsym");int(*close)(void*)=dlsym(l,"bionic_dlclose");const char*(*error)(void)=dlsym(l,"bionic_dlerror");int(*add)(const char*)=dlsym(l,"bionic_add_library_path");assert(open&&sym&&close&&error&&add);assert(!add(argv[2]));
 void*q=open(argv[3],RTLD_NOW|RTLD_NOLOAD);
 if(q){fprintf(stderr,"NOLOAD_BUG mapped=%p constructors=%d\n",q,creates);return 7;}
 assert(creates==0&&destroys==0);const char*e=error();assert(e&&strstr(e,"not loaded"));assert(!error());
 void*h=open(argv[3],RTLD_NOW);assert(h&&creates==1&&destroys==0);int(*identity)(void)=sym(h,"identity");assert(identity&&identity()==81);
 q=open(argv[3],RTLD_NOW|RTLD_NOLOAD);assert(q==h&&creates==1);assert(!close(q));assert(identity()==81&&destroys==0);
 q=open("fixture.so",RTLD_LAZY|RTLD_NOLOAD);assert(q==h);assert(!close(h));assert(identity()==81&&destroys==0);assert(!close(q)&&destroys==1);
 assert(!open(argv[3],RTLD_NOW|RTLD_NOLOAD));assert(creates==1&&destroys==1&&error()&&!error());
 void*core=open("libc.so.6",RTLD_NOW|RTLD_NOLOAD);assert(core);assert(sym(core,"strlen"));assert(!close(core));
 assert(!open("not-installed-sd-noload320.so",RTLD_NOW|RTLD_NOLOAD));assert(error()&&!error());
 puts("NOLOAD=PASS|absent-unmapped|constructors=1|destructors=1|reference-counts|glibc-already-loaded|errors-thread-owned");
}
''')
 subprocess.run(['gcc','-O2','-Wl,--export-dynamic','-o',str(root/'run'),str(root/'run.c'),'-ldl'],check=True)
 env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(root/'config'));q=subprocess.run([str(root/'run'),str(a.linker.resolve()),str(root),str(root/'fixture.so')],env=env,capture_output=True,text=True,timeout=10);print(json.dumps(dict(exit=q.returncode,stdout=q.stdout,stderr=q.stderr[-2200:])));assert q.returncode==0
