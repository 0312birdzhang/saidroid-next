BASE=/tmp/art-build/art-standalone/out/host/linux-x86
echo "=== framework 目录里有什么 ==="
ls $BASE/framework/ | grep -i "res\|apk" || echo "（没有 apk）"
echo "=== 复制 framework-res.apk ==="
cp -f /tmp/and23/out/framework/framework-res.apk $BASE/framework/ && echo "已复制"
ls -lh $BASE/framework/framework-res.apk
