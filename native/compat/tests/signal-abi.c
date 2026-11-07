#define _GNU_SOURCE
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <signal.h>
#include <dlfcn.h>
#include <errno.h>
#include <stdio.h>
#include <sys/mman.h>
#include <unistd.h>
struct bionic_action {int flags;union{void(*handler)(int);void(*action)(int,siginfo_t*,void*);}callback;uint64_t mask;void(*restorer)(void);};
struct special_action {bool(*handler)(int,siginfo_t*,void*);sigset_t mask;uint64_t flags;};
extern int bionic_sigaction(int,const struct bionic_action*,struct bionic_action*);
extern int bionic_sigprocmask(int,const uint64_t*,uint64_t*);
extern int bionic_pthread_sigmask(int,const uint64_t*,uint64_t*);
extern int bionic_sigemptyset(uint64_t*);
extern int bionic_sigaddset(uint64_t*,int);
static volatile sig_atomic_t special_hits,user_hits;
static bool special(int number,siginfo_t *info,void *context){(void)number;(void)info;(void)context;special_hits++;return true;}
static void user(int number){(void)number;user_hits++;}
int main(int argc,char **argv){
    assert(argc==2);void *chain=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);if(!chain){puts(dlerror());return 1;}
    void(*add)(int,struct special_action*)=dlsym(chain,"AddSpecialSignalHandlerFn");
    void(*remove_handler)(int,bool(*)(int,siginfo_t*,void*))=dlsym(chain,"RemoveSpecialSignalHandlerFn");assert(add&&remove_handler);
    struct special_action claimed={.handler=special};sigemptyset(&claimed.mask);add(SIGUSR1,&claimed);
    struct bionic_action action={.flags=SA_RESTART,.callback.handler=user,.mask=UINT64_C(1)<<(SIGUSR2-1)},old,readback;
    assert(bionic_sigaction(SIGUSR1,&action,&old)==0);assert(bionic_sigaction(SIGUSR1,NULL,&readback)==0);
    assert(readback.callback.handler==user&&(readback.mask&(UINT64_C(1)<<(SIGUSR2-1))));
    raise(SIGUSR1);assert(special_hits==1&&user_hits==0);
    remove_handler(SIGUSR1,special);raise(SIGUSR1);assert(user_hits==1);
    assert(bionic_sigaction(SIGUSR1,&old,NULL)==0);
    size_t page=(size_t)sysconf(_SC_PAGESIZE);char *region=mmap(NULL,page*2,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS,-1,0);assert(region!=MAP_FAILED);assert(mprotect(region+page,page,PROT_NONE)==0);
    uint64_t *mask=(uint64_t*)(region+page-8),previous,empty=0;
    assert(bionic_sigemptyset(mask)==0&&bionic_sigaddset(mask,SIGUSR2)==0);
    assert(bionic_sigprocmask(SIG_BLOCK,mask,&previous)==0);
    assert(bionic_sigprocmask(SIG_SETMASK,NULL,mask)==0);assert(*mask&(UINT64_C(1)<<(SIGUSR2-1)));
    assert(bionic_pthread_sigmask(SIG_SETMASK,&previous,mask)==0);
    assert(bionic_sigprocmask(SIG_SETMASK,&empty,mask)==0);
    assert(bionic_sigprocmask(SIG_SETMASK,&previous,NULL)==0);
    errno=EBUSY;assert(bionic_pthread_sigmask(999,&empty,NULL)==EINVAL&&errno==EBUSY);
    munmap(region,page*2);
    puts("API29_SIGNAL_ABI=PASS|guard_page=8-byte-mask|claimed_handler=first|user_handler=delivered|pthread_errors=preserved");return 0;
}
