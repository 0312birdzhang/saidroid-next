F=/tmp/shimtest/libandroid_runtime.so
echo "=== StringBlock 相关导出 ==="
nm -D --defined-only $F 2>/dev/null | grep -i "stringblock" | head -5
echo "=== 我们列表里 missing 的 4 个（逐个测）==="
for s in _ZN7android34register_android_content_StringBlockEP7_JNIEnv _ZN7android32register_android_util_StringBlockEP7_JNIEnv _Z31register_android_graphics_MovieP7_JNIEnv _Z32register_android_graphics_CameraP7_JNIEnv _Z38register_android_graphics_InterpolatorP7_JNIEnv _Z26register_android_os_BinderP7_JNIEnv; do
  n=$(nm -D --defined-only $F 2>/dev/null | grep -c "^[0-9a-f]* T $s$")
  printf "%s -> %s\n" "$s" "$n"
done
