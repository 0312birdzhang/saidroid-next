#!/bin/bash
echo "=== 链接错误 ==="
grep -E "cannot find|undefined reference" /tmp/art-build13.log 2>/dev/null | head -10
echo
echo "=== 上下文 ==="
grep -B3 "collect2" /tmp/art-build13.log 2>/dev/null | head -12
