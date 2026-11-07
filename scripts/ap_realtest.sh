#!/bin/bash
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
export PATH=$BASE/bin:$PATH
cd /tmp/ap || exit 1
LIBDIR=/tmp/realtest LOG=/tmp/ap/real.log
timeout 240 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so \
  $BASE/framework/framework-res.apk > $LOG 2>&1
echo "rc=$?"
grep -a "AP\[" $LOG | head -20
echo "=== 堆错误 ==="
grep -ac "invalid\|corrupt" $LOG
