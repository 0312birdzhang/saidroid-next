// Isolated candidate: read-only host snapshot. No Android network binding/DNS implementation.
// The Java owner imposes a shorter deadline; alarm/PDEATHSIG bound this helper independently.
#include <gio/gio.h>
#include <arpa/inet.h>
#include <linux/fib_rules.h>
#include <linux/if_addr.h>
#include <linux/if_link.h>
#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <net/if.h>
#include <poll.h>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <unistd.h>
#include <algorithm>
#include <chrono>
#include <cstring>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Bytes=std::vector<unsigned char>;
using Attrs=std::map<unsigned,std::vector<Bytes>>;
static std::string quote(const std::string&s){
    std::ostringstream o;o<<'"';for(unsigned char c:s){
        if(c=='"'||c=='\\')o<<'\\'<<c;
        else if(c<32||c>=127){const char*h="0123456789abcdef";o<<"\\u00"<<h[c>>4]<<h[c&15];}
        else o<<c;
    }o<<'"';return o.str();
}
static std::string array(const std::vector<std::string>&v){std::string s="[";for(size_t i=0;i<v.size();i++){if(i)s+=',';s+=v[i];}return s+"]";}
static Attrs attrs(const unsigned char*p,size_t n){
    Attrs a;while(n){
        if(n<sizeof(rtattr))throw std::runtime_error("short attribute");
        rtattr h;memcpy(&h,p,sizeof h);if(h.rta_len<sizeof h||h.rta_len>n)throw std::runtime_error("attribute length");
        a[h.rta_type&NLA_TYPE_MASK].push_back(Bytes(p+sizeof h,p+h.rta_len));
        size_t step=RTA_ALIGN(h.rta_len);if(step>n){if(h.rta_len!=n)throw std::runtime_error("attribute padding");break;}p+=step;n-=step;
    }return a;
}
static const Bytes*one(const Attrs&a,unsigned k){auto i=a.find(k);if(i==a.end())return nullptr;if(i->second.size()!=1)throw std::runtime_error("duplicate singleton attribute");return &i->second[0];}
static unsigned integer(const Attrs&a,unsigned k,unsigned fallback=0){auto v=one(a,k);if(!v)return fallback;if(v->size()!=4)throw std::runtime_error("integer attribute");unsigned x;memcpy(&x,v->data(),4);return x;}
static int byte(const Attrs&a,unsigned k){auto v=one(a,k);if(!v)return -1;if(v->size()!=1)throw std::runtime_error("byte attribute");return (*v)[0];}
static std::string text(const Attrs&a,unsigned k){auto v=one(a,k);if(!v)return "";if(v->empty()||v->back()!=0||v->size()>256)throw std::runtime_error("string attribute");return std::string((const char*)v->data(),v->size()-1);}
static std::string ip(const Attrs&a,unsigned k,unsigned family){auto v=one(a,k);if(!v)return "";if(v->size()!=(family==AF_INET?4u:16u))throw std::runtime_error("address attribute");char out[INET6_ADDRSTRLEN];if(!inet_ntop(family,v->data(),out,sizeof out))throw std::runtime_error("address conversion");return out;}
static long long millis(){return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
struct Message{unsigned type;Bytes body;};
struct Fd{int value;explicit Fd(int n):value(n){if(n<0)throw std::runtime_error("netlink socket");}~Fd(){close(value);}};
static std::vector<Message>dump(unsigned type,unsigned seq,long long deadline){
    if(type!=RTM_GETLINK&&type!=RTM_GETADDR&&type!=RTM_GETROUTE&&type!=RTM_GETRULE)throw std::runtime_error("read-only message required");
    Fd s(socket(AF_NETLINK,SOCK_RAW|SOCK_CLOEXEC,NETLINK_ROUTE));sockaddr_nl local{};local.nl_family=AF_NETLINK;
    if(bind(s.value,(sockaddr*)&local,sizeof local))throw std::runtime_error("netlink bind");
    Bytes request(NLMSG_HDRLEN+(type==RTM_GETLINK?sizeof(ifinfomsg):type==RTM_GETADDR?sizeof(ifaddrmsg):sizeof(rtmsg)),0);
    nlmsghdr*h=(nlmsghdr*)request.data();h->nlmsg_len=request.size();h->nlmsg_type=type;h->nlmsg_flags=NLM_F_REQUEST|NLM_F_DUMP;h->nlmsg_seq=seq;
    sockaddr_nl kernel{};kernel.nl_family=AF_NETLINK;
    if(sendto(s.value,request.data(),request.size(),0,(sockaddr*)&kernel,sizeof kernel)!=(ssize_t)request.size())throw std::runtime_error("netlink request");
    std::vector<Message>result;size_t total=0;unsigned char buffer[65536];
    for(;;){
        int left=(int)(deadline-millis());if(left<=0)throw std::runtime_error("netlink deadline");
        pollfd pfd{s.value,POLLIN,0};int ready=poll(&pfd,1,left);
        if(ready<0&&errno==EINTR)continue;if(ready<=0)throw std::runtime_error("netlink poll");
        sockaddr_nl peer{};iovec io{buffer,sizeof buffer};msghdr msg{};msg.msg_name=&peer;msg.msg_namelen=sizeof peer;msg.msg_iov=&io;msg.msg_iovlen=1;
        ssize_t size=recvmsg(s.value,&msg,0);if(size<0&&errno==EINTR)continue;
        if(size<0||msg.msg_flags&MSG_TRUNC||peer.nl_pid!=0)throw std::runtime_error("netlink receive");
        total+=size;if(total>1024*1024)throw std::runtime_error("netlink size limit");
        size_t remain=size;const unsigned char*at=buffer;
        while(remain){
            if(remain<NLMSG_HDRLEN)throw std::runtime_error("short netlink message");nlmsghdr n;memcpy(&n,at,sizeof n);
            if(n.nlmsg_len<NLMSG_HDRLEN||n.nlmsg_len>remain||n.nlmsg_seq!=seq)throw std::runtime_error("netlink framing");
            if(n.nlmsg_flags&NLM_F_DUMP_INTR)throw std::runtime_error("netlink interrupted dump");
            const unsigned char*body=at+NLMSG_HDRLEN;size_t bytes=n.nlmsg_len-NLMSG_HDRLEN;
            if(n.nlmsg_type==NLMSG_ERROR)throw std::runtime_error("netlink kernel error");
            if(n.nlmsg_type==NLMSG_DONE){if(bytes>=4){int code;memcpy(&code,body,4);if(code)throw std::runtime_error("netlink completion error");}return result;}
            if(result.size()>=4096)throw std::runtime_error("netlink count limit");result.push_back({n.nlmsg_type,Bytes(body,body+bytes)});
            size_t step=NLMSG_ALIGN(n.nlmsg_len);if(step>remain){if(n.nlmsg_len!=remain)throw std::runtime_error("netlink padding");break;}at+=step;remain-=step;
        }
    }
}
static std::vector<std::string>links(long long deadline){
    std::vector<std::string>out;for(const auto&m:dump(RTM_GETLINK,41001,deadline)){
        if(m.type!=RTM_NEWLINK||m.body.size()<sizeof(ifinfomsg))throw std::runtime_error("link shape");ifinfomsg h;memcpy(&h,m.body.data(),sizeof h);auto a=attrs(m.body.data()+sizeof h,m.body.size()-sizeof h);
        std::string name=text(a,IFLA_IFNAME);if(name.empty()||name.size()>=IFNAMSIZ||name.find('/')!=std::string::npos)throw std::runtime_error("link name");
        bool wireless=access(("/sys/class/net/"+name+"/wireless").c_str(),F_OK)==0||access(("/sys/class/net/"+name+"/phy80211").c_str(),F_OK)==0;
        std::string kind;auto info=one(a,IFLA_LINKINFO);if(info){auto nested=attrs(info->data(),info->size());kind=text(nested,IFLA_INFO_KIND);}
        bool physical=access(("/sys/class/net/"+name+"/device").c_str(),F_OK)==0;
        bool tunnel=access(("/sys/class/net/"+name+"/tun_flags").c_str(),F_OK)==0||kind=="tun"||kind=="wireguard"||kind=="ipip"||kind=="sit"||kind=="gre"||kind=="gretap"||kind=="ip6gre"||kind=="ip6gretap"||kind=="vxlan";
        std::ostringstream o;o<<"{\"index\":"<<h.ifi_index<<",\"name\":"<<quote(name)<<",\"type\":"<<h.ifi_type<<",\"flags\":"<<h.ifi_flags<<",\"mtu\":"<<integer(a,IFLA_MTU)<<",\"operstate\":"<<byte(a,IFLA_OPERSTATE)<<",\"carrier\":"<<byte(a,IFLA_CARRIER)<<",\"wireless\":"<<(wireless?"true":"false")<<",\"physical\":"<<(physical?"true":"false")<<",\"tunnel\":"<<(tunnel?"true":"false")<<",\"kind\":"<<quote(kind)<<'}';out.push_back(o.str());
    }return out;
}
static std::vector<std::string>addresses(long long deadline){
    std::vector<std::string>out;for(const auto&m:dump(RTM_GETADDR,41002,deadline)){
        if(m.type!=RTM_NEWADDR||m.body.size()<sizeof(ifaddrmsg))throw std::runtime_error("address shape");ifaddrmsg h;memcpy(&h,m.body.data(),sizeof h);if(h.ifa_family!=AF_INET&&h.ifa_family!=AF_INET6)continue;auto a=attrs(m.body.data()+sizeof h,m.body.size()-sizeof h);
        std::string address=ip(a,IFA_LOCAL,h.ifa_family);if(address.empty())address=ip(a,IFA_ADDRESS,h.ifa_family);
        std::ostringstream o;o<<"{\"index\":"<<h.ifa_index<<",\"family\":"<<unsigned(h.ifa_family)<<",\"prefix\":"<<unsigned(h.ifa_prefixlen)<<",\"flags\":"<<integer(a,IFA_FLAGS,h.ifa_flags)<<",\"scope\":"<<unsigned(h.ifa_scope)<<",\"address\":"<<quote(address)<<'}';out.push_back(o.str());
    }return out;
}
static std::vector<std::string>routes(long long deadline){
    std::vector<std::string>out;for(const auto&m:dump(RTM_GETROUTE,41003,deadline)){
        if(m.type!=RTM_NEWROUTE||m.body.size()<sizeof(rtmsg))throw std::runtime_error("route shape");rtmsg h;memcpy(&h,m.body.data(),sizeof h);if(h.rtm_family!=AF_INET&&h.rtm_family!=AF_INET6)continue;auto a=attrs(m.body.data()+sizeof h,m.body.size()-sizeof h);
        std::ostringstream o;o<<"{\"family\":"<<unsigned(h.rtm_family)<<",\"prefix\":"<<unsigned(h.rtm_dst_len)<<",\"sourcePrefix\":"<<unsigned(h.rtm_src_len)<<",\"tos\":"<<unsigned(h.rtm_tos)<<",\"table\":"<<integer(a,RTA_TABLE,h.rtm_table)<<",\"type\":"<<unsigned(h.rtm_type)<<",\"flags\":"<<h.rtm_flags<<",\"oif\":"<<integer(a,RTA_OIF)<<",\"metric\":"<<integer(a,RTA_PRIORITY)<<",\"destination\":"<<quote(ip(a,RTA_DST,h.rtm_family))<<",\"gateway\":"<<quote(ip(a,RTA_GATEWAY,h.rtm_family))<<",\"source\":"<<quote(ip(a,RTA_SRC,h.rtm_family))<<",\"multipath\":"<<(a.count(RTA_MULTIPATH)?"true":"false")<<'}';out.push_back(o.str());
    }return out;
}
static std::vector<std::string>rules(long long deadline){
    std::vector<std::string>out;for(const auto&m:dump(RTM_GETRULE,41004,deadline)){
        if(m.type!=RTM_NEWRULE||m.body.size()<sizeof(fib_rule_hdr))throw std::runtime_error("rule shape");fib_rule_hdr h;memcpy(&h,m.body.data(),sizeof h);if(h.family!=AF_INET&&h.family!=AF_INET6)continue;auto a=attrs(m.body.data()+sizeof h,m.body.size()-sizeof h);
        bool selectors=h.dst_len||h.src_len||h.tos||h.flags;
        for(const auto&v:a){unsigned k=v.first;
            if(k==FRA_TABLE||k==FRA_PRIORITY||k==FRA_PROTOCOL)continue;
            if(k==FRA_SUPPRESS_PREFIXLEN&&integer(a,k)==0xffffffffu)continue;
            selectors=true;
        }
        std::ostringstream o;o<<"{\"family\":"<<unsigned(h.family)<<",\"table\":"<<integer(a,FRA_TABLE,h.table)<<",\"priority\":"<<integer(a,FRA_PRIORITY)<<",\"action\":"<<unsigned(h.action)<<",\"selectors\":"<<(selectors?"true":"false")<<'}';out.push_back(o.str());
    }return out;
}
static std::string stringList(GVariant*properties,const char*key){
    GVariant*v=g_variant_lookup_value(properties,key,G_VARIANT_TYPE("as"));std::vector<std::string>out;
    if(v){gsize n=g_variant_n_children(v);if(n>64){g_variant_unref(v);throw std::runtime_error("service list limit");}for(gsize i=0;i<n;i++){GVariant*c=g_variant_get_child_value(v,i);const char*s=g_variant_get_string(c,nullptr);if(strlen(s)>256){g_variant_unref(c);g_variant_unref(v);throw std::runtime_error("service string limit");}out.push_back(quote(s));g_variant_unref(c);}g_variant_unref(v);}return array(out);
}
static std::string services(){
    GError*error=nullptr;GDBusConnection*bus=g_bus_get_sync(G_BUS_TYPE_SYSTEM,nullptr,&error);
    if(!bus){g_clear_error(&error);return "{\"status\":\"unavailable\",\"values\":[]}";}
    GVariant*reply=g_dbus_connection_call_sync(bus,"net.connman","/","net.connman.Manager","GetServices",nullptr,G_VARIANT_TYPE("(a(oa{sv}))"),G_DBUS_CALL_FLAGS_NONE,500,nullptr,&error);
    g_object_unref(bus);if(!reply){g_clear_error(&error);return "{\"status\":\"unavailable\",\"values\":[]}";}
    std::vector<std::string>out;GVariant*list=g_variant_get_child_value(reply,0);gsize n=g_variant_n_children(list);
    if(n>128){g_variant_unref(list);g_variant_unref(reply);throw std::runtime_error("service count limit");}
    for(gsize i=0;i<n;i++){
        GVariant*item=g_variant_get_child_value(list,i);GVariant*p=g_variant_get_child_value(item,1);const char*type="",*state="",*interface="";
        g_variant_lookup(p,"Type","&s",&type);g_variant_lookup(p,"State","&s",&state);
        GVariant*ethernet=g_variant_lookup_value(p,"Ethernet",G_VARIANT_TYPE("a{sv}"));if(ethernet)g_variant_lookup(ethernet,"Interface","&s",&interface);
        if(strlen(type)>32||strlen(state)>32||strlen(interface)>=IFNAMSIZ){if(ethernet)g_variant_unref(ethernet);g_variant_unref(p);g_variant_unref(item);g_variant_unref(list);g_variant_unref(reply);throw std::runtime_error("service field limit");}
        gboolean metered=FALSE;bool known=g_variant_lookup(p,"Metered","b",&metered);
        std::string s="{\"interface\":"+quote(interface)+",\"type\":"+quote(type)+",\"state\":"+quote(state)+",\"nameservers\":"+stringList(p,"Nameservers")+",\"domains\":"+stringList(p,"Domains")+",\"meteredKnown\":"+(known?"true":"false")+",\"metered\":"+(metered?"true":"false")+"}";
        out.push_back(s);if(ethernet)g_variant_unref(ethernet);g_variant_unref(p);g_variant_unref(item);
    }g_variant_unref(list);g_variant_unref(reply);return "{\"status\":\"read\",\"values\":"+array(out)+"}";
}
static std::string resolver(){
    std::ifstream f("/etc/resolv.conf");if(!f)return "{\"status\":\"unavailable\",\"scope\":\"global-default\"}";
    std::vector<std::string>dns,domains;std::string line;size_t bytes=0;
    while(std::getline(f,line)){bytes+=line.size()+1;if(bytes>65536)throw std::runtime_error("resolver size limit");line=line.substr(0,line.find('#'));std::istringstream in(line);std::string key,value;in>>key;
        if(key=="nameserver"&&in>>value){unsigned char raw[16];if(inet_pton(AF_INET,value.c_str(),raw)==1||inet_pton(AF_INET6,value.c_str(),raw)==1)dns.push_back(quote(value));}
        else if(key=="search"||key=="domain")while(in>>value){if(value.size()>255)throw std::runtime_error("resolver domain limit");domains.push_back(quote(value));}
        if(dns.size()>64||domains.size()>64)throw std::runtime_error("resolver count limit");
    }return "{\"status\":\"read\",\"scope\":\"global-default\",\"nameservers\":"+array(dns)+",\"domains\":"+array(domains)+"}";
}
int main(){
    pid_t parent=getppid();if(parent==1||prctl(PR_SET_PDEATHSIG,SIGKILL)||getppid()!=parent)return 3;alarm(2);
    try{
        auto start=millis();long long deadline=start+450;auto l=links(deadline),a=addresses(deadline),r=routes(deadline),u=rules(deadline);
        std::string connman=services(),resolv=resolver();auto end=millis();
        char ns[128];ssize_t n=readlink("/proc/self/ns/net",ns,sizeof(ns)-1);if(n<0)throw std::runtime_error("network namespace identity");ns[n]=0;
        std::string out="{\"schema\":1,\"complete\":true,\"netns\":"+quote(ns)+",\"uid\":"+std::to_string(getuid())+",\"elapsedMs\":"+std::to_string(end-start)+",\"links\":"+array(l)+",\"addresses\":"+array(a)+",\"routes\":"+array(r)+",\"rules\":"+array(u)+",\"services\":"+connman+",\"resolver\":"+resolv+"}";
        if(out.size()>262144)throw std::runtime_error("snapshot output limit");puts(out.c_str());return 0;
    }catch(const std::exception&e){std::string out="{\"schema\":1,\"complete\":false,\"error\":"+quote(e.what())+"}";puts(out.c_str());return 2;}
}
