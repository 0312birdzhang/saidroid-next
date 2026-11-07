#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== art 用到的 VIXL 类型 ==="
grep -ohE "vixl::aarch64::[A-Z][A-Za-z]+" art/compiler/utils/arm64/*.h art/compiler/optimizing/common_arm64.h 2>/dev/null | sort -u | head -20
echo
echo "=== 是否有 vixl 版本说明文件 ==="
find . -iname "*vixl*" -maxdepth 3 2>/dev/null | head -5
echo
echo "=== Android.bp 或 mk 里的 vixl 依赖版本 ==="
grep -rn "vixl" art/compiler/Android.mk 2>/dev/null | grep -iE "version|3\.|4\." | head -3
