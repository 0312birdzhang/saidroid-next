F=/tmp/shimtest/libandroid_runtime.so
echo "=== 调用点 vaddr 0xd8d8c 前后 ==="
objdump -d --start-address=0xd8cd0 --stop-address=0xd8e10 $F 2>/dev/null | tail -60
