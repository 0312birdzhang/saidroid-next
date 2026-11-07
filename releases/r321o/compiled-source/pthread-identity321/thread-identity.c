#define _GNU_SOURCE
#include <pthread.h>
#include <sys/syscall.h>
#include <signal.h>
#include <unistd.h>
#include <stdint.h>
#include <stddef.h>
#include <limits.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <errno.h>
#include <sched.h>
#include <string.h>

/* Android pthread_t is an opaque pointer to a Bionic thread descriptor. A
 * glibc pthread_t is a different object: returning it to Android leaks a second
 * libc's private layout. Keep Android handles in this registry and translate
 * every handle-bearing operation at the boundary. Host pthread calls retain
 * their ordinary ABI. The read-only prefix follows Android 10's ARM64 layout;
 * its TID, process, stack and scheduling metadata come from the real thread.
 */
typedef uintptr_t android_thread;
struct android_attr {
    uint32_t flags;
    void *stack_base;
    size_t stack_size,guard_size;
    int32_t sched_policy,sched_priority;
    char reserved[16];
};
struct translated_attr {pthread_attr_t *host;};
struct identity {
    struct identity *next,*prev;
    int32_t tid,pid;
    struct android_attr attr;
    _Atomic int join_state;
    void *cleanup_stack;
    void *(*start)(void*);
    void *argument,*result;
    /* The remainder belongs to this implementation, never to glibc's pthread. */
    pthread_t host;
    struct identity *registry_next;
    unsigned refs,destructor_pass;
    int started,live,exited,handle_owned,joined;
};
_Static_assert(sizeof(struct android_attr)==56,"Android ARM64 pthread_attr_t");
_Static_assert(offsetof(struct identity,tid)==16,"Android ARM64 thread TID");
_Static_assert(offsetof(struct identity,attr)==24,"Android ARM64 thread attributes");
static pthread_mutex_t registry_lock=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t registry_changed=PTHREAD_COND_INITIALIZER;
static pthread_key_t identity_key;
static pthread_once_t identity_once=PTHREAD_ONCE_INIT;
static int initialization_error;
static struct identity *registry,*live_head;
static _Thread_local struct identity *current;
static void unlink_live(struct identity *d){
    if(!d->live)return;
    if(d->prev)d->prev->next=d->next;else live_head=d->next;
    if(d->next)d->next->prev=d->prev;
    d->next=d->prev=NULL;d->live=0;
}
static void remove_registry(struct identity *d){
    struct identity **p=&registry;while(*p&&*p!=d)p=&(*p)->registry_next;
    if(*p)*p=d->registry_next;
}
static void reap(void){
    struct identity **p=&registry;
    while(*p){
        struct identity *d=*p;
        int gone=d->joined;
        if(d->exited&&!d->refs&&!gone){
            int saved=errno;
            gone=syscall(SYS_tgkill,d->pid,d->tid,0)<0&&errno==ESRCH;
            errno=saved;
        }
        if(d->exited&&!d->refs&&gone){*p=d->registry_next;free(d);}
        else p=&d->registry_next;
    }
}
static void describe(struct identity *d){
    d->host=pthread_self();d->tid=(int32_t)syscall(SYS_gettid);d->pid=(int32_t)getpid();
    pthread_attr_t a;
    if(!pthread_getattr_np(d->host,&a)){
        pthread_attr_getstack(&a,&d->attr.stack_base,&d->attr.stack_size);
        pthread_attr_getguardsize(&a,&d->attr.guard_size);
        int detached=0;pthread_attr_getdetachstate(&a,&detached);
        if(detached==PTHREAD_CREATE_DETACHED)d->attr.flags|=1;
        pthread_attr_destroy(&a);
    }
    struct sched_param parameter={0};int policy=0;
    if(!pthread_getschedparam(d->host,&policy,&parameter)){
        d->attr.sched_policy=policy;d->attr.sched_priority=parameter.sched_priority;
    }
}
static void finish_identity(void *pointer){
    struct identity *d=pointer;
    /* Other keys may call pthread_self() or detach from JNI in their own
     * destructors. Keep the descriptor valid through all POSIX destructor
     * passes. Detached/borrowed descriptors are freed only after the kernel
     * thread has actually ended, by a later registry operation. */
    if(++d->destructor_pass<PTHREAD_DESTRUCTOR_ITERATIONS){pthread_setspecific(identity_key,d);return;}
    pthread_mutex_lock(&registry_lock);
    unlink_live(d);d->exited=1;d->join_state=d->handle_owned?1:3;
    if(d->refs)d->refs--;
    pthread_mutex_unlock(&registry_lock);
}
static void fork_prepare(void){pthread_mutex_lock(&registry_lock);}
static void fork_parent(void){pthread_mutex_unlock(&registry_lock);}
static void fork_child(void){
    /* Only the calling thread survives fork. Old descriptors are intentionally
     * not traversed or freed from an atfork callback. The child's independent
     * registry starts with the actual surviving thread. */
    registry=live_head=current;
    if(current){
        current->host=pthread_self();current->tid=(int32_t)syscall(SYS_gettid);
        current->pid=(int32_t)getpid();current->next=current->prev=current->registry_next=NULL;
        current->live=1;current->exited=current->joined=current->handle_owned=0;
        current->refs=1;current->destructor_pass=0;current->join_state=0;
    }
    registry_changed=(pthread_cond_t)PTHREAD_COND_INITIALIZER;
    pthread_mutex_unlock(&registry_lock);
}
static void initialize(void){
    initialization_error=pthread_key_create(&identity_key,finish_identity);
    if(!initialization_error)initialization_error=pthread_atfork(fork_prepare,fork_parent,fork_child);
}
static int enter(struct identity *d){
    describe(d);current=d;
    int error=pthread_setspecific(identity_key,d);if(error)return error;
    pthread_mutex_lock(&registry_lock);reap();
    d->next=live_head;if(live_head)live_head->prev=d;live_head=d;d->live=1;
    d->started=1;pthread_cond_broadcast(&registry_changed);
    pthread_mutex_unlock(&registry_lock);return 0;
}
android_thread bionic_pthread_self(void){
    pthread_once(&identity_once,initialize);
    if(initialization_error){errno=initialization_error;return 0;}
    if(current)return (android_thread)current;
    struct identity *d=calloc(1,sizeof(*d));if(!d)return 0;
    d->refs=1;
    pthread_mutex_lock(&registry_lock);reap();d->registry_next=registry;registry=d;
    pthread_mutex_unlock(&registry_lock);
    int error=enter(d);
    if(error){pthread_mutex_lock(&registry_lock);remove_registry(d);pthread_mutex_unlock(&registry_lock);current=NULL;free(d);errno=error;return 0;}
    return (android_thread)d;
}
__attribute__((constructor)) static void register_initial_thread(void){(void)bionic_pthread_self();}
static void *start_thread(void *pointer){
    struct identity *d=pointer;
    int error=enter(d);
    if(error){pthread_mutex_lock(&registry_lock);d->started=-error;d->exited=1;d->refs--;pthread_cond_broadcast(&registry_changed);pthread_mutex_unlock(&registry_lock);return NULL;}
    return d->start(d->argument);
}
int bionic_pthread_create(android_thread *out,const struct translated_attr *attr,void *(*start)(void*),void *argument){
    if(!out||!start)return EINVAL;
    pthread_once(&identity_once,initialize);if(initialization_error)return initialization_error;
    struct identity *d=calloc(1,sizeof(*d));if(!d)return ENOMEM;
    int detached=PTHREAD_CREATE_JOINABLE;
    if(attr)pthread_attr_getdetachstate(attr->host,&detached);
    d->handle_owned=detached!=PTHREAD_CREATE_DETACHED;
    d->refs=2+d->handle_owned;d->start=start;d->argument=argument;
    pthread_mutex_lock(&registry_lock);reap();d->registry_next=registry;registry=d;pthread_mutex_unlock(&registry_lock);
    int previous_cancel;pthread_setcancelstate(PTHREAD_CANCEL_DISABLE,&previous_cancel);
    pthread_t host;int error=pthread_create(&host,attr?attr->host:NULL,start_thread,d);
    pthread_mutex_lock(&registry_lock);
    if(error){remove_registry(d);pthread_mutex_unlock(&registry_lock);free(d);pthread_setcancelstate(previous_cancel,NULL);return error;}
    while(!d->started)pthread_cond_wait(&registry_changed,&registry_lock);
    d->host=host;*out=(android_thread)d;d->refs--;
    error=d->started<0?-d->started:0;
    pthread_mutex_unlock(&registry_lock);
    pthread_setcancelstate(previous_cancel,NULL);return error;
}
/* The legacy helper misspelled this entry as attr_settstack, causing the
 * Android resolver to call glibc on a translated attribute object. */
