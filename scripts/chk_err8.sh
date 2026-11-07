#!/bin/bash
grep -B2 -A8 "error:" /tmp/art-build8.log 2>/dev/null | head -25
echo "=== 进度 ==="
echo "已编译 .o: $(find /tmp/art-build/art-standalone/out -name '*.o' 2>/dev/null | wc -l)"
