#!/bin/bash
cd /tmp/art-build/bionic_translation
rm -rf builddir
meson setup builddir --prefix=/usr/local 2>&1 | tail -10
echo "=== ninja build ==="
ninja -C builddir 2>&1 | tail -20
echo "=== 产物 ==="
find builddir -name "*.so*" 2>/dev/null | head -10
