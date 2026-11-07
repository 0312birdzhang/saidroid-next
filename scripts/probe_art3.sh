#!/bin/bash
cd /media/psf/Home/WorkSpace/saidroid-next/third_party/art-standalone
echo "=== envsetup.mk 的架构识别 ==="
grep -nE "aarch64|arm64|uname|x86_64" build/core/envsetup.mk 2>/dev/null | head -20
