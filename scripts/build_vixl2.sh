#!/bin/bash
cd /tmp/art-build/vixl || exit 1
rm -rf build && mkdir -p build
echo "=== 带正确宏重新编译 ==="
DEFS="-DVIXL_INCLUDE_TARGET_AARCH64 -DVIXL_CODE_BUFFER_MALLOC"
ok=0; fail=0
for f in src/aarch64/*.cc src/*.cc; do
  [ -f "$f" ] || continue
  b=$(basename $f .cc)
  if g++ -std=c++17 -O2 -fPIC $DEFS -I src -c "$f" -o "build/$b.o" 2>/tmp/v2_$b.log; then
    ok=$((ok+1))
  else
    fail=$((fail+1))
    [ $fail -le 2 ] && echo "FAIL: $b" && grep error /tmp/v2_$b.log | head -2
  fi
done
echo "编译: ok=$ok fail=$fail"
ar rcs build/libvixl.a build/*.o 2>/dev/null
ls -la build/libvixl.a 2>/dev/null
echo "=== 装到系统 ==="
cp build/libvixl.a /usr/local/lib/ 2>/dev/null
cp -r src/aarch64 /usr/local/include/ 2>/dev/null
cp src/*.h /usr/local/include/ 2>/dev/null
ls /usr/local/include/aarch64/registers-aarch64.h 2>/dev/null && echo "header=ok"
