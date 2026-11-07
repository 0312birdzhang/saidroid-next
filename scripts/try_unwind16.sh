#!/bin/bash
cd /tmp/art-build/bionic_translation
echo "=== 放宽 libunwind 版本要求到 1.6 ==="
python3 - <<'PY'
p="/tmp/art-build/bionic_translation/meson.build"
src=open(p).read()
src = src.replace("dependency('libunwind', version : '>=1.8.0')", "dependency('libunwind', version : '>=1.6.0')")
open(p,"w").write(src)
print("已改为 >=1.6.0")
PY
rm -rf builddir
meson setup builddir --prefix=/usr/local 2>&1 | tail -8
echo "=== ninja ==="
ninja -C builddir 2>&1 | tail -12
echo "=== 产物 ==="
find builddir -name "*.so*" 2>/dev/null | head -8
