#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/art-build/art-standalone
nohup make -j4 > /tmp/art-build.log 2>&1 &
echo "PID=$!"
sleep 30
echo "=== 30秒后状态 ==="
tail -15 /tmp/art-build.log 2>/dev/null
echo "=== 是否还在跑 ==="
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
