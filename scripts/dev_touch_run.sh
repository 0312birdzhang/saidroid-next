#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SSH '. /home/art/env.sh; cd /home/art/test; dalvikvm -cp /home/art/test/ap.dex TouchProbe /home/art/bio2 /home/art/lib/libsdbridge.so /home/art/touch > /home/art/test/touch.log 2>&1; echo rc=$?'
echo "=== TP 标记 ==="
$SSH "grep -a 'TP\[' /home/art/test/touch.log | head -40"
echo "=== 帧文件 ==="
$SSH "ls -l /home/art/touch-*.rgba 2>/dev/null"
echo "=== 尾部 ==="
$SSH "grep -av 'packed reloc' /home/art/test/touch.log | tail -8 | cut -c1-200"
