#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
cd /tmp/art-build/art-standalone
echo "=== 再试 make（带 JDK）==="
timeout 180 make -j2 2>&1 | head -40
echo "=== 结束 ==="
