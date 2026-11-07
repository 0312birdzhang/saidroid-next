A=/tmp/art-build/art-standalone/art/runtime/jni/java_vm_ext.cc
echo "=== LoadNativeLibrary 里的 LOG(FATAL)/CHECK ==="
sed -n '879,1120p' $A | grep -n "LOG(FATAL)\|CHECK\|LOG(ERROR)" | head -10
echo "=== 相关代码段 ==="
sed -n '1060,1110p' $A
