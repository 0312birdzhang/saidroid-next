#include "../service-access.hpp"
#include <fstream>
#include <iostream>
using namespace sd_identity;
int main(int argc,char**argv){try{
 require(argc==3,"Actual root registry and fresh verified APK facts required");
 std::ifstream state_file(argv[1]),facts_file(argv[2]);Json state,facts;state_file>>state;facts_file>>facts;
 std::vector<Json> apks=facts.get<std::vector<Json>>();ServiceAccess policy(state,apks);unsigned checks=0;
 auto uid=[&](const std::string& name){return state["packages"].at(name).at("app_id").get<unsigned>();};
 const std::string owner="org.example.saildroid.serviceowner",trusted="org.example.saildroid.servicetrusted",foreign="org.example.saildroid.serviceforeign",unrequested="org.example.saildroid.serviceunrequested";
 auto component=[&](const char* name){return owner+"/org.example.saildroid.servicefixture."+name;};
 auto check=[&](bool value,const char* message){require(value,message);++checks;};
 check(policy.may_register(uid(owner),component("PublicService")),"Actual service owner may register declared endpoint");
 check(!policy.may_register(uid(trusted),component("PublicService")),"Other UID cannot register owner endpoint");
 check(!policy.may_register(uid(foreign),component("PrivateService")),"Foreign signer UID cannot impersonate owner");
 check(!policy.may_register(uid(owner),component("DisabledService")),"Disabled declared endpoint cannot register");
 check(!policy.may_register(uid(owner),component("UndeclaredService")),"Undeclared endpoint cannot register");
 check(policy.decision(uid(owner),component("PrivateService"))=="allow:own-uid","Owner can reach own private endpoint");
 check(policy.decision(uid(trusted),component("PrivateService"))=="deny:not-exported","Same signer cannot override unexported service");
 check(policy.decision(uid(foreign),component("PublicService"))=="allow:exported","Foreign app can reach explicitly public endpoint");
 check(policy.decision(uid(trusted),component("SignatureService"))=="allow:verified-signature","Actual matching APK signer and requested permission permit service");
 check(policy.decision(uid(foreign),component("SignatureService"))=="deny:signature-mismatch","Actual different APK signer cannot receive signature permission");
 check(policy.decision(uid(unrequested),component("SignatureService"))=="deny:permission-not-requested","Same signer without declared request receives no permission");
 check(policy.decision(uid(trusted),component("DangerousService"))=="deny:permission-backend-unavailable","Dangerous permission not invented");
 check(policy.decision(uid(trusted),component("NormalService"))=="allow:normal-requested","Actual normal permission definition/request permitted");
 check(policy.decision(uid(unrequested),component("NormalService"))=="deny:permission-not-requested","Unrequested normal permission denied");
 check(policy.decision(uid(trusted),component("DisabledService"))=="deny:disabled","Disabled service not discoverable");
 check(policy.decision(0,component("PublicService"))=="deny:unknown-kernel-uid","Unregistered root UID does not become an app caller");
 check(policy.decision(19999,component("PublicService"))=="deny:unknown-kernel-uid","Unallocated app UID denied");
 auto bad=apks;bad[1]["signers"]=Json::array({std::string(64,'0')});bool denied=false;try{ServiceAccess changed(state,bad);}catch(...){denied=true;}check(denied,"Service facts must match actual durable verified signer binding");
 auto duplicate=apks;duplicate.push_back(apks[0]);denied=false;try{ServiceAccess changed(state,duplicate);}catch(...){denied=true;}check(denied,"Duplicate APK definition cannot shadow trusted package");
 std::cout<<"SERVICE_ACCESS=ready|checks="<<checks<<"|owner_uid="<<uid(owner)<<"|trusted_uid="<<uid(trusted)<<"|foreign_uid="<<uid(foreign)<<"|actual_signed_apk_metadata=true|no_permission_fabrication=true\n";return 0;
 }catch(const std::exception&e){std::cerr<<"SERVICE_ACCESS=failed|"<<e.what()<<'\n';return 1;}}
