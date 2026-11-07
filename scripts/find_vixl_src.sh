#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== art 源码里是否自带 vixl 副本 ==="
find . -path "*vixl*" -name "disasm-aarch64.h" 2>/dev/null | head -3
echo "=== Android.mk 里 vixl 的定义 ==="
grep -rn "libvixl\|VIXL" art/compiler/Android.mk 2>/dev/null | head -10
echo "=== 是否有 BUILD_VIXL 之类开关 ==="
grep -rn "BUILD_VIXL\|USE_VIXL\|vixl" build/core/*.mk 2>/dev/null | head -5
