/* Original software-only native operations for bounded VM IPC/storage tests.
 * Library paths are fixed by the root test orchestrator, never by an IPC caller.
 */
#define _GNU_SOURCE
#include "software-keymaster-vm.h"
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
struct sd_softkm {keymaster2_device_t* device;void(*release)(void*);};
static void params_clear(struct sd_softkm*s,keymaster_key_param_set_t*p) {
 for(size_t i=0;i<p->length;++i)if(keymaster_tag_get_type(p->params[i].tag)==KM_BYTES||keymaster_tag_get_type(p->params[i].tag)==KM_BIGNUM)s->release((void*)p->params[i].blob.data);
 s->release(p->params);memset(p,0,sizeof(*p));
}
struct sd_softkm* sd_softkm_open(const char* query_path,const char* linker_path,const char* library_path) {
 void*query=dlopen(query_path,RTLD_NOW|RTLD_LOCAL);if(!query)return NULL;
 size_t(*size)(void)=dlsym(query,"softkeymaster_object_size"),(*alignment)(void)=dlsym(query,"softkeymaster_object_alignment");if(!size||!alignment||size()==0||size()>1024*1024||alignment()>16)return NULL;
 void*linker=dlopen(linker_path,RTLD_NOW|RTLD_GLOBAL);if(!linker)return NULL;
 void*(*load)(const char*,int)=dlsym(linker,"bionic_dlopen");void*(*symbol)(void*,const char*)=dlsym(linker,"bionic_dlsym");if(!load||!symbol)return NULL;
 void*library=load(library_path,RTLD_NOW|RTLD_LOCAL);if(!library)return NULL;
 void*allocator=dlopen("libc_bio.so.0",RTLD_NOW|RTLD_NOLOAD);if(!allocator)return NULL;
 void*(*allocate)(size_t)=dlsym(allocator,"malloc");void(*release)(void*)=dlsym(allocator,"free");void(*construct)(void*)=symbol(library,"_ZN9keymaster19SoftKeymasterDeviceC1Ev");keymaster2_device_t*(*get_device)(void*)=symbol(library,"_ZN9keymaster19SoftKeymasterDevice17keymaster2_deviceEv");if(!allocate||!release||!construct||!get_device)return NULL;
 void*object=allocate(size());if(!object)return NULL;construct(object);keymaster2_device_t*device=get_device(object);
 if(!device||device->common.tag!=HARDWARE_DEVICE_TAG||!(device->flags&KEYMASTER_SOFTWARE_ONLY)){if(device)device->common.close(&device->common);return NULL;}
 keymaster_key_param_t configuration[]={keymaster_param_int(KM_TAG_OS_VERSION,100000),keymaster_param_int(KM_TAG_OS_PATCHLEVEL,0)};keymaster_key_param_set_t config={configuration,2};
 if(device->configure(device,&config)!=KM_ERROR_OK){device->common.close(&device->common);return NULL;}
 struct sd_softkm*s=calloc(1,sizeof(*s));if(!s){device->common.close(&device->common);return NULL;}s->device=device;s->release=release;return s;
}
void sd_softkm_close(struct sd_softkm*s){if(s){s->device->common.close(&s->device->common);memset(s,0,sizeof(*s));free(s);}}
void sd_softkm_clear_key(struct sd_softkm*s,keymaster_key_blob_t*b){if(b->key_material){memset((void*)b->key_material,0,b->key_material_size);s->release((void*)b->key_material);}memset(b,0,sizeof(*b));}
void sd_softkm_clear_blob(struct sd_softkm*s,keymaster_blob_t*b){if(b->data){memset((void*)b->data,0,b->data_length);s->release((void*)b->data);}memset(b,0,sizeof(*b));}
int sd_softkm_generate(struct sd_softkm*s,uint32_t algorithm,keymaster_key_blob_t*key){
 if(algorithm!=KM_ALGORITHM_RSA&&algorithm!=KM_ALGORITHM_EC)return KM_ERROR_UNSUPPORTED_ALGORITHM;
 keymaster_key_param_t p[10]={0};size_t n=0;p[n++]=keymaster_param_enum(KM_TAG_ALGORITHM,algorithm);p[n++]=keymaster_param_int(KM_TAG_KEY_SIZE,algorithm==KM_ALGORITHM_RSA?2048:256);p[n++]=keymaster_param_enum(KM_TAG_PURPOSE,KM_PURPOSE_SIGN);p[n++]=keymaster_param_enum(KM_TAG_PURPOSE,KM_PURPOSE_VERIFY);p[n++]=keymaster_param_enum(KM_TAG_DIGEST,KM_DIGEST_SHA_2_256);p[n++]=keymaster_param_bool(KM_TAG_NO_AUTH_REQUIRED);
 if(algorithm==KM_ALGORITHM_RSA){p[n++]=keymaster_param_long(KM_TAG_RSA_PUBLIC_EXPONENT,65537);p[n++]=keymaster_param_enum(KM_TAG_PADDING,KM_PAD_RSA_PKCS1_1_5_SIGN);}else p[n++]=keymaster_param_enum(KM_TAG_EC_CURVE,KM_EC_CURVE_P_256);
 keymaster_key_param_set_t params={p,n};keymaster_key_characteristics_t characteristics={0};int result=s->device->generate_key(s->device,&params,key,&characteristics);
 if(result==KM_ERROR_OK&&characteristics.hw_enforced.length)result=KM_ERROR_UNKNOWN_ERROR;
 params_clear(s,&characteristics.hw_enforced);params_clear(s,&characteristics.sw_enforced);if(result!=KM_ERROR_OK)sd_softkm_clear_key(s,key);return result;
}
int sd_softkm_operation(struct sd_softkm*s,uint32_t algorithm,keymaster_purpose_t purpose,const keymaster_key_blob_t*key,const uint8_t*message,size_t length,const keymaster_blob_t*signature,keymaster_blob_t*output){
 keymaster_key_param_t p[2]={keymaster_param_enum(KM_TAG_DIGEST,KM_DIGEST_SHA_2_256)};size_t n=1;if(algorithm==KM_ALGORITHM_RSA)p[n++]=keymaster_param_enum(KM_TAG_PADDING,KM_PAD_RSA_PKCS1_1_5_SIGN);keymaster_key_param_set_t params={p,n},empty={0};keymaster_operation_handle_t handle=0;int result=s->device->begin(s->device,purpose,key,&params,NULL,&handle);if(result!=KM_ERROR_OK)return result;
 keymaster_blob_t input={message,length},temporary={0};size_t consumed=0;result=s->device->update(s->device,handle,&empty,&input,&consumed,NULL,&temporary);sd_softkm_clear_blob(s,&temporary);if(result!=KM_ERROR_OK||consumed>length){s->device->abort(s->device,handle);return result==KM_ERROR_OK?KM_ERROR_UNKNOWN_ERROR:result;}input.data+=consumed;input.data_length-=consumed;return s->device->finish(s->device,handle,&empty,&input,signature,NULL,output);
}
