#!/bin/bash
cd /tmp/art-standalone
echo "=== Makefile 里的架构判断 ==="
grep -nE "uname|x86|arm|host" Makefile 2>/dev/null | head -15
echo
echo "=== build/core/config.mk 的架构 ==="
grep -nE "HOST_ARCH|TARGET_ARCH|aarch64|arm64" build/core/config.mk 2>/dev/null | head -10
