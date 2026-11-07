#!/bin/bash
echo "=== 下载 lz4 头文件 ==="
cd /tmp && rm -rf lz4tmp && mkdir lz4tmp && cd lz4tmp
apt-get download liblz4-dev 2>&1 | tail -2
ls *.deb 2>/dev/null
if [ -f liblz4-dev*.deb ]; then
  dpkg -x liblz4-dev*.deb ./x
  find x -name "lz4.h" 2>/dev/null
  cp -a x/usr/include/*.h /usr/include/ 2>/dev/null
  ls /usr/include/lz4.h 2>/dev/null && echo "lz4=ok"
fi
echo
echo "=== 检查 libnativehelper 在哪 ==="
find /tmp/art-build/art-standalone/out -name "libnativehelper*" 2>/dev/null | head -3
