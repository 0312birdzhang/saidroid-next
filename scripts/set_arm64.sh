#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 找 board config ==="
grep -rn "TARGET_ARCH := arm" build/core/*.mk build/buildspec.mk.default 2>/dev/null | head -5
echo
echo "=== buildspec.mk.default 内容 ==="
head -40 build/buildspec.mk.default 2>/dev/null | grep -vE "^#|^$" | head -10
