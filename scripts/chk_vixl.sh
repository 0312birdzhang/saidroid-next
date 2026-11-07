#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== disasm-aarch64.h 在哪 ==="
find . -name "disasm-aarch64.h" 2>/dev/null | head -3
echo "=== vixl 目录 ==="
ls external/vixl/ 2>/dev/null | head -5
find . -path "*vixl*" -name "*.h" 2>/dev/null | head -3
echo "=== assembler_arm64.h 的 include 路径 ==="
sed -n '30,45p' art/compiler/utils/arm64/assembler_arm64.h 2>/dev/null
