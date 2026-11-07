export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
echo "=== abort 之前的日志（找 FATAL 文本）==="
$SSH "grep -av 'packed reloc' /home/art/test/gdb3.log | grep -a -B2 -A6 'Check failed\|FATAL\|Aborting\|Fatal' | head -30"
echo "=== 920 行附近源码（CHECK 上下文）==="
sed -n '905,945p' /tmp/art-build/art-standalone/art/runtime/jni/java_vm_ext.cc
