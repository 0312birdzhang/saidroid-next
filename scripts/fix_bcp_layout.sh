#!/bin/bash
BASE=/tmp/art-build/art-standalone
OUT=$BASE/out/host/linux-x86
echo "=== 当前 java/dex/art 在哪 ==="
find $OUT -name "core-oj-hostdex.jar" 2>/dev/null | head -3
echo
echo "=== 建立正确布局: \$OUT/java/dex/art/ ==="
mkdir -p $OUT/java/dex/art
cp $OUT/framework/*hostdex.jar $OUT/java/dex/art/ 2>/dev/null
ls $OUT/java/dex/art/ 2>/dev/null | head -5
echo "文件数: $(ls $OUT/java/dex/art/*.jar 2>/dev/null | wc -l)"
echo
echo "=== 验证 realpath 能解析 ==="
realpath "$OUT/lib64/../java/dex/art/" 2>/dev/null
