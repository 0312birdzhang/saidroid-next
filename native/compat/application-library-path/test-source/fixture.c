#include <jni.h>
static int value=80,initializations;
JNIEXPORT jint JNI_OnLoad(JavaVM *vm,void *reserved) {
    (void)vm;(void)reserved;++initializations;return JNI_VERSION_1_6;
}
JNIEXPORT jint JNICALL Java_org_example_saildroid_nativepath_NativePathActivity_next(JNIEnv *env,jclass type) {
    (void)env;(void)type;return ++value;
}
JNIEXPORT jint JNICALL Java_org_example_saildroid_nativepath_NativePathActivity_loads(JNIEnv *env,jclass type) {
    (void)env;(void)type;return initializations;
}
