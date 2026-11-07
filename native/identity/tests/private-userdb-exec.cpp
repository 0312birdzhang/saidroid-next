// Internal VM contract launcher only: real read-only NSS view before ordinary UID.
// The trusted test supervisor supplies the fixed runtime and environment.
#include "../private-userdb.hpp"
#include <grp.h>
#include <sys/prctl.h>
#include <unistd.h>
#include <iostream>
extern char** environ;
int main(int argc,char**argv){try{
 sd_identity::root_caller();sd_identity::require(argc>=4,"VM fixture UID HOME ELF args");
 const unsigned uid=std::stoul(argv[1]);sd_identity::enter_private_userdb(uid,argv[2]);
 sd_identity::require(setgroups(0,nullptr)==0&&setresgid(uid,uid,uid)==0&&setresuid(uid,uid,uid)==0,"Actual fixture UID");
 sd_identity::require(prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0)==0,"No privilege elevation");
 umask(0077);execve(argv[3],argv+3,environ);throw std::runtime_error("Fixture exec failed");
 }catch(const std::exception&e){std::cerr<<"PRIVATE_USERDB_FIXTURE_ERROR="<<e.what()<<'\n';return 125;}}
