#pragma once
#include "app-identity.hpp"
#include <map>
namespace sd_identity {
// Constructed by the root install supervisor from a durable identity snapshot
// plus fresh successful immutable-APK verifier output. Decisions use the actual
// kernel Binder sender UID, never a package/UID claimed in transaction data.
class ServiceAccess {
  Json identities;
  std::map<std::string,Json> verified;
  std::map<unsigned,std::string> owners;
  std::map<std::string,Json> services;
  std::map<std::string,Json> permissions;
  static bool valid_class(const std::string& name) {
    return name.size()<=512&&std::regex_match(name,
        std::regex("[A-Za-z_$][A-Za-z0-9_$]*(\\.[A-Za-z_$][A-Za-z0-9_$]*)+"));
  }
  static bool requests(const Json& package,const std::string& permission) {
    for(const auto& item:package.at("requested_permissions"))if(item==permission)return true;
    return false;
  }
 public:
  ServiceAccess(const Json& registry,const std::vector<Json>& actual_verified_apks)
      :identities(registry) {
    root_caller();validate(identities);
    for(const auto& apk:actual_verified_apks) {
      require(apk.at("schema")=="saildroid-verified-apk-identity-v1"&&
                  apk.at("backend")=="matching-api29-PackageParser.collectCertificates"&&
                  apk.at("verifier_uid").is_number_integer()&&apk.at("verifier_uid").get<int>()!=0,
              "Real ordinary-UID APK verifier result required");
      const auto package=apk.at("package").get<std::string>();
      require(valid_package(package)&&identities["packages"].contains(package)&&
                  !identities["packages"][package]["retired"].get<bool>(),
              "Verified service package has no active allocated identity");
      const auto& saved=identities["packages"][package];
      require(apk.at("signers")==saved.at("signers")&&apk.at("shared_user_id").is_null()&&
                  apk.at("application_enabled").is_boolean()&&
                  apk.at("requested_permissions").is_array()&&
                  apk.at("declared_permissions").is_array()&&apk.at("declared_services").is_array(),
              "Verified manifest metadata/identity differs");
      const auto hash=apk.at("apk_sha256").get<std::string>();
      require(hash.size()==64&&hash.find_first_not_of("0123456789abcdef")==hash.npos,
              "Invalid verified immutable APK digest");
      require(verified.emplace(package,apk).second,"Duplicate verified package facts");
      const auto uid=saved["app_id"].get<unsigned>();
      require(owners.emplace(uid,package).second,"Duplicate active service owner UID");
      for(const auto& permission:apk.at("declared_permissions")) {
        require(permission.at("package")==package&&permission.at("protection_level").is_number_integer(),
                "Permission definition owner differs");
        const auto name=permission.at("name").get<std::string>();
        require(valid_package(name)&&permissions.emplace(name,permission).second,
                "Duplicate or invalid declared permission");
      }
      for(const auto& service:apk.at("declared_services")) {
        require(service.at("package")==package&&service.at("exported").is_boolean()&&
                    service.at("enabled").is_boolean()&&
                    (service.at("permission").is_null()||service.at("permission").is_string()),
                "Service definition owner or flags differ");
        const auto name=service.at("name").get<std::string>();
        require(valid_class(name)&&services.emplace(package+"/"+name,service).second,
                "Duplicate or invalid declared service");
      }
    }
  }
  bool may_register(unsigned kernel_uid,const std::string& component) const {
    auto service=services.find(component);if(service==services.end())return false;
    const auto package=service->second.at("package").get<std::string>();
    return owners.count(kernel_uid)&&owners.at(kernel_uid)==package&&
           verified.at(package).at("application_enabled").get<bool>()&&
           service->second.at("enabled").get<bool>();
  }
  std::string decision(unsigned kernel_uid,const std::string& component) const {
    auto caller=owners.find(kernel_uid);if(caller==owners.end())return "deny:unknown-kernel-uid";
    auto found=services.find(component);if(found==services.end())return "deny:undeclared-service";
    const auto& service=found->second;const auto owner=service.at("package").get<std::string>();
    if(!verified.at(owner).at("application_enabled").get<bool>()||
       !verified.at(caller->second).at("application_enabled").get<bool>()||
       !service.at("enabled").get<bool>())return "deny:disabled";
    if(owner==caller->second)return "allow:own-uid";
    if(!service.at("exported").get<bool>())return "deny:not-exported";
    if(service.at("permission").is_null())return "allow:exported";
    const auto permission=service.at("permission").get<std::string>();
    if(!requests(verified.at(caller->second),permission))return "deny:permission-not-requested";
    auto definition=permissions.find(permission);if(definition==permissions.end())return "deny:unknown-permission";
    const int protection=definition->second.at("protection_level").get<int>();
    // Explicitly supported base levels only. Dangerous/system/privileged/role/
    // rotation cases require their real dedicated backends; never auto-grant.
    if(protection==0)return "allow:normal-requested";
    if(protection!=2)return "deny:permission-backend-unavailable";
    const auto defining=definition->second.at("package").get<std::string>();
    return verified.at(caller->second).at("signers")==verified.at(defining).at("signers")
        ?"allow:verified-signature":"deny:signature-mismatch";
  }
};
} // namespace sd_identity
