#!/bin/bash
echo "=== 方案：手动解包 libcap-dev 头文件 ==="
cd /tmp
rm -rf captmp && mkdir captmp && cd captmp
echo "--- 尝试下载 deb ---"
apt-get download libcap-dev 2>&1 | tail -3
ls -la *.deb 2>/dev/null
if [ -f libcap-dev*.deb ]; then
  echo "--- 解包 ---"
  dpkg -x libcap-dev*.deb ./extracted
  find extracted -name "capability.h" 2>/dev/null
  ls extracted/usr/include/sys/ 2>/dev/null | head -3
fi
