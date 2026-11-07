#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
cd /tmp/art-build/art-standalone
echo "=== 显式传 TARGET_ARCH=arm64 ==="
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a 2>&1 | head -5
echo "--- 后台跑 ---"
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a > /tmp/art-build8.log 2>&1 &
echo "PID=$!"
sleep 60
echo "=== 60秒后 ==="
grep -E "TARGET_ARCH=" /tmp/art-build8.log 2>/dev/null | head -2
echo "错误: $(grep -c 'error:' /tmp/art-build8.log 2>/dev/null || echo 0)"
tail -5 /tmp/art-build8.log 2>/dev/null
