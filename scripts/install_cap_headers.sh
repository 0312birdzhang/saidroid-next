#!/bin/bash
cd /tmp/captmp/extracted 2>/dev/null || exit 1
echo "=== 安装头文件到系统 ==="
cp -a usr/include/sys/capability.h /usr/include/sys/ 2>&1
cp -a usr/include/sys/psx_syscall.h /usr/include/sys/ 2>/dev/null
ls -la /usr/include/sys/capability.h 2>/dev/null && echo "cap=ok"
echo
echo "=== 继续构建 ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/art-build/art-standalone
nohup make -j4 > /tmp/art-build5.log 2>&1 &
echo "PID=$!"
sleep 90
echo "=== 90秒后 ==="
echo "错误: $(grep -c 'error:' /tmp/art-build5.log 2>/dev/null || echo 0)"
tail -6 /tmp/art-build5.log 2>/dev/null
pgrep -f "make -j4" >/dev/null && echo RUNNING || echo STOPPED
