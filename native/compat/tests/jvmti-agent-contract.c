#include <jni.h>
#include <jvmti.h>

/* Real private-Bionic Agent_OnAttach and JVMTI environment. No external imports,
 * fabricated capability results, modified bytecode or swallowed callback error. */
static void trace(const char *message,long length) {
#if defined(__aarch64__)
    register long fd __asm__("x0")=2;
    register long text __asm__("x1")=(long)message;
    register long size __asm__("x2")=length;
    register long call __asm__("x8")=64;
    __asm__ volatile("svc #0":"+r"(fd):"r"(text),"r"(size),"r"(call):"memory","cc");
#else
#error This fixture requires the actual AArch64 build VM
#endif
}
#define TRACE(value) trace("JVMTI_STEP=" value "\n",sizeof("JVMTI_STEP=" value "\n")-1)
static volatile jint retransform_callbacks;
static void JNICALL class_file_hook(jvmtiEnv *ti,JNIEnv *jni,jclass redefined,jobject loader,
        const char *name,jobject domain,jint length,const unsigned char *bytes,
        jint *new_length,unsigned char **new_bytes) {
    (void)ti;(void)jni;(void)loader;(void)name;(void)domain;(void)length;(void)bytes;
    (void)new_length;(void)new_bytes;
    if(redefined){retransform_callbacks++;TRACE("class-file-hook");}
}

JNIEXPORT jint JNICALL Agent_OnAttach(JavaVM *vm,char *options,void *reserved) {
    (void)reserved;
    jvmtiEnv *ti=0;JNIEnv *jni=0;
    if((*vm)->GetEnv(vm,(void **)&ti,JVMTI_VERSION_1_2)!=JNI_OK || !ti)return 21;
    if((*vm)->GetEnv(vm,(void **)&jni,JNI_VERSION_1_6)!=JNI_OK || !jni)return 22;
    jvmtiPhase phase;
    if((*ti)->GetPhase(ti,&phase)!=JVMTI_ERROR_NONE || phase!=JVMTI_PHASE_LIVE)return 23;
    jvmtiCapabilities potential={0},wanted={0},actual={0};
    if((*ti)->GetPotentialCapabilities(ti,&potential)!=JVMTI_ERROR_NONE || !potential.can_retransform_classes || !potential.can_tag_objects)return 24;
    wanted.can_retransform_classes=1;wanted.can_tag_objects=1;
    if((*ti)->AddCapabilities(ti,&wanted)!=JVMTI_ERROR_NONE || (*ti)->GetCapabilities(ti,&actual)!=JVMTI_ERROR_NONE || !actual.can_retransform_classes || !actual.can_tag_objects)return 25;
    jint count=0;jclass *classes=0;
    if((*ti)->GetLoadedClasses(ti,&count,&classes)!=JVMTI_ERROR_NONE || count<10 || !classes)return 26;
    jclass target=0;
    for(jint index=0;index<count;index++){
        char *signature=0;
        if((*ti)->GetClassSignature(ti,classes[index],&signature,0)!=JVMTI_ERROR_NONE)return 30;
        const char *wanted=options&&options[0]?options:"LJvmtiAgentContract;";int match=1;
        unsigned int at=0;
        for(;;at++){if(signature[at]!=wanted[at]){match=0;break;}if(!wanted[at])break;}
        if(match)target=classes[index];
        if((*ti)->Deallocate(ti,(unsigned char *)signature)!=JVMTI_ERROR_NONE)return 30;
    }
    if((*ti)->Deallocate(ti,(unsigned char *)classes)!=JVMTI_ERROR_NONE)return 27;
    if(!target)return 30;
    jboolean modifiable=JNI_FALSE;
    if((*ti)->IsModifiableClass(ti,target,&modifiable)!=JVMTI_ERROR_NONE || !modifiable)return 31;
    jvmtiEventCallbacks callbacks={0};callbacks.ClassFileLoadHook=class_file_hook;
    if((*ti)->SetEventCallbacks(ti,&callbacks,sizeof(callbacks))!=JVMTI_ERROR_NONE ||
       (*ti)->SetEventNotificationMode(ti,JVMTI_ENABLE,JVMTI_EVENT_CLASS_FILE_LOAD_HOOK,0)!=JVMTI_ERROR_NONE)return 32;
    TRACE("retransform");
    if((*ti)->RetransformClasses(ti,1,&target)!=JVMTI_ERROR_NONE || retransform_callbacks!=1)return 33;
    if((*ti)->SetEventNotificationMode(ti,JVMTI_DISABLE,JVMTI_EVENT_CLASS_FILE_LOAD_HOOK,0)!=JVMTI_ERROR_NONE)return 34;
    TRACE("tag");
    jlong expected=0x1234567,tag=0;
    if((*ti)->SetTag(ti,target,expected)!=JVMTI_ERROR_NONE || (*ti)->GetTag(ti,target,&tag)!=JVMTI_ERROR_NONE || tag!=expected)return 35;
    jobject *objects=0;jlong *tags=0;jint found=0;
    TRACE("tagged-objects");
    if((*ti)->GetObjectsWithTags(ti,1,&expected,&found,&objects,&tags)!=JVMTI_ERROR_NONE ||
       found!=1 || !objects || !tags || tags[0]!=expected || !(*jni)->IsSameObject(jni,objects[0],target))return 36;
    (*jni)->DeleteLocalRef(jni,objects[0]);
    if((*ti)->Deallocate(ti,(unsigned char *)objects)!=JVMTI_ERROR_NONE ||
       (*ti)->Deallocate(ti,(unsigned char *)tags)!=JVMTI_ERROR_NONE ||
       (*ti)->SetTag(ti,target,0)!=JVMTI_ERROR_NONE)return 37;
    TRACE("complete");
    jclass system=(*jni)->FindClass(jni,"java/lang/System");
    jmethodID set=system?(*jni)->GetStaticMethodID(jni,system,"setProperty","(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;"):0;
    if(!set)return 28;
    jstring key=(*jni)->NewStringUTF(jni,"saidroid.jvmti.contract");
    jstring value=(*jni)->NewStringUTF(jni,"actual-live-capabilities");
    (*jni)->CallStaticObjectMethod(jni,system,set,key,value);
    return (*jni)->ExceptionCheck(jni)?29:JNI_OK;
}
