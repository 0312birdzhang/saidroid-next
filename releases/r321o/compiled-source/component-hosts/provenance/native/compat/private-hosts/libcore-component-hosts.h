#ifndef SAILDROID_LIBCORE_COMPONENT_HOSTS_H
#define SAILDROID_LIBCORE_COMPONENT_HOSTS_H
#include "component-hosts.h"
#include "../resolver/libcore-numeric-host.h"

static inline int sd_libcore_component_getaddrinfofornet(const char *host,const char *service,
        const struct addrinfo *hints,unsigned netid,unsigned mark,struct addrinfo **result){
    if(!result){errno=EINVAL;return EAI_SYSTEM;}
    *result=NULL;
    if(netid||mark){errno=ENONET;return EAI_SYSTEM;}
    if(host&&(!hints||!(hints->ai_flags&AI_NUMERICHOST))){
        struct sd_host_addresses addresses;
        int matched=sd_component_hosts_addresses(host,&addresses);
        if(matched<0){errno=EACCES;return EAI_SYSTEM;}
        if(matched){
            struct addrinfo numeric;memset(&numeric,0,sizeof(numeric));
            if(hints)numeric=*hints;
            numeric.ai_flags|=AI_NUMERICHOST;
            struct addrinfo **tail=result;int first_error=EAI_NONAME;
            for(unsigned i=0;i<addresses.count;i++){
                struct addrinfo *one=NULL;int rc=getaddrinfo(addresses.ip[i],service,&numeric,&one);
                if(rc){if(i==0)first_error=rc;continue;}
                if((numeric.ai_flags&AI_CANONNAME)&&one){
                    char *name=strdup(addresses.canonical[i]);
                    if(!name){freeaddrinfo(one);freeaddrinfo(*result);*result=NULL;return EAI_MEMORY;}
                    free(one->ai_canonname);one->ai_canonname=name;
                }
                *tail=one;while(*tail)tail=&(*tail)->ai_next;
            }
            return *result?0:first_error;
        }
    }
    return sd_libcore_getaddrinfofornet(host,service,hints,netid,mark,result);
}
#endif
