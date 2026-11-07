#include "../private-blob-store.hpp"
#include <sys/wait.h>
#include <future>
#include <iostream>
using namespace sd_keyblob;
int main(int argc,char**argv){try{
 check(argc==3&&getuid()==10050,"Actual service UID and typed-value fixture required");
 const std::string test=argv[1];Fd root(open(argv[2],O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC));check(root.value>=0,"Pin typed fixture");Store values(root.value,getuid(),{10000,10001},{1,3,4});
 bool rejected=false;
 try {
  if(test=="roundtrip"){
   values.create(10000,"cert/a",4,{},true);check(values.read(10000,"cert/a").data.empty(),"Empty value accepted");values.create(10000,"cert/a",4,{1,2,3},true);check(values.read(10000,"cert/a").data==std::vector<uint8_t>({1,2,3}),"Atomic value replacement");
   values.create(10001,"cert/a",4,{9},true);check(values.read(10001,"cert/a").data==std::vector<uint8_t>({9}),"Actual UID-separated same alias");
   check(values.list(10000,"cert/")==std::vector<std::string>({"cert/a"})&&values.list(10000,"other").empty(),"Literal prefix enumeration");values.erase(10000,"cert/a");values.erase(10001,"cert/a");
  }else if(test=="key-preserved"){
   values.create(10000,"a",1,{42});bool denied=false;try{values.create(10000,"a",4,{99},true);}catch(const Denied&){denied=true;}check(denied,"Typed value cannot replace native key");check(values.read(10000,"a").algorithm==1&&values.read(10000,"a").data==std::vector<uint8_t>({42}),"Native key record exactly preserved");values.erase(10000,"a");
  }else if(test=="threaded-replace"||test=="process-replace"){
   values.create(10000,"a",4,{0},true);
   if(test=="threaded-replace"){
    std::vector<std::future<void>> jobs;for(unsigned i=1;i<=8;++i)jobs.push_back(std::async(std::launch::async,[&,i]{values.create(10000,"a",4,std::vector<uint8_t>(4096,static_cast<uint8_t>(i)),true);}));for(auto&j:jobs)j.get();
   }else{
    std::vector<pid_t> jobs;for(unsigned i=1;i<=8;++i){auto child=fork();check(child>=0,"Fork actual value writer");if(!child){try{Store own(root.value,getuid(),{10000},{4});own.create(10000,"a",4,std::vector<uint8_t>(4096,static_cast<uint8_t>(i)),true);_exit(0);}catch(...){_exit(1);}}jobs.push_back(child);}
    for(auto child:jobs){int status;check(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"All independent value writers complete");}
   }
   auto final=values.read(10000,"a");check(final.data.size()==4096&&final.data[0]>=1&&final.data[0]<=8&&std::all_of(final.data.begin(),final.data.end(),[&](uint8_t b){return b==final.data[0];}),"Atomic complete winning value");check(values.list(10000,"")==std::vector<std::string>({"a"}),"One committed value only");values.erase(10000,"a");
  }else if(test=="default-kind-create"){Store original(root.value,getuid(),{10000});original.create(10000,"a",4,{1});}
  else if(test=="default-kind-read"){Store original(root.value,getuid(),{10000});original.read(10000,"a");}
  else if(test=="invalid-kind-config"){Store invalid(root.value,getuid(),{10000},{99});}
  else if(test=="key-replace-flag")values.create(10000,"a",1,{1},true);
  else if(test=="unknown-list")values.list(19999,"");
  else if(test.rfind("replace-",0)==0)values.create(10000,"a",4,{1},true);
  else values.list(10000,"");
 }catch(const std::logic_error&){throw;}catch(const std::exception&){rejected=true;}
 bool positive=test=="roundtrip"||test=="key-preserved"||test=="threaded-replace"||test=="process-replace";
 check(rejected!=positive,"Expected typed-value boundary result");std::cout<<"PRIVATE_TYPED_VALUES=PASS|case="<<test<<"|rejected="<<rejected<<"|actual_uid="<<getuid()<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<"PRIVATE_TYPED_VALUES=FAIL|"<<e.what()<<'\n';return 1;}}
