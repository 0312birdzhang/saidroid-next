"""An Android ELF parser must never receive glibc's relocated dynamic tables."""
from pathlib import Path
import subprocess,tempfile,argparse,os,json
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='sd-domain321-')as directory:
 root=Path(directory);(root/'config').mkdir()
 for name in ['android-domain','host-domain']:
  (root/(name+'.c')).write_text('int identity(void){return 81;}\n');subprocess.run(['gcc','-fPIC','-shared','-nostdlib','-Wl,--hash-style=both','-Wl,-z,separate-code','-o',str(root/(name+'.so')),str(root/(name+'.c'))],check=True)
 (root/'run.c').write_text(r'''
#define _GNU_SOURCE
#include <link.h>
#include <dlfcn.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
struct seen{int android,host;};static int verify_metadata;
static int inspect(struct dl_phdr_info*info,size_t size,void*data){struct seen*s=data;if(!info->dlpi_name)return 0;
 if(strstr(info->dlpi_name,"android-domain.so")){++s->android;assert(info->dlpi_phnum>0&&info->dlpi_phdr&&info->dlpi_addr);assert(size>=sizeof(*info));if(verify_metadata)assert(info->dlpi_adds==0&&info->dlpi_subs==0&&info->dlpi_tls_modid==0&&info->dlpi_tls_data==0);}
 if(strstr(info->dlpi_name,"host-domain.so"))++s->host;
 return 0;}
static int stop(struct dl_phdr_info*i,size_t z,void*d){(void)i;(void)z;(void)d;return 77;}
int main(int argc,char**argv){assert(argc==6);verify_metadata=argv[5][0]=='1';void*l=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(l);void*host=dlopen(argv[3],RTLD_NOW|RTLD_GLOBAL);assert(host);
 void*(*open)(const char*,int)=dlsym(l,"bionic_dlopen");int(*add)(const char*)=dlsym(l,"bionic_add_library_path");int(*iter)(int(*)(struct dl_phdr_info*,size_t,void*),void*)=dlsym(l,"bionic_dl_iterate_phdr");assert(open&&add&&iter&&!add(argv[4]));void*android=open(argv[2],RTLD_NOW);assert(android);
 struct seen s={0};assert(!iter(inspect,&s));printf("ANDROID_ITERATOR|android=%d|foreign_host=%d\n",s.android,s.host);fflush(stdout);if(s.android!=1||s.host)return 7;assert(iter(stop,0)==77);
 int(*mixed)(int(*)(struct dl_phdr_info*,size_t,void*),void*)=dlsym(l,"sd_mixed_dl_iterate_phdr");assert(mixed);memset(&s,0,sizeof(s));assert(!mixed(inspect,&s));assert(s.android==1&&s.host==1&&mixed(stop,0)==77);
 memset(&s,0,sizeof(s));assert(!dl_iterate_phdr(inspect,&s));assert(s.host==1&&s.android==0);puts("ANDROID_NAMESPACE=PASS|android-only-export|initialized-metadata|private-mixed-native-unwind|callback-stop|native-host-unchanged");}
''')
 subprocess.run(['gcc','-O2','-Wall','-Wextra','-o',str(root/'run'),str(root/'run.c'),'-ldl'],check=True)
 env=dict(os.environ,SAILDROID_STRICT_LINK='1',BIONIC_TRANSLATION_CONFIG_DIR=str(root/'config'),LD_LIBRARY_PATH='/var/tmp/saidroid-native-service-lifecycle305-v1/payload/lib:/home/art/lib');rows=[]
 for label,library,expected in [('baseline',a.baseline,7),('candidate',a.candidate,0)]:
  q=subprocess.run([str(root/'run'),str(library.resolve()),str(root/'android-domain.so'),str(root/'host-domain.so'),str(root),'0'if label=='baseline'else'1'],env=env,capture_output=True,text=True,timeout=10);(a.out/(label+'.stdout')).write_text(q.stdout);(a.out/(label+'.stderr')).write_text(q.stderr);print(label,q.returncode,q.stdout);assert q.returncode==expected,q.stderr[-3500:];rows.append(dict(label=label,rc=q.returncode,stdout=q.stdout))
 (a.out/'result.json').write_text(json.dumps(dict(passed=True,results=rows),indent=2)+'\n')
