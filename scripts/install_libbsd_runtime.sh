#!/bin/bash
echo "=== 下载 libbsd 运行库 ==="
cd /tmp && rm -rf bsdrun && mkdir bsdrun && cd bsdrun
apt-get download libbsd0 2>&1 | tail -2
ls *.deb 2>/dev/null
if [ -f libbsd0*.deb ]; then
  dpkg -x libbsd0*.deb ./x
  find x -name "libbsd.so*" 2>/dev/null
  cp -a x/usr/lib/*/libbsd.so* /usr/lib/aarch64-linux-gnu/ 2>/dev/null
  ldconfig 2>/dev/null
fi
echo "=== 验证 ==="
ls /usr/lib/aarch64-linux-gnu/libbsd.so* 2>/dev/null | head -3
echo "=== 继续 ninja ==="
cd /tmp/art-build/bionic_translation
ninja -C builddir 2>&1 | tail -12
echo "=== 产物 ==="
ls -la builddir/*.so* 2>/dev/null | head -8
