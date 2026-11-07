F=/tmp/shimtest/libandroidfw.so
echo "=== 是否 stripped ==="
file $F
echo "=== 动态符号数量 ==="
readelf -sW --dyn-syms $F 2>/dev/null | grep -c FUNC
echo "=== 0x20f80 附近的动态符号 ==="
readelf -sW --dyn-syms $F 2>/dev/null | awk 'NF>7 && $4=="FUNC" {a=strtonum("0x"$2); if (a<=0x20f80 && a>0) {print a, $8}}' | sort -n | tail -5
echo "=== 反汇编故障点附近 ==="
objdump -d --start-address=0x20f40 --stop-address=0x20fb0 $F 2>/dev/null | tail -25
