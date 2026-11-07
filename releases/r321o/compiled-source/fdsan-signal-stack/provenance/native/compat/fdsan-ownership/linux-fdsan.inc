/* Android10 Bionic fdsan semantics through SailDroid's process-private backend.
 * Called by the real Linux JNI object, including during core VM initialization.
 * Never derive a query result from Java's cached ownerId field.
 */
extern "C" {
    void bionic_android_fdsan_exchange_owner_tag(int, uint64_t, uint64_t);
    uint64_t bionic_android_fdsan_get_owner_tag(int);
    const char* bionic_android_fdsan_get_tag_type(uint64_t);
    uint64_t bionic_android_fdsan_get_tag_value(uint64_t);
    int bionic_android_fdsan_close_with_tag(int, uint64_t);
}

static bool sd_fdsan_null(JNIEnv* env, jobject fd) {
    if (fd != nullptr) return false;
    jniThrowNullPointerException(env, "fd == null");
    return true;
}

static jlong sd_fdsan_java_owner(JNIEnv* env, jobject fd) {
    static jfieldID owner = env->GetFieldID(JniConstants::fileDescriptorClass, "ownerId", "J");
    if (owner == nullptr) return 0;
    return env->GetLongField(fd, owner);
}

static void Linux_android_fdsan_exchange_owner_tag(JNIEnv* env, jobject,
        jobject fd, jlong expected, jlong update) {
    if (sd_fdsan_null(env, fd)) return;
    int raw = jniGetFDFromFileDescriptor(env, fd);
    if (!env->ExceptionCheck()) bionic_android_fdsan_exchange_owner_tag(raw, expected, update);
}

static jlong Linux_android_fdsan_get_owner_tag(JNIEnv* env, jobject, jobject fd) {
    if (sd_fdsan_null(env, fd)) return 0;
    int raw = jniGetFDFromFileDescriptor(env, fd);
    return env->ExceptionCheck() ? 0 : bionic_android_fdsan_get_owner_tag(raw);
}

static jstring Linux_android_fdsan_get_tag_type(JNIEnv* env, jobject, jlong tag) {
    return env->NewStringUTF(bionic_android_fdsan_get_tag_type(tag));
}

static jlong Linux_android_fdsan_get_tag_value(JNIEnv*, jobject, jlong tag) {
    return bionic_android_fdsan_get_tag_value(tag);
}
