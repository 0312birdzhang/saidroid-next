/* Android component hosts names for the actual Linux JNI getnameinfo path.
 * Numeric output and non-matching addresses retain the real libc resolver.
 * No shared hosts file, network namespace, hostname, or DNS policy is changed. */
#ifndef SAILDROID_LIBCORE_REVERSE_HOSTS_H
#define SAILDROID_LIBCORE_REVERSE_HOSTS_H
#include "../private-hosts/component-hosts.h"
#include <netdb.h>
#include <netinet/in.h>
#include <sys/socket.h>

/* 1=first canonical name for the binary address, 0=not in private hosts,
 * -1=untrusted/invalid component hosts file. Aliases never become PTR names. */
static inline int sd_component_hosts_reverse(int family,const void *address,char name[256]) {
    const unsigned char *raw=static_cast<const unsigned char *>(address);
    if(family==AF_INET6) {
        const struct in6_addr *six=static_cast<const struct in6_addr *>(address);
        /* Android10 gethostbyaddr unmaps these before its files lookup. */
        if(IN6_IS_ADDR_V4MAPPED(six)||IN6_IS_ADDR_V4COMPAT(six)) {
            family=AF_INET;raw+=12;
        }
    }
    if(family!=AF_INET&&family!=AF_INET6)return 0;
    char data[65537];int rc=sd_component_hosts_read(data);if(rc<=0)return rc;
    char *line_state=NULL;
    for(char *line=strtok_r(data,"\n",&line_state);line;line=strtok_r(NULL,"\n",&line_state)) {
        char *comment=strchr(line,'#');if(comment)*comment=0;
        char *state=NULL,*ip=strtok_r(line," \t\r",&state);if(!ip)continue;
        char *canonical=strtok_r(NULL," \t\r",&state);if(!canonical)continue;
        unsigned char parsed[16];
        if(inet_pton(family,ip,parsed)!=1||memcmp(raw,parsed,family==AF_INET?4:16))continue;
        if(strlen(canonical)>255)return -1;
        strcpy(name,canonical);return 1;
    }
    return 0;
}
static inline int sd_libcore_component_getnameinfo(const struct sockaddr *sa,socklen_t length,
        char *host,socklen_t host_length,int flags) {
    const int supported=NI_NUMERICHOST|NI_NAMEREQD|NI_NOFQDN|NI_NUMERICSERV|NI_DGRAM;
    if(!sa||!host||!host_length||(flags&NI_NUMERICHOST)||(flags&~supported))
        return getnameinfo(sa,length,host,host_length,NULL,0,flags);
    const void *address=NULL;
    if(sa->sa_family==AF_INET&&length>=sizeof(struct sockaddr_in))
        address=&reinterpret_cast<const struct sockaddr_in *>(sa)->sin_addr;
    else if(sa->sa_family==AF_INET6&&length>=sizeof(struct sockaddr_in6))
        address=&reinterpret_cast<const struct sockaddr_in6 *>(sa)->sin6_addr;
    if(!address)return getnameinfo(sa,length,host,host_length,NULL,0,flags);
    char name[256];int rc=sd_component_hosts_reverse(sa->sa_family,address,name);
    if(rc<0){errno=EACCES;return EAI_SYSTEM;}
    if(!rc)return getnameinfo(sa,length,host,host_length,NULL,0,flags);
    /* Android10 getnameinfo deliberately ignores NI_NOFQDN (its implementation
     * is disabled), and reports EAI_MEMORY for an insufficient name buffer. */
    size_t needed=strlen(name)+1;if(needed>host_length)return EAI_MEMORY;
    memcpy(host,name,needed);return 0;
}
#endif
