"""Two incompatible same-SONAME dependency groups must keep their own state."""
from pathlib import Path
import subprocess,tempfile,os,json,argparse
p=argparse.ArgumentParser();p.add_argument('linker',type=Path);a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='sd-origin320-')as directory:
 root=Path(directory);(root/'config').mkdir()
 for label,value in [('platform',17),('application',93)]:
  out=root/label;out.mkdir()
  def lib(name,body,*flags):
   (out/(name+'.c')).write_text(body);subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-o',str(out/(name+'.so')),str(out/(name+'.c')),*flags],check=True)
  lib('same',f'static int count={value};int value(void){{return count++;}}','-Wl,-soname,libsame.so')
  (out/'libsame.so').symlink_to('same.so')
  lib('entry','extern int value(void);int entry(void){return value();}','-L'+str(out),'-Wl,--no-as-needed','-lsame')
 c=root/'run.c';c.write_text(r'''
#define _GNU_SOURCE
#include <dlfcn.h>
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
 assert(argc==5);void*l=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(l);
 void*(*open)(const char*,int)=dlsym(l,"bionic_dlopen");void*(*sym)(void*,const char*)=dlsym(l,"bionic_dlsym");int(*close)(void*)=dlsym(l,"bionic_dlclose");int(*add)(const char*)=dlsym(l,"bionic_add_library_path");assert(!add(argv[2]));
 void*p=open(argv[3],RTLD_NOW);assert(p);int(*pv)(void)=sym(p,"entry");assert(pv&&pv()==17);
 void*a=open(argv[4],RTLD_NOW);assert(a&&a!=p);int(*av)(void)=sym(a,"entry");assert(av&&av()==93);assert(pv()==18&&av()==94);
 void*a2=open(argv[4],RTLD_NOW);assert(a2==a&&av()==95);assert(!close(a2));assert(!close(a));assert(pv()==19);assert(!close(p));puts("ORIGIN_DEPENDENCY=PASS");
}
''');subprocess.run(['gcc','-O2','-o',str(root/'run'),str(c),'-ldl'],check=True)
 env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(root/'config'));q=subprocess.run([str(root/'run'),str(a.linker.resolve()),str(root/'platform')+':'+str(root/'application'),str(root/'platform/entry.so'),str(root/'application/entry.so')],capture_output=True,text=True,env=env,timeout=10);print(json.dumps(dict(exit=q.returncode,stdout=q.stdout,stderr=q.stderr[-2200:])));assert q.returncode==0
