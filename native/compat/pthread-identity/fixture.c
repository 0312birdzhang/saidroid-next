#define _GNU_SOURCE
#include <pthread.h>
#include <dlfcn.h>
#include <stdint.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdatomic.h>
#include <stdlib.h>
#include <errno.h>
#include <time.h>
typedef uintptr_t handle;
static handle(*self)(void);static int(*create)(handle*,void*,void*(*)(void*),void*),(*join)(handle,void**),(*guest_gettid)(handle),(*equal)(handle,handle),(*setname)(handle,const char*),(*getname)(handle,char*,size_t),(*kill_thread)(handle,int),(*detach)(handle),(*cancel_thread)(handle),(*timedjoin)(handle,void**,const struct timespec*);
static atomic_int entered,allow_exit,destructors;static handle child_self;static pthread_key_t key;
struct prefix{struct prefix*next,*prev;int tid,pid;};
static void destructor(void *v){assert(self()==(handle)v);atomic_fetch_add(&destructors,1);}
static void *worker(void *p){handle h=self();assert(h!=(handle)pthread_self());assert(guest_gettid(h)==syscall(SYS_gettid));struct prefix *d=(void*)h;assert(d->tid==syscall(SYS_gettid)&&d->pid==getpid());assert(equal(h,h));assert(!kill_thread(h,0));assert(!setname(h,"sd-id-fixture"));char name[16];assert(!getname(h,name,sizeof(name))&&!strcmp(name,"sd-id-fixture"));pthread_setspecific(key,(void*)h);child_self=h;atomic_store(&entered,1);while(!atomic_load(&allow_exit))sched_yield();return p;}
static void *imported(void *p){handle h=self();assert(h!=(handle)pthread_self());assert(guest_gettid(h)==syscall(SYS_gettid));return p;}
static void *sleeper(void *p){(void)p;atomic_store(&entered,1);for(;;){pthread_testcancel();usleep(1000);}return NULL;}
static void *joiner(void *p){atomic_store(&allow_exit,1);join((handle)p,NULL);return NULL;}
static void *detached_worker(void *p){handle h=self();pthread_setspecific(key,(void*)h);atomic_fetch_add(&entered,1);return p;}
int main(int argc,char**argv){assert(argc==3);setbuf(stdout,NULL);void*h=dlopen(argv[1],RTLD_NOW|RTLD_GLOBAL);assert(h);self=dlsym(h,"bionic_pthread_self");if(!self){puts("PTHREAD_IDENTITY=baseline-rejected|reason=host-thread-structure-exposed");return 7;}
#define LOAD(variable,name) variable=dlsym(h,"bionic_pthread_"name);assert(variable)
LOAD(create,"create");LOAD(join,"join");LOAD(guest_gettid,"gettid_np");LOAD(equal,"equal");LOAD(setname,"setname_np");LOAD(getname,"getname_np");LOAD(kill_thread,"kill");LOAD(detach,"detach");LOAD(cancel_thread,"cancel");LOAD(timedjoin,"timedjoin_np");
handle main=self();assert(main!=(handle)pthread_self());assert(((struct prefix*)main)->tid==getpid());assert(!pthread_key_create(&key,destructor));
for(int i=0;i<250;i++){atomic_store(&entered,0);atomic_store(&allow_exit,0);handle c;assert(!create(&c,NULL,worker,(void*)0x73));while(!atomic_load(&entered))sched_yield();assert(c==child_self);assert(guest_gettid(c)>0&&guest_gettid(c)!=getpid());struct prefix*d=(void*)c;int count=0;while(d->next){assert(d->next->prev==d);d=d->next;assert(++count<128);}assert(d->tid==getpid());atomic_store(&allow_exit,1);void*r;assert(!join(c,&r)&&r==(void*)0x73);}
assert(atomic_load(&destructors)==250);pthread_t external;assert(!pthread_create(&external,NULL,imported,(void*)0x91));void*r;assert(!pthread_join(external,&r)&&r==(void*)0x91);assert(self()==main);
atomic_store(&entered,0);atomic_store(&allow_exit,0);handle target,waiter;
assert(!create(&target,NULL,sleeper,NULL));while(!atomic_load(&entered))sched_yield();
struct timespec deadline;clock_gettime(CLOCK_REALTIME,&deadline);assert(timedjoin(target,NULL,&deadline)==ETIMEDOUT);
assert(!create(&waiter,NULL,joiner,(void*)target));while(!atomic_load(&allow_exit))sched_yield();
assert(!cancel_thread(waiter));assert(!join(waiter,&r)&&r==PTHREAD_CANCELED);
assert(!cancel_thread(target));assert(!join(target,&r)&&r==PTHREAD_CANCELED);
atomic_store(&entered,0);for(int i=0;i<250;i++){handle h;assert(!create(&h,NULL,detached_worker,NULL));assert(!detach(h));}
for(int i=0;i<3000&&atomic_load(&destructors)<500;i++)usleep(1000);
assert(atomic_load(&entered)==250&&atomic_load(&destructors)==500);
for(int i=0;i<3000&&((struct prefix*)main)->prev;i++)usleep(1000);
assert(!((struct prefix*)main)->prev);
pid_t pid=fork();assert(pid>=0);if(!pid){assert(self()==main&&((struct prefix*)main)->tid==getpid()&&guest_gettid(main)==getpid());_exit(0);}int status;assert(waitpid(pid,&status,0)==pid&&WIFEXITED(status)&&WEXITSTATUS(status)==0);assert(((struct prefix*)main)->tid==getpid());puts("PTHREAD_IDENTITY=PASS|create-join=250|native-tids|linked-view|names|key-destructors|host-import|join-cancellation|timedjoin-timeout|detached=250|fork");return 0;}
