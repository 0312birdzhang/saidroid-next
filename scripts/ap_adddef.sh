F=/tmp/shimtest/libandroidfw.so
echo "=== addDefaultAssets 反汇编 ==="
objdump -d --start-address=0x19c34 --stop-address=0x19d00 $F 2>/dev/null | tail -35
echo "=== libc_bio 是否导出 getenv ==="
nm -D --defined-only /usr/local/lib/libc_bio.so.0 | grep -w "getenv\|environ" | head -5
echo "=== 其他 bio 库 ==="
for f in /usr/local/lib/lib*_bio.so*; do n=$(nm -D --defined-only $f 2>/dev/null | grep -cw "getenv"); [ "$n" != "0" ] && echo "$f 有 getenv"; done
