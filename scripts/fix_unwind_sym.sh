#!/bin/bash
echo "=== 检查 libunwind-common.h 的宏定义 ==="
grep -n "UNW_OBJ\|unw_set_iterate_phdr_function" /usr/local/include/libunwind-common.h 2>/dev/null | head -5
echo
echo "=== 系统旧版是否有通用符号 ==="
nm -D /usr/lib/aarch64-linux-gnu/libunwind.so.8 2>/dev/null | grep "iterate_phdr" | head -3
echo
echo "=== bionic_translation 编译时的 include 路径 ==="
grep -n "unwind" /tmp/art-build/bionic_translation/meson.build 2>/dev/null | head -3
