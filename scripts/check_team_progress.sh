#!/bin/bash
echo "=== 构建日志进度 ==="
ls -la /tmp/art-build*.log 2>/dev/null | tail -3
echo "=== 当前错误 ==="
grep -c "error:" /tmp/art-build4.log 2>/dev/null || echo 0
echo "=== 缺的头文件 ==="
ls /usr/include/sys/capability.h /usr/include/bsd/string.h 2>/dev/null
echo "=== 手动下载 libcap 头 ==="
mkdir -p /tmp/extra-headers/sys
cd /tmp
curl -sL --max-time 60 -o cap.tar.gz "https://mirrors.edge.kernel.org/pub/linux/libs/security/libcap/libcap-2.69.tar.gz" 2>/dev/null && tar xzf cap.tar.gz 2>/dev/null && ls libcap-2.69/libcap/include/sys/ 2>/dev/null | head -3
