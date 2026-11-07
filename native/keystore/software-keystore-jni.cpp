// VM prototype: actual original software Keymaster, real Binder caller identity,
// and private UID-separated storage. Not wired into any phone/product service.
#include "private-blob-store.hpp"
#include "software-key-policy.hpp"
#include "mce-lock-state.hpp"
#include <jni.h>
#include <hardware/keymaster2.h>
#include <dlfcn.h>
#include <map>
#include <memory>
#include <limits>

namespace {
constexpr int DENIED=6,NOT_FOUND=7,SYSTEM_ERROR=4,EXISTS=16;
struct Params {
 std::vector<keymaster_key_param_t> items;
 std::vector<std::vector<uint8_t>> blobs;
 Params()=default;Params(const Params&)=delete;Params&operator=(const Params&)=delete;Params(Params&&)=default;
 keymaster_key_param_set_t view() {return {items.data(),items.size()};}
 ~Params(){for(auto&b:blobs)sd_keyblob::wipe_bytes(b.data(),b.size());}
};
struct Bytes {
 std::vector<uint8_t> data;
 Bytes(JNIEnv*e,jbyteArray value){if(!value)return;auto n=e->GetArrayLength(value);sd_keyblob::check(n>=0&&n<=1024*1024,"Input exceeds private operation bound");data.resize(n);if(n)e->GetByteArrayRegion(value,0,n,reinterpret_cast<jbyte*>(data.data()));}
 ~Bytes(){sd_keyblob::wipe_bytes(data.data(),data.size());}
 keymaster_blob_t blob()const{return {data.data(),data.size()};}
};
keymaster2_device_t*device=nullptr;void(*release_native)(void*)=nullptr;
std::unique_ptr<sd_keylock::MceState> lock_state;
std::unique_ptr<sd_keyblob::Store> store;std::set<uid_t> allowed;
std::map<uid_t,std::vector<uint8_t>> attestation_identities;
std::map<uint64_t,uid_t> operations;std::mutex service_lock;
void require(JNIEnv*e,bool ok,const char*msg){if(!ok||e->ExceptionCheck())throw std::runtime_error(msg);}
jclass cls(JNIEnv*e,const char*n){auto c=e->FindClass(n);require(e,c,"Missing original framework class");return c;}
jmethodID method(JNIEnv*e,jclass c,const char*n,const char*s){auto id=e->GetMethodID(c,n,s);require(e,id,"Missing original framework method");return id;}
std::string text(JNIEnv*e,jstring s){sd_keyblob::check(s,"Alias required");const char*p=e->GetStringUTFChars(s,nullptr);require(e,p,"Alias encoding failed");std::string v(p);e->ReleaseStringUTFChars(s,p);return v;}
uid_t caller(JNIEnv*e,int requested) {
 auto c=cls(e,"android/os/Binder");auto tx=e->GetStaticMethodID(c,"isHandlingTransaction","()Z");auto uid=e->GetStaticMethodID(c,"getCallingUid","()I");require(e,tx&&uid,"Original Binder JNI unavailable");
 if(!e->CallStaticBooleanMethod(c,tx)){throw sd_keyblob::Denied();}
 auto actual=e->CallStaticIntMethod(c,uid);require(e,!e->ExceptionCheck(),"Actual Binder identity unavailable");e->DeleteLocalRef(c);
 if(!allowed.count(actual)||(requested!=-1&&requested!=actual)){throw sd_keyblob::Denied();}
 return actual;
}
Params decode(JNIEnv*e,jobject arguments) {
 Params p;if(!arguments)return p;
 auto c=cls(e,"android/security/keymaster/KeymasterArguments");auto field=e->GetFieldID(c,"mArguments","Ljava/util/List;");require(e,field,"Original argument list unavailable");auto list=e->GetObjectField(arguments,field);auto l=cls(e,"java/util/List");auto size=method(e,l,"size","()I"),get=method(e,l,"get","(I)Ljava/lang/Object;");int n=e->CallIntMethod(list,size);require(e,n>=0&&n<=128,"Too many key parameters");p.items.reserve(n);p.blobs.reserve(n);
 for(int i=0;i<n;++i){auto a=e->CallObjectMethod(list,get,i);require(e,a,"Null key parameter");auto ac=e->GetObjectClass(a);auto tf=e->GetFieldID(ac,"tag","I");require(e,tf,"Original tag missing");keymaster_key_param_t item{};item.tag=static_cast<keymaster_tag_t>(e->GetIntField(a,tf));
  switch(keymaster_tag_get_type(item.tag)) {
   case KM_ENUM:case KM_ENUM_REP:case KM_UINT:case KM_UINT_REP:{auto f=e->GetFieldID(ac,"value","I");require(e,f,"Original integer argument missing");item.integer=static_cast<uint32_t>(e->GetIntField(a,f));break;}
   case KM_ULONG:case KM_ULONG_REP:{auto f=e->GetFieldID(ac,"value","J");require(e,f,"Original long argument missing");item.long_integer=static_cast<uint64_t>(e->GetLongField(a,f));break;}
   case KM_DATE:{auto f=e->GetFieldID(ac,"date","Ljava/util/Date;");require(e,f,"Original date argument missing");auto date=e->GetObjectField(a,f);auto dc=cls(e,"java/util/Date");item.date_time=static_cast<uint64_t>(e->CallLongMethod(date,method(e,dc,"getTime","()J")));e->DeleteLocalRef(date);e->DeleteLocalRef(dc);break;}
   case KM_BOOL:item.boolean=true;break;
   case KM_BYTES:case KM_BIGNUM:{auto f=e->GetFieldID(ac,"blob","[B");require(e,f,"Original blob argument missing");auto bytes=static_cast<jbyteArray>(e->GetObjectField(a,f));Bytes b(e,bytes);p.blobs.push_back(std::move(b.data));item.blob={p.blobs.back().data(),p.blobs.back().size()};e->DeleteLocalRef(bytes);break;}
   default:throw std::runtime_error("Unsupported parameter type");
  }
  require(e,!e->ExceptionCheck(),"Cannot decode original key argument");p.items.push_back(item);e->DeleteLocalRef(a);e->DeleteLocalRef(ac);
 }
 e->DeleteLocalRef(c);e->DeleteLocalRef(l);e->DeleteLocalRef(list);return p;
}
jbyteArray bytes(JNIEnv*e,const uint8_t*p,size_t n){sd_keyblob::check(n<=1024*1024,"Native output exceeds bound");auto a=e->NewByteArray(n);require(e,a,"Cannot allocate result bytes");if(n)e->SetByteArrayRegion(a,0,n,reinterpret_cast<const jbyte*>(p));return a;}
jobject encode(JNIEnv*e,const keymaster_key_param_set_t&p){
 auto c=cls(e,"android/security/keymaster/KeymasterArguments");auto out=e->NewObject(c,method(e,c,"<init>","()V"));require(e,out,"Cannot allocate original arguments");sd_keyblob::check(p.length<=128,"Native argument output exceeds bound");
 for(size_t i=0;i<p.length;++i){auto&a=p.params[i];
  switch(keymaster_tag_get_type(a.tag)) {
   case KM_ENUM:case KM_ENUM_REP:e->CallVoidMethod(out,method(e,c,"addEnum","(II)V"),a.tag,a.enumerated);break;
   case KM_UINT:case KM_UINT_REP:e->CallVoidMethod(out,method(e,c,"addUnsignedInt","(IJ)V"),a.tag,static_cast<jlong>(a.integer));break;
   case KM_ULONG:case KM_ULONG_REP:{auto sm=e->GetStaticMethodID(c,"toUint64","(J)Ljava/math/BigInteger;");require(e,sm,"Original uint64 conversion missing");auto value=e->CallStaticObjectMethod(c,sm,static_cast<jlong>(a.long_integer));e->CallVoidMethod(out,method(e,c,"addUnsignedLong","(ILjava/math/BigInteger;)V"),a.tag,value);e->DeleteLocalRef(value);break;}
   case KM_BOOL:e->CallVoidMethod(out,method(e,c,"addBoolean","(I)V"),a.tag);break;
   case KM_DATE:{auto dc=cls(e,"java/util/Date");auto date=e->NewObject(dc,method(e,dc,"<init>","(J)V"),static_cast<jlong>(a.date_time));e->CallVoidMethod(out,method(e,c,"addDate","(ILjava/util/Date;)V"),a.tag,date);e->DeleteLocalRef(date);e->DeleteLocalRef(dc);break;}
   case KM_BYTES:case KM_BIGNUM:{auto b=bytes(e,a.blob.data,a.blob.data_length);e->CallVoidMethod(out,method(e,c,"addBytes","(I[B)V"),a.tag,b);e->DeleteLocalRef(b);break;}
   default:throw std::runtime_error("Native key parameter type not representable");
  }
  require(e,!e->ExceptionCheck(),"Cannot encode genuine native parameter");
 }e->DeleteLocalRef(c);return out;
}
void clear_params(keymaster_key_param_set_t&p){for(size_t i=0;i<p.length;++i)if(keymaster_tag_get_type(p.params[i].tag)==KM_BYTES||keymaster_tag_get_type(p.params[i].tag)==KM_BIGNUM){sd_keyblob::wipe_bytes(const_cast<uint8_t*>(p.params[i].blob.data),p.params[i].blob.data_length);release_native(const_cast<uint8_t*>(p.params[i].blob.data));}release_native(p.params);p={};}
struct NativeOutputs {
 keymaster_key_blob_t key{};keymaster_key_characteristics_t chars{};keymaster_key_param_set_t params{};keymaster_blob_t output{};keymaster_cert_chain_t chain{};
 ~NativeOutputs(){if(!release_native)return;for(size_t i=0;i<chain.entry_count;++i){release_native(const_cast<uint8_t*>(chain.entries[i].data));}release_native(chain.entries);sd_keyblob::wipe_bytes(const_cast<uint8_t*>(key.key_material),key.key_material_size);release_native(const_cast<uint8_t*>(key.key_material));clear_params(chars.hw_enforced);clear_params(chars.sw_enforced);clear_params(params);sd_keyblob::wipe_bytes(const_cast<uint8_t*>(output.data),output.data_length);release_native(const_cast<uint8_t*>(output.data));}
};
void shutdown(){if(device){for(auto&op:operations)device->abort(device,op.first);operations.clear();device->common.close(&device->common);device=nullptr;}store.reset();lock_state.reset();attestation_identities.clear();allowed.clear();}
void throw_java(JNIEnv*e,const char*message){if(!e->ExceptionCheck())e->ThrowNew(cls(e,"java/lang/IllegalStateException"),message);}
} // namespace

