#!/bin/bash
BASE=/tmp/art-build/art-standalone
OUT=$BASE/out/host/linux-x86
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$OUT/bin:$PATH
export LD_LIBRARY_PATH=$OUT/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/art-data
export ANDROID_ROOT=$OUT
mkdir -p $ANDROID_DATA
cd /tmp/hello
echo "=== 完整测试 ==="
timeout 300 $OUT/bin/dalvikvm -cp hello.dex Hello 2>&1 | head -20
echo "---"
echo "=== oat 产物 ==="
find /tmp/art-data -name "*.oat" -o -name "*.art" 2>/dev/null | head -5
