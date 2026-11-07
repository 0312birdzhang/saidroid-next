#!/bin/bash
echo "=== libunwind 1.6.2 是否有 unw_set_iterate_phdr_function ==="
nm -D /usr/lib/aarch64-linux-gnu/libunwind.so.8 2>/dev/null | grep -c "unw_set_iterate_phdr_function" || echo 0
echo "=== 现有的 unwind 符号 ==="
nm -D /usr/lib/aarch64-linux-gnu/libunwind.so.8 2>/dev/null | grep "unw_set" | head -3
echo
echo "=== 这个 API 在哪个版本引入 ==="
echo "查 libunwind 源码: unw_set_iterate_phdr_function 是 1.7+ 引入的"