extern "C" JNIEXPORT void JNICALL Java_org_saildroid_keystore_NativeSoftwareKeymaster_initialize(JNIEnv*e,jclass,jint fd,jintArray uids,jstring query,jstring linker,jstring library){
 std::lock_guard<std::mutex>guard(service_lock);
 try {
  sd_keyblob::check(!device&&!store&&getuid()==10050&&geteuid()==10050,"VM key service must initialize once as actual UID10050");
  auto n=e->GetArrayLength(uids);sd_keyblob::check(n>0&&n<=10000,"Verified registry required");std::vector<jint> values(n);e->GetIntArrayRegion(uids,0,n,values.data());for(int uid:values){sd_keyblob::check(uid>=10000&&uid<20000&&uid!=10050,"Invalid trusted app UID");allowed.insert(uid);}
  store=std::make_unique<sd_keyblob::Store>(fd,getuid(),allowed,std::set<uint32_t>{1,3,4,32,128});
  auto q=text(e,query),l=text(e,linker),lib=text(e,library);void*abi=dlopen(q.c_str(),RTLD_NOW|RTLD_LOCAL);sd_keyblob::check(abi,"ABI fixture load failed");auto size=reinterpret_cast<size_t(*)()>(dlsym(abi,"softkeymaster_object_size"));auto align=reinterpret_cast<size_t(*)()>(dlsym(abi,"softkeymaster_object_alignment"));sd_keyblob::check(size&&align&&size()==904&&align()==8,"Verified original software device ABI required");
  auto dl=dlopen(l.c_str(),RTLD_NOW|RTLD_GLOBAL);sd_keyblob::check(dl,"Current translated loader required");auto load=reinterpret_cast<void*(*)(const char*,int)>(dlsym(dl,"bionic_dlopen"));auto sym=reinterpret_cast<void*(*)(void*,const char*)>(dlsym(dl,"bionic_dlsym"));sd_keyblob::check(load&&sym,"Translated loader entry points required");auto handle=load(lib.c_str(),RTLD_NOW|RTLD_LOCAL);sd_keyblob::check(handle,"Original keymaster library load failed");auto allocator=dlopen("libc_bio.so.0",RTLD_NOW|RTLD_NOLOAD);auto allocate=reinterpret_cast<void*(*)(size_t)>(dlsym(allocator,"malloc"));release_native=reinterpret_cast<void(*)(void*)>(dlsym(allocator,"free"));auto construct=reinterpret_cast<void(*)(void*)>(sym(handle,"_ZN9keymaster19SoftKeymasterDeviceC1Ev"));auto get=reinterpret_cast<keymaster2_device_t*(*)(void*)>(sym(handle,"_ZN9keymaster19SoftKeymasterDevice17keymaster2_deviceEv"));sd_keyblob::check(allocate&&release_native&&construct&&get,"Original native software exports required");auto object=allocate(size());sd_keyblob::check(object,"Native object allocation failed");construct(object);device=get(object);sd_keyblob::check(device&&device->common.tag==HARDWARE_DEVICE_TAG&&(device->flags&KEYMASTER_SOFTWARE_ONLY),"Genuine software-only device required");
  keymaster_key_param_t configuration[]={keymaster_param_int(KM_TAG_OS_VERSION,100000),keymaster_param_int(KM_TAG_OS_PATCHLEVEL,0)};keymaster_key_param_set_t config{configuration,2};sd_keyblob::check(device->configure(device,&config)==KM_ERROR_OK,"Original keymaster configure failed");
 }catch(const std::exception&x){shutdown();throw_java(e,x.what());}
}
// The service is a separate kernel UID. Only its trusted startup code chooses
// this endpoint; app AIDL onKeyguardVisibilityChanged remains unsupported.
extern "C" JNIEXPORT void JNICALL Java_org_saildroid_keystore_NativeSoftwareKeymaster_configureLockState(JNIEnv*e,jclass,jstring endpoint){
 std::lock_guard<std::mutex>guard(service_lock);
 try {
  auto binder=cls(e,"android/os/Binder");auto handling=e->GetStaticMethodID(binder,"isHandlingTransaction","()Z");require(e,handling,"Original Binder JNI required");bool incoming=e->CallStaticBooleanMethod(binder,handling);e->DeleteLocalRef(binder);
  sd_keyblob::check(getuid()==10050&&geteuid()==10050&&device&&store&&!lock_state&&operations.empty()&&!incoming,"Lock-state backend is trusted startup only");
  lock_state=std::make_unique<sd_keylock::MceState>(text(e,endpoint));
 }catch(const std::exception&x){throw_java(e,x.what());}
}
// Only the trusted isolated service startup can seed real APK identity.
extern "C" JNIEXPORT void JNICALL Java_org_saildroid_keystore_NativeSoftwareKeymaster_configureAttestationIdentity(JNIEnv*e,jclass,jint uid,jbyteArray application_id){
 std::lock_guard<std::mutex>guard(service_lock);
 try {
  auto binder=cls(e,"android/os/Binder");auto handling=e->GetStaticMethodID(binder,"isHandlingTransaction","()Z");require(e,handling,"Original Binder JNI required");bool incoming=e->CallStaticBooleanMethod(binder,handling);e->DeleteLocalRef(binder);
  Bytes value(e,application_id);sd_keyblob::check(getuid()==10050&&geteuid()==10050&&device&&store&&!incoming&&operations.empty()&&allowed.count(uid)&&!attestation_identities.count(uid)&&!value.data.empty()&&value.data.size()<=65536,"Attestation identity requires trusted startup and verified UID");
  attestation_identities.emplace(uid,std::move(value.data));
 }catch(const std::exception&x){throw_java(e,x.what());}
}
extern "C" JNIEXPORT void JNICALL Java_org_saildroid_keystore_NativeSoftwareKeymaster_close(JNIEnv*,jclass){std::lock_guard<std::mutex>guard(service_lock);shutdown();}
// Trusted service lifecycle entry only. It never accepts an app-provided UID:
// the Java service supplies the owner recorded after real Binder authentication.
extern "C" JNIEXPORT jint JNICALL Java_org_saildroid_keystore_NativeSoftwareKeymaster_abortOwned(JNIEnv*,jclass,jlong handle,jint uid){
 std::lock_guard<std::mutex>guard(service_lock);
 if(getuid()!=10050||geteuid()!=10050||!device||!allowed.count(uid))return DENIED;
 const auto h=static_cast<uint64_t>(handle);auto found=operations.find(h);
 if(found==operations.end()||found->second!=static_cast<uid_t>(uid))return KM_ERROR_INVALID_OPERATION_HANDLE;
 auto code=device->abort(device,h);operations.erase(found);return code;
}
extern "C" JNIEXPORT jobject JNICALL Java_org_saildroid_keystore_NativeSoftwareKeymaster_call(JNIEnv*e,jclass,jint op,jstring alias,jint requested,jobject arguments,jbyteArray input,jbyteArray signature,jlong handle,jint purpose){
 std::lock_guard<std::mutex>guard(service_lock);auto rc=cls(e,"org/saildroid/keystore/NativeSoftwareKeymaster$Result");auto result=e->NewObject(rc,method(e,rc,"<init>","()V"));if(!result)return nullptr;int code=SYSTEM_ERROR;
 try {
  sd_keyblob::check(device&&store,"Private native service not initialized");auto uid=caller(e,requested);NativeOutputs out;auto params=decode(e,arguments);auto pv=params.view();Bytes data(e,input),sig(e,signature);std::string name;if(alias)name=text(e,alias);uint64_t native_handle=static_cast<uint64_t>(handle);size_t consumed=0;code=KM_ERROR_UNIMPLEMENTED;
  if(op==16){
   auto key=store->read(uid,name);keymaster_key_blob_t blob{key.data.data(),key.data.size()};
   if(key.algorithm!=KM_ALGORITHM_RSA&&key.algorithm!=KM_ALGORITHM_EC)code=KM_ERROR_INCOMPATIBLE_ALGORITHM;
   else if(!attestation_identities.count(uid))code=KM_ERROR_ATTESTATION_APPLICATION_ID_MISSING;
   else {
    bool valid=true;unsigned challenges=0;
    for(auto&p:params.items){if(p.tag==KM_TAG_ATTESTATION_CHALLENGE)++challenges;else valid=false;}
    if(!valid)code=DENIED;
    else if(challenges>1)code=KM_ERROR_INVALID_ARGUMENT;
    else {
     const auto&id=attestation_identities.at(uid);params.items.push_back(keymaster_param_blob(KM_TAG_ATTESTATION_APPLICATION_ID,id.data(),id.size()));pv=params.view();
     code=device->attest_key(device,&blob,&pv,&out.chain);
     if(code==0){
      sd_keyblob::check(out.chain.entries&&out.chain.entry_count>=2&&out.chain.entry_count<=10,"Invalid native attestation chain");
      auto bc=cls(e,"[B");auto chain=e->NewObjectArray(out.chain.entry_count,bc,nullptr);require(e,chain,"Cannot allocate genuine native certificate chain");size_t total=0;
      for(size_t i=0;i<out.chain.entry_count;++i){const auto&item=out.chain.entries[i];total+=item.data_length;sd_keyblob::check(item.data&&item.data_length&&total<=1024*1024,"Native attestation output exceeds bound");auto b=bytes(e,item.data,item.data_length);e->SetObjectArrayElement(chain,i,b);e->DeleteLocalRef(b);}
      e->SetObjectField(result,e->GetFieldID(rc,"certificates","[[B"),chain);e->DeleteLocalRef(chain);e->DeleteLocalRef(bc);
     }
    }
   }
  }else if(op==15){auto stamp=store->modification_time(uid,name);e->SetLongField(result,e->GetFieldID(rc,"modificationTime","J"),stamp);code=0;}
  else if(op==11){store->create(uid,name,4,data.data,true);code=0;}
  else if(op==12){auto value=store->read(uid,name);if(value.algorithm!=4)throw sd_keyblob::Denied();auto output=bytes(e,value.data.data(),value.data.size());e->SetObjectField(result,e->GetFieldID(rc,"output","[B"),output);e->DeleteLocalRef(output);code=0;}
  else if(op==13){auto values=store->list(uid,name);auto sc=cls(e,"java/lang/String");auto array=e->NewObjectArray(values.size(),sc,nullptr);require(e,array,"Cannot allocate alias results");for(size_t i=0;i<values.size();++i){auto item=e->NewStringUTF(values[i].substr(name.size()).c_str());require(e,item,"Cannot encode literal alias");e->SetObjectArrayElement(array,i,item);e->DeleteLocalRef(item);}e->SetObjectField(result,e->GetFieldID(rc,"aliases","[Ljava/lang/String;"),array);e->DeleteLocalRef(array);e->DeleteLocalRef(sc);code=0;}
  else if(op==10){code=device->add_rng_entropy(device,data.data.data(),data.data.size());}
  else if(op==1||op==14){
   uint32_t algorithm=0;unsigned algorithms=0;bool noauth=false,auth=false,wants_lock=false,unique=false;
   for(auto&p:params.items){
    if(p.tag==KM_TAG_ALGORITHM){algorithm=p.enumerated;++algorithms;}
    if(p.tag==KM_TAG_NO_AUTH_REQUIRED)noauth=true;
    if(p.tag==KM_TAG_INCLUDE_UNIQUE_ID)unique=true;
    if(p.tag==KM_TAG_UNLOCKED_DEVICE_REQUIRED)wants_lock=true;
    switch(p.tag){
     case KM_TAG_ALGORITHM:case KM_TAG_KEY_SIZE:case KM_TAG_PURPOSE:
     case KM_TAG_DIGEST:case KM_TAG_PADDING:case KM_TAG_BLOCK_MODE:case KM_TAG_RSA_PUBLIC_EXPONENT:
     case KM_TAG_EC_CURVE:case KM_TAG_NO_AUTH_REQUIRED:
     case KM_TAG_MIN_MAC_LENGTH:case KM_TAG_CALLER_NONCE:
     case KM_TAG_ACTIVE_DATETIME:case KM_TAG_ORIGINATION_EXPIRE_DATETIME:
     case KM_TAG_USAGE_EXPIRE_DATETIME:break;
     case KM_TAG_UNLOCKED_DEVICE_REQUIRED:
      if(!lock_state){auth=true;}
      break;
     default:auth=true;break; // No silently ignored auth/hardware/new tags.
    }
   }
   if(unique)code=DENIED;
   else if(algorithms!=1)code=KM_ERROR_INVALID_ARGUMENT;
   else if(algorithm!=KM_ALGORITHM_RSA&&algorithm!=KM_ALGORITHM_EC&&algorithm!=KM_ALGORITHM_AES&&algorithm!=KM_ALGORITHM_HMAC)code=KM_ERROR_UNSUPPORTED_ALGORITHM;
   else if(!noauth||auth)code=KM_ERROR_UNSUPPORTED_TAG;
   else {
    // Caller-supplied USER_ID was rejected above. The service derives the real
    // Android user from authenticated Binder UID, and native Keymaster retains
    // both this identity and the lock requirement inside its genuine key blob.
    if(wants_lock){params.items.push_back(keymaster_param_int(KM_TAG_USER_ID,uid/100000));pv=params.view();}
    const bool asymmetric=algorithm==KM_ALGORITHM_RSA||algorithm==KM_ALGORITHM_EC;
    if(op==1)code=device->generate_key(device,&pv,&out.key,&out.chars);
    else if((asymmetric&&purpose!=KM_KEY_FORMAT_PKCS8)||(!asymmetric&&purpose!=KM_KEY_FORMAT_RAW))code=KM_ERROR_UNSUPPORTED_KEY_FORMAT;
    else {auto imported=data.blob();code=device->import_key(device,&pv,static_cast<keymaster_key_format_t>(purpose),&imported,&out.key,&out.chars);}
    if(code==0){
     sd_keyblob::check(out.chars.hw_enforced.length==0,"Software device returned hardware authorizations");
     unsigned actual_algorithms=0;
     for(size_t i=0;i<out.chars.sw_enforced.length;++i)if(out.chars.sw_enforced.params[i].tag==KM_TAG_ALGORITHM){sd_keyblob::check(out.chars.sw_enforced.params[i].enumerated==algorithm,"Native algorithm differs from requested storage kind");++actual_algorithms;}
     sd_keyblob::check(actual_algorithms==1&&out.key.key_material&&out.key.key_material_size,"Missing genuine native key/algorithm");
     if(wants_lock){unsigned locks=0,users=0;for(size_t i=0;i<out.chars.sw_enforced.length;++i){const auto&entry=out.chars.sw_enforced.params[i];if(entry.tag==KM_TAG_UNLOCKED_DEVICE_REQUIRED)++locks;if(entry.tag==KM_TAG_USER_ID){sd_keyblob::check(entry.integer==uid/100000,"Native lock user mismatch");++users;}}sd_keyblob::check(locks==1&&users==1,"Native lock authorization not retained");}
     sd_keyblob::Blob saved(algorithm,std::vector<uint8_t>(out.key.key_material,out.key.key_material+out.key.key_material_size));store->create(uid,name,saved.algorithm,saved.data);
    }
   }
  }else if(op==2||op==3||op==4||op==8||op==9){
   auto key=store->read(uid,name);if(op!=8&&op!=9&&key.algorithm==4)throw sd_keyblob::Denied();keymaster_key_blob_t blob{key.data.data(),key.data.size()};
   if(op==2)code=device->get_key_characteristics(device,&blob,nullptr,nullptr,&out.chars);
   else if(op==3){if(purpose!=KM_KEY_FORMAT_X509||(key.algorithm!=KM_ALGORITHM_RSA&&key.algorithm!=KM_ALGORITHM_EC))code=KM_ERROR_UNSUPPORTED_KEY_FORMAT;else code=device->export_key(device,static_cast<keymaster_key_format_t>(purpose),&blob,nullptr,nullptr,&out.output);}
   else if(op==4){
    code=device->get_key_characteristics(device,&blob,nullptr,nullptr,&out.chars);
    if(code==0)code=sd_keypolicy::authorize(out.chars,static_cast<keymaster_purpose_t>(purpose),pv);
    if(code==0){
     unsigned locks=0,users=0;uint32_t user=~0u;
     for(size_t i=0;i<out.chars.sw_enforced.length;++i){const auto&entry=out.chars.sw_enforced.params[i];if(entry.tag==KM_TAG_UNLOCKED_DEVICE_REQUIRED)++locks;if(entry.tag==KM_TAG_USER_ID){++users;user=entry.integer;}}
     if(locks){
      if(locks!=1||users!=1||user!=uid/100000)code=KM_ERROR_INVALID_KEY_BLOB;
      // API29 allows public encrypt/verify while locked; sign/decrypt require
      // a fresh authenticated system-service query. Unknown/disconnected is locked.
      else if((purpose==KM_PURPOSE_SIGN||purpose==KM_PURPOSE_DECRYPT)&&(!lock_state||!lock_state->unlocked(user)))code=KM_ERROR_DEVICE_LOCKED;
     }
    }
    if(code==0&&operations.size()>=32)code=KM_ERROR_TOO_MANY_OPERATIONS;
    if(code==0)code=device->begin(device,static_cast<keymaster_purpose_t>(purpose),&blob,&pv,&out.params,&native_handle);
    if(code==0){sd_keyblob::check(native_handle&&!operations.count(native_handle),"Invalid native operation handle");operations.emplace(native_handle,uid);}
   }
   else if(op==8){store->erase(uid,name);code=0;}else code=0;
  }else if(op==5||op==6||op==7){
   auto found=operations.find(native_handle);if(found==operations.end()||found->second!=uid)code=KM_ERROR_INVALID_OPERATION_HANDLE;
   else if(op==7){code=device->abort(device,native_handle);operations.erase(found);}
   else {auto in=data.blob(),signature_blob=sig.blob();if(op==5)code=device->update(device,native_handle,&pv,&in,&consumed,&out.params,&out.output);else {code=device->finish(device,native_handle,&pv,&in,signature?&signature_blob:nullptr,&out.params,&out.output);operations.erase(found);}if(op==5&&code!=0){device->abort(device,native_handle);operations.erase(native_handle);}}
  }
  if(code==0){
   if(op==1||op==2||op==14){auto cc=cls(e,"android/security/keymaster/KeyCharacteristics");auto characteristics=e->NewObject(cc,method(e,cc,"<init>","()V"));auto sw=encode(e,out.chars.sw_enforced),hw=encode(e,out.chars.hw_enforced);e->SetObjectField(characteristics,e->GetFieldID(cc,"swEnforced","Landroid/security/keymaster/KeymasterArguments;"),sw);e->SetObjectField(characteristics,e->GetFieldID(cc,"hwEnforced","Landroid/security/keymaster/KeymasterArguments;"),hw);e->SetObjectField(result,e->GetFieldID(rc,"characteristics","Landroid/security/keymaster/KeyCharacteristics;"),characteristics);e->DeleteLocalRef(sw);e->DeleteLocalRef(hw);e->DeleteLocalRef(characteristics);e->DeleteLocalRef(cc);}
   if(op!=12){auto output=bytes(e,out.output.data,out.output.data_length);e->SetObjectField(result,e->GetFieldID(rc,"output","[B"),output);e->DeleteLocalRef(output);}
   auto extra=encode(e,out.params);e->SetObjectField(result,e->GetFieldID(rc,"outParams","Landroid/security/keymaster/KeymasterArguments;"),extra);e->DeleteLocalRef(extra);e->SetLongField(result,e->GetFieldID(rc,"handle","J"),static_cast<jlong>(native_handle));sd_keyblob::check(consumed<=data.data.size()&&consumed<=std::numeric_limits<jint>::max(),"Invalid native consumed count");e->SetIntField(result,e->GetFieldID(rc,"consumed","I"),consumed);
  }
 }catch(const sd_keyblob::Denied&){code=DENIED;}catch(const sd_keyblob::Missing&){code=NOT_FOUND;}catch(const sd_keyblob::Exists&){code=EXISTS;}catch(const std::exception&x){fprintf(stderr,"SOFTWARE_KEYSTORE_NATIVE_ERROR=%s\n",x.what());code=SYSTEM_ERROR;}
 if(e->ExceptionCheck()){return nullptr;}
 e->SetIntField(result,e->GetFieldID(rc,"code","I"),code);e->DeleteLocalRef(rc);return result;
}
