F=/tmp/shimtest/libandroidfw.so
echo "=== getTableCount 相关符号/PLT ==="
objdump -d $F 2>/dev/null | grep -n "getTableCount" | head -20
echo "=== 所有调用点 ==="
objdump -d $F 2>/dev/null | grep -n "bl.*getTableCount\|b.*<.*getTableCount" | head -20
