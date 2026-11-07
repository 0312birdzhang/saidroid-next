F=/tmp/shimtest/libandroidfw.so
echo "=== AssetManager::getResources(bool) 反汇编 ==="
objdump -d --start-address=0x199e8 --stop-address=0x19a40 $F 2>/dev/null | tail -25
echo "=== addDefaultAssets 真实修饰名 ==="
readelf -sW --dyn-syms $F 2>/dev/null | awk '$8 ~ /addDefault/ {print $2, $8}'
echo "=== addAssetPath 反汇编前 40 条 ==="
objdump -d --start-address=0x199ec --stop-address=0x19a60 $F 2>/dev/null | tail -30
