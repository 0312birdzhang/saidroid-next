#!/bin/bash
cd /tmp/art-build/bionic_translation
echo "=== 安装到 /usr/local ==="
cp -a builddir/libc_bio.so.0 builddir/libdl_bio.so.0.0.1 builddir/libpthread_bio.so.0 builddir/libstdc++_bio.so.0 /usr/local/lib/ 2>/dev/null
cd /usr/local/lib
ln -sf libdl_bio.so.0.0.1 libdl_bio.so.0 2>/dev/null
ln -sf libdl_bio.so.0 libdl_bio.so 2>/dev/null
ln -sf libc_bio.so.0 libc_bio.so 2>/dev/null
ln -sf libpthread_bio.so.0 libpthread_bio.so 2>/dev/null
ln -sf libstdc++_bio.so.0 libstdc++_bio.so 2>/dev/null
ldconfig 2>/dev/null
echo "=== 验证 ==="
ls -la /usr/local/lib/lib*_bio.so* 2>/dev/null | head -8
echo
echo "=== lz4 也补上 ==="
ln -sf /usr/lib/aarch64-linux-gnu/liblz4.so.1 /usr/lib/aarch64-linux-gnu/liblz4.so 2>/dev/null
ls /usr/lib/aarch64-linux-gnu/liblz4.so 2>/dev/null && echo "lz4=ok"
