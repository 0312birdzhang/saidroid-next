#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== GetAndroidRoot 的实现 ==="
grep -n -A10 "std::string GetAndroidRoot" art/runtime/runtime.cc 2>/dev/null | head -15
echo
echo "=== 我改的地方 ==="
sed -n '798,815p' art/runtime/runtime.cc 2>/dev/null
