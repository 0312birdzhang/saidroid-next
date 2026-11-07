#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== libart-compiler 的源码选择 ==="
sed -n '40,70p' art/compiler/Android.mk 2>/dev/null
