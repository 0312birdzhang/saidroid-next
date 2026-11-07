#!/bin/bash
echo "=== 当前文件状态 ==="
sed -n '350,362p' /tmp/art-build/art-standalone/system/core/liblog/fake_log_device.c 2>/dev/null
echo
echo "=== 是否有多个副本 ==="
find /tmp -name "fake_log_device.c" 2>/dev/null | head -5
