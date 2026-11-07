#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== code_generator.cc 的 include 条件 ==="
sed -n '15,30p' art/compiler/optimizing/code_generator.cc 2>/dev/null
echo
echo "=== common_arm.h 的 include ==="
sed -n '20,35p' art/compiler/optimizing/common_arm.h 2>/dev/null
