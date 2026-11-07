#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== dx.jar 详情 ==="
ls -la out/host/linux-x86/framework/dx.jar 2>/dev/null
echo "=== 内容验证 ==="
/tmp/jdkfull/jdk-21.0.13+9/bin/jar tf out/host/linux-x86/framework/dx.jar 2>/dev/null | head -5
echo "=== 已编译的 class 数 ==="
find out/host/common/obj/JAVA_LIBRARIES/dx_intermediates/classes -name "*.class" 2>/dev/null | wc -l
echo
echo "=== 当前 JDK ==="
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
$JAVA_HOME/bin/java -version 2>&1 | head -2
echo
echo "=== tools.jar 是否存在 ==="
ls $JAVA_HOME/lib/tools.jar 2>/dev/null || echo "不存在（JDK 9+ 正常）"
