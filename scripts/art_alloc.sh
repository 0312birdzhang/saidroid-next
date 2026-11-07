A=/tmp/art-build/art-standalone
echo "=== 谁写 ClassLoader.allocator ==="
grep -rn "SetAllocator\|setAllocator\|kAllocatorOffset\|AllocatorOffset" $A/art/runtime --include=*.cc --include=*.h | head -12
echo "=== GetAllocatorForClassLoader 实现 ==="
grep -rn -A8 "GetAllocatorForClassLoader" $A/art/runtime/class_linker.cc | head -20
