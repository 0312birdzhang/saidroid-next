#define _GNU_SOURCE
#include <stdint.h>
#include <assert.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <pthread.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
extern uint64_t android_fdsan_create_owner_tag(int,uint64_t);
extern uint64_t android_fdsan_get_owner_tag(int);
extern const char *android_fdsan_get_tag_type(uint64_t);
extern uint64_t android_fdsan_get_tag_value(uint64_t);
extern void android_fdsan_exchange_owner_tag(int,uint64_t,uint64_t);
extern int android_fdsan_close_with_tag(int,uint64_t);
static void *worker(void *seed){
    for(int i=0;i<500;i++){
        int fd=open("/dev/null",O_RDONLY|O_CLOEXEC);assert(fd>=0);
        uint64_t tag=android_fdsan_create_owner_tag(12,(uintptr_t)seed+(unsigned)i+1);
        assert(android_fdsan_get_owner_tag(fd)==0);
        android_fdsan_exchange_owner_tag(fd,0,tag);assert(android_fdsan_get_owner_tag(fd)==tag);
        assert(!strcmp(android_fdsan_get_tag_type(tag),"ZipArchive"));
        assert(android_fdsan_get_tag_value(tag)==(uintptr_t)seed+(unsigned)i+1);
        assert(android_fdsan_close_with_tag(fd,tag)==0);
    }
    return NULL;
}
int main(void){
    assert(android_fdsan_create_owner_tag(3,0)==0);
    pthread_t threads[4];for(uintptr_t i=0;i<4;i++)assert(pthread_create(&threads[i],NULL,worker,(void*)(i*1000))==0);
    int inherited=open("/dev/null",O_RDONLY|O_CLOEXEC);assert(inherited>=0);
    uint64_t inherited_tag=android_fdsan_create_owner_tag(3,456);
    android_fdsan_exchange_owner_tag(inherited,0,inherited_tag);
    for(int i=0;i<8;i++){
        pid_t child=fork();assert(child>=0);
        if(child==0){
            assert(android_fdsan_get_owner_tag(inherited)==inherited_tag);
            assert(android_fdsan_close_with_tag(inherited,inherited_tag)==0);
            assert(android_fdsan_get_owner_tag(inherited)==0);
            _exit(0);
        }
        int status;assert(waitpid(child,&status,0)==child);
        assert(WIFEXITED(status)&&WEXITSTATUS(status)==0);
        assert(android_fdsan_get_owner_tag(inherited)==inherited_tag);
    }
    assert(android_fdsan_close_with_tag(inherited,inherited_tag)==0);
    for(int i=0;i<4;i++)assert(pthread_join(threads[i],NULL)==0);
    int fd=open("/dev/null",O_RDONLY);uint64_t tag=android_fdsan_create_owner_tag(3,123);
    android_fdsan_exchange_owner_tag(fd,0,tag);assert(close(fd)==0);assert(android_fdsan_get_owner_tag(fd)==0);
    puts("API29_FDSAN=PASS|tagged_closes=2000|threads=4|host_close=retired|forks=8|parent_tags=preserved");return 0;
}
