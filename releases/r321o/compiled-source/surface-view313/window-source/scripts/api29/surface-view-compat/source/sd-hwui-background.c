#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <png.h>

typedef void *Display;typedef void *Config;typedef void *Context;typedef void *Surface;
static Display display;static Surface surface;static Context context;static void *egl,*gles;
/* The persistent parent is mapped only when an actual Android GPU frame is
 * queued. An empty parent must not replace the shell's launch Cover with black
 * while Application.onCreate or DEX loading is still running. */
int sd_hwui_background_create(void *native_display,void *native_window) {
    egl=dlopen("libEGL.so.1",RTLD_NOW|RTLD_LOCAL);gles=dlopen("libGLESv2.so.2",RTLD_NOW|RTLD_LOCAL);
    if(!egl||!gles)return -1;
#define EGL(name,result,args) result(*name)args=dlsym(egl,#name);if(!name)return -1
    EGL(eglGetDisplay,Display,(void*));EGL(eglInitialize,unsigned,(Display,int*,int*));
    EGL(eglChooseConfig,unsigned,(Display,const int*,Config*,int,int*));
    EGL(eglBindAPI,unsigned,(unsigned));EGL(eglCreateContext,Context,(Display,Config,Context,const int*));
    EGL(eglCreateWindowSurface,Surface,(Display,Config,void*,const int*));
#undef EGL
    /* The Android EGL bridge serializes libhybris' process-wide window map.
     * Resolve its raw native-window path for this owned parent as well. */
    eglGetDisplay=dlsym(RTLD_DEFAULT,"bionic_eglGetDisplay");
    eglInitialize=dlsym(RTLD_DEFAULT,"bionic_eglInitialize");
    eglCreateWindowSurface=dlsym(RTLD_DEFAULT,"sd_egl_host_create_window");
    if(!eglGetDisplay||!eglInitialize||!eglCreateWindowSurface)return -1;
    display=eglGetDisplay(native_display);int major,minor,count=0;Config config=NULL;
    int attributes[]={0x3033,4,0x3040,4,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3038};
    int context_attributes[]={0x3098,2,0x3038};
    if(!display||!eglInitialize(display,&major,&minor)||!eglBindAPI(0x30a0)||
       !eglChooseConfig(display,attributes,&config,1,&count)||count!=1)return -1;
    context=eglCreateContext(display,config,NULL,context_attributes);
    surface=eglCreateWindowSurface(display,config,native_window,NULL);
    fprintf(stderr,"SDHWUI=host_background_prepared|deferred_until_app_frame=true\n");
    return context&&surface?0:-1;
}
int sd_hwui_background_present(void) {
    if(!context||!surface)return -1;
    unsigned(*make)(Display,Surface,Surface,Context)=dlsym(egl,"eglMakeCurrent");
    unsigned(*swap)(Display,Surface)=dlsym(RTLD_DEFAULT,"sd_egl_host_swap");
    void(*color)(float,float,float,float)=dlsym(gles,"glClearColor");void(*clear)(unsigned)=dlsym(gles,"glClear");
    void(*finish)(void)=dlsym(gles,"glFinish");
    if(!make||!swap||!color||!clear||!finish||!make(display,surface,surface,context))return -1;
    color(16.f/255,24.f/255,32.f/255,1);clear(0x4000);finish();
    int success=swap(display,surface);make(display,NULL,NULL,NULL);
    fprintf(stderr,"SDHWUI=host_background|success=%d|cpu_readback=0\n",success);
    return success?0:-1;
}
void sd_hwui_background_destroy(void) {
    if(egl&&surface){unsigned(*destroy)(Display,Surface)=dlsym(RTLD_DEFAULT,"bionic_eglDestroySurface");if(destroy)destroy(display,surface);surface=NULL;}
    if(egl&&context){unsigned(*destroy)(Display,Context)=dlsym(egl,"eglDestroyContext");if(destroy)destroy(display,context);context=NULL;}
}

