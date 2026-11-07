"""Real ELF dependency-group relocation and failed-load rollback contracts."""
from pathlib import Path
import argparse, json, os, resource, subprocess, tempfile

p = argparse.ArgumentParser()
p.add_argument('linker', type=Path)
a = p.parse_args()
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
with tempfile.TemporaryDirectory(prefix='sd-linker-groups-') as directory:
    out = Path(directory)
    (out/'config').mkdir()
    def library(name, body, *flags):
        source = out/(name+'.c')
        source.write_text(body)
        subprocess.run(['gcc', '-shared', '-fPIC', '-nostdlib',
                        '-Wl,--hash-style=both', '-o', str(out/(name+'.so')),
                        str(source), *flags], check=True)
    library('provider', 'extern void fixture_init(void);extern void fixture_fini(void);__attribute__((constructor))static void init(void){fixture_init();}__attribute__((destructor))static void fini(void){fixture_fini();}int provided(void){return 73;}')
    library('middle', 'extern int provided(void);int middle(void){return provided();}',
            '-Wl,--no-as-needed', str(out/'provider.so'))
    library('top', 'extern int provided(void);int value(void){return provided()+1;}',
            '-Wl,--no-as-needed', str(out/'middle.so'))
    library('bad', 'extern int absent(void);int value(void){return absent();}',
            '-Wl,--no-as-needed', str(out/'middle.so'), '-Wl,-soname,failed.so')
    library('good', 'int value(void){return 91;}', '-Wl,-soname,failed.so')
    library('unrelated', 'extern int provided(void);int value(void){return provided();}')
    runner = out/'test.c'
    runner.write_text(r'''
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
static int initialized,finalized;
void fixture_init(void){initialized++;}
void fixture_fini(void){finalized++;}
static void *(*open_guest)(const char*,int);
static void *(*symbol_guest)(void*,const char*);
static int (*close_guest)(void*);
static const char *(*error_guest)(void);
static void *load(const char *name){return open_guest(name,RTLD_NOW);}
static int mapped(const char *name){
 FILE *file=fopen("/proc/self/maps","r");assert(file);char line[8192];int found=0;
 while(fgets(line,sizeof(line),file))if(strstr(line,name))found=1;
 fclose(file);return found;
}
int main(int argc,char **argv){
 assert(argc==4);void *linker=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(linker);
 open_guest=dlsym(linker,"bionic_dlopen");symbol_guest=dlsym(linker,"bionic_dlsym");
 close_guest=dlsym(linker,"bionic_dlclose");error_guest=dlsym(linker,"bionic_dlerror");
 int(*add_path)(const char*)=dlsym(linker,"bionic_add_library_path");
 assert(open_guest&&symbol_guest&&close_guest&&error_guest&&add_path&&!add_path(argv[2]));
 assert(!chdir(argv[2]));
 if(!strcmp(argv[3],"group")){
  void *h=load("top.so");if(!h){fprintf(stderr,"%s\n",error_guest());return 11;}
  int(*value)(void)=symbol_guest(h,"value");assert(value&&value()==74);assert(initialized==1&&finalized==0);
  assert(!close_guest(h));assert(initialized==1&&finalized==1);assert(!mapped("top.so")&&!mapped("middle.so")&&!mapped("provider.so"));
 }else if(!strcmp(argv[3],"scope")){
  void *provider=load("provider.so");assert(provider&&initialized==1&&!finalized);
  assert(!load("unrelated.so"));assert(error_guest());
  assert(!load("bad.so"));assert(error_guest());
  int(*value)(void)=symbol_guest(provider,"provided");assert(value&&value()==73);
  assert(initialized==1&&!finalized&&!mapped("middle.so"));
  assert(!close_guest(provider));assert(finalized==1&&!mapped("provider.so"));
 }else{
  for(int i=0;i<1100;i++){
   assert(!load("bad.so"));assert(error_guest());assert(!initialized&&!finalized);
   /* A SONAME lookup after the failed object was unmapped previously read
    * its stale string table and crashed. It must also release dependencies. */
   void *h=load("good.so");assert(h);assert(!close_guest(h));
   assert(!mapped("bad.so")&&!mapped("middle.so")&&!mapped("provider.so"));
  }
  /* Corrected bytes at the same path must be retryable, with no stale error. */
  assert(!rename("good.so","bad.so"));void *h=load("bad.so");assert(h);
  int(*value)(void)=symbol_guest(h,"value");assert(value&&value()==91);assert(!close_guest(h));
 }
 puts("LINKER_GROUP_CONTRACT=PASS");return 0;
}
''')
    subprocess.run(['gcc', '-O2', '-Wall', '-Wextra', '-Werror', str(runner),
                    '-rdynamic', '-o', str(out/'test'), '-ldl'], check=True)
    env = dict(os.environ, SAILDROID_STRICT_LINK='1',
               BIONIC_TRANSLATION_CONFIG_DIR=str(out/'config'))
    rows = []
    for case in ['group', 'scope', 'rollback']:
        r = subprocess.run([str(out/'test'), str(a.linker.resolve()), str(out), case],
                           env=env, capture_output=True, text=True, timeout=30)
        rows.append(dict(case=case, exit=r.returncode, output=r.stdout[-1000:], error=r.stderr[-2000:]))
    print(json.dumps(dict(cases=rows), indent=2))
    assert all(row['exit']==0 for row in rows)
