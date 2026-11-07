#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== art 源码里 vixl 的版本线索 ==="
grep -rn "VIXL_VERSION\|vixl.*version" art/compiler/utils/arm64/*.h art/compiler/utils/arm64/*.cc 2>/dev/null | head -5
echo "=== assembler_arm64.h 用的 VIXL API ==="
grep -nE "vixl::|VIXL" art/compiler/utils/arm64/assembler_arm64.h 2>/dev/null | head -10
echo "=== art 的 git 版本 ==="
git log --oneline -1 2>/dev/null
echo "=== 是否有 vixl 版本说明 ==="
grep -rn "vixl" README.md art/README* 2>/dev/null | head -5
