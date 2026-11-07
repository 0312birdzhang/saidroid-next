#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 谁用 HOST_JDK_TOOLS_JAR ==="
grep -rn "HOST_JDK_TOOLS_JAR" build/core/*.mk 2>/dev/null | head -10
echo
echo "=== 当前构建是否已经用到 ==="
grep -c "HOST_JDK_TOOLS_JAR" /tmp/art-build4.log 2>/dev/null || echo 0
echo
echo "=== dx 是否已经编出来 ==="
find out -name "dx" -o -name "dx.jar" 2>/dev/null | head -5
ls -la out/host/linux-x86/bin/ 2>/dev/null | head -8
