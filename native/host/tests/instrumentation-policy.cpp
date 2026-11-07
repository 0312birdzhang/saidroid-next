#include "../instrumentation-policy.hpp"
#include <sys/wait.h>

int main(int argc,char **argv) {
  if(argc!=2||getuid()!=0)return 2;
  fs::path root=fs::canonical(argv[1]),dir=root/"grants",apk=root/"app.apk",file=dir/"run.json";
  fs::create_directory(dir);chmod(root.c_str(),0755);chmod(dir.c_str(),0755);
  {std::ofstream out(apk);out<<"exact fixture APK bytes";}chmod(apk.c_str(),0644);
  Json request={{"run_id","test-run"},{"component","org.example.policy/Runner"},{"official_policy_grant",file.string()}};
  auto raw=request.dump();
  Json valid={{"schema","saidroid-official-instrumentation-policy-v1"},{"boot",boot_id()},
    {"component_root",root.string()},{"package","org.example.policy"},{"run_id","test-run"},
    {"instrumentation",request["component"]},{"request_sha256",sha(raw)},
    {"apk_sha256",sha(read_text(apk))},{"hidden_api_checks",false},
    {"expires_monotonic_us",static_cast<uint64_t>(g_get_monotonic_time())+60000000},
    {"official_config_sha256",std::string(64,'a')}};
  auto write=[&](const Json &v){fs::remove(file);std::ofstream out(file);out<<v.dump();out.close();chmod(file.c_str(),0644);};
  auto call=[&]{return instrumentation_hidden_api_checks(request,raw,root,"org.example.policy",apk,dir);};
  unsigned checks=0;
  auto reject=[&](const char *label){bool denied=false;try{call();}catch(const std::exception &){denied=true;}if(!denied)throw std::runtime_error(std::string("Accepted ")+label);checks++;};
  write(valid);if(call())throw std::runtime_error("Valid run grant denied");checks++;
  pid_t child=fork();if(!child){if(setgid(65534)||setuid(65534))_exit(3);try{_exit(call()?4:0);}catch(...){_exit(5);}}
  int status=0;waitpid(child,&status,0);if(!WIFEXITED(status)||WEXITSTATUS(status))throw std::runtime_error("Ordinary user cannot consume valid grant");checks++;
  if(!instrumentation_hidden_api_checks(Json::object(),"{}",root,"org.example.policy",apk,dir))throw std::runtime_error("Normal app policy relaxed");checks++;
  for(const auto &entry:std::vector<std::pair<std::string,Json>>{
    {"package","org.example.other"},{"boot","other-boot"},{"component_root","/other"},
    {"run_id","other-run"},{"instrumentation","org.other/Runner"},{"request_sha256",std::string(64,'b')},
    {"apk_sha256",std::string(64,'c')},{"hidden_api_checks",true},{"hidden_api_checks",0},{"official_config_sha256","invalid"},
    {"expires_monotonic_us",0},{"expires_monotonic_us",static_cast<uint64_t>(g_get_monotonic_time())+13ULL*3600*1000000}}){
      auto altered=valid;altered[entry.first]=entry.second;write(altered);reject(entry.first.c_str());
  }
  write(valid);chmod(file.c_str(),0666);reject("writable file");
  write(valid);chown(file.c_str(),65534,65534);reject("user-owned file");
  write(valid);chmod(dir.c_str(),0777);reject("writable directory");chmod(dir.c_str(),0755);
  write(valid);fs::path saved=dir/"saved.json";fs::rename(file,saved);fs::create_symlink(saved,file);reject("symlink");fs::remove(file);fs::rename(saved,file);
  fs::create_hard_link(file,saved);reject("hardlink");fs::remove(saved);
  write(valid);auto old=request;request["official_policy_grant"]=(root/"outside.json").string();reject("outside directory");request=old;
  bool denied=false;try{instrumentation_hidden_api_checks(Json{{"hidden_api_checks",false}},"{}",root,"org.example.policy",apk,dir);}catch(...){denied=true;}
  if(!denied)throw std::runtime_error("Application request granted itself an override");checks++;
  std::cout<<"INSTRUMENTATION_POLICY=PASS|checks="<<checks<<"|ordinary_app=enforced|root_run_grant=bounded|tampering=denied\n";
}
