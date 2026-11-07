/* Internal VM contract for the original Android10 software Keymaster library.
 * Uses its own allocator/constructor and the official public C Keymaster2 ABI.
 * Creates fresh in-memory keys only. No keystore daemon, aliases, hardware,
 * credentials, AndroidKeyStore provider, or CTS acceptance is implied.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdbool.h>
#include <hardware/keymaster2.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>

static void (*native_free)(void*);
static unsigned checks;
#define REQUIRE(c) do { if (!(c)) { fprintf(stderr,"SOFT_KEYMASTER=FAIL|line=%d|check=%s\n",__LINE__,#c); exit(2); } ++checks; } while(0)
static void clear_blob(keymaster_blob_t* b) { if(b->data) { memset((void*)b->data,0,b->data_length); native_free((void*)b->data); } memset(b,0,sizeof(*b)); }
static void clear_key(keymaster_key_blob_t* b) { if(b->key_material) { memset((void*)b->key_material,0,b->key_material_size); native_free((void*)b->key_material); } memset(b,0,sizeof(*b)); }
static void clear_params(keymaster_key_param_set_t* p) {
    for(size_t i=0;i<p->length;++i) if(keymaster_tag_get_type(p->params[i].tag)==KM_BYTES || keymaster_tag_get_type(p->params[i].tag)==KM_BIGNUM) native_free((void*)p->params[i].blob.data);
    native_free(p->params); memset(p,0,sizeof(*p));
}
static keymaster_key_blob_t generate(keymaster2_device_t* device, keymaster_algorithm_t algorithm) {
    keymaster_key_param_t p[10]={0}; size_t n=0;
    p[n++]=keymaster_param_enum(KM_TAG_ALGORITHM,algorithm);
    p[n++]=keymaster_param_int(KM_TAG_KEY_SIZE,algorithm==KM_ALGORITHM_RSA?2048:256);
    p[n++]=keymaster_param_enum(KM_TAG_PURPOSE,KM_PURPOSE_SIGN);
    p[n++]=keymaster_param_enum(KM_TAG_PURPOSE,KM_PURPOSE_VERIFY);
    p[n++]=keymaster_param_enum(KM_TAG_DIGEST,KM_DIGEST_SHA_2_256);
    p[n++]=keymaster_param_bool(KM_TAG_NO_AUTH_REQUIRED);
    if(algorithm==KM_ALGORITHM_RSA) {
        p[n++]=keymaster_param_long(KM_TAG_RSA_PUBLIC_EXPONENT,65537);
        p[n++]=keymaster_param_enum(KM_TAG_PADDING,KM_PAD_RSA_PKCS1_1_5_SIGN);
    } else p[n++]=keymaster_param_enum(KM_TAG_EC_CURVE,KM_EC_CURVE_P_256);
    keymaster_key_param_set_t params={p,n}; keymaster_key_blob_t key={0}; keymaster_key_characteristics_t characteristics={0};
    int rc=device->generate_key(device,&params,&key,&characteristics);
    printf("SOFT_KEYMASTER_GENERATE=actual|algorithm=%u|result=%d|hardware_enforced=%zu|software_enforced=%zu\n",algorithm,rc,characteristics.hw_enforced.length,characteristics.sw_enforced.length);
    REQUIRE(rc==KM_ERROR_OK && key.key_material && key.key_material_size>0);
    REQUIRE(characteristics.hw_enforced.length==0 && characteristics.sw_enforced.length>0);
    clear_params(&characteristics.hw_enforced); clear_params(&characteristics.sw_enforced); return key;
}
static int operation(keymaster2_device_t* device, keymaster_algorithm_t algorithm, keymaster_purpose_t purpose, const keymaster_key_blob_t* key, const unsigned char* data, size_t length, const keymaster_blob_t* signature, keymaster_blob_t* result) {
    keymaster_key_param_t p[2]={keymaster_param_enum(KM_TAG_DIGEST,KM_DIGEST_SHA_2_256)};size_t n=1;
    if(algorithm==KM_ALGORITHM_RSA) p[n++]=keymaster_param_enum(KM_TAG_PADDING,KM_PAD_RSA_PKCS1_1_5_SIGN);
    keymaster_key_param_set_t params={p,n};keymaster_operation_handle_t handle=0;
    int rc=device->begin(device,purpose,key,&params,NULL,&handle);if(rc!=KM_ERROR_OK)return rc;
    keymaster_key_param_set_t empty={0};keymaster_blob_t input={data,length};size_t consumed=0;keymaster_blob_t update_output={0};
    rc=device->update(device,handle,&empty,&input,&consumed,NULL,&update_output); clear_blob(&update_output);
    if(rc!=KM_ERROR_OK){device->abort(device,handle);return rc;}
    REQUIRE(consumed<=length);input.data+=consumed;input.data_length-=consumed;
    return device->finish(device,handle,&empty,&input,signature,NULL,result);
}
static void cohort(keymaster2_device_t* device,keymaster_algorithm_t algorithm) {
    const unsigned char message[]="SailDroid genuine software Keymaster generated-key contract";
    keymaster_key_blob_t key=generate(device,algorithm),wrong=generate(device,algorithm);
    keymaster_blob_t signature={0},output={0};
    REQUIRE(operation(device,algorithm,KM_PURPOSE_SIGN,&key,message,sizeof(message)-1,NULL,&signature)==KM_ERROR_OK && signature.data_length>0);
    REQUIRE(operation(device,algorithm,KM_PURPOSE_VERIFY,&key,message,sizeof(message)-1,&signature,&output)==KM_ERROR_OK);clear_blob(&output);
    REQUIRE(operation(device,algorithm,KM_PURPOSE_VERIFY,&wrong,message,sizeof(message)-1,&signature,&output)==KM_ERROR_VERIFICATION_FAILED);clear_blob(&output);
    unsigned char changed[sizeof(message)];memcpy(changed,message,sizeof(message));changed[0]^=1;
    REQUIRE(operation(device,algorithm,KM_PURPOSE_VERIFY,&key,changed,sizeof(message)-1,&signature,&output)==KM_ERROR_VERIFICATION_FAILED);clear_blob(&output);
    ((unsigned char*)signature.data)[signature.data_length/2]^=1;
    REQUIRE(operation(device,algorithm,KM_PURPOSE_VERIFY,&key,message,sizeof(message)-1,&signature,&output)==KM_ERROR_VERIFICATION_FAILED);clear_blob(&output);
    clear_blob(&signature);
    unsigned char* damaged=malloc(key.key_material_size);REQUIRE(damaged);memcpy(damaged,key.key_material,key.key_material_size);damaged[key.key_material_size/2]^=1;
    keymaster_key_blob_t tampered={damaged,key.key_material_size};keymaster_key_param_t digest=keymaster_param_enum(KM_TAG_DIGEST,KM_DIGEST_SHA_2_256);keymaster_key_param_set_t params={&digest,1};keymaster_operation_handle_t handle=0;
    REQUIRE(device->begin(device,KM_PURPOSE_SIGN,&tampered,&params,NULL,&handle)==KM_ERROR_INVALID_KEY_BLOB);memset(damaged,0,key.key_material_size);free(damaged);
    if(algorithm==KM_ALGORITHM_EC) {
        REQUIRE(device->begin(device,KM_PURPOSE_SIGN,&key,&params,NULL,&handle)==KM_ERROR_OK);
        REQUIRE(device->abort(device,handle)==KM_ERROR_OK);
        REQUIRE(device->abort(device,handle)==KM_ERROR_INVALID_OPERATION_HANDLE);
    }
    keymaster_blob_t public_key={0};REQUIRE(device->export_key(device,KM_KEY_FORMAT_X509,&key,NULL,NULL,&public_key)==KM_ERROR_OK && public_key.data_length>0);clear_blob(&public_key);
    clear_key(&key);clear_key(&wrong);
    printf("SOFT_KEYMASTER_COHORT=PASS|algorithm=%u|sign=true|verify=true|wrong_key_rejected=true|tampered_message_rejected=true|tampered_signature_rejected=true|tampered_blob_rejected=true|generated_key_material_cleared=true\n",algorithm);
}
int main(int argc,char**argv) {
    setvbuf(stdout,NULL,_IOLBF,0);REQUIRE(argc==4);REQUIRE(getuid()==65534 && geteuid()==65534);
    void* query=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);REQUIRE(query);
    size_t (*object_size)(void)=dlsym(query,"softkeymaster_object_size");size_t (*object_alignment)(void)=dlsym(query,"softkeymaster_object_alignment");REQUIRE(object_size && object_alignment);
    size_t bytes=object_size();REQUIRE(bytes>0 && bytes<1024*1024 && object_alignment()<=16);
    void* linker=dlopen(argv[2],RTLD_NOW|RTLD_GLOBAL);if(!linker)fprintf(stderr,"linker_error=%s\n",dlerror());REQUIRE(linker);
    void* (*guest_open)(const char*,int)=dlsym(linker,"bionic_dlopen");void*(*guest_symbol)(void*,const char*)=dlsym(linker,"bionic_dlsym");const char*(*guest_error)(void)=dlsym(linker,"bionic_dlerror");REQUIRE(guest_open && guest_symbol && guest_error);
    void* library=guest_open(argv[3],RTLD_NOW|RTLD_LOCAL);if(!library)fprintf(stderr,"native_error=%s\n",guest_error());REQUIRE(library);
    /* The translation exposes libc allocation through its real host-loadable backend.
     * Query that exact already-loaded SONAME, preserving its allocation guards.
     * bionic_dlsym currently rejects the weak C++ operator-new export. */
    void* allocator=dlopen("libc_bio.so.0",RTLD_NOW|RTLD_NOLOAD);REQUIRE(allocator);
    void*(*allocate)(size_t)=dlsym(allocator,"malloc");void(*construct)(void*)=guest_symbol(library,"_ZN9keymaster19SoftKeymasterDeviceC1Ev");keymaster2_device_t*(*get_device)(void*)=guest_symbol(library,"_ZN9keymaster19SoftKeymasterDevice17keymaster2_deviceEv");native_free=dlsym(allocator,"free");REQUIRE(allocate && construct && get_device && native_free);
    void* object=allocate(bytes);REQUIRE(object);construct(object);keymaster2_device_t* device=get_device(object);REQUIRE(device && device->common.tag==HARDWARE_DEVICE_TAG && device->common.module);
    REQUIRE(device->flags & KEYMASTER_SOFTWARE_ONLY);
    printf("SOFT_KEYMASTER_DEVICE=ready|object_bytes=%zu|flags=%u|module=%s|uid=%u|hardware=false\n",bytes,device->flags,device->common.module->name,getuid());
    keymaster_key_param_set_t empty={0};keymaster_key_blob_t key={0};keymaster_key_characteristics_t characteristics={0};
    REQUIRE(device->generate_key(device,&empty,&key,&characteristics)==KM_ERROR_KEYMASTER_NOT_CONFIGURED);
    keymaster_key_param_t configuration[2]={keymaster_param_int(KM_TAG_OS_VERSION,100000),keymaster_param_int(KM_TAG_OS_PATCHLEVEL,0)};keymaster_key_param_set_t config={configuration,2};
    REQUIRE(device->configure(device,&config)==KM_ERROR_OK);
    puts("SOFT_KEYMASTER_CONFIGURATION=ephemeral-test|os_version=100000|os_patchlevel=0|security_patch_claim=false");
    cohort(device,KM_ALGORITHM_RSA);cohort(device,KM_ALGORITHM_EC);
    REQUIRE(device->common.close(&device->common)==0);
    printf("SOFT_KEYMASTER=PASS|checks=%u|real_original_native_library=true|software_only=true|ephemeral_keys_only=true|device_closed=true|AndroidKeyStore_provider=false|CTS_run=false\n",checks);return 0;
}
