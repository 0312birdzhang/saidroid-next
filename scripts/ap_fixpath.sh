BASE=/tmp/art-build/art-standalone/out/host/linux-x86
echo "=== 现有 java/dex/art ==="
ls $BASE/java/dex/art 2>/dev/null | head -20
echo "=== 复制 framework jar ==="
mkdir -p $BASE/java/dex/art
for j in framework-hostdex.jar framework2-hostdex.jar framework3-hostdex.jar framework4-hostdex.jar; do
  cp -f /tmp/fw23/jars/$j $BASE/java/dex/art/$j && echo "  $j"
done
echo "=== 结果 ==="
ls -lh $BASE/java/dex/art | head -20
