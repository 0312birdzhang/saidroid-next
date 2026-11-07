#!/bin/bash
echo "=== 错误类型统计 ==="
grep -oE "error: [^;]*" /tmp/art-build6.log 2>/dev/null | sed 's/[0-9]\+/N/g' | sort | uniq -c | sort -rn | head -12
echo
echo "=== 第一个错误详情 ==="
grep -B2 -A4 "error:" /tmp/art-build6.log 2>/dev/null | head -20
