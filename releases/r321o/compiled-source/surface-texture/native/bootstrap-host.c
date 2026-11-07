#define _GNU_SOURCE
#include <jni.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <pthread.h>

extern void sd_texture_set_allocator(void*);
extern int sd_texture_allocate(unsigned,unsigned,int,unsigned,uint64_t,const void**,unsigned*);
extern int sd_texture_owns_handle(const void*);
static void* (*android_open)(const char*,int);
static void* (*android_symbol)(void*,const char*);
static const void* (*buffer_handle)(void*);
static void* (*client_buffer)(void*);
static void (*hardware_release)(JNIEnv*,jclass,jlong);
static int (*hardware_id)(void*);
static void (*real_release)(JNIEnv*,jclass,jlong);
static JNINativeMethod surface_methods[128],egl_methods[128];
static int surface_count,egl_count;
static JNINativeMethod* capture_target;
static int* capture_count;
static jint capture_natives(JNIEnv*env,jclass type,const JNINativeMethod*methods,jint count) {
    (void)env;(void)type;
    if(count<0||count>128)return JNI_ERR;
    memcpy(capture_target,methods,sizeof(*methods)*count);*capture_count=count;return JNI_OK;
}
static int capture(JNIEnv*env,int(*reg)(JNIEnv*),JNINativeMethod*target,int*count) {
    /* Keep the real JNIEnvExt/thread. Only its per-env dispatch pointer changes
     * temporarily while this same thread calls the upstream registrar. */
    const struct JNINativeInterface_* original=*env;
    struct JNINativeInterface_ table=*original;
    table.RegisterNatives=capture_natives;
    capture_target=target;capture_count=count;
    *(const struct JNINativeInterface_**)env=&table;
    int result=reg(env);
    *(const struct JNINativeInterface_**)env=original;
    capture_target=NULL;capture_count=NULL;
    return result;
}
static void mixed_release(JNIEnv*env,jclass type,jlong pointer) {
    /* The helper can distinguish its local HostProducer window from a real
     * BufferQueue Surface. Each is released by its original reference owner. */
    if(pointer&&hardware_id((void*)(intptr_t)pointer)>0)hardware_release(env,type,pointer);
    else real_release(env,type,pointer);
}
static int installed;
JNIEXPORT void JNICALL Java_SdTexture_nativeInstall(JNIEnv*env,jclass type) {
    (void)type;if(installed)return;
    const char*root=getenv("ANDROID_ROOT");char path[1024];
    void*linker=dlopen("libdl_bio.so.0",RTLD_NOW|RTLD_GLOBAL);
    android_open=linker?dlsym(linker,"bionic_dlopen"):NULL;
    android_symbol=linker?dlsym(linker,"bionic_dlsym"):NULL;
    if(!root||!android_open||!android_symbol)goto failed;
    snprintf(path,sizeof(path),"%s/android-libs/libsdtexture-android.so",root);
    void*helper=android_open(path,RTLD_NOW);if(!helper)goto failed;
    void(*set_host)(void*)=android_symbol(helper,"sd_texture_set_host_allocator");
    void*allocate=android_symbol(helper,"sd_texture_android_allocate");
    buffer_handle=android_symbol(helper,"sd_texture_buffer_handle");
    client_buffer=android_symbol(helper,"sd_texture_client_buffer");
    if(!set_host||!allocate||!buffer_handle||!client_buffer)goto failed;
    set_host(sd_texture_allocate);sd_texture_set_allocator(allocate);
    snprintf(path,sizeof(path),"%s/android-libs/libandroid_runtime.so",root);
    void*runtime=android_open(path,RTLD_NOW);if(!runtime)goto failed;
    int(*texture)(JNIEnv*)=android_symbol(runtime,"_ZN7android40register_android_graphics_SurfaceTextureEP7_JNIEnv");
    int(*layer)(JNIEnv*)=android_symbol(runtime,"_ZN7android34register_android_view_TextureLayerEP7_JNIEnv");
    int(*view)(JNIEnv*)=android_symbol(runtime,"_ZN7android33register_android_view_TextureViewEP7_JNIEnv");
    int(*surface)(JNIEnv*)=android_symbol(runtime,"_ZN7android29register_android_view_SurfaceEP7_JNIEnv");
    int(*egl)(JNIEnv*)=android_symbol(runtime,"_Z33register_android_opengl_jni_EGL14P7_JNIEnv");
    if(!texture||!view||!layer||!surface||!egl)goto failed;
    if(layer(env)<0||(*env)->ExceptionCheck(env)||texture(env)<0||(*env)->ExceptionCheck(env)||view(env)<0||(*env)->ExceptionCheck(env))goto failed;
    if(capture(env,surface,surface_methods,&surface_count)<0||(*env)->ExceptionCheck(env))goto failed;
    if(capture(env,egl,egl_methods,&egl_count)<0||(*env)->ExceptionCheck(env))goto failed;
    hardware_id=android_symbol(helper,"sd_texture_surface_window_id");
    snprintf(path,sizeof(path),"%s/lib/libsdwindow.so",root);
    void*window=dlopen(path,RTLD_NOW|RTLD_LOCAL);hardware_release=window?dlsym(window,"Java_SdWindowHost_nativeHardwareRelease"):NULL;
    if(!hardware_id||!hardware_release)goto failed;
    const char*names[]={"nativeCreateFromSurfaceTexture","nativeLockCanvas","nativeUnlockCanvasAndPost","nativeIsValid","nativeRelease","nativeGetWidth","nativeGetHeight","nativeIsConsumerRunningBehind","nativeAllocateBuffers",NULL};
    jclass surface_class=(*env)->FindClass(env,"android/view/Surface");int restored=0;
    for(int i=0;i<surface_count;i++)for(int j=0;names[j];j++)if(!strcmp(surface_methods[i].name,names[j])) {
        JNINativeMethod method=surface_methods[i];
        if(!strcmp(method.name,"nativeRelease")){real_release=method.fnPtr;method.fnPtr=mixed_release;}
        if((*env)->RegisterNatives(env,surface_class,&method,1)<0)goto failed;
        restored++;
    }
    if(!real_release||restored!=9)goto failed;
    jclass egl_class=(*env)->FindClass(env,"android/opengl/EGL14");int windows=0;
    for(int i=0;i<egl_count;i++)if(!strcmp(egl_methods[i].name,"_eglCreateWindowSurface")||!strcmp(egl_methods[i].name,"_eglCreateWindowSurfaceTexture")) {
        if((*env)->RegisterNatives(env,egl_class,&egl_methods[i],1)<0)goto failed;
        windows++;
    }
    if(windows!=2)goto failed;
    installed=1;fprintf(stderr,"SDTEXTURE=installed|SurfaceTexture=upstream-api29|TextureView=upstream-api29|TextureLayer=upstream-api29|Surface=mixed-owner|EGL=real-bufferqueue\n");return;
failed:
    if(!(*env)->ExceptionCheck(env))(*env)->ThrowNew(env,(*env)->FindClass(env,"java/lang/IllegalStateException"),"SurfaceTexture native backend installation failed");
}

