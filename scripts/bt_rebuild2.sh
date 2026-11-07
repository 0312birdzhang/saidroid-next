#!/bin/bash
set -u
SRC=/media/psf/Home/WorkSpace/saidroid-next/third_party/bionic_translation
DST=/tmp/art-build/bionic_translation
rsync -a --delete --exclude builddir "$SRC"/ "$DST"/
cd "$DST" || exit 1
ninja -C builddir 2>&1 | grep -E "error|FAILED" | head -10
echo "=== NEEDED ==="
readelf -d builddir/libc_bio.so.0 | grep NEEDED
echo "=== ldd -r 检查未解析 ==="
LD_LIBRARY_PATH=$DST/builddir ldd -r builddir/libc_bio.so.0 2>&1 | grep -i "undefined\|not found" | head -5
echo "=== 安装 ==="
cp -a builddir/libc_bio.so.0 builddir/libdl_bio.so.0.0.1 builddir/libpthread_bio.so.0 builddir/libstdc++_bio.so.0 /usr/local/lib/
cd /usr/local/lib && ln -sf libdl_bio.so.0.0.1 libdl_bio.so.0 && ln -sf libc_bio.so.0 libc_bio.so && ldconfig 2>/dev/null
ls -l /usr/local/lib/libc_bio.so.0
