#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
cd /tmp/art-build/art-standalone
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a \
  ART_HOST_CODEGEN_ARCHS=arm64 > /tmp/art-build11.log 2>&1 &
echo "PID=$!"
sleep 180
echo "=== 3分钟后 ==="
echo "错误: $(grep -c 'error:' /tmp/art-build11.log 2>/dev/null || echo 0)"
echo ".o 数: $(find out -name '*.o' 2>/dev/null | wc -l)"
grep -E "error:" /tmp/art-build11.log 2>/dev/null | head -3
tail -4 /tmp/art-build11.log 2>/dev/null
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
