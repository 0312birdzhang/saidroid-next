#include "../mce-lock-state.hpp"
#include <iostream>
int main(int argc,char**argv){try{if(argc!=3)return 2;if(getuid()!=10050||geteuid()!=10050)return 3;std::cout<<"MCE_QUERY_IDENTITY=actual|uid="<<getuid()<<"|euid="<<geteuid()<<std::endl;sd_keylock::MceState backend(argv[1]);std::string reason;bool unlocked=backend.unlocked(std::stoul(argv[2]),&reason);std::cout<<"MCE_LOCK_STATE=queried|unlocked="<<unlocked<<"|reason="<<reason<<'\n';return unlocked?0:10;}catch(const std::exception&error){std::cout<<"MCE_LOCK_STATE=unavailable|reason="<<error.what()<<'\n';return 20;}}
