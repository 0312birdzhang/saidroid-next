F=/tmp/shimtest/libandroid_runtime.so
echo "=== Binder / Parcel / BinderInternal 注册入口 ==="
nm -D --defined-only $F 2>/dev/null | grep -E "register_android_os_(Binder|Parcel|BinderInternal|ParcelFileDescriptor|Process|UserHandle)" | head -10
echo "=== 全部 register_android_os_* ==="
nm -D --defined-only $F 2>/dev/null | grep -oE "_ZN?7?android[0-9]+register_android_os_[A-Za-z]+EP7_JNIEnv|_Z[0-9]+register_android_os_[A-Za-z]+P7_JNIEnv" | head -20
