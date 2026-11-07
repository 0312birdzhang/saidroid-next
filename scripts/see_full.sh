#!/bin/bash
BASE=/tmp/art-build/art-standalone
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$BASE/out/host/linux-x86/bin:$PATH
export LD_LIBRARY_PATH=$BASE/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/art-data
export ANDROID_ROOT=$BASE/out/host/linux-x86
mkdir -p $ANDROID_DATA
cd /tmp/hello
echo "=== 完整输出（前30行）==="
timeout 240 $BASE/out/host/linux-x86/bin/dalvikvm -cp hello.dex Hello 2>&1 | head -30
echo "=== 退出码: $? ==="
