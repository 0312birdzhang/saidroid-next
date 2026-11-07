#!/bin/bash
echo "=== 用 defsym 覆盖所有变体 ==="
cd /tmp/art-build/bionic_translation
rm -rf builddir
PKG_CONFIG_PATH=/usr/local/lib/pkgconfig meson setup builddir --prefix=/usr/local 2>&1 | grep -c ERROR
LDFLAGS="-Wl,--defsym,_ULaarch64_set_iterate_phdr_function=_Uaarch64_set_iterate_phdr_function -Wl,--defsym,unw_set_iterate_phdr_function=_Uaarch64_set_iterate_phdr_function" \
  ninja -C builddir 2>&1 | tail -6
echo "=== 验证 ==="
nm -D builddir/libdl_bio.so.0.0.1 2>/dev/null | grep "iterate_phdr" | head -3
echo "=== 装到系统 ==="
cp -a builddir/libc_bio.so.0 builddir/libdl_bio.so.0.0.1 builddir/libpthread_bio.so.0 builddir/libstdc++_bio.so.0 /usr/local/lib/ 2>/dev/null
ldconfig 2>/dev/null
