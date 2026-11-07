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
cat > /tmp/ap/f.gdb <<'GDB'
set pagination off
set confirm off
set breakpoint pending on
handle SIGSEGV stop print nopass
run
printf "\n=== FRAMES ===\n"
info registers pc x0 x1 x29 x30
set $_walk = (unsigned long)$x29
set $_n = 0
while $_walk != 0 && $_n < 24
  printf "fp[%d] addr=0x%lx saved_fp=0x%lx saved_lr=0x%lx\n", $_n, $_walk, *(unsigned long*)$_walk, *(unsigned long*)($_walk+8)
  set $_walk = *(unsigned long*)$_walk
  set $_n = $_n + 1
end
printf "=== END FRAMES ===\n"
kill
quit
GDB
timeout 420 gdb -batch -nx -x /tmp/ap/f.gdb --args \
  $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so $APK \
  > /tmp/ap/fp.log 2>&1
echo "gdb rc=$?"
grep -a "fp\[\|=== FRAMES\|x29\|x30" /tmp/ap/fp.log | head -30
