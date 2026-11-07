#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 编译 trampoline_compiler 时的实际命令 ==="
grep -A2 "trampoline_compiler" /tmp/art-build11.log 2>/dev/null | head -5
echo
echo "=== 从 ninja/make 输出找 -DART_ENABLE_CODEGEN ==="
grep -oE "\-DART_ENABLE_CODEGEN_[a-z0-9_]+" /tmp/art-build11.log 2>/dev/null | sort -u | head -10
echo
echo "=== ART_HOST_CODEGEN_ARCHS 是否生效 ==="
grep -oE "ART_HOST_CODEGEN_ARCHS=[a-z0-9 ]*" /tmp/art-build11.log 2>/dev/null | head -3
