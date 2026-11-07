"""Reject incompatible/truncated ELF inputs before parsing or mapping them."""
from pathlib import Path
import argparse,json,os,resource,struct,subprocess,tempfile

p=argparse.ArgumentParser();p.add_argument('linker',type=Path);p.add_argument('--control',type=Path);a=p.parse_args()
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with tempfile.TemporaryDirectory(prefix='sd-linker-elf-')as directory:
 out=Path(directory);(out/'config').mkdir()
 source=out/'good.c';source.write_text('int value(void){return 73;}')
 subprocess.run(['gcc','-shared','-fPIC','-nostdlib','-Wl,--hash-style=both',str(source),'-o',str(out/'good.so')],check=True)
 original=(out/'good.so').read_bytes();assert original[4]==2
 cases={}
 def change(name,offset,fmt,value):
  raw=bytearray(original);struct.pack_into(fmt,raw,offset,value);cases[name]=raw
 change('wrong-class',4,'B',1)
 change('wrong-machine',18,'<H',40)
 change('wrong-endian',5,'B',2)
 change('not-shared-object',16,'<H',2)
 cases['truncated-header']=original[:32]
 change('program-offset-overflow',32,'<Q',0xfffffffffffffff0)
 change('program-table-truncated',32,'<Q',len(original)-16)
 change('too-many-programs',56,'<H',65)
 phoff=struct.unpack_from('<Q',original,32)[0];phnum=struct.unpack_from('<H',original,56)[0]
 load=next(phoff+i*56 for i in range(phnum)if struct.unpack_from('<I',original,phoff+i*56)[0]==1)
 change('segment-outside-file',load+8,'<Q',len(original)+4096)
 change('segment-memory-too-small',load+40,'<Q',0)
 change('segment-address-overflow',load+16,'<Q',0xfffffffffffffff0)
 for name,raw in cases.items():(out/(name+'.so')).write_bytes(raw)
 runner=out/'test.c';runner.write_text(r'''
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc,char **argv){
 assert(argc==4);void *linker=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(linker);
 void *(*open_guest)(const char*,int)=dlsym(linker,"bionic_dlopen");
 void *(*symbol_guest)(void*,const char*)=dlsym(linker,"bionic_dlsym");
 int(*close_guest)(void*)=dlsym(linker,"bionic_dlclose");
 const char *(*error_guest)(void)=dlsym(linker,"bionic_dlerror");
 int(*add_path)(const char*)=dlsym(linker,"bionic_add_library_path");
 assert(open_guest&&symbol_guest&&close_guest&&error_guest&&add_path);
 assert(!add_path(argv[2])&&!chdir(argv[2]));
 void *bad=open_guest(argv[3],RTLD_NOW);
 if(bad){close_guest(bad);return 21;}
 assert(error_guest());
 void *good=open_guest("good.so",RTLD_NOW);assert(good);
 int(*value)(void)=symbol_guest(good,"value");assert(value&&value()==73);
 assert(!close_guest(good));puts("ELF_REJECTION_AND_RETRY=PASS");return 0;
}
''')
 subprocess.run(['gcc','-O2','-Wall','-Wextra','-Werror',str(runner),'-o',str(out/'test'),'-ldl'],check=True)
 env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(out/'config'));rows=[]
 if a.control:
  # The previous loader actually admitted this incompatible-class ELF.
  r=subprocess.run([str(out/'test'),str(a.control),str(out),'wrong-class.so'],env=env,capture_output=True,text=True,timeout=10)
  assert r.returncode==21,dict(exit=r.returncode,error=r.stderr[-2000:])
  rows.append(dict(case='previous-loader-admits-wrong-class',exit=r.returncode))
 for name in cases:
  r=subprocess.run([str(out/'test'),str(a.linker),str(out),name+'.so'],env=env,capture_output=True,text=True,timeout=10)
  row=dict(case=name,exit=r.returncode,output=r.stdout.strip());rows.append(row)
  assert r.returncode==0,dict(row,error=r.stderr[-2000:])
 print(json.dumps(dict(status='PASS',scope='Real private linker, incompatible/malformed input rejection and subsequent valid ELF execution',cases=rows),indent=2))
