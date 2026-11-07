L=/tmp/ap/run.log
echo "=== AP[10] 附近的栈 ==="
grep -an -A12 "FAIL new Resources" $L | grep -av "^.*AP\[10\] FAIL new Resources : java" | head -20
