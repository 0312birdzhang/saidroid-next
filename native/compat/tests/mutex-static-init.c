#define _GNU_SOURCE
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <assert.h>
#include <string.h>
#define THREADS 6
#define ROUNDS 800
static pthread_barrier_t before,after;
static uint64_t guest[5];static int counter;
static int(*lock_guest)(void*),(*unlock_guest)(void*),(*destroy_guest)(void*);
static void *worker(void *ignored){
 (void)ignored;
 for(int round=0;round<ROUNDS;round++){
  pthread_barrier_wait(&before);
  for(int i=0;i<8;i++){assert(!lock_guest(guest));counter++;assert(!unlock_guest(guest));}
  pthread_barrier_wait(&after);
 }
 return NULL;
}
int main(int argc,char**argv){
 assert(argc==2);void *library=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);if(!library){puts(dlerror());return 2;}
 lock_guest=dlsym(library,"bionic_pthread_mutex_lock");unlock_guest=dlsym(library,"bionic_pthread_mutex_unlock");destroy_guest=dlsym(library,"bionic_pthread_mutex_destroy");assert(lock_guest&&unlock_guest&&destroy_guest);
 pthread_barrier_init(&before,0,THREADS+1);pthread_barrier_init(&after,0,THREADS+1);pthread_t t[THREADS];
 for(int i=0;i<THREADS;i++)assert(!pthread_create(&t[i],NULL,worker,NULL));
 for(int round=0;round<ROUNDS;round++){
  memset(guest,0,sizeof(guest));counter=0;pthread_barrier_wait(&before);pthread_barrier_wait(&after);
  if(counter!=THREADS*8){fprintf(stderr,"MUTEX_RACE=failed|round=%d|counter=%d|expected=%d\n",round,counter,THREADS*8);return 3;}
  int result=destroy_guest(guest);if(result){fprintf(stderr,"MUTEX_RACE=failed|round=%d|destroy_errno=%d\n",round,result);return 4;}
 }
 for(int i=0;i<THREADS;i++)pthread_join(t[i],NULL);
 puts("MUTEX_RACE=passed");return 0;
}
