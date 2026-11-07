// Internal prototype protocol over real kernel Binder. This is not Android's
// IKeystoreService wire protocol, Java provider, or a deployable service.
#include "../private-blob-store.hpp"
#include "../../identity/app-identity.hpp"
#include "../../identity/tests/kernel-binder-wire.hpp"
#include "software-keymaster-vm.h"
#include <fstream>
#include <memory>
#include <signal.h>
namespace wire=sd_identity_wire;
constexpr uid_t service_uid=10050;
enum Operation:uint32_t {Generate=1,Sign=2,Verify=3,Erase=4};
struct Request {uint32_t operation=0,algorithm=0,claimed_uid=0,message_length=0,signature_length=0;char alias[128]{};uint8_t message[128]{},signature[512]{};};
struct Response {int32_t result=0;uint32_t actual_caller=0,server_uid=0,length=0;uint8_t signature[512]{};};
static unsigned assertions=0;
static void must(bool condition,const char* message){wire::require(condition,message);++assertions;}
static const char* store_path;static int state_fd=-1;static std::set<uid_t> allowed;
static pid_t start_service(const char* device,const char* query,const char* linker,const char* library,unsigned calls) {
 int ready[2];must(pipe(ready)==0,"Private service readiness pipe");pid_t server=fork();must(server>=0,"Fork actual key-service UID");
 if(!server){try {
  close(ready[0]);wire::ordinary(service_uid);sd_keyblob::Store store(state_fd,service_uid,allowed);close(state_fd);
  std::unique_ptr<sd_softkm,decltype(&sd_softkm_close)> backend(sd_softkm_open(query,linker,library),sd_softkm_close);wire::require(bool(backend),"Create genuine software-only native backend");
  wire::Binder binder(device);int zero=0;wire::require(ioctl(binder.fd,BINDER_SET_CONTEXT_MGR,&zero)==0,"Claim fresh real Binder context");std::vector<uint8_t> commands;uint32_t enter=BC_ENTER_LOOPER;wire::append(commands,enter);binder.exchange(commands,false);wire::require(write(ready[1],"R",1)==1,"Publish native key-service readiness");close(ready[1]);
  for(unsigned i=0;i<calls;++i){auto incoming=binder.transaction(false);wire::require(incoming.code==0x194b&&incoming.data_size==sizeof(Request),"Complete bounded key request");Request request{};memcpy(&request,reinterpret_cast<const void*>(incoming.data.ptr.buffer),sizeof(request));Response response{};response.actual_caller=incoming.sender_euid;response.server_uid=getuid();
   try {
    if(!allowed.count(incoming.sender_euid))throw sd_keyblob::Denied();
    wire::require(request.message_length<=sizeof(request.message)&&request.signature_length<=sizeof(request.signature)&&strnlen(request.alias,sizeof(request.alias))<sizeof(request.alias),"Bounded caller payload");
    const std::string alias(request.alias);const uid_t caller=incoming.sender_euid;
    if(request.operation==Generate){keymaster_key_blob_t key{};response.result=sd_softkm_generate(backend.get(),request.algorithm,&key);if(response.result==KM_ERROR_OK){try{sd_keyblob::Blob pending(request.algorithm,{key.key_material,key.key_material+key.key_material_size});store.create(caller,alias,request.algorithm,pending.data);}catch(...){sd_softkm_clear_key(backend.get(),&key);throw;}sd_softkm_clear_key(backend.get(),&key);}}
    else if(request.operation==Erase){store.erase(caller,alias);response.result=KM_ERROR_OK;}
    else if(request.operation==Sign||request.operation==Verify){auto saved=store.read(caller,alias);keymaster_key_blob_t key{saved.data.data(),saved.data.size()};keymaster_blob_t signature{request.signature,request.signature_length},output{};
     response.result=sd_softkm_operation(backend.get(),saved.algorithm,request.operation==Sign?KM_PURPOSE_SIGN:KM_PURPOSE_VERIFY,&key,request.message,request.message_length,request.operation==Verify?&signature:nullptr,&output);
     if(response.result==KM_ERROR_OK&&request.operation==Sign){wire::require(output.data_length<=sizeof(response.signature),"Bounded real signature");response.length=output.data_length;memcpy(response.signature,output.data,output.data_length);}sd_softkm_clear_blob(backend.get(),&output);std::fill(saved.data.begin(),saved.data.end(),0);
    }else throw std::runtime_error("Unknown private key operation");
   }catch(const sd_keyblob::Denied&){response.result=-1001;}catch(const sd_keyblob::Missing&){response.result=-1002;}catch(const sd_keyblob::Exists&){response.result=-1003;}catch(const std::exception&e){dprintf(2,"PRIVATE_KEY_REQUEST=denied|reason=%s\n",e.what());response.result=-1004;}
   binder_transaction_data reply{};reply.data_size=sizeof(response);reply.data.ptr.buffer=reinterpret_cast<binder_uintptr_t>(&response);commands.clear();uint32_t free_buffer=BC_FREE_BUFFER,reply_command=BC_REPLY;wire::append(commands,free_buffer);wire::append(commands,incoming.data.ptr.buffer);wire::append(commands,reply_command);wire::append(commands,reply);binder.exchange(commands,false);
   dprintf(1,"PRIVATE_KEY_IPC=handled|kernel_uid=%u|service_uid=%u|operation=%u|result=%d|claimed_uid_ignored=true\n",incoming.sender_euid,getuid(),request.operation,response.result);
  }
  backend.reset();dprintf(1,"PRIVATE_KEY_SERVICE=stopped|actual_uid=%u|calls=%u|original_device_closed=true\n",getuid(),calls);_exit(0);
 }catch(const std::exception&e){dprintf(2,"PRIVATE_KEY_SERVICE=failed|%s\n",e.what());_exit(1);}}
 close(ready[1]);char marker=0;must(read(ready[0],&marker,1)==1&&marker=='R',"Wait real key service");close(ready[0]);return server;
}
static Response call(const char* device,uid_t uid,Request request) {
 int result_pipe[2];must(pipe(result_pipe)==0,"Key client response pipe");pid_t child=fork();must(child>=0,"Fork real application caller");
 if(!child){try{
  close(result_pipe[0]);close(state_fd);wire::ordinary(uid);errno=0;int private_directory=open(store_path,O_RDONLY|O_DIRECTORY|O_CLOEXEC);wire::require(private_directory<0&&errno==EACCES,"Application cannot read service-owned private store");
  wire::Binder binder(device);binder_transaction_data transaction{};transaction.target.handle=0;transaction.code=0x194b;transaction.sender_euid=0;transaction.sender_pid=1;transaction.data_size=sizeof(request);transaction.data.ptr.buffer=reinterpret_cast<binder_uintptr_t>(&request);std::vector<uint8_t> commands;uint32_t send=BC_TRANSACTION;wire::append(commands,send);wire::append(commands,transaction);binder.exchange(commands,false);auto incoming=binder.transaction(true);wire::require(incoming.data_size==sizeof(Response),"Complete private key reply");Response response{};memcpy(&response,reinterpret_cast<const void*>(incoming.data.ptr.buffer),sizeof(response));wire::require(response.actual_caller==uid&&response.server_uid==service_uid,"Genuine kernel caller/service UID response");commands.clear();uint32_t free_buffer=BC_FREE_BUFFER;wire::append(commands,free_buffer);wire::append(commands,incoming.data.ptr.buffer);binder.exchange(commands,false);wire::require(write(result_pipe[1],&response,sizeof(response))==sizeof(response),"Publish actual response to test parent");_exit(0);
 }catch(const std::exception&e){dprintf(2,"PRIVATE_KEY_CLIENT=failed|%s\n",e.what());_exit(1);}}
 close(result_pipe[1]);Response response{};size_t offset=0;while(offset<sizeof(response)){ssize_t n=read(result_pipe[0],reinterpret_cast<char*>(&response)+offset,sizeof(response)-offset);if(n<0&&errno==EINTR)continue;must(n>0,"Read actual application result");offset+=n;}close(result_pipe[0]);int status;must(waitpid(child,&status,0)==child&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"Actual key client exited cleanly");return response;
}
static Request request(Operation operation,uint32_t algorithm=KM_ALGORITHM_RSA,const std::vector<uint8_t>& signature={}) {
 Request r{};r.operation=operation;r.algorithm=algorithm;r.claimed_uid=0;strcpy(r.alias,"same-alias");const char message[]="original native key ownership and restart proof";r.message_length=sizeof(message)-1;memcpy(r.message,message,r.message_length);r.signature_length=signature.size();if(!signature.empty())memcpy(r.signature,signature.data(),signature.size());return r;
}
static void service_done(pid_t& server){int status;must(waitpid(server,&status,0)==server&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"Actual key service exited cleanly");server=-1;}
int main(int argc,char**argv){pid_t server=-1;try{
 must(argc==8&&getuid()==0,"Root orchestrator: registry,state,two Binder nodes,ABI query,linker,original native library");std::ifstream input(argv[1]);sd_identity::Json registry;input>>registry;input.close();sd_identity::validate(registry);for(auto it=registry["packages"].begin();it!=registry["packages"].end();++it)if(!it.value()["retired"].get<bool>())allowed.insert(it.value()["app_id"].get<uid_t>());
 const uid_t owner=registry["packages"]["org.example.saildroid.serviceowner"]["app_id"].get<uid_t>(),other=registry["packages"]["org.example.saildroid.servicetrusted"]["app_id"].get<uid_t>();must(owner!=other&&allowed.count(owner)&&allowed.count(other)&&!allowed.count(19999),"Actual verified distinct app UID assignments");store_path=argv[2];state_fd=open(store_path,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);must(state_fd>=0,"Pin real private service state");
 server=start_service(argv[3],argv[5],argv[6],argv[7],10);
 must(call(argv[3],owner,request(Generate)).result==0,"Owner creates genuine RSA key");
 must(call(argv[3],owner,request(Generate)).result==-1003,"Existing alias cannot silently replace a key");
 must(call(argv[3],other,request(Sign)).result==-1002,"Other UID cannot use owner's alias");
 must(call(argv[3],other,request(Erase)).result==-1002,"Other UID cannot delete owner's alias");
 must(call(argv[3],other,request(Generate,KM_ALGORITHM_EC)).result==0,"Second UID owns independent same-name EC alias");
 auto signed_value=call(argv[3],owner,request(Sign));must(signed_value.result==0&&signed_value.length>0,"Real RSA signature over Binder");std::vector<uint8_t> signature(signed_value.signature,signed_value.signature+signed_value.length);
 must(call(argv[3],owner,request(Verify,KM_ALGORITHM_RSA,signature)).result==0,"Owner verifies real signature");
 must(call(argv[3],other,request(Verify,KM_ALGORITHM_EC,signature)).result==KM_ERROR_VERIFICATION_FAILED,"Other same-name alias cannot verify owner key signature");
 must(call(argv[3],19999,request(Generate)).result==-1001,"Unregistered actual UID cannot allocate keys despite forged root payload");
 auto tampered=request(Verify,KM_ALGORITHM_RSA,signature);tampered.message[0]^=1;must(call(argv[3],owner,tampered).result==KM_ERROR_VERIFICATION_FAILED,"Real native verification rejects modified message");service_done(server);
 server=start_service(argv[4],argv[5],argv[6],argv[7],9);
 auto after_restart=call(argv[4],owner,request(Sign));must(after_restart.result==0&&after_restart.length>0,"Persisted genuine RSA key usable after complete service/backend restart");signature.assign(after_restart.signature,after_restart.signature+after_restart.length);
 must(call(argv[4],owner,request(Verify,KM_ALGORITHM_RSA,signature)).result==0,"Persisted native key verifies after restart");
 auto other_signed=call(argv[4],other,request(Sign,KM_ALGORITHM_EC));must(other_signed.result==0&&other_signed.length>0,"Second UID EC key survives restart");std::vector<uint8_t> other_signature(other_signed.signature,other_signed.signature+other_signed.length);
 must(call(argv[4],other,request(Verify,KM_ALGORITHM_EC,other_signature)).result==0,"Actual EC verification after restart");
 must(call(argv[4],owner,request(Erase)).result==0,"Owner durably deletes own alias");must(call(argv[4],owner,request(Sign)).result==-1002,"Deleted key is absent");
 must(call(argv[4],other,request(Sign,KM_ALGORITHM_EC)).result==0,"Deleting owner key preserves other UID key");
 must(call(argv[4],19999,request(Sign)).result==-1001,"Unknown UID rejected after restart");must(call(argv[4],other,request(Erase)).result==0,"Second owner deletes its own key");service_done(server);close(state_fd);state_fd=-1;
 std::cout<<"PRIVATE_KEY_KERNEL_STORE=PASS|assertions="<<assertions<<"|actual_calls=19|real_signed_app_uids=true|kernel_sender_not_payload=true|private_store_kernel_permissions=true|real_service_restart=true|native_RSA_EC=true|same_alias_isolated=true|unknown_uid_denied=true|AndroidKeyStore_protocol=false|CTS_run=false\n";return 0;
 }catch(const std::exception&e){if(server>0){kill(server,SIGKILL);waitpid(server,nullptr,0);}if(state_fd>=0)close(state_fd);std::cerr<<"PRIVATE_KEY_KERNEL_STORE=failed|"<<e.what()<<'\n';return 1;}}
