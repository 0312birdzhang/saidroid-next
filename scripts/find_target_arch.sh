#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 全局搜 TARGET_ARCH := ==="
grep -rn "TARGET_ARCH *:*=" build/core/*.mk Makefile 2>/dev/null | head -10
echo
echo "=== buildspec.mk 是否存在 ==="
ls -la build/buildspec.mk 2>/dev/null || echo "不存在（用默认）"
echo
echo "=== 默认值在 envsetup.mk ==="
grep -nE "TARGET_ARCH|TARGET_ARCH_VARIANT" build/core/envsetup.mk 2>/dev/null | head -10
