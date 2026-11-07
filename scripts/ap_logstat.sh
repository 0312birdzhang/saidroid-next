L=/tmp/ap/run.log
echo "=== 总行数 $(wc -l < $L) ==="
echo "=== 出现最多的 5 类行（去掉数字）==="
sed -E 's/[0-9]+/N/g' $L | sort | uniq -c | sort -rn | head -8
echo "=== AP 之后到结尾的非重复内容 ==="
grep -an "AP\[6\]\|AP\[5\]" $L | head
echo "=== 结尾 15 行 ==="
tail -15 $L
