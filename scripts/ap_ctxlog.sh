L=/tmp/ap/ctx.log
echo "=== 行数 $(wc -l < $L) ==="
echo "=== 头部 30 行 ==="
grep -av "packed reloc" $L | head -30
