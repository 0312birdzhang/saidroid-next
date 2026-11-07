F=/tmp/shimtest/libandroidfw.so
echo "=== 0x21f80 最近的已导出符号 ==="
nm -D --defined-only $F 2>/dev/null | awk '{a=strtonum("0x"$1); if ($2=="T" && a<=0x21f80) {last=$0; la=a}} END {n=split(last,f," "); printf "  %s  (+0x%x)\n", f[3], 0x21f80-la}'
echo "=== 上下文反汇编 0x21f40 - 0x21fe0 ==="
objdump -d --start-address=0x21f40 --stop-address=0x21fe0 $F 2>/dev/null | tail -30
echo "=== 下一个符号（找函数边界）==="
nm -D --defined-only $F 2>/dev/null | sort | awk '{a=strtonum("0x"$1); if ($2=="T" && a>0x21f80) {print; exit}}'
