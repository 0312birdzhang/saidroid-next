#!/bin/bash
echo "=== 装 VIXL 到系统 ==="
cd /tmp/art-build/vixl
mkdir -p /usr/local/lib /usr/local/include
cp build/libvixl.a /usr/local/lib/ 2>/dev/null
cp -r src/aarch64 /usr/local/include/ 2>/dev/null
cp src/*.h /usr/local/include/ 2>/dev/null
ldconfig 2>/dev/null
echo "=== 验证 ==="
ls -la /usr/local/lib/libvixl.a 2>/dev/null
ls /usr/local/include/aarch64/disasm-aarch64.h 2>/dev/null && echo "header=ok"
echo
echo "=== 继续 art 构建 ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include:$CPLUS_INCLUDE_PATH
export LIBRARY_PATH=/usr/local/lib:$LIBRARY_PATH
cd /tmp/art-build/art-standalone
nohup make -j4 > /tmp/art-build6.log 2>&1 &
echo "PID=$!"
sleep 90
echo "=== 90秒后 ==="
echo "错误: $(grep -c 'error:' /tmp/art-build6.log 2>/dev/null || echo 0)"
tail -6 /tmp/art-build6.log 2>/dev/null
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
