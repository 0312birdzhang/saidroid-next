#!/bin/bash
JAVA=/tmp/jdkfull/jdk-21.0.13+9/bin
mkdir -p /tmp/region/src/android/graphics /tmp/region/out
cp /media/psf/Home/.dsh/bot/workspace/sailfish-os/build/Region.java /tmp/region/src/android/graphics/Region.java
cd /tmp/region
echo "=== 编译 AOSP Region.java ==="
$JAVA/javac --release 8 -nowarn -cp /tmp/fw23/cls -d out src/android/graphics/Region.java 2>&1 | grep -v obsolete | head -12
ls -l out/android/graphics/Region.class 2>/dev/null || echo "编译失败"
echo "=== 替换进框架 class 集 ==="
if [ -f out/android/graphics/Region.class ]; then
  cp out/android/graphics/Region.class /tmp/fw23/cls/android/graphics/Region.class
  echo "replaced"
  $JAVA/javap -p -classpath /tmp/fw23/cls android.graphics.Region 2>/dev/null | grep -E "Region\(" | head -6
fi
