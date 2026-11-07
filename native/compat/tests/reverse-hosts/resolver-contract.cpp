#include "../../reverse-hosts/libcore-reverse-hosts.h"
#include <string>
#include <cstdio>
static unsigned checks;
static void require(bool okay,const char *message){if(!okay){fprintf(stderr,"CHECK_FAILED=%s\n",message);exit(1);}++checks;}
static sockaddr_storage make(const std::string &ip){sockaddr_storage s{};if(ip.find(':')==std::string::npos){auto p=reinterpret_cast<sockaddr_in *>(&s);p->sin_family=AF_INET;require(inet_pton(AF_INET,ip.c_str(),&p->sin_addr)==1,"actual IPv4 address");}else{auto p=reinterpret_cast<sockaddr_in6 *>(&s);p->sin6_family=AF_INET6;require(inet_pton(AF_INET6,ip.c_str(),&p->sin6_addr)==1,"actual IPv6 address");}return s;}
static int lookup(const std::string &ip,int flags,char *name,socklen_t size){auto s=make(ip);return sd_libcore_component_getnameinfo(reinterpret_cast<sockaddr *>(&s),s.ss_family==AF_INET?sizeof(sockaddr_in):sizeof(sockaddr_in6),name,size,flags);}
int main(int argc,char **argv){
 require(argc==3&&getuid()==65534,"actual ordinary uid");require(setenv("ANDROID_ROOT",argv[1],1)==0,"private root");std::string mode=argv[2];char name[1025];
 require(lookup("192.0.2.1",NI_NUMERICHOST,name,sizeof(name))==0&&std::string(name)=="192.0.2.1","numeric output bypasses hostfile");
 if(mode=="rejected"){
  errno=0;require(lookup("192.0.2.1",NI_NAMEREQD,name,sizeof(name))==EAI_SYSTEM&&errno==EACCES,"untrusted file fails closed");
 }else if(mode=="missing"){
  auto s=make("127.0.0.1");char system[1025];int baseline=getnameinfo(reinterpret_cast<sockaddr *>(&s),sizeof(sockaddr_in),system,sizeof(system),nullptr,0,NI_NAMEREQD);
  require(baseline==0&&lookup("127.0.0.1",NI_NAMEREQD,name,sizeof(name))==0&&std::string(name)==system,"absent file uses actual NSS");
 }else{
  require(lookup("192.0.2.1",NI_NAMEREQD,name,sizeof(name))==0&&std::string(name)=="first.canonical.invalid","first canonical, not alias or later duplicate");
  require(lookup("192.0.2.1",NI_NAMEREQD|NI_NOFQDN,name,sizeof(name))==0&&std::string(name)=="first.canonical.invalid","canonical Android10 ignores NOFQDN");
  require(lookup("::ffff:192.0.2.1",NI_NAMEREQD,name,sizeof(name))==0&&std::string(name)=="first.canonical.invalid","mapped IPv4 unmapping");
  char tiny[3]={'x','x','x'};require(lookup("192.0.2.1",NI_NAMEREQD,tiny,sizeof(tiny))==EAI_MEMORY&&std::string(tiny,3)=="xxx","no partial write on small buffer");
  for(unsigned i=1;i<=200;++i){
   std::string ip="198.51.100."+std::to_string(i),expected="entry"+std::to_string(i)+".canonical.invalid";
   require(lookup(ip,NI_NAMEREQD,name,sizeof(name))==0&&std::string(name)==expected,"full real IPv4 private inventory");
   char six[128];snprintf(six,sizeof(six),"2001:db8::%x",i);require(lookup(six,NI_NAMEREQD,name,sizeof(name))==0&&std::string(name)==expected,"full real IPv6 private inventory");
   require(lookup(ip,NI_NUMERICHOST,name,sizeof(name))==0&&std::string(name)==ip,"numeric request retained");
  }
  require(lookup("::1",NI_NAMEREQD,name,sizeof(name))==0&&std::string(name)=="ip6-localhost","real private IPv6 loopback");
  require(lookup("127.0.0.1",NI_NAMEREQD,name,sizeof(name))==0&&std::string(name)=="localhost","real private IPv4 loopback");
 }
 printf("REVERSE_COMPONENT_HOSTS_CONTRACT=PASS|checks=%u|mode=%s|uid=%u\n",checks,mode.c_str(),getuid());return 0;
}
