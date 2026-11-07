#!/bin/bash
BASE=/tmp/art-build/art-standalone
export LD_LIBRARY_PATH=$BASE/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/art-data
export ANDROID_ROOT=$BASE/out/host/linux-x86
mkdir -p $ANDROID_DATA
cd /tmp/hello
echo "=== gdb backtrace ==="
timeout 180 gdb -batch -ex run -ex "bt 15" --args \
  $BASE/out/host/linux-x86/bin/dalvikvm -cp hello.dex Hello 2>&1 | tail -25
