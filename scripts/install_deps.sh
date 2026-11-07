#!/bin/bash
echo "=== 等 apt 锁释放 ==="
for i in $(seq 1 10); do
  if ! fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
    echo "锁已释放"
    break
  fi
  sleep 5
done
echo "=== 安装缺失依赖 ==="
apt-get install -y libcap-dev libbsd-dev zlib1g-dev liblzma-dev 2>&1 | tail -10
echo "=== 验证 ==="
ls /usr/include/sys/capability.h 2>/dev/null && echo "cap=ok"
ls /usr/include/bsd/string.h 2>/dev/null && echo "bsd=ok"
