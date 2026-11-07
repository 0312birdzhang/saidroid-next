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
echo "=== 运行（过滤噪音）==="
timeout 300 $OUT/bin/dalvikvm -cp hello.dex Hello 2>&1 | grep -aE "^OPTART|^sum=|Hello|Exception|Error" | head -8
echo "---"
echo "=== oat 缓存 ==="
find /.cache/art /tmp/art-data -name "*.oat" 2>/dev/null | head -5
echo "=== boot.art ==="
find / -maxdepth 4 -name "boot.art" 2>/dev/null | head -3
