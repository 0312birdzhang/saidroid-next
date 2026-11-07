L=/tmp/ap/run.log
echo "=== SDBRIDGE 行 ==="
grep -a "SDBRIDGE" $L | head -8
echo "=== 错误/异常 ==="
grep -a "No implementation\|NoSuchMethod\|NoClassDef\|UnsatisfiedLink\|Exception\|abort" $L | grep -av "packed reloc" | head -10
echo "=== 尾部 20 ==="
grep -av "packed reloc" $L | tail -20 | cut -c1-200
