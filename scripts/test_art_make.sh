#!/bin/bash
echo "=== 复制到本地磁盘（共享目录编译慢）==="
rm -rf /tmp/art-build
mkdir -p /tmp/art-build
cp -r /media/psf/Home/WorkSpace/saidroid-next/third_party/art-standalone /tmp/art-build/ 2>&1 | head -3
echo "复制完成: $(du -sh /tmp/art-build/art-standalone 2>/dev/null | cut -f1)"
cd /tmp/art-build/art-standalone
echo "=== 试运行 make（只看前 30 行输出）==="
timeout 120 make -j2 2>&1 | head -30
echo "=== RC=$? ==="
