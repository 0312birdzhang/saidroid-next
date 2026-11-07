#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/art-build/art-standalone
nohup make -j4 > /tmp/art-build2.log 2>&1 &
echo "PID=$!"
sleep 90
echo "=== 90秒后 ==="
grep -cE "error:" /tmp/art-build2.log 2>/dev/null || echo "0 errors"
tail -8 /tmp/art-build2.log 2>/dev/null
echo "=== 进程 ==="
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
