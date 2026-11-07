#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== buildspec 默认值 ==="
grep -nE "TARGET_ARCH|TARGET_ARCH_VARIANT" build/buildspec.mk.default 2>/dev/null | head -8
echo
echo "=== Makefile 里怎么设的 ==="
grep -nE "TARGET_ARCH" Makefile 2>/dev/null | head -5
