#!/bin/bash
echo "=== 传 VIXL 源码到 VM ==="
mkdir -p /tmp/art-build
rm -rf /tmp/art-build/vixl
cp -r /media/psf/Home/WorkSpace/saidroid-next/third_party/vixl /tmp/art-build/vixl 2>/dev/null
if [ ! -d /tmp/art-build/vixl ]; then
  echo "共享目录没有 vixl，需从 Mac 传"
  exit 1
fi
cd /tmp/art-build/vixl
echo "=== 编译 VIXL 静态库 ==="
mkdir -p build
g++ -std=c++17 -O2 -fPIC -I src -c src/aarch64/*.cc src/*.cc -o /dev/null 2>&1 | head -5
echo "--- 逐个编译 ---"
ok=0; fail=0
for f in src/aarch64/*.cc src/*.cc; do
  b=$(basename $f .cc)
  if g++ -std=c++17 -O2 -fPIC -I src -c "$f" -o "build/$b.o" 2>/dev/null; then
    ok=$((ok+1))
  else
    fail=$((fail+1))
  fi
done
echo "编译: ok=$ok fail=$fail"
ar rcs build/libvixl.a build/*.o 2>/dev/null
ls -la build/libvixl.a 2>/dev/null
