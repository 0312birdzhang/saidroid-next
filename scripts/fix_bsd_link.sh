#!/bin/bash
echo "=== 创建 libbsd.so 符号链接 ==="
ln -sf /usr/lib/aarch64-linux-gnu/libbsd.so.0 /usr/lib/aarch64-linux-gnu/libbsd.so 2>/dev/null
ls -la /usr/lib/aarch64-linux-gnu/libbsd.so 2>/dev/null
echo "=== 继续 ninja ==="
cd /tmp/art-build/bionic_translation
ninja -C builddir 2>&1 | tail -10
echo "=== 最终产物 ==="
ls -la builddir/*.so.* 2>/dev/null | grep -v "\.p" | head -8
