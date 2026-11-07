#!/bin/bash
echo "=== 方案：从 VIXL 源码里找 aarch32 ==="
ls /tmp/art-build/vixl/src/aarch32/ 2>/dev/null | head -5
echo
echo "=== 如果没有，创建空桩 ==="
mkdir -p /usr/local/include/aarch32
if [ ! -f /usr/local/include/aarch32/macro-assembler-aarch32.h ]; then
cat > /usr/local/include/aarch32/macro-assembler-aarch32.h <<'EOF'
#ifndef AARCH32_MACRO_ASSEMBLER_STUB_H
#define AARCH32_MACRO_ASSEMBLER_STUB_H
/* Stub: aarch32 not needed for arm64-only build */
namespace vixl { namespace aarch32 {
  class MacroAssembler {};
} }
#endif
EOF
echo "已创建 aarch32 桩头文件"
fi
ls -la /usr/local/include/aarch32/
