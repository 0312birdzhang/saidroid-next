set -u
rm -rf /tmp/realtest
cp -a /tmp/shimtest /tmp/realtest
cp -f /tmp/and23/bio2/libhwui.so /tmp/realtest/libhwui.so
ls -l /tmp/realtest/libhwui.so
echo "=== 依赖检查 ==="
LD_LIBRARY_PATH=/tmp/realtest ldd -r /tmp/realtest/libhwui.so 2>&1 | grep -i "not found\|undefined" | head -5
echo "(空=可解析)"
