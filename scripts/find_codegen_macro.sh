#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== ART_ENABLE_CODEGEN_arm 定义在哪 ==="
grep -rn "ART_ENABLE_CODEGEN_arm\b" art/compiler/Android.mk build/core/*.mk 2>/dev/null | head -8
echo
echo "=== 定义逻辑 ==="
grep -rn "ART_ENABLE_CODEGEN" art/compiler/Android.mk 2>/dev/null | head -12
