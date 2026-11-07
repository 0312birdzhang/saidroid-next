L=/tmp/ap/ctx.log
echo "=== abort 原因 ==="
grep -an "Aborting thread\|Pending exception\|Check failed\|abort message\|Runtime aborting\|JNI FatalError\|CHECK failed\|NoSuchMethod\|NoClassDef\|UnsatisfiedLink" $L | grep -av "packed reloc" | head -10
echo "=== Fatal signal 之前 30 行 ==="
n=$(grep -an "Fatal signal" $L | head -1 | cut -d: -f1)
sed -n "$((n>32?n-32:1)),$((n-1))p" $L | grep -av "packed reloc" | cut -c1-220 | head -32
