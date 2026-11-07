#!/bin/bash
JDK=/tmp/jdkfull/jdk-21.0.13+9
cd /tmp/CT 2>/dev/null || exit 1
echo "=== 那 3 个 art 匹配是什么 ==="
$JDK/bin/jar tf macapk-loader.jar 2>/dev/null | grep -iE "dex2oat|art|oat" | head -5
echo
echo "=== ClassFileWriter 证明输出是 .class ==="
$JDK/bin/javap -p -cp macapk-loader.jar com.macapk.dex.ClassFileWriter 2>/dev/null | head -8
echo
echo "=== 转换产物实际是 class 文件 ==="
echo "之前实测：DexConverter.convert() 返回 Map<String, byte[]>"
echo "key = 类名，value = JVM class 字节码（CAFEBABE）"
