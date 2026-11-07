/* Cooperative local-process resource guard.
 * No peer census or global UID quota. Kernel UID limits remain authoritative.
 * FD references are conservatively counted, not advertised as unique OFDs.
 * No cached watch ledger and no add-then-rm rollback. */
#define _GNU_SOURCE
#include <sys/inotify.h>
#include <sys/stat.h>
#include <sys/file.h>
#include <sys/sysmacros.h>
#include <sys/syscall.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
#include <dirent.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <limits.h>
#include <time.h>

extern long saildroid_raw_syscall6(long,long,long,long,long,long,long);
static pthread_mutex_t process_lock=PTHREAD_MUTEX_INITIALIZER;
static unsigned process_cap=512,instance_cap=16;
static int (*path_mapper)(const char *,char **);
#ifdef SD_GUARD_FIXTURE
static char fixture_lock_directory[PATH_MAX];
static unsigned long local_scans,uid_scans,policy_denials,unknown_denials;
static int fixture_pause_notify=-1,fixture_pause_resume=-1;
void sd_guard_fixture_pause_once(int notify,int resume){pthread_mutex_lock(&process_lock);fixture_pause_notify=notify;fixture_pause_resume=resume;pthread_mutex_unlock(&process_lock);}
int sd_guard_fixture_configure_local(const char *directory,unsigned cap,unsigned instances) {
    if(!directory||strlen(directory)>=sizeof(fixture_lock_directory)||!cap||!instances){errno=EINVAL;return -1;}
    pthread_mutex_lock(&process_lock);
    strcpy(fixture_lock_directory,directory);process_cap=cap;instance_cap=instances;
    pthread_mutex_unlock(&process_lock);return 0;
}
void sd_guard_fixture_stats(unsigned long *out) {
    pthread_mutex_lock(&process_lock);out[0]=local_scans;out[1]=uid_scans;out[2]=policy_denials;out[3]=unknown_denials;pthread_mutex_unlock(&process_lock);
}
#define COUNT(x) (++(x))
#else
#define COUNT(x) ((void)0)
#endif
/* A tri-state shared translator: 1 owns *mapped, 0 unmapped, -1 real errno.
 * Bridge installation must happen before app/native threads start. */
