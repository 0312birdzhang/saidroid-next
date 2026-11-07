// API29 no-auth software subset. Based on the original AOSP KeymasterEnforcement
// purpose/date/nonce rules; full auth, hardware and lock-state are unsupported.
#pragma once
#include <hardware/keymaster_defs.h>
#include <time.h>
#include <limits>
namespace sd_keypolicy {
inline keymaster_error_t authorize(const keymaster_key_characteristics_t& chars,
        keymaster_purpose_t purpose,const keymaster_key_param_set_t& operation) {
 if(chars.hw_enforced.length)return KM_ERROR_INVALID_KEY_BLOB;
 uint32_t algorithm=0;unsigned algorithms=0;bool permitted=false,noauth=false,caller_nonce=false;
 for(size_t i=0;i<chars.sw_enforced.length;++i){const auto&p=chars.sw_enforced.params[i];
  if(p.tag==KM_TAG_ALGORITHM){algorithm=p.enumerated;++algorithms;}
  else if(p.tag==KM_TAG_PURPOSE&&p.enumerated==static_cast<uint32_t>(purpose))permitted=true;
  else if(p.tag==KM_TAG_NO_AUTH_REQUIRED)noauth=true;
  else if(p.tag==KM_TAG_CALLER_NONCE)caller_nonce=true;
 }
 if(algorithms!=1||!noauth)return KM_ERROR_INVALID_KEY_BLOB;
 // Like original API29, operations on asymmetric public keys need no private
 // key-use authorization. The native implementation still checks algorithm.
 if((algorithm==KM_ALGORITHM_RSA||algorithm==KM_ALGORITHM_EC)&&
    (purpose==KM_PURPOSE_ENCRYPT||purpose==KM_PURPOSE_VERIFY))return KM_ERROR_OK;
 if(purpose!=KM_PURPOSE_ENCRYPT&&purpose!=KM_PURPOSE_DECRYPT&&purpose!=KM_PURPOSE_SIGN&&purpose!=KM_PURPOSE_VERIFY)return KM_ERROR_UNSUPPORTED_PURPOSE;
 if(!permitted)return KM_ERROR_INCOMPATIBLE_PURPOSE;
 timespec now{};
 if(clock_gettime(CLOCK_REALTIME,&now)!=0||now.tv_sec<0||now.tv_nsec<0||now.tv_nsec>=1000000000||static_cast<uint64_t>(now.tv_sec)>(std::numeric_limits<uint64_t>::max()-999)/1000)return KM_ERROR_SECURE_HW_COMMUNICATION_FAILED;
 const uint64_t millis=static_cast<uint64_t>(now.tv_sec)*1000+static_cast<uint64_t>(now.tv_nsec)/1000000;
 const bool origination=purpose==KM_PURPOSE_ENCRYPT||purpose==KM_PURPOSE_SIGN;
 for(size_t i=0;i<chars.sw_enforced.length;++i){const auto&p=chars.sw_enforced.params[i];
  if(p.tag==KM_TAG_ACTIVE_DATETIME&&millis<p.date_time)return KM_ERROR_KEY_NOT_YET_VALID;
  if(((p.tag==KM_TAG_ORIGINATION_EXPIRE_DATETIME&&origination)||
      (p.tag==KM_TAG_USAGE_EXPIRE_DATETIME&&!origination))&&millis>p.date_time)return KM_ERROR_KEY_EXPIRED;
 }
 if(origination&&!caller_nonce)for(size_t i=0;i<operation.length;++i)if(operation.params[i].tag==KM_TAG_NONCE)return KM_ERROR_CALLER_NONCE_PROHIBITED;
 return KM_ERROR_OK;
}
}
