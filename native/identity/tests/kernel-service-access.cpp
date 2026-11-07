#include "../service-access.hpp"
#include "kernel-binder-wire.hpp"
#include <fstream>
namespace wire=sd_identity_wire;
struct ServiceProof {uint32_t caller,owner,allowed,payload;};
int main(int argc,char**argv){try{
 wire::require(argc==8&&getuid()==0,"Actual root identity/policy/device/caller/service/expectation required");
 std::ifstream registry_file(argv[1]),facts_file(argv[2]);sd_identity::Json registry,facts;registry_file>>registry;facts_file>>facts;
 sd_identity::ServiceAccess policy(registry,facts.get<std::vector<sd_identity::Json>>());
 const std::string owner="org.example.saildroid.serviceowner";
 const unsigned server_uid=registry["packages"][owner]["app_id"].get<unsigned>();
 const unsigned client_uid=std::stoul(argv[4]);const std::string component=argv[5],expected=argv[6];
 const bool expected_allowed=expected.rfind("allow:",0)==0;
 const unsigned payload=std::stoul(argv[7]);
 int ready[2];wire::require(pipe(ready)==0,"Create service readiness pipe");pid_t server=fork();wire::require(server>=0,"Fork actual service UID");
 if(!server){try{
  close(ready[0]);wire::ordinary(server_uid);wire::Binder binder(argv[3]);
  wire::require(policy.may_register(getuid(),owner+"/org.example.saildroid.servicefixture.PublicService"),"Root-verified owner registers service namespace");
  int unused=0;wire::require(ioctl(binder.fd,BINDER_SET_CONTEXT_MGR,&unused)==0,"Actual private context claim");std::vector<uint8_t>commands;uint32_t enter=BC_ENTER_LOOPER;wire::append(commands,enter);binder.exchange(commands,false);wire::require(write(ready[1],"R",1)==1,"Publish real service readiness");close(ready[1]);
  auto incoming=binder.transaction(false);wire::require(incoming.code==0x194&&incoming.data_size==sizeof(uint32_t),"Actual service request shape");
  uint32_t actual;memcpy(&actual,reinterpret_cast<const void*>(incoming.data.ptr.buffer),sizeof(actual));wire::require(actual==payload,"Actual request payload");
  // Authorization uses only the kernel-stamped UID and immutable root-verified
  // manifest data inherited by this service process. Sender fields are ignored.
  const auto decision=policy.decision(incoming.sender_euid,component);
  wire::require(decision==expected&&incoming.sender_euid==client_uid,"Actual service access decision for genuine kernel UID");
  ServiceProof proof{incoming.sender_euid,static_cast<uint32_t>(getuid()),decision.rfind("allow:",0)==0,actual+1};binder_transaction_data reply{};reply.data_size=sizeof(proof);reply.data.ptr.buffer=reinterpret_cast<binder_uintptr_t>(&proof);commands.clear();uint32_t free_buffer=BC_FREE_BUFFER;wire::append(commands,free_buffer);wire::append(commands,incoming.data.ptr.buffer);uint32_t reply_command=BC_REPLY;wire::append(commands,reply_command);wire::append(commands,reply);binder.exchange(commands,false);
  dprintf(1,"KERNEL_SERVICE_ACCESS=handled|actual_caller_uid=%u|service_uid=%u|decision=%s|claimed_root_ignored=true\n",incoming.sender_euid,getuid(),decision.c_str());_exit(0);
 }catch(const std::exception&e){dprintf(2,"KERNEL_SERVICE_ACCESS=failed|%s\n",e.what());_exit(1);}}
 close(ready[1]);char marker;wire::require(read(ready[0],&marker,1)==1&&marker=='R',"Actual declared service ready");close(ready[0]);pid_t client=fork();wire::require(client>=0,"Fork actual application caller");
 if(!client){try{
  wire::ordinary(client_uid);wire::Binder binder(argv[3]);binder_transaction_data request{};request.target.handle=0;request.code=0x194;request.sender_euid=0;request.sender_pid=1;request.data_size=sizeof(payload);request.data.ptr.buffer=reinterpret_cast<binder_uintptr_t>(&payload);std::vector<uint8_t>commands;uint32_t transaction=BC_TRANSACTION;wire::append(commands,transaction);wire::append(commands,request);binder.exchange(commands,false);auto incoming=binder.transaction(true);wire::require(incoming.data_size==sizeof(ServiceProof),"Actual service response shape");ServiceProof proof;memcpy(&proof,reinterpret_cast<const void*>(incoming.data.ptr.buffer),sizeof(proof));wire::require(proof.caller==client_uid&&proof.owner==server_uid&&bool(proof.allowed)==expected_allowed&&proof.payload==payload+1,"Actual permission decision/data/identity response");commands.clear();uint32_t free_buffer=BC_FREE_BUFFER;wire::append(commands,free_buffer);wire::append(commands,incoming.data.ptr.buffer);binder.exchange(commands,false);_exit(0);
 }catch(const std::exception&e){dprintf(2,"KERNEL_SERVICE_CLIENT=failed|%s\n",e.what());_exit(1);}}
 int a,b;wire::require(waitpid(client,&a,0)==client&&waitpid(server,&b,0)==server,"Wait own service/client");wire::require(WIFEXITED(a)&&WEXITSTATUS(a)==0&&WIFEXITED(b)&&WEXITSTATUS(b)==0,"Actual service permission contract");std::cout<<"KERNEL_SERVICE_POLICY=ready|actual_signed_apk_metadata=true|actual_kernel_caller="<<client_uid<<"|decision="<<expected<<'\n';return 0;
 }catch(const std::exception&e){std::cerr<<"KERNEL_SERVICE_POLICY=failed|"<<e.what()<<'\n';return 1;}}
