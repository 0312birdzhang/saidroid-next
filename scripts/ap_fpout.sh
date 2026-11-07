L=/tmp/ap/fp.log
echo "=== gdb 尾部（非 reloc）==="
grep -av "packed reloc" $L | tail -35
