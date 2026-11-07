#include <jni.h>
#include <stdio.h>

/* No Android camera capture backend is installed in this component. Its
 * exposed-camera registry is empty, matching PackageManager's absent camera
 * features. This says nothing about physical Sailfish cameras. */
static jint count(JNIEnv *env, jclass type) {
    (void)env; (void)type;
    fprintf(stderr,"SDCAMERA=enumerate|exposed=0|backend=unavailable|host_camera_count=not-queried\n");
    return 0;
}
static void info(JNIEnv *env,jclass type,jint id,jobject output) {
    (void)type;(void)id;(void)output;
    (*env)->ThrowNew(env,(*env)->FindClass(env,"java/lang/RuntimeException"),"Android camera ID unavailable: capture backend not connected");
}
static jint setup(JNIEnv *env,jobject camera,jobject reference,jint id,jint version,jstring package) {
    (void)camera;(void)reference;(void)id;(void)version;(void)package;
    fprintf(stderr,"SDCAMERA=open_rejected|reason=capture-backend-unavailable\n");
    (*env)->ThrowNew(env,(*env)->FindClass(env,"java/lang/RuntimeException"),"Android camera capture backend is unavailable");
    return -1;
}
static void release(JNIEnv *env,jobject camera) {
    jclass type=(*env)->GetObjectClass(env,camera);
    jfieldID context=(*env)->GetFieldID(env,type,"mNativeContext","J");
    if(context&&(*env)->GetLongField(env,camera,context))
        (*env)->ThrowNew(env,(*env)->FindClass(env,"java/lang/IllegalStateException"),"Unexpected Android camera context without capture backend");
    (*env)->DeleteLocalRef(env,type);
}
int sd_camera_capability_install(JNIEnv *env) {
    jclass type=(*env)->FindClass(env,"android/hardware/Camera");
    if(!type)return -1;
    JNINativeMethod methods[]={
        {"getNumberOfCameras","()I",count},
        {"_getCameraInfo","(ILandroid/hardware/Camera$CameraInfo;)V",info},
        {"native_setup","(Ljava/lang/Object;IILjava/lang/String;)I",setup},
        {"native_release","()V",release}
    };
    int result=(*env)->RegisterNatives(env,type,methods,4);
    (*env)->DeleteLocalRef(env,type);
    return result;
}
