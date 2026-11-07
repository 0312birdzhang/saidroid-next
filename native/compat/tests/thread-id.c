#define _GNU_SOURCE
#include <pthread.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <assert.h>
#include <stdio.h>
extern int bionic_pthread_gettid_np(pthread_t);
static pthread_barrier_t barrier;
static int actual[3];
static void *worker(void *argument) {
    int index=(int)(long)argument;
    actual[index]=(int)syscall(SYS_gettid);
    pthread_barrier_wait(&barrier);pthread_barrier_wait(&barrier);
    return NULL;
}
int main(void) {
    pthread_t threads[3];pthread_barrier_init(&barrier,NULL,4);
    for(long i=0;i<3;i++)assert(!pthread_create(&threads[i],NULL,worker,(void*)i));
    pthread_barrier_wait(&barrier);
    int own=(int)syscall(SYS_gettid);
    assert(bionic_pthread_gettid_np(pthread_self())==own);
    for(int i=0;i<3;i++) {
        int translated=bionic_pthread_gettid_np(threads[i]);
        assert(translated==actual[i]&&translated!=own);
        printf("THREAD_ID=verified|index=%d|tid=%d|caller=%d\n",i,translated,own);
    }
    pthread_barrier_wait(&barrier);
    for(int i=0;i<3;i++)pthread_join(threads[i],NULL);
    pthread_barrier_destroy(&barrier);return 0;
}
