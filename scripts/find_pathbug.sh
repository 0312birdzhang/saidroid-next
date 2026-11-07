#!/bin/bash
cd /tmp/art-build/art-standalone 2>/dev/null || cd /opt/art/src 2>/dev/null || exit 1
echo "=== parsed_options.cc 附近的路径拼接 ==="
sed -n '580,600p' art/runtime/parsed_options.cc 2>/dev/null
echo "=== 搜 dex2oat 路径拼接 ==="
grep -rn "dex2oat" art/runtime/*.cc art/runtime/*.h 2>/dev/null | grep -iE "path|exec|bin" | head -8
