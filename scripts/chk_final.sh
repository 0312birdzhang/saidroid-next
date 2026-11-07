#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 构建是否完成 ==="
tail -15 /tmp/art-build15.log 2>/dev/null
echo
echo "=== 产物 ==="
ls -la out/host/linux-x86/bin/ 2>/dev/null
echo "=== lib64 ==="
ls out/host/linux-x86/lib64/*.so 2>/dev/null | head -8
