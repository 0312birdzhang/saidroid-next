"""Check real page protections and constructor/function/data behavior."""
from pathlib import Path
import argparse,tempfile,subprocess,os,json
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sd-segment321-')as directory:
 root=Path(directory);(root/'config').mkdir()
 (root/'fixture.c').write_text('''extern void inspect(void*,void*,void*);static const char ro[]="read-only";static int data=41;int next(void){return ++data;}__attribute__((constructor))static void init(void){inspect((void*)next,(void*)ro,(void*)&data);}\n''')
 subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both','-Wl,-z,relro','-Wl,-z,separate-code','-Wl,-z,max-page-size=4096','-o',str(root/'fixture.so'),str(root/'fixture.c')],check=True)
 (root/'run.c').write_text(r'''
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static int constructors,correct=1;
static int permission(void*p,const char*expected){
 FILE*f=fopen("/proc/self/maps","r");assert(f);char line[1024],perms[5];unsigned long lo,hi;int found=0;
 while(fgets(line,sizeof(line),f))if(sscanf(line,"%lx-%lx %4s",&lo,&hi,perms)==3&&(uintptr_t)p>=lo&&(uintptr_t)p<hi){found=1;printf("SEGMENT|address=%p|actual=%s|expected=%s\n",p,perms,expected);correct&=!strncmp(perms,expected,3);break;}
 fclose(f);assert(found);return correct;
}
void inspect(void*code,void*ro,void*data){++constructors;permission(code,"r-x");permission(ro,"r--");permission(data,"rw-");}
int main(int argc,char**argv){assert(argc==4);void*l=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(l);void*(*open)(const char*,int)=dlsym(l,"bionic_dlopen");void*(*sym)(void*,const char*)=dlsym(l,"bionic_dlsym");int(*close)(void*)=dlsym(l,"bionic_dlclose");int(*add)(const char*)=dlsym(l,"bionic_add_library_path");assert(open&&sym&&close&&add&&!add(argv[3]));void*h=open(argv[2],RTLD_NOW);assert(h);int(*next)(void)=sym(h,"next");assert(next&&constructors==1&&next()==42&&next()==43);assert(!close(h));if(!correct)return 7;puts("SEGMENT_PROTECTION=PASS|constructor-sees-final-permissions|code=rx|rodata=r|data=rw|function-and-state=unchanged");}
''')
 subprocess.run(['gcc','-O2','-Wall','-Wextra','-Werror','-Wl,--export-dynamic','-o',str(root/'run'),str(root/'run.c'),'-ldl'],check=True)
 env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(root/'config'),LD_LIBRARY_PATH='/var/tmp/saidroid-native-service-lifecycle305-v1/payload/lib:/home/art/lib');results=[]
 for name,path,code in [('baseline',a.baseline,7),('candidate',a.candidate,0)]:
  q=subprocess.run([str(root/'run'),str(path.resolve()),str(root/'fixture.so'),str(root)],env=env,capture_output=True,text=True,timeout=15);(a.out/(name+'.stdout')).write_text(q.stdout);(a.out/(name+'.stderr')).write_text(q.stderr);print(name,q.returncode,q.stdout,flush=True);assert q.returncode==code,q.stderr;results.append(dict(label=name,returncode=q.returncode,stdout=q.stdout))
 (a.out/'result.json').write_text(json.dumps(dict(passed=True,results=results),indent=2)+'\n')
