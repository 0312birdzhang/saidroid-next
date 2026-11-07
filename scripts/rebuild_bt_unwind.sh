#!/bin/bash
cd /tmp/art-build/bionic_translation
echo "=== 强制用 /usr/local 的 libunwind 头 ==="
rm -rf builddir
PKG_CONFIG_PATH=/usr/local/lib/pkgconfig meson setup builddir --prefix=/usr/local 2>&1 | grep -E "libunwind|ERROR" | head -5
echo "=== 构建 ==="
ninja -C builddir 2>&1 | tail -10
echo "=== 检查 libdl_bio 的符号 ==="
nm -D builddir/libdl_bio.so.0.0.1 2>/dev/null | grep "iterate_phdr" | head -3
