#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== 恢复 Android.mk 的 arm 依赖 ==="
cp art/compiler/Android.mk.bak art/compiler/Android.mk 2>/dev/null && echo "已恢复"
grep -n "libart-compiler-defaults_arm_CODEGEN_SRCS)" art/compiler/Android.mk 2>/dev/null | head -3
echo
echo "=== 现在 VIXL 有完整 aarch32，应该能编 ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
export LD_LIBRARY_PATH=/usr/local/lib
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a \
  ART_HOST_CODEGEN_ARCHS=arm64 > /tmp/art-build14.log 2>&1 &
echo "PID=$!"
sleep 150
echo "错误: $(grep -c 'error:' /tmp/art-build14.log 2>/dev/null || echo 0)"
grep -E "error:|cannot find" /tmp/art-build14.log 2>/dev/null | head -3
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
