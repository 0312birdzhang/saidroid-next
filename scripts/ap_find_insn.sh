F=/tmp/shimtest/libandroidfw.so
echo "=== 段表（vaddr / offset / filesz）==="
readelf -lW $F 2>/dev/null | awk '/LOAD/ {print "vaddr="$3" off="$2" filesz="$5" flags="$7}'
echo "=== 搜索 ldr x0, [x0, #112] ==="
objdump -d $F 2>/dev/null | grep -n "ldr	x0, \[x0, #112\]" | head -10
