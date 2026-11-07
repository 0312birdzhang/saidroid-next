#!/bin/bash
echo "=== 错误行 ==="
grep -nE "error:|Error [0-9]|\*\*\*" /tmp/art-build.log 2>/dev/null | head -20
echo
echo "=== 最后 25 行 ==="
tail -25 /tmp/art-build.log 2>/dev/null
