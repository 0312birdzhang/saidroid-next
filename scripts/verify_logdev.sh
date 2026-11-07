#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/art-build/art-standalone
echo "=== 单独编译这个文件验证 ==="
gcc -c -o /tmp/test_logdev.o system/core/liblog/fake_log_device.c \
  -I system/core/include -I system/core/liblog/include 2>&1 | head -10
[ -f /tmp/test_logdev.o ] && echo "COMPILE=ok" || echo "COMPILE=fail"
