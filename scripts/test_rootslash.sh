#!/bin/bash
export JAVA_HOME=/opt/art/jdk
export PATH=$JAVA_HOME/bin:/opt/art/bin:$PATH
export LD_LIBRARY_PATH=/opt/art/lib/aarch64-linux-gnu:/opt/art/lib
export ANDROID_DATA=/tmp/art-data
mkdir -p $ANDROID_DATA
cd /tmp/hello

echo "=== 试1: ANDROID_ROOT 不带斜杠（预期失败）==="
ANDROID_ROOT=/opt/art /opt/art/bin/dalvikvm -cp hello.dex Hello 2>&1 | grep -aE "Failed to execve|OPTART|sum=" | head -3

echo
echo "=== 试2: ANDROID_ROOT 带斜杠 ==="
ANDROID_ROOT=/opt/art/ /opt/art/bin/dalvikvm -cp hello.dex Hello 2>&1 | grep -aE "Failed to execve|OPTART|sum=" | head -3

echo
echo "=== 试3: 不设 ANDROID_ROOT（走 PATH）==="
unset ANDROID_ROOT
/opt/art/bin/dalvikvm -cp hello.dex Hello 2>&1 | grep -aE "Failed to execve|OPTART|sum=" | head -3
