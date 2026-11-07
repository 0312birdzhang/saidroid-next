#define _GNU_SOURCE
#include <jni.h>
#include <signal.h>
#include <stdint.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <stdio.h>
struct bionic_action {int flags;union{void(*handler)(int);void(*action)(int,siginfo_t*,void*);}callback;uint64_t mask;void(*restorer)(void);};
static struct bionic_action previous;
static int(*change)(int,const struct bionic_action*,struct bionic_action*);
static volatile sig_atomic_t called;
static void handler(int number,siginfo_t *info,void *context){
    called++;
    if(previous.flags&SA_SIGINFO)previous.callback.action(number,info,context);
    else if(previous.callback.handler!=SIG_DFL&&previous.callback.handler!=SIG_IGN)previous.callback.handler(number);
    else _Exit(90);
}
JNIEXPORT void JNICALL Java_SignalJitProbe_install(JNIEnv *env,jclass type){
    void (*diagnostics)(void)=dlsym(RTLD_DEFAULT,"sd_failure_diagnostics_install");if(diagnostics)diagnostics();
    (void)env;(void)type;change=dlsym(RTLD_DEFAULT,"bionic_sigaction");if(!change)abort();
    Dl_info location={0};if(dladdr(change,&location))fprintf(stderr,"SIGNAL_PROBE_ADAPTER=%s\n",location.dli_fname);
    struct bionic_action action={.flags=SA_SIGINFO,.callback.action=handler};
    if(change(SIGSEGV,&action,&previous))abort();
    if(dladdr(previous.callback.action,&location))fprintf(stderr,"SIGNAL_PROBE_PREVIOUS=%s|address=%p\n",location.dli_fname,previous.callback.action);
    struct sigaction kernel;sigaction(SIGSEGV,NULL,&kernel);
    if(dladdr(kernel.sa_sigaction,&location))fprintf(stderr,"SIGNAL_PROBE_KERNEL=%s|address=%p\n",location.dli_fname,kernel.sa_sigaction);
}
JNIEXPORT jint JNICALL Java_SignalJitProbe_hits(JNIEnv *env,jclass type){(void)env;(void)type;return called;}
JNIEXPORT void JNICALL Java_SignalJitProbe_restore(JNIEnv *env,jclass type){(void)env;(void)type;if(change(SIGSEGV,&previous,NULL))abort();}
