#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <sys/inotify.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#include <string.h>
static int (*add_watch)(int,const char*,uint32_t);
static int instance;
static char watched[1024];
static void *worker(void *unused) {
    (void)unused;
    int value=add_watch(instance,watched,IN_CREATE|IN_MASK_ADD);
    if(value<0)return (void*)2;
    pthread_testcancel();return (void*)3;
}
int main(int argc,char **argv) {
    if(argc!=2&&argc!=3)return 2;
    void *module=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!module){fprintf(stderr,"%s\n",dlerror());return 3;}
    int (*configure)(const char*,unsigned,unsigned)=dlsym(module,"sd_guard_fixture_configure_local");
    void (*pause_once)(int,int)=dlsym(module,"sd_guard_fixture_pause_once");
    int (*initialize)(int)=dlsym(module,"inotify_init1");add_watch=dlsym(module,"inotify_add_watch");
    if(!configure||!pause_once||!initialize||!add_watch)return 4;
    char temporary[]="/tmp/saidroid-cancel-XXXXXX";char *directory=argc==3?argv[2]:mkdtemp(temporary);if(!directory)return 5;
    if(configure(directory,3,16)<0)return 6;
    snprintf(watched,sizeof(watched),"%s/watched",directory);if(mkdir(watched,0700)<0)return 7;
    instance=initialize(IN_CLOEXEC|IN_NONBLOCK);if(instance<0||add_watch(instance,watched,IN_CREATE)<0)return 8;
    int notify[2],resume[2];if(pipe(notify)||pipe(resume))return 9;
    pause_once(notify[1],resume[0]);pthread_t thread;if(pthread_create(&thread,NULL,worker,NULL))return 10;
    char byte;if(read(notify[0],&byte,1)!=1)return 11;
    if(pthread_cancel(thread))return 12;
    if(write(resume[1],"x",1)!=1)return 13;
    void *result=NULL;if(pthread_join(thread,&result)||result!=PTHREAD_CANCELED)return 14;
    /* This call must acquire both locks; timeout is enforced by the runner. */
    if(add_watch(instance,watched,IN_ATTRIB)<0)return 15;
    close(instance);for(int i=0;i<2;i++){close(notify[i]);close(resume[i]);}
    rmdir(watched);char lock[1024];snprintf(lock,sizeof(lock),"%s/allocation.lock",directory);unlink(lock);rmdir(directory);
    puts("CANCELLATION_GUARD=passed|worker_cancelled=true|subsequent_update=true|locks_released=true");return 0;
}
