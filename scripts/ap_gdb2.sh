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

cat > /tmp/ap/t.gdb <<'GDB'
set pagination off
set confirm off
set breakpoint pending on
rbreak out_of_range
commands
  silent
  printf "\n=== out_of_range thrown ===\n"
  bt 25
  printf "=== end ===\n"
  kill
  quit
end
run
printf "\n=== no out_of_range ===\n"
GDB
timeout 420 gdb -batch -nx -x /tmp/ap/t.gdb --args \
  $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so $APK 2>&1 | grep -v "^\[New Thread\|^\[Thread " | tail -60
