#!/bin/bash
echo "=== 重建 libdl_bio，用 --defsym 解析符号 ==="
cd /tmp/art-build/bionic_translation
rm -rf builddir
PKG_CONFIG_PATH=/usr/local/lib/pkgconfig meson setup builddir --prefix=/usr/local 2>&1 | grep -E "libunwind found|ERROR" | head -3
echo "=== 构建（加 defsym）==="
LDFLAGS="-Wl,--defsym,unw_set_iterate_phdr_function=_Uaarch64_set_iterate_phdr_function" \
  ninja -C builddir 2>&1 | tail -8
echo "=== 验证符号 ==="
nm -D builddir/libdl_bio.so.0.0.1 2>/dev/null | grep "iterate_phdr" | head -3
