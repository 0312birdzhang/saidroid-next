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
break __cxa_throw
commands
  silent
  set $tn = (char*)((void**)$x1)[1]
  if $_streq($tn, "std::out_of_range")
    printf "\n=== out_of_range thrown ===\n"
    printf "what = "
    output *(std::string*)&((std::logic_error*)$x0)->_M_msg
    printf "\n"
    bt 25
    printf "=== end ===\n"
    kill
    quit
  end
  continue
end
run
printf "\n=== no out_of_range ===\n"
GDB
timeout 420 gdb -batch -nx -x /tmp/ap/t.gdb --args \
  $BASE/bin/dalvikvm -cp /tmp/ap/ap.dex AssetProbe $LIBDIR /tmp/ap/libsdbridge.so $APK 2>&1 | grep -v "^\[New Thread\|^\[Thread \|^\[Detaching" | tail -50
