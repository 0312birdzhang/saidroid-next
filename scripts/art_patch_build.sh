#!/bin/bash
# VM 侧：打 oat_file_assistant 补丁并增量重编 libart
set -u
export JAVA_HOME=/tmp/jdkfull/jdk-21.0.13+9
export PATH=$JAVA_HOME/bin:$PATH
export CPLUS_INCLUDE_PATH=/usr/local/include
export LIBRARY_PATH=/usr/local/lib
A=/tmp/art-build/art-standalone

echo "=== 打补丁 ==="
python3 /media/psf/Home/WorkSpace/saidroid-next/scripts/art_fix_oatassist.py $A/art/runtime/oat_file_assistant.cc || exit 1
sed -n '205,222p' $A/art/runtime/oat_file_assistant.cc

echo "=== 增量编译 ==="
cd $A
nohup make -j4 TARGET_ARCH=arm64 TARGET_ARCH_VARIANT=armv8-a ART_HOST_CODEGEN_ARCHS=arm64 > /tmp/art-rebuild.log 2>&1 &
echo "PID=$!"
sleep 5
echo "已启动"
