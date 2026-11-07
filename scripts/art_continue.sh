#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/art-build/art-standalone
nohup make -j4 > /tmp/art-build4.log 2>&1 &
echo "PID=$!"
sleep 120
echo "=== 2分钟后 ==="
echo "错误数: $(grep -c 'error:' /tmp/art-build4.log 2>/dev/null || echo 0)"
echo "进度: $(grep -oE '\[[0-9]+%\]' /tmp/art-build4.log 2>/dev/null | tail -1)"
tail -5 /tmp/art-build4.log 2>/dev/null
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
