#!/bin/bash
# VM 侧：跑 AssetProbe。环境变量控制是否加护栏/进 gdb。
#   SD_ALLOC_GUARD=1   开护栏分配器
#   GDB=1              在 gdb 下跑，SIGSEGV 时打栈
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
export PATH=$BASE/bin:$PATH
mkdir -p $ANDROID_DATA
LIBDIR=${LIBDIR:-/tmp/shimtest}
APK=${APK:-/tmp/and23/out/framework/framework-res.apk}
FRES=${FRES:-}
ARGS="$LIBDIR /tmp/ap/libsdbridge.so $APK $FRES"

cd /tmp/ap || exit 1
echo "=== run: LIBDIR=$LIBDIR APK=$APK guard=${SD_ALLOC_GUARD:-0} gdb=${GDB:-0} ==="
if [ "${GDB:-0}" = "1" ]; then
  gdb -batch -nx \
    -ex "set pagination off" \
    -ex "set confirm off" \
    -ex "handle SIGSEGV stop print nopass" \
    -ex "handle SIGABRT stop print nopass" \
    -ex "run" \
    -ex "printf \"\\n=== FAULT ===\\n\"" \
    -ex "info registers pc" \
    -ex "x/i \$pc" \
    -ex "bt 40" \
    -ex "info sharedlibrary" \
    -ex "kill" \
    --args $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $ARGS 2>&1 | tail -120
else
  timeout 600 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $ARGS 2>&1 | tail -80
  echo "rc=$?"
fi
