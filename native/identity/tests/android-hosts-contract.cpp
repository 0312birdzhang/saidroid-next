// Internal fixtures for the pure hosts composition; no network/host mutation.
#include "../android-hosts-view.hpp"
#include <iostream>
#include <vector>
int main() {
  unsigned checks=0;
  const auto require=[&](bool value){if(!value)throw std::runtime_error("Hosts composition contract failed");++checks;};
  const std::string canonical="127.0.0.1 localhost\n::1 ip6-localhost\n";
  require(sd_identity::android_hosts_view("")==canonical);
  require(sd_identity::android_hosts_view(canonical)==canonical);
  const std::string sailfish="127.0.0.1 localhost.localdomain localhost\n::1 localhost6.localdomain6 localhost6\n192.0.2.7 example.invalid # private host alias\n";
  require(sd_identity::android_hosts_view(sailfish)==sailfish+"::1 ip6-localhost\n");
  require(sd_identity::android_hosts_view("# localhost ip6-localhost")=="# localhost ip6-localhost\n"+canonical);
  const std::string uppercase="127.0.0.1\tLOCALHOST\r\n0:0:0:0:0:0:0:1\tip6-LOCALHOST\n";
  require(sd_identity::android_hosts_view(uppercase)==uppercase);
  require(sd_identity::android_hosts_view("::1 localhost ip6-localhost\n")=="::1 localhost ip6-localhost\n127.0.0.1 localhost\n");
  require(sd_identity::android_hosts_view("127.0.0.1 localhost # comment\n")=="127.0.0.1 localhost # comment\n::1 ip6-localhost\n");
  require(sd_identity::android_hosts_view("::1 ip6-localhost")=="::1 ip6-localhost\n127.0.0.1 localhost\n");
  for(const auto& invalid:std::vector<std::string>{
      "192.0.2.1 localhost\n", "2001:db8::1 ip6-localhost\n",
      "127.0.0.1 ip6-localhost\n", "bad-address ip6-localhost\n",
      "127.0.0.2 localhost\n", "::ffff:127.0.0.1 ip6-localhost\n",
      canonical+"192.0.2.1 LOCALHOST\n", std::string("x\0y",3),std::string(1024*1024+1,'#')}) {
    bool denied=false;
    try{sd_identity::android_hosts_view(invalid);}catch(const std::runtime_error&){denied=true;}
    require(denied);
  }
  std::cout<<"ANDROID_HOSTS_COMPOSITION=PASS|checks="<<checks<<"|host_mutations=0\n";
}
