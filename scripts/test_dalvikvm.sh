#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 文件类型 ==="
file out/host/linux-x86/bin/dalvikvm 2>/dev/null | cut -c1-90
echo
echo "=== 设置库路径并测试 ==="
export LD_LIBRARY_PATH=/tmp/art-build/art-standalone/out/host/linux-x86/lib64:/usr/local/lib
out/host/linux-x86/bin/dalvikvm --help 2>&1 | head -15
