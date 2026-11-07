#!/bin/bash
# 把补过的 Binder.java 编进框架 class 集
set -u
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
SRC=/media/psf/Home/WorkSpace/saidroid-next/scripts/framework/Binder.java
W=/tmp/fw23
mkdir -p $W/patchsrc/android/os $W/patchout
cp $SRC $W/patchsrc/android/os/Binder.java
cd $W || exit 1
echo "=== 编译 Binder.java（对 multi.jar 的 class 集）==="
$JAVA/javac --release 8 -nowarn -cp $W/cls -d $W/patchout $W/patchsrc/android/os/Binder.java 2>&1 | grep -v "obsolete\|警告" | head -15
if [ ! -f $W/patchout/android/os/Binder.class ]; then echo "编译失败"; exit 1; fi
echo "=== 替换进框架 class 集 ==="
cp $W/patchout/android/os/Binder.class $W/cls/android/os/Binder.class
echo "replaced"
$JAVA/javap -p -classpath $W/cls android.os.Binder 2>/dev/null | grep -E "onBinderStrictModePolicyChange|execTransact|mObject" | head -5
