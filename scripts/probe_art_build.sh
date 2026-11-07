#!/bin/bash
cd /media/psf/Home/WorkSpace/saidroid-next/third_party/art-standalone
echo "=== Makefile 架构处理 ==="
grep -nE "uname -m|ARCH|arm64|aarch64" Makefile 2>/dev/null | head -20
echo
echo "=== build/core 里的架构 ==="
grep -rnE "aarch64|arm64" build/core/config.mk 2>/dev/null | head -10
