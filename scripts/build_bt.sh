#!/bin/bash
echo "=== 准备 bionic_translation ==="
rm -rf /tmp/art-build/bionic_translation
cp -r /media/psf/Home/WorkSpace/saidroid-next/third_party/bionic_translation /tmp/art-build/ 2>/dev/null
cd /tmp/art-build/bionic_translation || exit 1
echo "=== meson setup ==="
meson setup builddir --prefix=/usr/local 2>&1 | tail -15
echo "=== ninja ==="
ninja -C builddir 2>&1 | tail -15
echo "=== 产物 ==="
find builddir -name "*.so*" 2>/dev/null | head -10
