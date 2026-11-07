#!/bin/bash
echo "=== 我的 /tmp/art-build 状态 ==="
cd /tmp/art-build/art-standalone 2>/dev/null && git status --short 2>/dev/null | head -5
echo
echo "=== 产物对比 ==="
echo "--- 我的 ---"
ls -la /tmp/art-build/art-standalone/out/host/linux-x86/bin/ 2>/dev/null | tail -4
echo "--- 同事的 ---"
ls -la /opt/art/bin/ 2>/dev/null | head -5
echo
echo "=== 两边 dalvikvm 是否都能跑 ==="
echo "--- 我的 ---"
LD_LIBRARY_PATH=/tmp/art-build/art-standalone/out/host/linux-x86/lib64:/usr/local/lib \
  /tmp/art-build/art-standalone/out/host/linux-x86/bin/dalvikvm -showversion 2>&1 | head -3
echo "--- 同事的 ---"
LD_LIBRARY_PATH=/opt/art/lib/aarch64-linux-gnu \
  /opt/art/bin/dalvikvm -showversion 2>&1 | head -3
