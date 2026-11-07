#!/bin/bash
echo "=== 下载 libbsd-dev ==="
cd /tmp && rm -rf bsdtmp && mkdir bsdtmp && cd bsdtmp
apt-get download libbsd-dev 2>&1 | tail -2
ls *.deb 2>/dev/null
if [ -f libbsd-dev*.deb ]; then
  dpkg -x libbsd-dev*.deb ./x
  echo "=== 装头文件 ==="
  cp -a x/usr/include/* /usr/include/ 2>/dev/null
  ls /usr/include/bsd/string.h 2>/dev/null && echo "bsd_header=ok"
  echo "=== 装 pkgconfig ==="
  cp -a x/usr/lib/*/pkgconfig/*.pc /usr/lib/pkgconfig/ 2>/dev/null || mkdir -p /usr/lib/pkgconfig && cp -a x/usr/lib/*/pkgconfig/*.pc /usr/lib/pkgconfig/ 2>/dev/null
  find x -name "libbsd.pc" 2>/dev/null
fi
echo "=== 检查 pkg-config ==="
pkg-config --exists libbsd && echo "pkgconfig=ok" || echo "pkgconfig=missing"
