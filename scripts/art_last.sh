#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
export LD_LIBRARY_PATH=/usr/local/lib
cd /tmp/art-build/art-standalone
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a \
  ART_HOST_CODEGEN_ARCHS=arm64 > /tmp/art-build13.log 2>&1 &
echo "PID=$!"
sleep 200
echo "=== 状态 ==="
echo "错误: $(grep -c 'error:' /tmp/art-build13.log 2>/dev/null || echo 0)"
grep -E "error:|cannot find" /tmp/art-build13.log 2>/dev/null | head -5
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
echo "=== 产物 ==="
ls -la out/host/linux-x86/bin/ 2>/dev/null
