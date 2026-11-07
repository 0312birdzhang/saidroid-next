#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
cd /tmp/art-build/art-standalone
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a ART_HOST_CODEGEN_ARCHS=arm64 > /tmp/art-rb3.log 2>&1 &
sleep 150
echo "错误: $(grep -c 'error:' /tmp/art-rb3.log 2>/dev/null || echo 0)"
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo DONE
echo "=== 测试 ==="
BASE=/tmp/art-build/art-standalone
export LD_LIBRARY_PATH=$BASE/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/art-data
export ANDROID_ROOT=$BASE/out/host/linux-x86
mkdir -p $ANDROID_DATA
cd /tmp/hello
timeout 240 $BASE/out/host/linux-x86/bin/dalvikvm -cp hello.dex Hello 2>&1 | head -12
