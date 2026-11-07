#include "app-identity.hpp"
#include <iostream>
using namespace sd_identity;
int main(int argc,char**argv) {
 try {
  require(argc >= 3,"usage: identity-tool STATE init|snapshot|allocate|retire [PACKAGE SIGNER...]");
  const std::string command=argv[2];
  if(command=="init") {
   require(argc==3,"init takes no package arguments");Registry registry(argv[1],true);
   std::cout<<registry.snapshot().dump()<<'\n';return 0;
  }
  Registry registry(argv[1]);
  if(command=="snapshot") {require(argc==3,"snapshot takes no package arguments");std::cout<<registry.snapshot().dump()<<'\n';}
  else if(command=="allocate") {
   require(argc>=5,"verified package and certificate fingerprints required");
   std::vector<std::string> signers;for(int i=4;i<argc;++i)signers.emplace_back(argv[i]);
   const auto uid=registry.allocate_verified(argv[3],std::move(signers));
   std::cout<<Json{{"package",argv[3]},{"uid",uid},{"gid",uid}}.dump()<<'\n';
  } else if(command=="retire") {require(argc==4,"one installed package required");registry.retire(argv[3]);}
  else throw std::runtime_error("Unknown identity operation");
  return 0;
 }catch(const std::exception&e){std::cerr<<"APP_IDENTITY_ERROR="<<e.what()<<'\n';return 1;}
}
