#!/bin/bash
echo "=== 1.8.1 的 aarch64 库符号 ==="
nm -D /usr/local/lib/libunwind-aarch64.so.8.1.0 2>/dev/null | grep -c "unw_set_iterate_phdr_function"
echo "=== 具体符号 ==="
nm -D /usr/local/lib/libunwind-aarch64.so.8.1.0 2>/dev/null | grep "unw_set_iterate" | head -2
echo
echo "=== pkg-config 版本 ==="
pkg-config --modversion libunwind 2>/dev/null || echo "需更新 pc"
echo "=== .pc 文件位置 ==="
find /usr/local -name "libunwind*.pc" 2>/dev/null | head -3
