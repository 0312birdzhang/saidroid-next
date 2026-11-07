/* Component-local Android hosts file before host DNS/NSS. No global file writes.
 * Root-owned regular files and directories only; no symlinks or writable data.
 * Callers keep their real libc/Bionic addrinfo allocation and flag semantics. */
#ifndef SAILDROID_COMPONENT_HOSTS_H
#define SAILDROID_COMPONENT_HOSTS_H
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <limits.h>
#include <arpa/inet.h>
#include <ctype.h>

static inline int sd_hosts_trusted(int fd,int directory){
    struct stat value;
    return fstat(fd,&value)==0&&value.st_uid==0&&!(value.st_mode&022)
        &&(directory?S_ISDIR(value.st_mode):(S_ISREG(value.st_mode)&&value.st_nlink==1&&value.st_size<=65536));
}
/* 1=trusted file read, 0=no configured file, -1=invalid/untrusted file. */
static inline int sd_component_hosts_read(char data[65537]){
    const char *root=getenv("ANDROID_ROOT");if(!root||!*root)return 0;
    if(root[0]!='/'||strlen(root)>=PATH_MAX)return -1;
    char canonical[PATH_MAX];if(!realpath(root,canonical)||strcmp(root,canonical))return -1;
    int parent=open(root,O_RDONLY|O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW);
    if(parent<0)return -1;
    if(!sd_hosts_trusted(parent,1)){close(parent);return -1;}
    const char *parts[]={"system","etc","hosts"};int fd=-1;
    for(unsigned i=0;i<3;i++){
        fd=openat(parent,parts[i],O_RDONLY|O_CLOEXEC|O_NOFOLLOW|(i<2?O_DIRECTORY:0));
        int saved=errno;close(parent);errno=saved;
        if(fd<0)return errno==ENOENT?0:-1;
        if(!sd_hosts_trusted(fd,i<2)){close(fd);return -1;}
        parent=fd;
    }
    struct stat before,after;if(fstat(fd,&before)){close(fd);return -1;}
    size_t total=0;int failed=0;
    while(total<65537){
        ssize_t n=read(fd,data+total,65537-total);
        if(n<0&&errno==EINTR)continue;
        if(n<0){failed=1;break;}
        if(!n)break;total+=(size_t)n;
    }
    if(fstat(fd,&after))failed=1;close(fd);
    if(failed||total>65536||total!=(size_t)before.st_size||before.st_dev!=after.st_dev||before.st_ino!=after.st_ino||before.st_size!=after.st_size||before.st_mtim.tv_sec!=after.st_mtim.tv_sec||before.st_mtim.tv_nsec!=after.st_mtim.tv_nsec||memchr(data,0,total))return -1;
    data[total]=0;return 1;
}
static inline int sd_hosts_name_equal(const char *a,const char *b){
    size_t na=strlen(a),nb=strlen(b);if(na&&a[na-1]=='.')na--;if(nb&&b[nb-1]=='.')nb--;
    return na==nb&&!strncasecmp(a,b,na);
}
/* Generic static hosts entries, bounded by the trusted64KiB file. */
struct sd_host_addresses { unsigned count; char ip[64][INET6_ADDRSTRLEN]; char canonical[64][256]; };
static inline int sd_component_hosts_addresses(const char *host,struct sd_host_addresses *addresses){
    addresses->count=0;
    char data[65537];int read_result=sd_component_hosts_read(data);if(read_result<=0)return read_result;
    char *line_state=NULL;
    for(char *line=strtok_r(data,"\n",&line_state);line;line=strtok_r(NULL,"\n",&line_state)){
        char *comment=strchr(line,'#');if(comment)*comment=0;
        char *state=NULL,*ip=strtok_r(line," \t\r",&state);if(!ip)continue;
        char *first=strtok_r(NULL," \t\r",&state);if(!first)continue;
        unsigned char raw[16];int actual=inet_pton(AF_INET,ip,raw)==1?AF_INET:inet_pton(AF_INET6,ip,raw)==1?AF_INET6:0;
        int matched=sd_hosts_name_equal(host,first);
        for(char *alias=strtok_r(NULL," \t\r",&state);alias;alias=strtok_r(NULL," \t\r",&state))if(sd_hosts_name_equal(host,alias))matched=1;
        if(!matched)continue;
        if(!actual||strlen(first)>255||addresses->count==64)return -1;
        unsigned index=addresses->count++;strcpy(addresses->ip[index],ip);strcpy(addresses->canonical[index],first);
    }
    return addresses->count?1:0;
}
#endif
