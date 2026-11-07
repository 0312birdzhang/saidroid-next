L=/tmp/ap/ctx.log
echo "=== 异常/错误行 ==="
grep -a "No implementation\|NoSuchMethod\|Exception\|Error\|abort\|fatal\|Failed" $L | grep -av "packed reloc" | head -12
echo "=== 最后 25 行非 reloc ==="
grep -av "packed reloc" $L | tail -25 | cut -c1-200
