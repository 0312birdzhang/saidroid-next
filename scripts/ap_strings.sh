F=/tmp/shimtest/libandroidfw.so
echo "=== .rodata 0x2e400-0x2e4a0（vaddr = file+0x1000）==="
objdump -s -j .rodata --start-address=0x2e400 --stop-address=0x2e4a0 $F 2>/dev/null | tail -12
echo "=== 用 dd 直接看 0x2e410 起 ==="
dd if=$F bs=1 skip=$((0x2e410)) count=160 2>/dev/null | tr -c '[:print:]' '\n' | grep -v '^$' | head -8
