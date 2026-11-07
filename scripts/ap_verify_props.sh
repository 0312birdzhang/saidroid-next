echo "=== /usr/local/lib/libc_bio.so.0 是否含新默认值 ==="
strings /usr/local/lib/libc_bio.so.0 | grep -E "Pixel 3a XL|ro.product.cpu.abilist32|SD_BUILD_PROP" | head -5
echo "=== 顺手把 /tmp/shimtest 里的 bio 库同步成新版 ==="
B=/tmp/art-build/bionic_translation/builddir
cp -f $B/libc_bio.so.0 $B/libdl_bio.so.0.0.1 $B/libpthread_bio.so.0 $B/libstdc++_bio.so.0 /tmp/shimtest/ 2>/dev/null
ln -sf libdl_bio.so.0.0.1 /tmp/shimtest/libdl_bio.so.0
ln -sf libc_bio.so.0 /tmp/shimtest/libc_bio.so
ln -sf libpthread_bio.so.0 /tmp/shimtest/libpthread_bio.so
ln -sf libstdc++_bio.so.0 /tmp/shimtest/libstdc++_bio.so
ls -l /tmp/shimtest/lib*_bio.so.0