void saildroid_inotify_set_path_mapper(int (*mapper)(const char *,char **)) {
    pthread_mutex_lock(&process_lock);path_mapper=mapper;pthread_mutex_unlock(&process_lock);
}
static void enter_guard(int *old_cancel) {
    pthread_setcancelstate(PTHREAD_CANCEL_DISABLE,old_cancel);
    pthread_mutex_lock(&process_lock);
}
static void leave_guard(int old_cancel,int error) {
    pthread_mutex_unlock(&process_lock);
    /* All scoped FDs and both locks are released before pending cancellation
     * can run. Do not add a testcancel point to the native inotify API. */
    errno=error;pthread_setcancelstate(old_cancel,NULL);errno=error;
}
static void before_fork(void){pthread_mutex_lock(&process_lock);}
static void after_fork(void){pthread_mutex_unlock(&process_lock);}
__attribute__((constructor)) static void initialize_guard(void) {
    /* A normal libc fork cannot inherit an operation's temporary flock/duplicate
     * descriptors. Raw clone/fork are outside this cooperative boundary. */
    pthread_atfork(before_fork,after_fork,after_fork);
}
static long raw(long nr,long a,long b,long c){return saildroid_raw_syscall6(nr,a,b,c,0,0,0);}
static int numeric(const char *s) {if(!*s)return 0;for(;*s;s++)if(*s<'0'||*s>'9')return 0;return 1;}
static uint64_t milliseconds(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint64_t)t.tv_sec*1000+t.tv_nsec/1000000;}
static int checked_directory(int parent,const char *name,uid_t uid,int create) {
    if(create&&mkdirat(parent,name,0700)<0&&errno!=EEXIST)return -1;
    int fd=openat(parent,name,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return -1;
    struct stat st;if(fstat(fd,&st)<0||st.st_uid!=uid||(st.st_mode&0777)!=0700){close(fd);errno=EACCES;return -1;}
    return fd;
}
static int shared_lock(void) {
    int directory=-1;
#ifdef SD_GUARD_FIXTURE
    if(fixture_lock_directory[0]) {
        directory=open(fixture_lock_directory,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
        struct stat st;if(directory<0)return -1;
        if(fstat(directory,&st)<0||st.st_uid!=getuid()||(st.st_mode&0777)!=0700){close(directory);errno=EACCES;return -1;}
    } else
#endif
    {
        int base=open("/run/user",O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(base<0)return -1;
        struct stat st;if(fstat(base,&st)<0||st.st_uid!=0||(st.st_mode&0022)){close(base);errno=EACCES;return -1;}
        char uid[32];snprintf(uid,sizeof(uid),"%u",(unsigned)getuid());
        int user=checked_directory(base,uid,getuid(),0);close(base);if(user<0)return -1;
        directory=checked_directory(user,"saildroid-inotify",getuid(),1);close(user);if(directory<0)return -1;
    }
    int fd=openat(directory,"allocation.lock",O_RDWR|O_CREAT|O_NOFOLLOW|O_CLOEXEC,0600);close(directory);if(fd<0)return -1;
    struct stat st;if(fstat(fd,&st)<0||!S_ISREG(st.st_mode)||st.st_uid!=getuid()||st.st_nlink!=1||(st.st_mode&0777)!=0600){close(fd);errno=EACCES;return -1;}
    /* Every operation opens its own OFD. Threads and separately launched
     * processes therefore contend on the same kernel lock. */
    if(flock(fd,LOCK_EX)<0){int error=errno;close(fd);errno=error;return -1;}return fd;
}
struct counts {unsigned long watches,instances;};
static int fd_rows(const char *name,unsigned long *rows) {
    FILE *f=fopen(name,"re");if(!f)return -1;char line[1024];*rows=0;
    while(fgets(line,sizeof(line),f)) {
        if(strncmp(line,"inotify ",8))continue;
        unsigned wd;unsigned long long ino,dev;
        if(sscanf(line,"inotify wd:%x ino:%llx sdev:%llx",&wd,&ino,&dev)!=3){fclose(f);errno=EIO;return -1;}
        ++*rows;
    }
    int failed=ferror(f);fclose(f);if(failed){errno=EIO;return -1;}return 0;
}
static int process_counts(pid_t pid,int exclude,struct counts *out,uint64_t deadline) {
    char directory[80];snprintf(directory,sizeof(directory),"/proc/%ld/fdinfo",(long)pid);
    DIR *dir=opendir(directory);if(!dir)return -1;struct dirent *entry;unsigned visited=0;
    errno=0;
    while((entry=readdir(dir))) {
        if(!numeric(entry->d_name))continue;
        if(pid==getpid()&&strtol(entry->d_name,NULL,10)==exclude)continue;
        if(++visited>65536||milliseconds()>deadline){closedir(dir);errno=EOVERFLOW;return -1;}
        char path[128],link[64];snprintf(path,sizeof(path),"/proc/%ld/fd/%.16s",(long)pid,entry->d_name);
        ssize_t size=readlink(path,link,sizeof(link)-1);
        if(size<0){if(errno==ENOENT){errno=0;continue;}int error=errno;closedir(dir);errno=error;return -1;}
        link[size]=0;if(strcmp(link,"anon_inode:inotify")){errno=0;continue;}
        snprintf(path,sizeof(path),"/proc/%ld/fdinfo/%.16s",(long)pid,entry->d_name);
        unsigned long rows=0;if(fd_rows(path,&rows)<0){if(errno==ENOENT){errno=0;continue;}int error=errno;closedir(dir);errno=error;return -1;}
        out->instances++;out->watches+=rows;errno=0;
    }
    int error=errno;closedir(dir);errno=error;return error?-1:0;
}
static int deny(int unknown) {COUNT(policy_denials);if(unknown)COUNT(unknown_denials);errno=ENOSPC;return -1;}
static int add_watch(int fd,const char *path,uint32_t mask,int android_path) {
    int result=-1,error=0,lockfd=-1,instance=-1;char *mapped=NULL;
    int old_cancel;enter_guard(&old_cancel);
    if(android_path&&path_mapper) {
        int changed=path_mapper(path,&mapped);if(changed<0)goto done;
        if(changed>0){if(!mapped){errno=ENOMEM;goto done;}path=mapped;}
    }
    lockfd=shared_lock();if(lockfd<0)goto done;
    instance=fcntl(fd,F_DUPFD_CLOEXEC,0);if(instance<0)goto done;
    char fdpath[80],link[64];snprintf(fdpath,sizeof(fdpath),"/proc/self/fd/%d",instance);
    ssize_t size=readlink(fdpath,link,sizeof(link)-1);if(size<0)goto done;link[size]=0;
    if(strcmp(link,"anon_inode:inotify")){errno=EINVAL;goto done;}
    unsigned long own_instance_rows=0;
    snprintf(fdpath,sizeof(fdpath),"/proc/self/fdinfo/%d",instance);
    if(fd_rows(fdpath,&own_instance_rows)<0)goto done;
#ifdef SD_GUARD_FIXTURE
    if(fixture_pause_notify>=0) {
        int notify=fixture_pause_notify,resume=fixture_pause_resume;
        fixture_pause_notify=-1;fixture_pause_resume=-1;char value='x';
        if(write(notify,&value,1)!=1||read(resume,&value,1)!=1){errno=EIO;goto done;}
    }
#endif
    /* Do not open the watch target. Linux 4.9 reports O_PATH open/close
     * notifications, so even an inode pin can invent application events.
     * At the cap reject updates too: stat plus a pathname add cannot prove
     * that a concurrent rename will not turn an update into an allocation. */
    if(own_instance_rows>=process_cap){deny(0);goto done;}
    struct counts local={0};COUNT(local_scans);
    if(process_counts(getpid(),instance,&local,milliseconds()+250)<0){deny(1);goto done;}
    if(local.watches>=process_cap){deny(0);goto done;}
    result=(int)raw(SYS_inotify_add_watch,instance,(long)path,mask);
done:
    error=errno;if(instance>=0)close(instance);if(lockfd>=0)close(lockfd);free(mapped);
    leave_guard(old_cancel,error);return result;
}
__attribute__((visibility("hidden"))) int sd_guard_host_add(int fd,const char *path,uint32_t mask){return add_watch(fd,path,mask,0);}
int inotify_add_watch(int fd,const char *path,uint32_t mask){return sd_guard_host_add(fd,path,mask);}
__attribute__((visibility("hidden"))) int sd_guard_android_add(int fd,const char *path,uint32_t mask){return add_watch(fd,path,mask,1);}
int bionic_inotify_add_watch(int fd,const char *path,uint32_t mask){return sd_guard_android_add(fd,path,mask);}
__attribute__((visibility("hidden"))) int sd_guard_init1(int flags) {
    if(flags&~(IN_NONBLOCK|IN_CLOEXEC)){errno=EINVAL;return -1;}
    int old_cancel;enter_guard(&old_cancel);int lockfd=shared_lock(),result=-1,error;
    if(lockfd<0)goto done;
    struct counts local={0};COUNT(local_scans);
    if(process_counts(getpid(),-1,&local,milliseconds()+250)<0||local.instances>=instance_cap){errno=EMFILE;goto done;}
    result=(int)raw(SYS_inotify_init1,flags,0,0);
done:error=errno;if(lockfd>=0)close(lockfd);leave_guard(old_cancel,error);return result;
}
int inotify_init1(int flags){return sd_guard_init1(flags);}
int inotify_init(void){return sd_guard_init1(0);}
int bionic_inotify_init1(int flags){return sd_guard_init1(flags);}
int bionic_inotify_init(void){return sd_guard_init1(0);}
__attribute__((visibility("hidden"))) int sd_guard_remove(int fd,int wd) {
    int old_cancel;enter_guard(&old_cancel);int lockfd=shared_lock(),result=-1;
    if(lockfd>=0)result=(int)raw(SYS_inotify_rm_watch,fd,wd,0);
    int error=errno;if(lockfd>=0)close(lockfd);leave_guard(old_cancel,error);return result;
}
int inotify_rm_watch(int fd,int wd){return sd_guard_remove(fd,wd);}
int bionic_inotify_rm_watch(int fd,int wd){return sd_guard_remove(fd,wd);}

/* syscall() returns long; do not tail-return an int ABI error (AArch64 w0
 * zero-extends -1 to 0xffffffff). Explicit conversion sign-extends correctly. */
__attribute__((visibility("hidden"))) long sd_guard_sys_init(long flags){return sd_guard_init1((int)flags);}
__attribute__((visibility("hidden"))) long sd_guard_sys_add(long fd,long path,long mask){return sd_guard_host_add((int)fd,(const char *)path,(uint32_t)mask);}
__attribute__((visibility("hidden"))) long sd_guard_sys_android_add(long fd,long path,long mask){return sd_guard_android_add((int)fd,(const char *)path,(uint32_t)mask);}
__attribute__((visibility("hidden"))) long sd_guard_sys_remove(long fd,long wd){return sd_guard_remove((int)fd,(int)wd);}
