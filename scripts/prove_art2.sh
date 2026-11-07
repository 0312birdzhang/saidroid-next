#!/bin/bash
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
BASE=/tmp/art-build/art-standalone
export LD_LIBRARY_PATH=$BASE/out/host/linux-x86/lib64:/usr/local/lib
export ANDROID_DATA=/tmp/dalvik-data
export ANDROID_ROOT=$BASE/out/host/linux-x86
mkdir -p $ANDROID_DATA
BCP="$BASE/out/host/linux-x86/framework/core-oj-hostdex.jar:$BASE/out/host/linux-x86/framework/core-libart-hostdex.jar"
cd /tmp/hello
echo "=== 测试1 ==="
$BASE/out/host/linux-x86/bin/dalvikvm -Xbootclasspath:"$BCP" -cp t1.dex T1 2>&1 | grep -a -E "ART_TEST|sum_|string_len|arr_99"
echo "=== 测试2 ==="
$BASE/out/host/linux-x86/bin/dalvikvm -Xbootclasspath:"$BCP" -cp t2.dex T2 2>&1 | grep -a -E "ART_TEST|caught="