int bionic_pthread_attr_setstack(struct translated_attr *attr,void *base,size_t size){
    if(!attr||!attr->host)return EINVAL;
    return pthread_attr_setstack(attr->host,base,size);
}
struct reference {pthread_t host;struct identity *identity;};
static struct reference acquire(android_thread handle){
    struct reference r={(pthread_t)handle,NULL};
    pthread_mutex_lock(&registry_lock);reap();
    for(struct identity *d=registry;d;d=d->registry_next)
        if((android_thread)d==handle){d->refs++;r.host=d->host;r.identity=d;break;}
    pthread_mutex_unlock(&registry_lock);return r;
}
static void release(struct reference r){
    if(!r.identity)return;
    pthread_mutex_lock(&registry_lock);r.identity->refs--;reap();pthread_mutex_unlock(&registry_lock);
}
int bionic_pthread_equal(android_thread one,android_thread two){struct reference a=acquire(one),b=acquire(two);int result=pthread_equal(a.host,b.host);release(a);release(b);return result;}
static void joined(struct reference r){if(r.identity){pthread_mutex_lock(&registry_lock);r.identity->joined=1;if(r.identity->handle_owned){r.identity->handle_owned=0;r.identity->refs--;}pthread_mutex_unlock(&registry_lock);}}
static void cancel_join(void *pointer){release(*(struct reference*)pointer);}
int bionic_pthread_join(android_thread thread,void **result){
    struct reference r=acquire(thread);int error;
    pthread_cleanup_push(cancel_join,&r);
    error=pthread_join(r.host,result);if(!error)joined(r);
    pthread_cleanup_pop(0);
    release(r);return error;
}
int bionic_pthread_tryjoin_np(android_thread thread,void **result){struct reference r=acquire(thread);int error=pthread_tryjoin_np(r.host,result);if(!error)joined(r);release(r);return error;}
int bionic_pthread_timedjoin_np(android_thread thread,void **result,const struct timespec *time){
    struct reference r=acquire(thread);int error;
    pthread_cleanup_push(cancel_join,&r);
    error=pthread_timedjoin_np(r.host,result,time);if(!error)joined(r);
    pthread_cleanup_pop(0);
    release(r);return error;
}
int bionic_pthread_detach(android_thread thread){struct reference r=acquire(thread);int error=pthread_detach(r.host);if(!error&&r.identity){pthread_mutex_lock(&registry_lock);r.identity->join_state=3;r.identity->attr.flags|=1;if(r.identity->handle_owned){r.identity->handle_owned=0;r.identity->refs--;}pthread_mutex_unlock(&registry_lock);}release(r);return error;}
int bionic_pthread_gettid_np(android_thread thread){struct reference r=acquire(thread);clockid_t clock;int error=pthread_getcpuclockid(r.host,&clock);int tid=error?-1:~((int)clock>>3);release(r);if(error)errno=error;return tid;}
extern int sd_legacy_bionic_pthread_getattr_np(uintptr_t,void*);
int bionic_pthread_getattr_np(android_thread thread,void *attr){struct reference r=acquire(thread);int error=sd_legacy_bionic_pthread_getattr_np((uintptr_t)r.host,attr);release(r);return error;}
#define SIMPLE(name,parameters,arguments) int bionic_##name parameters {struct reference r=acquire(thread);int error=name arguments;release(r);return error;}
SIMPLE(pthread_getcpuclockid,(android_thread thread,clockid_t *clock),(r.host,clock))
SIMPLE(pthread_getschedparam,(android_thread thread,int *policy,struct sched_param *param),(r.host,policy,param))
SIMPLE(pthread_setschedparam,(android_thread thread,int policy,const struct sched_param *param),(r.host,policy,param))
SIMPLE(pthread_setschedprio,(android_thread thread,int priority),(r.host,priority))
SIMPLE(pthread_setname_np,(android_thread thread,const char *name),(r.host,name))
SIMPLE(pthread_getname_np,(android_thread thread,char *name,size_t size),(r.host,name,size))
SIMPLE(pthread_getaffinity_np,(android_thread thread,size_t size,cpu_set_t *set),(r.host,size,set))
SIMPLE(pthread_setaffinity_np,(android_thread thread,size_t size,const cpu_set_t *set),(r.host,size,set))
SIMPLE(pthread_cancel,(android_thread thread),(r.host))
int bionic_pthread_kill(android_thread thread,int signal){struct reference r=acquire(thread);int error=pthread_kill(r.host,signal==33?SIGRTMIN:signal);release(r);return error;}
