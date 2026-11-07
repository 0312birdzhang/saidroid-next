#include <jni.h>
#include <stdint.h>

/* Test adapter only: call the exact platform registration function returned by
 * the existing bridge's real ELF symbol lookup. No network API replacement. */
JNIEXPORT jint JNICALL Java_NativeNetworkRegistrationContract_registerActual(
        JNIEnv *env,jclass type,jlong address) {
    (void)type;
    if(!address)return -1;
    int (*function)(JNIEnv *)=(int(*)(JNIEnv *))(uintptr_t)address;
    return function(env);
}
