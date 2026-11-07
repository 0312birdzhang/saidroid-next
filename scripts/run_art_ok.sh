#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export LD_LIBRARY_PATH=/tmp/art-build/art-standalone/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/dalvik-data
mkdir -p $ANDROID_DATA
cd /tmp/hello
echo "=== 用 --release 8 编译 ==="
$JAVA_HOME/bin/javac --release 8 Hello.java 2>&1 | head -3
echo "=== dx 转换 ==="
/tmp/art-build/art-standalone/out/host/linux-x86/bin/dx --dex --output=hello.dex . 2>&1 | head -5
ls -la hello.dex 2>/dev/null
echo
echo "=== dalvikvm 执行 ==="
/tmp/art-build/art-standalone/out/host/linux-x86/bin/dalvikvm -cp hello.dex Hello 2>&1 | head -12
