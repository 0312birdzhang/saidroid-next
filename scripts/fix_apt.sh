#!/bin/bash
echo "=== 修复 apt 依赖 ==="
apt-get --fix-broken install -y 2>&1 | tail -12
echo "=== 再装依赖 ==="
apt-get install -y libcap-dev libbsd-dev zlib1g-dev 2>&1 | tail -8
echo "=== 验证 ==="
ls /usr/include/sys/capability.h 2>/dev/null && echo "cap=ok" || echo "cap=missing"
ls /usr/include/bsd/string.h 2>/dev/null && echo "bsd=ok" || echo "bsd=missing"
ls /usr/include/zlib.h 2>/dev/null && echo "zlib=ok" || echo "zlib=missing"
