#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== find-jdk-tools-jar.sh 的逻辑 ==="
cat build/core/find-jdk-tools-jar.sh 2>/dev/null | head -30
echo
echo "=== config.mk 里 HOST_JDK_TOOLS_JAR 怎么算 ==="
sed -n '485,500p' build/core/config.mk 2>/dev/null