/* Called from the process-private EGL shim for real BufferQueue surfaces.
 * Bypass Wayland's wl_egl_window converter, use the same vendor EGL display
 * and actual native ANativeWindow. No compositor window/mapping is created. */
static _Thread_local int native_error;
int sd_texture_egl_take_error(void){int error=native_error;native_error=0;return error;}
void* sd_texture_egl_create_window(void*display,void*config,void*window,const int*attributes) {
    /* Use the exact Android EGL handle already selected by libhybris, including
     * its device-specific LIBEGL selection, rather than opening a second EGL. */
    void*library=dlopen("libEGL.so.1",RTLD_NOW|RTLD_LOCAL);
    struct Interface {void*(*symbol)(const char*);};
    struct Interface*interface=library?dlsym(library,"hybris_egl_interface"):NULL;
    void*(*create)(void*,void*,void*,const int*)=interface&&interface->symbol?interface->symbol("eglCreateWindowSurface"):NULL;
    int(*error)(void)=interface&&interface->symbol?interface->symbol("eglGetError"):NULL;
    if(!create||!window){native_error=0x300b;return NULL;}
    void*result=create(display,config,window,attributes);
    if(!result)native_error=error?error():0x300b;
    fprintf(stderr,"SDTEXTURE=producer_egl_surface|result=%p|window=%p|queue=android-bufferqueue|error=0x%x|lookup=hybris-current-egl\n",result,window,native_error);
    return result;
}
int sd_texture_native_image(void*buffer) {return buffer_handle&&sd_texture_owns_handle(buffer_handle(buffer));}

void* sd_texture_native_client_buffer(void*hardware_buffer){
    void*native=client_buffer?client_buffer(hardware_buffer):NULL;
    if(!native||!sd_texture_owns_handle(buffer_handle(native)))return NULL;
    fprintf(stderr,"SDTEXTURE=native_client_buffer|ownership=component-gralloc\n");
    return native;
}
