#!/bin/bash
set -u
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
SRC=/media/psf/Home/WorkSpace/saidroid-next/scripts/framework/Parcel.java
W=/tmp/fw23
mkdir -p $W/patchsrc/android/os $W/patchout
cp $SRC $W/patchsrc/android/os/Parcel.java
cd $W || exit 1
echo "=== 编译 Parcel.java ==="
$JAVA/javac --release 8 -nowarn -cp $W/cls -d $W/patchout $W/patchsrc/android/os/Parcel.java 2>&1 | grep -v "obsolete\|unchecked\|Recompile" | head -20
if [ ! -f $W/patchout/android/os/Parcel.class ]; then echo "编译失败"; exit 1; fi
cp $W/patchout/android/os/Parcel.class $W/cls/android/os/Parcel.class
echo "replaced"
$JAVA/javap -p -classpath $W/cls android.os.Parcel 2>/dev/null | grep -E "nativeSetDataSize|nativeCreate" | head -3
