#include "../../private-hosts/libcore-component-hosts.h"
#include <set>
#include <string>
#include <cstdio>
static unsigned checks;
static void require(bool condition,const char *reason){if(!condition){fprintf(stderr,"CHECK_FAILED=%s\n",reason);exit(1);}checks++;}
static std::set<std::string> lookup(const char *name,int family,int flags,const char *service,const char *expected_canonical=nullptr){
    addrinfo hints{};hints.ai_family=family;hints.ai_socktype=SOCK_STREAM;hints.ai_flags=flags;addrinfo *result=nullptr;
    int rc=sd_libcore_component_getaddrinfofornet(name,service,&hints,0,0,&result);require(rc==0&&result,"Actual resolver result");std::set<std::string> addresses;
    if(expected_canonical)require(result->ai_canonname&&std::string(result->ai_canonname)==expected_canonical,"Actual canonical name");
    for(addrinfo *p=result;p;p=p->ai_next){char text[INET6_ADDRSTRLEN];unsigned port;
        if(p->ai_family==AF_INET){auto address=reinterpret_cast<sockaddr_in *>(p->ai_addr);require(inet_ntop(AF_INET,&address->sin_addr,text,sizeof(text)),"ActualIPv4conversion");port=ntohs(address->sin_port);}
        else{require(p->ai_family==AF_INET6,"Actual supported family");auto address=reinterpret_cast<sockaddr_in6 *>(p->ai_addr);require(inet_ntop(AF_INET6,&address->sin6_addr,text,sizeof(text)),"ActualIPv6conversion");port=ntohs(address->sin6_port);}
        if(service&&std::string(service)=="12345")require(port==12345,"Real service port conversion");addresses.insert(text);
    }
    freeaddrinfo(result);return addresses;
}
int main(int argc,char **argv){
    require(argc==3&&getuid()==65534,"Actual unprivileged contract");require(setenv("ANDROID_ROOT",argv[1],1)==0,"Set actual componentroot");
    std::string mode=argv[2];addrinfo hints{};hints.ai_family=AF_UNSPEC;hints.ai_socktype=SOCK_STREAM;addrinfo *result=nullptr;
    if(mode=="rejected"){
        errno=0;int rc=sd_libcore_component_getaddrinfofornet("private.invalid",nullptr,&hints,0,0,&result);
        require(rc==EAI_SYSTEM&&errno==EACCES&&result==nullptr,"Untrusted static configuration fails closed");
    }else if(mode=="missing"){
        require(lookup("localhost",AF_INET,0,nullptr).count("127.0.0.1"),"Absent private file retains real NSS");
    }else{
        require(lookup("private.invalid",AF_UNSPEC,AI_CANONNAME,"12345","canonical.invalid")==std::set<std::string>({"192.0.2.1","192.0.2.2","2001:db8::1"}),"All actual static addresses retained");
        require(lookup("PRIVATE.INVALID.",AF_INET,AI_CANONNAME,nullptr,"canonical.invalid")==std::set<std::string>({"192.0.2.1","192.0.2.2"}),"Case/trailingdot andIPv4family");
        require(lookup("private.invalid",AF_INET6,0,nullptr)==std::set<std::string>({"2001:db8::1"}),"IPv6family actual selection");
        require(lookup("ip6-localhost",AF_INET6,0,nullptr)==std::set<std::string>({"::1"}),"Actual private IPv6loopback alias");
        require(lookup("localhost",AF_INET,0,nullptr).count("127.0.0.1"),"Private IPv4loopback config");
        require(lookup("001.002.003.004",AF_INET,AI_NUMERICHOST,nullptr)==std::set<std::string>({"1.2.3.4"}),"Existing decimalnumeric semantics retained");
        hints.ai_flags=AI_NUMERICHOST;int rc=sd_libcore_component_getaddrinfofornet("private.invalid",nullptr,&hints,0,0,&result);require(rc==EAI_NONAME&&!result,"Numeric-only lookup cannotresolvealiases");
        hints.ai_flags=0;errno=0;rc=sd_libcore_component_getaddrinfofornet("private.invalid",nullptr,&hints,1,0,&result);require(rc==EAI_SYSTEM&&errno==ENONET&&!result,"Nondefault network still rejected");
        rc=sd_libcore_component_getaddrinfofornet("private.invalid",nullptr,&hints,0,1,&result);require(rc==EAI_SYSTEM&&errno==ENONET&&!result,"Unsupported fwmark still rejected");
        rc=sd_libcore_component_getaddrinfofornet("private.invalid","no-such-test-service",&hints,0,0,&result);require(rc==EAI_SERVICE&&!result,"Real service error retained");
        hints.ai_family=AF_INET6;hints.ai_flags=AI_V4MAPPED;auto mapped=lookup("v4only.invalid",AF_INET6,AI_V4MAPPED,nullptr);require(mapped==std::set<std::string>({"::ffff:192.0.2.3"}),"Actual libcV4mapped flags retained");
    }
    printf("COMPONENT_HOSTS_CONTRACT=PASS|checks=%u|mode=%s|uid=%u\n",checks,mode.c_str(),getuid());return 0;
}
