#define _GNU_SOURCE
#include <sys/resource.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <linux/capability.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <pwd.h>

/* Installed root-owned with only CAP_SYS_RESOURCE. The ART child is always the
 * invoking ordinary Linux user and has no capabilities or privilege gain path. */
int main(int argc,char **argv){
    uid_t uid=getuid();
    if(uid==0||geteuid()!=uid){fputs("SailDroid must run as the phone user\n",stderr);return 1;}
    struct rlimit limit;
    if(getrlimit(RLIMIT_NICE,&limit)<0){perror("getrlimit");return 1;}
    {struct rlimit requested={28,28};if(setrlimit(RLIMIT_NICE,&requested)<0){perror("SailDroid scheduling setup");return 1;}}
    struct __user_cap_header_struct header={_LINUX_CAPABILITY_VERSION_3,0};
    struct __user_cap_data_struct caps[2]={{0}};
    if(syscall(SYS_capset,&header,caps)<0){perror("drop capabilities");return 1;}
    if(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)<0){perror("no_new_privs");return 1;}
    if(argc==2&&!strcmp(argv[1],"--print-limits")){
        getrlimit(RLIMIT_NICE,&limit);syscall(SYS_capget,&header,caps);
        printf("{\"uid\":%u,\"nice_limit\":%lu,\"effective_capabilities\":%llu,\"no_new_privs\":%d}\n",uid,(unsigned long)limit.rlim_cur,(unsigned long long)(((uint64_t)caps[1].effective<<32)|caps[0].effective),prctl(PR_GET_NO_NEW_PRIVS,0,0,0,0));return 0;
    }
    const char *binary="/home/art/bin/dalvikvm";
    struct stat info;
    if(lstat(binary,&info)<0||!S_ISREG(info.st_mode)||info.st_uid!=0||(info.st_mode&022)){fputs("Invalid SailDroid runtime ownership\n",stderr);return 1;}
    struct passwd *account=getpwuid(uid);if(!account||!account->pw_dir||account->pw_dir[0]!='/'){fputs("Phone user account unavailable\n",stderr);return 1;}
    setenv("HOME",account->pw_dir,1);setenv("USER",account->pw_name,1);setenv("LOGNAME",account->pw_name,1);
    char runtime_directory[128];snprintf(runtime_directory,sizeof(runtime_directory),"/run/user/%u",uid);
    setenv("ANDROID_ROOT","/home/art/api29-root",1);setenv("ANDROID_DATA","/home/art/data",1);
    setenv("LD_LIBRARY_PATH","/home/art/lib",1);setenv("ICU_DATA","/home/art/api29-root/usr/icu",1);
    setenv("SD_BUILD_PROP","/home/art/api29-root/build.prop",1);
    setenv("BIONIC_TRANSLATION_CONFIG_DIR","/home/art/api29-root/linker-config",1);
    setenv("SAILDROID_STRICT_LINK","1",1);
    if(access("/home/art/api29-root/lib/libpthread_bio.so.0",R_OK)==0)
        setenv("LD_PRELOAD","/home/art/api29-root/lib/libpthread_bio.so.0:/home/art/api29-root/lib/libsdhost29.so:/home/art/api29-root/lib/libdl_bio.so.0:libresolv.so.2",1);
    else setenv("LD_PRELOAD","/home/art/api29-root/lib/libsdhost29.so:/home/art/api29-root/lib/libdl_bio.so.0:libresolv.so.2",1);
    /* Components that ship the matching Android Surface adapter use HWUI by
     * default. An explicit 0 keeps the diagnostic software backend available. */
    if(access("/home/art/api29-root/android-libs/libsdhwui-native.so",R_OK)==0)
        setenv("SAILDROID_HWUI","1",0);
    const char *hardware=getenv("SAILDROID_HWUI");
    if(hardware&&!strcmp(hardware,"1")){
        setenv("EGL_PLATFORM","wayland",1);
        setenv("HYBRIS_EGLPLATFORM","wayland",1);
    }
    setenv("EXTERNAL_STORAGE","/home/art/data/shared",1);
    setenv("XDG_RUNTIME_DIR",runtime_directory,1);setenv("WAYLAND_DISPLAY","../../display/wayland-0",1);
    char **arguments=calloc((size_t)argc+1,sizeof(char*));if(!arguments)return 1;
    arguments[0]=(char*)binary;for(int i=1;i<argc;i++)arguments[i]=argv[i];
    execv(binary,arguments);perror("SailDroid exec");return 1;
}
