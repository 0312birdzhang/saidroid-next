export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no root@bonito"
echo "=== 设备 libart.so 是否引用 bionic_dlopen ==="
$SSH "ls -l /home/art/lib/libart.so; nm -D /home/art/lib/libart.so 2>/dev/null | grep -c bionic_dlopen; strings /home/art/lib/libart.so | grep -c 'bionic_dlopen'"
echo "=== NEEDED ==="
$SSH "readelf -d /home/art/lib/libart.so 2>/dev/null | grep NEEDED | head -8"
echo "=== VM 侧刚编的（未 strip）对比 ==="
BASE=/tmp/art-build/art-standalone/out/host/linux-x86
nm -D $BASE/lib64/libart.so 2>/dev/null | grep -c bionic_dlopen
readelf -d $BASE/lib64/libart.so 2>/dev/null | grep NEEDED | head -8
