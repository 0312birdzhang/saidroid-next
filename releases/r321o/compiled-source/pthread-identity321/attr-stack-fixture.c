#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <errno.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
/* Android ARM64 pthread_attr_t is 56 bytes. The adapter stores a host pointer
 * in it; calling raw glibc on the outer object silently updates the wrong one. */
struct guest_attr { unsigned char bytes[56]; };
static int (*attr_init)(void*),(*attr_destroy)(void*),(*attr_setstack)(void*,void*,size_t),(*attr_getstack)(const void*,void**,size_t*),(*thread_create)(uintptr_t*,const void*,void*(*)(void*),void*),(*thread_join)(uintptr_t,void**),(*thread_getattr)(uintptr_t,void*);
static uintptr_t(*thread_self)(void);
static void *expected_base;static size_t expected_size;
static void *worker(void *argument){
    volatile unsigned char local=0x5a;void*base=NULL;size_t size=0;
    struct guest_attr a;assert(!thread_getattr(thread_self(),&a));assert(!attr_getstack(&a,&base,&size));assert(!attr_destroy(&a));
    assert(base==expected_base&&size==expected_size);
    assert((uintptr_t)&local>=(uintptr_t)base&&(uintptr_t)&local<(uintptr_t)base+size);
    pthread_attr_t host;void*hostbase=NULL;size_t hostsize=0;
    assert(!pthread_getattr_np(pthread_self(),&host));assert(!pthread_attr_getstack(&host,&hostbase,&hostsize));assert(!pthread_attr_destroy(&host));
    assert(hostbase==base&&hostsize==size);
    printf("CREATED_THREAD_STACK|base=%p|size=%zu|sp_probe=%p|host_and_android_match=1\n",base,size,(void*)&local);return argument;
}
int main(int argc,char**argv){
    assert(argc==3||argc==5);setbuf(stdout,NULL);void*h=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);if(!h){puts(dlerror());return 2;}
#define LOAD(v,n) do{v=dlsym(h,"bionic_pthread_" n);assert(v);}while(0)
    LOAD(attr_init,"attr_init");LOAD(attr_destroy,"attr_destroy");LOAD(attr_getstack,"attr_getstack");
    attr_setstack=dlsym(h,"bionic_pthread_attr_setstack");
    if(argc==3&&!attr_setstack){puts("ATTR_STACK=baseline-rejected|reason=correctly-spelled-export-missing");return 7;}
    if(argc==5){
        void*l=dlopen(argv[3],RTLD_NOW|RTLD_GLOBAL);if(!l){puts(dlerror());return 2;}
        void*(*guest_open)(const char*,int)=dlsym(l,"bionic_dlopen");void*(*guest_symbol)(void*,const char*)=dlsym(l,"bionic_dlsym");assert(guest_open&&guest_symbol);
        int(*add_path)(const char*)=dlsym(l,"bionic_add_library_path");assert(add_path);char*directory=strdup(argv[4]);char*slash=strrchr(directory,'/');assert(slash);*slash=0;assert(!add_path(directory));void*g=guest_open(slash+1,RTLD_NOW);assert(g);free(directory);void*(*resolved)(void)=guest_symbol(g,"guest_setstack_address");assert(resolved);
        void*address=resolved();if(attr_setstack)assert(address==(void*)attr_setstack);else assert(address==dlsym(RTLD_DEFAULT,"pthread_attr_setstack"));Dl_info origin={0};dladdr(address,&origin);printf("ANDROID_RELOCATION|symbol=pthread_attr_setstack|origin=%s|resolved=%p|adapter=%p\n",origin.dli_fname?origin.dli_fname:"?",address,(void*)attr_setstack);
        int(*through_guest)(void*,void*,size_t)=guest_symbol(g,"guest_setstack");assert(through_guest);attr_setstack=through_guest;
    }
    size_t page=(size_t)sysconf(_SC_PAGESIZE);expected_size=6*1024*1024;
    unsigned char*mapping=mmap(NULL,expected_size+2*page,PROT_NONE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);assert(mapping!=MAP_FAILED);expected_base=mapping+page;assert(!mprotect(expected_base,expected_size,PROT_READ|PROT_WRITE));
    struct {uint64_t before;struct guest_attr value;uint64_t after;} guarded={.before=0xaabbccdd12345678,.after=0x9876543211223344};
    assert(!attr_init(&guarded.value));assert(!attr_setstack(&guarded.value,expected_base,expected_size));void*base=NULL;size_t size=0;assert(!attr_getstack(&guarded.value,&base,&size));
    printf("ATTR_STACK_READBACK|requested_base=%p|requested_size=%zu|actual_base=%p|actual_size=%zu\n",expected_base,expected_size,base,size);
    assert(guarded.before==0xaabbccdd12345678&&guarded.after==0x9876543211223344);
    if(base!=expected_base||size!=expected_size){puts("ATTR_STACK=baseline-rejected|reason=host-fallback-mutates-outer-android-object");assert(!attr_destroy(&guarded.value));munmap(mapping,expected_size+2*page);return 7;}
    assert(attr_setstack(&guarded.value,expected_base,1)==EINVAL);assert(!attr_getstack(&guarded.value,&base,&size));assert(base==expected_base&&size==expected_size);
    LOAD(thread_create,"create");LOAD(thread_join,"join");LOAD(thread_self,"self");LOAD(thread_getattr,"getattr_np");
    for(int i=0;i<12;i++){uintptr_t thread;void*result=NULL;assert(!thread_create(&thread,&guarded.value,worker,(void*)0x73));assert(!thread_join(thread,&result)&&result==(void*)0x73);}
    assert(!attr_destroy(&guarded.value));assert(!munmap(mapping,expected_size+2*page));puts("ATTR_STACK=PASS|explicit-6MiB-stack|actual-thread-SP-inside|android-host-bounds-identical|undersize-rejected|guard-pages|reuse-12");return 0;
}
