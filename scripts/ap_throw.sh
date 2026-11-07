#!/bin/bash
# 用 throwwatch 抓 std::out_of_range 的现场
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
export PATH=$BASE/bin:$PATH
mkdir -p $ANDROID_DATA
LIBDIR=${LIBDIR:-/tmp/shimtest}
APK=${APK:-/tmp/and23/out/framework/framework-res.apk}
WATCH=${WATCH:-out_of_range}
cd /tmp/ap || exit 1

echo "=== 编译 throwwatch ==="
gcc -shared -fPIC -O1 -o /tmp/ap/libthrowwatch.so \
  /media/psf/Home/WorkSpace/saidroid-next/scripts/debug/throwwatch.c -ldl 2>&1 | head -5
ls -l /tmp/ap/libthrowwatch.so

echo "=== 运行 (watch=$WATCH) ==="
SD_THROW_WATCH=$WATCH LD_PRELOAD=/tmp/ap/libthrowwatch.so \
  timeout 120 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so $APK \
  > /tmp/ap/throw.log 2>&1
echo "rc=$?"
echo "=== AP 标记 ==="
grep -a "AP\[" /tmp/ap/throw.log | head -20
echo "=== throwwatch 现场 ==="
awk '/=== throwwatch/{p=1} p' /tmp/ap/throw.log | head -40
