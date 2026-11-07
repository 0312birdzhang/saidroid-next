#include <jni.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
int sd_runtime_control_start(const char *,int(*)(void),int(*)(void),int(*)(const char *),int(*)(void));
void sd_runtime_control_stop(void);
static JavaVM *runtime_vm;
static jclass runtime_class;
static jmethodID close_method;
static jclass diagnostics;
static jmethodID dump_method;
static char *endpoint;
static int awake(void){return 1;}
static int dump_runtime(void){
    JNIEnv *env=NULL;if((*runtime_vm)->AttachCurrentThreadAsDaemon(runtime_vm,(void**)&env,NULL)!=JNI_OK)return 0;
    (*env)->CallStaticVoidMethod(env,diagnostics,dump_method);int success=!(*env)->ExceptionCheck(env);
    if(!success){(*env)->ExceptionDescribe(env);(*env)->ExceptionClear(env);}
    (*runtime_vm)->DetachCurrentThread(runtime_vm);return success;
}
static int close_runtime(void){
    JNIEnv *env=NULL;
    if((*runtime_vm)->AttachCurrentThreadAsDaemon(runtime_vm,(void**)&env,NULL)!=JNI_OK)return 0;
    // Unlinking marks the close request for the supervisor's cleanup deadline.
    if(endpoint)unlink(endpoint);
    (*env)->CallStaticVoidMethod(env,runtime_class,close_method);
    int success=!(*env)->ExceptionCheck(env);
    if(!success){(*env)->ExceptionDescribe(env);(*env)->ExceptionClear(env);}
    (*runtime_vm)->DetachCurrentThread(runtime_vm);return success;
}
JNIEXPORT void JNICALL Java_SdRuntimeControl_nativeStart(JNIEnv *env,jclass type,jstring path){
    (*env)->GetJavaVM(env,&runtime_vm);runtime_class=(*env)->NewGlobalRef(env,type);close_method=(*env)->GetStaticMethodID(env,type,"onCloseRequested","()V");if(!close_method)return;
    diagnostics=(*env)->NewGlobalRef(env,(*env)->FindClass(env,"SdRuntimeDiagnostics"));dump_method=(*env)->GetStaticMethodID(env,diagnostics,"dumpThreads","()V");if(!dump_method)return;
    const char *text=(*env)->GetStringUTFChars(env,path,NULL);if(!text)return;endpoint=strdup(text);(*env)->ReleaseStringUTFChars(env,path,text);
    if(!endpoint||sd_runtime_control_start(endpoint,awake,close_runtime,NULL,dump_runtime)<0)(*env)->ThrowNew(env,(*env)->FindClass(env,"java/lang/IllegalStateException"),"Runtime close endpoint unavailable");
}
JNIEXPORT void JNICALL Java_SdRuntimeControl_nativeStop(JNIEnv *env,jclass type){
    (void)env;(void)type;
    sd_runtime_control_stop();
}
