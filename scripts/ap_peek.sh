L=/tmp/ap/run.log
echo "=== 行数: $(wc -l < $L 2>/dev/null) ==="
echo "=== AP 标记 ==="
grep -a "AP\[" $L 2>/dev/null | head -40
echo "=== SDBRIDGE 行 ==="
grep -a "SDBRIDGE" $L 2>/dev/null | head -20
echo "=== 首个非 AP 错误上下文 ==="
n=$(grep -an "malloc()\|free()\|corrupt\|signal" $L 2>/dev/null | head -1 | cut -d: -f1)
echo "first=$n"
if [ -n "$n" ]; then sed -n "1,${n}p" $L | tail -25; fi
echo "=== 尾部 ==="
tail -3 $L 2>/dev/null
