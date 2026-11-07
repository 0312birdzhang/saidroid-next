#!/bin/bash
echo "=== 用真实 aarch32 头文件 ==="
rm -rf /usr/local/include/aarch32
cp -r /tmp/art-build/vixl/src/aarch32 /usr/local/include/ 2>/dev/null
ls /usr/local/include/aarch32/ 2>/dev/null | head -5
echo
echo "=== 编译 aarch32 的 .cc 到 libvixl.a ==="
cd /tmp/art-build/vixl
DEFS="-DVIXL_INCLUDE_TARGET_AARCH32 -DVIXL_INCLUDE_TARGET_AARCH64 -DVIXL_CODE_BUFFER_MALLOC"
ok=0
for f in src/aarch32/*.cc; do
  [ -f "$f" ] || continue
  b=$(basename $f .cc)
  g++ -std=c++17 -O2 -fPIC $DEFS -I src -c "$f" -o "build/a32_$b.o" 2>/dev/null && ok=$((ok+1))
done
echo "aarch32 编译: $ok 个"
ar rcs build/libvixl.a build/*.o 2>/dev/null
ls -la build/libvixl.a
cp build/libvixl.a /usr/local/lib/
