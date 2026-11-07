#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <linux/capability.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <unistd.h>

static int checks;
static void require(int value,const char *name) {
    if(!value){fprintf(stderr,"UTS291_CONTRACT=failed|check=%s|errno=%d\n",name,errno);exit(10);}
    ++checks;
}
int main(int argc,char **argv) {
    require(argc==2||argc==3,"expected-ordinary-uid");uid_t uid=(uid_t)strtoul(argv[1],NULL,10);
    require(uid&&getuid()==uid&&geteuid()==uid,"actual-ordinary-uid");
    uid_t real,effective,saved;require(!getresuid(&real,&effective,&saved)&&real==uid&&effective==uid&&saved==uid,"no-saved-root-uid");
    struct utsname identity;require(!uname(&identity),"actual-uname");
    require(!strcmp(identity.nodename,"localhost")&&!strcmp(identity.domainname,"localdomain"),"genuine-android-kernel-uts");
    struct __user_cap_header_struct header={_LINUX_CAPABILITY_VERSION_3,0};struct __user_cap_data_struct caps[2]={{0}};
    require(!syscall(SYS_capget,&header,caps)&&!caps[0].effective&&!caps[1].effective&&!caps[0].permitted&&!caps[1].permitted&&!caps[0].inheritable&&!caps[1].inheritable,"zero-all-capability-sets");
    require(prctl(PR_GET_NO_NEW_PRIVS,0,0,0,0)==1,"kernel-no-new-privileges");
    errno=0;require(sethostname("forbidden",9)==-1&&errno==EPERM,"cannot-change-private-hostname");
    errno=0;require(setdomainname("forbidden",9)==-1&&errno==EPERM,"cannot-change-private-domain");
    errno=0;require(unshare(CLONE_NEWUTS)==-1&&errno==EPERM,"cannot-create-another-privileged-uts");
    errno=0;require(unshare(CLONE_NEWNET)==-1&&errno==EPERM,"cannot-create-network-namespace");
    errno=0;require(setuid(0)==-1&&errno==EPERM,"cannot-regain-root");
    errno=0;require(prctl(PR_SET_NO_NEW_PRIVS,0,0,0,0)==-1&&errno==EINVAL,"cannot-disable-no-new-privileges");
    struct rlimit limit;require(!getrlimit(RLIMIT_NICE,&limit)&&limit.rlim_cur==40&&limit.rlim_max==40,"normal-android-scheduling-limit");
    struct rlimit raised={41,41};errno=0;require(setrlimit(RLIMIT_NICE,&raised)==-1&&errno==EPERM,"cannot-raise-hard-limit");
    require(!getenv("LD_PRELOAD")&&!getenv("LD_LIBRARY_PATH")&&!getenv("SAILDROID_UTS_TEST_SECRET"),"clean-worker-environment");
    DIR *directory=opendir("/proc/self/fd");require(directory!=NULL,"fd-inventory");int own=dirfd(directory),extra=0;struct dirent *entry;
    while((entry=readdir(directory))){char *end;long fd=strtol(entry->d_name,&end,10);if(!*end&&fd>2&&fd!=own)++extra;}
    require(!closedir(directory)&&extra==0,"no-inherited-extra-fds");
    char uts[128],net[128],path[128];ssize_t n=readlink("/proc/self/ns/uts",uts,sizeof(uts)-1);require(n>0,"uts-namespace-identity");uts[n]=0;n=readlink("/proc/self/ns/net",net,sizeof(net)-1);require(n>0,"network-namespace-identity");net[n]=0;
    snprintf(path,sizeof(path),"/proc/%d/ns/uts",getpid());
    printf("{\"passed\":true,\"checks\":%d,\"uid\":%u,\"hostname\":\"%s\",\"domainname\":\"%s\",\"uts\":\"%s\",\"net\":\"%s\",\"extra_fds\":%d}\n",checks,getuid(),identity.nodename,identity.domainname,uts,net,extra);
    if(argc==3){char token;require(!fflush(stdout),"ready-output");require(read(STDIN_FILENO,&token,1)==1&&token=='X',"bounded-parent-release");}
    return 0;
}
