#define _GNU_SOURCE
#include <jni.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pthread.h>

/* The Android helper is loaded by the Android linker; this side remains a
 * glibc Wayland client. Only C functions and opaque pointers cross the ABI. */
extern void *sd_window_gpu_display(void);
extern void *sd_window_gpu_window(int id);
extern void sd_window_gpu_presented(void);
extern void sd_window_gpu_layout(int id,int x,int y,int width,int height,int visible);
static void *(*new_surface)(int,int,int);
static void (*delete_surface)(void *),(*retain_surface)(void *);
static void (*resize_surface)(void *,int,int);
static int (*identify_window)(void *);
struct owned_surface {void *pointer;int id,width,height,references;struct owned_surface *next;};
static struct owned_surface *owned;
static pthread_mutex_t owned_lock=PTHREAD_MUTEX_INITIALIZER;
static struct owned_surface *find_surface(jlong pointer) {
    for(struct owned_surface *s=owned;s;s=s->next)if(s->pointer==(void*)(intptr_t)pointer)return s;
    return NULL;
}
static jboolean surface_valid(JNIEnv *env,jclass type,jlong pointer) {
    (void)env;(void)type;pthread_mutex_lock(&owned_lock);
    int found=find_surface(pointer)!=NULL;
    pthread_mutex_unlock(&owned_lock);return found?JNI_TRUE:JNI_FALSE;
}
static jint surface_width(JNIEnv *env,jclass type,jlong pointer) {
    (void)env;(void)type;pthread_mutex_lock(&owned_lock);
    struct owned_surface *s=find_surface(pointer);int value=s?s->width:0;
    pthread_mutex_unlock(&owned_lock);return value;
}
static jint surface_height(JNIEnv *env,jclass type,jlong pointer) {
    (void)env;(void)type;pthread_mutex_lock(&owned_lock);
    struct owned_surface *s=find_surface(pointer);int value=s?s->height:0;
    pthread_mutex_unlock(&owned_lock);return value;
}
static jboolean surface_behind(JNIEnv *env,jclass type,jlong pointer) {
    (void)env;(void)type;(void)pointer;return JNI_FALSE;
}
static void surface_allocate(JNIEnv *env,jclass type,jlong pointer) {
    (void)env;(void)type;(void)pointer; /* EGL's gralloc queue allocates on demand. */
}
JNIEXPORT void JNICALL Java_SdWindowHost_nativeHardwareRelease(JNIEnv *env,jclass type,jlong pointer);
static int initialize(JNIEnv *env) {
    if(new_surface)return 1;
    void *linker=dlopen("libdl_bio.so.0",RTLD_NOW|RTLD_GLOBAL);
    void *(*open_android)(const char*,int)=linker?dlsym(linker,"bionic_dlopen"):NULL;
    void *(*symbol_android)(void*,const char*)=linker?dlsym(linker,"bionic_dlsym"):NULL;
    char path[1024];
    const char *root=getenv("ANDROID_ROOT");
    if(!root||!open_android||!symbol_android)goto fail;
    snprintf(path,sizeof(path),"%s/android-libs/libsdhwui-native.so",root);
    void *helper=open_android(path,RTLD_NOW);
    if(!helper)goto fail;
    new_surface=symbol_android(helper,"sd_hwui_new_surface");
    delete_surface=symbol_android(helper,"sd_hwui_delete_surface");
    retain_surface=symbol_android(helper,"sd_hwui_retain_surface");
    resize_surface=symbol_android(helper,"sd_hwui_resize_surface");
    identify_window=symbol_android(helper,"sd_hwui_window_id");
    void (*register_host)(void*(*)(void),void*(*)(int),int(*)(void*),void(*)(void))=
        dlsym(RTLD_DEFAULT,"sd_hwui_register_host");
    if(!new_surface||!delete_surface||!retain_surface||!resize_surface||!identify_window||!register_host)goto fail;
    register_host(sd_window_gpu_display,sd_window_gpu_window,identify_window,sd_window_gpu_presented);
    JNINativeMethod methods[]={
        {"nativeIsValid","(J)Z",surface_valid},
        {"nativeRelease","(J)V",Java_SdWindowHost_nativeHardwareRelease},
        {"nativeGetWidth","(J)I",surface_width},{"nativeGetHeight","(J)I",surface_height},
        {"nativeIsConsumerRunningBehind","(J)Z",surface_behind},
        {"nativeAllocateBuffers","(J)V",surface_allocate}};
    if((*env)->RegisterNatives(env,(*env)->FindClass(env,"android/view/Surface"),methods,sizeof(methods)/sizeof(methods[0]))<0)goto fail;
    return 1;
fail:
    new_surface=NULL;
    (*env)->ThrowNew(env,(*env)->FindClass(env,"java/lang/IllegalStateException"),
        "API29 HWUI native-window helper could not be initialized");
    return 0;
}
JNIEXPORT void JNICALL Java_SdWindowHost_nativeHardwareInitialize(JNIEnv *env,jclass type) {
    (void)type;initialize(env);
}
JNIEXPORT jlong JNICALL Java_SdWindowHost_nativeHardwareSurface(JNIEnv *env,jclass type,jint id,jint width,jint height) {
    (void)type;
    if(!initialize(env))return 0;
    void *pointer=new_surface(id,width,height);
    if(!pointer)return 0;
    struct owned_surface *entry=calloc(1,sizeof(*entry));
    if(!entry){delete_surface(pointer);return 0;}
    entry->pointer=pointer;entry->id=id;entry->width=width;entry->height=height;entry->references=1;
    pthread_mutex_lock(&owned_lock);entry->next=owned;owned=entry;pthread_mutex_unlock(&owned_lock);
    return (jlong)(intptr_t)pointer;
}
JNIEXPORT jlong JNICALL Java_SdWindowHost_nativeHardwareRetain(JNIEnv *env,jclass type,jlong pointer) {
    (void)type;pthread_mutex_lock(&owned_lock);
    struct owned_surface *entry=find_surface(pointer);
    if(entry){entry->references++;retain_surface(entry->pointer);}
    pthread_mutex_unlock(&owned_lock);
    if(!entry){(*env)->ThrowNew(env,(*env)->FindClass(env,"java/lang/IllegalStateException"),"GPU Surface reference is not owned");return 0;}
    return pointer;
}
JNIEXPORT void JNICALL Java_SdWindowHost_nativeHardwareRelease(JNIEnv *env,jclass type,jlong pointer) {
    (void)env;(void)type;if(!pointer)return;
    struct owned_surface *found=NULL;int remaining=0;pthread_mutex_lock(&owned_lock);
    struct owned_surface **p=&owned;
    while(*p){if((*p)->pointer==(void*)(intptr_t)pointer){found=*p;remaining=--found->references;if(!remaining)*p=found->next;break;}p=&(*p)->next;}
    pthread_mutex_unlock(&owned_lock);
    if(found){delete_surface(found->pointer);if(!remaining)free(found);}
}
JNIEXPORT void JNICALL Java_SdWindowHost_nativeHardwareLayout(JNIEnv *env,jclass type,jlong pointer,jint x,jint y,jint width,jint height,jboolean visible) {
    (void)env;(void)type;pthread_mutex_lock(&owned_lock);
    struct owned_surface *entry=find_surface(pointer);int id=0;
    if(entry){entry->width=width;entry->height=height;id=entry->id;resize_surface(entry->pointer,width,height);}
    pthread_mutex_unlock(&owned_lock);
    if(id)sd_window_gpu_layout(id,x,y,width,height,visible);
}

extern void sd_window_gpu_z(int id,int z);
JNIEXPORT void JNICALL Java_SdWindowHost_nativeHardwareZ(JNIEnv *env,jclass type,jlong pointer,jint z){
 (void)env;(void)type;pthread_mutex_lock(&owned_lock);struct owned_surface *entry=find_surface(pointer);int id=entry?entry->id:0;pthread_mutex_unlock(&owned_lock);if(id)sd_window_gpu_z(id,z);
}
