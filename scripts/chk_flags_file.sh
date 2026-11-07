#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 找 cflags 记录 ==="
find out -name "*.cflags" -o -name "cflags*" 2>/dev/null | head -3
echo
echo "=== 从 build 目录找 ART_ENABLE ==="
grep -rl "ART_ENABLE_CODEGEN_arm\b" out/ 2>/dev/null | head -3
echo
echo "=== 直接看 libart-compiler 的中间文件 ==="
ls out/host/linux-x86/obj/SHARED_LIBRARIES/libart-compiler_intermediates/ 2>/dev/null | head -5
