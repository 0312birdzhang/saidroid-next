L=/tmp/ap/run.log
echo "=== 完整栈（AP[10] 段落）==="
sed -n '/AP\[10\] FAIL/,/AP\[11\]/p' $L | grep -a "at \|Exception" | head -12
echo
echo "=== libc_bio 的 system_property 实现 ==="
grep -n "system_property_get\|system_property_find\|prop_area\|__system_property" /tmp/art-build/bionic_translation/libc/libc-misc.c | head -12
