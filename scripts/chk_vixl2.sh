#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== external 目录 ==="
ls external/ 2>/dev/null
echo
echo "=== vixl 是否为空 ==="
ls -la external/vixl/ 2>/dev/null
echo
echo "=== 构建系统怎么引用 vixl ==="
grep -rn "vixl" art/compiler/Android.mk 2>/dev/null | head -8
