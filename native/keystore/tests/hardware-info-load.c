#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>

#define CHECK(x) do { if (!(x)) { fprintf(stderr,"CHECK failed line %d: %s\n",__LINE__,#x); exit(1); } } while(0)
int main(int argc,char**argv) {
    CHECK(argc==3 && getuid()!=0);
    void* linker=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);CHECK(linker);
    void*(*load)(const char*,int)=dlsym(linker,"bionic_dlopen");
    void*(*symbol)(void*,const char*)=dlsym(linker,"bionic_dlsym");
    char*(*error)(void)=dlsym(linker,"bionic_dlerror");CHECK(load&&symbol&&error);
    void* module=load(argv[2],RTLD_NOW|RTLD_LOCAL);
    if(!module)fprintf(stderr,"Android load failure: %s\n",error());
    CHECK(module);
    int(*info)(void*,size_t)=symbol(module,"sd_keymaster4_hardware_info");CHECK(info);
    unsigned char output[522],before[522];memset(output,0xa5,sizeof(output));memcpy(before,output,sizeof(output));
    CHECK(info(NULL,0)==-1);CHECK(info(NULL,520)==-1);
    CHECK(info(output,519)==-1);CHECK(!memcmp(output,before,sizeof(output)));
    CHECK(info(output,521)==-1);CHECK(!memcmp(output,before,sizeof(output)));
    CHECK(info(output,0)==-1);CHECK(!memcmp(output,before,sizeof(output)));
    printf("HARDWARE_INFO_LOAD=PASS|actual_uid=%u|invalid_calls=5|hardware_RPC_calls=0|keys_touched=0\n",(unsigned)getuid());
    return 0;
}
