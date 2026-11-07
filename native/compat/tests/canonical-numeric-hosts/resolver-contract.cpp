#include "../../canonical-numeric-hosts/libcore-canonical-numeric-hosts.h"
#include <cstdio>
#include <string>
static unsigned checks;
static void require(bool okay,const char *message){if(!okay){fprintf(stderr,"CHECK_FAILED=%s\n",message);exit(1);}++checks;}
static void query(const char *name,const char *expected,int flags,int family=AF_INET){
 addrinfo hints{};hints.ai_family=family;hints.ai_flags=flags;hints.ai_socktype=SOCK_STREAM;addrinfo *result=nullptr;
 int rc=sd_libcore_canonical_getaddrinfofornet(name,"12345",&hints,0,0,&result);require(rc==0&&result,"actual numeric/alias result");
 if(flags&AI_CANONNAME)require(result->ai_canonname&&std::string(result->ai_canonname)==((std::string(name)=="1"||std::string(name)=="0x7f.0.0.1")?"numeric-alias.invalid":name),"original numeric input/canonical alias retained");
 for(auto p=result;p;p=p->ai_next){char actual[128];unsigned port=0;if(p->ai_family==AF_INET){auto v=reinterpret_cast<sockaddr_in *>(p->ai_addr);require(inet_ntop(AF_INET,&v->sin_addr,actual,sizeof(actual)),"actual IPv4 bytes");port=ntohs(v->sin_port);}else{require(p->ai_family==AF_INET6,"actual IPv6 family");auto v=reinterpret_cast<sockaddr_in6 *>(p->ai_addr);require(inet_ntop(AF_INET6,&v->sin6_addr,actual,sizeof(actual)),"actual IPv6 bytes");port=ntohs(v->sin6_port);}require(std::string(actual)==expected,"actual expected address");require(port==12345,"real libc service conversion");}freeaddrinfo(result);
}
int main(int argc,char **argv){
 require(argc==3&&getuid()==65534,"ordinary kernel uid");require(setenv("ANDROID_ROOT",argv[1],1)==0,"component root");std::string mode=argv[2];addrinfo hints{};hints.ai_family=AF_INET;hints.ai_socktype=SOCK_STREAM;addrinfo *result=nullptr;
 for(int flags:{0,AI_NUMERICHOST,AI_CANONNAME,AI_CANONNAME|AI_NUMERICHOST})query("0177.00.00.01","177.0.0.1",flags);
 query("127.000.000.001","::ffff:127.0.0.1",AI_V4MAPPED,AF_INET6);
 if(mode=="valid"){
  for(const char *alias:{"1","0x7f.0.0.1"}){query(alias,"198.51.100.12",0);query(alias,"198.51.100.12",AI_CANONNAME);hints.ai_flags=AI_NUMERICHOST;require(sd_libcore_canonical_getaddrinfofornet(alias,nullptr,&hints,0,0,&result)==EAI_NONAME&&!result,"numeric-only request cannot resolve a private alias");}
  for(const char *legacy:{"2","1.2","1.2.3","4294967295","0x1.0x2.0x3.0x4","0256.0.0.1"})for(int flags:{0,AI_NUMERICHOST}){hints.ai_flags=flags;require(sd_libcore_canonical_getaddrinfofornet(legacy,nullptr,&hints,0,0,&result)==EAI_NONAME&&!result,"deprecated numeric forms rejected on both paths");}
  query("normal-alias.invalid","198.51.100.12",0);
 }else{
  require(mode=="rejected","expected trust mode");hints.ai_flags=0;errno=0;require(sd_libcore_canonical_getaddrinfofornet("1",nullptr,&hints,0,0,&result)==EAI_SYSTEM&&errno==EACCES&&!result,"invalid configuration cannot supply numeric alias");
 }
 hints.ai_flags=0;errno=0;require(sd_libcore_canonical_getaddrinfofornet("127.0.0.1",nullptr,&hints,77,0,&result)==EAI_SYSTEM&&errno==ENONET&&!result,"nondefault network remains real unsupported boundary");
 errno=0;require(sd_libcore_canonical_getaddrinfofornet("127.0.0.1",nullptr,&hints,0,7,&result)==EAI_SYSTEM&&errno==ENONET&&!result,"unsupported mark retains errno boundary");
 printf("CANONICAL_NUMERIC_HOSTS_NATIVE_CONTRACT=PASS|checks=%u|mode=%s|uid=%u\n",checks,mode.c_str(),getuid());return 0;
}
