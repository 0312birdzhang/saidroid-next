/* Diagnostic only: public host NDK codec, not a CTS executor or pass result.
 * Moving YUV scene follows AOSP CTS VideoEncoderDecoderTest (Apache-2.0).
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <time.h>
#include <unistd.h>
#ifdef SD_MEDIA_JNI
#include <jni.h>
#define TIMING_SCOPE "private-ndk-diagnostic"
#else
#define TIMING_SCOPE "host-ndk-diagnostic"
#endif

typedef struct {int32_t offset,size;int64_t pts;uint32_t flags;} BufferInfo;
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
static uint8_t yplane[520*440],uvplane[520*220];
static void fill(uint8_t *buffer,unsigned frame){
 double x=(1-sin(frame/7.))*.1+frame*.005;
 double y=(1-cos(frame/10.))+frame*.01;
 if(frame%32==0)x+=((frame%64)/32)+.3+y;
 if(frame%32==13)y+=((frame%64)/32)+.6+x;
 int xi=(int)(fmod(x,2)*200),yi=(int)(fmod(y,2)*200);
 if(xi>200)xi=400-xi;
 if(yi>200)yi=400-yi;
 for(int row=0;row<240;row++)memcpy(buffer+row*320,yplane+(yi+row)*520+xi,320);
 for(int row=0;row<120;row++)memcpy(buffer+320*240+row*320,uvplane+(yi/2+row)*520+(xi/2)*2,320);
}
#define API(type,name,args) type (*name)args=dlsym_api(library,#name);if(!name)return 3
static void *(*symbol)(void*,const char*);
static void *dlsym_api(void *library,const char *name){void *result=symbol(library,name);if(!result)fprintf(stderr,"MISSING_API=%s\n",name);return result;}
static int run_encode(void){
 if(!getuid()||prctl(PR_SET_NO_NEW_PRIVS,1,0,0,0))return 2;
 setvbuf(stdout,NULL,_IOLBF,0);
#ifdef SD_MEDIA_JNI
 symbol=dlsym;
 void *library=dlopen("libmediandk.so",RTLD_NOW);if(!library)return 2;
#else
 void *hybris=dlopen("/usr/lib64/libhybris-common.so.1",RTLD_NOW|RTLD_LOCAL);if(!hybris)return 2;
 void *(*open_android)(const char*,int)=dlsym(hybris,"android_dlopen");symbol=dlsym(hybris,"android_dlsym");
 if(!open_android||!symbol)return 2;
 void *library=open_android("/system/lib64/libmediandk.so",RTLD_NOW);if(!library)return 2;
#endif
 API(void*,AMediaCodec_createCodecByName,(const char*));
 API(void*,AMediaFormat_new,(void));API(void,AMediaFormat_delete,(void*));
 API(void,AMediaFormat_setInt32,(void*,const char*,int32_t));
 API(void,AMediaFormat_setString,(void*,const char*,const char*));
 API(int32_t,AMediaCodec_configure,(void*,void*,void*,void*,uint32_t));
 API(int32_t,AMediaCodec_start,(void*));API(int32_t,AMediaCodec_stop,(void*));
 API(int32_t,AMediaCodec_delete,(void*));
 API(ssize_t,AMediaCodec_dequeueInputBuffer,(void*,int64_t));
 API(uint8_t*,AMediaCodec_getInputBuffer,(void*,size_t,size_t*));
 API(int32_t,AMediaCodec_queueInputBuffer,(void*,size_t,off_t,size_t,uint64_t,uint32_t));
 API(ssize_t,AMediaCodec_dequeueOutputBuffer,(void*,BufferInfo*,int64_t));
 API(uint8_t*,AMediaCodec_getOutputBuffer,(void*,size_t,size_t*));
 API(int32_t,AMediaCodec_releaseOutputBuffer,(void*,size_t,_Bool));
 for(int row=0;row<440;row++)for(int col=0;col<520;col++){
  int v=(row+col)&255;if(v<16)v=16;if(v>235)v=235;yplane[row*520+col]=v;
 }
 for(int row=0;row<220;row++)for(int col=0;col<260;col++){
  uvplane[row*520+col*2]=row;uvplane[row*520+col*2+1]=col;
 }
 double begin=now();void *codec=AMediaCodec_createCodecByName("OMX.google.h264.encoder");if(!codec)return 4;
 printf("MEDIA_TIMING=create|milliseconds=%.3f\n",(now()-begin)*1000);
 void *format=AMediaFormat_new();if(!format){AMediaCodec_delete(codec);return 4;}
 AMediaFormat_setString(format,"mime","video/avc");
 AMediaFormat_setInt32(format,"width",320);AMediaFormat_setInt32(format,"height",240);
 AMediaFormat_setInt32(format,"color-format",21);AMediaFormat_setInt32(format,"bitrate",2296396);
 AMediaFormat_setInt32(format,"frame-rate",30);AMediaFormat_setInt32(format,"bitrate-mode",1);
 AMediaFormat_setInt32(format,"i-frame-interval",5);
 begin=now();int32_t status=AMediaCodec_configure(codec,format,NULL,NULL,1);AMediaFormat_delete(format);
 printf("MEDIA_TIMING=configure|status=%d|milliseconds=%.3f\n",status,(now()-begin)*1000);
 if(status){AMediaCodec_delete(codec);return 5;}
 begin=now();status=AMediaCodec_start(codec);printf("MEDIA_TIMING=start|status=%d|milliseconds=%.3f\n",status,(now()-begin)*1000);
 if(status){AMediaCodec_delete(codec);return 5;}
 unsigned input=0,output=0;uint64_t bytes=0,hash=1469598103934665603ULL;
 double started=now(),copy_time=0,queue_time=0,release_time=0,input_wait=0,output_wait=0;int eos=0,error=0;
 while(now()-started<25){
  if(input<300){
   double wait_started=now();ssize_t index=AMediaCodec_dequeueInputBuffer(codec,1000);input_wait+=now()-wait_started;
   if(index>=0){
    size_t capacity=0;uint8_t *buffer=AMediaCodec_getInputBuffer(codec,index,&capacity);
    if(!buffer||capacity<320*240*3/2){error=6;break;}
    double t=now();fill(buffer,input);copy_time+=now()-t;t=now();
    status=AMediaCodec_queueInputBuffer(codec,index,0,320*240*3/2,132+input*1000000ULL/30,input==299?4:0);
    queue_time+=now()-t;if(status){error=7;break;}input++;
   }else if(index!=-1){error=8;break;}
  }
  BufferInfo info={0};double wait_started=now();ssize_t index=AMediaCodec_dequeueOutputBuffer(codec,&info,1000);output_wait+=now()-wait_started;
  if(index>=0){
   if(info.size>0){
    size_t capacity=0;uint8_t *buffer=AMediaCodec_getOutputBuffer(codec,index,&capacity);
    if(!buffer||info.offset<0||info.size<0||(size_t)info.offset>capacity||(size_t)info.size>capacity-info.offset){error=9;break;}
    bytes+=info.size;
    for(int i=0;i<info.size&&i<64;i++){hash^=buffer[info.offset+i];hash*=1099511628211ULL;}
   }
   if(!(info.flags&2))output++;
   double t=now();status=AMediaCodec_releaseOutputBuffer(codec,index,0);release_time+=now()-t;
   if(status){error=10;break;}
   if(info.flags&4){eos=1;break;}
  }else if(index<-3){error=11;break;}
 }
 double elapsed=now()-started;status=AMediaCodec_stop(codec);AMediaCodec_delete(codec);
 printf("MEDIA_TIMING=result|scope=" TIMING_SCOPE "|input=%u|output=%u|eos=%d|bytes=%llu|hash=%llx|seconds=%.6f|fps=%.3f|copy_ms=%.3f|queue_ms=%.3f|release_ms=%.3f|input_wait_ms=%.3f|output_wait_ms=%.3f|stop_status=%d|error=%d\n",input,output,eos,(unsigned long long)bytes,(unsigned long long)hash,elapsed,output/elapsed,copy_time*1000,queue_time*1000,release_time*1000,input_wait*1000,output_wait*1000,status,error);
 return error?error:(!eos||input!=300||output<299||!bytes||status?12:0);
}
#ifdef SD_MEDIA_JNI
JNIEXPORT jint JNICALL Java_org_example_saildroid_mediatiming_MediaTimingInstrumentation_runNative(JNIEnv *env,jclass type){
 (void)env;(void)type;return run_encode();
}
#else
int main(void){return run_encode();}
#endif
