#!/bin/bash
JDK=/tmp/jdkfull/jdk-21.0.13+9
cd /tmp; rm -rf CT; mkdir CT; cd CT
cp "/media/psf/Home/WorkSpace/saidroid-next/runtime/macapk-loader.jar" .
echo "=== DexConverter 的公开 API ==="
$JDK/bin/javap -p -cp macapk-loader.jar com.macapk.dex.DexConverter 2>/dev/null | grep -E "public static" | head -5
echo
echo "=== 它输出什么？（找 ClassFileWriter）==="
$JDK/bin/jar tf macapk-loader.jar 2>/dev/null | grep -iE "ClassFileWriter|ConstantPool|Instruction" | head -5
echo
echo "=== 是否有 dex2oat / ART 痕迹 ==="
$JDK/bin/jar tf macapk-loader.jar 2>/dev/null | grep -icE "dex2oat|art|oat" || echo "0"
