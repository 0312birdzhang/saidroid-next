// Root supervisor seals decisions from previously genuinely verified immutable
// APK facts plus the durable identity snapshot. This is not an APK verifier.
#include "service-access.hpp"
#include <iostream>
using namespace sd_identity;
static Json input(const fs::path& path){
 Fd directory(open_state_directory(path.parent_path()));
 const auto name=path.filename().string();require(!name.empty()&&name!="."&&name!="..","Invalid policy source name");
 Fd file(openat(directory.value,name.c_str(),O_RDONLY|O_NOFOLLOW|O_CLOEXEC));
 trusted_file(file.value,false);return Json::parse(read_all(file.value));
}
int main(int argc,char**argv){try{
 root_caller();require(argc==4,"usage: compile-service-policy IDENTITIES VERIFIED_APKS NEW_POLICY");
 const auto identities=input(argv[1]),facts=input(argv[2]);
 require(facts.is_array()&&facts.size()<=10000,"Bounded verified APK snapshot required");
 ServiceAccess access(identities,facts.get<std::vector<Json>>());
 Json callers=Json::object(),apks=Json::object(),services=Json::object();
 for(const auto& apk:facts){
  const auto package=apk.at("package").get<std::string>();
  const auto uid=identities.at("packages").at(package).at("app_id").get<unsigned>();
  callers[std::to_string(uid)]=package;apks[package]=apk.at("apk_sha256");
 }
 for(const auto& apk:facts){
  const auto package=apk.at("package").get<std::string>();
  const auto uid=identities.at("packages").at(package).at("app_id").get<unsigned>();
  for(const auto& service:apk.at("declared_services")){
   const auto component=package+"/"+service.at("name").get<std::string>();
   Json decisions=Json::object();
   for(auto caller=callers.begin();caller!=callers.end();++caller)
    decisions[caller.key()]=access.decision(static_cast<unsigned>(std::stoul(caller.key())),component);
   services[component]=Json{{"owner_uid",uid},{"registration_enabled",access.may_register(uid,component)},{"callers",decisions}};
  }
 }
 const Json result{{"schema","saildroid-verified-service-policy-v1"},{"callers",callers},{"apk_hashes",apks},{"services",services}};
 const auto data=result.dump(2)+"\n";require(data.size()<=4*1024*1024,"Service policy exceeds bound");
 const fs::path output=argv[3];Fd directory(open_state_directory(output.parent_path()));const auto name=output.filename().string();
 require(!name.empty()&&name!="."&&name!="..","Invalid output name");
 Fd file(openat(directory.value,name.c_str(),O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600));require(file.value>=0,"New policy required; refusing replacement");
 size_t done=0;while(done<data.size()){const auto count=write(file.value,data.data()+done,data.size()-done);if(count<0&&errno==EINTR)continue;require(count>0,"Cannot write policy");done+=static_cast<size_t>(count);}
 require(fsync(file.value)==0&&fchmod(file.value,0444)==0&&fsync(file.value)==0&&fsync(directory.value)==0,"Cannot seal policy");
 std::cout<<"VERIFIED_SERVICE_POLICY=sealed|callers="<<callers.size()<<"|services="<<services.size()<<"|mode=0444|shared_uid=false\n";
 }catch(const std::exception&e){std::cerr<<"VERIFIED_SERVICE_POLICY_ERROR="<<e.what()<<'\n';return 1;}}
