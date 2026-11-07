#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <cstdlib>
#include <grp.h>
#include <pwd.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/statvfs.h>
#include <unistd.h>
static void require(bool v,const char*m){if(!v)throw std::runtime_error(m);}
int main(int argc,char**argv){try{
 require(argc==3,"Expected actual allocated UID and private data path");
 unsigned uid=std::stoul(argv[1]);std::string data=argv[2];
 require(getuid()==uid&&geteuid()==uid&&getgid()==uid&&getegid()==uid,"Kernel UID/GID differs");
 auto* account=getpwuid(uid);require(account&&std::string(account->pw_name)=="u0_a"+std::to_string(uid-10000)&&std::string(account->pw_dir)==data,"Actual private NSS account differs");
 auto* group=getgrgid(uid);require(group&&group->gr_gid==uid,"Actual private NSS group differs");
 struct statvfs account_view{};require(statvfs("/etc/passwd",&account_view)==0&&(account_view.f_flag&ST_RDONLY),"Private account view is not a read-only mount");
 require(getgroups(0,nullptr)==0,"Unexpected supplementary groups");
 require(prctl(PR_GET_NO_NEW_PRIVS,0,0,0,0)==1,"Privilege elevation not blocked");
 require(std::getenv("LD_PRELOAD")==nullptr&&std::getenv("LD_LIBRARY_PATH")==nullptr&&
             std::getenv("SAILDROID_PRIVILEGED_SECRET")==nullptr,"Inherited privileged environment leaked");
 require(std::getenv("HOME")&&data==std::getenv("HOME"),"Private application home differs");
 std::ifstream status("/proc/self/status");std::string line;bool permitted=false,effective=false,bounding=false;
 while(std::getline(status,line)){
  if(line.rfind("CapPrm:",0)==0)permitted=line.find_first_not_of("0\t ",7)==std::string::npos;
  if(line.rfind("CapEff:",0)==0)effective=line.find_first_not_of("0\t ",7)==std::string::npos;
  if(line.rfind("CapBnd:",0)==0)bounding=line.find_first_not_of("0\t ",7)==std::string::npos;
 }
 require(permitted&&effective&&bounding,"Capabilities remain after application exec");
 char cwd[2];require(getcwd(cwd,sizeof(cwd))&&std::string(cwd)=="/","Application cwd differs");
 struct rlimit nice{};require(getrlimit(RLIMIT_NICE,&nice)==0&&nice.rlim_cur==40,"Actual inherited scheduler limit differs");
 std::ofstream output(data+"/actual-exec.txt");output<<"uid="<<getuid()<<" gid="<<getgid()<<" nnp=1 caps=0\n";output.close();require(output.good(),"Cannot write own private data");
 std::cout<<"APP_IDENTITY_WORKER=ready|uid="<<getuid()<<"|gid="<<getgid()<<"|caps=0|bounding=0|supplementary_groups=0|private_userdb=ready|no_new_privs=1|nice_limit=40|cwd=/\n";return 0;
 }catch(const std::exception&e){std::cerr<<"APP_IDENTITY_WORKER=failed|"<<e.what()<<'\n';return 1;}}
