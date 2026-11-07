#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== main.mk 的 JDK 检查 ==="
sed -n '150,175p' build/core/main.mk 2>/dev/null
