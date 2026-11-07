#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== trampoline_compiler.cc 的 include 段 ==="
sed -n '15,35p' art/compiler/trampolines/trampoline_compiler.cc 2>/dev/null
