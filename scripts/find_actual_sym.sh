#!/bin/bash
echo "=== 实际符号名（宏展开后）==="
nm -D /usr/local/lib/libunwind-aarch64.so.8.1.0 2>/dev/null | grep -i "iterate_phdr" | head -5
echo
echo "=== 编译产物里 ==="
find /tmp/libunwind-src -name "*set_iterate*" 2>/dev/null | head -3
echo
echo "=== 库里的所有 set_ 符号 ==="
nm -D /usr/local/lib/libunwind-aarch64.so.8.1.0 2>/dev/null | grep "set_" | head -8
