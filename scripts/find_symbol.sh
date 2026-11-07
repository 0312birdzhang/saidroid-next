#!/bin/bash
echo "=== 1.8.1 所有 unw_set 符号 ==="
nm -D /usr/local/lib/libunwind-aarch64.so.8.1.0 2>/dev/null | grep "unw_set" | head -5
echo
echo "=== 源码里有这个函数吗 ==="
grep -rn "unw_set_iterate_phdr_function" /tmp/libunwind-src/src/ /tmp/libunwind-src/include/ 2>/dev/null | head -3
echo
echo "=== bionic_translation 怎么用的 ==="
grep -rn "unw_set_iterate_phdr_function" /tmp/art-build/bionic_translation/ 2>/dev/null | head -3
