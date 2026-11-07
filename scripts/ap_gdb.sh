#!/bin/bash
# 在 glibc 第一次报堆错误时停下，打全栈
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

cat > /tmp/ap/cmds.gdb <<'GDB'
set pagination off
set confirm off
set breakpoint pending on
break __libc_message
commands
  silent
  printf "\n=== FIRST HEAP ERROR ===\n"
  bt 30
  printf "\n=== end bt ===\n"
  kill
  quit
end
run
printf "\n=== exited without heap error ===\n"
GDB

timeout 420 gdb -batch -nx -x /tmp/ap/cmds.gdb --args \
  $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so $APK 2>&1 | tail -80
