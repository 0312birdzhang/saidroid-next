A=/tmp/art-build/art-standalone/art/runtime/jni/java_vm_ext.cc
echo "=== 文件行数 ==="; wc -l $A
echo "=== dlopen / dlsym 相关 ==="
grep -n "dlopen\|dlsym\|android_dlopen_ext\|LoadNativeLibrary" $A | head -20
