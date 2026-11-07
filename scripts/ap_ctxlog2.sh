L=/tmp/ap/ctx.log
echo "=== 尾部 40 行（非 reloc）==="
grep -av "packed reloc" $L | tail -40 | cut -c1-220
