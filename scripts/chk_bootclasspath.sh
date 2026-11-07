#!/bin/bash
cd /tmp/art-build/art-standalone
echo "=== bootclasspath 相关产物 ==="
find out -name "*-hostdex.jar" -o -name "core-*.jar" 2>/dev/null | head -8
echo
echo "=== java 目录 ==="
ls out/host/linux-x86/framework/ 2>/dev/null | head -10
echo
echo "=== dalvikvm 需要的环境 ==="
strings out/host/linux-x86/bin/dalvikvm 2>/dev/null | grep -iE "bootclasspath|ANDROID_ROOT|ANDROID_DATA" | head -5
