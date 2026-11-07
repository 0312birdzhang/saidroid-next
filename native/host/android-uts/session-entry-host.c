#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <grp.h>
#include <linux/capability.h>
#include <pwd.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

/* Root-owned service startup primitive, never setuid or file-capability enabled.
 * A trusted service unit supplies the user and executable. The executable is
 * reached only after private UTS setup, permanent UID/GID drop, zero capabilities
 * and no_new_privs. No network or mount namespace is changed. */
static int fail(const char *step) {
    fprintf(stderr,"SD_ANDROID_UTS=failed|step=%s|errno=%d\n",step,errno);
    return 125;
}
static int close_extra_fds(void) {
    DIR *directory=opendir("/proc/self/fd");
    if(!directory)return -1;
    int own=dirfd(directory),result=0;
    struct dirent *entry;
    while((entry=readdir(directory))) {
        char *end=NULL;long fd=strtol(entry->d_name,&end,10);
        if(!end||*end||fd<3||fd==own)continue;
        if(close((int)fd)&&errno!=EBADF){result=-1;break;}
    }
    if(closedir(directory))result=-1;
    return result;
}
int main(int argc,char **argv) {
    if(getuid()!=0||geteuid()!=0||getgid()!=getegid()) {
        errno=EPERM;return fail("root-service-startup-required");
    }
    if(argc<5||strcmp(argv[1],"--user")||strcmp(argv[3],"--")||argv[4][0]!='/') {
        errno=EINVAL;return fail("usage-user-and-absolute-command-required");
    }
    struct passwd *entry=getpwnam(argv[2]);
    if(!entry||!entry->pw_uid||!entry->pw_gid||!entry->pw_dir||entry->pw_dir[0]!='/') {
        errno=EINVAL;return fail("ordinary-account-required");
    }
    uid_t uid=entry->pw_uid;gid_t gid=entry->pw_gid;
    char *name=strdup(entry->pw_name),*home=strdup(entry->pw_dir);
    if(!name||!home){free(name);free(home);return fail("account-copy");}
    struct stat executable;
    if(lstat(argv[4],&executable)||!S_ISREG(executable.st_mode)||executable.st_uid!=0
            ||(executable.st_mode&022)||!(executable.st_mode&0111)) {
        errno=EACCES;return fail("immutable-root-owned-command-required");
    }
    /* unshare precedes both writes: the Sailfish host keeps its real identity.
     * Values are the unchanged Android10 rootdir/init.rc startup defaults. */
    if(unshare(CLONE_NEWUTS))return fail("private-uts");
    if(sethostname("localhost",9)||setdomainname("localdomain",11))return fail("android-uts-defaults");
    /* Match the existing native host/bootstrap RLIMIT_NICE=40 before its
     * ordinary worker loses CAP_SYS_RESOURCE. */
    struct rlimit nice_limit={40,40};
    if(setrlimit(RLIMIT_NICE,&nice_limit))return fail("ordinary-scheduling-limit");
    if(initgroups(name,gid)||prctl(PR_SET_KEEPCAPS,0,0,0,0)
            ||setresgid(gid,gid,gid)||setresuid(uid,uid,uid))return fail("permanent-account-drop");
    struct __user_cap_header_struct header={_LINUX_CAPABILITY_VERSION_3,0};
    struct __user_cap_data_struct caps[2]={{0}};
    if(syscall(SYS_capset,&header,caps)||prctl(PR_CAP_AMBIENT,PR_CAP_AMBIENT_CLEAR_ALL,0,0,0)
            ||prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return fail("zero-capabilities-no-new-privileges");
    if(getuid()!=uid||geteuid()!=uid||getgid()!=gid||getegid()!=gid
            ||syscall(SYS_capget,&header,caps)||caps[0].effective||caps[1].effective
            ||caps[0].permitted||caps[1].permitted||caps[0].inheritable||caps[1].inheritable
            ||prctl(PR_GET_NO_NEW_PRIVS,0,0,0,0)!=1) {
        errno=EPERM;return fail("ordinary-identity-verification");
    }
    if(chdir("/")||close_extra_fds())return fail("clean-exec-context");
    if(clearenv()||setenv("PATH","/usr/bin:/bin",1)||setenv("LANG","C.UTF-8",1)
            ||setenv("HOME",home,1)||setenv("USER",name,1)||setenv("LOGNAME",name,1))
        return fail("ordinary-environment");
    free(name);free(home);
    fprintf(stderr,"SD_ANDROID_UTS=ready|uid=%u|gid=%u|hostname=localhost|domainname=localdomain|capabilities=0|no_new_privs=1|network_namespace=inherited\n",uid,gid);
    execv(argv[4],argv+4);return fail("ordinary-command-exec");
}
