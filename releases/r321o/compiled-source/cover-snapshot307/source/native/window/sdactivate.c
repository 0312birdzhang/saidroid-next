#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <poll.h>
#include <unistd.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
static _Atomic int listening;
static int listener=-1;
static pthread_t server_thread;
static char socket_path[sizeof(((struct sockaddr_un*)0)->sun_path)];
static int (*activate_window)(void);
static int (*close_window)(void);
static int (*open_uri)(const char *);
static int (*dump_threads)(void);
static void *serve(void *unused){
    (void)unused;
    while(listening){
        struct pollfd pollfd={listener,POLLIN,0};if(poll(&pollfd,1,500)<=0)continue;
        int client=accept4(listener,NULL,NULL,SOCK_CLOEXEC);if(client<0)continue;
        struct ucred credential;socklen_t size=sizeof(credential);
        if(getsockopt(client,SOL_SOCKET,SO_PEERCRED,&credential,&size)<0||credential.uid!=getuid()){close(client);continue;}
        struct timeval timeout={2,0};setsockopt(client,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));setsockopt(client,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
        char command[16384];size_t used=0;while(used<sizeof(command)-1){ssize_t count=read(client,command+used,sizeof(command)-1-used);if(count<=0)break;used+=(size_t)count;if(memchr(command,'\n',used))break;}command[used]=0;
        const char *reply="invalid\n";
        if(!strcmp(command,"activate\n"))reply=activate_window()?"requested\n":"unsupported\n";
        else if(!strcmp(command,"close\n"))reply=close_window()?"closing\n":"unsupported\n";
        else if(!strcmp(command,"dump\n"))reply=dump_threads&&dump_threads()?"requested\n":"unsupported\n";
        else if(used>6&&!strncmp(command,"open ",5)&&command[used-1]=='\n'&&!memchr(command,'\n',used-1)){
            command[used-1]=0;
            if(open_uri&&open_uri(command+5)){activate_window();reply="requested\n";}else reply="unsupported\n";
        }
        send(client,reply,strlen(reply),MSG_NOSIGNAL);close(client);
    }
    return NULL;
}
int sd_activation_start(const char *path,int (*request)(void),int (*close_request)(void),int (*open_request)(const char *),int (*dump_request)(void)){
    if(!path||!path[0])return 0;
    if(strlen(path)>=sizeof(socket_path)){errno=ENAMETOOLONG;return -1;}
    struct stat status;if(lstat(path,&status)==0){if(!S_ISSOCK(status.st_mode)||status.st_uid!=getuid()){errno=EPERM;return -1;}if(unlink(path)<0)return -1;}
    listener=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);if(listener<0)return -1;
    struct sockaddr_un address={.sun_family=AF_UNIX};strcpy(address.sun_path,path);
    if(bind(listener,(struct sockaddr*)&address,sizeof(address))<0||chmod(path,0600)<0||listen(listener,4)<0){close(listener);listener=-1;return -1;}
    strcpy(socket_path,path);activate_window=request;close_window=close_request;open_uri=open_request;dump_threads=dump_request;listening=1;
    if(pthread_create(&server_thread,NULL,serve,NULL)){listening=0;close(listener);listener=-1;unlink(path);return -1;}
    return 0;
}
void sd_activation_stop(void){if(!listening)return;listening=0;shutdown(listener,SHUT_RDWR);pthread_join(server_thread,NULL);close(listener);listener=-1;unlink(socket_path);}
