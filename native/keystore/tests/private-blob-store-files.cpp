#include "../private-blob-store.hpp"
#include <iostream>
#include <sys/wait.h>
#include <future>
#include <atomic>
#include <dirent.h>
using sd_keyblob::Store;
static void require(bool b,const char*m){sd_keyblob::check(b,m);}
int main(int argc,char**argv){try{
 require(argc==3&&getuid()==10050,"Filesystem contract runs as actual isolated service UID");const std::string test=argv[1];int root=open(argv[2],O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);require(root>=0,"Open caller fixture");Store store(root,getuid(),{10000,10001});bool rejected=false;
 try {
  if(test=="valid"){store.create(10000,"a",1,{1,2,3});auto value=store.read(10000,"a");require(value.algorithm==1&&value.data==std::vector<uint8_t>({1,2,3}),"Actual committed blob data");store.erase(10000,"a");try{store.read(10000,"a");throw std::logic_error("Deleted alias survived");}catch(const sd_keyblob::Missing&){} }
  else if(test=="no-replacement"){store.create(10000,"a",1,{1});try{store.create(10000,"a",1,{2});throw std::logic_error("Existing alias replaced");}catch(const sd_keyblob::Exists&){}require(store.read(10000,"a").data==std::vector<uint8_t>({1}),"Original preserved after duplicate create");store.erase(10000,"a");}
  else if(test=="literal-path-alias"){const std::string alias="../../escape/\xff";store.create(10000,alias,3,{1,2});require(store.read(10000,alias).data==std::vector<uint8_t>({1,2}),"Encoded alias stays within namespace");store.erase(10000,alias);}
  else if(test=="unknown-uid")store.create(0,"a",1,{1});
  else if(test=="empty-alias")store.create(10000,"",1,{1});
  else if(test=="large-alias")store.create(10000,std::string(121,'a'),1,{1});
  else if(test=="wrong-algorithm")store.create(10000,"a",7,{1});
  else if(test=="empty-data")store.create(10000,"a",1,{});
  else if(test=="large-data")store.create(10000,"a",1,std::vector<uint8_t>(1024*1024+1,0));
  else if(test=="threaded-create"){
   std::atomic<unsigned> successes{0},duplicates{0};std::vector<std::future<void>> jobs;
   for(unsigned i=0;i<8;++i)jobs.push_back(std::async(std::launch::async,[&,i]{try{store.create(10000,"a",1,{static_cast<uint8_t>(i)});++successes;}catch(const sd_keyblob::Exists&){++duplicates;}}));
   for(auto&job:jobs){job.get();}
   require(successes==1&&duplicates==7,"Concurrent threads cannot overwrite key aliases");auto value=store.read(10000,"a");require(value.data.size()==1&&value.data[0]<8,"Thread winner file is complete");store.erase(10000,"a");
  }else if(test=="process-create"){
   std::vector<pid_t> children;
   for(unsigned i=0;i<8;++i){pid_t child=fork();require(child>=0,"Fork concurrent real service processes");if(!child){try{Store child_store(root,getuid(),{10000});child_store.create(10000,"a",1,{static_cast<uint8_t>(i)});_exit(0);}catch(const sd_keyblob::Exists&){_exit(2);}catch(...){_exit(1);}}children.push_back(child);}
   unsigned successes=0,duplicates=0;for(auto child:children){int status;require(waitpid(child,&status,0)==child&&WIFEXITED(status),"Join concurrent service");if(WEXITSTATUS(status)==0)++successes;else if(WEXITSTATUS(status)==2)++duplicates;else throw std::runtime_error("Concurrent store failed");}
   require(successes==1&&duplicates==7,"Separate open-file descriptions provide process exclusion");auto value=store.read(10000,"a");require(value.data.size()==1&&value.data[0]<8,"Process winner file is complete");store.erase(10000,"a");
  }else if(test=="erase-symlink")store.erase(10000,"a");
  else store.read(10000,"a");
 }catch(const std::logic_error&){throw;}catch(const std::exception&){rejected=true;}
 const bool positive=test=="valid"||test=="no-replacement"||test=="literal-path-alias"||test=="threaded-create"||test=="process-create";
 require(rejected!=positive,"Filesystem boundary acceptance matches contract");close(root);std::cout<<"PRIVATE_BLOB_FILES=PASS|case="<<test<<"|rejected="<<rejected<<"|actual_uid="<<getuid()<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<"PRIVATE_BLOB_FILES=FAIL|"<<e.what()<<'\n';return 1;}}
