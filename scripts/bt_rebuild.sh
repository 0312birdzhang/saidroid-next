#!/bin/bash
# 在 VM 上重建 libc_bio / libdl_bio / libpthread_bio / libstdc++_bio
set -u
SRC=/media/psf/Home/WorkSpace/saidroid-next/third_party/bionic_translation
DST=/tmp/art-build/bionic_translation
echo "=== 同步源码 ==="
rsync -a --delete --exclude builddir "$SRC"/ "$DST"/
cd "$DST" || exit 1
if [ ! -f builddir/build.ninja ]; then
  meson setup builddir --prefix=/usr/local 2>&1 | tail -8
fi
echo "=== ninja ==="
ninja -C builddir 2>&1 | grep -E "error|warning: implicit|FAILED" | head -25
echo "rc=$?"
echo "=== 产物 ==="
ls -lh builddir/libc_bio.so.0 builddir/libdl_bio.so.0.0.1 builddir/libpthread_bio.so.0 builddir/libstdc++_bio.so.0 2>/dev/null
echo "=== 安装到 /usr/local/lib ==="
cp -a builddir/libc_bio.so.0 builddir/libdl_bio.so.0.0.1 builddir/libpthread_bio.so.0 builddir/libstdc++_bio.so.0 /usr/local/lib/ 2>/dev/null
cd /usr/local/lib
ln -sf libdl_bio.so.0.0.1 libdl_bio.so.0
ln -sf libdl_bio.so.0 libdl_bio.so
ln -sf libc_bio.so.0 libc_bio.so
ln -sf libpthread_bio.so.0 libpthread_bio.so
ln -sf libstdc++_bio.so.0 libstdc++_bio.so
ldconfig 2>/dev/null
echo "=== 护栏符号检查 ==="
nm -D --defined-only builddir/libc_bio.so.0 2>/dev/null | grep -E " T (malloc|free|calloc|realloc|memalign|posix_memalign|aligned_alloc|malloc_usable_size|valloc)$"
