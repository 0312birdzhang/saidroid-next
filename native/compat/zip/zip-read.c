/* Android10 ZipFile.read removes the obsolete 8KiB temporary-buffer limit.
 * Keep the existing JNI ABI and invoke the already-loaded original ZIP backend.
 * Opaque handles avoid coupling this adapter to private jzfile layout.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <jni.h>

static void sd_zip_throw(JNIEnv *env, const char *type, const char *message)
{
    jclass error = (*env)->FindClass(env, type);
    if (error != NULL) {
        (*env)->ThrowNew(env, error, message);
        (*env)->DeleteLocalRef(env, error);
    }
}

JNIEXPORT jint JNICALL ZipFile_read(JNIEnv *env, jclass cls, jlong file,
                                    jlong entry, jlong pos, jbyteArray bytes,
                                    jint off, jint len)
{
    if (bytes == NULL) {
        sd_zip_throw(env, "java/lang/NullPointerException", "bytes == null");
        return -1;
    }
    jsize length = (*env)->GetArrayLength(env, bytes);
    if (off < 0 || len < 0 || (int64_t)off + len > length) {
        sd_zip_throw(env, "java/lang/ArrayIndexOutOfBoundsException", "Invalid ZIP read range");
        return -1;
    }
    void *library = dlopen("libopenjdk.so", RTLD_NOW | RTLD_NOLOAD);
    void (*lock)(void *) = library ? (void (*)(void *))dlsym(library, "ZIP_Lock") : NULL;
    void (*unlock)(void *) = library ? (void (*)(void *))dlsym(library, "ZIP_Unlock") : NULL;
    jint (*read_zip)(void *, void *, jlong, void *, jint) = library
        ? (jint (*)(void *, void *, jlong, void *, jint))dlsym(library, "ZIP_Read") : NULL;
    jstring (*get_message)(JNIEnv *, jclass, jlong) = library
        ? (jstring (*)(JNIEnv *, jclass, jlong))dlsym(library, "ZipFile_getZipMessage") : NULL;
    void (*throw_io)(JNIEnv *, const char *) = library
        ? (void (*)(JNIEnv *, const char *))dlsym(library, "JNU_ThrowIOExceptionWithLastError") : NULL;
    if (lock == NULL || unlock == NULL || read_zip == NULL || get_message == NULL || throw_io == NULL) {
        if (library != NULL) dlclose(library);
        sd_zip_throw(env, "java/lang/UnsatisfiedLinkError", "Original loaded ZIP backend unavailable");
        return -1;
    }
    jbyte *buffer = (*env)->GetByteArrayElements(env, bytes, NULL);
    if (buffer == NULL) { dlclose(library); return -1; }
    void *handle = (void *)(intptr_t)file;
    lock(handle);
    jint result = read_zip(handle, (void *)(intptr_t)entry, pos, buffer + off, len);
    int saved_errno = errno;
    jstring message = result == -1 ? get_message(env, cls, file) : NULL;
    unlock(handle);
    (*env)->ReleaseByteArrayElements(env, bytes, buffer, 0);
    if (result == -1 && !(*env)->ExceptionCheck(env)) {
        if (message != NULL) {
            jclass error = (*env)->FindClass(env, "java/util/zip/ZipException");
            if (error != NULL) {
                jmethodID ctor = (*env)->GetMethodID(env, error, "<init>", "(Ljava/lang/String;)V");
                if (ctor != NULL) {
                    jthrowable instance = (*env)->NewObject(env, error, ctor, message);
                    if (instance != NULL) {
                        (*env)->Throw(env, instance);
                        (*env)->DeleteLocalRef(env, instance);
                    }
                }
                (*env)->DeleteLocalRef(env, error);
            }
        } else {
            errno = saved_errno;
            throw_io(env, "Error reading ZIP file");
        }
    }
    if (message != NULL) (*env)->DeleteLocalRef(env, message);
    dlclose(library);
    return result;
}
