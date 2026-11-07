#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
BASE=/tmp/art-build/art-standalone
export LD_LIBRARY_PATH=$BASE/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/dalvik-data
export ANDROID_ROOT=$BASE/out/host/linux-x86
mkdir -p $ANDROID_DATA

BCP="$BASE/out/host/linux-x86/framework/core-oj-hostdex.jar:$BASE/out/host/linux-x86/framework/core-libart-hostdex.jar"
echo "=== bootclasspath ==="
echo "$BCP" | tr ':' '\n' | head -3
echo
echo "=== 执行 ==="
cd /tmp/hello
$BASE/out/host/linux-x86/bin/dalvikvm -Xbootclasspath:"$BCP" -cp hello.dex Hello 2>&1 | head -15
