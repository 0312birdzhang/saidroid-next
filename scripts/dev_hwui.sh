#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
echo "=== 设备 bio2 里是否有 hwui 依赖 ==="
$SSH "ls -l /home/art/bio2/libhwui.so /home/art/bio2/libRS.so /home/art/bio2/libbcc.so /home/art/bio2/libLLVM.so 2>&1 | head -6"
echo "=== 备份替身并推真实 hwui ==="
$SSH "cp -f /home/art/bio2/libhwui.so /home/art/bio2/libhwui-shim.so.bak 2>/dev/null; echo backed-up"
$SCP /tmp/and23/bio2/libhwui.so root@bonito:/home/art/bio2/libhwui.so
$SCP /tmp/ap/libsdbridge.so root@bonito:/home/art/lib/libsdbridge.so
$SSH "ls -l /home/art/bio2/libhwui.so"
