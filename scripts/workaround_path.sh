#!/bin/bash
echo "=== 在 /opt/art 根放 dex2oat 软链（绕过路径 bug）==="
ln -sf /opt/art/bin/dex2oat /opt/art/dex2oat 2>/dev/null
ln -sf /opt/art/bin/dex2oatd /opt/art/dex2oatd 2>/dev/null
ls -la /opt/art/dex2oat 2>/dev/null

echo
echo "=== 重新测试（ANDROID_ROOT=/opt/art）==="
export JAVA_HOME=/opt/art/jdk
export PATH=$JAVA_HOME/bin:/opt/art/bin:$PATH
export LD_LIBRARY_PATH=/opt/art/lib/aarch64-linux-gnu:/opt/art/lib
export ANDROID_DATA=/tmp/art-data
export ANDROID_ROOT=/opt/art
mkdir -p $ANDROID_DATA
cd /tmp/hello
timeout 300 /opt/art/bin/dalvikvm -cp hello.dex Hello 2>&1 | grep -aE "Failed to execve|OPTART|sum=|GenerateImage|Failed to compile" | head -6
