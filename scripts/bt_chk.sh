echo "=== VM 上的源码是否已更新 ==="
grep -c "真实环境变量优先" /tmp/art-build/bionic_translation/libc/libc-misc.c
ls -l /tmp/art-build/bionic_translation/libc/libc-misc.c
echo "=== 只重跑 ninja，看它怎么说 ==="
cd /tmp/art-build/bionic_translation
ninja -C builddir 2>&1 | tail -6
echo "=== 产物时间 ==="
ls -l builddir/libc_bio.so.0
echo "=== 新逻辑是否在 so 里 ==="
strings builddir/libc_bio.so.0 | grep -c "ANDROID_ROOT"
