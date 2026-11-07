#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== ART_HOST_CODEGEN_ARCHS 定义 ==="
grep -n -B3 -A8 "ART_HOST_CODEGEN_ARCHS" art/build/Android.common_build.mk 2>/dev/null | head -25
