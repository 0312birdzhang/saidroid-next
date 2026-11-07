#!/bin/bash
echo "=== 错误详情 ==="
grep -B3 -A6 "error:" /tmp/art-build9.log 2>/dev/null | head -20
echo
echo "=== dalvikvm 是否可执行 ==="
cd /tmp/art-build/art-standalone
file out/host/linux-x86/bin/dalvikvm 2>/dev/null | cut -c1-100
echo "=== 试运行 ==="
out/host/linux-x86/bin/dalvikvm --help 2>&1 | head -5
