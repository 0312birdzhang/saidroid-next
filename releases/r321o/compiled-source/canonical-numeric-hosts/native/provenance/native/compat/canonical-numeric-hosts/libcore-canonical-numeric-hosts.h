/* netd's strict decimal dotted-quad semantics on both numeric-only and normal
 * LinuxJNI paths. Preserve actual private hosts aliases, NSS/DNS for hostnames,
 * IPv6/scopes, libc addrinfo ownership, and the explicit Android network boundary. */
#ifndef SAILDROID_LIBCORE_CANONICAL_NUMERIC_HOSTS_H
#define SAILDROID_LIBCORE_CANONICAL_NUMERIC_HOSTS_H
#include "../private-hosts/libcore-component-hosts.h"

static inline int sd_libcore_canonical_getaddrinfofornet(const char *host,const char *service,
        const struct addrinfo *hints,unsigned netid,unsigned mark,struct addrinfo **result) {
    if(!result){errno=EINVAL;return EAI_SYSTEM;}
    *result=NULL;
    if(netid||mark){errno=ENONET;return EAI_SYSTEM;}
    if(host&&!strchr(host,':')) {
        char normalized[16];
        if(sd_libcore_ipv4_decimal(host,normalized)) {
            struct addrinfo numeric{};if(hints)numeric=*hints;numeric.ai_flags|=AI_NUMERICHOST;
            int rc=sd_libcore_component_getaddrinfofornet(normalized,service,&numeric,0,0,result);
            if(!rc&&(numeric.ai_flags&AI_CANONNAME)&&*result) {
                // Android10 explore_numeric retains its original input as canonname.
                char *name=strdup(host);if(!name){freeaddrinfo(*result);*result=NULL;return EAI_MEMORY;}
                free((*result)->ai_canonname);(*result)->ai_canonname=name;
            }
            return rc;
        }
        if(!hints||!(hints->ai_flags&AI_NUMERICHOST)) {
            // Identify exactly the extra numeric syntaxes that glibc would
            // otherwise accept without consulting DNS. This probe cannot do DNS.
            struct addrinfo numeric{},*legacy=NULL;numeric.ai_family=AF_UNSPEC;
            numeric.ai_socktype=SOCK_STREAM;numeric.ai_flags=AI_NUMERICHOST;
            int rc=getaddrinfo(host,NULL,&numeric,&legacy);
            if(rc==0) {
                freeaddrinfo(legacy);
                // Numeric-looking names can still be explicitly supplied as
                // genuine private hosts aliases; do not suppress that files lookup.
                struct sd_host_addresses configured;int found=sd_component_hosts_addresses(host,&configured);
                if(found<0){errno=EACCES;return EAI_SYSTEM;}
                if(!found)return EAI_NONAME;
            }
        }
    }
    return sd_libcore_component_getaddrinfofornet(host,service,hints,netid,mark,result);
}
#endif
