#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int constructors,destructors;
void fixture_loaded(void){constructors++;}
void fixture_unloaded(void){destructors++;}
int main(int argc,char **argv){
 if(argc!=3)return 2;
 void *loader=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);if(!loader){fprintf(stderr,"%s\n",dlerror());return 3;}
 void *(*open_guest)(const char*,int)=dlsym(loader,"bionic_dlopen");
 void *(*symbol_guest)(void*,const char*)=dlsym(loader,"bionic_dlsym");
 int (*close_guest)(void*)=dlsym(loader,"bionic_dlclose");
 int (*add_path)(const char*)=dlsym(loader,"bionic_add_library_path");
 if(!open_guest||!symbol_guest||!close_guest||!add_path||add_path(argv[2]))return 4;
 char file[4096];snprintf(file,sizeof(file),"%s/libunload.so",argv[2]);
 for(int n=0;n<20;n++){
  void *one=open_guest(file,RTLD_NOW),*two=open_guest(file,RTLD_NOW);
  if(!one||one!=two||constructors!=n+1||destructors!=n)return 5;
  int (*value)(void)=symbol_guest(one,"fixture_value");if(!value||value()!=73)return 6;
  if(close_guest(one)||destructors!=n||value()!=73)return 7;
  if(close_guest(two)||destructors!=n+1)return 8;
  FILE *maps=fopen("/proc/self/maps","r");char line[8192];if(!maps)return 9;
  while(fgets(line,sizeof(line),maps))if(strstr(line,file)){fclose(maps);return 10;}
  fclose(maps);
 }
 printf("LINKER_UNLOAD=PASS|cycles=20|constructors=%d|destructors=%d|unmapped=true|refcounts=true\n",constructors,destructors);
 return 0;
}
