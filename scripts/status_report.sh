#!/bin/bash
echo "=== 1. 构建进展 ==="
echo "make 已推进到: $(grep -oE 'target [A-Za-z_]+' /tmp/art-build4.log 2>/dev/null | tail -1)"
echo "编译过的 .o 数: $(find /tmp/art-build/art-standalone/out -name '*.o' 2>/dev/null | wc -l)"
echo
echo "=== 2. 唯一阻塞 ==="
grep -B2 "error:" /tmp/art-build4.log 2>/dev/null | head -8
echo
echo "=== 3. apt 状态 ==="
dpkg --audit 2>&1 | head -8
