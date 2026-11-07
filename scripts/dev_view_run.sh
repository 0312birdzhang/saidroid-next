#!/bin/bash
set -u
export SSHPASS="${SSHPASS:?Set SSHPASS for device development}"
SSH="sshpass -e ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@bonito"
SCP="sshpass -e scp -o StrictHostKeyChecking=no -o ConnectTimeout=10"
$SCP /tmp/ap/ap.dex root@bonito:/home/art/test/ap.dex
$SSH '. /home/art/env.sh; cd /home/art/test; dalvikvm -cp /home/art/test/ap.dex ViewProbe /home/art/bio2 /home/art/lib/libsdbridge.so /home/art/view.rgba > /home/art/test/view.log 2>&1; echo rc=$?'
echo "=== VP 标记 ==="
$SSH "grep -a 'VP\[' /home/art/test/view.log | head -30"
echo "=== 文件 ==="
$SSH "ls -l /home/art/view.rgba 2>/dev/null"
echo "=== 尾部 ==="
$SSH "grep -av 'packed reloc' /home/art/test/view.log | tail -10 | cut -c1-200"
