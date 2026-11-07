L=/tmp/ap/run.log
echo "=== 尾部 25 行 ==="
tail -25 $L
echo "=== PC 行 ==="
grep -a "pc:\|Thread:" $L | head -4
