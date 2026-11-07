#!/bin/bash
BASE=/tmp/art-build/art-standalone
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$BASE/out/host/linux-x86/bin:$PATH
export LD_LIBRARY_PATH=$BASE/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/art-data
export ANDROID_ROOT=$BASE/out/host/linux-x86
mkdir -p $ANDROID_DATA
cd /tmp/hello
echo "=== 用修复后的 libart 测试 ==="
timeout 300 $BASE/out/host/linux-x86/bin/dalvikvm -cp hello.dex Hello 2>&1 | grep -aE "Failed to execve|OPTART|sum=|GenerateImage|Failed to compile|Hello" | head -8
echo
echo "=== 是否生成了 oat ==="
find /tmp/art-data -name "*.oat" 2>/dev/null | head -3
