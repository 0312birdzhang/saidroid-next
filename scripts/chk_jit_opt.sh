#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== art/compiler 的架构选择 ==="
grep -nE "arm64|arm_vixl|HOST_ARCH" art/compiler/Android.mk 2>/dev/null | head -15
echo
echo "=== 是否可跳过 compiler ==="
grep -nE "libart-compiler|art-compiler" Makefile 2>/dev/null | head -5
