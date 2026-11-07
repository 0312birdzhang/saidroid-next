#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/art-build/art-standalone
echo "=== 预建中间目录 ==="
mkdir -p out/host/linux-x86/obj/SHARED_LIBRARIES/libart-dexlayout_intermediates 2>/dev/null
mkdir -p out/host/linux-x86/obj 2>/dev/null
echo "=== 单线程重试（避免目录竞争）==="
nohup make -j1 > /tmp/art-build3.log 2>&1 &
echo "PID=$!"
sleep 60
echo "=== 60秒后 ==="
grep -cE "error:" /tmp/art-build3.log 2>/dev/null || echo "0"
tail -6 /tmp/art-build3.log 2>/dev/null
pgrep -f "make -j1" >/dev/null && echo RUNNING || echo STOPPED
