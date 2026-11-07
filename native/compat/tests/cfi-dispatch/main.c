#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
extern void __cfi_slowpath(uint64_t,void *);
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    void *library=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
    if(!library){fprintf(stderr,"%s\n",dlerror());return 3;}
    void *target=dlsym(library,"target");
    if(!target)return 4;
    if(!strcmp(argv[2],"unmapped"))target=(void *)(uintptr_t)1;
    __cfi_slowpath(!strcmp(argv[2],"wrong-type")?43:42,target);
    int (*checks)(void)=dlsym(library,"checks");
    if(checks&&checks()!=1)return 5;
    dlclose(library);return 0;
}
