#!/bin/bash
cd /tmp/art-build/bionic_translation
echo "=== 为什么需要 1.8+ ==="
grep -rn "libunwind" meson.build 2>/dev/null | head -5
echo
echo "=== 用 1.6.2 会缺什么 API ==="
grep -rn "unw_\|_Unwind" linker/*.c libc/*.c 2>/dev/null | head -8
