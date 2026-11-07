#!/bin/bash
rm -rf /tmp/art-build/vixl
cp -r /media/psf/Home/WorkSpace/saidroid-next/third_party/vixl-aosp /tmp/art-build/vixl 2>/dev/null
cd /tmp/art-build/vixl || exit 1
echo "=== 编译 AOSP VIXL ==="
mkdir -p build
ok=0; fail=0
for f in src/aarch64/*.cc src/*.cc; do
  [ -f "$f" ] || continue
  b=$(basename $f .cc)
  if g++ -std=c++17 -O2 -fPIC -I src -c "$f" -o "build/$b.o" 2>/tmp/vixl_$b.log; then
    ok=$((ok+1))
  else
    fail=$((fail+1))
    [ $fail -le 3 ] && echo "FAIL: $b" && head -3 /tmp/vixl_$b.log
  fi
done
echo "编译: ok=$ok fail=$fail"
ar rcs build/libvixl.a build/*.o 2>/dev/null
ls -la build/libvixl.a 2>/dev/null
