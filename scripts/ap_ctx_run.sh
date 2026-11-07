#!/bin/bash
# VM 侧跑 ContextProbe
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
export PATH=$BASE/bin:$PATH
mkdir -p $ANDROID_DATA
LIBDIR=${LIBDIR:-/tmp/shimtest}
LOG=${LOG:-/tmp/ap/ctx.log}
cd /tmp/ap || exit 1
timeout 240 $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex ContextProbe $LIBDIR /tmp/ap/libsdbridge.so \
  $BASE/framework/framework-res.apk > $LOG 2>&1
echo "rc=$?"
echo "=== CP 标记 ==="
grep -a "CP\[" $LOG | head -40
echo "=== 栈 ==="
grep -a "    at " $LOG | head -12
echo "=== 尾部 ==="
grep -av "packed reloc" $LOG | tail -8
