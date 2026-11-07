#pragma once
/* VM-only native backend boundary, not an Android KeyStore API. */
#include <stdbool.h>
#include <hardware/keymaster2.h>
#ifdef __cplusplus
extern "C" {
#endif
struct sd_softkm;
struct sd_softkm* sd_softkm_open(const char* abi_query,const char* linker,const char* original_library);
void sd_softkm_close(struct sd_softkm*);
int sd_softkm_generate(struct sd_softkm*,uint32_t algorithm,keymaster_key_blob_t* key);
int sd_softkm_operation(struct sd_softkm*,uint32_t algorithm,keymaster_purpose_t purpose,const keymaster_key_blob_t* key,const uint8_t* message,size_t message_length,const keymaster_blob_t* signature,keymaster_blob_t* output);
void sd_softkm_clear_key(struct sd_softkm*,keymaster_key_blob_t*);
void sd_softkm_clear_blob(struct sd_softkm*,keymaster_blob_t*);
#ifdef __cplusplus
}
#endif
