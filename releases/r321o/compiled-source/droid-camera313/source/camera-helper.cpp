// Physical Android camera access stays in a clean helper process, separate from ART's bionic loader.
#include "protocol.h"
#include "headers/droidmediacamera.h"
#include <dlfcn.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <atomic>
#include <string>
#include <vector>
using namespace sd_camera;
#define API_LIST(X) \
 X(droid_media_init) X(droid_media_camera_get_number_of_cameras) X(droid_media_camera_get_info) \
 X(droid_media_camera_connect) X(droid_media_camera_disconnect) X(droid_media_camera_get_parameters) \
 X(droid_media_camera_set_parameters) X(droid_media_camera_set_callbacks) X(droid_media_camera_start_preview) \
 X(droid_media_camera_stop_preview) X(droid_media_camera_set_preview_callback_flags) \
 X(droid_media_camera_start_auto_focus) X(droid_media_camera_cancel_auto_focus) X(droid_media_camera_take_picture) \
 X(droid_media_camera_send_command) X(droid_media_camera_lock) X(droid_media_camera_unlock) \
 X(droid_media_camera_reconnect) X(droid_media_camera_enable_face_detection)
#define DECLARE(name) static decltype(&name) name##_fn;
API_LIST(DECLARE)
#undef DECLARE
static int channel=3;
static std::mutex output_mutex;
static std::atomic<bool> running{true};
static DroidMediaCamera* camera;
static std::atomic<int> width{0},height{0},format{17};
static bool read_all(void*memory,size_t size){char*p=(char*)memory;while(size){ssize_t n=read(channel,p,size);if(n<0&&errno==EINTR)continue;if(n<=0)return false;p+=n;size-=n;}return true;}
static bool write_all(const void*memory,size_t size){const char*p=(const char*)memory;while(size){ssize_t n=send(channel,p,size,MSG_NOSIGNAL);if(n<0&&errno==EINTR)continue;if(n<=0){running=false;return false;}p+=n;size-=n;}return true;}
static bool send(Header h,const void*bytes=nullptr){std::lock_guard<std::mutex>guard(output_mutex);if(!running)return false;return write_all(&h,sizeof(h))&&(!h.size||write_all(bytes,h.size));}
static void notify(int type,int a=0,int b=0){Header h;h.type=event|type;h.a=a;h.b=b;send(h);}
static void shutter(void*){notify(2);}
static void focus(void*,int value){notify(4,value);}
static void focus_move(void*,int value){notify(0x800,value);}
static void error(void*,int value){notify(1,value);}
static void zoom(void*,int value,int stopped){notify(8,value,stopped);}
static void bytes(int type,DroidMediaData*data){if(!data||data->size<0||data->size>max_payload)return;Header h;h.type=event|type;h.size=data->size;send(h,data->data);}
static void jpeg(void*,DroidMediaData*data){bytes(0x100,data);}
static void raw(void*,DroidMediaData*data){bytes(0x80,data);}
static void postview(void*,DroidMediaData*data){bytes(0x40,data);}
static void raw_notify(void*){notify(0x200);}
static void faces(void*,const DroidMediaCameraFace*data,size_t count){if(!data||count>100)return;Header h;h.type=event|0x400;h.size=count*sizeof(DroidMediaCameraFace);send(h,data);}
static void preview(void*,DroidMediaData*data){
 if(!data||data->size<=0||data->size>max_payload)return;
 // Drop a preview frame if a control reply or JPEG currently owns the socket.
 std::unique_lock<std::mutex>guard(output_mutex,std::try_to_lock);if(!guard.owns_lock()||!running)return;
 Header h;h.type=event|0x10;h.size=data->size;h.a=width;h.b=height;h.c=format;
 write_all(&h,sizeof(h));if(running)write_all(data->data,data->size);
}
static void update_size(const std::string&parameters){
 auto i=parameters.find("preview-size=");if(i!=std::string::npos){int w=0,h=0;if(sscanf(parameters.c_str()+i+13,"%dx%d",&w,&h)==2&&w>0&&h>0&&w<=8192&&h<=8192){width=w;height=h;}}
 i=parameters.find("preview-format=");if(i!=std::string::npos){auto end=parameters.find(';',i);auto value=parameters.substr(i+15,end==std::string::npos?end:end-i-15);format=value=="yuv420sp"?17:value=="yuv420p"?0x32315659:value=="yuv422i-yuyv"?20:0;}
}
static bool load_api(){
 void*lib=dlopen("libgstdroid-1.0.so.0",RTLD_NOW|RTLD_LOCAL);if(!lib){fprintf(stderr,"SDCAMERA_HELPER=unavailable|reason=%s\n",dlerror());return false;}
#define LOAD(name) name##_fn=(decltype(name##_fn))dlsym(lib,#name);if(!name##_fn){fprintf(stderr,"SDCAMERA_HELPER=unavailable|symbol=%s\n",#name);return false;}
 API_LIST(LOAD)
#undef LOAD
 return droid_media_init_fn();
}
static void close_camera(){if(camera){droid_media_camera_stop_preview_fn(camera);DroidMediaCameraCallbacks empty{};droid_media_camera_set_callbacks_fn(camera,&empty,nullptr);droid_media_camera_disconnect_fn(camera);camera=nullptr;}}
int main(int argc,char**argv){
 if(argc==3&&!strcmp(argv[1],"--fd")){channel=atoi(argv[2]);if(channel<3||channel>4096)return 64;}
 if(!load_api())return 2;
 if(argc==2&&!strcmp(argv[1],"--metadata")){
  int count=droid_media_camera_get_number_of_cameras_fn();printf("SDCAMERA_METADATA %d\n",count);
  for(int i=0;i<count;i++){DroidMediaCameraInfo info{};if(!droid_media_camera_get_info_fn(&info,i))return 3;printf("%d %d %d\n",i,info.facing,info.orientation);}return 0;
 }
 timeval timeout{2,0};setsockopt(channel,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
 fprintf(stderr,"SDCAMERA_HELPER=ready|pid=%d|backend=droidmedia\n",getpid());
 DroidMediaCameraCallbacks callbacks{};callbacks.shutter_cb=shutter;callbacks.focus_cb=focus;callbacks.focus_move_cb=focus_move;callbacks.error_cb=error;callbacks.zoom_cb=zoom;callbacks.raw_image_cb=raw;callbacks.compressed_image_cb=jpeg;callbacks.postview_frame_cb=postview;callbacks.raw_image_notify_cb=raw_notify;callbacks.preview_frame_cb=preview;callbacks.preview_metadata_cb=faces;
 Header command;
 while(running&&read_all(&command,sizeof(command))){
  if(command.magic!=magic||command.size>max_payload||command.type& (event|response))break;
  std::vector<char>payload(command.size+1);if(command.size&&!read_all(payload.data(),command.size))break;payload[command.size]=0;
  Header result;result.type=response|command.type;result.sequence=command.sequence;result.a=0;std::string text;
  if(command.type==COUNT)result.b=droid_media_camera_get_number_of_cameras_fn();
  else if(command.type==INFO){DroidMediaCameraInfo info{};result.a=droid_media_camera_get_info_fn(&info,command.a)?0:-1;result.b=info.facing;result.c=info.orientation;}
  else if(command.type==OPEN){if(camera)result.a=-1;else{camera=droid_media_camera_connect_fn(command.a);result.a=camera?0:-1;if(camera){droid_media_camera_set_callbacks_fn(camera,&callbacks,nullptr);char*p=droid_media_camera_get_parameters_fn(camera);if(p){update_size(p);free(p);}}}}
  else if(command.type==CLOSE){close_camera();}
  else if(!camera)result.a=-1;
  else switch(command.type){
   case PARAMETERS:{char*p=droid_media_camera_get_parameters_fn(camera);if(p){text=p;free(p);update_size(text);}else result.a=-1;break;}
   case SET_PARAMETERS:result.a=droid_media_camera_set_parameters_fn(camera,payload.data())?0:-1;if(!result.a)update_size(payload.data());break;
   case START:droid_media_camera_set_preview_callback_flags_fn(camera,5);result.a=droid_media_camera_start_preview_fn(camera)?0:-1;break;
   case STOP:droid_media_camera_stop_preview_fn(camera);break;
   case FOCUS:result.a=droid_media_camera_start_auto_focus_fn(camera)?0:-1;break;
   case CANCEL_FOCUS:result.a=droid_media_camera_cancel_auto_focus_fn(camera)?0:-1;break;
   case TAKE:result.a=droid_media_camera_take_picture_fn(camera,command.a)?0:-1;break;
   case DISPLAY:result.a=droid_media_camera_send_command_fn(camera,3,command.a,0)?0:-1;break;
   case LOCK:result.a=droid_media_camera_lock_fn(camera)?0:-1;break;
   case UNLOCK:result.a=droid_media_camera_unlock_fn(camera)?0:-1;break;
   case RECONNECT:result.a=droid_media_camera_reconnect_fn(camera)?0:-1;break;
   case FACE:result.a=droid_media_camera_enable_face_detection_fn(camera,(DroidMediaCameraFaceDetectionType)command.a,command.b!=0)?0:-1;break;
   case ZOOM:result.a=droid_media_camera_send_command_fn(camera,command.b?2:1,command.a,0)?0:-1;break;
   case SHUTTER_SOUND:result.a=droid_media_camera_send_command_fn(camera,8,command.a,0)?0:-1;break;
   case FOCUS_MOVE:result.a=droid_media_camera_send_command_fn(camera,11,command.a,0)?0:-1;break;
   default:result.a=-1;
  }
  result.size=text.size();if(!send(result,text.data()))break;
  if(command.type==CLOSE)break;
 }
 close_camera();fprintf(stderr,"SDCAMERA_HELPER=closed|pid=%d\n",getpid());return 0;
}
