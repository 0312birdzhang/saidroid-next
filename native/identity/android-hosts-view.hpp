#pragma once
// A private application hosts view. Preserve host entries verbatim and add
// only Android's canonical loopback names. Never write the host's /etc/hosts.
#include <arpa/inet.h>
#include <algorithm>
#include <cctype>
#include <sstream>
#include <stdexcept>
#include <string>

namespace sd_identity {
inline std::string android_hosts_view(const std::string& original) {
  if(original.size()>1024*1024||original.find('\0')!=std::string::npos)
    throw std::runtime_error("Host hosts file exceeds private view bounds");
  bool ipv4_localhost=false,ipv6_localhost=false;
  std::istringstream lines(original);std::string line;
  while(std::getline(lines,line)) {
    const auto comment=line.find('#');
    if(comment!=std::string::npos)line.resize(comment);
    std::istringstream fields(line);std::string address,alias;
    if(!(fields>>address))continue;
    in_addr v4{};in6_addr v6{};
    const bool is4=inet_pton(AF_INET,address.c_str(),&v4)==1;
    const bool is6=inet_pton(AF_INET6,address.c_str(),&v6)==1;
    while(fields>>alias) {
      std::transform(alias.begin(),alias.end(),alias.begin(),
                     [](unsigned char c){return static_cast<char>(std::tolower(c));});
      if(alias=="ip6-localhost") {
        if(!is6||!IN6_IS_ADDR_LOOPBACK(&v6))
          throw std::runtime_error("Host ip6-localhost conflicts with Android loopback identity");
        ipv6_localhost=true;
      } else if(alias=="localhost") {
        if(is4&&v4.s_addr==htonl(INADDR_LOOPBACK))ipv4_localhost=true;
        else if(!is6||!IN6_IS_ADDR_LOOPBACK(&v6))
          throw std::runtime_error("Host localhost conflicts with Android loopback identity");
      }
    }
  }
  std::string result=original;
  if(!ipv4_localhost||!ipv6_localhost) {
    if(!result.empty()&&result.back()!='\n')result+='\n';
    if(!ipv4_localhost)result+="127.0.0.1 localhost\n";
    if(!ipv6_localhost)result+="::1 ip6-localhost\n";
  }
  return result;
}
} // namespace sd_identity
