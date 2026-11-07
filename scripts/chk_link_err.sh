#!/bin/bash
echo "=== 链接错误 ==="
grep -B5 "collect2" /tmp/art-build12.log 2>/dev/null | head -20
echo
echo "=== undefined 符号 ==="
grep -oE "undefined reference to [^ ]*" /tmp/art-build12.log 2>/dev/null | head -10
