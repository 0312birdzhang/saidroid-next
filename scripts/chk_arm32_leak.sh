#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== Android.mk 里 arm 和 arm64 的条件 ==="
grep -nE "ifeq.*TARGET_ARCH|ifeq.*HOST_ARCH|arm_vixl|_arm_CODEGEN" art/compiler/Android.mk 2>/dev/null | head -20
echo
echo "=== 当前构建的架构变量 ==="
grep -E "TARGET_ARCH|HOST_ARCH" /tmp/art-build7.log 2>/dev/null | head -3
