#!/bin/bash
cd /media/psf/Home/WorkSpace/saidroid-next/third_party/art-standalone
echo "=== build/core 文件 ==="
ls build/core/ 2>/dev/null | head -12
echo
echo "=== 架构定义在哪 ==="
grep -rlnE "HOST_ARCH.*:=|aarch64" build/core/*.mk 2>/dev/null | head -5
echo
echo "=== config.mk 的 HOST_ARCH ==="
grep -nE "HOST_ARCH|HOST_OS|uname" build/core/config.mk 2>/dev/null | head -10
