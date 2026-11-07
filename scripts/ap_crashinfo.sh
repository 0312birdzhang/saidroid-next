L=/tmp/ap/ctx.log
echo "=== 故障信号与寄存器 ==="
grep -a -A16 "Fatal signal" $L | grep -aE "Fatal signal|pc:|x0:|x29:|x30:|sp:" | head -8
echo "=== 故障前 Java 栈 ==="
grep -a "    at " $L | head -12
