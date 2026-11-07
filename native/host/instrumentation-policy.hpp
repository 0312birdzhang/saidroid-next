#pragma once
#include "host-common.hpp"

// Root-owned, run-scoped authorization for an original instrumentation option.
// An application's writable request cannot grant itself a hidden-API exemption.
inline bool instrumentation_hidden_api_checks(
    const Json &request, const std::string &request_bytes,
    const fs::path &component, const std::string &package,
    const fs::path &apk, const fs::path &policy_directory = "/home/art/test/cts-run-policies") {
  if (!request.contains("official_policy_grant")) {
    if (request.contains("hidden_api_checks") && request.at("hidden_api_checks") != true)
      throw std::runtime_error("Untrusted instrumentation policy override");
    return true;
  }
  auto fail = [] { throw std::runtime_error("Invalid official instrumentation policy grant"); };
  struct stat parent{};
  if (lstat(policy_directory.c_str(), &parent) || !S_ISDIR(parent.st_mode) ||
      parent.st_uid != 0 || (parent.st_mode & 022) ||
      fs::canonical(policy_directory) != policy_directory) fail();
  fs::path path=request.at("official_policy_grant").get<std::string>();
  if (path.parent_path()!=policy_directory ||
      !std::regex_match(path.filename().string(),std::regex("[A-Za-z0-9_.-]+\\.json"))) fail();
  int fd=open(path.c_str(),O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
  if(fd<0)fail();
  struct stat info{};
  if(fstat(fd,&info)||!S_ISREG(info.st_mode)||info.st_uid!=0||
      (info.st_mode&022)||info.st_nlink!=1||info.st_size<=0||info.st_size>8192){close(fd);fail();}
  std::string bytes(static_cast<size_t>(info.st_size),'\0');size_t offset=0;
  while(offset<bytes.size()){
    ssize_t n=read(fd,bytes.data()+offset,bytes.size()-offset);
    if(n<0&&errno==EINTR)continue;
    if(n<=0){close(fd);fail();}
    offset+=static_cast<size_t>(n);
  }
  close(fd);
  auto grant=Json::parse(bytes);
  const auto now=static_cast<uint64_t>(g_get_monotonic_time());
  auto expiry=grant.at("expires_monotonic_us").get<uint64_t>();
  if(grant.at("schema")!="saidroid-official-instrumentation-policy-v1" ||
      grant.at("boot")!=boot_id() || grant.at("package")!=package ||
      grant.at("component_root")!=component.string() ||
      grant.at("run_id")!=request.at("run_id") ||
      grant.at("instrumentation")!=request.at("component") ||
      grant.at("request_sha256")!=sha(request_bytes) ||
      grant.at("apk_sha256")!=sha(read_text(apk)) ||
      (!grant.at("hidden_api_checks").is_boolean()||grant.at("hidden_api_checks").get<bool>()) ||
      expiry<=now || expiry-now>12ULL*60*60*1000000 ||
      !std::regex_match(grant.at("official_config_sha256").get<std::string>(),
                        std::regex("[0-9a-f]{64}"))) fail();
  std::cerr<<"SDHOST=instrumentation_hidden_api_policy|checks=disabled|scope=single-process|authorization=root-owned-run-grant|config_sha256="
           <<grant.at("official_config_sha256").get<std::string>()<<'\n';
  return false;
}
