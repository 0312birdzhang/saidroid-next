#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 出错的代码行 ==="
sed -n '355,365p' system/core/liblog/fake_log_device.c 2>/dev/null
echo
echo "=== 编译这个文件用的 flags ==="
grep -n "fake_log_device" /tmp/art-build.log 2>/dev/null | head -3
