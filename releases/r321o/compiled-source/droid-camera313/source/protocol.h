#pragma once
#include <cstdint>
namespace sd_camera {
constexpr uint32_t magic=0x53444331;
constexpr uint32_t response=0x40000000;
constexpr uint32_t event=0x80000000;
constexpr uint32_t max_payload=32*1024*1024;
enum Command:uint32_t {COUNT=1,INFO,OPEN,PARAMETERS,SET_PARAMETERS,START,STOP,FOCUS,CANCEL_FOCUS,TAKE,DISPLAY,LOCK,UNLOCK,RECONNECT,FACE,ZOOM,SHUTTER_SOUND,FOCUS_MOVE,CLOSE};
// Camera events retain the API29 CAMERA_MSG_* bit values.
struct Header {uint32_t magic=sd_camera::magic,size=0,type=0,sequence=0;int32_t a=0,b=0,c=0;};
}
