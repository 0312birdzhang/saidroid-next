#define _GNU_SOURCE
#include <dlfcn.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
static void *(*open_bionic)(const char*,int);
static const char *(*error_bionic)(void);
static pthread_barrier_t barrier;
static int missing,foreign,overwritten;
static void fail_open(int id,int seq){char path[160];snprintf(path,sizeof(path),"/saidroid-dlerror-fixture/missing-thread-%d-sequence-%d.so",id,seq);if(open_bionic(path,RTLD_NOW)!=NULL)abort();}
static void *consumer(void*unused){(void)unused;
 for(int i=0;i<100;i++){
  pthread_barrier_wait(&barrier);const char*err=error_bionic();if(err)foreign++;
  pthread_barrier_wait(&barrier);pthread_barrier_wait(&barrier);
  fail_open(2,i);(void)error_bionic();pthread_barrier_wait(&barrier);
 }
 return NULL;
}
int main(int argc,char**argv){
 if(argc!=2)return 2;
 void*l=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!l){fprintf(stderr,"fixture loader: %s\n",dlerror());return 2;}
 open_bionic=dlsym(l,"bionic_dlopen");error_bionic=dlsym(l,"bionic_dlerror");if(!open_bionic||!error_bionic)return 2;
 pthread_barrier_init(&barrier,NULL,2);pthread_t thread;pthread_create(&thread,NULL,consumer,NULL);
 for(int i=0;i<100;i++){
  fail_open(1,i);pthread_barrier_wait(&barrier);pthread_barrier_wait(&barrier);
  const char*err=error_bionic();if(!err||!strstr(err,"missing-thread-1-"))missing++;
  if(error_bionic()!=NULL){fprintf(stderr,"Error not consumed\n");return 3;}
  fail_open(1,i);err=error_bionic();char saved[1024];snprintf(saved,sizeof(saved),"%s",err?err:"");
  pthread_barrier_wait(&barrier);pthread_barrier_wait(&barrier);
  if(!err||strcmp(err,saved))overwritten++;
 }
 pthread_join(thread,NULL);pthread_barrier_destroy(&barrier);
 printf("DLERROR_FIXTURE=done|iterations=100|foreign=%d|missing=%d|overwritten=%d|passed=%s\n",foreign,missing,overwritten,foreign==0&&missing==0&&overwritten==0?"true":"false");
 return foreign||missing||overwritten?1:0;
}
