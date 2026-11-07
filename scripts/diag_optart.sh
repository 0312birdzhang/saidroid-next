#!/bin/bash
echo "=== /opt/art 布局 ==="
find /opt/art -maxdepth 2 -type d 2>/dev/null | head -10
echo
echo "=== libdl_bio 的符号 ==="
nm -D /opt/art/lib/aarch64-linux-gnu/libdl_bio.so.0 2>/dev/null | grep "iterate_phdr" | head -3
echo
echo "=== libunwind 在哪 ==="
ls /opt/art/lib/aarch64-linux-gnu/libunwind* 2>/dev/null | head -3
ldd /opt/art/lib/aarch64-linux-gnu/libdl_bio.so.0 2>/dev/null | grep -E "unwind|not found" | head -3
