#!/bin/bash
# 全量日志版：不加 tail，输出到文件
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
export PATH=$BASE/bin:$PATH
mkdir -p $ANDROID_DATA
LIBDIR=${LIBDIR:-/tmp/shimtest}
APK=${APK:-/tmp/and23/out/framework/framework-res.apk}
LOG=${LOG:-/tmp/ap/run.log}
cd /tmp/ap || exit 1
echo "=== ENV: guard=${SD_ALLOC_GUARD:-0} tcache=${GLIBC_TUNABLES:-default} LOG=$LOG ==="
timeout 300 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so $APK > $LOG 2>&1
echo "rc=$?"
echo "=== 日志行数: $(wc -l < $LOG) ==="
echo "=== AP 标记 ==="
grep -a "AP\[" $LOG | head -40
echo "=== 首个堆错误前后 ==="
n=$(grep -an "malloc()\|free()\|corrupt" $LOG | head -1 | cut -d: -f1)
echo "first_error_line=$n"
if [ -n "$n" ]; then sed -n "$((n>6?n-6:1)),$((n+4))p" $LOG; fi
echo "=== 重复次数 ==="
grep -ac "unaligned tcache" $LOG
