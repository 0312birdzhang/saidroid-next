#!/bin/bash
set -u
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
export LD_LIBRARY_PATH=$BASE/lib64:/usr/local/lib
export ANDROID_ROOT=$BASE
export ANDROID_DATA=/tmp/art-data
export PATH=$BASE/bin:$PATH
mkdir -p $ANDROID_DATA
LIBDIR=${LIBDIR:-/tmp/shimtest}
APK=${APK:-/tmp/and23/out/framework/framework-res.apk}
cd /tmp/ap || exit 1
cat > /tmp/ap/s.gdb <<'GDB'
set pagination off
set confirm off
set breakpoint pending on
handle SIGSEGV stop print nopass
handle SIGABRT stop print nopass
handle SIGBUS stop print nopass
run
printf "\n=== FAULT ===\n"
info registers pc x0 x1 x2 x29 x30
x/6i $pc-8
printf "\n=== bt 40 ===\n"
bt 40
printf "\n=== mappings 里包含 pc 的段 ===\n"
info proc mappings
printf "\n=== end ===\n"
kill
quit
GDB
timeout 420 gdb -batch -nx -x /tmp/ap/s.gdb --args \
  $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so $APK \
  > /tmp/ap/gdb.log 2>&1
echo "gdb rc=$?"
echo "=== AP 标记 ==="
grep -a "AP\[" /tmp/ap/gdb.log | head -20
echo "=== FAULT 段 ==="
awk '/=== FAULT ===/{p=1} p' /tmp/ap/gdb.log | head -70