/* Honest native startup surface: application's installed icon, before ART. */
int sd_hwui_background_startup(const char *path,int width,int height) {
 unsigned(*make)(Display,Surface,Surface,Context)=dlsym(egl,"eglMakeCurrent");
 unsigned(*swap)(Display,Surface)=dlsym(RTLD_DEFAULT,"sd_egl_host_swap");
 if(!make||!swap||!make(display,surface,surface,context))return -1;
#define GL(name,result,args) result(*name)args=dlsym(gles,#name);if(!name)return -1
 GL(glClearColor,void,(float,float,float,float));GL(glClear,void,(unsigned));
 GL(glCreateShader,unsigned,(unsigned));GL(glShaderSource,void,(unsigned,int,const char**,const int*));
 GL(glCompileShader,void,(unsigned));GL(glCreateProgram,unsigned,(void));
 GL(glAttachShader,void,(unsigned,unsigned));GL(glLinkProgram,void,(unsigned));
 GL(glUseProgram,void,(unsigned));GL(glGetAttribLocation,int,(unsigned,const char*));
 GL(glVertexAttribPointer,void,(unsigned,int,unsigned,unsigned,int,const void*));
 GL(glEnableVertexAttribArray,void,(unsigned));GL(glDrawArrays,void,(unsigned,int,int));
 GL(glGenTextures,void,(int,unsigned*));GL(glBindTexture,void,(unsigned,unsigned));
 GL(glTexParameteri,void,(unsigned,unsigned,int));GL(glTexImage2D,void,(unsigned,int,int,int,int,int,unsigned,unsigned,const void*));
 GL(glViewport,void,(int,int,int,int));GL(glDeleteTextures,void,(int,const unsigned*));
 GL(glDeleteProgram,void,(unsigned));GL(glDeleteShader,void,(unsigned));
 GL(glEnable,void,(unsigned));GL(glBlendFunc,void,(unsigned,unsigned));GL(glDisable,void,(unsigned));
#undef GL
 glViewport(0,0,width,height);glClearColor(16.f/255,24.f/255,32.f/255,1);glClear(0x4000);
 png_image image={0};image.version=PNG_IMAGE_VERSION;
 int icon=path&&png_image_begin_read_from_file(&image,path);
 if(icon){
  image.format=PNG_FORMAT_RGBA;
  if(image.width>2048||image.height>2048){png_image_free(&image);make(display,NULL,NULL,NULL);return -1;}
  void *pixels=malloc(PNG_IMAGE_SIZE(image));
  icon=pixels&&png_image_finish_read(&image,NULL,pixels,0,NULL);
  if(icon){
   const char *vs="attribute vec2 a;attribute vec2 t;varying vec2 uv;void main(){uv=t;gl_Position=vec4(a,0.,1.);}";
   const char *fs="precision mediump float;varying vec2 uv;uniform sampler2D icon;void main(){gl_FragColor=texture2D(icon,uv);}";
   unsigned v=glCreateShader(0x8B31),f=glCreateShader(0x8B30);glShaderSource(v,1,&vs,NULL);glCompileShader(v);glShaderSource(f,1,&fs,NULL);glCompileShader(f);
   unsigned program=glCreateProgram();glAttachShader(program,v);glAttachShader(program,f);glLinkProgram(program);glUseProgram(program);
   unsigned texture;glGenTextures(1,&texture);glBindTexture(0x0DE1,texture);glTexParameteri(0x0DE1,0x2801,0x2601);glTexParameteri(0x0DE1,0x2800,0x2601);glTexParameteri(0x0DE1,0x2802,0x812F);glTexParameteri(0x0DE1,0x2803,0x812F);
   glTexImage2D(0x0DE1,0,0x1908,image.width,image.height,0,0x1908,0x1401,pixels);
   float x=.18f,y=x*(float)width/height;float vertices[]={-x,-y,0,1,x,-y,1,1,-x,y,0,0,x,y,1,0};
   int a=glGetAttribLocation(program,"a"),t=glGetAttribLocation(program,"t");
   if(a>=0&&t>=0){glVertexAttribPointer(a,2,0x1406,0,4*sizeof(float),vertices);glEnableVertexAttribArray(a);glVertexAttribPointer(t,2,0x1406,0,4*sizeof(float),vertices+2);glEnableVertexAttribArray(t);glEnable(0x0BE2);glBlendFunc(0x0302,0x0303);glDrawArrays(0x0005,0,4);glDisable(0x0BE2);}
   glDeleteTextures(1,&texture);glDeleteProgram(program);glDeleteShader(v);glDeleteShader(f);
  }
  free(pixels);png_image_free(&image);
 }
 int success=swap(display,surface);make(display,NULL,NULL,NULL);
 fprintf(stderr,"SDHOST=startup_gpu|icon=%d|success=%d|cpu_readback=0\n",icon,success);
 return success?0:-1;
}
